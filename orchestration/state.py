
from typing import TypedDict, Any


class VMwareAgentState(TypedDict, total=False):

    # Cost Optimization Agent output
    cost_report: dict[str, Any]

    # RPA Agent output
    rpa_report: dict[str, Any]

    # FinOps Agent output
    finops_report: dict[str, Any]

    # Final combined output
    final_report: dict[str, Any]
