import json
import asyncio
import logging
from datetime import datetime, date, timedelta
from collections import defaultdict
from pocketflow import Node, BatchNode
from utils.telegram_api import get_latest_updates, send_message
from utils.call_llm import call_llm, transcribe_audio_with_llm
from utils.gsheets_api import append_row, get_all_records, get_budgets, set_budget

logger = logging.getLogger(__name__)

def calculate_monthly_spend(category: str, all_records: list) -> float:
        """
        Calculates total spending for a category in the current month.
        """
        total = 0.0
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        for record in all_records:
            if record.get('Tipo') == 'Gasto' and record.get('Categoria', '').lower() == category:
                try:
                    record_date = datetime.strptime(record.get('Fecha', ''), "%Y-%m-%d")
                    if record_date.month == current_month and record_date.year == current_year:
                        total += float(record.get('Monto', 0))
                except (ValueError, TypeError):
                    continue
        return total

class GetMessageNode(Node):
    # Modified to handle different message types
    def exec(self, _):
        logger.debug("Node [GetMessageNode]: Fetching new messages...")
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        update_data = loop.run_until_complete(get_latest_updates())
        return update_data # This now contains the 'type' key

    def post(self, shared, _, exec_res):
        if not exec_res:
            return None # Stop if no new message
        
        shared["telegram_input"] = exec_res
        
        # Branching logic: if it's audio, go to transcribe. If text, go to detect intent.
        if exec_res.get("type") == "audio":
            logger.info("-> Message type is AUDIO. Routing to transcription.")
            return "transcribe"
        elif exec_res.get("type") == "text":
            logger.info("-> Message type is TEXT. Routing to intent detection.")
            return "detect_intent"
        
        return None
    
class TranscribeAudioNode(Node):
    def prep(self, shared):
        return shared.get("telegram_input", {}).get("audio_path")

    def exec(self, audio_path):
        if not audio_path: return None
        logger.info("Node [TranscribeAudioNode]: Transcribing audio...")
        transcribed_text = transcribe_audio_with_llm(audio_path)
        logger.info(f"-> Transcription result: '{transcribed_text}'")
        return transcribed_text

    def post(self, shared, _, exec_res):
        if exec_res:
            # CRITICAL STEP: Overwrite the telegram_input with the transcribed text
            shared["telegram_input"]["message_text"] = exec_res
            return "default" # Now, proceed to the intent detection node
        return "stop" # Stop if transcription failed

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
        Responde ÚNICAMENTE con un objeto JSON.

        Las intenciones posibles son: "REGISTRAR_GASTO", "REGISTRAR_INGRESO", "CONSULTAR_GASTOS", "DEFINIR_PRESUPUESTO", "CONSULTAR_PRESUPUESTO", "OTRO".

        Ejemplos:
        - Mensaje: "gaste 5000 en cafe" -> {{"intent": "REGISTRAR_GASTO", "entities": {{}}}}
        - Mensaje: "cargué 100000 de mi sueldo" -> {{"intent": "REGISTRAR_INGRESO", "entities": {{}}}}
        - Mensaje: "cuanto gaste hoy?" -> {{"intent": "CONSULTAR_GASTOS", "entities": {{"start_date": "{today_str}", "end_date": "{today_str}"}}}}
        - Mensaje: "fijar presupuesto de 20000 para Salidas" -> {{"intent": "DEFINIR_PRESUPUESTO", "entities": {{}}}}
        - Mensaje: "como voy con el presupuesto de alimentos" -> {{"intent": "CONSULTAR_PRESUPUESTO", "entities": {{"category": "alimentos"}}}}
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
        elif intent == "REGISTRAR_INGRESO":
            logger.info("-> Intent detected: REGISTRAR_INGRESO")
            return "log_income"
        elif intent == "CONSULTAR_GASTOS":
            logger.info("-> Intent detected: CONSULTAR_GASTOS")
            return "query_expense"
        elif intent == "DEFINIR_PRESUPUESTO":
            logger.info("-> Intent detected: DEFINIR_PRESUPUESTO")
            return "set_budget"
        elif intent == "CONSULTAR_PRESUPUESTO":
            logger.info("-> Intent detected: CONSULTAR_PRESUPUESTO")
            return "query_budget"
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
        2.  La clave "description" DEBE contener el detalle del gasto (ej: "supermercado", "cafe con amigos").
        3.  Para la clave "category", DEBES elegir uno de los siguientes valores: [{categories_str}]. Si no encaja, usa "otros".
        4.  NO inventes claves nuevas como "currency" o "establishment".

        **EJEMPLOS DE CLASIFICACIÓN:**
        - Texto: "fui al super y gaste 12000" -> [{{"amount": 12000, "category": "alimentos", "description": "supermercado"}}]
        - Texto: "2500 en un cafe con medialunas" -> [{{"amount": 2500, "category": "salidas", "description": "cafe con medialunas"}}]
        - Texto: "hice un gasto de 28000 pesos en medicamento ibupirac" -> [{{"amount": 28000, "category": "medicamentos", "description": "medicamento ibupirac"}}]
        - Texto: "cargué nafta por 15000 y 3000 de un peaje" -> [{{"amount": 15000, "category": "auto", "description": "nafta"}}, {{"amount": 3000, "category": "auto", "description": "peaje"}}]

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
                    "category": expense.get("category", expense.get("alimentos", "otros")).lower(),
                    "type": "Gasto"
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
        if exec_res: 
            shared["parsed_transactions"] = exec_res
        return "default"
    
