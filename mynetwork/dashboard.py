import dash  
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import os

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CYBORG])

app.layout = dbc.Container([
    # HEADER & MASTER STATUS
    html.H1("CREDIT DIRECT | HYBRID NOC COMMAND", className="text-center my-4", style={'color': '#00FF00'}),
    html.Div(id='master-status-led', className="text-center p-2 mb-4", style={'borderRadius': '5px'}),

    # TOP ROW: CLOUD STATS & ALERTS
    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardHeader("AWS CLOUD (ALB) TARGETS"),
            dbc.CardBody([html.H3(id='cloud-stats-text', className="text-center")])
        ], color="dark", outline=True), width=4),
        dbc.Col(html.Div(id='alerts-area'), width=8),
    ]),

    # MIDDLE ROW: PERFORMANCE GRAPHS
    dbc.Row([
        dbc.Col(dcc.Graph(id='latency-line'), width=6),
        dbc.Col(dcc.Graph(id='jitter-bar'), width=6),
    ], className="mt-4"),

    # BOTTOM ROW: RADIO QUALITY
    dbc.Row([
        dbc.Col(dcc.Graph(id='signal-scatter'), width=12),
    ], className="mt-4"),

    dcc.Interval(id='refresh-interval', interval=5000, n_intervals=0)
], fluid=True)

@app.callback(
    [Output('latency-line', 'figure'), Output('jitter-bar', 'figure'), 
     Output('signal-scatter', 'figure'), Output('cloud-stats-text', 'children'), 
     Output('alerts-area', 'children'), Output('master-status-led', 'children'),
     Output('master-status-led', 'style')],
    [Input('refresh-interval', 'n_intervals')]
)
def update_dashboard(n):
    if not os.path.exists('network_stats.csv'):
        return [px.scatter()]*3, "N/A", [], "INITIALIZING...", {'backgroundColor': 'gray'}

    df = pd.read_csv('network_stats.csv').tail(40)
    latest = df.iloc[-1]

    # 1. LATENCY & JITTER
    fig_lat = px.line(df, x='Time', y='Latency', color='Branch', title="Branch Latency (ms)", template="plotly_dark")
    fig_jit = px.bar(df, x='Time', y='Jitter', color='Branch', title="Jitter (Stability)", template="plotly_dark")
    
    # 2. RADIO QUALITY (RSRP vs SINR)
    fig_sig = px.scatter(df, x='RSRP', y='SINR', color='Branch', size='Latency', 
                         title="Signal Health (Excellent: RSRP > -80, SINR > 15)", template="plotly_dark")

    # 3. CLOUD STATUS
    cloud_info = f"Healthy: {latest['Cloud_H']} | Unhealthy: {latest['Cloud_U']}"
    
    # 4. ALERTS & MASTER STATUS
    alerts = []
    is_critical = False

    if latest['Status'] == "DOWN":
        alerts.append(dbc.Alert(f"CRITICAL: {latest['Branch']} is OFFLINE!", color="danger"))
        is_critical = True
    if latest['Cloud_U'] > 0:
        alerts.append(dbc.Alert("AWS ALERT: Cloud instance health check failed!", color="warning"))
    if latest['SINR'] < 5:
        alerts.append(dbc.Alert("SIGNAL NOISE: Check for interference in Benin branch.", color="info"))

    # MASTER LED LOGIC
    if is_critical: 
        led_text = "SYSTEM STATUS: CRITICAL ERROR"
        led_style = {'backgroundColor': '#660000', 'color': '#FF0000', 'fontWeight': 'bold'}
    else:
        led_text = "SYSTEM STATUS: ALL SYSTEMS OPERATIONAL"
        led_style = {'backgroundColor': '#004400', 'color': '#00FF00', 'fontWeight': 'bold'}

    return fig_lat, fig_jit, fig_sig, cloud_info, alerts, led_text, led_style

if __name__ == "__main__":
    app.run(debug=True, port=8050)    