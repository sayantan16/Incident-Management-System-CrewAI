from incident_management_crewai.orchestrator.graph import LogOrchestrator


def generate_graph_visualization():
    # Initialize the orchestrator
    orchestrator = LogOrchestrator()

    # Access the workflow (StateGraph)
    workflow = orchestrator.workflow

    # Create a DOT representation
    dot_output = "digraph Workflow {\n"

    # Add nodes to the graph
    for node in workflow.nodes.keys():
        dot_output += f'''    "{node}" [shape=box];\n'''

    # Add edges to the graph
    for edge in workflow.edges:
        source, target = edge
        dot_output += f'''    "{source}" -> "{target}";\n'''

    # Add conditional branches (if any)
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

    # Optionally, render the DOT file to an image (requires Graphviz installed)
    try:
        import graphviz
        graph = graphviz.Source(dot_output)
        graph.render("workflow_graph", format="png", cleanup=True)
        print("Graph visualization saved as 'workflow_graph.png'.")
    except ImportError:
        print("Graphviz not installed. Install it to generate PNG/SVG files.")


if __name__ == "__main__":
    generate_graph_visualization()
