from dash import dcc
from dash import html
from dash.dependencies import Input, Output
from dash_auth import BasicAuth
import os
import dash_bootstrap_components as dbc

# Connect to main app.py file
from app import app
from app import server

# Connect to your app pages
from apps import (
    doc,
    app_sankey_commodity,
    app_sankey_ownership,
)

# VALID_USERNAME_PASSWORD_PAIRS = [["hello", "world"]]
# auth = BasicAuth(app, VALID_USERNAME_PASSWORD_PAIRS)


app.layout = html.Div(
    [
        dbc.Tabs(
            [
                dbc.Tab(
                    label="Metal ores footprint",
                    tab_id="tab-1",
                    active_label_style={"color": "#FF8200"},
                    # label_style={"color": "#00005A"},
                ),
                dbc.Tab(
                    label="Metal ores ownership",
                    tab_id="tab-2",
                    active_label_style={"color": "#FF8200"},
                    # label_style={"color": "#00005A"},
                ),
                dbc.Tab(
                    label="Documentation and downloads",
                    tab_id="tab-3",
                    active_label_style={"color": "#FF8200"},
                    # label_style={"color": "#00005A"},
                ),
            ],
            id="tabs",
            active_tab="tab-1",
        ),
        html.Div(id="content"),
    ]
)


@app.callback(Output("content", "children"), [Input("tabs", "active_tab")])
def switch_tab(at):
    if at == "tab-1":
        return app_sankey_commodity.layout  # app_sankey_commodity
    elif at == "tab-2":
        return app_sankey_ownership.layout  # app_sankey_ownership
    elif at == "tab-3":
        return doc.layout


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))
    app.run_server(debug=False, host="0.0.0.0", port=port)


# if __name__ == "__main__":
#     app.run_server(host="127.0.0.1", port=8050)
