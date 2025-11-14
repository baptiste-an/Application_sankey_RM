from dash import html, dcc
import dash_bootstrap_components as dbc
import pathlib
from app import app


DATA_PATH = pathlib.Path(__file__).parent.joinpath("data").resolve()


text = dcc.Markdown(
    """
    ##### Documentation

    The goal of this project is to build sankey diagrams to map the value chains of metals. We build over 100,000 Sankey diagrams to visualize metal flows across 159 countries and 4 world regions, covering three key steps: mine owner nationality, extraction region, and final consumption region.
    The first tab shows the sankeys with the production-based account and the consumption-based account. The second tab adds a mine ownership layer before the production-based account.
    These diagrams are based on the GLORIA MRIO, available at https://ielab.info/, as well as on S&P Global data for mine ownership.

    ##### Code and figures downloads

    The **code** used to calculate used to build the **sankeys** is available on github: https://github.com/baptiste-an/Mapping-metal-flows-sankeys.

    The **code** to build the **application** is based on: https://github.com/baptiste-an/Application-mapping-GHG.

    The **sankey diagrams in svg format** can be downloaded from the FigShare folder associated with this publication.
    
    ##### Funding

    This paper associated with this publication has been produced under the Climate Compatible Growth (CCG) programme, which is funded by UK aid from the UK government. However, the views expressed herein do not necessarily reflect the UK government's official policies.
    
    ##### Citation

    Andrieu, B., Cervantes Barron, K., Heydari, M. et al. Country’s wealth is not associated with domestic control of metal ore extraction. Commun Earth Environ 6, 379 (2025). https://doi.org/10.1038/s43247-025-02321-1
    
    Lenzen, M., A. Geschke, M.D. Abd Rahman, Y. Xiao, J. Fry, R. Reyes, E. Dietzenbacher, S. Inomata, K. Kanemoto, B. Los, D. Moran, H. Schulte in den Bäumen, A. Tukker, T. Walmsley, T. Wiedmann, R. Wood and N. Yamano (2017) The Global MRIO Lab -charting the world economy. Economic Systems Research 29, 158-186. https://doi.org/10.1080/09535314.2017.1301887

    Lenzen, M., A. Geschke, J. West, J. Fry, A. Malik, S. Giljum, L.M.i. Canals, P. Piñero, S. Lutter, T. Wiedmann, M. Li, M. Sevenster, J. Potočnik, I. Teixeira, M.V. Voore, K. Nansai and H. Schandl (2021) Implementing the Material Footprint to measure progress towards SDGs 8 and 12. Nature Sustainability. https://www.nature.com/articles/s41893-021-00811-6

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
                                src=app.get_asset_url("gloria.png"),
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