class ParseIncomeNode(Node):
    # New node to handle income parsing
    def prep(self, shared):
        return shared.get("telegram_input", {})

    def exec(self, telegram_input):
        message_text = telegram_input.get("message_text")
        user_name = telegram_input.get("user_name")
        chat_id = telegram_input.get("chat_id")

        if not all([message_text, user_name, chat_id]): return None

        logger.info(f"Node [ParseIncomeNode]: Sending text to LLM for analysis...")
        prompt = f"""
        Analiza el siguiente texto y extrae el monto y la descripción del ingreso.
        Responde ÚNICAMENTE con un objeto JSON con las claves "amount" y "description".

        Ejemplos:
        - Texto: "cargué 150000 de mi sueldo" -> {{"amount": 150000, "description": "sueldo"}}
        - Texto: "me pagaron 20000 por el proyecto freelance" -> {{"amount": 20000, "description": "proyecto freelance"}}

        Texto a analizar: "{message_text}"
        """
        llm_response_str = call_llm(prompt)
        logger.info(f"-> LLM response: {llm_response_str}")

        try:
            raw_income = json.loads(llm_response_str.strip().replace("```json", "").replace("```", ""))
            today_date = datetime.now().strftime("%Y-%m-%d")
            
            clean_income = {
                "date": today_date, "who": user_name, "chat_id": chat_id,
                "amount": raw_income.get("amount"),
                "description": raw_income.get("description", "Sin descripción"),
                "category": "Ingreso", # Fixed category for income
                "type": "Ingreso" # Add type
            }
            return [clean_income] # Return as a list to be consistent
        except (json.JSONDecodeError, TypeError):
            logger.error("-> Error: LLM response is not valid JSON.")
            return []

    def post(self, shared, _, exec_res):
        if exec_res: shared["parsed_transactions"] = exec_res
        return "default"

class ParseBudgetNode(Node):
    # New node to extract budget details from a message
    def prep(self, shared):
        return shared.get("telegram_input", {}).get("message_text")

    def exec(self, message_text):
        if not message_text: return None
        logger.info("Node [ParseBudgetNode]: Extracting budget details...")

        prompt = f"""
        Analiza el siguiente texto y extrae la categoría y el monto para un presupuesto.
        Responde ÚNICAMENTE con un objeto JSON con las claves "category" y "amount".
        La categoría debe ser una sola palabra y en minúsculas.

        Ejemplos:
        - Texto: "Quiero fijar un presupuesto de 50000 para Alimentos" -> {{"category": "alimentos", "amount": 50000}}
        - Texto: "presupuesto para salidas: 25000" -> {{"category": "salidas", "amount": 25000}}
        - Texto: "Setea 10000 en Ocio" -> {{"category": "ocio", "amount": 10000}}

        Texto a analizar: "{message_text}"
        """
        llm_response_str = call_llm(prompt)
        logger.info(f"-> LLM budget parse response: {llm_response_str}")
        try:
            return json.loads(llm_response_str.strip().replace("```json", "").replace("```", ""))
        except (json.JSONDecodeError, TypeError):
            logger.error("-> Error: Could not parse budget details from LLM response.")
            return None

    def post(self, shared, _, exec_res):
        if exec_res and "category" in exec_res and "amount" in exec_res:
            shared["budget_details"] = exec_res
            return "default"
        # If parsing fails, we'll just stop the flow for this action
        return "stop"

