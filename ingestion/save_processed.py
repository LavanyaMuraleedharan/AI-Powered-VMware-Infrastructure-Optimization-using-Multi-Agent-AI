
import json
from pathlib import Path

from log_reader import read_all_logs
from log_parser import parse_all_logs
from log_classifier import classify_all_logs


BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "processed"

OUTPUT_DIR.mkdir(exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "classified_logs.json"


def save_classified_logs():

    # Step 1: Read raw VMware logs
    raw_logs = read_all_logs()

    # Step 2: Parse logs
    parsed_logs = parse_all_logs(raw_logs)

    # Step 3: Classify logs
    classified_logs = classify_all_logs(parsed_logs)

    # Step 4: Save JSON
    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:

        json.dump(
            classified_logs,
            file,
            indent=4
        )

    print("\n========== DATA PERSISTENCE ==========")
    print("Total records:", len(classified_logs))
    print("Saved to:", OUTPUT_FILE)


if __name__ == "__main__":
    save_classified_logs()
