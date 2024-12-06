#!/usr/bin/env python
from incident_management_crewai.orchestrator.graph import LogOrchestrator


def run():
    orchestrator = LogOrchestrator()
    orchestrator.run()


if __name__ == "__main__":
    run()
