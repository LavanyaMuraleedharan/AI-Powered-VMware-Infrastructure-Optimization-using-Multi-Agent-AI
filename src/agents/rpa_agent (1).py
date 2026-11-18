"""
RPA Agent for the existing Cost -> FinOps -> Supervisor workflow.

This file consumes the reports produced by the existing agents.
It does not modify cost_agent.py, finops_agent.py, or supervisor_agent.py.

Execution is a DRY RUN only. No live infrastructure APIs or commands
are called by this prototype.
"""

import json
import tempfile
from pathlib import Path
from datetime import datetime


TEMP_ROOT = Path(tempfile.gettempdir())

COST_AGENT_REPORT = (
    TEMP_ROOT / "cost_agent_reports" / "cost_agent_report.json"
)
SUPERVISOR_REPORT = (
    TEMP_ROOT / "supervisor_agent_reports" / "supervisor_agent_report.json"
)

OUTPUT_DIR = TEMP_ROOT / "rpa_agent_reports"
OUTPUT_JSON = OUTPUT_DIR / "rpa_agent_report.json"
OUTPUT_MD = OUTPUT_DIR / "rpa_agent_report.md"
AUDIT_LOG = OUTPUT_DIR / "rpa_audit_log.jsonl"


# ============================================================
# 1. FILE AND DATA HELPERS
# ============================================================

def load_json(path):
    if not path.exists():
        raise FileNotFoundError(
            f"Required report not found: {path}. "
            "Run the Supervisor Agent first."
        )

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False, default=str)


def money(value):
    try:
        if value is None:
            return "Not established"
        return f"₹{float(value):,.2f}"
    except (TypeError, ValueError):
        return "Not established"


def as_float(value):
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def unwrap_supervisor_report(data):
    """Accept either the raw report or run_supervisor_agent() wrapper."""
    if isinstance(data, dict) and isinstance(data.get("report"), dict):
        return data["report"]
    return data


# ============================================================
# 2. BUILD ACTION PROPOSALS FROM EXISTING REPORTS
# ============================================================

def build_action_proposals(supervisor_report, cost_report):
    """
    Uses Supervisor's consolidated domain results and the Cost Agent's
    detailed storage example. Existing agent files remain unchanged.
    """
    consolidated = supervisor_report.get(
        "consolidated_optimization_report", {}
    )
    domains = consolidated.get("domains", [])

    if not isinstance(domains, list) or not domains:
        raise ValueError(
            "Supervisor report has no consolidated domain results."
        )

    sections = cost_report.get("sections", {})
    storage_detail = sections.get("detailed_example")

    proposals = []

    for domain_result in domains:
        if not isinstance(domain_result, dict):
            continue

        domain = domain_result.get("domain", "Unknown")
        detected_issue = domain_result.get(
            "detected_issue", "No issue description available."
        )
        domain_savings = as_float(
            domain_result.get("monthly_savings_inr")
        )

        recommendation = (
            domain_result.get("supervisor_decision")
            or domain_result.get("finops_recommendation")
            or f"Review and validate the {domain} optimization opportunity."
        )

        # The current Cost Agent report contains one detailed Storage
        # example under sections.detailed_example. Use it only for Storage.
        if domain.lower() == "storage" and isinstance(storage_detail, dict):
            asset_id = storage_detail.get("asset_id")
            asset_savings = as_float(
                storage_detail.get("estimated_monthly_savings_inr")
            )

            if asset_id:
                action = (
                    f"Reclaim eligible unused storage capacity for asset "
                    f"{asset_id} after operational validation"
                )

                proposals.append({
                    "action_id": f"{domain.upper().replace('/', '_')}-001",
                    "domain": domain,
                    "asset_id": str(asset_id),
                    "detected_issue": detected_issue,
                    "proposed_action": action,
                    "recommendation": recommendation,
                    "estimated_monthly_savings_inr": (
                        asset_savings
                        if asset_savings is not None
                        else domain_savings
                    ),
                    "savings_basis": (
                        "Asset-level estimate from Cost Agent detailed_example"
                        if asset_savings is not None
                        else "Domain-level estimate; asset-level amount unavailable"
                    ),
                    "asset_metrics": {
                        "total_capacity_tb": storage_detail.get(
                            "total_capacity_tb"
                        ),
                        "used_capacity_tb": storage_detail.get(
                            "used_capacity_tb"
                        ),
                        "unused_capacity_tb": storage_detail.get(
                            "unused_capacity_tb"
                        ),
                        "utilization_pct": storage_detail.get(
                            "utilization_pct"
                        ),
                        "monthly_cost_inr": storage_detail.get(
                            "monthly_cost_inr"
                        ),
                        "cost_exposure_inr": storage_detail.get(
                            "cost_exposure_inr"
                        ),
                    },
                    "required_checks": [
                        "Verify the storage asset identity",
                        "Check application and workload dependencies",
                        "Validate performance and capacity requirements",
                        "Verify redundancy, backup and recovery requirements",
                        "Confirm future capacity demand",
                    ],
                })
                continue

        # Generic proposal for domains where the current Supervisor
        # report does not provide an individual asset identifier.
        proposals.append({
            "action_id": f"{domain.upper().replace('/', '_')}-001",
            "domain": domain,
            "asset_id": None,
            "detected_issue": detected_issue,
            "proposed_action": recommendation,
            "recommendation": recommendation,
            "estimated_monthly_savings_inr": domain_savings,
            "savings_basis": "Domain-level estimate from Supervisor report",
            "asset_metrics": {},
            "required_checks": [
                f"Verify the affected {domain} resource and its ownership",
                "Check workload and application dependencies",
                "Validate operational, security and compliance requirements",
                "Confirm the proposed change is safe and reversible",
            ],
        })

    if not proposals:
        raise ValueError("No actionable domain proposals were created.")

    return proposals


