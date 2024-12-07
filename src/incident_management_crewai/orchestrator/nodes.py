import os
import time


class Nodes:
    def __init__(self, log_dir: str, crew_ai):
        self.log_dir = log_dir
        self.crew_ai = crew_ai

    def monitor_logs(self, state):
        print("# Monitoring logs")
        existing_logs = state.get("log_queue", [])
        processed_logs = state.get("processed_logs", [])

        # List all log files, excluding .gitkeep and other hidden files
        all_logs = [
            log for log in os.listdir(self.log_dir)
            if log != ".gitkeep" and not log.startswith(".")
        ]

        new_logs = [
            log for log in all_logs
            if log not in existing_logs and log not in processed_logs
        ]

        if not new_logs and state.get("empty_checks", 0) >= 5:
            print("## No new logs for 5 iterations. Stopping workflow.")
            state["stop_workflow"] = True
            return state

        if not new_logs:
            print("## No new logs")
            state["empty_checks"] = state.get("empty_checks", 0) + 1
        else:
            state["log_queue"].extend(new_logs)
            state["empty_checks"] = 0

        return state

    def new_logs_found(self, state):
        if len(state.get("log_queue", [])) > 0:
            print("## New logs found")
            return "continue"
        else:
            print("## No new logs")
            return "end"

    def process_single_log(self, state):
        if not state["log_queue"]:
            print("## No logs to process")
            return state

        log_file = state["log_queue"].pop(0)
        print(f"### Processing log: {log_file}")

        try:
            # Prepare the inputs for CrewAI kickoff
            inputs = {
                "log_file_path": os.path.join(self.log_dir, log_file),
                "csv_file_path": os.path.abspath(os.path.join(os.path.dirname(__file__), '../../history/historical_incidents.csv'))
            }

            print(f"Inputs passed to kickoff: {inputs}")

            # Directly kickoff CrewAI with both file paths
            self.crew_ai.crew().kickoff(inputs=inputs)

            # Mark log as processed
            state["processed_logs"].append(log_file)
            print(f"### Successfully processed log: {log_file}")

        except Exception as e:
            print(f"### Error processing log {log_file}: {e}")

            # Track retries
            retry_count = state["retry_count"].get(log_file, 0) + 1
            state["retry_count"][log_file] = retry_count

            if retry_count <= 3:
                print(
                    f"### Re-queueing log {log_file} (Retry {retry_count}/3)")
                state["log_queue"].append(log_file)
            else:
                print(f"### Moving log {log_file} to failed_logs")
                state["failed_logs"].append(log_file)

        return state

    def wait_next_run(self, state):
        print("## Waiting for 60 seconds")
        time.sleep(60)
        return state
