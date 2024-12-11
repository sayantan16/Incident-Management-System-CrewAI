import dash
from dash import dcc, html, Input, Output, State, ctx
import dash_bootstrap_components as dbc
import pandas as pd
import os
import threading
from orchestrator.graph import LogOrchestrator
import logging
import json
import glob
import base64

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    external_scripts=[
        "https://cdn.jsdelivr.net/npm/animejs@3.2.1/lib/anime.min.js"
    ]
)
server = app.server
orchestrator = LogOrchestrator()

tasks = [
    "monitor_system_logs",          # card1, top-left
    "classify_incident_severity",   # card2, top-right
    "perform_root_cause_analysis",  # card3, second row right
    "suggest_resolutions",          # card4, second row left
    "notify_stakeholders"           # card5, third row left
]

DATA_FOLDER_PATH = "/Users/sayantankundu/Documents/incident_management_crewai/src/incident_management_crewai/data"
LOG_FILE_PATH = "/Users/sayantankundu/Documents/incident_management_crewai/src/incident_management_crewai/logs/crew_output.txt"


def clear_data_folder():
    for file_path in glob.glob(os.path.join(DATA_FOLDER_PATH, "*")):
        if os.path.basename(file_path) != ".gitkeep":
            os.remove(file_path)


def clear_log_file():
    open(LOG_FILE_PATH, 'w').close()


def read_classify_incident_severity_from_logs():
    if not os.path.exists(LOG_FILE_PATH):
        return None

    with open(LOG_FILE_PATH, 'r') as f:
        lines = f.readlines()

    classify_output_lines = []
    start_collecting = False
    for line in lines:
        if 'task_name="classify_incident_severity"' in line:
            start_collecting = True
            classify_output_lines = [line]
        elif start_collecting:
            if 'task_name=' in line and 'classify_incident_severity' not in line:
                break
            classify_output_lines.append(line)

    if not classify_output_lines:
        return None

    full_output = "".join(classify_output_lines)
    if 'output="' not in full_output:
        return None

    json_str = full_output.split('output="', 1)[-1]
    if '"' in json_str:
        json_str = json_str.rsplit('"', 1)[0]

    json_str = json_str.replace('\n', '').replace('\r', '')

    try:
        parsed = json.loads(json_str)
        if isinstance(parsed, str):
            parsed = json.loads(parsed)
        if isinstance(parsed, dict):
            return parsed
    except (json.JSONDecodeError, ValueError):
        return None
    return None


app.layout = dbc.Container(fluid=False, className="p-4", children=[

    dcc.Store(id='severity-store',
              data={"CRITICAL": 0, "ERROR": 0, "WARNING": 0, "INFO": 0}),
    dcc.Store(id='processed-incidents', data=[]),
    dcc.Store(id='processed-once', data=False),
    dcc.Store(id='arrow-trigger', data={"completed_task": None}),

    dbc.Card(
        dbc.CardBody(
            html.H2("Incident Management Dashboard",
                    className="text-white text-center mb-0")
        ),
        className="mb-4 bg-dark border-info"
    ),

    dbc.Row([
        dbc.Col([
            dbc.Card(
                dbc.CardBody([
                    html.H4("Log Severity Levels",
                            className="text-white mb-3"),
                    dcc.Graph(id='severity-bar-chart',
                              style={'height': '300px'})
                ]),
                className="mb-4 bg-dark border-info"
            )
        ])
    ]),

    html.H4("Task Workflow", className="text-white mb-3"),
    html.Div(id='workflow-container', className='workflow-container', children=[
        html.Div(id='task-workflow', className='zigzag-layout')
    ]),

    dbc.Card(
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dcc.Upload(
                        id='upload-log',
                        children=html.Button(
                            'Upload Log File', className="btn btn-primary animated-btn"),
                        multiple=True,
                        disabled=False
                    ),
                    html.Div(id='selected-file-name',
                             className="mt-2 text-white")
                ], width=4),
                dbc.Col([
                    dbc.Button("Process Log", id="process-log-button",
                               color="primary", disabled=True, className="animated-btn")
                ], width=4, className="d-flex align-items-start"),
                dbc.Col([
                    dbc.Button("Add More Files", id="add-more-files-button",
                               color="secondary", disabled=True, className="animated-btn")
                ], width=4, className="d-flex align-items-start")
            ], className="mb-3", justify="around"),
            dbc.Spinner(html.Div(id='upload-status',
                        className="mt-2 text-white"))
        ]),
        className="bg-dark border-info mb-4"
    ),

    dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Add Additional Files")),
            dbc.ModalBody([
                dcc.Upload(
                    id='additional-upload',
                    children=html.Button(
                        'Select Files', className="btn btn-primary animated-btn"),
                    multiple=True
                ),
                html.Div(id='additional-files-names',
                         className="mt-2 text-white"),
            ]),
            dbc.ModalFooter([
                dbc.Button("Confirm", id="confirm-add-files",
                           color="success", className="me-2 animated-btn"),
                dbc.Button("Close", id="close-add-files-modal",
                           className="btn btn-secondary animated-btn")
            ])
        ],
        id="add-files-modal",
        is_open=False,
        backdrop="static"
    ),

    dcc.Interval(id='interval-component', interval=3000, n_intervals=0)
])