class SetBudgetNode(Node):
    # New node to save the parsed budget to the Google Sheet
    def prep(self, shared):
        return {
            "budget_details": shared.get("budget_details"),
            "chat_id": shared.get("telegram_input", {}).get("chat_id")
        }

    def exec(self, prep_data):
        budget_details = prep_data.get("budget_details")
        chat_id = prep_data.get("chat_id")

        if not all([budget_details, chat_id]):
            return "Error: Faltan datos para registrar el presupuesto."

        category = budget_details["category"]
        amount = budget_details["amount"]

        logger.info(f"Node [SetBudgetNode]: Setting budget for '{category}'...")
        success = set_budget(category.capitalize(), float(amount)) # Capitalize for consistency in the sheet

        if success:
            message = f"✅ Presupuesto actualizado!\nCategoría: {category.capitalize()}\nMonto Máximo: {float(amount):,.2f} PESOS"
        else:
            message = "❌ Hubo un error al guardar tu presupuesto. Inténtalo de nuevo."
        
        # Send confirmation message
        loop = asyncio.get_event_loop()
        loop.run_until_complete(send_message(chat_id, message))
        return "done"

class QueryBudgetNode(Node):
    def prep(self, shared):
        return {
            "user_intent": shared.get("user_intent", {}),
            "chat_id": shared.get("telegram_input", {}).get("chat_id")
        }

    def exec(self, prep_data):
        user_intent = prep_data.get("user_intent")
        chat_id = prep_data.get("chat_id")

        if not all([user_intent, chat_id]):
            return "Error: Faltan datos para consultar el presupuesto."

        category = user_intent.get("entities", {}).get("category")
        if not category:
            return "No entendí para qué categoría quieres consultar el presupuesto. Inténtalo de nuevo, por ejemplo: '¿cuánto me queda para alimentos?'"

        logger.info(f"Node [QueryBudgetNode]: Querying budget for category '{category}'...")
        
        budgets = get_budgets()
        budget_amount = budgets.get(category.lower())

        if not budget_amount:
            return f"No tienes un presupuesto definido para la categoría '{category.capitalize()}'."

        all_records = get_all_records("Gastos")
        spent_amount = calculate_monthly_spend(category.lower(), all_records)
        remaining_amount = budget_amount - spent_amount
        
        percentage = (spent_amount / budget_amount) * 100 if budget_amount > 0 else 0

        message = (
            f"📊 **Estado de tu Presupuesto para '{category.capitalize()}'**\n"
            f"-----------------------------------\n"
            f" Límite Mensual: {budget_amount:,.2f} PESOS\n"
            f" Total Gastado: {spent_amount:,.2f} PESOS ({percentage:.1f}%)\n"
            f"-----------------------------------\n"
            f" **Te quedan: {remaining_amount:,.2f} PESOS**"
        )
        
        loop = asyncio.get_event_loop()
        loop.run_until_complete(send_message(chat_id, message))
        return "done"

    def post(self, shared, _, exec_res):
        # This node sends its own message, so it's an endpoint.
        return "stop"

