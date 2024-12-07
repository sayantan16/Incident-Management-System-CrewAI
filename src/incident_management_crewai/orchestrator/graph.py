from langgraph.graph import StateGraph  # type: ignore
from incident_management_crewai.state import LogState
from .nodes import Nodes
from incident_management_crewai.crew import IncidentManagementCrewai
import os


class LogOrchestrator:
    def __init__(self):
        self.crew_ai = IncidentManagementCrewai()
        self.nodes = Nodes(log_dir=os.path.abspath(os.path.join(
            os.path.dirname(__file__), '../../incident_management_crewai/data')), crew_ai=self.crew_ai)
        self.workflow = StateGraph(LogState)

        # Add nodes
        self.workflow.add_node("monitor_logs", self.nodes.monitor_logs)
        self.workflow.add_node("process_log", self.nodes.process_single_log)
        self.workflow.add_node("wait", self.nodes.wait_next_run)

        self.workflow.set_entry_point("monitor_logs")
        self.workflow.add_conditional_edges(
            "monitor_logs",
            self.nodes.new_logs_found,
            {
                "continue": "process_log",
                "end": "wait"
            }
        )
        self.workflow.add_edge("process_log", "monitor_logs")
        self.workflow.add_edge("wait", "monitor_logs")

        self.app = self.workflow.compile()

    def run(self):
        initial_state = {
            "log_queue": [],
            "failed_logs": [],
            "processed_logs": [],
            "retry_count": {}
        }
        self.app.invoke(initial_state)
