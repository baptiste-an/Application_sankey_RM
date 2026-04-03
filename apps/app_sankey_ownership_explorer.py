import json
import lzma
import pathlib
import pickle

import dash_bootstrap_components as dbc
import numpy as np
import plotly.graph_objs as go
from dash import Input, Output, State, callback_context, dcc, html, no_update
from dash.exceptions import PreventUpdate

from app import app

DATA_PATH = pathlib.Path(__file__).parent.joinpath("data").resolve()
DATA_ROOT = DATA_PATH.joinpath("Results", "Sankey_preprocessed")

YEAR_MIN = 2000
YEAR_MAX = 2022
YEAR_DEFAULT = 2022

SCOPE_GLOBAL = "global"
SCOPE_LOCAL = "local"
DETAIL_SUMMARY = "summary"
DETAIL_DETAILED = "detailed"

COMMODITIES = [
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

PALETTE_COLORS = [
    "#4C72B0",
    "#55A868",
    "#C44E52",
    "#8172B3",
    "#CCB974",
    "#64B5CD",
    "#8C8C8C",
    "#E377C2",
    "#F39C12",
    "#17BECF",
    "#9E9E9E",
    "#F1A340",
    "#D84A6B",
    "#5E4FA2",
    "#2C7BB6",
]

LEGACY_COLOR_MAPPING = {
    # Legacy palette used in older preprocessed files.
    "#0072ff": "#4C72B0",
    "#00cafe": "#55A868",
    "#b0ebff": "#C44E52",
    "#fff1b7": "#8172B3",
    "#ffdc23": "#CCB974",
    "#ffb758": "#64B5CD",
    "#ff8200": "#8C8C8C",
}

with open(DATA_PATH.joinpath("dictreg.json"), encoding="utf-8") as f:
    REGIONS = json.loads(f.read())

REGIONS.pop("DYE", None)
REGIONS.pop("SDS", None)
REGIONS["World"] = "World"

FIGURE_FONT = "Avenir Next, Segoe UI Variable Text, Trebuchet MS, Tahoma, sans-serif"


def _normalize_color(color_value):
    if not isinstance(color_value, str):
        return color_value
    return LEGACY_COLOR_MAPPING.get(color_value.lower(), color_value)


def _coerce_scope(scope):
    return scope if scope in {SCOPE_GLOBAL, SCOPE_LOCAL} else SCOPE_GLOBAL


def _coerce_detail(detail):
    return detail if detail in {DETAIL_SUMMARY, DETAIL_DETAILED} else DETAIL_SUMMARY


def _effective_detail(scope, detail):
    detail = _coerce_detail(detail)
    if _coerce_scope(scope) != SCOPE_LOCAL:
        return DETAIL_SUMMARY
    return detail


def _coerce_commodity(commodity):
    if commodity in COMMODITIES:
        return commodity
    return "Copper ores"


def _coerce_year(year):
    try:
        year = int(year)
    except (TypeError, ValueError):
        return YEAR_DEFAULT
    return min(max(year, YEAR_MIN), YEAR_MAX)


def _coerce_region(region):
    if region in REGIONS:
        return region
    return "World"


def _coerce_unit(unit):
    if unit in {"kTonnes", "Tonnes per capita"}:
        return unit
    return "kTonnes"


def _sort_regions(regions):
    return sorted(regions, key=lambda item: (item != "World", REGIONS.get(item, item)))


def _view_summary_text(scope, detail, commodity, region, year, unit):
    scope = _coerce_scope(scope)
    detail = _effective_detail(scope, detail)
    commodity = _coerce_commodity(commodity)
    region = _coerce_region(region)
    year = _coerce_year(year)
    unit = _coerce_unit(unit)

    if scope == SCOPE_GLOBAL:
        scope_line = "View mode: full world view."
    else:
        scope_line = (
            "View mode: region-focused view (only links connected to the selected region are shown "
            "at owner location, extraction location, or final consumption)."
        )

    detail_line = (
        "Consumption detail: one stage."
        if detail == DETAIL_SUMMARY
        else "Consumption detail: three stages."
    )
    region_label = REGIONS.get(region, region)
    return (
        f"{scope_line} {detail_line} "
        f"Selected case: {commodity}; {region_label} ({region}); {year}; {unit}."
    )


def _apply_figure_theme(fig, legend_y=-0.07, height=620):
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
    return _apply_figure_theme(fig, height=620)


def _legend_names(region):
    return [
        "<b>Nationality of mine owners:</b>",
        REGIONS.get(region, region),
        "Africa",
        "Asia-Pacific",
        "EECCA",
        "Europe",
        "Latin America",
        "Middle East",
        "North America",
        "Unknown",
    ]


def _create_legend_traces(colors, names):
    return [
        go.Scatter(
            x=[None],
            y=[None],
            mode="markers",
            marker={"size": 10, "color": color},
            showlegend=True,
            name=name,
        )
        for color, name in zip(colors, names)
    ]


def _data_dir(scope, detail, commodity):
    scope = _coerce_scope(scope)
    detail = _effective_detail(scope, detail)
    commodity = _coerce_commodity(commodity)

    if scope == SCOPE_GLOBAL:
        return DATA_ROOT.joinpath("Ownership simple global", commodity), "simple"
    if detail == DETAIL_DETAILED:
        return DATA_ROOT.joinpath("Commodity all ownership", commodity), "detailed"
    return DATA_ROOT.joinpath("Ownership simple local", commodity), "simple"


def _regions_for_selection(scope, detail, commodity, year):
    year = _coerce_year(year)
    commodity_dir, _ = _data_dir(scope, detail, commodity)
    regions = set()
    if commodity_dir.exists():
        for file_path in commodity_dir.glob(f"*_{year}.pkl.lzma"):
            stem = file_path.name[: -len(".pkl.lzma")]
            if "_" not in stem:
                continue
            region, _ = stem.rsplit("_", 1)
            regions.add(region)

    if regions:
        return _sort_regions(list(regions))
    return _sort_regions(list(REGIONS.keys()))


def _load_preprocessed(scope, detail, commodity, region, year):
    commodity_dir, mode_kind = _data_dir(scope, detail, commodity)
    preprocessed_data_path = commodity_dir.joinpath(f"{region}_{year}.pkl.lzma")
    with lzma.open(preprocessed_data_path, "rb") as f:
        preprocessed_data = pickle.load(f)
    return preprocessed_data, mode_kind


def _build_figure(scope, detail, commodity, region, year, unit):
    scope = _coerce_scope(scope)
    detail = _effective_detail(scope, detail)
    commodity = _coerce_commodity(commodity)
    region = _coerce_region(region)
    year = _coerce_year(year)
    unit = _coerce_unit(unit)

    preprocessed_data, mode_kind = _load_preprocessed(
        scope=scope,
        detail=detail,
        commodity=commodity,
        region=region,
        year=year,
    )

    sankey = (
        preprocessed_data["sankey_cap"]
        if unit == "Tonnes per capita"
        else preprocessed_data["sankey"]
    )
    layout = preprocessed_data["layout"]
    arrows_and_labels = preprocessed_data["arrows_and_labels"]

    if mode_kind == "simple":
        for ann in arrows_and_labels.get("annotations", []):
            if "Nationality of mine owners" in ann.get("text", ""):
                ann["x"] = min(1, ann.get("x", 0) + 0.03)

    sankey["link"]["color"] = np.array([_normalize_color(c) for c in sankey["link"]["color"]])

    fig = go.Figure(sankey)
    fig.update_layout(**layout)
    fig.update_layout(
        shapes=arrows_and_labels.get("shapes", []),
        annotations=arrows_and_labels.get("annotations", []),
    )

    legend_colors = ["white"] + list(PALETTE_COLORS[:9])
    fig.add_traces(_create_legend_traces(legend_colors, _legend_names(region)))
    fig.update_layout(showlegend=True)

    return _apply_figure_theme(fig, legend_y=-0.08, height=620)


DEFAULT_SCOPE = SCOPE_GLOBAL
DEFAULT_DETAIL = DETAIL_SUMMARY
DEFAULT_COMMODITY = _coerce_commodity("Copper ores")
DEFAULT_YEAR = YEAR_DEFAULT
DEFAULT_UNIT = "kTonnes"
_default_regions = _regions_for_selection(
    DEFAULT_SCOPE,
    DEFAULT_DETAIL,
    DEFAULT_COMMODITY,
    DEFAULT_YEAR,
)
DEFAULT_REGION = "World" if "World" in _default_regions else _default_regions[0]

try:
    INITIAL_FIGURE = _build_figure(
        scope=DEFAULT_SCOPE,
        detail=DEFAULT_DETAIL,
        commodity=DEFAULT_COMMODITY,
        region=DEFAULT_REGION,
        year=DEFAULT_YEAR,
        unit=DEFAULT_UNIT,
    )
except Exception:
    INITIAL_FIGURE = _empty_figure("No preprocessed Sankey file found for this selection.")

SUGGESTED_CITATION_MARKDOWN = """
#### Suggested citation

If you use these diagrams, please cite:

Andrieu, B., Cervantes Barron, K., Heydari, M. et al. (2025). *Country's wealth is not associated with domestic control of metal ore extraction*. Communications Earth & Environment, 6, 379. https://www.nature.com/articles/s43247-025-02321-1

Data source and method:

- Lenzen, M. et al. (2021). *Implementing the Material Footprint to measure progress towards SDGs 8 and 12*. Nature Sustainability. https://www.nature.com/articles/s41893-021-00811-6
- Lenzen, M. et al. (2017). *The Global MRIO Lab - charting the world economy*. Economic Systems Research, 29, 158-186. https://doi.org/10.1080/09535314.2017.1301887
"""


layout = dbc.Container(
    [
        html.Section(
            [
                html.H2("Ownership Explorer", className="page-head-title"),
                html.P(
                    "Use one chart workspace for both global context and focal-country analysis.",
                    className="page-head-subtitle",
                ),
            ],
            className="page-head reveal",
        ),
        html.Div(
            dcc.Markdown(
                """
Use the controls below in this order:

- **View scope**
  - **Global view** shows the whole world system.
  - **Region-focused view** keeps only links connected to the selected region.
- **Consumption detail**
  - **One stage** shows one combined final-consumption block.
  - **Three stages** shows a more detailed breakdown on the right side.
- **Commodity, region, year, and unit** define the exact case shown in the chart.
- In this tab, the left-most stage shows where mine owners are based.
"""
            ),
            className="app-card info-card docs-card reveal",
        ),
        html.Div(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            html.Div(
                                [
                                    html.H4("1. Start with scope"),
                                    html.P("Start with global view, then switch to region-focused view to reduce clutter."),
                                ],
                                className="guide-kpi",
                            ),
                            xs=12,
                            md=4,
                        ),
                        dbc.Col(
                            html.Div(
                                [
                                    html.H4("2. Add detail"),
                                    html.P("Keep one-stage detail first; use three-stage detail only when you need finer interpretation."),
                                ],
                                className="guide-kpi",
                            ),
                            xs=12,
                            md=4,
                        ),
                        dbc.Col(
                            html.Div(
                                [
                                    html.H4("3. Interpret ownership"),
                                    html.P("Read the left-most column as owner location, then follow links to extraction and consumption."),
                                ],
                                className="guide-kpi",
                            ),
                            xs=12,
                            md=4,
                        ),
                    ],
                    class_name="g-3 guide-kpis",
                )
            ],
            className="app-card info-card reveal",
        ),
        html.Div(
            [
                html.Div(
                    _view_summary_text(
                        DEFAULT_SCOPE,
                        DEFAULT_DETAIL,
                        DEFAULT_COMMODITY,
                        DEFAULT_REGION,
                        DEFAULT_YEAR,
                        DEFAULT_UNIT,
                    ),
                    id="ownership-view-summary",
                    className="view-summary",
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            html.Div(
                                [
                                    html.P("View scope", className="control-label"),
                                    dbc.RadioItems(
                                        id="ownership-explorer-scope",
                                        options=[
                                            {
                                                "label": "Global context",
                                                "value": SCOPE_GLOBAL,
                                            },
                                            {
                                                "label": "Isolate region flows",
                                                "value": SCOPE_LOCAL,
                                            },
                                        ],
                                        value=DEFAULT_SCOPE,
                                        inline=True,
                                        persistence=True,
                                        persistence_type="session",
                                        class_name="control-radio-group",
                                    ),
                                ],
                                className="control-field",
                            ),
                            width=12,
                        ),
                    ],
                    class_name="g-3",
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            html.Div(
                                [
                                    html.P(
                                        "Consumption detail (isolate mode only)",
                                        className="control-label",
                                    ),
                                    dbc.RadioItems(
                                        id="ownership-explorer-detail",
                                        options=[
                                            {
                                                "label": "1-step consumption view",
                                                "value": DETAIL_SUMMARY,
                                            },
                                            {
                                                "label": "3-step consumption view",
                                                "value": DETAIL_DETAILED,
                                            },
                                        ],
                                        value=DEFAULT_DETAIL,
                                        inline=True,
                                        persistence=True,
                                        persistence_type="session",
                                        class_name="control-radio-group",
                                    ),
                                ],
                                className="control-field",
                                id="ownership-explorer-detail-wrap",
                            ),
                            width=12,
                        ),
                    ],
                    class_name="g-3 mt-1",
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            html.Div(
                                [
                                    html.P("Commodity", className="control-label"),
                                    dcc.Dropdown(
                                        id="ownership-explorer-commodity",
                                        options=[
                                            {"label": commodity, "value": commodity}
                                            for commodity in COMMODITIES
                                        ],
                                        value=DEFAULT_COMMODITY,
                                        clearable=False,
                                        multi=False,
                                        persistence=True,
                                        persistence_type="session",
                                        className="dash-dropdown",
                                    ),
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
                                    dcc.Dropdown(
                                        id="ownership-explorer-region",
                                        options=[
                                            {
                                                "label": REGIONS.get(region, region),
                                                "value": region,
                                            }
                                            for region in _default_regions
                                        ],
                                        value=DEFAULT_REGION,
                                        clearable=False,
                                        multi=False,
                                        persistence=True,
                                        persistence_type="session",
                                        className="dash-dropdown",
                                    ),
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
                                    dcc.Dropdown(
                                        id="ownership-explorer-unit",
                                        options=["kTonnes", "Tonnes per capita"],
                                        value=DEFAULT_UNIT,
                                        clearable=False,
                                        multi=False,
                                        persistence=True,
                                        persistence_type="session",
                                        className="dash-dropdown",
                                    ),
                                ],
                                className="control-field",
                            ),
                            xs=12,
                            md=4,
                        ),
                    ],
                    class_name="g-3 mt-1",
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            html.Div(
                                [
                                    html.P("Data year", className="control-label"),
                                    html.Div(
                                        id="ownership-explorer-year-label",
                                        className="control-value-label",
                                        children=f"Data year: {DEFAULT_YEAR}",
                                    ),
                                    dcc.Slider(
                                        id="ownership-explorer-year",
                                        min=YEAR_MIN,
                                        max=YEAR_MAX,
                                        step=1,
                                        value=DEFAULT_YEAR,
                                        marks={
                                            str(year): str(year)
                                            for year in range(YEAR_MIN, YEAR_MAX + 1, 2)
                                        },
                                        tooltip={
                                            "placement": "bottom",
                                            "always_visible": False,
                                        },
                                        persistence=True,
                                        persistence_type="session",
                                        className="themed-slider",
                                    ),
                                ],
                                className="control-field",
                            ),
                            width=12,
                        ),
                    ],
                    class_name="g-3 mt-1",
                ),
            ],
            className="app-card controls-card reveal",
        ),
        html.Div(
            [
                dcc.Graph(
                    id="ownership-explorer-graph",
                    figure=INITIAL_FIGURE,
                    responsive=True,
                    className="themed-graph",
                    style={"height": "620px", "width": "100%"},
                )
            ],
            className="app-card graph-card reveal",
        ),
        html.Div(
            dcc.Markdown(
                "Read this as: owner location (left), then extraction, then consumption stages. "
                "Suggested workflow: start with **Global view**, switch to **Region-focused view**, "
                "then increase consumption detail from **one stage** to **three stages** when needed."
            ),
            className="app-card info-card slim-card reveal",
        ),
        html.Div(
            dcc.Markdown(SUGGESTED_CITATION_MARKDOWN),
            className="app-card info-card reveal",
        ),
    ],
    fluid=True,
    className="page-frame page-ownership-explorer",
)


