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
YEAR = 2022
YEAR_MIN = 2000
YEAR_MAX = 2022

with open(DATA_PATH.joinpath("dictreg.json")) as f:
    REGIONS = json.loads(f.read())

REGIONS.pop("DYE", None)
REGIONS.pop("SDS", None)
REGIONS["World"] = "World"

COMMODITY_ORDER = [
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

SIMPLE_OWNERSHIP_COMMODITIES = [
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

# Shared palette order used by preprocessing legends.
colors = [
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


def _normalize_color(color_value):
    if not isinstance(color_value, str):
        return color_value
    return LEGACY_COLOR_MAPPING.get(color_value.lower(), color_value)

FIGURE_FONT = "Avenir Next, Segoe UI Variable Text, Trebuchet MS, Tahoma, sans-serif"


def _sort_commodities(commodities):
    rank = {name: idx for idx, name in enumerate(COMMODITY_ORDER)}
    return sorted(commodities, key=lambda item: (rank.get(item, 999), item))


def _sort_regions(regions):
    return sorted(regions, key=lambda item: (item != "World", REGIONS.get(item, item)))


def _apply_figure_theme(fig, legend_y=-0.06, height=620):
    fig.update_layout(
        height=height,
        font={"family": FIGURE_FONT, "size": 12, "color": "#44372b"},
        margin={"l": 20, "r": 20, "t": 56, "b": 92},
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
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
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


def _mode_dirs(sankey_subtype=None, mode="local"):
    mode_key = mode.lower()
    if mode_key == "local":
        folder = "Ownership simple local"
    elif mode_key == "global":
        folder = "Ownership simple global"
    else:
        raise ValueError(f"Unsupported mode: {mode}")

    base_dir = DATA_ROOT.joinpath(folder)
    if sankey_subtype:
        return folder, base_dir.joinpath(sankey_subtype)
    return folder, base_dir


def _discover_dataset(mode):
    _, mode_root = _mode_dirs(mode=mode)
    options = {}
    if not mode_root.exists():
        return options

    for commodity_dir in mode_root.iterdir():
        if not commodity_dir.is_dir():
            continue

        regions = set()
        for file_path in commodity_dir.glob(f"*_{YEAR}.pkl.lzma"):
            stem = file_path.name[: -len(".pkl.lzma")]
            if "_" not in stem:
                continue
            region, _ = stem.rsplit("_", 1)
            regions.add(region)

        if regions:
            options[commodity_dir.name] = _sort_regions(list(regions))

    return options


def _available_commodities(mode):
    _, mode_root = _mode_dirs(mode=mode)
    if mode_root.exists():
        on_disk = {d.name for d in mode_root.iterdir() if d.is_dir()}
        discovered = [c for c in SIMPLE_OWNERSHIP_COMMODITIES if c in on_disk]
        if discovered:
            return discovered
    return list(SIMPLE_OWNERSHIP_COMMODITIES)


def _regions_for_commodity(mode, commodity, year=YEAR):
    _, commodity_root = _mode_dirs(sankey_subtype=commodity, mode=mode)
    regions = set()
    if commodity_root.exists():
        for file_path in commodity_root.glob(f"*_{year}.pkl.lzma"):
            stem = file_path.name[: -len(".pkl.lzma")]
            if "_" not in stem:
                continue
            region, _ = stem.rsplit("_", 1)
            regions.add(region)

    if regions:
        return _sort_regions(list(regions))

    # Fallback that keeps the UI usable even if a commodity folder is incomplete.
    return _sort_regions(list(REGIONS.keys()))


def _select_defaults(dataset, commodity=None, region=None):
    if not dataset:
        return None, None

    commodities = _sort_commodities(list(dataset.keys()))
    if commodity not in dataset:
        commodity = commodities[0]

    regions = dataset.get(commodity, [])
    if not regions:
        return commodity, None

    if region not in regions:
        region = "World" if "World" in regions else regions[0]

    return commodity, region


def fig_sankey_simple(region, year, unit="kt", sankey_subtype=None, mode="local"):
    """Builds a simplified Sankey diagram for a given region and year."""

    if not sankey_subtype:
        raise ValueError("sankey_subtype is required")

    _, preprocessed_dir = _mode_dirs(sankey_subtype, mode=mode)
    preprocessed_data_path = preprocessed_dir.joinpath(f"{region}_{year}.pkl.lzma")

    with lzma.open(preprocessed_data_path, "rb") as f:
        preprocessed_data = pickle.load(f)

    sankey = preprocessed_data["sankey_cap"] if unit == "t/cap" else preprocessed_data["sankey"]
    layout = preprocessed_data["layout"]
    arrows_and_labels = preprocessed_data["arrows_and_labels"]

    for ann in arrows_and_labels.get("annotations", []):
        if "Nationality of mine owners" in ann.get("text", ""):
            ann["x"] = min(1, ann.get("x", 0) + 0.03)

    sankey["link"]["color"] = np.array([_normalize_color(c) for c in sankey["link"]["color"]])

    fig = go.Figure(sankey)
    fig.update_layout(**layout)
    fig.update_layout(
        shapes=arrows_and_labels["shapes"], annotations=arrows_and_labels["annotations"]
    )

    legend_colors = ["white"] + list(colors[:9])
    legend_names = [
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

    fig.add_traces(create_legend(legend_colors, legend_names))

    fig.update_layout(showlegend=True)
    _apply_figure_theme(fig, legend_y=-0.08, height=620)

    return fig


def create_simple_ownership_page(prefix, mode, title):
    mode_key = mode.lower()
    if mode_key == "global":
        valid_tab_ids = {"tab-1"}
    elif mode_key == "local":
        valid_tab_ids = {"tab-2"}
    else:
        valid_tab_ids = set()

    commodities = _available_commodities(mode=mode)
    default_commodity = "Copper ores" if "Copper ores" in commodities else commodities[0]
    default_year = YEAR
    default_regions = _regions_for_commodity(
        mode=mode, commodity=default_commodity, year=default_year
    )
    default_region = "World" if "World" in default_regions else default_regions[0]

    commodity_dropdown = dcc.Dropdown(
        id=f"{prefix}-commodity",
        options=[{"label": commodity, "value": commodity} for commodity in commodities],
        value=default_commodity,
        multi=False,
        clearable=False,
        persistence=True,
        persistence_type="session",
        className="dash-dropdown",
    )
    region_dropdown = dcc.Dropdown(
        id=f"{prefix}-region",
        options=[
            {"label": REGIONS.get(region, region), "value": region}
            for region in default_regions
        ],
        value=default_region,
        multi=False,
        clearable=False,
        persistence=True,
        persistence_type="session",
        className="dash-dropdown",
    )
    year_slider = dcc.Slider(
        id=f"{prefix}-year",
        min=YEAR_MIN,
        max=YEAR_MAX,
        step=1,
        value=default_year,
        marks={str(year): str(year) for year in range(YEAR_MIN, YEAR_MAX + 1, 2)},
        tooltip={"placement": "bottom", "always_visible": False},
        persistence=True,
        persistence_type="session",
        className="themed-slider",
    )
    try:
        initial_figure = fig_sankey_simple(
            region=default_region,
            year=default_year,
            unit="kt",
            sankey_subtype=default_commodity,
            mode=mode,
        )
    except FileNotFoundError:
        initial_figure = _empty_figure("No preprocessed Sankey file found for this selection.")
    layout = dbc.Container(
        [
            html.Section(
                [
                    html.H2(title, className="page-head-title"),
                    html.P(
                        "Inspect how mine ownership nationality maps to extraction and final "
                        "consumption flows for each region-year selection.",
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
                                        commodity_dropdown,
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
                                        region_dropdown,
                                    ],
                                    className="control-field",
                                ),
                                xs=12,
                                md=4,
                            ),
                            dbc.Col(
                                html.Div(
                                    [
                                        html.P("Data Year", className="control-label"),
                                        html.Div(
                                            id=f"{prefix}-year-label",
                                            className="control-value-label",
                                        ),
                                    ],
                                    className="control-field",
                                ),
                                xs=12,
                                md=4,
                            ),
                        ],
                        class_name="g-3",
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                html.Div(
                                    [
                                        html.P("Timeline", className="control-label"),
                                        year_slider,
                                    ],
                                    className="control-field",
                                ),
                                width=12,
                            )
                        ],
                        class_name="g-3 mt-1",
                    ),
                ],
                className="app-card controls-card reveal",
            ),
            html.Div(
                [
                    dcc.Graph(
                        id=f"{prefix}-graph",
                        responsive=True,
                        figure=initial_figure,
                        className="themed-graph",
                        style={"height": "620px", "width": "100%"},
                    )
                ],
                className="app-card graph-card reveal",
            ),
            html.Div(
                dcc.Markdown(
                    "You may **use your browser's zoom function for better readability**."
                ),
                className="app-card info-card slim-card reveal",
            ),
        ],
        fluid=True,
        className="page-frame page-simple-ownership",
    )

    @app.callback(
        Output(f"{prefix}-region-memory", "data", allow_duplicate=True),
        Input(f"{prefix}-region", "value"),
        prevent_initial_call=True,
    )
    def remember_region(region):
        return region

    @app.callback(
        Output(f"{prefix}-commodity", "value"),
        Output(f"{prefix}-year", "value"),
        Output(f"{prefix}-region-memory", "data", allow_duplicate=True),
        Output(f"{prefix}-region", "value"),
        Input("tabs", "active_tab"),
        State("shared-commodity-store", "data"),
        State("shared-year-store", "data"),
        State("shared-region-store", "data"),
        prevent_initial_call=True,
    )
    def apply_shared_selection(active_tab, shared_commodity, shared_year, shared_region):
        if active_tab not in valid_tab_ids:
            raise PreventUpdate

        commodity = (
            shared_commodity if shared_commodity in commodities else default_commodity
        )
        try:
            year = int(shared_year)
        except (TypeError, ValueError):
            year = default_year
        year = min(max(year, YEAR_MIN), YEAR_MAX)

        valid_regions = _regions_for_commodity(mode=mode, commodity=commodity, year=year)
        if valid_regions:
            region = (
                shared_region
                if shared_region in valid_regions
                else ("World" if "World" in valid_regions else valid_regions[0])
            )
        else:
            region = default_region

        return commodity, year, region, region

    @app.callback(
        Output("shared-commodity-store", "data", allow_duplicate=True),
        Output("shared-year-store", "data", allow_duplicate=True),
        Output("shared-region-store", "data", allow_duplicate=True),
        Input(f"{prefix}-commodity", "value"),
        Input(f"{prefix}-year", "value"),
        Input(f"{prefix}-region", "value"),
        prevent_initial_call=True,
    )
    def persist_shared_selection(commodity, year, region):
        triggered = callback_context.triggered_id

        commodity_out = no_update
        year_out = no_update
        region_out = no_update

        if triggered == f"{prefix}-commodity":
            commodity_out = (
                commodity if commodity in commodities else default_commodity
            )
        elif triggered == f"{prefix}-year":
            try:
                year_out = int(year)
            except (TypeError, ValueError):
                year_out = default_year
            year_out = min(max(year_out, YEAR_MIN), YEAR_MAX)
        elif triggered == f"{prefix}-region":
            region_out = region if region in REGIONS else default_region

        return commodity_out, year_out, region_out

    # ---------------------------------------------------------------------------
    # Dash 4.x fix: The original two-Output callback
    #   Output(prefix-region, "options") + Output(prefix-region, "value")
    # causes IndexError: list index out of range in _prepare_grouping / map_grouping
    # when the callback fires as an initial callback for dynamically-injected tab
    # content, because the Dash 4.x renderer can send the "outputs" field as a
    # single dict instead of a list in that scenario.
    #
    # Fix: both outputs now target dcc.Store components that live in the STATIC
    # layout (index.py), so they are always present when the callback fires.
    # Two lightweight single-Output callbacks then forward the stored values to
    # the actual dropdown components in the dynamic content.
    # ---------------------------------------------------------------------------

    @app.callback(
        Output(f"{prefix}-region-options-store", "data"),
        Output(f"{prefix}-resolved-region-store", "data"),
        Input(f"{prefix}-commodity", "value"),
        Input(f"{prefix}-year", "value"),
        State(f"{prefix}-region-memory", "data"),
    )
    def update_region_stores(commodity, year, remembered_region):
        """Compute options and resolved region; write to static Stores."""
        if commodity not in commodities:
            commodity = default_commodity
        if year is None:
            year = default_year
        regions = _regions_for_commodity(mode=mode, commodity=commodity, year=year)
        options = [
            {"label": REGIONS.get(r, r), "value": r} for r in regions
        ]
        if remembered_region in regions:
            selected_region = remembered_region
        else:
            selected_region = "World" if "World" in regions else regions[0]
        return options, selected_region

    @app.callback(
        Output(f"{prefix}-region", "options"),
        Input(f"{prefix}-region-options-store", "data"),
    )
    def apply_region_options(options):
        """Forward options from static Store to the dynamic dropdown."""
        return options if options else []

    @app.callback(
        Output(f"{prefix}-region", "value"),
        Input(f"{prefix}-resolved-region-store", "data"),
    )
    def apply_resolved_region(region):
        """Forward resolved region from static Store to the dynamic dropdown."""
        return region

    @app.callback(
        Output(f"{prefix}-year-label", "children"),
        Input(f"{prefix}-year", "value"),
    )
    def update_year_label(year):
        selected_year = default_year if year is None else int(year)
        return f"Data year: {selected_year}"

    @app.callback(
        Output(f"{prefix}-graph", "figure"),
        Input(f"{prefix}-commodity", "value"),
        Input(f"{prefix}-region", "value"),
        Input(f"{prefix}-year", "value"),
    )
    def update_figure(commodity, region, year):
        if commodity not in commodities:
            commodity = default_commodity
        if year is None:
            year = default_year
        regions = _regions_for_commodity(mode=mode, commodity=commodity, year=year)
        if region not in regions:
            region = "World" if "World" in regions else (regions[0] if regions else None)
        if not commodity or not region:
            return _empty_figure("No dataset found for this tab.")

        try:
            return fig_sankey_simple(
                region=region,
                year=int(year),
                unit="kt",
                sankey_subtype=commodity,
                mode=mode,
            )
        except FileNotFoundError:
            return _empty_figure("No preprocessed Sankey file found for this selection.")

    return layout
