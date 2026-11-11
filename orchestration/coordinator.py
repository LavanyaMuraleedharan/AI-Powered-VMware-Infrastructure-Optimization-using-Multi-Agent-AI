
import json
import sys

from pathlib import Path

from langgraph.graph import StateGraph, START, END

from state import VMwareAgentState


# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent

AGENTS_DIR = BASE_DIR / "agents"
PROCESSED_DIR = BASE_DIR / "processed"

sys.path.insert(0, str(AGENTS_DIR))

from cost_agent import run_cost_agent
from rpa_agent import run_rpa_agent
from finops import run_finops_agent


# ----------------------------------
# NODE 1: COST OPTIMIZATION AGENT
# ----------------------------------

def cost_node(state: VMwareAgentState):

    print("\n[COST AGENT] Analyzing infrastructure...")

    result = run_cost_agent()

    print("[COST AGENT] Analysis completed.")

    return {
        "cost_report": result
    }


# ----------------------------------
# NODE 2: RPA AGENT
# ----------------------------------

def rpa_node(state: VMwareAgentState):

    print("\n[RPA AGENT] Preparing remediation workflows...")

    cost_results = state["cost_report"]

    result = run_rpa_agent(cost_results)

    print("[RPA AGENT] Analysis completed.")

    return {
        "rpa_report": result
    }


# ----------------------------------
# NODE 3: FINOPS AGENT
# ----------------------------------

def finops_node(state: VMwareAgentState):

    print("\n[FINOPS AGENT] Evaluating financial impact...")

    cost_results = state["cost_report"]

    result = run_finops_agent(cost_results)

    print("[FINOPS AGENT] Analysis completed.")

    return {
        "finops_report": result
    }


# ----------------------------------
# NODE 4: DECISION COORDINATOR
# ----------------------------------

def decision_node(state: VMwareAgentState):

    print("\n[COORDINATOR] Combining agent results...")

    cost = state["cost_report"]
    rpa = state["rpa_report"]
    finops = state["finops_report"]

    final_report = {

        "project": "VMware Multi-Agent Infrastructure Optimization",

        "cost_optimization": {
            "total_vms_analyzed":
                cost["total_vms_analyzed"],

            "vm_analysis":
                cost["vm_analysis"]
        },

        "automation": {
            "total_actions_identified":
                rpa["total_actions_identified"],

            "actions_requiring_approval":
                rpa["actions_requiring_approval"],

            "remediation_actions":
                rpa["remediation_actions"]
        },

        "financial_analysis": finops["analysis"],

        "execution_policy": {
            "execution_mode": "SIMULATION_ONLY",
            "automatic_execution": False,
            "human_approval_required": True
        }
    }

    return {
        "final_report": final_report
    }


# ----------------------------------
# BUILD LANGGRAPH
# ----------------------------------

workflow = StateGraph(VMwareAgentState)

workflow.add_node("cost_agent", cost_node)
workflow.add_node("rpa_agent", rpa_node)
workflow.add_node("finops_agent", finops_node)
workflow.add_node("decision_coordinator", decision_node)


# Execution flow

workflow.add_edge(START, "cost_agent")

# Cost Agent runs first
# RPA and FinOps run in parallel afterwards

workflow.add_edge("cost_agent", "rpa_agent")
workflow.add_edge("cost_agent", "finops_agent")

# Wait for both agents before coordinating
workflow.add_edge(
    ["rpa_agent", "finops_agent"],
    "decision_coordinator"
)

workflow.add_edge("decision_coordinator", END)


# Compile graph
app = workflow.compile()


# ----------------------------------
# EXECUTE MULTI-AGENT SYSTEM
# ----------------------------------

def run_multi_agent_system():

    print("\n===================================")
    print("VMWARE MULTI-AGENT SYSTEM")
    print("===================================")

    result = app.invoke({})

    final_report = result["final_report"]

    PROCESSED_DIR.mkdir(exist_ok=True)

    output_file = (
        PROCESSED_DIR / "final_optimization_report.json"
    )

    with open(output_file, "w", encoding="utf-8") as file:

        json.dump(
            final_report,
            file,
            indent=4
        )

    print("\n===================================")
    print("WORKFLOW COMPLETED")
    print("===================================")

    print(json.dumps(final_report, indent=4))

    print("\nReport saved to:", output_file)


if __name__ == "__main__":

    run_multi_agent_system()
