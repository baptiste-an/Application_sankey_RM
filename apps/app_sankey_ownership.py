"""
 # @ Create Time: 2022-08-23 15:40:55.513725
"""

import pandas as pd
import plotly.graph_objs as go
from dash import Dash, html, dcc, Output, Input, State, callback, MATCH, callback_context, no_update
from dash_auth import BasicAuth
from dash.exceptions import PreventUpdate
import uuid
import dash_bootstrap_components as dbc
import pyarrow.feather as feather
import pathlib
import json
from flask_caching import Cache
from app import app
from slider import PlaybackSliderAIO
from collections import Counter
import pickle
import lzma
import numpy as np


# VALID_USERNAME_PASSWORD_PAIRS = [["hello", "world"]]
# app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME])
# # server = app.server

# auth = BasicAuth(app, VALID_USERNAME_PASSWORD_PAIRS)


cache = Cache(
    app.server, config={"CACHE_TYPE": "FileSystemCache", "CACHE_DIR": "cache"}
)

DATA_PATH = pathlib.Path(__file__).parent.joinpath("data").resolve()

REGIONS = {}

with open(f"{DATA_PATH}/dictreg.json") as f:
    REGIONS = json.loads(f.read())
# REGIONS = {"FRA": "France", "CHN": "China", "GBR": "United Kingdom"}
REGIONS.pop("DYE")
REGIONS.pop("SDS")
REGIONS["World"] = "World"
LABELS = [{"label": v, "value": k} for k, v in REGIONS.items()]

dropdown = dcc.Dropdown(
    id="slct2",
    options=LABELS,
    multi=False,
    value="World",
    clearable=False,
    persistence=True,
    persistence_type="session",
    className="dash-dropdown",
)
COMMODITY_OPTIONS = [
    "Copper ores",
    "Iron ores",
    "Nickel ores",
    "Lead ores",
    "Zinc ores",
    "Tin ores",
    "Manganese ores",
    "Uranium ores",
    "Gold ores",
    "Silver ores",
    "Aluminium ores",
]
dropdown_subtype = dcc.Dropdown(
    id="slct_subtype",
    options=COMMODITY_OPTIONS,
    multi=False,
    value="Copper ores",
    clearable=False,
    persistence=True,
    persistence_type="session",
    className="dash-dropdown",
)
dropdown_unit = dcc.Dropdown(
    id="slct_unit",
    options=[
        "kTonnes",
        "Tonnes per capita",
    ],
    multi=False,
    value="kTonnes",
    clearable=False,
    persistence=True,
    persistence_type="session",
    className="dash-dropdown",
)

graph = dcc.Graph(
    id="graph2",
    responsive=True,
    className="themed-graph",
    style={"height": "620px", "width": "100%"},
)
slider = PlaybackSliderAIO(
    aio_id="bruh2",
    slider_props={
        "min": 2000,
        "max": 2022,
        "step": 1,
        "value": 2022,
        "marks": {str(year): str(year) for year in range(2000, 2023, 1)},
        "persistence": True,
        "persistence_type": "session",
    },
    button_props={"className": "float-left"},
    interval_props={"interval": 2500},
)
link = html.A(
    "https://www.nature.com/articles/s43247-025-02321-1",
    href="https://www.nature.com/articles/s43247-025-02321-1",
    target="_blank",
)
link2 = html.A(
    "https://doi.org/10.1080/09535314.2017.1301887",
    href="https://doi.org/10.1080/09535314.2017.1301887",
    target="_blank",
)
link3 = html.A(
    "https://www.nature.com/articles/s41893-021-00811-6",
    href="https://www.nature.com/articles/s41893-021-00811-6",
    target="_blank",
)

explanation = dcc.Markdown(
    """
    Any flow represented here is related to the region selected either because ores were controlled by companies whose headquarters were based in that region, or because the ores were extracted in that region, or because ores were embodied in the region's final consumption. The flows unrelated to the region selected are not shown.
    EECCA refers to Eastern Europe, Caucasus and Central Asia. RoW refers to Rest of the World. NPISHS refers to Non-Profit Institutions Serving Households. GFCF refers to Gross Fixed Capital Formation.
    """
)


wording = text = dcc.Markdown(
    """
    Suggested wording: *We used the sankey diagrams (Andrieu et al. In prep) based on release 059 of the GLORIA global environmentally-extended multi-region input-output (MRIO) database (Lenzen et al. 2021), constructed in the Global MRIO Lab (Lenzen et al. 2017).*
    """
)

