"""
🛡️ SafeOps-Agent: Input Guard and Validation Logic
"""

import re

# Simple list of simulated prohibited terms to simulate an enterprise "Input Guard"
# In a real enterprise system, this might be its own LLM call or a sophisticated rules engine.
PROHIBITED_TERMS = [
    "ignore previous instructions",
    "sudo",
    "chmod 777",
    "bypass authentication",
    "rm -rf"
]

def check_input_guard(text: str) -> (bool, str):
    """
    Checks if a user query is safe to process.
    Returns (True, "Passed") if safe, or (False, "Violation reason") if blocked.
    """
    text_lower = text.lower()
    for term in PROHIBITED_TERMS:
        if term in text_lower:
            return False, f"Input Guard triggered: Prohibited term '{term}' detected."
            
    # Simulate prompt injection detection logic here
    if len(text) > 1000:
        return False, "Input Guard triggered: Payload length exceeds 1000 characters."
        
    return True, "Passed"