@app.callback(
    Output("ownership-explorer-detail-wrap", "style"),
    Output("ownership-explorer-detail", "value"),
    Input("ownership-explorer-scope", "value"),
    State("ownership-explorer-detail", "value"),
)
def toggle_detail_control(scope, detail_value):
    scope = _coerce_scope(scope)
    detail_value = _coerce_detail(detail_value)
    if scope == SCOPE_LOCAL:
        return {"display": "block"}, detail_value
    return {"display": "none"}, DETAIL_SUMMARY


@app.callback(
    Output("ownership-explorer-region", "options"),
    Output("ownership-explorer-region", "value"),
    Input("ownership-explorer-scope", "value"),
    Input("ownership-explorer-detail", "value"),
    Input("ownership-explorer-commodity", "value"),
    Input("ownership-explorer-year", "value"),
    State("ownership-explorer-region", "value"),
)
def update_region_options(scope, detail, commodity, year, current_region):
    scope = _coerce_scope(scope)
    detail = _effective_detail(scope, detail)
    commodity = _coerce_commodity(commodity)
    year = _coerce_year(year)
    current_region = _coerce_region(current_region)

    regions = _regions_for_selection(scope, detail, commodity, year)
    options = [{"label": REGIONS.get(region, region), "value": region} for region in regions]

    if current_region in regions:
        resolved_region = current_region
    else:
        resolved_region = "World" if "World" in regions else regions[0]

    return options, resolved_region


