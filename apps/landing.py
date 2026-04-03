import json
import re
from pathlib import Path

import dash_bootstrap_components as dbc
import plotly.graph_objs as go
from dash import dcc, html

from apps import app_sankey_commodity as commodity_view
from apps import app_sankey_ownership_explorer as ownership_view

DATA_PATH = Path(__file__).parent.joinpath("data").resolve()
PREPROCESSED_ROOT = DATA_PATH.joinpath("Results", "Sankey_preprocessed")
EXAMPLE_COMMODITY = "Copper ores"
EXAMPLE_REGIONS_PREFERRED = ("CHL", "AUS", "CHN", "GBR", "USA", "ZMB", "World")

with open(DATA_PATH.joinpath("dictreg.json"), encoding="utf-8") as f:
    REGIONS = json.loads(f.read())
REGIONS.pop("DYE", None)
REGIONS.pop("SDS", None)
REGIONS["World"] = "World"


def _base_font():
    return "Avenir Next, Segoe UI Variable Text, Trebuchet MS, Tahoma, sans-serif"


def _message_figure(title, message):
    fig = go.Figure()
    fig.update_layout(
        title=title,
        height=420,
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
                "font": {"family": _base_font(), "size": 14, "color": "#5f4c3b"},
            }
        ],
        font={"family": _base_font(), "size": 12, "color": "#44372b"},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin={"l": 20, "r": 20, "t": 56, "b": 20},
    )
    return fig


