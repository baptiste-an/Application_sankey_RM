from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import os
import dash_bootstrap_components as dbc

# Connect to main app.py file
from app import app
from app import server

# Connect to your app pages
from apps import (
    doc,
    landing,
    app_sankey_commodity,
    app_sankey_ownership_explorer,
)

# VALID_USERNAME_PASSWORD_PAIRS = [["hello", "world"]]
# auth = BasicAuth(app, VALID_USERNAME_PASSWORD_PAIRS)


app.layout = html.Div(
    [
        dcc.Store(id="shared-region-store", data="World"),
        dcc.Store(id="shared-year-store", data=2022),
        dcc.Store(id="shared-unit-store", data="kTonnes"),
        dcc.Store(id="shared-commodity-store", data="Copper ores"),
        html.Div(
            [
                html.Header(
                    [
                        html.Div(
                            [
                                html.P("Global Material Flow Explorer", className="app-overline"),
                                html.H1("Global Metal Ore Flow Sankey Diagrams", className="app-title"),
                                html.P(
                                    "Interactive visualisation of extraction, consumption, and ownership pathways "
                                    "for metal ores across regions and years.",
                                    className="app-subtitle",
                                ),
                            ],
                            className="app-masthead-inner",
                        )
                    ],
                    className="app-masthead reveal",
                ),
                html.Div(
                    [
                        dbc.Tabs(
                            [
                                dbc.Tab(
                                    label="Start here",
                                    tab_id="tab-landing",
                                ),
                                dbc.Tab(
                                    label="Footprint explorer",
                                    tab_id="tab-3",
                                ),
                                dbc.Tab(
                                    label="Ownership explorer",
                                    tab_id="tab-1",
                                ),
                                dbc.Tab(
                                    label="Documentation and downloads",
                                    tab_id="tab-5",
                                ),
                            ],
                            id="tabs",
                            active_tab="tab-landing",
                            class_name="app-tabs-nav",
                        )
                    ],
                    className="app-tabs-shell reveal",
                ),
                html.Main(id="content", className="app-content reveal"),
            ],
            className="app-shell",
        ),
    ],
    className="app-page",
)


@app.callback(Output("content", "children"), [Input("tabs", "active_tab")])
def switch_tab(active_tab):
    if active_tab == "tab-landing":
        return landing.layout
    if active_tab == "tab-1":
        return app_sankey_ownership_explorer.layout
    if active_tab == "tab-3":
        return app_sankey_commodity.layout
    if active_tab == "tab-5":
        return doc.layout
    return html.Div()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))
    app.run(debug=False, host="0.0.0.0", port=port)


# if __name__ == "__main__":
#     app.run(host="127.0.0.1", port=8050)
