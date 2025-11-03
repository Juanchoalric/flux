from pocketflow import Flow
from nodes import (
    GetMessageNode,
    DetectIntentNode,
    ParseExpenseListNode,
    ParseIncomeNode,
    ProcessTransactionBatchNode,
    FetchSheetDataNode,
    FormatSummaryNode,
    SendSummaryNode,
    ParseBudgetNode, # Import new node
    SetBudgetNode      # Import new node
)

def create_expense_flow():
    """
    Creates and returns the complete flow with all branches.
    """
    # 1. Create instances of all nodes
    get_message_node = GetMessageNode()
    detect_intent_node = DetectIntentNode()
    
    # Branch: LOGGING
    parse_expense_node = ParseExpenseListNode()
    parse_income_node = ParseIncomeNode()
    process_transaction_node = ProcessTransactionBatchNode()
    
    # Branch: QUERYING
    fetch_data_node = FetchSheetDataNode()
    format_summary_node = FormatSummaryNode()
    send_summary_node = SendSummaryNode()

    # Branch: BUDGETING
    parse_budget_node = ParseBudgetNode()
    set_budget_node = SetBudgetNode()
    
    # 2. Connect the flow sequences
    get_message_node >> detect_intent_node
    
    parse_expense_node >> process_transaction_node
    parse_income_node >> process_transaction_node
    
    fetch_data_node >> format_summary_node >> send_summary_node

    parse_budget_node >> set_budget_node # Connect the new budget branch
    
    # 3. Manually connect the branches to the intent node
    detect_intent_node.successors = {
        "log_expense": parse_expense_node,
        "log_income": parse_income_node,
        "query_expense": fetch_data_node,
        "set_budget": parse_budget_node # Add the new branch
    }
    
    # 4. Create the Flow object
    return Flow(start=get_message_node)