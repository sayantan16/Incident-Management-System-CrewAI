import dash
from dash import dcc, html, Input, Output, State, ctx
import dash_bootstrap_components as dbc
import pandas as pd
import os
import threading
from orchestrator.graph import LogOrchestrator
import logging
from threading import Lock
import json
import glob
import base64

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
server = app.server
orchestrator = LogOrchestrator()

tasks = [
    "monitor_system_logs",
    "classify_incident_severity",
    "perform_root_cause_analysis",
    "suggest_resolutions",
    "notify_stakeholders"
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
    """Read the classify_incident_severity output from the log file directly and return parsed JSON if found."""
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

    html.H4("Task Outputs", className="text-white mb-3"),

    html.Div(id='task-output-cards', className="mb-4"),

    dbc.Card(
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dcc.Upload(
                        id='upload-log',
                        children=html.Button(
                            'Upload Log File', className="btn btn-primary"),
                        multiple=True
                    ),
                    html.Div(id='selected-file-name',
                             className="mt-2 text-white")
                ], width=4),
                dbc.Col([
                    dbc.Button("Process Log", id="process-log-button",
                               color="primary", disabled=True)
                ], width=4, className="d-flex align-items-start"),
                dbc.Col([
                    dbc.Button("Add More Files", id="add-more-files-button",
                               color="secondary", disabled=True)
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
                        'Select Files', className="btn btn-primary"),
                    multiple=True
                ),
                html.Div(id='additional-files-names',
                         className="mt-2 text-white"),
            ]),
            dbc.ModalFooter([
                dbc.Button("Confirm", id="confirm-add-files",
                           color="success", className="me-2"),
                dbc.Button("Close", id="close-add-files-modal",
                           className="btn btn-secondary")
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
    State('severity-store', 'data')
)
def update_bar_chart(n, severity_data):
    total_count = sum(severity_data.values())
    df = pd.DataFrame(list(severity_data.items()),
                      columns=["Severity", "Count"])
    fig = {
        'data': [{
            'x': df['Severity'],
            'y': df['Count'],
            'type': 'bar',
            'marker': {'color': '#17a2b8'}
        }],
        'layout': {
            'plot_bgcolor': '#222222',
            'paper_bgcolor': '#222222',
            'font': {'color': 'white'},
            'xaxis': {'title': 'Severity'},
            'yaxis': {'title': 'Count', 'autorange': True},
            'title': f'Log Severity Levels (Total: {total_count})'
        }
    }
    return fig


@app.callback(
    [Output('task-output-cards', 'children'),
     Output('severity-store', 'data'),
     Output('processed-incidents', 'data')],
    Input('interval-component', 'n_intervals'),
    State('severity-store', 'data'),
    State('processed-incidents', 'data')
)
def update_task_outputs(n, severity_data, processed_incidents):
    task_data = parse_log_file()
    cards = []

    rca_completed = False
    classify_completed = False

    if task_data.get("perform_root_cause_analysis"):
        if 'status="completed"' in task_data["perform_root_cause_analysis"]:
            rca_completed = True

    if task_data.get("classify_incident_severity"):
        if 'status="completed"' in task_data["classify_incident_severity"]:
            classify_completed = True

    for task in tasks:
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

        card = dbc.Card([
            dbc.CardBody([
                html.H4(task.replace('_', ' ').title(),
                        className='card-title mb-3',
                        style={'fontSize': '20px', 'color': '#17a2b8', 'fontWeight': 'bold'}),
                html.Pre(
                    formatted_output,
                    className='card-text text-white',
                    style={
                        'whiteSpace': 'pre-wrap',
                        'wordBreak': 'break-all',
                        'maxHeight': '200px',
                        'overflowY': 'auto'
                    }
                ),
                dbc.Alert("✅ Completed" if task_completed else "⏳ Processing...",
                          color="success" if task_completed else "warning", className="mt-3")
            ])
        ], className='mb-3 bg-dark border-info')
        cards.append(card)

    # If both tasks are completed, try to increment severity if new incident
    if rca_completed and classify_completed:
        parsed = read_classify_incident_severity_from_logs()
        if parsed and isinstance(parsed, dict):
            incident_meta = parsed.get("incident_metadata", {})
            reason = incident_meta.get("reason", "").upper()
            incident_id = incident_meta.get("incident_id", None)

            # Only increment if we have a new incident_id
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

    layout = html.Div([
        dbc.Row([dbc.Col(cards[0] if len(cards) > 0 else html.Div(), width=6),
                 dbc.Col(cards[1] if len(cards) > 1 else html.Div(), width=6)], className="mb-3"),
        dbc.Row([dbc.Col(cards[2] if len(cards) > 2 else html.Div(), width=6),
                 dbc.Col(cards[3] if len(cards) > 3 else html.Div(), width=6)], className="mb-3"),
        dbc.Row([dbc.Col(cards[4] if len(cards) > 4 else html.Div(), width=6),
                 dbc.Col(html.Div(), width=6)])
    ])
    return layout, severity_data, processed_incidents


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


@app.callback(
    [Output('upload-status', 'children'),
     Output('add-more-files-button', 'disabled'),
     Output('processed-once', 'data')],
    Input('process-log-button', 'n_clicks'),
    State('upload-log', 'filename'),
    State('upload-log', 'contents'),
    State('processed-once', 'data')
)
def process_log(n_clicks, filenames, contents, processed_once):
    if processed_once:
        return "Already processed once. Please restart the app.", True, processed_once

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
        return f"Processing {', '.join(filenames)}...", False, True
    return "Please upload a log file.", True, processed_once


@app.callback(
    Output('process-log-button', 'disabled'),
    [Input('upload-log', 'filename'),
     Input('processed-once', 'data')]
)
def toggle_process_button(filenames, processed_once):
    # If we have already processed once, always disable
    if processed_once:
        return True

    # If no filenames chosen, disable
    if not filenames:
        return True

    # If filenames chosen and not processed once, enable
    return False


@app.callback(
    Output('add-files-modal', 'is_open'),
    [
        Input('add-more-files-button', 'n_clicks'),
        Input('close-add-files-modal', 'n_clicks'),
        Input('confirm-add-files', 'n_clicks')
    ],
    [
        State('additional-upload', 'filename'),
        State('additional-upload', 'contents'),
        State('add-files-modal', 'is_open')
    ]
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
    return html.Button('Upload Log File', className="btn btn-primary")


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
