from typing import TypedDict, List


class LogState(TypedDict):
    # List of log file paths queued for processing
    log_queue: List[str]
    failed_logs: List[str]        # List of logs that failed to process
    processed_logs: List[str]     # List of successfully processed logs
    retry_count: dict[str, int]   # Retry count for each log
