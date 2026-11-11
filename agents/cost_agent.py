
import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

LOG_FILE = BASE_DIR / "processed" / "classified_logs.json"

INVENTORY_FILE = BASE_DIR / "data" / "resource_inventory.json"


def load_json(file_path):

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def analyze_vm(vm):

    recommendations = []

    cpu_usage = vm["cpu_usage_percent"]
    memory_usage = vm["memory_usage_percent"]
    storage_usage = (
        vm["storage_used_gb"] /
        vm["storage_allocated_gb"]
    ) * 100

    # CPU analysis
    if cpu_usage < 15:

        recommendations.append({
            "resource": "CPU",
            "issue": "Potential CPU overallocation",
            "current_allocation": vm["cpu_allocated"],
            "recommendation": "Review CPU allocation",
            "risk": "Medium"
        })

    # Memory analysis
    if memory_usage < 20:

        recommendations.append({
            "resource": "MEMORY",
            "issue": "Potential memory overallocation",
            "current_allocation_gb": vm["memory_allocated_gb"],
            "recommendation": "Review memory allocation",
            "risk": "Medium"
        })

    # Storage analysis
    if storage_usage < 35:

        recommendations.append({
            "resource": "STORAGE",
            "issue": "Low storage utilization",
            "allocated_gb": vm["storage_allocated_gb"],
            "used_gb": vm["storage_used_gb"],
            "utilization_percent": round(storage_usage, 2),
            "recommendation": "Review storage allocation",
            "risk": "Low"
        })

    return recommendations


def run_cost_agent():

    logs = load_json(LOG_FILE)
    inventory = load_json(INVENTORY_FILE)

    results = []

    for vm in inventory:

        recommendations = analyze_vm(vm)

        results.append({
            "vm_name": vm["vm_name"],
            "application": vm["application"],
            "environment": vm["environment"],
            "recommendations": recommendations
        })

    # Collect infrastructure-related log events
    infrastructure_events = [
        log for log in logs
        if log.get("category") in [
            "STORAGE",
            "CPU",
            "MEMORY",
            "NETWORK"
        ]
    ]

    output = {
        "agent": "CostOptimizationAgent",
        "total_vms_analyzed": len(inventory),
        "infrastructure_events": len(infrastructure_events),
        "vm_analysis": results
    }

    return output


if __name__ == "__main__":

    result = run_cost_agent()

    print("\n========== COST OPTIMIZATION AGENT ==========")

    print(json.dumps(result, indent=4))