def _normalize_figure(fig, title, height=560):
    fig.update_layout(
        title=title,
        height=height,
        margin={"l": 20, "r": 20, "t": 56, "b": 80},
        font={"family": _base_font(), "size": 12, "color": "#44372b"},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def _safe_figure(title, builder, height=560):
    try:
        fig = builder()
    except Exception as exc:
        return _message_figure(title, f"Example unavailable in this environment: {type(exc).__name__}")
    return _normalize_figure(fig, title=title, height=height)


def _toy_width_figure():
    fig = go.Figure(
        go.Sankey(
            node={
                "label": ["Mine A", "Mine B", "Smelter"],
                "pad": 22,
                "thickness": 18,
                "color": "#1e2638",
            },
            link={
                "source": [0, 1],
                "target": [2, 2],
                "value": [9, 3],
                "color": ["#4C72B0", "#CCB974"],
            },
        )
    )
    return _normalize_figure(fig, "Toy diagram 1: Width equals quantity", height=420)


def _toy_filter_figure(global_view=True):
    labels = [
        "Extraction:<br>other regions",
        "Extraction:<br>focus region",
        "Consumption:<br>rest of world",
        "Consumption:<br>focus region",
    ]
    flows = [
        # source, target, value, color
        (0, 2, 18, "rgba(85,168,104,0.78)"),
        (0, 3, 4, "rgba(85,168,104,0.78)"),
        (1, 2, 10, "rgba(76,114,176,0.78)"),
        (1, 3, 6, "rgba(76,114,176,0.78)"),
    ]

    if global_view:
        active_flows = flows
        title = "Toy diagram 2a: Global context"
    else:
        # Keep only links connected to the focus region (source or target).
        active_flows = [flow for flow in flows if flow[0] == 1 or flow[1] == 3]
        title = "Toy diagram 2b: Isolate region flows"

    source, target, value, color = zip(*active_flows)

    fig = go.Figure(
        go.Sankey(
            arrangement="fixed",
            node={
                "label": labels,
                "x": [0.01, 0.01, 0.99, 0.99],
                "y": [0.16, 0.72, 0.16, 0.72],
                "pad": 24,
                "thickness": 18,
                "color": "#1e2638",
                "line": {"color": "rgba(255,255,255,0.85)", "width": 1},
                "hovertemplate": "%{label}<extra></extra>",
            },
            link={
                "source": source,
                "target": target,
                "value": value,
                "color": color,
                "line": {"color": "rgba(255,255,255,0.35)", "width": 0.5},
                "hovertemplate": "%{source.label} -> %{target.label}<br>Flow: %{value}<extra></extra>",
            },
        )
    )
    return _normalize_figure(fig, title, height=420)


def _toy_ownership_figure():
    fig = go.Figure(
        go.Sankey(
            node={
                "label": [
                    "Owner nationality",
                    "Extraction region",
                    "Consumption region",
                ],
                "pad": 22,
                "thickness": 18,
                "color": "#1e2638",
            },
            link={
                "source": [0, 1],
                "target": [1, 2],
                "value": [8, 8],
                "color": ["#C44E52", "#4C72B0"],
            },
        )
    )
    return _normalize_figure(fig, "Toy diagram 3: Ownership layer", height=420)


def _list_cases(folder):
    out = set()
    if not folder.exists():
        return out
    for file_path in folder.glob("*.pkl.lzma"):
        match = re.match(r"([^_]+)_(\d{4})\.pkl\.lzma$", file_path.name)
        if match:
            out.add((match.group(1), int(match.group(2))))
    return out


def _pick_guided_example():
    cases = [
        _list_cases(PREPROCESSED_ROOT.joinpath("All_commodities_simple global")),
        _list_cases(PREPROCESSED_ROOT.joinpath("All_commodities_simple local")),
        _list_cases(PREPROCESSED_ROOT.joinpath("All commodities")),
        _list_cases(PREPROCESSED_ROOT.joinpath("Ownership simple global", EXAMPLE_COMMODITY)),
        _list_cases(PREPROCESSED_ROOT.joinpath("Ownership simple local", EXAMPLE_COMMODITY)),
        _list_cases(PREPROCESSED_ROOT.joinpath("Commodity all ownership", EXAMPLE_COMMODITY)),
    ]

    if not all(cases):
        return "World", 2002

    common = set.intersection(*cases)
    if not common:
        return "World", 2002

    regions = sorted({region for region, _ in common})
    region = None
    for preferred in EXAMPLE_REGIONS_PREFERRED:
        if preferred in regions:
            region = preferred
            break
    if region is None:
        region = regions[0]

    year = max(y for r, y in common if r == region)
    return region, year


def _guided_case_reason(region_code):
    if region_code == "CHL":
        return (
            "Chile is used here because it has complete coverage across all guided views and "
            "typically shows a strong contrast between global context and isolate-region filtering."
        )
    if region_code == "AUS":
        return (
            "Australia is used here because it has complete coverage across all guided views and "
            "typically shows a stronger contrast between global context and isolate-region filtering."
        )
    if region_code == "CHN":
        return (
            "China is used here because it has complete coverage across all guided views and "
            "typically shows substantial inbound and outbound links, which makes structural differences easy to read."
        )
    return (
        "This region-year case is used because it has complete coverage across all guided views, "
        "so the diagrams can be compared step-by-step without changing data availability conditions."
    )


def _build_real_examples(region, year):
    return {
        "footprint_global_1step": _safe_figure(
            "Step 1: Footprint Explorer | Global view, all commodities, one consumption stage",
            lambda: commodity_view._build_figure(
                scope="global",
                detail="summary",
                region=region,
                year=year,
                unit="kTonnes",
                commodity="All commodities",
            ),
        ),
        "footprint_local_1step": _safe_figure(
            "Step 2: Footprint Explorer | Region-focused view, all commodities, one consumption stage",
            lambda: commodity_view._build_figure(
                scope="local",
                detail="summary",
                region=region,
                year=year,
                unit="kTonnes",
                commodity="All commodities",
            ),
        ),
        "footprint_local_1step_commodity": _safe_figure(
            f"Step 3: Footprint Explorer | Region-focused view, {EXAMPLE_COMMODITY}, one consumption stage",
            lambda: commodity_view._build_figure(
                scope="local",
                detail="summary",
                region=region,
                year=year,
                unit="kTonnes",
                commodity=EXAMPLE_COMMODITY,
            ),
        ),
        "footprint_local_3step": _safe_figure(
            f"Step 4: Footprint Explorer | Region-focused view, {EXAMPLE_COMMODITY}, three consumption stages",
            lambda: commodity_view._build_figure(
                scope="local",
                detail="detailed",
                region=region,
                year=year,
                unit="kTonnes",
                commodity=EXAMPLE_COMMODITY,
            ),
        ),
        "ownership_global_1step": _safe_figure(
            f"Step 5: Ownership Explorer | Add owner layer, global view, one consumption stage ({EXAMPLE_COMMODITY})",
            lambda: ownership_view._build_figure(
                scope="global",
                detail="summary",
                commodity=EXAMPLE_COMMODITY,
                region=region,
                year=year,
                unit="kTonnes",
            ),
        ),
        "ownership_local_1step": _safe_figure(
            f"Step 6: Ownership Explorer | Add owner layer, region-focused view, one consumption stage ({EXAMPLE_COMMODITY})",
            lambda: ownership_view._build_figure(
                scope="local",
                detail="summary",
                commodity=EXAMPLE_COMMODITY,
                region=region,
                year=year,
                unit="kTonnes",
            ),
        ),
        "ownership_local_3step": _safe_figure(
            f"Step 7: Ownership Explorer | Add owner layer, region-focused view, three consumption stages ({EXAMPLE_COMMODITY})",
            lambda: ownership_view._build_figure(
                scope="local",
                detail="detailed",
                commodity=EXAMPLE_COMMODITY,
                region=region,
                year=year,
                unit="kTonnes",
            ),
        ),
    }


def _step_block(step_id, markdown_text, figure):
    return html.Div(
        [
            dcc.Markdown(markdown_text),
            dcc.Graph(
                id=step_id,
                figure=figure,
                responsive=True,
                className="themed-graph",
                style={"height": "560px", "width": "100%"},
            ),
        ],
        className="app-card info-card graph-card reveal",
    )


def _tab_map_card(title, body):
    return dbc.Col(
        html.Div([html.H4(title), html.P(body)], className="tab-map-item"),
        xs=12,
        lg=4,
    )


def _definition_card(title, body):
    return dbc.Col(
        html.Div([html.H4(title), html.P(body)], className="definition-card"),
        xs=12,
        md=4,
    )


GUIDE_REGION, GUIDE_YEAR = _pick_guided_example()
GUIDE_REGION_LABEL = REGIONS.get(GUIDE_REGION, GUIDE_REGION)
GUIDE_REASON = _guided_case_reason(GUIDE_REGION)
EXAMPLE_FIGURES = _build_real_examples(GUIDE_REGION, GUIDE_YEAR)
TOY_WIDTH_FIGURE = _toy_width_figure()
TOY_GLOBAL_FIGURE = _toy_filter_figure(global_view=True)
TOY_LOCAL_FIGURE = _toy_filter_figure(global_view=False)
TOY_OWNERSHIP_FIGURE = _toy_ownership_figure()

layout = dbc.Container(
    [
        html.Section(
            [
                html.H2(
                    "Start here: Scope, definitions, and reading guide",
                    className="page-head-title",
                ),
                html.P(
                    "Conceptual overview and step-by-step interpretation of the Sankey views.",
                    className="page-head-subtitle",
                ),
            ],
            className="page-head reveal",
        ),
        html.Div(
            dcc.Markdown(
                """
## Visualisation objective

These Sankey diagrams are designed to represent how metal ores move through the global economy,
from extraction to downstream final demand.

The objective is to compare, for each region and year:

- extraction-linked pathways,
- consumption-linked pathways,
- and, when ownership is enabled, control of extraction through mine-owner nationality.
"""
            ),
            className="app-card info-card reveal",
        ),
        html.Div(
            dcc.Markdown(
                """
## Core accounting concepts

PBA means **Production-Based Account** and CBA means **Consumption-Based Account**.

- **Production-based account (PBA):** attributes flows to the region where extraction/production occurs.
- **Consumption-based account (CBA):** attributes flows to the region where final demand is located.
- **Ownership extension:** inserts mine-owner nationality as an additional first stage before extraction.

Plain-language translation:

- PBA answers: "where was the material extracted?"
- CBA answers: "where was the material finally used?"
- Ownership extension answers: "who controls the extraction assets?"

In this app, you can compare these perspectives side-by-side by switching between the Footprint and Ownership tabs.
"""
            ),
            className="app-card info-card reveal",
        ),
        html.Div(
            [
                dcc.Markdown("## What is available on this website"),
                dbc.Row(
                    [
                        _tab_map_card(
                            "Start here",
                            "Conceptual explanation, toy diagrams, and a guided reading sequence.",
                        ),
                        _tab_map_card(
                            "Footprint explorer",
                            "Non-ownership pathways from extraction to consumption (global or isolated region scope).",
                        ),
                        _tab_map_card(
                            "Ownership explorer",
                            "Same pathways with owner nationality added as the first stage.",
                        ),
                    ],
                    class_name="g-3 tab-map-grid",
                ),
            ],
            className="app-card info-card reveal",
        ),
        html.Div(
            [
                dcc.Markdown("## How to read one diagram"),
                dbc.Row(
                    [
                        _definition_card("Node", "A stage in the chain, such as owner nationality, extraction, or consumption."),
                        _definition_card("Link", "A flow connecting two stages."),
                        _definition_card("Width", "Link width is proportional to flow magnitude in that chart."),
                    ],
                    class_name="g-3 definition-grid",
                ),
                dcc.Markdown(
                    """
**Color rule:** colors are assigned at the first stage of the Sankey and are preserved along the chain,
so each colored path can be tracked across downstream stages.
"""
                ),
            ],
            className="app-card info-card reveal",
        ),
        html.Div(
            dcc.Markdown(
                """
## Scope and detail controls used in both explorer tabs

- **Global view:** keeps the full world system visible around the selected region.
- **Region-focused view:** keeps only links connected to the selected region
  (at the owner stage where shown, extraction stage, or final-consumption stage).
- **One consumption stage:** the right side of the chart is shown as one combined final-use block.
- **Three consumption stages:** the right side is split into three stages for more detail.
"""
            ),
            className="app-card info-card reveal",
        ),
        html.Div(
            [
                dcc.Markdown(
                    """
## Toy diagram 1 (explanation)

This toy case illustrates the width rule.
`Mine A -> Smelter` is three times larger than `Mine B -> Smelter`.
"""
                ),
                dcc.Graph(
                    id="landing-toy-width",
                    figure=TOY_WIDTH_FIGURE,
                    responsive=True,
                    className="themed-graph",
                    style={"height": "420px", "width": "100%"},
                ),
            ],
            className="app-card info-card graph-card reveal",
        ),
        html.Div(
            [
                dcc.Markdown(
                    """
## Toy diagram 2 (explanation)

These two diagrams show the difference between global context and isolate region filtering.
The global version keeps all surrounding flows; the isolate version retains only flows connected to the focus region.
In this toy case, isolate mode removes only one link: `Extraction: other regions -> Consumption: rest of world`.
"""
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            dcc.Graph(
                                id="landing-toy-global",
                                figure=TOY_GLOBAL_FIGURE,
                                responsive=True,
                                className="themed-graph",
                                style={"height": "420px", "width": "100%"},
                            ),
                            xs=12,
                            lg=6,
                        ),
                        dbc.Col(
                            dcc.Graph(
                                id="landing-toy-local",
                                figure=TOY_LOCAL_FIGURE,
                                responsive=True,
                                className="themed-graph",
                                style={"height": "420px", "width": "100%"},
                            ),
                            xs=12,
                            lg=6,
                        ),
                    ],
                    class_name="g-3",
                ),
            ],
            className="app-card info-card graph-card reveal",
        ),
        html.Div(
            [
                dcc.Markdown(
                    """
## Toy diagram 3 (explanation)

Ownership mode adds one stage on the left. This stage represents owner nationality of extraction assets.
Downstream stages are then interpreted in the same left-to-right flow logic.
"""
                ),
                dcc.Graph(
                    id="landing-toy-ownership-layer",
                    figure=TOY_OWNERSHIP_FIGURE,
                    responsive=True,
                    className="themed-graph",
                    style={"height": "420px", "width": "100%"},
                ),
            ],
            className="app-card info-card graph-card reveal",
        ),
        html.Div(
            dcc.Markdown(
                f"""
## Guided empirical case used in the seven-step sequence

- Region: `{GUIDE_REGION_LABEL}` (`{GUIDE_REGION}`)
- Year: `{GUIDE_YEAR}`
- Commodity in Step 1 and Step 2: `All commodities`
- Commodity in Step 3 to Step 7: `{EXAMPLE_COMMODITY}`

Why this case:
{GUIDE_REASON}
"""
            ),
            className="app-card info-card reveal",
        ),
        html.Div(
            dcc.Markdown(
                f"""
## Recommended reading sequence

All seven steps use the same selected region and year shown above; each step changes only one setting at a time.

1. Start with a full-world view (`All commodities`).
2. Keep `All commodities`, but switch to a region-focused view.
3. Keep the same region-focused view, and switch commodity to `{EXAMPLE_COMMODITY}`.
4. Keep `{EXAMPLE_COMMODITY}` and split the consumption side into three stages.
5. Add mine-owner information while returning to a full-world view.
6. Keep owner information, and switch back to a region-focused view.
7. Keep owner information and region-focused view, and split consumption into three stages.
"""
            ),
            className="app-card info-card reveal",
        ),
        _step_block(
            "landing-footprint-global-1step",
            f"""
## Step 1. Footprint Explorer: Global view, all commodities, one consumption stage

Selected case for this guide: **{GUIDE_REGION_LABEL} ({GUIDE_REGION}), {GUIDE_YEAR}**.
This first chart keeps the full world visible. It combines all metal commodities, with one extraction stage on the left and one final-consumption stage on the right.
Use this as your baseline: identify the largest links before we apply any filtering.
""",
            EXAMPLE_FIGURES["footprint_global_1step"],
        ),
        _step_block(
            "landing-footprint-local-1step",
            f"""
## Step 2. Footprint Explorer: Region-focused view, all commodities, one consumption stage

Region and year are still **{GUIDE_REGION_LABEL} ({GUIDE_REGION}), {GUIDE_YEAR}**.
Compared with Step 1, the only change is the scope: now we keep only links connected to {GUIDE_REGION_LABEL}
as an extraction location or as a final-consumption location.
This helps you see which part of the global system is directly linked to the selected region.
""",
            EXAMPLE_FIGURES["footprint_local_1step"],
        ),
        _step_block(
            "landing-footprint-local-1step-commodity",
            f"""
## Step 3. Footprint Explorer: Region-focused view, {EXAMPLE_COMMODITY}, one consumption stage

Region and year remain **{GUIDE_REGION_LABEL} ({GUIDE_REGION}), {GUIDE_YEAR}**.
Keep the same region-focused scope as Step 2, and change only one setting: commodity moves from `All commodities`
to `{EXAMPLE_COMMODITY}`.
Compare Step 2 and Step 3 to see what is specific to `{EXAMPLE_COMMODITY}` versus the full mix of commodities.
""",
            EXAMPLE_FIGURES["footprint_local_1step_commodity"],
        ),
        _step_block(
            "landing-footprint-local-3step",
            f"""
## Step 4. Footprint Explorer: Region-focused view, {EXAMPLE_COMMODITY}, three consumption stages

Region and year remain **{GUIDE_REGION_LABEL} ({GUIDE_REGION}), {GUIDE_YEAR}**.
Keep the same commodity and scope as Step 3, and split the right side from one consumption block into three stages.
This gives a more detailed reading of where the same `{EXAMPLE_COMMODITY}` flow ends up.
""",
            EXAMPLE_FIGURES["footprint_local_3step"],
        ),
        _step_block(
            "landing-ownership-global-1step",
            f"""
## Step 5. Ownership Explorer: Add owner layer, global view, one consumption stage ({EXAMPLE_COMMODITY})

Region and year remain **{GUIDE_REGION_LABEL} ({GUIDE_REGION}), {GUIDE_YEAR}**.
Compared with Step 4, we switch to the Ownership Explorer and return to a full-world view with one consumption stage.
The new left-most column shows where mine owners are based, before extraction and final consumption.
""",
            EXAMPLE_FIGURES["ownership_global_1step"],
        ),
        _step_block(
            "landing-ownership-local-1step",
            f"""
## Step 6. Ownership Explorer: Add owner layer, region-focused view, one consumption stage ({EXAMPLE_COMMODITY})

Region and year remain **{GUIDE_REGION_LABEL} ({GUIDE_REGION}), {GUIDE_YEAR}**.
Keep the ownership structure from Step 5, and switch only the scope to region-focused mode.
Now links are kept only when {GUIDE_REGION_LABEL} appears at the owner stage, extraction stage, or final-consumption stage.
""",
            EXAMPLE_FIGURES["ownership_local_1step"],
        ),
        _step_block(
            "landing-ownership-local-3step",
            f"""
## Step 7. Ownership Explorer: Add owner layer, region-focused view, three consumption stages ({EXAMPLE_COMMODITY})

Region and year remain **{GUIDE_REGION_LABEL} ({GUIDE_REGION}), {GUIDE_YEAR}**.
Keep the same settings as Step 6, and split consumption into three stages.
This is the most detailed chart in the sequence, combining owner location, extraction location, and detailed final consumption.
""",
            EXAMPLE_FIGURES["ownership_local_3step"],
        ),
    ],
    fluid=True,
    className="page-frame page-landing",
)
