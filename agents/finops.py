
import json
from pathlib import Path

from cost_agent import run_cost_agent


BASE_DIR = Path(__file__).resolve().parent.parent

INVENTORY_FILE = BASE_DIR / "data" / "resource_inventory.json"


def load_inventory():

    with open(INVENTORY_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def calculate_financial_metrics(inventory, cost_results):

    total_monthly_cost = sum(
        vm["monthly_cost_usd"] for vm in inventory
    )

    total_vms = len(inventory)

    application_costs = {}

    total_potential_savings = 0

    vm_savings = []

    for vm in inventory:

        vm_name = vm["vm_name"]
        application = vm["application"]
        monthly_cost = vm["monthly_cost_usd"]

        application_costs[application] = (
            application_costs.get(application, 0) + monthly_cost
        )

        # Estimate potential savings based on
        # the number of optimization candidates.
        vm_result = next(
            (
                item for item in cost_results["vm_analysis"]
                if item["vm_name"] == vm_name
            ),
            None
        )

        recommendation_count = (
            len(vm_result["recommendations"])
            if vm_result else 0
        )

        # Illustrative planning assumption only:
        # 5% of monthly cost per candidate resource,
        # capped at 15% per VM.
        estimated_savings = min(
            monthly_cost * 0.15,
            monthly_cost * 0.05 * recommendation_count
        )

        total_potential_savings += estimated_savings

        vm_savings.append({
            "vm_name": vm_name,
            "application": application,
            "monthly_cost_usd": monthly_cost,
            "optimization_candidates": recommendation_count,
            "estimated_monthly_savings_usd": round(
                estimated_savings, 2
            )
        })

    remaining_cost = (
        total_monthly_cost - total_potential_savings
    )

    return {
        "total_vms": total_vms,
        "total_monthly_cost_usd": round(
            total_monthly_cost, 2
        ),
        "estimated_monthly_savings_usd": round(
            total_potential_savings, 2
        ),
        "projected_monthly_cost_usd": round(
            remaining_cost, 2
        ),
        "estimated_annual_savings_usd": round(
            total_potential_savings * 12, 2
        ),
        "application_costs": application_costs,
        "vm_financial_analysis": vm_savings
    }


def run_finops_agent(cost_results=None):

    inventory = load_inventory()

    if cost_results is None:
        cost_results = run_cost_agent()

    financial_metrics = calculate_financial_metrics(
        inventory,
        cost_results
    )

    return {
        "agent": "FinOpsAgent",
        "currency": "USD",
        "analysis": financial_metrics,
        "data_status": "SYNTHETIC_TEST_DATA",
        "savings_status": "ESTIMATED_NOT_REALIZED"
    }


if __name__ == "__main__":

    result = run_finops_agent()

    print("\n========== FINOPS AGENT OUTPUT ==========\n")

    print(json.dumps(result, indent=4))

    output_file = BASE_DIR / "processed" / "finops_report.json"

    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(result, file, indent=4)

    print("\nFinOps report saved to:", output_file)
