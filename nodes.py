import json
import asyncio
import logging
from datetime import datetime, date, timedelta
from collections import defaultdict
from pocketflow import Node, BatchNode
from utils.telegram_api import get_latest_updates, send_message
from utils.call_llm import call_llm
from utils.gsheets_api import append_row, get_all_records

logger = logging.getLogger(__name__)

class GetMessageNode(Node):
    def exec(self, _):
        logger.debug("Nodo [GetMessageNode]: Buscando nuevos mensajes...")
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        update_data = loop.run_until_complete(get_latest_updates())
        if update_data:
            logger.info(f"-> Mensaje recibido de '{update_data['user_name']}': {update_data['message_text']}")
        return update_data
    def post(self, shared, _, exec_res):
        if exec_res:
            shared["telegram_input"] = exec_res
            return "default"
        return None

class DetectIntentNode(Node):
    def prep(self, shared):
        return shared.get("telegram_input", {}).get("message_text")

    def exec(self, message_text):
        if not message_text: return None
        logger.info("Nodo [DetectIntentNode]: Clasificando intención del usuario...")
        
        prompt = f"""
        Analiza el siguiente mensaje de un usuario y clasifica su intención.
        Responde únicamente con un objeto JSON.
        El objeto debe tener una clave "intent" y una clave "entities".

        Las intenciones posibles son: "REGISTRAR_GASTO", "CONSULTAR_GASTOS", "OTRO".

        Si la intención es "CONSULTAR_GASTOS", extrae el período de tiempo en la clave "entities".
        - Si menciona un mes, usa {{"month": "nombre_del_mes"}}.
        - Si menciona un período fijo, usa {{"period": "valor"}}.

        **REGLAS IMPORTANTES PARA PERÍODOS:**
        - Los únicos valores permitidos para "period" son: "hoy", "ayer", "esta_semana", "semana_pasada".
        - Cualquier mención de "hoy" (como "gastos de hoy", "cuánto gasté hoy?") DEBE resultar en {{"period": "hoy"}}.
        - Cualquier mención de "ayer" DEBE resultar en {{"period": "ayer"}}.

        Ejemplos:
        - Mensaje: "gaste 5000 en cafe" -> {{"intent": "REGISTRAR_GASTO", "entities": {{}}}}
        - Mensaje: "cuanto gaste hoy?" -> {{"intent": "CONSULTAR_GASTOS", "entities": {{"period": "hoy"}}}}
        - Mensaje: "resumen para hoy" -> {{"intent": "CONSULTAR_GASTOS", "entities": {{"period": "hoy"}}}}
        - Mensaje: "resumen de ayer" -> {{"intent": "CONSULTAR_GASTOS", "entities": {{"period": "ayer"}}}}
        - Mensaje: "gastos de la semana pasada" -> {{"intent": "CONSULTAR_GASTOS", "entities": {{"period": "semana_pasada"}}}}
        - Mensaje: "hola" -> {{"intent": "OTRO", "entities": {{}}}}

        Mensaje a analizar: "{message_text}"
        """
        
        response_str = call_llm(prompt)
        logger.info(f"-> Respuesta de intención del LLM: {response_str}")
        try:
            clean_response = response_str.strip().replace("```json", "").replace("```", "")
            return json.loads(clean_response)
        except (json.JSONDecodeError, TypeError):
            return {"intent": "OTRO", "entities": {}}

    def post(self, shared, _, exec_res):
        if not exec_res: return "stop"
        shared["user_intent"] = exec_res
        intent = exec_res.get("intent")
        if intent == "REGISTRAR_GASTO":
            logger.info("-> Intención detectada: REGISTRAR_GASTO")
            return "log_expense"
        elif intent == "CONSULTAR_GASTOS":
            logger.info("-> Intención detectada: CONSULTAR_GASTOS")
            return "query_expense"
        else:
            logger.info("-> Intención detectada: OTRO. Deteniendo flujo.")
            return "stop"

class ParseExpenseListNode(Node):
    def prep(self, shared):
        return {"telegram_input": shared.get("telegram_input", {}), "valid_categories": shared.get("valid_categories", ["otros"])}

    def exec(self, prep_data):
        telegram_input, valid_categories = prep_data["telegram_input"], prep_data["valid_categories"]
        message_text, user_name, chat_id = telegram_input.get("message_text"), telegram_input.get("user_name"), telegram_input.get("chat_id")
        
        if not all([message_text, user_name, chat_id]): return None
        
        logger.info(f"Nodo [ParseExpenseListNode]: Enviando texto a LLM para análisis...")
        categories_str = ", ".join(valid_categories)
        
        prompt = f"""
        Analiza el siguiente texto y extrae todos los gastos que encuentres.
        Responde únicamente con un array de objetos JSON.

        **REGLAS IMPORTANTES:**
        1.  El formato de cada objeto DEBE ser EXACTAMENTE: {{"amount": <numero>, "category": "<categoria>", "description": "<descripcion>"}}.
        2.  La clave "description" DEBE contener el detalle del gasto (ej: "supermercado changomas", "cafe con amigos").
        3.  Para la clave "category", DEBES elegir uno de los siguientes valores: [{categories_str}]. Si no encaja, usa "otros".
        4.  NO inventes claves nuevas como "currency" o "establishment".

        Texto: "{message_text}"
        """
        
        llm_response_str = call_llm(prompt)
        logger.info(f"-> Respuesta del LLM: {llm_response_str}")
        
        try:
            raw_expenses = json.loads(llm_response_str.strip().replace("```json", "").replace("```", ""))
            
            clean_expenses = []
            today_date = datetime.now().strftime("%Y-%m-%d")
            
            for expense in raw_expenses:
                clean_expense = {
                    "date": today_date,
                    "who": user_name,
                    "chat_id": chat_id,
                    "amount": expense.get("amount"),
                    "description": expense.get("description", expense.get("establishment", "Sin descripción")),
                    "category": expense.get("category", expense.get("alimentos", "otros")).lower()
                }

                if clean_expense["category"] not in valid_categories:
                    logger.warning(f"-> Categoría inválida '{clean_expense['category']}', asignando 'otros'.")
                    clean_expense["category"] = "otros"
                
                clean_expenses.append(clean_expense)

            return clean_expenses

        except (json.JSONDecodeError, TypeError):
            logger.error("-> Error: La respuesta del LLM no es un JSON válido.")
            return []

    def post(self, shared, _, exec_res):
        if exec_res: shared["parsed_expenses"] = exec_res
        return "default"

