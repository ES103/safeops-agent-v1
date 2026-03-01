"""
🛠️ SafeOps-Agent: Mock Enterprise Tools
"""

import time
from typing import Dict, Any
from langchain_core.tools import tool
from pydantic import BaseModel, Field

# --- Tool Schemas (The "Output Guard") ---

class ResetPasswordInput(BaseModel):
    emp_id: str = Field(description="The unique employee ID, e.g., 'E12345'")
    reason: str = Field(description="The justification for resetting the password.")

class QuerySalaryInput(BaseModel):
    emp_id: str = Field(description="The unique employee ID, e.g., 'E12345'")
    month: str = Field(description="The YYYY-MM formatted month to query, e.g., '2026-02'")

class TransferAssetInput(BaseModel):
    asset_id: str = Field(description="The unique asset tracking ID, e.g., 'ASSET-9901'")
    target_dept: str = Field(description="The department receiving the asset, e.g., 'Engineering'")
    justification: str = Field(description="Why this transfer is occurring.")

# --- Mock Tools ---

@tool("reset_employee_password", args_schema=ResetPasswordInput)
def reset_employee_password(emp_id: str, reason: str) -> str:
    """Resets an employee's password and generates a temporary one."""
    # Simulate API latency for observability tracking
    time.sleep(0.5)
    return f"SUCCESS: Password for {emp_id} reset successfully. Reason logged: {reason}"

@tool("query_salary", args_schema=QuerySalaryInput)
def query_salary(emp_id: str, month: str) -> Dict[str, Any]:
    """Queries an employee's salary for a specific month. High privilege required."""
    time.sleep(0.8)
    return {
        "status": "success",
        "emp_id": emp_id,
        "month": month,
        "base_salary": 8500,
        "bonus": 1200,
        "currency": "USD"
    }

@tool("transfer_asset", args_schema=TransferAssetInput)
def transfer_asset(asset_id: str, target_dept: str, justification: str) -> str:
    """Transfers a physical or digital asset to a new department. Extremely high risk operation."""
    time.sleep(1.2)
    return f"SUCCESS: Asset {asset_id} transferred to {target_dept}. Justification logged: {justification}"


# Export list of tools for the agent
enterprise_tools = [reset_employee_password, query_salary, transfer_asset]
