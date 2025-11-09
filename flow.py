from pocketflow import Flow
from nodes import (
    GetMessageNode,
    TranscribeAudioNode,
    DetectIntentNode,
    ParseExpenseListNode,
    ParseIncomeNode,
    ProcessTransactionBatchNode,
    FetchSheetDataNode,
    FormatSummaryNode,
    QueryBudgetNode,
    SendSummaryNode,
    ParseBudgetNode,
    SetBudgetNode,
    AddCategoryNode,
    QueryExpensesByCategoryNode,
    HelpNode,
    FallbackNode
)

def create_expense_flow():
    """
    Creates and returns the complete flow with audio transcription and all branches.
    """
    # 1. Create instances of all nodes
    get_message_node = GetMessageNode()
    transcribe_audio_node = TranscribeAudioNode()
    detect_intent_node = DetectIntentNode()
    query_budget_node = QueryBudgetNode()
    add_category_node = AddCategoryNode()
    query_expenses_by_category_node = QueryExpensesByCategoryNode()
    help_node = HelpNode()
    fallback_node = FallbackNode()
    
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
    # The transcription node correctly flows into the intent detection node by default.
    transcribe_audio_node >> detect_intent_node
    
    # Connect all other linear sequences
    parse_expense_node >> process_transaction_node
    parse_income_node >> process_transaction_node
    fetch_data_node >> format_summary_node >> send_summary_node
    parse_budget_node >> set_budget_node
    
    # 3. Manually define the branching logic from the starting nodes
    get_message_node.successors = {
        "transcribe": transcribe_audio_node,
        "detect_intent": detect_intent_node
    }

    detect_intent_node.successors = {
        "log_expense": parse_expense_node,
        "log_income": parse_income_node,
        "query_expense": fetch_data_node,
        "set_budget": parse_budget_node,
        "query_budget": query_budget_node,
        "add_category": add_category_node,
        "query_by_category": query_expenses_by_category_node,
        "show_help": help_node,
        "fallback": fallback_node
    }
    
    # 4. Create the Flow object, specifying the start node
    return Flow(start=get_message_node)