# ============================================================
# 3. HUMAN APPROVAL
# ============================================================

def collect_human_approval(proposal, interactive=True):
    """
    A = Approve, R = Reject, M = Modify.
    A modified action requires a second explicit confirmation.
    """
    result = {
        "decision": "PENDING",
        "approval_status": "Pending",
        "reviewer": None,
        "approval_reference": None,
        "validation_completed": False,
        "validation_evidence": None,
        "approved_action": proposal["proposed_action"],
        "decision_timestamp": None,
    }

    if not interactive:
        return result

    print("\n" + "=" * 65)
    print("                         HUMAN APPROVAL")
    print("=" * 65)
    print(f"\nAction: {proposal['action_id']}")
    print(f"Domain: {proposal['domain']}")
    print(f"Asset ID: {proposal.get('asset_id') or 'Not provided'}")
    print(f"Detected issue: {proposal['detected_issue']}")
    print(f"Proposed action: {proposal['proposed_action']}")
    print(
        "Estimated savings: "
        f"{money(proposal.get('estimated_monthly_savings_inr'))}/month"
    )
    print(f"Savings basis: {proposal['savings_basis']}")

    metrics = proposal.get("asset_metrics", {})
    if metrics:
        print(
            "Asset metrics: "
            f"unused={metrics.get('unused_capacity_tb')} TB; "
            f"utilization={metrics.get('utilization_pct')}%"
        )

    print("\nRequired checks:")
    for check in proposal["required_checks"]:
        print(f"- {check}")

    while True:
        decision = input(
            "\nA - Approve | R - Reject | M - Modify\n"
            "Select A / R / M: "
        ).strip().upper()

        if decision in {"A", "R", "M"}:
            break
        print("Invalid selection. Enter A, R or M.")

    result["decision"] = decision
    result["decision_timestamp"] = datetime.now().isoformat(
        timespec="seconds"
    )

    if decision == "R":
        result["approval_status"] = "Rejected"
        result["reviewer"] = input("Enter reviewer name/ID: ").strip()
        result["approval_reference"] = input(
            "Enter approval reference: "
        ).strip()
        return result

    if decision == "M":
        modified_action = input(
            "\nEnter the modified action for review: "
        ).strip()

        if not modified_action:
            result["approval_status"] = "Modification not provided"
            result["decision"] = "MODIFY_PENDING"
            return result

        result["approved_action"] = modified_action

        confirm = input(
            "Approve this modified action? (Y/N): "
        ).strip().upper()

        if confirm != "Y":
            result["approval_status"] = "Modified action not approved"
            result["decision"] = "MODIFY_NOT_APPROVED"
            result["approved_action"] = modified_action
            return result

    result["reviewer"] = input("Enter reviewer name/ID: ").strip()
    result["approval_reference"] = input(
        "Enter approval reference: "
    ).strip()

    validation = input(
        "Have all required operational checks been completed? (Y/N): "
    ).strip().upper()

    evidence = input(
        "Enter validation evidence/notes: "
    ).strip()

    result["validation_completed"] = validation == "Y"
    result["validation_evidence"] = evidence or None

    required_fields_present = all([
        result["reviewer"],
        result["approval_reference"],
        result["validation_completed"],
        result["validation_evidence"],
    ])

    if required_fields_present:
        result["approval_status"] = "Approved"
        result["decision"] = "APPROVED"
    else:
        result["approval_status"] = (
            "Pending - approval or validation details incomplete"
        )
        result["decision"] = "PENDING_VALIDATION"

    return result