@app.callback(
    Output('severity-bar-chart', 'figure'),
    Input('interval-component', 'n_intervals'),
    State('severity-store', 'data'),
    State('processed-incidents', 'data')
)
def update_bar_chart(n, severity_data, processed_incidents):
    # Show total based on number of processed incidents
    total_count = len(processed_incidents)

    df = pd.DataFrame(list(severity_data.items()),
                      columns=["Severity", "Count"])
    fig = {
        'data': [{
            'x': df['Severity'],
            'y': df['Count'],
            'type': 'bar',
            'marker': {'color': '#17a2b8'},
            'name': 'Log Severity'
        }],
        'layout': {
            'plot_bgcolor': '#222222',
            'paper_bgcolor': '#222222',
            'font': {'color': 'white'},
            'xaxis': {'title': 'Severity'},
            'yaxis': {'title': 'Count', 'autorange': True},
            'title': f'Log Severity Levels',
            'transition': {'duration': 500, 'easing': 'cubic-in-out'}
        }
    }
    return fig


@app.callback(
    [Output('task-workflow', 'children'),
     Output('severity-store', 'data'),
     Output('processed-incidents', 'data'),
     Output('arrow-trigger', 'data')],
    Input('interval-component', 'n_intervals'),
    State('severity-store', 'data'),
    State('processed-incidents', 'data'),
    State('arrow-trigger', 'data')
)
def update_task_outputs(n, severity_data, processed_incidents, arrow_data):
    task_data = parse_log_file()

    rca_completed = False
    classify_completed = False
    completed_tasks_indices = []

    for i, task in enumerate(tasks):
        output = task_data.get(task)
        formatted_output = "⏳ In Progress..."
        task_completed = False

        if output and 'status="completed"' in output:
            task_completed = True

        if output:
            try:
                json_output = output.split('output=')[-1].strip()
                json_output = json_output.replace('\n', '').replace('\r', '')
                parsed_json = json.loads(json_output)
                if isinstance(parsed_json, str):
                    parsed_json = json.loads(parsed_json)
                if isinstance(parsed_json, dict):
                    formatted_output = json.dumps(parsed_json, indent=2)
                else:
                    formatted_output = json_output
            except (json.JSONDecodeError, ValueError):
                formatted_output = output

        status_class = "pending"
        if 'In Progress' in formatted_output:
            status_class = "in-progress"
        if task_completed:
            status_class = "completed"
            completed_tasks_indices.append(i)

        card = dbc.Card(
            [
                html.H5(task.replace('_', ' ').title(),
                        className='workflow-card-title'),
                html.Div(
                    html.Pre(formatted_output,
                             className='workflow-card-output'),
                    className='workflow-card-output-container'
                )
            ],
            className=f'workflow-card {status_class} card{i+1}',
            style={"width": "300px", "height": "200px"}
        )

        if i == 0:
            card1 = card
        elif i == 1:
            card2 = card
        elif i == 2:
            card3 = card
        elif i == 3:
            card4 = card
        elif i == 4:
            card5 = card

    layout = html.Div([
        card1,
        card2,
        card3,
        card4,
        card5,
        html.Div(className='wf-arrow arrow-1-2'),
        html.Div(className='wf-arrow arrow-2-3'),
        html.Div(className='wf-arrow arrow-3-4'),
        html.Div(className='wf-arrow arrow-4-5')
    ], className='zigzag-layout')

    if task_data.get("perform_root_cause_analysis") and 'status="completed"' in task_data["perform_root_cause_analysis"]:
        rca_completed = True
    if task_data.get("classify_incident_severity") and 'status="completed"' in task_data["classify_incident_severity"]:
        classify_completed = True

    if rca_completed and classify_completed:
        parsed = read_classify_incident_severity_from_logs()
        if parsed and isinstance(parsed, dict):
            incident_meta = parsed.get("incident_metadata", {})
            reason = incident_meta.get("reason", "").upper()
            incident_id = incident_meta.get("incident_id", None)
            if incident_id and incident_id not in processed_incidents:
                severity_to_increment = None
                if "CRITICAL" in reason:
                    severity_to_increment = "CRITICAL"
                elif "ERROR" in reason:
                    severity_to_increment = "ERROR"
                elif "WARNING" in reason:
                    severity_to_increment = "WARNING"
                elif "INFO" in reason:
                    severity_to_increment = "INFO"

                if severity_to_increment and severity_to_increment in severity_data:
                    severity_data[severity_to_increment] += 1
                    processed_incidents.append(incident_id)

    # Arrow triggering logic unchanged
    previously_completed_task = arrow_data.get("completed_task", None)
    new_completed_task = None
    for i, task in enumerate(tasks):
        if i in completed_tasks_indices:
            if previously_completed_task is None or i > previously_completed_task:
                new_completed_task = i
                break

    if new_completed_task is not None:
        arrow_data["completed_task"] = new_completed_task

    return layout, severity_data, processed_incidents, arrow_data


