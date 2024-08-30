"""
 # @ Create Time: 2022-08-23 15:40:55.513725
"""

import pandas as pd
import plotly.graph_objs as go
from dash import Dash, html, dcc, Output, Input, State, callback, MATCH
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

LABELS = [{"label": v, "value": k} for k, v in REGIONS.items()]

dropdown = dcc.Dropdown(
    id="slct2",
    options=LABELS,
    multi=False,
    value="FRA",
)
dropdown_subtype = dcc.Dropdown(
    id="slct_subtype",
    options=[
        "Copper ores",
        "Nickel ores",
        "Lead ores",
        "Zinc ores",
        "Tin ores",
        "Manganese ores",
        "Uranium ores",
        "Gold ores",
        "Silver ores",
    ],
    multi=False,
    value="Copper ores",
)
dropdown_unit = dcc.Dropdown(
    id="slct_unit",
    options=[
        "Tonnes",
        #  "Tonnes per capita",
    ],
    multi=False,
    value="Tonnes",
)
graph = dcc.Graph(id="graph2", responsive=True, style={"height": "550px"})
slider = PlaybackSliderAIO(
    aio_id="bruh2",
    slider_props={
        "min": 2000,
        "max": 2022,  # 2019
        "step": 1,
        "value": 2008,
        "marks": {str(year): str(year) for year in range(2000, 2023, 1)},
    },
    button_props={"className": "float-left"},
    interval_props={"interval": 2500},
)
link = html.A(
    "https://www.refficiency.org/",
    href="https://www.refficiency.org/",
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

wording = text = dcc.Markdown(
    """
    Suggested wording: *We used the sankey diagrams (Andrieu et al. In prep) based on release 059 of the GLORIA global environmentally-extended multi-region input-output (MRIO) database (Lenzen et al. 2021), constructed in the Global MRIO Lab (Lenzen et al. 2017).*
    """
)

citation = html.Div(
    [
        html.P(html.Strong("Citation:"), className="mb-0"),
        html.P(
            [
                "Andrieu, B., Cervantes Barron, K., Heydari, M., Cullen, J., In prep. ",
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
    className="border",
)


layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col([dropdown_subtype], width=2),
                dbc.Col(html.Div("Select commodity"), width=2),
                dbc.Col([dropdown], width=2),
                dbc.Col(html.Div("Select region"), width=2),
                dbc.Col([dropdown_unit], width=2),
                dbc.Col(html.Div("Select unit"), width=2),
            ],
            justify="center",
            align="center",
        ),
        dbc.Row(
            [
                dbc.Col(
                    [graph],
                    width=12,
                    style={"height": 550},
                )
            ]
        ),
        dbc.Row([dbc.Col([slider])], justify="center"),
        html.Div(
            dcc.Markdown(
                "You may **use your browser's zoom function for better readability**. A full documentation is available in the associated paper."
            ),
            style={"fontSize": 13},
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


@app.callback(
    Output("graph2", "figure"),
    Input("slct2", "value"),
    Input(PlaybackSliderAIO.ids.slider("bruh2"), "value"),
    Input("slct_subtype", "value"),
)
@cache.memoize()
def fig_sankey(
    region,
    year,
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

    sankey_type = "Commodity ownership"
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
    with lzma.open(preprocessed_data_path, "rb") as f:
        preprocessed_data = pickle.load(f)

    # Extract Sankey, layout, and arrows/labels
    sankey = preprocessed_data["sankey"]
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

    return fig
