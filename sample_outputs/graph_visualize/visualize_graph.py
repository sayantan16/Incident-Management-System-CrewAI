from incident_management_crewai.orchestrator.graph import LogOrchestrator


def generate_graph_visualization():

    orchestrator = LogOrchestrator()
    workflow = orchestrator.workflow
    dot_output = "digraph Workflow {\n"

    for node in workflow.nodes.keys():
        dot_output += f'''    "{node}" [shape=box];\n'''

    for edge in workflow.edges:
        source, target = edge
        dot_output += f'''    "{source}" -> "{target}";\n'''

    for source, branches in workflow.branches.items():
        for condition, branch in branches.items():
            for end_name, target in branch.ends.items():
                dot_output += f'''    "{source}" -> "{
                    target}" [label="{end_name}"];\n'''

    dot_output += "}\n"

    # Save the DOT file
    with open("workflow_graph.dot", "w") as file:
        file.write(dot_output)
    print("DOT file saved as 'workflow_graph.dot'.")


if __name__ == "__main__":
    generate_graph_visualization()