# ============================================================
# 4. SIMULATED RPA EXECUTION
# ============================================================

def simulate_action(proposal, approval):
    if approval["approval_status"] != "Approved":
        return {
            "execution_status": "Not executed",
            "execution_result": (
                "Action was not executed because approval or validation "
                "requirements were not completed."
            ),
            "real_infrastructure_changes": False,
        }

    action = approval["approved_action"]
    asset_id = proposal.get("asset_id")

    target = f" for {asset_id}" if asset_id else ""

    return {
        "execution_status": "Successful - simulated",
        "execution_result": (
            f"DRY RUN: {action}{target} was simulated. "
            "No live infrastructure API, command or configuration was changed."
        ),
        "real_infrastructure_changes": False,
    }


# ============================================================
# 5. AUDIT LOG
# ============================================================

def append_audit_log(record):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(AUDIT_LOG, "a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")


# ============================================================
# 6. REPORT GENERATION
# ============================================================

def build_rpa_report(user_request, proposals, results):
    approved_count = sum(
        1 for item in results
        if item["approval"]["approval_status"] == "Approved"
    )
    rejected_count = sum(
        1 for item in results
        if item["approval"]["approval_status"] == "Rejected"
    )
    simulated_count = sum(
        1 for item in results
        if item["execution"]["execution_status"] == "Successful - simulated"
    )

    if simulated_count == len(results):
        workflow_status = "Workflow completed"
    elif approved_count or rejected_count:
        workflow_status = "Workflow partially completed"
    else:
        workflow_status = "Awaiting human approval"

    return {
        "report_title": "RPA Agent Execution Report",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "user_request": user_request,
        "workflow_status": workflow_status,
        "summary": {
            "total_actions": len(proposals),
            "approved_actions": approved_count,
            "rejected_actions": rejected_count,
            "simulated_actions": simulated_count,
            "real_infrastructure_changes": False,
        },
        "actions": results,
        "final_rpa_agent_response": (
            f"RPA reviewed {len(proposals)} action(s): "
            f"{approved_count} approved, {rejected_count} rejected, "
            f"and {simulated_count} simulated successfully. "
            "No live infrastructure changes were executed."
        ),
    }


def create_markdown_report(report):
    lines = [
        "# RPA Agent Execution Report",
        "",
        f"**Generated at:** {report['generated_at']}",
        f"**User request:** {report['user_request']}",
        f"**Workflow status:** {report['workflow_status']}",
        "",
        "## Execution summary",
        "",
        f"- Total actions: {report['summary']['total_actions']}",
        f"- Approved: {report['summary']['approved_actions']}",
        f"- Rejected: {report['summary']['rejected_actions']}",
        f"- Simulated successfully: {report['summary']['simulated_actions']}",
        "- Real infrastructure changes: No",
        "",
        "## Action details",
    ]

    for item in report["actions"]:
        proposal = item["proposal"]
        approval = item["approval"]
        execution = item["execution"]

        lines.extend([
            "",
            f"### {proposal['domain']} – {proposal['action_id']}",
            f"- Asset ID: {proposal.get('asset_id') or 'Not provided'}",
            f"- Action: {approval['approved_action']}",
            f"- Estimated savings: "
            f"{money(proposal.get('estimated_monthly_savings_inr'))}/month",
            f"- Human decision: {approval['decision']}",
            f"- Approval status: {approval['approval_status']}",
            f"- Execution status: {execution['execution_status']}",
            f"- Result: {execution['execution_result']}",
        ])

    lines.extend([
        "",
        "## Final RPA Agent response",
        "",
        report["final_rpa_agent_response"],
    ])

    return "\n".join(lines)


