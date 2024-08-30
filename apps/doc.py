from dash import html, dcc
import dash_bootstrap_components as dbc
import pathlib
from app import app


DATA_PATH = pathlib.Path(__file__).parent.joinpath("data").resolve()


text = dcc.Markdown(
    """
    ##### Documentation

    [...]

    ##### Code and figures downloads

    [...]
    
    ##### Funding

    [...]
    
    ##### Citation

    [...]

"""
)

# *This text will be italic*
# _This will also be italic_
# **This text will be bold**
# __This will also be bold__
# _You **can** combine them_


layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.A(
                            html.Img(
                                src=app.get_asset_url("iel.png"),
                                style={"height": 100, "justify": "center"},
                            ),
                            href="https://ielab.info/resources/gloria/about",
                            target="_blank",
                        )
                    ],
                    width=3,
                ),
                dbc.Col(
                    [
                        html.A(
                            html.Img(
                                src=app.get_asset_url("rec.png"),
                                style={"height": 100, "justify": "center"},
                            ),
                            href="https://www.refficiency.org/",
                            target="_blank",
                        )
                    ],
                    width=3,
                ),
                dbc.Col(
                    [
                        html.A(
                            html.Img(
                                src=app.get_asset_url("ccg.png"),
                                style={"height": 100, "justify": "center"},
                            ),
                            href="https://climatecompatiblegrowth.com/",
                            target="_blank",
                        )
                    ],
                    width=3,
                ),
                # dbc.Col(
                #     [
                #         html.A(
                #             html.Img(src=app.get_asset_url("uga2.jpg"), style={"height": 100, "justify": "center"}),
                #             href="https://www.univ-grenoble-alpes.fr/english/",
                #             target="_blank",
                #         )
                #     ],
                #     width=2,
                # ),
            ],
            justify="center",
        ),
        html.Div(text, className="border", style={"fontSize": 13}),
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
        # dbc.Row([dbc.Col([thanks], width=12)])
        # html.Div(thanks, id="page-content"),
    ],
    fluid=True,
)
