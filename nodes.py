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
        # Fetching new messages...
        logger.debug("Node [GetMessageNode]: Fetching new messages...")
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        update_data = loop.run_until_complete(get_latest_updates())
        if update_data:
            logger.info(f"-> Message received from '{update_data['user_name']}': {update_data['message_text']}")
        return update_data
    def post(self, shared, _, exec_res):
        if exec_res:
            shared["telegram_input"] = exec_res
            # Continue to the next node
            return "default"
        # Stop if no new message
        return None

class DetectIntentNode(Node):
    def prep(self, shared):
        return shared.get("telegram_input", {}).get("message_text")

    def exec(self, message_text):
        if not message_text: return None
        logger.info("Node [DetectIntentNode]: Classifying user intent...")
        
        today_str = datetime.now().strftime("%Y-%m-%d")

        prompt = f"""
        Analiza el mensaje del usuario y clasifica su intención.
        La fecha de hoy es {today_str}.
        Responde ÚNICAMENTE con un objeto JSON que tenga las claves "intent" y "entities".

        Las intenciones posibles son: "REGISTRAR_GASTO", "CONSULTAR_GASTOS", "OTRO".

        Si la intención es "CONSULTAR_GASTOS", extrae el período de tiempo en la clave "entities".
        Las entidades deben contener "start_date" y "end_date" en formato "YYYY-MM-DD".

        **REGLAS IMPORTANTES PARA FECHAS:**
        - "hoy" significa que start_date y end_date son {today_str}.
        - "ayer" significa que ambas fechas son la fecha de ayer.
        - "esta semana" significa desde el último lunes hasta el próximo domingo.
        - "la semana pasada" significa desde el lunes hasta el domingo de la semana anterior.
        - Si se menciona un mes (ej: "gastos de mayo"), calcula las fechas de inicio y fin para ese mes en el año actual.

        Ejemplos:
        - Mensaje: "gaste 5000 en cafe" -> {{"intent": "REGISTRAR_GASTO", "entities": {{}}}}
        - Mensaje: "cuanto gaste hoy?" -> {{"intent": "CONSULTAR_GASTOS", "entities": {{"start_date": "{today_str}", "end_date": "{today_str}"}}}}
        - Mensaje: "resumen de ayer" -> {{"intent": "CONSULTAR_GASTOS", "entities": {{"start_date": "{(datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')}", "end_date": "{(datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')}"}}}}
        - Mensaje: "hola" -> {{"intent": "OTRO", "entities": {{}}}}

        Mensaje a analizar: "{message_text}"
        """
        
        response_str = call_llm(prompt)
        logger.info(f"-> LLM intent response: {response_str}")
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
            logger.info("-> Intent detected: REGISTRAR_GASTO")
            return "log_expense"
        elif intent == "CONSULTAR_GASTOS":
            logger.info("-> Intent detected: CONSULTAR_GASTOS")
            return "query_expense"
        else:
            logger.info("-> Intent detected: OTRO. Stopping flow.")
            return "stop"

