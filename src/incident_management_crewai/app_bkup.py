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

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
server = app.server

orchestrator = LogOrchestrator()

# Global state
log_counts = {"CRITICAL": 0, "ERROR": 0, "WARNING": 0, "INFO": 0}
processing = False
task_lock = Lock()

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


app.layout = dbc.Container(fluid=False, className="p-4", children=[

    # Stylish heading
    dbc.Card(
        dbc.CardBody(
            html.H2("Incident Management Dashboard",
                    className="text-white text-center mb-0")
        ),
        className="mb-4 bg-dark border-info"
    ),

    # Severity Chart
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

    # Task Outputs Header
    html.H4("Task Outputs", className="text-white mb-3"),

    # Task Outputs container
    html.Div(id='task-output-cards', className="mb-4"),

    # Upload and Process Buttons in one row
    dbc.Card(
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dcc.Upload(
                        id='upload-log',
                        children=html.Button(
                            'Upload Log File', className="btn btn-primary"),
                        multiple=False
                    ),
                    html.Div(id='selected-file-name',
                             className="mt-2 text-white")
                ], width=4),

                dbc.Col([
                    dbc.Button("Process Log", id="process-log-button",
                               color="primary")
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

    # Modal for adding more files
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
    Input('interval-component', 'n_intervals')
)
def update_bar_chart(n):
    df = pd.DataFrame(list(log_counts.items()), columns=["Severity", "Count"])
    fig = {
        'data': [{'x': df['Severity'], 'y': df['Count'], 'type': 'bar', 'marker': {'color': '#17a2b8'}}],
        'layout': {
            'plot_bgcolor': '#222222',
            'paper_bgcolor': '#222222',
            'font': {'color': 'white'},
            'xaxis': {'title': 'Severity'},
            'yaxis': {'title': 'Count'}
        }
    }
    return fig


@app.callback(
    Output('task-output-cards', 'children'),
    Input('interval-component', 'n_intervals')
)
def update_task_outputs(n):
    task_data = parse_log_file()
    cards = []

    for task in tasks:
        output = task_data.get(task)
        formatted_output = "⏳ In Progress..."

        if output:
            try:
                json_output = output.split('output=')[-1].strip()
                json_output = json_output.replace('\n', '').replace('\r', '')
                formatted_output = json.dumps(
                    json.loads(json_output), indent=2)
            except (json.JSONDecodeError, ValueError):
                formatted_output = output

        card = dbc.Card([
            dbc.CardBody([
                html.H4(task.replace('_', ' ').title(),
                        className='card-title mb-3',
                        style={'fontSize': '20px', 'color': '#17a2b8', 'fontWeight': 'bold'}),
                html.Pre(formatted_output, className='card-text text-white',
                         style={
                             'whiteSpace': 'pre-wrap',
                             'wordBreak': 'break-all',
                             'maxHeight': '200px',
                             'overflowY': 'auto'
                         }),
                dbc.Alert("✅ Completed" if output else "⏳ Processing...",
                          color="success" if output else "warning", className="mt-3")
            ])
        ], className='mb-3 bg-dark border-info')
        cards.append(card)

    card1 = cards[0] if len(cards) > 0 else html.Div()
    card2 = cards[1] if len(cards) > 1 else html.Div()
    card3 = cards[2] if len(cards) > 2 else html.Div()
    card4 = cards[3] if len(cards) > 3 else html.Div()
    card5 = cards[4] if len(cards) > 4 else html.Div()

    layout = html.Div([
        dbc.Row([
            dbc.Col(card1, width=6),
            dbc.Col(card2, width=6),
        ], className="mb-3"),
        dbc.Row([
            dbc.Col(card3, width=6),
            dbc.Col(card4, width=6),
        ], className="mb-3"),
        dbc.Row([
            dbc.Col(card5, width=6),
            dbc.Col(html.Div(), width=6)
        ])
    ])
    return layout


@app.callback(
    Output('selected-file-name', 'children'),
    Input('upload-log', 'filename')
)
def show_selected_file(filename):
    if filename:
        return f"Selected File: {filename}"
    return ""


@app.callback(
    [Output('upload-status', 'children'),
     Output('add-more-files-button', 'disabled')],
    Input('process-log-button', 'n_clicks'),
    State('upload-log', 'filename'),
    State('upload-log', 'contents')
)
def process_log(n_clicks, filename, contents):
    if n_clicks and filename:
        log_path = os.path.join(DATA_FOLDER_PATH, filename)

        # Save the uploaded file
        with open(log_path, "wb") as f:
            f.write(contents.encode('utf-8'))

        # Clear the log file before starting the process
        clear_log_file()

        # Run the orchestrator in a background thread
        def run_orchestrator():
            try:
                orchestrator.run()
                logging.info("Orchestrator run completed successfully.")
            except Exception as e:
                logging.error(f"Error during orchestrator run: {e}")

        threading.Thread(target=run_orchestrator).start()
        return f"{filename}", False

    return "Please upload a log file.", True


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
    # Determine which button triggered the callback
    triggered_id = ctx.triggered_id if hasattr(ctx, 'triggered_id') else None

    # If user clicked "Add More Files" button
    if triggered_id == 'add-more-files-button':
        # Toggle modal: if closed, open it; if open, close it
        return not is_open

    # If user clicked "Close" in the modal
    if triggered_id == 'close-add-files-modal':
        return False  # Always close the modal

    # If user clicked "Confirm"
    if triggered_id == 'confirm-add-files':
        if filenames and contents:
            # Handle single file scenario
            if isinstance(filenames, str):
                filenames = [filenames]
                contents = [contents]

            # Save each file
            for name, file_content in zip(filenames, contents):
                content_string = file_content.split('base64,')[-1]
                decoded = base64.b64decode(content_string)
                file_path = os.path.join(DATA_FOLDER_PATH, name)
                with open(file_path, 'wb') as f:
                    f.write(decoded)

        # After confirming, close the modal
        return False

    # If no action matches, just return current state
    return is_open


@app.callback(
    Output('additional-files-names', 'children'),
    Input('additional-upload', 'filename')
)
def show_additional_files(filenames):
    if filenames is None:
        return ""
    if isinstance(filenames, str):
        # single file
        return f"Selected File: {filenames}"
    else:
        # multiple files
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
    # Return the Upload Log File button again if needed
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