class ProcessTransactionBatchNode(BatchNode):
    # Updated with improved budget alert logic
    def prep(self, shared):
        return shared.get("parsed_transactions", [])

    def exec(self, transaction_item):
        chat_id = transaction_item.get("chat_id")
        if not chat_id: return

        logger.info(f"Node [ProcessTransactionBatchNode]: Processing transaction -> {transaction_item['description']}")
        sheet_data = [transaction_item.get(k) for k in ["date", "amount", "category", "description", "who", "type"]]
        
        if not append_row(sheet_data):
            logger.error("-> Error saving to Google Sheets.")
            return

        trans_type = transaction_item.get("type", "Gasto")
        if trans_type == "Gasto":
            confirmation_message = (f"Gasto Registrado ✅\n"
                                  f"Monto: {transaction_item.get('amount', 0.0)} PESOS\n"
                                  f"Categoría: {transaction_item.get('category', 'N/A')}")
        else:
            confirmation_message = (f"Ingreso Registrado 💸\n"
                                  f"Monto: {transaction_item.get('amount', 0.0)} PESOS\n"
                                  f"Descripción: {transaction_item.get('description', 'N/A')}")
        
        loop = asyncio.get_event_loop()
        loop.run_until_complete(send_message(chat_id, confirmation_message))
        logger.info(f"-> Confirmation sent to {chat_id}.")

        if trans_type == "Gasto":
            category = transaction_item.get("category", "").lower()
            current_amount = float(transaction_item.get("amount", 0))
            
            budgets = get_budgets()
            budget_amount = budgets.get(category)

            if budget_amount:
                logger.info(f"-> Budget found for '{category}': {budget_amount}. Checking status...")
                
                all_records = get_all_records("Gastos")
                total_spent_this_month = calculate_monthly_spend(category, all_records)
                spent_before_this = total_spent_this_month - current_amount
                
                # Add logging to see the numbers
                logger.info(f"-> Budget Check: Spent before={spent_before_this}, Spent now={total_spent_this_month}, Budget={budget_amount}")
                
                percentage_before = (spent_before_this / budget_amount) * 100 if budget_amount > 0 else 0
                percentage_after = (total_spent_this_month / budget_amount) * 100 if budget_amount > 0 else 0
                
                alert_message = None
                
                # Case 1: You just crossed 100%
                if percentage_after >= 100 and percentage_before < 100:
                    alert_message = (f"🚨 ¡Alerta de Presupuesto! 🚨\n"
                                     f"Acabas de superar el 100% de tu presupuesto para '{category.capitalize()}'.\n"
                                     f"Gastado este mes: {total_spent_this_month:,.2f} de {budget_amount:,.2f} PESOS.")
                # Case 2: You were already over 100% and are spending more
                elif percentage_after > 100 and percentage_before >= 100:
                    alert_message = (f"🚨 ¡Sigues por encima del presupuesto! 🚨\n"
                                     f"Nuevo gasto en '{category.capitalize()}' mientras estás sobre el límite.\n"
                                     f"Gastado este mes: {total_spent_this_month:,.2f} de {budget_amount:,.2f} PESOS.")
                # Case 3: You just crossed 85%
                elif percentage_after >= 85 and percentage_before < 85:
                    alert_message = (f"⚠️ ¡Atención! ⚠️\n"
                                     f"Ya has utilizado más del 85% de tu presupuesto para '{category.capitalize()}'.\n"
                                     f"Gastado este mes: {total_spent_this_month:,.2f} de {budget_amount:,.2f} PESOS.")
                
                if alert_message:
                    logger.info(f"-> Sending budget alert to {chat_id}.")
                    loop.run_until_complete(send_message(chat_id, alert_message))

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
    # Updated to include a detailed income breakdown in the summary
    def prep(self, shared):
        return {"records": shared.get("sheet_data", []), "intent": shared.get("user_intent", {})}

    def exec(self, prep_data):
        logger.info("Node [FormatSummaryNode]: Calculating and formatting summary...")
        records = prep_data["records"]
        entities = prep_data.get("intent", {}).get("entities", {})
        
        if not records:
            return "No tienes transacciones registradas todavía."

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

        # Filter records by date
        date_filtered_records = [
            r for r in records 
            if r.get("Fecha") and start_date <= datetime.strptime(r["Fecha"], "%Y-%m-%d").date() <= end_date
        ]

        if not date_filtered_records:
            return f"No se encontraron transacciones {title}."

        # Separate expenses and income
        expense_records = [r for r in date_filtered_records if r.get('Tipo') == 'Gasto']
        income_records = [r for r in date_filtered_records if r.get('Tipo') == 'Ingreso']

        # Calculate totals
        total_spent = sum(float(r.get('Monto', 0)) for r in expense_records)
        total_earned = sum(float(r.get('Monto', 0)) for r in income_records)
        balance = total_earned - total_spent

        # Build the summary message
        summary_lines = [f"📊 Resumen de Finanzas {title}", "-----------------------------------"]
        summary_lines.append(f"💸 Total Ingresado: {total_earned:,.2f} PESOS")
        summary_lines.append(f"💰 Total Gastado: {total_spent:,.2f} PESOS")
        summary_lines.append(f"⚖️ Balance Final: {balance:,.2f} PESOS\n")

        # Income Breakdown
        if income_records:
            summary_lines.append("Detalle de Ingresos:")
            by_source = defaultdict(float)
            for r in income_records:
                by_source[r.get('Descripcion', 'sin descripcion')] += float(r.get('Monto', 0))
            
            sorted_sources = sorted(by_source.items(), key=lambda item: item[1], reverse=True)
            for source, amount in sorted_sources:
                summary_lines.append(f"  - {source.capitalize()}: {amount:,.2f} PESOS")
            summary_lines.append("") # Add a blank line for spacing
        
        # Expense Breakdown
        if expense_records:
            summary_lines.append("Detalle de Gastos por Categoría:")
            by_category = defaultdict(float)
            for r in expense_records:
                by_category[r.get('Categoria', 'sin categoria')] += float(r.get('Monto', 0))
            
            sorted_categories = sorted(by_category.items(), key=lambda item: item[1], reverse=True)
            for category, amount in sorted_categories:
                summary_lines.append(f"  - {category.capitalize()}: {amount:,.2f} PESOS")
        else:
            summary_lines.append("No se registraron gastos en este período.")
            
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