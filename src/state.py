"""
🛡️ SafeOps-Agent: LangGraph State Definition
"""

from typing import TypedDict, Annotated, List, Optional
from langchain_core.messages import BaseMessage
import operator

class SafeOpsState(TypedDict):
    """
    Main state for the Guardian system.
    Tracks messages, execution confidence, and retry attempts for fallback logic.
    """
    # The message history, populated by the user and the agent
    messages: Annotated[List[BaseMessage], operator.add]
    
    # Track the number of times we've retried a failed validation or tool call
    retry_count: int
    
    # The agent's stated confidence in its ability to execute the next action cleanly
    confidence_score: float
    
    # Are we escalating to a human?
    escalation_reason: Optional[str]
