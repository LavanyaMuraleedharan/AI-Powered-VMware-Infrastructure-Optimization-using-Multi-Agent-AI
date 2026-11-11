
import json
from pathlib import Path

from cost_agent import run_cost_agent


BASE_DIR = Path(__file__).resolve().parent.parent

LOG_FILE = BASE_DIR / "processed" / "classified_logs.json"


def load_logs():

    with open(LOG_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def generate_remediation_plan(recommendation, vm_name):

    resource = recommendation["resource"]
    issue = recommendation["issue"]

    # Determine the operational action
    if resource == "CPU":

        action = "REVIEW_CPU_ALLOCATION"
        description = "Review VM CPU allocation and resize if approved."

    elif resource == "MEMORY":

        action = "REVIEW_MEMORY_ALLOCATION"
        description = "Review memory allocation and resize if approved."

    elif resource == "STORAGE":

        action = "REVIEW_STORAGE_ALLOCATION"
        description = "Review storage allocation and identify reclaimable capacity."

    else:

        action = "MANUAL_INVESTIGATION"
        description = "Investigate infrastructure issue manually."

    return {
        "resource_name": vm_name,
        "issue": issue,
        "resource_type": resource,
        "automation_action": action,
        "description": description,
        "execution_status": "PENDING_APPROVAL",
        "approval_required": True,
        "execution_mode": "SIMULATION_ONLY"
    }


def analyze_log_events(logs):

    actions = []

    for log in logs:

        category = log.get("category")
        severity = log.get("severity")

        if category == "STORAGE" and severity in ["WARNING", "ERROR"]:

            actions.append({
                "source": log.get("source_file"),
                "issue": log.get("message"),
                "resource_type": "STORAGE",
                "automation_action": "RUN_STORAGE_DIAGNOSTICS",
                "description": "Collect storage device health, latency and path information.",
                "execution_status": "PENDING_APPROVAL",
                "approval_required": True,
                "execution_mode": "SIMULATION_ONLY"
            })

        elif category == "NETWORK" and severity in ["WARNING", "ERROR"]:

            actions.append({
                "source": log.get("source_file"),
                "issue": log.get("message"),
                "resource_type": "NETWORK",
                "automation_action": "RUN_NETWORK_DIAGNOSTICS",
                "description": "Check network interface status and connectivity.",
                "execution_status": "PENDING_APPROVAL",
                "approval_required": True,
                "execution_mode": "SIMULATION_ONLY"
            })

    return actions


def run_rpa_agent(cost_results=None):

    if cost_results is None:
        cost_results = run_cost_agent()

    remediation_actions = []

    # Step 2: Generate actions for identified VM issues
    for vm in cost_results["vm_analysis"]:

        for recommendation in vm["recommendations"]:

            plan = generate_remediation_plan(
                recommendation,
                vm["vm_name"]
            )

            remediation_actions.append(plan)

    # Step 3: Analyse VMware diagnostic logs
    logs = load_logs()

    log_actions = analyze_log_events(logs)

    remediation_actions.extend(log_actions)

    # Step 4: Prepare final RPA output
    output = {
        "agent": "RPA_Agent",
        "total_actions_identified": len(remediation_actions),
        "actions_requiring_approval": sum(
            1 for action in remediation_actions
            if action["approval_required"]
        ),
        "execution_mode": "SIMULATION_ONLY",
        "remediation_actions": remediation_actions
    }

    return output


if __name__ == "__main__":

    result = run_rpa_agent()

    print("\n========== RPA AGENT OUTPUT ==========\n")

    print(json.dumps(result, indent=4))

    # Save the output
    output_file = BASE_DIR / "processed" / "rpa_actions.json"

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(result, file, indent=4)

    print("\nRPA output saved to:", output_file)
