import json
import asyncio
import os
import logging
from datetime import datetime, date, timedelta
from collections import defaultdict
from pocketflow import Node, BatchNode
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from utils.telegram_api import get_latest_updates, send_message, send_document
from utils.call_llm import call_llm, transcribe_audio_with_llm, analyze_image_with_llm
from utils.gsheets_api import (
    append_row,
    get_all_records,
    get_budgets,
    set_budget,
    add_category,
    find_last_row_by_user,
    update_row,
    delete_row,
)
from utils.prompts import (
    get_detect_intent_prompt,
    get_edit_expense_prompt,
    get_add_category_prompt,
    get_parse_expense_prompt,
    get_parse_income_prompt,
    get_parse_budget_prompt,
    get_monthly_analysis_prompt,
    get_analyze_receipt_prompt,
)

logger = logging.getLogger(__name__)


def calculate_monthly_spend(category: str, all_records: list) -> float:
    """
    Calculates total spending for a category in the current month.
    """
    total = 0.0
    current_month = datetime.now().month
    current_year = datetime.now().year

    for record in all_records:
        if (
            record.get("Tipo") == "Gasto"
            and record.get("Categoria", "").lower() == category.lower()
        ):
            try:
                record_date = datetime.strptime(record.get("Fecha", ""), "%Y-%m-%d")
                if (
                    record_date.month == current_month
                    and record_date.year == current_year
                ):
                    total += float(record.get("Monto", 0))
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
        return update_data

    def post(self, shared, _, exec_res):
        if not exec_res:
            return None

        shared["telegram_input"] = exec_res
        msg_type = exec_res.get("type")

        if msg_type == "audio":
            logger.info("-> Message type is AUDIO. Routing to transcription.")
            return "transcribe"
        elif msg_type == "text":
            logger.info("-> Message type is TEXT. Routing to intent detection.")
            return "detect_intent"
        elif msg_type == "photo":
            logger.info("-> Message type is PHOTO. Routing to receipt analysis.")
            return "analyze_receipt"

        return None


class AnalyzeReceiptNode(Node):
    def prep(self, shared):
        return {
            "photo_path": shared.get("telegram_input", {}).get("photo_path"),
            "valid_categories": shared.get("valid_categories", ["otros"]),
        }

    def exec(self, prep_data):
        photo_path = prep_data.get("photo_path")
        valid_categories = prep_data.get("valid_categories")

        if not photo_path:
            return None

        logger.info("Node [AnalyzeReceiptNode]: Analyzing receipt image...")
        categories_str = ", ".join(valid_categories)

        prompt = get_analyze_receipt_prompt(categories_str)

        response_str = analyze_image_with_llm(photo_path, prompt)
        logger.info(f"-> LLM receipt response: {response_str}")

        try:
            if os.path.exists(photo_path):
                os.remove(photo_path)
        except Exception as e:
            logger.warning(f"Could not delete temp file {photo_path}: {e}")

        try:
            clean_response = (
                response_str.strip().replace("```json", "").replace("```", "")
            )
            parsed_items = json.loads(clean_response)

            for item in parsed_items:
                raw_cat = item.get("category", "otros")
                item["category"] = normalize_category(raw_cat, valid_categories)
            return parsed_items

        except (json.JSONDecodeError, TypeError):
            logger.error("-> Error parsing JSON from image analysis.")
            return []

    def post(self, shared, _, exec_res):
        if exec_res:
            user_data = shared.get("telegram_input", {})
            enriched_transactions = []
            today = datetime.now().strftime("%Y-%m-%d")

            for item in exec_res:
                item.update(
                    {
                        "date": today,
                        "who": user_data.get("user_name"),
                        "chat_id": user_data.get("chat_id"),
                        "type": "Gasto",
                    }
                )
                enriched_transactions.append(item)

            shared["parsed_transactions"] = enriched_transactions
            return "default"

        return "fallback"


class TranscribeAudioNode(Node):
    def prep(self, shared):
        return shared.get("telegram_input", {}).get("audio_path")

    def exec(self, audio_path):
        if not audio_path:
            return None
        logger.info("Node [TranscribeAudioNode]: Transcribing audio...")
        transcribed_text = transcribe_audio_with_llm(audio_path)
        logger.info(f"-> Transcription result: '{transcribed_text}'")
        return transcribed_text

    def post(self, shared, prep_res, exec_res):
        if exec_res is not None:
            # Store transcribed text so DetectIntentNode can process it
            shared["telegram_input"]["message_text"] = exec_res
        return "detect_intent"