# ============================================================
# 7. MAIN RPA WORKFLOW
# ============================================================

def run_rpa_agent(
    user_request=None,
    supervisor_report=None,
    cost_report=None,
    interactive=True,
):
    """
    Standalone usage:
        python src/agents/rpa_agent.py

    Programmatic usage:
        run_rpa_agent(user_request="Analyze storage")

    The default standalone flow loads reports created by the existing
    Cost Agent and Supervisor Agent.
    """
    if supervisor_report is None:
        supervisor_report = load_json(SUPERVISOR_REPORT)

    supervisor_report = unwrap_supervisor_report(supervisor_report)

    if cost_report is None:
        cost_report = load_json(COST_AGENT_REPORT)

    if not isinstance(supervisor_report, dict):
        raise ValueError("Supervisor report must be a dictionary.")

    if not isinstance(cost_report, dict):
        raise ValueError("Cost Agent report must be a dictionary.")

    request = (
        user_request
        or supervisor_report.get("user_request")
        or cost_report.get("user_request")
        or "Not provided"
    )

    proposals = build_action_proposals(
        supervisor_report,
        cost_report,
    )

    results = []

    for proposal in proposals:
        approval = collect_human_approval(
            proposal,
            interactive=interactive,
        )

        execution = simulate_action(
            proposal,
            approval,
        )

        result = {
            "proposal": proposal,
            "approval": approval,
            "execution": execution,
        }
        results.append(result)

        append_audit_log({
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "user_request": request,
            "action_id": proposal["action_id"],
            "domain": proposal["domain"],
            "asset_id": proposal.get("asset_id"),
            "decision": approval["decision"],
            "approval_status": approval["approval_status"],
            "reviewer": approval["reviewer"],
            "approval_reference": approval["approval_reference"],
            "validation_completed": approval["validation_completed"],
            "execution_status": execution["execution_status"],
            "real_infrastructure_changes": False,
        })

    report = build_rpa_report(request, proposals, results)
    markdown = create_markdown_report(report)

    save_json(OUTPUT_JSON, report)
    OUTPUT_MD.write_text(markdown, encoding="utf-8")

    # Update the Supervisor report with the RPA handoff/results.
    supervisor_report["rpa_handoff"] = {
        "status": report["workflow_status"],
        "automation_allowed": False,
        "execution_completed": (
            report["summary"]["simulated_actions"] > 0
        ),
        "rpa_report_path": str(OUTPUT_JSON),
        "audit_log_path": str(AUDIT_LOG),
    }
    supervisor_report["rpa_execution_results"] = results
    supervisor_report["human_approval"] = {
        "required": True,
        "status": (
            "Approved" if report["summary"]["approved_actions"] else
            "Rejected" if report["summary"]["rejected_actions"] else
            "Pending"
        ),
        "approved_actions": [
            item for item in results
            if item["approval"]["approval_status"] == "Approved"
        ],
        "rejected_actions": [
            item for item in results
            if item["approval"]["approval_status"] == "Rejected"
        ],
    }
    save_json(SUPERVISOR_REPORT, supervisor_report)

    print("\n" + "=" * 65)
    print("                 RPA AGENT - EXECUTION SUMMARY")
    print("=" * 65)
    print(f"Workflow Status: {report['workflow_status']}")

    for item in results:
        proposal = item["proposal"]
        approval = item["approval"]
        execution = item["execution"]

        print("\n" + "-" * 60)
        print(f"Domain: {proposal['domain']}")
        print(f"Asset ID: {proposal.get('asset_id') or 'Not provided'}")
        print(f"Action: {approval['approved_action']}")
        print(
            "Estimated savings: "
            f"{money(proposal.get('estimated_monthly_savings_inr'))}/month"
        )
        print(f"Human decision: {approval['decision']}")
        print(f"Approval status: {approval['approval_status']}")
        print(f"Execution status: {execution['execution_status']}")
        print(f"Result: {execution['execution_result']}")

    print("\nFINAL RPA AGENT RESPONSE")
    print(report["final_rpa_agent_response"])
    print(f"\nJSON: {OUTPUT_JSON}")
    print(f"Markdown: {OUTPUT_MD}")
    print(f"Audit log: {AUDIT_LOG}")

    return report


if __name__ == "__main__":
    run_rpa_agent()
