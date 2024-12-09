import os
import time
import logging
import json

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')


class Nodes:
    def __init__(self, log_dir: str, crew_ai):
        self.log_dir = log_dir
        self.crew_ai = crew_ai

        # Ensure the log directory exists
        os.makedirs(self.log_dir, exist_ok=True)

    def monitor_logs(self, state):
        logging.info("# Monitoring logs")
        existing_logs = state.get("log_queue", [])
        processed_logs = state.get("processed_logs", [])
        failed_logs = state.get("failed_logs", [])

        # List all log files, excluding hidden files
        all_logs = [log for log in os.listdir(
            self.log_dir) if not log.startswith(".")]

        # Identify new logs that are not in existing, processed, or failed logs
        new_logs = [
            log for log in all_logs
            if log not in existing_logs and log not in processed_logs and log not in failed_logs
        ]

        if not new_logs and state.get("empty_checks", 0) >= 5:
            logging.info("## No new logs for 5 iterations. Stopping workflow.")
            state["stop_workflow"] = True
            return state

        if not new_logs:
            logging.info("## No new logs found in this iteration.")
            state["empty_checks"] = state.get("empty_checks", 0) + 1
        else:
            logging.info(f"## New logs found: {new_logs}")
            state["log_queue"].extend(new_logs)
            state["empty_checks"] = 0

        return state

    def new_logs_found(self, state):
        if state.get("log_queue"):
            logging.info("## New logs detected in the queue.")
            return "continue"
        else:
            logging.info("## No new logs available to process.")
            return "end"

    def clear_log_file(self):
        log_file_path = "/Users/sayantankundu/Documents/incident_management_crewai/src/incident_management_crewai/logs/crew_output.txt"
        try:
            # Clear the content of the log file
            open(log_file_path, 'w').close()
            logging.info(f"Log file '{log_file_path}' cleared successfully.")
        except Exception as e:
            logging.error(f"Failed to clear log file '{log_file_path}': {e}")

    def process_single_log(self, state):
        self.clear_log_file()  # Clear the log file before starting

        if not state["log_queue"]:
            logging.info("No logs available in the queue to process.")
            return state

        log_file = state["log_queue"].pop(0)
        logging.info(f"Processing log: {log_file}")

        try:
            inputs = {
                "log_file_path": os.path.join(self.log_dir, log_file),
                "csv_file_path": os.path.abspath(os.path.join(os.path.dirname(__file__), '../../history/historical_incidents.csv'))
            }

            logging.info(f"Inputs passed to CrewAI kickoff: {inputs}")

            # Kickoff CrewAI workflow
            crew_output = self.crew_ai.crew().kickoff(inputs=inputs)

            # Log various outputs
            logging.info(f"Raw Output: {crew_output.raw}")

            if crew_output.json_dict:
                logging.info(f"""JSON Output:\n{json.dumps(
                    crew_output.json_dict, indent=2)}""")

            if crew_output.pydantic:
                logging.info(f"Pydantic Output: {crew_output.pydantic}")

            logging.info(f"Tasks Output: {crew_output.tasks_output}")
            logging.info(f"Token Usage: {crew_output.token_usage}")

            state["processed_logs"].append(log_file)
            logging.info(f"Successfully processed log: {log_file}")

        except Exception as e:
            logging.error(f"Error processing log '{log_file}': {e}")

            retry_count = state.setdefault(
                "retry_count", {}).get(log_file, 0) + 1
            state["retry_count"][log_file] = retry_count

            if retry_count <= 3:
                logging.info(
                    f"Re-queueing log '{log_file}' (Retry {retry_count}/3)")
                state["log_queue"].append(log_file)
            else:
                logging.info(f"""Moving log '{
                             log_file}' to failed_logs after 3 failed attempts.""")
                state["failed_logs"].append(log_file)

        return state

    def wait_next_run(self, state):
        logging.info("## Waiting for 10 seconds before the next run.")
        time.sleep(10)
        return state