@app.callback(
    Output("ownership-explorer-year-label", "children"),
    Input("ownership-explorer-year", "value"),
)
def update_year_label(year):
    return f"Data year: {_coerce_year(year)}"


@app.callback(
    Output("ownership-view-summary", "children"),
    Input("ownership-explorer-scope", "value"),
    Input("ownership-explorer-detail", "value"),
    Input("ownership-explorer-commodity", "value"),
    Input("ownership-explorer-region", "value"),
    Input("ownership-explorer-year", "value"),
    Input("ownership-explorer-unit", "value"),
)
def update_view_summary(scope, detail, commodity, region, year, unit):
    return _view_summary_text(scope, detail, commodity, region, year, unit)


@app.callback(
    Output("ownership-explorer-graph", "figure"),
    Input("ownership-explorer-scope", "value"),
    Input("ownership-explorer-detail", "value"),
    Input("ownership-explorer-commodity", "value"),
    Input("ownership-explorer-region", "value"),
    Input("ownership-explorer-year", "value"),
    Input("ownership-explorer-unit", "value"),
)
def update_figure(scope, detail, commodity, region, year, unit):
    scope = _coerce_scope(scope)
    detail = _effective_detail(scope, detail)
    commodity = _coerce_commodity(commodity)
    year = _coerce_year(year)
    unit = _coerce_unit(unit)

    regions = _regions_for_selection(scope, detail, commodity, year)
    region = _coerce_region(region)
    if region not in regions:
        region = "World" if "World" in regions else regions[0]

    try:
        return _build_figure(
            scope=scope,
            detail=detail,
            commodity=commodity,
            region=region,
            year=year,
            unit=unit,
        )
    except FileNotFoundError:
        if scope == SCOPE_GLOBAL:
            mode_msg = "global context"
        elif detail == DETAIL_DETAILED:
            mode_msg = "isolated region with 3-step consumption"
        else:
            mode_msg = "isolated region with 1-step consumption"
        return _empty_figure(f"No preprocessed Sankey file found for {mode_msg}.")


