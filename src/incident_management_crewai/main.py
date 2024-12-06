#!/usr/bin/env python
import sys
from incident_management_crewai.crew import IncidentManagementCrewai


def run():
    # Dynamic inputs for your tools
    inputs = {
        'log_file_path': '/Users/sayantankundu/Documents/incident_management_crewai/src/incident_management_crewai/data/logs.txt',
        'csv_file_path': '/Users/sayantankundu/Documents/incident_management_crewai/history/historical_incidents.csv'
    }

    print(f"Inputs passed to kickoff: {inputs}")

    # Kickoff the Crew with dynamic inputs
    IncidentManagementCrewai().crew().kickoff(inputs=inputs)


if __name__ == "__main__":
    run()
