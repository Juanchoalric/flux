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
    Creates and returns the complete flow with intent branching.
    """
    # 1. Create instances of all nodes
    get_message_node = GetMessageNode()
    detect_intent_node = DetectIntentNode()
    
    # 2. Nodes for the LOG EXPENSE branch
    parse_expense_node = ParseExpenseListNode()
    process_expense_node = ProcessExpenseBatchNode()
    
    # 3. Nodes for the QUERY EXPENSE branch
    fetch_data_node = FetchSheetDataNode()
    format_summary_node = FormatSummaryNode()
    send_summary_node = SendSummaryNode()
    
    # 4. Connect the linear parts of the flow
    get_message_node >> detect_intent_node
    
    # 5. Connect the sequence for the LOG EXPENSE branch
    parse_expense_node >> process_expense_node
    
    # 6. Connect the sequence for the QUERY EXPENSE branch
    fetch_data_node >> format_summary_node >> send_summary_node
    
    # 7. Manually connect the branches to the intent node
    detect_intent_node.successors = {
        "log_expense": parse_expense_node,
        "query_expense": fetch_data_node
    }
    
    # 8. Create the Flow object, specifying the start node
    return Flow(start=get_message_node)