@app.callback(
    Output("ownership-explorer-commodity", "value"),
    Output("ownership-explorer-year", "value"),
    Output("ownership-explorer-region", "value"),
    Output("ownership-explorer-unit", "value"),
    Input("tabs", "active_tab"),
    State("shared-commodity-store", "data"),
    State("shared-year-store", "data"),
    State("shared-region-store", "data"),
    State("shared-unit-store", "data"),
    prevent_initial_call=True,
)
def apply_shared_selection(active_tab, commodity, year, region, unit):
    if active_tab != "tab-1":
        raise PreventUpdate

    return (
        _coerce_commodity(commodity),
        _coerce_year(year),
        _coerce_region(region),
        _coerce_unit(unit),
    )


@app.callback(
    Output("shared-commodity-store", "data", allow_duplicate=True),
    Output("shared-year-store", "data", allow_duplicate=True),
    Output("shared-region-store", "data", allow_duplicate=True),
    Output("shared-unit-store", "data", allow_duplicate=True),
    Input("ownership-explorer-commodity", "value"),
    Input("ownership-explorer-year", "value"),
    Input("ownership-explorer-region", "value"),
    Input("ownership-explorer-unit", "value"),
    prevent_initial_call=True,
)
def persist_shared_selection(commodity, year, region, unit):
    triggered = callback_context.triggered_id

    commodity_out = no_update
    year_out = no_update
    region_out = no_update
    unit_out = no_update

    if triggered == "ownership-explorer-commodity":
        commodity_out = _coerce_commodity(commodity)
    elif triggered == "ownership-explorer-year":
        year_out = _coerce_year(year)
    elif triggered == "ownership-explorer-region":
        region_out = _coerce_region(region)
    elif triggered == "ownership-explorer-unit":
        unit_out = _coerce_unit(unit)

    return commodity_out, year_out, region_out, unit_out
