from dash import dcc, html
import dash_bootstrap_components as dbc
from app import app

PARTNERS = [
    ("gloria.png", "https://ielab.info/resources/gloria/about", "GLORIA"),
    ("rec.png", "https://www.refficiency.org/", "REfficiency"),
    ("ccg.png", "https://climatecompatiblegrowth.com/", "CCG"),
]

DOC_TEXT = dcc.Markdown(
    """
## What this app contains

This website provides interactive Sankey diagrams to explore global metal ore value chains.

Main views:

- **Footprint Explorer**: extraction-to-consumption pathways (without ownership layer)
- **Ownership Explorer**: same pathways plus mine-owner nationality at the left-most stage

Data coverage in the publication setup includes many countries and years (2000-2022), with regional aggregation where needed.

## Data and method

The Sankey diagrams combine:

- GLORIA MRIO data for production and consumption accounting
- Mine ownership information from S&P Global sources used in the associated research workflow

Interpretation logic follows the associated paper in *Communications Earth & Environment*.

## Downloads and code

- Sankey methodology/code repository: https://github.com/baptiste-an/Mapping-metal-flows-sankeys
- Web app code base: https://github.com/baptiste-an/Application-mapping-GHG
- Figure downloads (SVG): FigShare folder associated with the publication

## Suggested citation

Andrieu, B., Cervantes Barron, K., Heydari, M. et al. Country's wealth is not associated with domestic control of metal ore extraction. *Commun Earth Environ* 6, 379 (2025). https://doi.org/10.1038/s43247-025-02321-1

Lenzen, M., A. Geschke, M.D. Abd Rahman, Y. Xiao, J. Fry, R. Reyes, E. Dietzenbacher, S. Inomata, K. Kanemoto, B. Los, D. Moran, H. Schulte in den Baeumen, A. Tukker, T. Walmsley, T. Wiedmann, R. Wood and N. Yamano (2017) The Global MRIO Lab - charting the world economy. *Economic Systems Research* 29, 158-186. https://doi.org/10.1080/09535314.2017.1301887

Lenzen, M., A. Geschke, J. West, J. Fry, A. Malik, S. Giljum, L.M.i. Canals, P. Pinero, S. Lutter, T. Wiedmann, M. Li, M. Sevenster, J. Potocnik, I. Teixeira, M.V. Voore, K. Nansai and H. Schandl (2021) Implementing the Material Footprint to measure progress towards SDGs 8 and 12. *Nature Sustainability*. https://www.nature.com/articles/s41893-021-00811-6

## Funding note

This publication was produced under the Climate Compatible Growth (CCG) programme, funded by UK aid from the UK government. The views expressed do not necessarily reflect UK government policy.
"""
)

layout = dbc.Container(
    [
        html.Section(
            [
                html.H2("Documentation and Downloads", className="page-head-title"),
                html.P(
                    "Methods, references, and access links for the Sankey application.",
                    className="page-head-subtitle",
                ),
            ],
            className="page-head reveal",
        ),
        dbc.Row(
            [
                dbc.Col(
                    html.A(
                        html.Div(
                            html.Img(
                                src=app.get_asset_url(img_name),
                                alt=alt_text,
                                className="partner-logo",
                            ),
                            className="partner-card",
                        ),
                        href=url,
                        target="_blank",
                        className="partner-link",
                    ),
                    xs=12,
                    md=4,
                )
                for img_name, url, alt_text in PARTNERS
            ],
            class_name="g-3 partner-grid reveal",
        ),
        html.Div(DOC_TEXT, className="app-card info-card docs-card reveal"),
    ],
    fluid=True,
    className="page-frame page-docs",
)