class DetectIntentNode(Node):
    def prep(self, shared):
        return shared.get("telegram_input", {}).get("message_text")

    def exec(self, message_text):
        if not message_text:
            return None
        logger.info("Node [DetectIntentNode]: Classifying user intent...")

        today_str = datetime.now().strftime("%Y-%m-%d")

        prompt = get_detect_intent_prompt(today_str, message_text)

        response_str = call_llm(prompt)
        logger.info(f"-> LLM intent response: {response_str}")
        try:
            clean_response = (
                response_str.strip().replace("```json", "").replace("```", "")
            )
            return json.loads(clean_response)
        except (json.JSONDecodeError, TypeError):
            return {"intent": "OTRO", "entities": {}}

    def post(self, shared, _, exec_res):
        if not exec_res:
            return None
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
        elif intent == "AGREGAR_CATEGORIA":
            logger.info("-> Intent detected: AGREGAR_CATEGORIA")
            return "add_category"
        elif intent == "CONSULTAR_GASTOS_POR_CATEGORIA":
            logger.info("-> Intent detected: CONSULTAR_GASTOS_POR_CATEGORIA")
            return "query_by_category"
        elif intent == "PEDIR_AYUDA":
            logger.info("-> Intent detected: PEDIR_AYUDA")
            return "show_help"
        elif intent == "EDITAR_ULTIMO_GASTO":
            logger.info("-> Intent detected: EDITAR_ULTIMO_GASTO")
            return "edit_last"
        elif intent == "ELIMINAR_ULTIMO_GASTO":
            logger.info("-> Intent detected: ELIMINAR_ULTIMO_GASTO")
            return "delete_last"
        else:
            logger.info("-> Intent detected: OTRO. Routing to fallback.")
            return "fallback"


def normalize_category(input_category: str, valid_categories: list[str]) -> str:
    """
    Looks for a match in the list of valid categories, ignoring case.
    1. If no match is found, returns the input in lowercase.
    2. If the input is empty, returns "otros".
    """
    if not input_category:
        return "otros"

    input_clean = input_category.strip().lower()

    for valid in valid_categories:
        if valid.strip().lower() == input_clean:
            return valid

    return input_clean


def parse_relative_date(date_str: str) -> str:
    """
    Parse relative date strings to YYYY-MM-DD format.
    Handles: "today", "yesterday", "2daysago", "3daysago", etc.
    Also handles day names like "monday", "tuesday", etc.
    """
    if not date_str:
        return datetime.now().strftime("%Y-%m-%d")

    date_str = date_str.lower().strip()
    today = date.today()

    # Handle "today"
    if date_str == "today":
        return today.strftime("%Y-%m-%d")

    # Handle "yesterday"
    if date_str == "yesterday":
        yesterday = today - timedelta(days=1)
        return yesterday.strftime("%Y-%m-%d")

    # Handle "Xdaysago" patterns
    if "daysago" in date_str or "days ago" in date_str:
        try:
            # Extract number: "2daysago" -> 2, "3 days ago" -> 3
            num_str = (
                date_str.replace("daysago", "").replace("days ago", "").replace(" ", "")
            )
            days = int(num_str)
            target_date = today - timedelta(days=days)
            return target_date.strftime("%Y-%m-%d")
        except (ValueError, AttributeError):
            pass

    # Handle day names (monday, tuesday, etc.)
    day_map = {
        "monday": 0,
        "lunes": 0,
        "tuesday": 1,
        "martes": 1,
        "wednesday": 2,
        "miercoles": 2,
        "thursday": 3,
        "jueves": 3,
        "friday": 4,
        "viernes": 4,
        "saturday": 5,
        "sabado": 5,
        "sunday": 6,
        "domingo": 6,
    }

    for day_name, day_num in day_map.items():
        if day_name in date_str:
            # Calculate days to subtract to reach that day
            current_day = today.weekday()
            days_to_subtract = (current_day - day_num) % 7
            if days_to_subtract == 0:
                # If it's the same day, assume last week
                days_to_subtract = 7
            target_date = today - timedelta(days=days_to_subtract)
            return target_date.strftime("%Y-%m-%d")

    # Try parsing as YYYY-MM-DD directly
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return date_str
    except ValueError:
        pass

    # Default to today if nothing works
    return today.strftime("%Y-%m-%d")


