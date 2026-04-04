"""
Footprint explorer (non-ownership) with unified scope/detail controls.
"""

import json
import lzma
import pathlib
import pickle

import dash_bootstrap_components as dbc
import numpy as np
import plotly.graph_objs as go
from dash import Input, Output, State, callback_context, dcc, html, no_update
from dash.exceptions import PreventUpdate
from flask_caching import Cache

from app import app
from slider import PlaybackSliderAIO

cache = Cache(
    app.server, config={"CACHE_TYPE": "FileSystemCache", "CACHE_DIR": "cache"}
)

DATA_PATH = pathlib.Path(__file__).parent.joinpath("data").resolve()
DATA_ROOT = DATA_PATH.joinpath("Results", "Sankey_preprocessed")

YEAR_MIN = 2000
YEAR_MAX = 2022
YEAR_DEFAULT = 2022

SCOPE_GLOBAL = "global"
SCOPE_LOCAL = "local"
DETAIL_SUMMARY = "summary"
DETAIL_DETAILED = "detailed"

COMMODITY_OPTIONS = [
    "All commodities",
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
    "Chromium ores",
    "Platinum ores",
    "Titanium ores",
    "Other metal ores",
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

ALL_SIMPLE_GLOBAL_ALIASES = [
    "All_commodities_simple global",
    "All commodities simple global",
]
ALL_SIMPLE_LOCAL_ALIASES = [
    "All_commodities_simple local",
    "All commodities simple local",
]
COMMODITY_SIMPLE_GLOBAL_ALIASES = [
    "Commodity simple global",
    "Commodity_simple global",
]
COMMODITY_SIMPLE_LOCAL_ALIASES = [
    "Commodity simple local",
    "Commodity_simple local",
]

FIGURE_FONT = "Avenir Next, Segoe UI Variable Text, Trebuchet MS, Tahoma, sans-serif"

with open(DATA_PATH.joinpath("dictreg.json"), encoding="utf-8") as f:
    REGIONS = json.loads(f.read())
REGIONS.pop("DYE", None)
REGIONS.pop("SDS", None)
REGIONS["World"] = "World"


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


def _coerce_commodity(commodity):
    if commodity in COMMODITY_OPTIONS:
        return commodity
    return "Copper ores"


def _sort_regions(regions):
    return sorted(regions, key=lambda item: (item != "World", REGIONS.get(item, item)))


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


def _commodity_legend(region):
    return {
        "colors": ["white"] + list(PALETTE_COLORS[:8]),
        "names": [
            "<b>Region of ores extraction:</b>",
            REGIONS.get(region, region),
            "Africa",
            "Asia-Pacific",
            "EECCA",
            "Europe",
            "Latin America",
            "Middle East",
            "North America",
        ],
    }


def _all_commodities_legend():
    return {
        "colors": ["white"] + list(PALETTE_COLORS[:8]),
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
        "colors2": ["white"] + list(PALETTE_COLORS[8:15]),
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
    }


def _candidate_dirs(scope, detail, commodity):
    scope = _coerce_scope(scope)
    detail = _effective_detail(scope, detail)
    commodity = _coerce_commodity(commodity)
    all_commodities = commodity == "All commodities"

    if scope == SCOPE_GLOBAL and detail == DETAIL_SUMMARY:
        aliases = ALL_SIMPLE_GLOBAL_ALIASES if all_commodities else COMMODITY_SIMPLE_GLOBAL_ALIASES
    elif scope == SCOPE_LOCAL and detail == DETAIL_SUMMARY:
        aliases = ALL_SIMPLE_LOCAL_ALIASES if all_commodities else COMMODITY_SIMPLE_LOCAL_ALIASES
    elif scope == SCOPE_LOCAL and detail == DETAIL_DETAILED:
        aliases = ["All commodities"] if all_commodities else ["Commodity"]
    else:
        aliases = ["All commodities"] if all_commodities else ["Commodity"]

    dirs = []
    for alias in aliases:
        base = DATA_ROOT.joinpath(alias)
        dirs.append(base if all_commodities else base.joinpath(commodity))
    return dirs


def _resolve_existing_dir(scope, detail, commodity):
    candidates = _candidate_dirs(scope, detail, commodity)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def _dataset_mode_label(scope, detail):
    scope = _coerce_scope(scope)
    detail = _effective_detail(scope, detail)
    if scope == SCOPE_GLOBAL:
        return "global context, 1-step"
    if detail == DETAIL_SUMMARY:
        return "isolate region flows, 1-step"
    return "isolate region flows, 3-step"


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
            "at extraction or final consumption)."
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


def _regions_for_selection(scope, detail, commodity, year):
    year = _coerce_year(year)
    data_dir = _resolve_existing_dir(scope, detail, commodity)
    regions = set()

    if data_dir.exists():
        for file_path in data_dir.glob(f"*_{year}.pkl.lzma"):
            stem = file_path.name[: -len(".pkl.lzma")]
            if "_" not in stem:
                continue
            region, _ = stem.rsplit("_", 1)
            regions.add(region)

    if regions:
        return _sort_regions(list(regions))
    return _sort_regions(list(REGIONS.keys()))


def _load_preprocessed(scope, detail, commodity, region, year):
    data_dir = _resolve_existing_dir(scope, detail, commodity)
    data_path = data_dir.joinpath(f"{region}_{year}.pkl.lzma")
    with lzma.open(data_path, "rb") as f:
        preprocessed_data = pickle.load(f)
    return preprocessed_data, data_path


@cache.memoize()
def _build_figure(scope, detail, region, year, unit, commodity):
    scope = _coerce_scope(scope)
    detail = _effective_detail(scope, detail)
    region = _coerce_region(region)
    year = _coerce_year(year)
    unit = _coerce_unit(unit)
    commodity = _coerce_commodity(commodity)

    preprocessed_data, _ = _load_preprocessed(scope, detail, commodity, region, year)

    sankey = (
        preprocessed_data["sankey_cap"]
        if unit == "Tonnes per capita"
        else preprocessed_data["sankey"]
    )
    layout = preprocessed_data["layout"]
    arrows_and_labels = preprocessed_data["arrows_and_labels"]

    sankey["link"]["color"] = np.array([_normalize_color(c) for c in sankey["link"]["color"]])

    fig = go.Figure(sankey)
    fig.update_layout(**layout)
    fig.update_layout(
        shapes=arrows_and_labels.get("shapes", []),
        annotations=arrows_and_labels.get("annotations", []),
    )

    if commodity == "All commodities":
        legend = _all_commodities_legend()
        fig.add_traces(_create_legend_traces(legend["colors"], legend["names"]))
        fig.add_traces(_create_legend_traces(legend["colors2"], legend["names2"]))
        legend_y = -0.11
    else:
        legend = _commodity_legend(region)
        fig.add_traces(_create_legend_traces(legend["colors"], legend["names"]))
        legend_y = -0.06

    fig.update_layout(showlegend=True)
    return _apply_figure_theme(fig, legend_y=legend_y, height=620)


def fig_sankey(region, year, unit="kTonnes", sankey_subtype="Copper ores"):
    """
    Backward-compatible helper used by landing examples.
    Keeps the historical non-ownership detailed behavior.
    """
    try:
        return _build_figure(
            scope=SCOPE_LOCAL,
            detail=DETAIL_DETAILED,
            region=region,
            year=year,
            unit=unit,
            commodity=sankey_subtype,
        )
    except FileNotFoundError:
        return _empty_figure("No preprocessed Sankey file found for this selection.")


DEFAULT_SCOPE = SCOPE_GLOBAL
DEFAULT_DETAIL = DETAIL_SUMMARY
DEFAULT_COMMODITY = "All commodities"
DEFAULT_YEAR = YEAR_DEFAULT
DEFAULT_UNIT = "kTonnes"
_default_regions = _regions_for_selection(
    DEFAULT_SCOPE, DEFAULT_DETAIL, DEFAULT_COMMODITY, DEFAULT_YEAR
)
DEFAULT_REGION = "World" if "World" in _default_regions else _default_regions[0]

try:
    INITIAL_FIGURE = _build_figure(
        scope=DEFAULT_SCOPE,
        detail=DEFAULT_DETAIL,
        region=DEFAULT_REGION,
        year=DEFAULT_YEAR,
        unit=DEFAULT_UNIT,
        commodity=DEFAULT_COMMODITY,
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
                html.H2("Footprint Explorer", className="page-head-title"),
                html.P(
                    "Explore non-ownership flows in one workspace, from global context to focal-region detail.",
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
- Colors start at the left side of each path and stay the same along that path.
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
                                    html.H4("1. Pick scope"),
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
                                    html.H4("2. Pick detail"),
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
                                    html.H4("3. Read left to right"),
                                    html.P("Read one chart carefully first, then compare the same settings across years."),
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
                    id="footprint-view-summary",
                    className="view-summary",
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            html.Div(
                                [
                                    html.P("View scope", className="control-label"),
                                    dbc.RadioItems(
                                        id="footprint-explorer-scope",
                                        options=[
                                            {"label": "Global context", "value": SCOPE_GLOBAL},
                                            {"label": "Isolate region flows", "value": SCOPE_LOCAL},
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
                        )
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
                                        id="footprint-explorer-detail",
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
                                id="footprint-explorer-detail-wrap",
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
                                        id="slct_subtype_2",
                                        options=COMMODITY_OPTIONS,
                                        value=DEFAULT_COMMODITY,
                                        multi=False,
                                        clearable=False,
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
                                        id="slct2_2",
                                        options=[
                                            {"label": REGIONS.get(r, r), "value": r}
                                            for r in _default_regions
                                        ],
                                        value=DEFAULT_REGION,
                                        multi=False,
                                        clearable=False,
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
                                        id="slct_unit_2",
                                        options=["kTonnes", "Tonnes per capita"],
                                        value=DEFAULT_UNIT,
                                        multi=False,
                                        clearable=False,
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
            ],
            className="app-card controls-card reveal",
        ),
        html.Div(
            [
                dcc.Graph(
                    id="graph2_2",
                    responsive=True,
                    figure=INITIAL_FIGURE,
                    className="themed-graph",
                    style={"height": "620px", "width": "100%"},
                )
            ],
            className="app-card graph-card reveal",
        ),
        html.Div(
            [
                PlaybackSliderAIO(
                    aio_id="bruh2_2",
                    slider_props={
                        "min": YEAR_MIN,
                        "max": YEAR_MAX,
                        "step": 1,
                        "value": DEFAULT_YEAR,
                        "marks": {str(year): str(year) for year in range(YEAR_MIN, YEAR_MAX + 1, 1)},
                        "persistence": True,
                        "persistence_type": "session",
                    },
                    button_props={"className": "float-left"},
                    interval_props={"interval": 2500},
                )
            ],
            className="app-card slider-card reveal",
        ),
        html.Div(
            dcc.Markdown(
                "Suggested workflow: start with **Global view**, then switch to **Region-focused view**. "
                "Only after that, increase consumption detail from **one stage** to **three stages** if needed."
            ),
            className="app-card info-card slim-card reveal",
        ),
        html.Div(
            dcc.Markdown(SUGGESTED_CITATION_MARKDOWN),
            className="app-card info-card reveal",
        ),
    ],
    fluid=True,
    className="page-frame page-commodity",
)


@app.callback(
    Output("footprint-explorer-detail-wrap", "style"),
    Output("footprint-explorer-detail", "value"),
    Input("footprint-explorer-scope", "value"),
    State("footprint-explorer-detail", "value"),
)
def toggle_detail_control(scope, detail_value):
    scope = _coerce_scope(scope)
    detail_value = _coerce_detail(detail_value)
    if scope == SCOPE_LOCAL:
        return {"display": "block"}, detail_value
    return {"display": "none"}, DETAIL_SUMMARY


@app.callback(
    Output("slct2_2", "options"),
    Output("slct2_2", "value"),
    Input("footprint-explorer-scope", "value"),
    Input("footprint-explorer-detail", "value"),
    Input("slct_subtype_2", "value"),
    Input(PlaybackSliderAIO.ids.slider("bruh2_2"), "value"),
    State("slct2_2", "value"),
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
    Output("footprint-view-summary", "children"),
    Input("footprint-explorer-scope", "value"),
    Input("footprint-explorer-detail", "value"),
    Input("slct_subtype_2", "value"),
    Input("slct2_2", "value"),
    Input(PlaybackSliderAIO.ids.slider("bruh2_2"), "value"),
    Input("slct_unit_2", "value"),
)
def update_view_summary(scope, detail, commodity, region, year, unit):
    return _view_summary_text(scope, detail, commodity, region, year, unit)


@app.callback(
    Output("graph2_2", "figure"),
    Input("footprint-explorer-scope", "value"),
    Input("footprint-explorer-detail", "value"),
    Input("slct2_2", "value"),
    Input(PlaybackSliderAIO.ids.slider("bruh2_2"), "value"),
    Input("slct_unit_2", "value"),
    Input("slct_subtype_2", "value"),
)
def update_figure(scope, detail, region, year, unit, commodity):
    scope = _coerce_scope(scope)
    detail = _effective_detail(scope, detail)
    region = _coerce_region(region)
    year = _coerce_year(year)
    unit = _coerce_unit(unit)
    commodity = _coerce_commodity(commodity)

    regions = _regions_for_selection(scope, detail, commodity, year)
    if region not in regions:
        region = "World" if "World" in regions else regions[0]

    try:
        return _build_figure(
            scope=scope,
            detail=detail,
            region=region,
            year=year,
            unit=unit,
            commodity=commodity,
        )
    except FileNotFoundError:
        mode_label = _dataset_mode_label(scope, detail)
        return _empty_figure(
            "No preprocessed Sankey file found for "
            f"{mode_label} | {commodity} | {region} | {year}."
        )


@app.callback(
    Output("slct2_2", "value", allow_duplicate=True),
    Output(PlaybackSliderAIO.ids.slider("bruh2_2"), "value", allow_duplicate=True),
    Output("slct_unit_2", "value", allow_duplicate=True),
    Output("slct_subtype_2", "value", allow_duplicate=True),
    Input("tabs", "active_tab"),
    State("shared-region-store", "data"),
    State("shared-year-store", "data"),
    State("shared-unit-store", "data"),
    State("shared-commodity-store", "data"),
    prevent_initial_call=True,
)
def apply_shared_selection(active_tab, region, year, unit, commodity):
    if active_tab != "tab-3":
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
    Input("slct2_2", "value"),
    Input(PlaybackSliderAIO.ids.slider("bruh2_2"), "value"),
    Input("slct_unit_2", "value"),
    Input("slct_subtype_2", "value"),
    prevent_initial_call=True,
)
def persist_shared_selection(region, year, unit, commodity):
    triggered = callback_context.triggered_id

    region_out = no_update
    year_out = no_update
    unit_out = no_update
    commodity_out = no_update

    if triggered == "slct2_2":
        region_out = _coerce_region(region)
    elif isinstance(triggered, dict) and triggered.get("subcomponent") == "slider":
        year_out = _coerce_year(year)
    elif triggered == "slct_unit_2":
        unit_out = _coerce_unit(unit)
    elif triggered == "slct_subtype_2":
        commodity_out = _coerce_commodity(commodity)

    return region_out, year_out, unit_out, commodity_out
