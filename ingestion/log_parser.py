
import re
from datetime import datetime


# VMware log parsing pattern
LOG_PATTERN = re.compile(
    r'^(?P<timestamp>\S+)\s+'
    r'(?P<level_code>[A-Za-z]{2})\((?P<level_id>\d+)\)\s+'
    r'(?P<component>[\w.-]+):\s*'
    r'(?P<details>.*)$'
)

# Extract CPU and World ID
CONTEXT_PATTERN = re.compile(
    r'cpu(?P<cpu_id>\d+):(?P<world_id>\d+)'
)

# Extract operation ID
OP_ID_PATTERN = re.compile(
    r'opID=(?P<operation_id>\S+)'
)


def parse_log_entry(log_entry):
    """
    Converts one raw VMware log entry into structured data.
    """

    raw_log = log_entry["raw_log"]

    match = LOG_PATTERN.match(raw_log)

    if not match:
        return {
            "source_file": log_entry["source_file"],
            "line_number": log_entry["line_number"],
            "raw_log": raw_log,
            "parse_status": "failed"
        }

    data = match.groupdict()

    details = data["details"]

    # Extract CPU and World ID
    context_match = CONTEXT_PATTERN.search(details)

    cpu_id = None
    world_id = None

    if context_match:
        cpu_id = int(context_match.group("cpu_id"))
        world_id = int(context_match.group("world_id"))

    # Extract operation ID
    op_match = OP_ID_PATTERN.search(details)

    operation_id = (
        op_match.group("operation_id")
        if op_match else None
    )

    # Determine severity
    severity_mapping = {
        "In": "INFO",
        "Wa": "WARNING",
        "Er": "ERROR",
        "Cr": "CRITICAL",
        "Db": "DEBUG"
    }

    severity = severity_mapping.get(
        data["level_code"], "UNKNOWN"
    )

    # Extract subsystem
    subsystem_match = re.search(
        r'(NVMEDEV|NvmeDiscover|NMP|VMFS|StorageDevice|'
        r'Network|TCP|SCSI)',
        details,
        re.IGNORECASE
    )

    subsystem = (
        subsystem_match.group(0)
        if subsystem_match else "GENERAL"
    )

    # Final structured output
    return {
        "source_file": log_entry["source_file"],
        "line_number": log_entry["line_number"],
        "timestamp": data["timestamp"],
        "component": data["component"],
        "severity": severity,
        "level_code": data["level_code"],
        "cpu_id": cpu_id,
        "world_id": world_id,
        "operation_id": operation_id,
        "subsystem": subsystem,
        "message": details,
        "raw_log": raw_log,
        "parse_status": "success"
    }


def parse_all_logs(log_entries):

    parsed_logs = []

    for entry in log_entries:
        parsed = parse_log_entry(entry)
        parsed_logs.append(parsed)

    return parsed_logs


if __name__ == "__main__":

    from log_reader import read_all_logs

    raw_logs = read_all_logs()

    parsed_logs = parse_all_logs(raw_logs)

    print("\n========== PARSED VMWARE LOGS ==========\n")

    for log in parsed_logs:
        print(log)

    successful = sum(
        1 for log in parsed_logs
        if log["parse_status"] == "success"
    )

    failed = len(parsed_logs) - successful

    print("\n========== PARSING SUMMARY ==========")
    print("Total logs:", len(parsed_logs))
    print("Successfully parsed:", successful)
    print("Failed:", failed)
