from crewai import Agent, Crew, Process, Task
from crewai.tasks.task_output import TaskOutput
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import CSVSearchTool, FileReadTool, EXASearchTool, FileWriterTool
from tools.custom_tool import EmailSimulationTool, AppendCSVRowTool
import threading
import logging


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

task_outputs = {}
task_lock = threading.Lock()


def task_callback(output: TaskOutput):
    with task_lock:
        task_outputs[output.name] = output.raw
        logging.info(f"""Task completed! Name: {
                     output.name}, Output: {output.raw}""")


def format_email(self, incident_details):
    subject = f"""CRITICAL incident in {incident_details['component']} on {
        incident_details['timestamp']}"""
    body = f"""<html>
    <body>
        <h2>{subject}</h2>
        <p><strong>Incident Overview:</strong></p>
        <ul>
            <li><strong>Timestamp:</strong> {incident_details['timestamp']}</li>
            <li><strong>Severity:</strong> {incident_details['severity']}</li>
            <li><strong>Component:</strong> {incident_details['component']}</li>
            <li><strong>Message:</strong> {incident_details['message']}</li>
            <li><strong>Source:</strong> {incident_details['source']}</li>
            <li><strong>Stack Trace:</strong><br><pre>{incident_details['stack_trace']}</pre></li>
        </ul>
        <p><strong>Incident Metadata:</strong></p>
        <ul>
            <li><strong>Incident ID:</strong> {incident_details['incident_metadata']['incident_id']}</li>
            <li><strong>Priority:</strong> {incident_details['incident_metadata']['priority']}</li>
            <li><strong>Reason:</strong> {incident_details['incident_metadata']['reason']}</li>
        </ul>
        <p><strong>Root Cause Analysis:</strong></p>
        <ul>
            <li><strong>Summary:</strong> {incident_details['root_cause_analysis']['summary']}</li>
            <li><strong>Validation Steps:</strong> {incident_details['root_cause_analysis']['validation_steps']}</li>
        </ul>
        <p><strong>Suggested Resolutions:</strong></p>
        <p><strong>Internet-Sourced Resolutions:</strong></p>
        <ul>
            {''.join([f"<li>{res}</li>" for res in incident_details['internet_resolution']])}
        </ul>
        <p><strong>LLM-Generated Resolutions:</strong></p>
        <ul>
            {''.join([f"<li>{res}</li>" for res in incident_details['llm_resolution']])}
        </ul>
        <p><strong>Action Required:</strong> Due to the critical severity, immediate action is necessary. Please review the suggested resolutions and apply appropriate fixes to prevent a reoccurrence of this issue.</p>
        <p>Best regards,<br>Your Incident Management Team</p>
    </body>
    </html>"""
    return body

# def process_feedback(self, incident_details):
#     print("\nWas the resolution effective?")
#     feedback = input().strip().lower()

#     if feedback == "yes":
#         # Prepare data for appending to CSV
#         row_data = {
#             "Incident ID": incident_details["incident_metadata"]["incident_id"],
#             "Timestamp": incident_details["timestamp"],
#             "Component": incident_details["component"],
#             "Message": incident_details["message"],
#             "Source": incident_details["source"],
#             "Severity": incident_details["incident_metadata"]["severity"],
#             "Affected Modules": incident_details["details"].get("affected_modules", "N/A"),
#             "RCA Summary": incident_details["root_cause_analysis"]["summary"]
#         }
#         try:
#             print("Appending incident details to historical_incidents.csv...")
#             self.feedback_agent.run_tool(
#                 tool_name="Append CSV Row Tool",
#                 arguments={
#                     "file_path": ""
#                     "row_data": row_data
#                 }
#             )
#             print("Feedback recorded successfully.")
#         except Exception as e:
#             print(f"Error appending to CSV: {e}")

#     elif feedback == "no":
#         print(
#             "Please provide additional information about why the resolution did not work:")
#         user_input = input().strip()

#         incident_details["additional_user_info"] = user_input
#         print("Restarting the workflow with updated incident information...")
#         try:
#             self.rca_agent.run_task(
#                 "perform_root_cause_analysis", inputs=incident_details
#             )
#         except Exception as e:
#             print(f"Error restarting the process: {e}")

#     else:
#         print("Invalid input. Please respond with 'yes' or 'no'.")


@CrewBase
class IncidentManagementCrewai():
    """IncidentManagementCrewai crew"""

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def monitoring_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['monitoring_agent'],
            tools=[FileReadTool()],
            verbose=True,
        )

    @agent
    def classification_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['classification_agent'],
            verbose=True,
        )

    @agent
    def rca_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['rca_agent'],
            tools=[CSVSearchTool()],
            verbose=True,
        )

    @agent
    def resolution_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['resolution_agent'],
            tools=[EXASearchTool()],
            verbose=True,
        )

    @agent
    def notification_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['notification_agent'],
            tools=[EmailSimulationTool()],
            verbose=True,
            allow_delegation=False,
            on_generate=lambda incident_details: {
                "final_email_content": self.format_email(incident_details),
            },
        )

    # @agent
    # def feedback_agent(self) -> Agent:
    #     return Agent(
    #         config=self.agents_config['feedback_agent'],
    #         tools=[AppendCSVRowTool()],
    #         verbose=True
    #     )

    @task
    def monitor_system_logs(self) -> Task:
        return Task(
            config=self.tasks_config['monitor_system_logs'],
            callback=task_callback
        )

    @task
    def classify_incident_severity(self) -> Task:
        return Task(
            config=self.tasks_config['classify_incident_severity'],
            callback=task_callback
        )

    @task
    def perform_root_cause_analysis(self) -> Task:
        return Task(
            config=self.tasks_config['perform_root_cause_analysis'],
            callback=task_callback
        )

    @task
    def suggest_resolutions(self) -> Task:
        return Task(
            config=self.tasks_config['suggest_resolutions'],
            callback=task_callback
        )

    @task
    def notify_stakeholders(self) -> Task:
        return Task(
            config=self.tasks_config['notify_stakeholders'],
            callback=task_callback,
            on_run=lambda incident_details: self.notification_agent.run_tool(
                tool_name="EmailSimulationTool",
                arguments={
                    "recipient_email": "stakeholder@example.com",
                    "subject": f"CRITICAL incident in {incident_details['component']} on {incident_details['timestamp']}",
                    "body": self.format_email(incident_details),
                }
            )
        )

    # @task
    # def collect_and_process_feedback(self) -> Task:
    #     return Task(
    #         config=self.tasks_config['collect_and_process_feedback'],
    #         human_input=True,
    #         on_run=lambda incident_details: self.process_feedback(
    #             incident_details)
    #     )

    @crew
    def crew(self) -> Crew:
        """Creates the IncidentManagementCrewai crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            full_output=True,
            output_log_file="/Users/sayantankundu/Documents/incident_management_crewai/src/incident_management_crewai/logs/crew_output.txt"
        )