citation = html.Div(
    [
        explanation,
        html.H3("Citation", className="citation-title"),
        html.P(
            [
                "Andrieu, B., Cervantes Barron, K., Heydari, M. et al. Country’s wealth is not associated with domestic control of metal ore extraction. Commun Earth Environ 6, 379 (2025).",
                link,
            ]
        ),
        html.P(
            [
                "Lenzen, M., A. Geschke, M.D. Abd Rahman, Y. Xiao, J. Fry, R. Reyes, E. Dietzenbacher, S. Inomata, K. Kanemoto, B. Los, D. Moran, H. Schulte in den Bäumen, A. Tukker, T. Walmsley, T. Wiedmann, R. Wood and N. Yamano (2017) The Global MRIO Lab -charting the world economy. Economic Systems Research 29, 158-186. ",
                link2,
            ]
        ),
        html.P(
            [
                "Lenzen, M., A. Geschke, J. West, J. Fry, A. Malik, S. Giljum, L.M.i. Canals, P. Piñero, S. Lutter, T. Wiedmann, M. Li, M. Sevenster, J. Potočnik, I. Teixeira, M.V. Voore, K. Nansai and H. Schandl (2021) Implementing the Material Footprint to measure progress towards SDGs 8 and 12. Nature Sustainability. ",
                link3,
            ]
        ),
        wording,
        # html.Img(
        #     src=app.get_asset_url("NTNU.png"),
        #     style={
        #         "height": "100px",
        #         "display": "block",
        #         "margin-left": "auto",
        #         "margin-right": "auto",
        #     },
        # ),
    ],
    className="app-card info-card reveal",
)


layout = dbc.Container(
    [
        html.Section(
            [
                html.H2("Metal Ores Ownership", className="page-head-title"),
                html.P(
                    "Trace ownership nationality, extraction locations, and final "
                    "consumption flows in one view.",
                    className="page-head-subtitle",
                ),
            ],
            className="page-head reveal",
        ),
        html.Div(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            html.Div(
                                [
                                    html.P("Commodity", className="control-label"),
                                    dropdown_subtype,
                                ],
                                className="control-field",
                            ),
                            xs=12,
                            md=4,
                        ),
                        dbc.Col(
                            html.Div(
                                [
                                    html.P("Region", className="control-label"),
                                    dropdown,
                                ],
                                className="control-field",
                            ),
                            xs=12,
                            md=4,
                        ),
                        dbc.Col(
                            html.Div(
                                [
                                    html.P("Unit", className="control-label"),
                                    dropdown_unit,
                                ],
                                className="control-field",
                            ),
                            xs=12,
                            md=4,
                        ),
                    ],
                    class_name="g-3",
                ),
            ],
            className="app-card controls-card reveal",
        ),
        html.Div([graph], className="app-card graph-card reveal"),
        html.Div([slider], className="app-card slider-card reveal"),
        html.Div(
            dcc.Markdown(
                "You may **use your browser's zoom function for better readability**. A full documentation is available in the associated paper."
            ),
            className="app-card info-card slim-card reveal",
        ),
        citation,
        # dbc.Row(
        #     [
        #         dbc.Col(
        #             [
        #                 html.A(
        #                     html.Img(
        #                         src=app.get_asset_url("exiobase.png"),
        #                         style={"height": 100, "justify": "center"},
        #                     ),
        #                     href="https://www.exiobase.eu/",
        #                     target="_blank",
        #                 )
        #             ],
        #             width=6,
        #         )
        #     ],
        #     justify="center",
        # ),
    ],
    fluid=True,
    className="page-frame page-ownership",
)
color_mapping = {
    "#0072ff": "#4C72B0",  # Deep Blue
    "#00cafe": "#55A868",  # Green
    "#b0ebff": "#C44E52",  # Red
    "#fff1b7": "#8172B3",  # Purple
    "#ffdc23": "#CCB974",  # Mustard Yellow
    "#ffb758": "#64B5CD",  # Cyan
    "#ff8200": "#8C8C8C",  # Gray
    "#0072ff": "#E377C2",  # Pink
    "#00cafe": "#F39C12",  # Orange
    "#b0ebff": "#17BECF",  # Sky Blue
}

FIGURE_FONT = "Avenir Next, Segoe UI Variable Text, Trebuchet MS, Tahoma, sans-serif"


