from crewai import Agent, Crew, Process, Task  # type: ignore
from crewai.project import CrewBase, agent, crew, task  # type: ignore
from crewai_tools import CSVSearchTool, FileReadTool, EXASearchTool, FileWriterTool  # type: ignore
from incident_management_crewai.tools.custom_tool import EmailSimulationTool, AppendCSVRowTool


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


# def run_agents(self, incident_details):
#     """Run agents sequentially based on the tasks."""
#     try:
#         print("### Classifying Incident Severity")
#         self.classification_agent.run_task(
#             "classify_incident_severity", inputs=incident_details)

#         print("### Performing Root Cause Analysis")
#         self.rca_agent.run_task(
#             "perform_root_cause_analysis", inputs=incident_details)

#         print("### Suggesting Resolutions")
#         self.resolution_agent.run_task(
#             "suggest_resolutions", inputs=incident_details)

#         print("### Notifying Stakeholders")
#         self.notification_agent.run_task(
#             "notify_stakeholders", inputs=incident_details)

#         print("### Collecting Feedback")
#         self.feedback_agent.run_task(
#             "collect_and_process_feedback", inputs=incident_details)

#     except Exception as e:
#         print(f"Error while running agents: {e}")
#         raise


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
#                     "file_path": "/Users/sayantankundu/Documents/incident_management_crewai/src/incident_management_crewai/data/historical_incidents.csv",  # Adjust path if needed
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
            # Default config if any
            config=self.agents_config['monitoring_agent'],
            tools=[FileReadTool()],
            verbose=True,
            allow_delegation=False,
        )

    @agent
    def classification_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['classification_agent'],
            verbose=True,
            allow_delegation=False,
        )

    @agent
    def rca_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['rca_agent'],
            tools=[CSVSearchTool()],
            verbose=True,
            allow_delegation=False,
        )

    @agent
    def resolution_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['resolution_agent'],
            tools=[EXASearchTool()],
            verbose=True,
            allow_delegation=False,
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
            config=self.tasks_config['monitor_system_logs']
        )

    @task
    def classify_incident_severity(self) -> Task:
        return Task(
            config=self.tasks_config['classify_incident_severity']
        )

    @task
    def perform_root_cause_analysis(self) -> Task:
        return Task(
            config=self.tasks_config['perform_root_cause_analysis']
        )

    @task
    def suggest_resolutions(self) -> Task:
        return Task(
            config=self.tasks_config['suggest_resolutions']
        )

    @task
    def notify_stakeholders(self) -> Task:
        return Task(
            config=self.tasks_config['notify_stakeholders'],
            on_run=lambda incident_details: self.notification_agent.run_tool(
                tool_name="EmailSimulationTool",
                arguments={
                    "recipient_email": "stakeholder@example.com",  # Replace with recipient email
                    "subject": f"CRITICAL incident in {incident_details['component']} on {incident_details['timestamp']}",
                    "body": self.format_email(incident_details),
                }
            )
        )

    # @task
    # def process_log_task(self, log_content: str) -> Task:
    #     return Task(
    #         description=f"Process the log content:\n{log_content}",
    #         on_run=lambda incident_details: self.run_agents(incident_details)
    #     )

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
        )
