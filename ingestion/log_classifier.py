
import re

# Rules for identifying VMware infrastructure events
CLASSIFICATION_RULES = {
    "STORAGE": {
        "keywords": [
    "nvme",
    "nvmedev",
    "datastore",
    "vmfs",
    "storage",
    "scsi",
    "naa.",
    "latency",
    "disk",
    "namespace",
    "controller",
    "path degraded"
],
        "issue_types": {
            "capacity": ["capacity", "space", "datastore"],
            "latency": ["latency", "slow", "timeout"],
            "device_discovery": [
    "discover",
    "namespace",
    "controller"
],

"device_scan_success": [
    "scan completed successfully"
]
        }
    },

    "CPU": {
        "keywords": [
            "cpu usage", "cpu utilization", "processor",
            "cpu contention", "cpu ready"
        ],
        "issue_types": {
            "high_cpu": ["high cpu", "cpu contention"],
            "cpu_contention": ["cpu ready", "processor contention"]
        }
    },

    "MEMORY": {
        "keywords": [
            "memory", "ballooning", "swapping",
            "out of memory", "heap", "oom"
        ],
        "issue_types": {
            "memory_pressure": ["ballooning", "swapping", "oom"],
            "memory_allocation": ["allocation", "out of memory"]
        }
    },

    "NETWORK": {
        "keywords": [
            "network", "vmnic", "nic", "packet",
            "connectivity", "ethernet", "tcp", "vlan"
        ],
        "issue_types": {
            "connectivity": ["connectivity", "link down", "interruption"],
            "packet_loss": ["packet loss", "dropped packets"],
            "network_interface": ["vmnic", "nic", "ethernet"]
        }
    },

    "VM_OPERATIONS": {
        "keywords": [
            "virtual machine", "vm power",
            "powered on", "powered off",
            "migration", "snapshot", "vMotion"
        ],
        "issue_types": {
            "vm_lifecycle": ["powered on", "powered off", "power"],
            "migration": ["migration", "vmotion"],
            "snapshot": ["snapshot"]
        }
    }
}


def classify_log(log):

    message = log.get("message", "").lower()

    # Preserve failed parsing records for investigation
    if log.get("parse_status") != "success":
        return {
            **log,
            "category": "UNCLASSIFIED",
            "issue_type": "PARSE_FAILURE",
            "classification_confidence": 0.0
        }

    matched_categories = []

    for category, rules in CLASSIFICATION_RULES.items():

        matched_keywords = [
            keyword for keyword in rules["keywords"]
            if re.search(
                r"(?<!\w)" + re.escape(keyword) + r"(?!\w)",
                message
            )
        ]

        if matched_keywords:
            matched_categories.append(
                (category, matched_keywords)
            )

    if not matched_categories:
        return {
            **log,
            "category": "UNCLASSIFIED",
            "issue_type": "UNKNOWN_EVENT",
            "classification_confidence": 0.0
        }

    # Select the category with the most matching keywords
    category, matched_keywords = max(
        matched_categories,
        key=lambda item: len(item[1])
    )

    rules = CLASSIFICATION_RULES[category]

    issue_type = "GENERAL_EVENT"

    for issue, keywords in rules["issue_types"].items():

        if any(keyword in message for keyword in keywords):
            issue_type = issue
            break

    # Simple rule-based confidence indicator, not an ML probability
    confidence = min(
        0.95,
        0.60 + (0.10 * (len(matched_keywords) - 1))
    )

    return {
        **log,
        "category": category,
        "issue_type": issue_type,
        "matched_keywords": matched_keywords,
        "classification_confidence": confidence
    }


def classify_all_logs(parsed_logs):

    classified_logs = []

    for log in parsed_logs:
        classified_logs.append(classify_log(log))

    return classified_logs


if __name__ == "__main__":

    from log_reader import read_all_logs
    from log_parser import parse_all_logs

    raw_logs = read_all_logs()
    parsed_logs = parse_all_logs(raw_logs)

    classified_logs = classify_all_logs(parsed_logs)

    print("\n========== CLASSIFIED VMWARE LOGS ==========\n")

    for log in classified_logs:

        print(
            f"File: {log['source_file']} | "
            f"Category: {log['category']} | "
            f"Issue: {log['issue_type']} | "
            f"Severity: {log.get('severity', 'UNKNOWN')}"
        )

    print("\n========== CLASSIFICATION SUMMARY ==========")

    categories = {}

    for log in classified_logs:
        category = log["category"]
        categories[category] = categories.get(category, 0) + 1

    for category, count in categories.items():
        print(f"{category}: {count}")

    print("\nTotal classified:", len(classified_logs))