class HelpNode(Node):
    """
    Sends a comprehensive help message listing all bot features.
    """

    def prep(self, shared):
        return shared.get("telegram_input", {}).get("chat_id")

    def exec(self, chat_id):
        if not chat_id:
            return {"message": "Error: chat_id not found."}

        help_text = """
            *¡Hola! Soy tu asistente de finanzas. Esto es todo lo que puedo hacer por vos:*

            *1. Registrar Transacciones (Texto o Voz)*
            - `gaste 5000 en cafe y 12000 en el super`
            - `cobre 150000 de mi sueldo`

            *2. Consultar Resúmenes*
            - `resumen de esta semana`
            - `resumen del mes pasado`

            *3. Gestionar Presupuestos*
            - `fijar presupuesto de 80000 para alimentos`
            - `cuanto me queda para salidas?`

            *4. Consultas Detalladas*
            - `cuales fueron mis gastos en auto este mes?`
            - `mostrame los gastos de ropa y ocio de la semana pasada`

            *5. Personalizar Categorías*
            - `agrega la categoria Gimnasio`
            - `añade las categorias Inversiones y Viajes`

            _Puedes usar texto o mensajes de voz para la mayoría de los comandos._
            """

        keyboard = [
            [
                InlineKeyboardButton(
                    "📊 Pedir Resumen de Hoy", callback_data="resumen de hoy"
                )
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        return {"message": help_text, "chat_id": chat_id, "reply_markup": reply_markup}

    def post(self, shared, _, exec_res):
        chat_id = exec_res.get("chat_id")
        message = exec_res.get("message")
        reply_markup = exec_res.get("reply_markup")
        if chat_id and message:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(send_message(chat_id, message, reply_markup))
        return None


class FallbackNode(Node):
    """
    Handles cases where the bot doesn't understand the user's intent.
    """

    def prep(self, shared):
        return shared.get("telegram_input", {}).get("chat_id")

    def exec(self, chat_id):
        if not chat_id:
            return {"message": "Error: chat_id not found."}

        fallback_text = """
            😕 No entendí tu mensaje.

            Recuerda que puedes registrar gastos, ingresos o pedir resúmenes.

            *Por ejemplo, puedes intentar con:*
            - `gaste 1500 en un cafe`
            - `resumen de hoy`
            - `cuanto me queda para alimentos?`
            """
        keyboard = [
            [InlineKeyboardButton("❓ Ver todos los comandos", callback_data="ayuda")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        return {
            "message": fallback_text,
            "chat_id": chat_id,
            "reply_markup": reply_markup,
        }

    def post(self, shared, _, exec_res):
        chat_id = exec_res.get("chat_id")
        message = exec_res.get("message")
        reply_markup = exec_res.get("reply_markup")
        if chat_id and message:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(send_message(chat_id, message, reply_markup))
        return None


class DeleteLastExpenseNode(Node):
    def prep(self, shared):
        return {
            "user_name": shared.get("telegram_input", {}).get("user_name"),
            "chat_id": shared.get("telegram_input", {}).get("chat_id"),
        }

    def exec(self, prep_data):
        user_name = prep_data.get("user_name")
        chat_id = prep_data.get("chat_id")
        if not all([user_name, chat_id]):
            return {"message": "Error: No pude identificarte."}

        logger.info(
            f"Node [DeleteLastExpenseNode]: Finding last expense for user '{user_name}'..."
        )
        last_expense = find_last_row_by_user(user_name)

        if not last_expense:
            return {
                "message": "No encontré gastos recientes registrados por ti.",
                "chat_id": chat_id,
            }

        row_to_delete = last_expense["row_number"]
        deleted_data = last_expense["data"]
        success = delete_row(row_to_delete)

        if success:
            message = (
                f"🗑️ Gasto eliminado con éxito:\n"
                f"  - Descripción: {deleted_data.get('Descripcion')}\n"
                f"  - Monto: {deleted_data.get('Monto')}"
            )
        else:
            message = "❌ Hubo un error al intentar eliminar el último gasto."

        return {"message": message, "chat_id": chat_id}

    def post(self, shared, _, exec_res):
        chat_id = exec_res.get("chat_id")
        message = exec_res.get("message")
        if chat_id and message:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(send_message(chat_id, message))
        return None


class EditLastExpenseNode(Node):
    def prep(self, shared):
        return {
            "user_name": shared.get("telegram_input", {}).get("user_name"),
            "chat_id": shared.get("telegram_input", {}).get("chat_id"),
            "message_text": shared.get("telegram_input", {}).get("message_text"),
            "valid_categories": shared.get("valid_categories", []),
        }

    def exec(self, prep_data):
        user_name, chat_id, message_text, valid_categories = (
            prep_data["user_name"],
            prep_data["chat_id"],
            prep_data["message_text"],
            prep_data["valid_categories"],
        )
        if not all([user_name, chat_id, message_text]):
            return {"message": "Error: Faltan datos para la edición."}

        logger.info(
            f"Node [EditLastExpenseNode]: Finding last expense for user '{user_name}'..."
        )
        last_expense = find_last_row_by_user(user_name)

        if not last_expense:
            return {
                "message": "No encontré gastos recientes para editar.",
                "chat_id": chat_id,
            }

        row_to_edit = last_expense["row_number"]
        original_data = last_expense["data"]
        categories_str = ", ".join(valid_categories)

        prompt = get_edit_expense_prompt(categories_str, message_text)

        llm_response_str = call_llm(prompt)
        logger.info(f"-> LLM edit parse response: {llm_response_str}")

        try:
            updates = json.loads(
                llm_response_str.strip().replace("```json", "").replace("```", "")
            )
            if not updates:
                return {
                    "message": "No entendí qué querías cambiar. Intenta de nuevo, por ejemplo: 'cambia el monto a 5000'.",
                    "chat_id": chat_id,
                }

            update_for_sheet = {}
            if "amount" in updates:
                update_for_sheet["Monto"] = updates["amount"]
            if "category" in updates:
                update_for_sheet["Categoria"] = normalize_category(
                    updates["category"], valid_categories
                )
            if "description" in updates:
                update_for_sheet["Descripcion"] = updates["description"]

            success = update_row(row_to_edit, update_for_sheet)

            if success:
                message = "✏️ Gasto actualizado con éxito!\n\n*Antes:*\n"
                message += f"  - Desc: {original_data.get('Descripcion')}, Monto: {original_data.get('Monto')}, Cat: {original_data.get('Categoria')}\n"
                message += "\n*Ahora:*\n"
                new_desc = update_for_sheet.get(
                    "Descripcion", original_data.get("Descripcion")
                )
                new_monto = update_for_sheet.get("Monto", original_data.get("Monto"))
                new_cat = update_for_sheet.get(
                    "Categoria", original_data.get("Categoria")
                )
                message += f"  - Desc: {new_desc}, Monto: {new_monto}, Cat: {new_cat}"
            else:
                message = "❌ Hubo un error al intentar actualizar el gasto."

            return {"message": message, "chat_id": chat_id}
        except (json.JSONDecodeError, TypeError):
            return {
                "message": "Hubo un error procesando tu solicitud de edición.",
                "chat_id": chat_id,
            }

    def post(self, shared, _, exec_res):
        chat_id = exec_res.get("chat_id")
        message = exec_res.get("message")
        if chat_id and message:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(send_message(chat_id, message))
        return None


class QueryExpensesByCategoryNode(Node):
    def prep(self, shared):
        return {
            "user_intent": shared.get("user_intent", {}),
            "chat_id": shared.get("telegram_input", {}).get("chat_id"),
        }

    def exec(self, prep_data):
        user_intent = prep_data.get("user_intent")
        chat_id = prep_data.get("chat_id")
        if not all([user_intent, chat_id]):
            return {"message": "Error: Faltan datos para la consulta."}

        entities = user_intent.get("entities", {})
        categories_to_query = entities.get("categories")
        start_date_str = entities.get("start_date")
        end_date_str = entities.get("end_date")

        if not all([categories_to_query, start_date_str, end_date_str]):
            return {
                "message": "No entendí qué categorías o qué período de tiempo quieres consultar. Inténtalo de nuevo.",
                "chat_id": chat_id,
            }

        logger.info(
            f"Node [QueryExpensesByCategoryNode]: Querying for categories {categories_to_query} from {start_date_str} to {end_date_str}..."
        )

        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            return {
                "message": "Recibí un formato de fecha inválido. Por favor, intenta de nuevo.",
                "chat_id": chat_id,
            }

        all_records = get_all_records("Gastos")

        date_filtered_records = [
            r
            for r in all_records
            if r.get("Fecha")
            and start_date
            <= datetime.strptime(r["Fecha"], "%Y-%m-%d").date()
            <= end_date
        ]

        logger.debug(
            f"Found {len(date_filtered_records)} records after date filtering: {date_filtered_records}"
        )

        final_records = [
            r
            for r in date_filtered_records
            if r.get("Tipo") == "Gasto"
            and r.get("Categoria", "").strip().lower() in categories_to_query
        ]

        title_period = f"del {start_date_str} al {end_date_str}"
        if start_date_str == end_date_str:
            title_period = f"el día {start_date_str}"

        if not final_records:
            message = f"No se encontraron gastos para las categorías {', '.join(categories_to_query)} durante el período {title_period}."
            return {"message": message, "chat_id": chat_id}

        total_spent = sum(float(r.get("Monto", 0)) for r in final_records)

        grouped_expenses = defaultdict(list)
        for r in final_records:
            category_key = r.get("Categoria", "Sin Categoria").strip().capitalize()
            grouped_expenses[category_key].append(
                f"  - {r.get('Fecha')}: {r.get('Descripcion')} - ${float(r.get('Monto', 0)):,.2f}"
            )

        message_lines = [
            f"🔎 Detalle de Gastos para {', '.join(c.capitalize() for c in categories_to_query)} ({title_period}):\n"
        ]

        for category, expenses in grouped_expenses.items():
            message_lines.append(f"**{category}:**")
            message_lines.extend(expenses)

        message_lines.append("\n-----------------------------------")
        message_lines.append(f"💰 **Total Gastado:** ${total_spent:,.2f} PESOS")

        return {"message": "\n".join(message_lines), "chat_id": chat_id}

    def post(self, shared, _, exec_res):
        chat_id = exec_res.get("chat_id")
        message = exec_res.get("message")
        if chat_id and message:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(send_message(chat_id, message))
        return None


class AddCategoryNode(Node):
    def prep(self, shared):
        return {
            "message_text": shared.get("telegram_input", {}).get("message_text"),
            "chat_id": shared.get("telegram_input", {}).get("chat_id"),
        }

    def exec(self, prep_data):
        message_text = prep_data.get("message_text")
        chat_id = prep_data.get("chat_id")
        if not all([message_text, chat_id]):
            return {"message": "Error: Missing data to add categories."}

        logger.info("Node [AddCategoryNode]: Parsing new category names...")

        prompt = get_add_category_prompt(message_text)

        llm_response_str = call_llm(prompt)
        logger.info(f"-> LLM category parse response: {llm_response_str}")

        try:
            parsed_data = json.loads(
                llm_response_str.strip().replace("```json", "").replace("```", "")
            )
            category_names = parsed_data.get("category_names")

            if not category_names or not isinstance(category_names, list):
                return {
                    "message": "No pude identificar ninguna categoría nueva para agregar."
                }

            added_categories = []
            existing_categories = []

            for name in category_names:
                if add_category(name):
                    added_categories.append(name.capitalize())
                else:
                    existing_categories.append(name.capitalize())

            response_parts = []
            if added_categories:
                response_parts.append(
                    f"✅ Categorías agregadas: {', '.join(added_categories)}."
                )
            if existing_categories:
                response_parts.append(
                    f"⚠️ Estas categorías ya existían: {', '.join(existing_categories)}."
                )

            message = "\n".join(response_parts)
            return {"message": message, "chat_id": chat_id}

        except (json.JSONDecodeError, TypeError):
            return {
                "message": "Hubo un error procesando tu solicitud.",
                "chat_id": chat_id,
            }

    def post(self, shared, _, exec_res):
        chat_id = exec_res.get("chat_id")
        message = exec_res.get("message")
        if chat_id and message:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(send_message(chat_id, message))

        return None


class ParseExpenseListNode(Node):
    def prep(self, shared):
        return {
            "telegram_input": shared.get("telegram_input", {}),
            "valid_categories": shared.get("valid_categories", ["otros"]),
        }

    def exec(self, prep_data):
        telegram_input, valid_categories = (
            prep_data["telegram_input"],
            prep_data["valid_categories"],
        )
        message_text, user_name, chat_id = (
            telegram_input.get("message_text"),
            telegram_input.get("user_name"),
            telegram_input.get("chat_id"),
        )

        if not all([message_text, user_name, chat_id]):
            return None

        logger.info(f"Node [ParseExpenseListNode]: Sending text to LLM for analysis...")
        categories_str = ", ".join(valid_categories)
        today_str = datetime.now().strftime("%Y-%m-%d")

        prompt = get_parse_expense_prompt(categories_str, message_text, today_str)

        llm_response_str = call_llm(prompt)
        logger.info(f"-> LLM response: {llm_response_str}")

        try:
            raw_expenses = json.loads(
                llm_response_str.strip().replace("```json", "").replace("```", "")
            )

            clean_expenses = []

            for expense in raw_expenses:
                raw_cat = expense.get("category", expense.get("alimentos", "otros"))
                normalized_cat = normalize_category(raw_cat, valid_categories)

                # Parse date from LLM response
                raw_date = expense.get("date", "today")
                parsed_date = parse_relative_date(raw_date)

                clean_expense = {
                    "date": parsed_date,
                    "who": user_name,
                    "chat_id": chat_id,
                    "amount": expense.get("amount"),
                    "description": expense.get(
                        "description", expense.get("establishment", "Sin descripción")
                    ),
                    "category": normalized_cat,
                    "type": "Gasto",
                }

                if clean_expense["category"] not in valid_categories:
                    logger.warning(
                        f"-> Invalid category '{clean_expense['category']}', assigning 'otros'."
                    )
                    clean_expense["category"] = "otros"

                clean_expenses.append(clean_expense)

            return clean_expenses

        except (json.JSONDecodeError, TypeError):
            logger.error("-> Error: LLM response is not valid JSON.")
            return []

    def post(self, shared, prep_res, exec_res):
        if exec_res is not None:
            shared["parsed_transactions"] = exec_res
        return "default"


class ParseIncomeNode(Node):
    def prep(self, shared):
        return shared.get("telegram_input", {})

    def exec(self, telegram_input):
        message_text = telegram_input.get("message_text")
        user_name = telegram_input.get("user_name")
        chat_id = telegram_input.get("chat_id")

        if not all([message_text, user_name, chat_id]):
            return None

        logger.info(f"Node [ParseIncomeNode]: Sending text to LLM for analysis...")

        prompt = get_parse_income_prompt(message_text)

        llm_response_str = call_llm(prompt)
        logger.info(f"-> LLM response: {llm_response_str}")

        try:
            raw_income = json.loads(
                llm_response_str.strip().replace("```json", "").replace("```", "")
            )
            today_date = datetime.now().strftime("%Y-%m-%d")

            clean_income = {
                "date": today_date,
                "who": user_name,
                "chat_id": chat_id,
                "amount": raw_income.get("amount"),
                "description": raw_income.get("description", "Sin descripción"),
                "category": "Ingreso",
                "type": "Ingreso",
            }
            return [clean_income]
        except (json.JSONDecodeError, TypeError):
            logger.error("-> Error: LLM response is not valid JSON.")
            return []

    def post(self, shared, prep_res, exec_res):
        if exec_res is not None:
            shared["parsed_transactions"] = exec_res
        return "default"


class ParseBudgetNode(Node):
    def prep(self, shared):
        return shared.get("telegram_input", {}).get("message_text")

    def exec(self, message_text):
        if not message_text:
            return None
        logger.info("Node [ParseBudgetNode]: Extracting budget details...")

        prompt = get_parse_budget_prompt(message_text)

        llm_response_str = call_llm(prompt)
        logger.info(f"-> LLM budget parse response: {llm_response_str}")
        try:
            return json.loads(
                llm_response_str.strip().replace("```json", "").replace("```", "")
            )
        except (json.JSONDecodeError, TypeError):
            logger.error("-> Error: Could not parse budget details from LLM response.")
            return None

    def post(self, shared, _, exec_res):
        if exec_res and "category" in exec_res and "amount" in exec_res:
            shared["budget_details"] = exec_res
            return "default"
        return None


class SetBudgetNode(Node):
    def prep(self, shared):
        return {
            "budget_details": shared.get("budget_details"),
            "chat_id": shared.get("telegram_input", {}).get("chat_id"),
        }

    def exec(self, prep_data):
        budget_details = prep_data.get("budget_details")
        chat_id = prep_data.get("chat_id")

        if not all([budget_details, chat_id]):
            return "Error: Faltan datos para registrar el presupuesto."

        category = budget_details["category"]
        amount = budget_details["amount"]

        logger.info(f"Node [SetBudgetNode]: Setting budget for '{category}'...")
        success = set_budget(category.capitalize(), float(amount))

        if success:
            message = f"✅ Presupuesto actualizado!\nCategoría: {category.capitalize()}\nMonto Máximo: {float(amount):,.2f} PESOS"
        else:
            message = "❌ Hubo un error al guardar tu presupuesto. Inténtalo de nuevo."

        loop = asyncio.get_event_loop()
        loop.run_until_complete(send_message(chat_id, message))
        return "done"


class QueryBudgetNode(Node):
    def prep(self, shared):
        return {
            "user_intent": shared.get("user_intent", {}),
            "chat_id": shared.get("telegram_input", {}).get("chat_id"),
        }

    def exec(self, prep_data):
        user_intent = prep_data.get("user_intent")
        chat_id = prep_data.get("chat_id")

        if not all([user_intent, chat_id]):
            return "Error: Faltan datos para consultar el presupuesto."

        category = user_intent.get("entities", {}).get("category")
        if not category:
            return "No entendí para qué categoría quieres consultar el presupuesto. Inténtalo de nuevo, por ejemplo: '¿cuánto me queda para alimentos?'"

        logger.info(
            f"Node [QueryBudgetNode]: Querying budget for category '{category}'..."
        )

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
        return None


class ProcessTransactionBatchNode(BatchNode):
    def prep(self, shared):
        return shared.get("parsed_transactions", [])

    def exec(self, transaction_item):
        chat_id = transaction_item.get("chat_id")
        if not chat_id:
            return

        logger.info(
            f"Node [ProcessTransactionBatchNode]: Processing transaction -> {transaction_item['description']}"
        )
        sheet_data = [
            transaction_item.get(k)
            for k in ["date", "amount", "category", "description", "who", "type"]
        ]

        if not append_row(sheet_data):
            logger.error("-> Error saving to Google Sheets.")
            return

        trans_type = transaction_item.get("type", "Gasto")
        transaction_date = transaction_item.get("date", "N/A")

        if trans_type == "Gasto":
            confirmation_message = (
                f"Gasto Registrado ✅\n"
                f"Fecha: {transaction_date}\n"
                f"Monto: {transaction_item.get('amount', 0.0)} PESOS\n"
                f"Categoría: {transaction_item.get('category', 'N/A')}"
            )
        else:
            confirmation_message = (
                f"Ingreso Registrado 💸\n"
                f"Fecha: {transaction_date}\n"
                f"Monto: {transaction_item.get('amount', 0.0)} PESOS\n"
                f"Descripción: {transaction_item.get('description', 'N/A')}"
            )

        loop = asyncio.get_event_loop()
        loop.run_until_complete(send_message(chat_id, confirmation_message))
        logger.info(f"-> Confirmation sent to {chat_id}.")

        if trans_type == "Gasto":
            category = transaction_item.get("category", "").lower()
            current_amount = float(transaction_item.get("amount", 0))

            budgets = get_budgets()
            budget_amount = budgets.get(category)

            if budget_amount:
                logger.info(
                    f"-> Budget found for '{category}': {budget_amount}. Checking status..."
                )

                all_records = get_all_records("Gastos")
                total_spent_this_month = calculate_monthly_spend(category, all_records)
                spent_before_this = total_spent_this_month - current_amount

                logger.info(
                    f"-> Budget Check: Spent before={spent_before_this}, Spent now={total_spent_this_month}, Budget={budget_amount}"
                )

                percentage_before = (
                    (spent_before_this / budget_amount) * 100
                    if budget_amount > 0
                    else 0
                )
                percentage_after = (
                    (total_spent_this_month / budget_amount) * 100
                    if budget_amount > 0
                    else 0
                )

                alert_message = None

                # Case 1: You just crossed 100%
                if percentage_after >= 100 and percentage_before < 100:
                    alert_message = (
                        f"🚨 ¡Alerta de Presupuesto! 🚨\n"
                        f"Acabas de superar el 100% de tu presupuesto para '{category.capitalize()}'.\n"
                        f"Gastado este mes: {total_spent_this_month:,.2f} de {budget_amount:,.2f} PESOS."
                    )
                # Case 2: You were already over 100% and are spending more
                elif percentage_after > 100 and percentage_before >= 100:
                    alert_message = (
                        f"🚨 ¡Sigues por encima del presupuesto! 🚨\n"
                        f"Nuevo gasto en '{category.capitalize()}' mientras estás sobre el límite.\n"
                        f"Gastado este mes: {total_spent_this_month:,.2f} de {budget_amount:,.2f} PESOS."
                    )
                # Case 3: You just crossed 85%
                elif percentage_after >= 85 and percentage_before < 85:
                    alert_message = (
                        f"⚠️ ¡Atención! ⚠️\n"
                        f"Ya has utilizado más del 85% de tu presupuesto para '{category.capitalize()}'.\n"
                        f"Gastado este mes: {total_spent_this_month:,.2f} de {budget_amount:,.2f} PESOS."
                    )

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
    def prep(self, shared):
        return {
            "records": shared.get("sheet_data", []),
            "intent": shared.get("user_intent", {}),
        }

    def exec(self, prep_data):
        logger.info("Node [FormatSummaryNode]: Calculating and formatting summary...")
        records = prep_data["records"]
        entities = prep_data.get("intent", {}).get("entities", {})

        if not records:
            return "No tienes transacciones registradas todavía."

        start_date_str = entities.get("start_date")
        end_date_str = entities.get("end_date")

        if not all([start_date_str, end_date_str]):
            return "No pude entender el rango de fechas para el resumen. Por favor, intenta de nuevo."

        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            return "Recibí un formato de fecha inválido. Por favor, intenta de nuevo."

        title_period = f"del {start_date_str} al {end_date_str}"
        if start_date_str == end_date_str:
            title_period = f"para el día {start_date_str}"

        date_filtered_records = [
            r
            for r in records
            if r.get("Fecha")
            and start_date
            <= datetime.strptime(r["Fecha"], "%Y-%m-%d").date()
            <= end_date
        ]

        if not date_filtered_records:
            return f"No se encontraron transacciones en el período {title_period}."

        expense_records = [r for r in date_filtered_records if r.get("Tipo") == "Gasto"]
        income_records = [
            r for r in date_filtered_records if r.get("Tipo") == "Ingreso"
        ]

        total_spent = sum(float(r.get("Monto", 0)) for r in expense_records)
        total_earned = sum(float(r.get("Monto", 0)) for r in income_records)
        balance = total_earned - total_spent

        summary_lines = [
            f"📊 Resumen de Finanzas {title_period}",
            "-----------------------------------",
        ]
        summary_lines.append(f"💸 Total Ingresado: {total_earned:,.2f} PESOS")
        summary_lines.append(f"💰 Total Gastado: {total_spent:,.2f} PESOS")
        summary_lines.append(f"⚖️ Balance Final: {balance:,.2f} PESOS\n")

        if income_records:
            summary_lines.append("Detalle de Ingresos:")
            by_source = defaultdict(float)
            for r in income_records:
                by_source[r.get("Descripcion", "sin descripcion")] += float(
                    r.get("Monto", 0)
                )
            sorted_sources = sorted(
                by_source.items(), key=lambda item: item[1], reverse=True
            )
            for source, amount in sorted_sources:
                summary_lines.append(f"  - {source.capitalize()}: {amount:,.2f} PESOS")
            summary_lines.append("")

        if expense_records:
            summary_lines.append("Detalle de Gastos por Categoría:")
            by_category = defaultdict(float)
            for r in expense_records:
                by_category[r.get("Categoria", "sin categoria")] += float(
                    r.get("Monto", 0)
                )
            sorted_categories = sorted(
                by_category.items(), key=lambda item: item[1], reverse=True
            )
            for category, amount in sorted_categories:
                summary_lines.append(
                    f"  - {category.capitalize()}: {amount:,.2f} PESOS"
                )
        else:
            summary_lines.append("No se registraron gastos en este período.")

        return "\n".join(summary_lines)

    def post(self, shared, _, exec_res):
        shared["summary_message"] = exec_res
        return "default"


class SendSummaryNode(Node):
    def prep(self, shared):
        return {
            "chat_id": shared.get("telegram_input", {}).get("chat_id"),
            "message": shared.get("summary_message"),
        }

    def exec(self, prep_data):
        chat_id, message = prep_data["chat_id"], prep_data["message"]
        if not all([chat_id, message]):
            return
        logger.info("Node [SendSummaryNode]: Sending summary to the user.")
        loop = asyncio.get_event_loop()
        loop.run_until_complete(send_message(chat_id, message))


class DataExtractionNode(Node):
    """
    Process 1: Fetches and structures expense data from the last two months
    for comparative analysis.
    """

    def exec(self, _):
        logger.info("Node [DataExtractionNode]: Fetching data for the last 2 months...")
        all_records = get_all_records("Gastos")

        today = date.today()

        end_of_last_month = today.replace(day=1) - timedelta(days=1)
        start_of_last_month = end_of_last_month.replace(day=1)

        end_of_month_before = start_of_last_month - timedelta(days=1)
        start_of_month_before = end_of_month_before.replace(day=1)

        def process_month(start_date, end_date):
            month_expenses = [
                r
                for r in all_records
                if r.get("Tipo") == "Gasto"
                and r.get("Fecha")
                and start_date
                <= datetime.strptime(r["Fecha"], "%Y-%m-%d").date()
                <= end_date
            ]

            total = sum(float(r.get("Monto", 0)) for r in month_expenses)
            by_category = defaultdict(float)
            for r in month_expenses:
                by_category[r.get("Categoria", "Otros")] += float(r.get("Monto", 0))

            return {
                "total": total,
                "by_category": dict(by_category),
                "raw_expenses": month_expenses,
            }

        analysis_data = {
            "last_month": process_month(start_of_last_month, end_of_last_month),
            "month_before": process_month(start_of_month_before, end_of_month_before),
            "last_month_name": start_of_last_month.strftime("%B de %Y"),
        }

        logger.info(
            f"Data extracted for {analysis_data['last_month_name']}. Total spend: {analysis_data['last_month']['total']}"
        )
        return analysis_data

    def post(self, shared, _, exec_res):
        shared["analysis_data"] = exec_res
        return "default"


class MonthlyAnalysisNode(Node):
    """
    Process 2: Takes the structured data, sends it to an LLM for analysis,
    and sends the final summary to the admin.
    """

    def prep(self, shared):
        return {
            "analysis_data": shared.get("analysis_data"),
            "admin_chat_id": shared.get("admin_chat_id"),
        }

    def exec(self, prep_data):
        analysis_data = prep_data.get("analysis_data")
        admin_chat_id = prep_data.get("admin_chat_id")
        if not all([analysis_data, admin_chat_id]):
            logger.error("Missing analysis data or admin_chat_id.")
            return None

        logger.info("Node [MonthlyAnalysisNode]: Generating analysis with LLM...")

        data_str = json.dumps(analysis_data, indent=2, ensure_ascii=False)
        last_month_name = analysis_data.get("last_month_name", "el mes pasado")

        prompt = get_monthly_analysis_prompt(data_str, last_month_name)

        summary_text = call_llm(prompt)

        if summary_text:
            try:
                asyncio.run(send_message(admin_chat_id, summary_text))
                logger.info("Successfully sent monthly summary to admin.")
            except Exception as e:
                logger.error(f"Error sending summary message: {e}")
        else:
            logger.error("LLM failed to generate a summary.")

        return "done"

    def post(self, shared, _, exec_res):
        return None


class ExportReportNode(Node):
    """
    Exports financial report to PDF and sends it via Telegram.
    Supports exporting: monthly summary, category breakdown, or full statement.
    """

    def prep(self, shared):
        return {
            "user_intent": shared.get("user_intent", {}),
            "telegram_input": shared.get("telegram_input", {}),
            "sheet_data": shared.get("sheet_data", []),
        }

    def exec(self, prep_data):
        user_intent = prep_data.get("user_intent", {})
        telegram_input = prep_data.get("telegram_input", {})
        sheet_data = prep_data.get("sheet_data", [])

        chat_id = telegram_input.get("chat_id")
        export_type = user_intent.get("entities", {}).get("export_type", "monthly")

        if not chat_id:
            return {"message": "Error: No puedo identificar el chat.", "chat_id": None}

        logger.info(f"Node [ExportReportNode]: Generating {export_type} report...")

        # Generate PDF
        pdf_path = generate_financial_pdf(sheet_data, export_type)

        if not pdf_path:
            return {"message": "❌ Error al generar el reporte.", "chat_id": chat_id}

        # Send PDF
        try:
            asyncio.run(
                send_document(
                    chat_id, pdf_path, f"📊 Tu reporte {export_type} está listo!"
                )
            )
            logger.info(f"Successfully sent {export_type} report to chat {chat_id}")

            # Cleanup temp file
            if os.path.exists(pdf_path):
                os.remove(pdf_path)

            return {"message": "✅ Reporte enviado!", "chat_id": chat_id}
        except Exception as e:
            logger.error(f"Error sending report: {e}")
            return {
                "message": f"❌ Error al enviar el reporte: {e}",
                "chat_id": chat_id,
            }

    def post(self, shared, _, exec_res):
        if exec_res and exec_res.get("message"):
            asyncio.run(send_message(exec_res["chat_id"], exec_res["message"]))
        return "default"


def generate_financial_pdf(sheet_data: list, export_type: str = "monthly") -> str:
    """
    Generates a PDF report from sheet data.

    Args:
        sheet_data: List of transaction records
        export_type: Type of export (monthly, category, full)

    Returns:
        Path to generated PDF file
    """
    try:
        from fpdf import FPDF

        pdf = FPDF()
        pdf.add_page()

        # Title
        pdf.set_font("Arial", "B", 16)
        pdf.cell(
            0, 10, f"Reporte Financiero - {export_type.title()}", ln=True, align="C"
        )
        pdf.ln(10)

        # Summary
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "Resumen General", ln=True)
        pdf.set_font("Arial", "", 10)

        # Calculate totals
        total_income = 0
        total_expenses = 0
        by_category = defaultdict(float)

        for record in sheet_data:
            monto = float(record.get("Monto", 0))
            tipo = record.get("Tipo", "")
            categoria = record.get("Categoria", "Otros")

            if tipo == "Ingreso":
                total_income += monto
            elif tipo == "Gasto":
                total_expenses += monto
                by_category[categoria] += monto

        # Print totals
        pdf.cell(0, 8, f"Total Ingresos: ${total_income:,.2f}", ln=True)
        pdf.cell(0, 8, f"Total Gastos: ${total_expenses:,.2f}", ln=True)
        pdf.cell(0, 8, f"Balance: ${total_income - total_expenses:,.2f}", ln=True)
        pdf.ln(5)

        # Category breakdown
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "Gastos por Categoría", ln=True)
        pdf.set_font("Arial", "", 10)

        for cat, amount in sorted(
            by_category.items(), key=lambda x: x[1], reverse=True
        ):
            pdf.cell(0, 8, f"{cat}: ${amount:,.2f}", ln=True)

        # Save
        os.makedirs("temp", exist_ok=True)
        pdf_path = (
            f"temp/reporte_{export_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        )
        pdf.output(pdf_path)

        return pdf_path

    except Exception as e:
        logger.error(f"Error generating PDF: {e}")
        return None
