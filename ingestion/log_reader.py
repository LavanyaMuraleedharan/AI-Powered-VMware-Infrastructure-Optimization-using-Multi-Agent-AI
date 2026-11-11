
from pathlib import Path


# Project root directory
BASE_DIR = Path(__file__).resolve().parent.parent

# ESXi log directory
LOG_DIR = BASE_DIR / "logs" / "esxi"


def read_log_file(file_path):
    """
    Reads a VMware log file and returns individual log entries.
    """

    log_entries = []

    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as file:

            for line_number, line in enumerate(file, start=1):

                line = line.strip()

                if not line:
                    continue

                log_entries.append({
                    "source_file": file_path.name,
                    "line_number": line_number,
                    "raw_log": line
                })

        print(f"[SUCCESS] Read {len(log_entries)} entries from {file_path.name}")

    except FileNotFoundError:
        print(f"[ERROR] File not found: {file_path}")

    except OSError as error:
        print(f"[ERROR] Unable to read {file_path}: {error}")

    return log_entries


def read_all_logs():
    """
    Reads all .log files from the ESXi directory.
    """

    all_logs = []

    if not LOG_DIR.exists():
        print(f"[ERROR] Log directory does not exist: {LOG_DIR}")
        return all_logs

    log_files = sorted(LOG_DIR.glob("*.log"))

    if not log_files:
        print("[WARNING] No log files found.")
        return all_logs

    for log_file in log_files:
        entries = read_log_file(log_file)
        all_logs.extend(entries)

    return all_logs


if __name__ == "__main__":

    logs = read_all_logs()

    print("\n========== LOG READER OUTPUT ==========")

    for log in logs:
        print(log)

    print("\nTotal log entries:", len(logs))