class ProcessExpenseBatchNode(BatchNode):
    def prep(self, shared):
        return shared.get("parsed_expenses", [])
    def exec(self, expense_item):
        chat_id = expense_item.get("chat_id")
        if not chat_id: return
        logger.info(f"Nodo [ProcessExpenseBatchNode]: Procesando gasto -> {expense_item['description']}")
        sheet_data = [expense_item.get(k) for k in ["date", "amount", "category", "description", "who"]]
        if not append_row(sheet_data):
            logger.error("-> Error al guardar en Google Sheets.")
            return
        confirmation_message = (f"Registrado ✅\n{expense_item.get('amount', 0.0)} PESOS\nCategoría: {expense_item.get('category', 'N/A')}\n"
                              f"Descripción: {expense_item.get('description', 'N/A')}\nFecha: {expense_item.get('date', 'N/A')}\n"
                              f"Quién: {expense_item.get('who', 'N/A')}")
        loop = asyncio.get_event_loop()
        loop.run_until_complete(send_message(chat_id, confirmation_message))
        logger.info(f"-> Confirmación enviada a {chat_id}.")

class FetchSheetDataNode(Node):
    def exec(self, _):
        logger.info("Nodo [FetchSheetDataNode]: Leyendo datos de Google Sheet...")
        records = get_all_records()
        logger.info(f"-> Se encontraron {len(records)} registros en total.")
        return records
    def post(self, shared, _, exec_res):
        shared["sheet_data"] = exec_res
        return "default"

class FormatSummaryNode(Node):
    def prep(self, shared):
        return {"records": shared.get("sheet_data", []), "intent": shared.get("user_intent", {})}
    def exec(self, prep_data):
        logger.info("Nodo [FormatSummaryNode]: Calculando y formateando resumen...")
        records = prep_data["records"]
        entities = prep_data.get("intent", {}).get("entities", {})
        if not records:
            return "No tienes gastos registrados todavía."
        today = date.today()
        title, start_date, end_date = "", None, None
        period = entities.get("period")
        if period == "hoy":
            start_date = end_date = today
            title = "Hoy"
        elif period == "ayer":
            start_date = end_date = today - timedelta(days=1)
            title = "Ayer"
        elif period == "esta_semana":
            start_date = today - timedelta(days=today.weekday())
            end_date = start_date + timedelta(days=6)
            title = "Esta Semana"
        elif period == "semana_pasada":
            end_of_last_week = today - timedelta(days=today.weekday() + 1)
            start_date = end_of_last_week - timedelta(days=6)
            end_date = end_of_last_week
            title = "la Semana Pasada"
        else:
            month_map = {"enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6, "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12}
            target_month_name = entities.get("month")
            now = datetime.now()
            target_year = now.year
            if target_month_name:
                target_month_num = month_map.get(target_month_name)
                if not target_month_num: return f"No reconozco el mes '{target_month_name}'."
            else:
                target_month_num = now.month
                target_month_name = list(month_map.keys())[list(month_map.values()).index(target_month_num)]
            title = f"{target_month_name.capitalize()} {target_year}"
            filtered_records = [r for r in records if datetime.strptime(r.get("Fecha", ""), "%Y-%m-%d").month == target_month_num and datetime.strptime(r.get("Fecha", ""), "%Y-%m-%d").year == target_year]
        if start_date and end_date:
            filtered_records = [r for r in records if start_date <= datetime.strptime(r.get("Fecha", ""), "%Y-%m-%d").date() <= end_date]
        if not filtered_records:
            return f"No se encontraron gastos para {title}."
        total_spent = sum(float(r.get('Monto', 0)) for r in filtered_records)
        by_category = defaultdict(float)
        for r in filtered_records:
            by_category[r.get('Categoria', 'sin categoria')] += float(r.get('Monto', 0))
        summary_lines = [f"📊 Resumen de Gastos para {title}", "-----------------------------------", f"💰 Total Gastado: {total_spent:,.2f} PESOS\n", " breakdown por Categoría:"]
        sorted_categories = sorted(by_category.items(), key=lambda item: item[1], reverse=True)
        for category, amount in sorted_categories:
            summary_lines.append(f"  - {category.capitalize()}: {amount:,.2f} PESOS")
        return "\n".join(summary_lines)
    def post(self, shared, _, exec_res):
        shared["summary_message"] = exec_res
        return "default"

class SendSummaryNode(Node):
    def prep(self, shared):
        return {"chat_id": shared.get("telegram_input", {}).get("chat_id"), "message": shared.get("summary_message")}
    def exec(self, prep_data):
        chat_id, message = prep_data["chat_id"], prep_data["message"]
        if not all([chat_id, message]): return
        logger.info("Nodo [SendSummaryNode]: Enviando resumen al usuario.")
        loop = asyncio.get_event_loop()
        loop.run_until_complete(send_message(chat_id, message))