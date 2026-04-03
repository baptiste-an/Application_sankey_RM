from dash import dcc
from dash import html
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
                                    className="app-masthead-copy",
                                ),
                                html.A(
                                    html.Img(
                                        src=app.get_asset_url("ccml-logo.svg"),
                                        className="app-masthead-logo",
                                        alt="CCML logo",
                                    ),
                                    href="https://www.ccml.org.uk/",
                                    target="_blank",
                                    rel="noopener noreferrer",
                                    className="app-masthead-logo-link",
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
                                    children=landing.layout,
                                ),
                                dbc.Tab(
                                    label="Footprint explorer",
                                    tab_id="tab-3",
                                    children=app_sankey_commodity.layout,
                                ),
                                dbc.Tab(
                                    label="Ownership explorer",
                                    tab_id="tab-1",
                                    children=app_sankey_ownership_explorer.layout,
                                ),
                                dbc.Tab(
                                    label="Documentation and downloads",
                                    tab_id="tab-5",
                                    children=doc.layout,
                                ),
                            ],
                            id="tabs",
                            active_tab="tab-landing",
                            class_name="app-tabs-nav",
                        )
                    ],
                    className="app-tabs-shell reveal",
                ),
            ],
            className="app-shell",
        ),
    ],
    className="app-page",
)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))
    app.run(debug=False, host="0.0.0.0", port=port)


# if __name__ == "__main__":
#     app.run(host="127.0.0.1", port=8050)
