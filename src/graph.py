"""
🕸️ SafeOps-Agent: LangGraph Workflow Engine + Shield
"""

import os
import json
from enum import Enum
from typing import Dict, Any, Literal
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

from .state import SafeOpsState
from .tools import enterprise_tools
from .guards import check_input_guard

# Try to import ChatOpenAI
try:
    from langchain_openai import ChatOpenAI
except ImportError:
    # Need to run pip install
    pass


# --- Model Configuration ---

prompt_instructions = """You are SafeOps, an enterprise automated operations agent.
Your priority is security, compliance, and strict adherence to protocol.

You have access to highly sensitive tools:
- reset_employee_password
- query_salary
- transfer_asset

CRITICAL INSTRUCTIONS (Output Guard):
Before taking ANY action, you must output a JSON object evaluating your confidence in executing this request securely and accurately.

Format expected:
```json
{
  "confidence_score": <float between 0.0 and 1.0>,
  "rationale": "<string explaining your confidence level>"
}
```

If your confidence is >= 0.7, proceed to call the appropriate tool.
If your confidence is < 0.7, DO NOT call any tool. End your response there.

OUT OF SCOPE QUERIES:
If a user asks about general knowledge (e.g., weather, history, capitals), you MUST set "confidence_score": 0.0 because it is entirely unrelated to your enterprise operations role.
"""

def get_llm():
    """Retrieve the OpenRouter LLM configured for this project."""
    # We bind tools immediately so output validation handles schema parsing.
    return ChatOpenAI(
        model=os.environ.get("OPENROUTER_MODEL", "google/gemini-2.0-flash-001"),
        api_key=os.environ.get("OPENROUTER_API_KEY", "dummy"),
        base_url="https://openrouter.ai/api/v1",
        temperature=0.0
    ).bind_tools(enterprise_tools)


# --- LangGraph Nodes ---

def run_input_guard(state: SafeOpsState) -> Dict:
    """Node 1: Shield Layer - Analyze incoming message"""
    last_message = state["messages"][-1]
    
    # We only guard Human Messages
    if isinstance(last_message, HumanMessage):
        is_safe, reason = check_input_guard(last_message.content)
        if not is_safe:
            # Inject a system override that bypasses the LLM
            return {
                "escalation_reason": reason,
                "confidence_score": 0.0
            }
            
    return {"retry_count": state.get("retry_count", 0)}

def call_agent_engine(state: SafeOpsState) -> Dict:
    """Node 2: Engine Layer - Execute the LLM logic"""
    # If the guard already triggered, short circuit
    if state.get("escalation_reason") and "Input Guard" in state["escalation_reason"]:
         return {}
         
    llm = get_llm()
    # Inject system prompt
    messages = [SystemMessage(content=prompt_instructions)] + state["messages"]
    
    response = llm.invoke(messages)
    
    # Try to extract the confidence score from the JSON instructions
    confidence = 1.0 # Default high if missing
    try:
        content = response.content
        if "```json" in content:
            json_str = content.split("```json")[1].split("```")[0].strip()
            parsed = json.loads(json_str)
            confidence = float(parsed.get("confidence_score", 1.0))
    except Exception:
        # If the LLM failed to output the required JSON schema,
        # we lower the confidence to trigger a potential fallback.
        confidence = 0.5 
    
    return {
        "messages": [response],
        "confidence_score": confidence
    }

# Node 3: Tools are executed via prebuilt ToolNode
tool_node = ToolNode(enterprise_tools)

def handle_human_escalation(state: SafeOpsState) -> Dict:
    """Node 4: Submits the context to a human due to low confidence or retries."""
    
    # Determine the reason if it wasn't already set by the Input Guard
    reason = state.get("escalation_reason")
    if not reason:
        if state.get("retry_count", 0) >= 3:
            reason = "Maximum retries (3) exceeded for validation."
        elif state.get("confidence_score", 1.0) < 0.7:
            reason = f"Low Confidence Score ({state.get('confidence_score')})"
        else:
            reason = "Unknown Agent Failure"
            
    escalation_message = AIMessage(
         content=f"⚠️ BLOCKING ACTION: Connecting to Human Agent... Reason: {reason}"
    )
    return {
         "messages": [escalation_message],
         "escalation_reason": reason
    }


# --- LangGraph Edges (Control Flow) ---

def should_continue_or_fallback(state: SafeOpsState) -> Literal["tools", "human_escalation", "__end__", "agent"]:
    """
    Decides the next step after the Agent reasons.
    Implements the Threshold Fallback (Confidence & Retries).
    """
    # 1. Did the input guard fail?
    if state.get("escalation_reason") and "Input Guard" in state["escalation_reason"]:
        return "human_escalation"
        
    last_message = state["messages"][-1]
    
    # 2. Threshold Fallback: Confidence
    if state.get("confidence_score", 1.0) < 0.7:
        return "human_escalation"
        
    # 3. Threshold Fallback: Retries
    if state.get("retry_count", 0) >= 3:
        return "human_escalation"

    # 4. Did the agent call a tool?
    if hasattr(last_message, "tool_calls") and len(last_message.tool_calls) > 0:
        return "tools"
        
    # 5. Otherwise, the agent just responded.
    return "__end__"

def after_tool_execution(state: SafeOpsState) -> Literal["agent"]:
    # The output from the prebuilt ToolNode includes the ToolMessage
    # Here we could implement the Output Validation/Self-Correction check.
    # If the tool returned an error string, we bounce it back to the agent.
    # To implement this cleanly, we simply route back to agent:
    return "agent"

# --- Build the Graph ---

def build_graph() -> StateGraph:
    workflow = StateGraph(SafeOpsState)

    # Add Nodes
    workflow.add_node("guard", run_input_guard)
    workflow.add_node("agent", call_agent_engine)
    workflow.add_node("tools", tool_node)
    workflow.add_node("human_escalation", handle_human_escalation)

    # Set Entry Point
    workflow.add_edge(START, "guard")
    workflow.add_edge("guard", "agent")

    # Routing logic from Agent
    workflow.add_conditional_edges(
        "agent",
        should_continue_or_fallback,
    )

    # Routing from Tools
    workflow.add_edge("tools", "agent")
    
    # Human Escalation ends the run
    workflow.add_edge("human_escalation", END)

    return workflow.compile()