@app.callback(
    Output('selected-file-name', 'children'),
    Input('upload-log', 'filename')
)
def show_selected_file(filenames):
    if not filenames:
        return ""
    if isinstance(filenames, str):
        return f"Selected Files: {filenames}"
    else:
        return "Selected Files: " + ", ".join(filenames)


# Original logic restored, just add what you requested
@app.callback(
    [Output('upload-status', 'children'),
     Output('add-more-files-button', 'disabled'),
     Output('processed-once', 'data'),
     Output('add-more-files-button', 'color'),
     Output('upload-log', 'disabled')],
    Input('process-log-button', 'n_clicks'),
    State('upload-log', 'filename'),
    State('upload-log', 'contents'),
    State('processed-once', 'data')
)
def process_log(n_clicks, filenames, contents, processed_once):
    if processed_once:
        return "Already processed once. Please restart the app.", True, processed_once, "secondary", False

    if n_clicks and filenames:
        if isinstance(filenames, str):
            filenames = [filenames]
            contents = [contents]

        for fname, fcontent in zip(filenames, contents):
            log_path = os.path.join(DATA_FOLDER_PATH, fname)
            with open(log_path, "wb") as f:
                f.write(fcontent.encode('utf-8'))

        clear_log_file()

        def run_orchestrator():
            try:
                orchestrator.run()
                logging.info("Orchestrator run completed successfully.")
            except Exception as e:
                logging.error(f"Error during orchestrator run: {e}")

        threading.Thread(target=run_orchestrator).start()

        # After processing:
        # - Add more files button enabled (False for disabled means enabled)
        # - Change add-more-files-button color to "info"
        # - Disable upload log file
        return f"Processing {', '.join(filenames)}...", False, True, "info", True

    return "Please upload a log file.", True, processed_once, "secondary", False


@app.callback(
    Output('process-log-button', 'disabled'),
    [Input('upload-log', 'filename'),
     Input('processed-once', 'data')]
)
def toggle_process_button(filenames, processed_once):
    # Original logic: enable process button if a file is chosen and not processed once
    if processed_once:
        return True
    if not filenames:
        return True
    return False


@app.callback(
    Output('add-files-modal', 'is_open'),
    [Input('add-more-files-button', 'n_clicks'),
     Input('close-add-files-modal', 'n_clicks'),
     Input('confirm-add-files', 'n_clicks')],
    [State('additional-upload', 'filename'),
     State('additional-upload', 'contents'),
     State('add-files-modal', 'is_open')]
)
def handle_modal(add_click, close_click, confirm_click, filenames, contents, is_open):
    triggered_id = ctx.triggered_id if hasattr(ctx, 'triggered_id') else None

    if triggered_id == 'add-more-files-button':
        return not is_open
    if triggered_id == 'close-add-files-modal':
        return False
    if triggered_id == 'confirm-add-files':
        if filenames and contents:
            if isinstance(filenames, str):
                filenames = [filenames]
                contents = [contents]
            for name, file_content in zip(filenames, contents):
                content_string = file_content.split('base64,')[-1]
                decoded = base64.b64decode(content_string)
                file_path = os.path.join(DATA_FOLDER_PATH, name)
                with open(file_path, 'wb') as f:
                    f.write(decoded)
        return False
    return is_open


@app.callback(
    Output('additional-files-names', 'children'),
    Input('additional-upload', 'filename')
)
def show_additional_files_modal(filenames):
    if filenames is None:
        return ""
    if isinstance(filenames, str):
        return f"Selected Files: {filenames}"
    else:
        files_list = [html.Li(file) for file in filenames]
        return html.Div([
            html.P("Selected Files:"),
            html.Ul(files_list)
        ], className="mt-2")


@app.callback(
    Output('upload-log', 'children'),
    Input('add-more-files-button', 'n_clicks')
)
def add_more_files(n_clicks):
    return html.Button('Upload Log File', className="btn btn-primary animated-btn")


def parse_log_file():
    task_data = {task: None for task in tasks}
    if not os.path.exists(LOG_FILE_PATH):
        return task_data

    with open(LOG_FILE_PATH, 'r') as f:
        lines = f.readlines()

    current_task = None
    current_output = []
    for line in lines:
        if "task_name=" in line:
            if current_task and current_output:
                task_data[current_task] = "".join(current_output).strip()
            current_task = line.split('task_name="')[1].split('"')[0]
            current_output = [line]
        elif current_task:
            current_output.append(line)

    if current_task and current_output:
        task_data[current_task] = "".join(current_output).strip()

    return task_data


if __name__ == '__main__':
    clear_data_folder()
    clear_log_file()
    app.run_server(debug=True)
