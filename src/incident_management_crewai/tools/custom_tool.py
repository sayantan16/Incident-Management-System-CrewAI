from crewai.tools import BaseTool  # type: ignore
from typing import Type
from pydantic import BaseModel, Field  # type: ignore
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import csv
import os


class EmailSimulationToolInput(BaseModel):
    """Input schema for EmailSimulationTool."""
    recipient_email: str = Field(...,
                                 description="The recipient's email address.")
    subject: str = Field(..., description="The subject line of the email.")
    body: str = Field(...,
                      description="The HTML or plain text body of the email.")


class EmailSimulationTool(BaseTool):
    name: str = "Email Simulation Tool"
    description: str = (
        "This tool sends an email notification with the specified recipient email, subject, and body."
    )
    args_schema: Type[BaseModel] = EmailSimulationToolInput

    def _run(self, recipient_email: str, subject: str, body: str) -> str:
        smtp_server = "localhost"
        smtp_port = 1025
        sender_email = "noreply@simulation.com"

        try:
            msg = MIMEMultipart()
            msg["From"] = sender_email
            msg["To"] = recipient_email
            msg["Subject"] = subject

            msg.attach(MIMEText(body, "html"))

            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.sendmail(sender_email, recipient_email, msg.as_string())

            return f"Email successfully sent to {recipient_email} with subject '{subject}'."
        except Exception as e:
            return f"Failed to send email: {str(e)}"


class AppendCSVRowToolInput(BaseModel):
    """Input schema for the CSV appending tool."""
    file_path: str = Field(..., description="Path to the CSV file.")
    row_data: dict = Field(
        ..., description="Row data to append as a dictionary with keys matching column names.")


class AppendCSVRowTool(BaseTool):
    name: str = "Append CSV Row Tool"
    description: str = (
        "Appends a new row of data to an existing CSV file. If the file does not exist, creates it with headers based on the provided data."
    )
    args_schema: Type[BaseModel] = AppendCSVRowToolInput

    def _run(self, file_path: str, row_data: dict) -> str:
        try:
            file_exists = os.path.exists(file_path)

            with open(file_path, mode='a', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=row_data.keys())

                if not file_exists:
                    writer.writeheader()

                writer.writerow(row_data)

            return f"Row successfully added to {file_path}."
        except Exception as e:
            return f"Failed to write to CSV file: {e}"
