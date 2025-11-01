from pocketflow import Flow
from nodes import (
    GetMessageNode,
    DetectIntentNode,
    ParseExpenseListNode,
    ProcessExpenseBatchNode,
    FetchSheetDataNode,
    FormatSummaryNode,
    SendSummaryNode
)

def create_expense_flow():
    """
    Crea y retorna el flujo completo con ramificación de intenciones.
    """
    # 1. Crear instancias de todos los nodos
    get_message_node = GetMessageNode()
    detect_intent_node = DetectIntentNode()
    
    # Nodos de la rama de REGISTRO
    parse_expense_node = ParseExpenseListNode()
    process_expense_node = ProcessExpenseBatchNode()
    
    # Nodos de la rama de CONSULTA
    fetch_data_node = FetchSheetDataNode()
    format_summary_node = FormatSummaryNode()
    send_summary_node = SendSummaryNode()
    
    # 2. Conectar las partes lineales del flujo
    get_message_node >> detect_intent_node
    
    # Conectar la secuencia de la rama de REGISTRO
    parse_expense_node >> process_expense_node
    
    # Conectar la secuencia de la rama de CONSULTA
    fetch_data_node >> format_summary_node >> send_summary_node
    
    # 3. Conectar manualmente las ramas al nodo de intención
    detect_intent_node.successors = {
        "log_expense": parse_expense_node,
        "query_expense": fetch_data_node
    }
    
    # 4. Crear el objeto Flow, especificando el nodo de inicio
    return Flow(start=get_message_node)