class ParseExpenseListNode(Node):
    def prep(self, shared):
        return {"telegram_input": shared.get("telegram_input", {}), "valid_categories": shared.get("valid_categories", ["otros"])}

    def exec(self, prep_data):
        telegram_input, valid_categories = prep_data["telegram_input"], prep_data["valid_categories"]
        message_text, user_name, chat_id = telegram_input.get("message_text"), telegram_input.get("user_name"), telegram_input.get("chat_id")
        
        if not all([message_text, user_name, chat_id]): return None
        
        logger.info(f"Node [ParseExpenseListNode]: Sending text to LLM for analysis...")
        categories_str = ", ".join(valid_categories)
        
        prompt = f"""
        Analiza el siguiente texto y extrae todos los gastos que encuentres.
        Responde ÚNICAMENTE con un array de objetos JSON.

        **REGLAS IMPORTANTES:**
        1.  El formato de cada objeto DEBE ser EXACTAMENTE: {{"amount": <numero>, "category": "<categoria>", "description": "<descripcion>"}}.
        2.  La clave "description" DEBE contener el detalle del gasto (ej: "supermercado changomas", "cafe con amigos").
        3.  Para la clave "category", DEBES elegir uno de los siguientes valores: [{categories_str}]. Si no encaja, usa "otros".
        4.  NO inventes claves nuevas como "currency" o "establishment".

        Texto a analizar: "{message_text}"
        """
        
        llm_response_str = call_llm(prompt)
        logger.info(f"-> LLM response: {llm_response_str}")
        
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
                    logger.warning(f"-> Invalid category '{clean_expense['category']}', assigning 'otros'.")
                    clean_expense["category"] = "otros"
                
                clean_expenses.append(clean_expense)

            return clean_expenses

        except (json.JSONDecodeError, TypeError):
            logger.error("-> Error: LLM response is not valid JSON.")
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
        logger.info(f"Node [ProcessExpenseBatchNode]: Processing expense -> {expense_item['description']}")
        sheet_data = [expense_item.get(k) for k in ["date", "amount", "category", "description", "who"]]
        if not append_row(sheet_data):
            logger.error("-> Error saving to Google Sheets.")
            return
        confirmation_message = (f"Registrado ✅\n{expense_item.get('amount', 0.0)} PESOS\nCategoría: {expense_item.get('category', 'N/A')}\n"
                              f"Descripción: {expense_item.get('description', 'N/A')}\nFecha: {expense_item.get('date', 'N/A')}\n"
                              f"Quién: {expense_item.get('who', 'N/A')}")
        loop = asyncio.get_event_loop()
        loop.run_until_complete(send_message(chat_id, confirmation_message))
        logger.info(f"-> Confirmation sent to {chat_id}.")

class FetchSheetDataNode(Node):
    def exec(self, _):
        logger.info("Node [FetchSheetDataNode]: Reading data from Google Sheet...")
        records = get_all_records()
        logger.info(f"-> Found {len(records)} total records.")
        return records
    def post(self, shared, _, exec_res):
        shared["sheet_data"] = exec_res
        return "default"

class FormatSummaryNode(Node):
    def prep(self, shared):
        return {"records": shared.get("sheet_data", []), "intent": shared.get("user_intent", {})}
    def exec(self, prep_data):
        logger.info("Node [FormatSummaryNode]: Calculating and formatting summary...")
        records = prep_data["records"]
        entities = prep_data.get("intent", {}).get("entities", {})
        
        if not records:
            return "No tienes gastos registrados todavía."

        start_date_str = entities.get("start_date")
        end_date_str = entities.get("end_date")

        if not all([start_date_str, end_date_str]):
            return "No pude entender el rango de fechas. Por favor, intenta de nuevo."

        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            return "El formato de fecha que recibí era inválido. Intenta de nuevo."

        title = f"del {start_date_str} al {end_date_str}"
        if start_date == end_date:
            title = f"para el {start_date_str}"

        filtered_records = [
            r for r in records 
            if r.get("Fecha") and start_date <= datetime.strptime(r["Fecha"], "%Y-%m-%d").date() <= end_date
        ]

        if not filtered_records:
            return f"No se encontraron gastos {title}."

        total_spent = sum(float(r.get('Monto', 0)) for r in filtered_records)
        by_category = defaultdict(float)
        for r in filtered_records:
            by_category[r.get('Categoria', 'sin categoria')] += float(r.get('Monto', 0))
        
        summary_lines = [f"📊 Resumen de Gastos {title}", "-----------------------------------", f"💰 Total Gastado: {total_spent:,.2f} PESOS\n", "Detalle por Categoría:"]
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
        logger.info("Node [SendSummaryNode]: Sending summary to the user.")
        loop = asyncio.get_event_loop()
        loop.run_until_complete(send_message(chat_id, message))