def _apply_figure_theme(fig, legend_y=-0.06, height=620):
    fig.update_layout(
        height=height,
        font={"family": FIGURE_FONT, "size": 12, "color": "#44372b"},
        margin={"l": 20, "r": 20, "t": 56, "b": 94},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        hoverlabel={
            "bgcolor": "#fff7ee",
            "bordercolor": "#cfb59c",
            "font": {"family": FIGURE_FONT, "size": 12, "color": "#34291f"},
        },
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": legend_y,
            "xanchor": "center",
            "x": 0.5,
            "font": {"size": 11, "color": "#5f4c3b"},
            "bgcolor": "rgba(0,0,0,0)",
        },
    )
    fig.update_xaxes(showgrid=False, zeroline=False, showticklabels=False)
    fig.update_yaxes(showgrid=False, zeroline=False, showticklabels=False)
    return fig


def _empty_figure(message):
    fig = go.Figure()
    fig.update_layout(
        xaxis={"visible": False},
        yaxis={"visible": False},
        annotations=[
            {
                "text": message,
                "xref": "paper",
                "yref": "paper",
                "x": 0.5,
                "y": 0.5,
                "showarrow": False,
                "font": {"family": FIGURE_FONT, "size": 15, "color": "#5f4c3b"},
            }
        ],
        showlegend=False,
    )
    return _apply_figure_theme(fig, legend_y=-0.06, height=620)


@app.callback(
    Output("graph2", "figure"),
    Input("slct2", "value"),
    Input(PlaybackSliderAIO.ids.slider("bruh2"), "value"),
    Input("slct_unit", "value"),
    Input("slct_subtype", "value"),
)
@cache.memoize()
def fig_sankey(
    region,
    year,
    unit="kTonnes",
    sankey_subtype="Copper ores",
):
    """Builds sankey diagram.

    Parameters
    ----------
    region : string
    year : int

    Returns
    -------
    fig : figure
    """

    if region not in REGIONS:
        region = "World"
    if unit not in ["kTonnes", "Tonnes per capita"]:
        unit = "kTonnes"
    if not sankey_subtype:
        sankey_subtype = "Copper ores"

    sankey_type = "Commodity all ownership"
    preprocessed_data_path = (
        "Results/Sankey_preprocessed/"
        + sankey_type
        + "/"
        + sankey_subtype
        + "/"
        + region
        + "_"
        + str(year)
        + ".pkl.lzma"
    )
    preprocessed_data_path = DATA_PATH.joinpath(preprocessed_data_path)
    try:
        with lzma.open(preprocessed_data_path, "rb") as f:
            preprocessed_data = pickle.load(f)
    except FileNotFoundError:
        return _empty_figure("No preprocessed Sankey file found for this selection.")

    # Extract Sankey, layout, and arrows/labels
    if unit == "kTonnes":
        sankey = preprocessed_data["sankey"]
    elif unit == "Tonnes per capita":
        sankey = preprocessed_data["sankey_cap"]
    layout = preprocessed_data["layout"]
    arrows_and_labels = preprocessed_data["arrows_and_labels"]

    updated_colors = [
        color_mapping.get(color, color) for color in sankey["link"]["color"]
    ]
    sankey["link"]["color"] = np.array(updated_colors)

    # Create the figure
    fig = go.Figure(sankey)
    fig.update_layout(**layout)

    # Add preprocessed shapes and annotations
    fig.update_layout(shapes=arrows_and_labels["shapes"])
    fig.update_layout(annotations=arrows_and_labels["annotations"])

    # Define legends based on the Sankey type
    if sankey_type in ["Commodity", "Commodity all ownership", "All commodities"]:
        legend_data = {
            "Commodity": {
                "colors": [
                    "white",
                    "#4C72B0",
                    "#55A868",
                    "#C44E52",
                    "#8172B3",
                    "#CCB974",
                    "#64B5CD",
                    "#8C8C8C",
                    "#E377C2",
                ],
                "names": [
                    "<b>Region of ores extraction:</b>",
                    REGIONS[region],
                    "Africa",
                    "Asia-Pacific",
                    "EECCA",
                    "Europe",
                    "Latin America",
                    "Middle East",
                    "North America",
                ],
            },
            "Commodity all ownership": {
                "colors": [
                    "white",
                    "#4C72B0",
                    "#55A868",
                    "#C44E52",
                    "#8172B3",
                    "#CCB974",
                    "#64B5CD",
                    "#8C8C8C",
                    "#E377C2",
                    "#F39C12",
                ],
                "names": [
                    "<b>Nationality of mine owners:</b>",
                    REGIONS[region],
                    "Africa",
                    "Asia-Pacific",
                    "EECCA",
                    "Europe",
                    "Latin America",
                    "Middle East",
                    "North America",
                    "Unknown",
                ],
            },
            "All commodities": {
                "colors": [
                    "white",
                    "#4C72B0",
                    "#55A868",
                    "#C44E52",
                    "#8172B3",
                    "#CCB974",
                    "#64B5CD",
                    "#8C8C8C",
                    "#E377C2",
                ],
                "names": [
                    "<b>Metal ores:</b>",
                    "Aluminium ores",
                    "Chromium ores",
                    "Copper ores",
                    "Gold ores",
                    "Iron ores",
                    "Lead ores",
                    "Manganese ores",
                    "Nickel ores",
                ],
                "colors2": [
                    "white",
                    "#F39C12",
                    "#17BECF",
                    "#9E9E9E",
                    "#F1A340",
                    "#D84A6B",
                    "#5E4FA2",
                    "#2C7BB6",
                ],
                "names2": [
                    " ",
                    "Other metal ores",
                    "Platinum ores",
                    "Silver ores",
                    "Tin ores",
                    "Titanium ores",
                    "Uranium ores",
                    "Zinc ores",
                ],
            },
        }

        # Generate Scatter traces for the legend
        def create_legend(colors, names):
            return [
                go.Scatter(
                    x=[None],
                    y=[None],
                    mode="markers",
                    marker=dict(size=10, color=clr),
                    showlegend=True,
                    name=nm,
                )
                for clr, nm in zip(colors, names)
            ]

        legend_info = legend_data[sankey_type]
        legend_traces = create_legend(legend_info["colors"], legend_info["names"])
        fig.add_traces(legend_traces)

        yleg = -0.06
        if sankey_type == "All commodities":
            legend_traces2 = create_legend(
                legend_info["colors2"], legend_info["names2"]
            )
            fig.add_traces(legend_traces2)
            yleg = -0.11

        fig.update_layout(showlegend=True)
        _apply_figure_theme(fig, legend_y=yleg, height=620)
    else:
        _apply_figure_theme(fig, legend_y=-0.06, height=620)

    return fig


