
from pathlib import Path


def classify_dataset(file_path):
    """
    Classify datasets based on their folder and file names.
    """

    path = Path(file_path).as_posix().lower()

    if "gwa" in path or "faststorage" in path:
        return "vmware"

    if "raw_query_timings" in path or "system_profiling_log" in path:
        return "database"

    if "asi_opensource_server_hourly" in path:
        return "compute_gpu"

    if "cache" in path or "pools" in path:
        return "storage"

    if path.endswith(".pdf") or "licens" in path:
        return "licensing"

    return "unknown"


def classify_datasets(file_paths):
    """
    Classify multiple dataset files.
    """

    classified_datasets = {}

    for file_path in file_paths:
        category = classify_dataset(file_path)

        classified_datasets.setdefault(category, []).append(
            str(file_path)
        )

    return classified_datasets