try:
    graph.figure = fig_sankey(
        region=dropdown.value,
        year=2022,
        unit=dropdown_unit.value,
        sankey_subtype=dropdown_subtype.value,
    )
except Exception:
    graph.figure = _empty_figure("No preprocessed Sankey file found for this selection.")


def _coerce_year(year):
    try:
        year = int(year)
    except (TypeError, ValueError):
        return 2022
    return min(max(year, 2000), 2022)


def _coerce_region(region):
    return region if region in REGIONS else "World"


def _coerce_unit(unit):
    return unit if unit in ["kTonnes", "Tonnes per capita"] else "kTonnes"


def _coerce_commodity(commodity):
    if commodity in COMMODITY_OPTIONS:
        return commodity
    return "Copper ores"


@app.callback(
    Output("slct2", "value"),
    Output(PlaybackSliderAIO.ids.slider("bruh2"), "value"),
    Output("slct_unit", "value"),
    Output("slct_subtype", "value"),
    Input("tabs", "active_tab"),
    State("shared-region-store", "data"),
    State("shared-year-store", "data"),
    State("shared-unit-store", "data"),
    State("shared-commodity-store", "data"),
    prevent_initial_call=True,
)
def apply_shared_selection(active_tab, region, year, unit, commodity):
    if active_tab not in {"tab-4", "tab-2"}:
        raise PreventUpdate

    return (
        _coerce_region(region),
        _coerce_year(year),
        _coerce_unit(unit),
        _coerce_commodity(commodity),
    )


@app.callback(
    Output("shared-region-store", "data", allow_duplicate=True),
    Output("shared-year-store", "data", allow_duplicate=True),
    Output("shared-unit-store", "data", allow_duplicate=True),
    Output("shared-commodity-store", "data", allow_duplicate=True),
    Input("slct2", "value"),
    Input(PlaybackSliderAIO.ids.slider("bruh2"), "value"),
    Input("slct_unit", "value"),
    Input("slct_subtype", "value"),
    prevent_initial_call=True,
)
def persist_shared_selection(region, year, unit, commodity):
    triggered = callback_context.triggered_id

    region_out = no_update
    year_out = no_update
    unit_out = no_update
    commodity_out = no_update

    if triggered == "slct2":
        region_out = _coerce_region(region)
    elif isinstance(triggered, dict) and triggered.get("subcomponent") == "slider":
        year_out = _coerce_year(year)
    elif triggered == "slct_unit":
        unit_out = _coerce_unit(unit)
    elif triggered == "slct_subtype":
        commodity_out = _coerce_commodity(commodity)

    return region_out, year_out, unit_out, commodity_out
