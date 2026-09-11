from typing import Dict, Any

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver

from backend.state import ORCAState
from tools.sst_engine import get_sst_timeseries
from tools.sst_forecast import get_sst_trend_forecast
from bio_tools import get_chlorophyll_bbox

try:
    from llm_advisor import generate_llm_advisory
except ImportError:
    generate_llm_advisory = None


# ============================================================
# KEYWORD GROUPS
# ============================================================

SST_KEYWORDS = [
    "sst",
    "sea surface temperature",
    "sea temperature",
    "temperature",
    "thermal",
    "heat",
    "heat stress",
    "warming",
    "warming trend",
    "cooling",
    "anomaly",
]

CHL_KEYWORDS = [
    "chlorophyll",
    "chlorophyll-a",
    "chlorophyll a",
    "chlor-a",
    "chl",
    "algae",
    "algal",
    "phytoplankton",
    "bloom",
    "bloom risk",
]

COMBINED_KEYWORDS = [
    "hab",
    "harmful algal bloom",
    "harmful algae",
    "algal bloom",
    "algae growth",
    "algae growth conditions",
    "bloom conditions",
    "bloom risk",
    "favorable for algae",
    "favourable for algae",
    "favorable conditions for algae",
    "favourable conditions for algae",
    "marine bloom",
]

FORECAST_KEYWORDS = [
    "forecast",
    "next week",
    "next 7 days",
    "next seven days",
    "coming week",
    "coming days",
    "future",
    "outlook",
    "trend",
    "warming trend",
    "cooling trend",
]


# ============================================================
# HELPERS
# ============================================================

def contains_any(text: str, keywords: list[str]) -> bool:
    text = text.lower()
    return any(keyword in text for keyword in keywords)


def add_trace(
    state: ORCAState,
    agent: str,
    status: str,
    progress: int,
) -> list[dict[str, Any]]:
    trace = list(state.get("agent_trace", []))

    trace.append(
        {
            "agent": agent,
            "status": status,
            "progress": progress,
        }
    )

    return trace


def bbox_values(state: ORCAState):
    bbox = state["location_bbox"]

    return (
        bbox["lat_min"],
        bbox["lat_max"],
        bbox["lon_min"],
        bbox["lon_max"],
    )


# ============================================================
# ROUTER AGENT
# ============================================================

def router_node(state: ORCAState) -> ORCAState:
    query = state.get("user_query", "").lower()

    needs_sst = contains_any(query, SST_KEYWORDS)
    needs_chl = contains_any(query, CHL_KEYWORDS)
    needs_combined = contains_any(query, COMBINED_KEYWORDS)
    needs_forecast = contains_any(query, FORECAST_KEYWORDS)

    # HAB / algae-growth questions need both evidence streams.
    if needs_combined:
        needs_sst = True
        needs_chl = True

    # Any forecast/outlook question requires SST trend analysis.
    if needs_forecast:
        needs_sst = True

    # Safe default for unknown scientific questions.
    if not needs_sst and not needs_chl:
        needs_sst = True
        needs_chl = True

    requested_agents = []

    if needs_sst:
        requested_agents.append("sst")

    if needs_chl:
        requested_agents.append("chlorophyll")

    requested_capabilities = []

    if needs_forecast:
        requested_capabilities.append("sst_forecast")

    if needs_combined:
        requested_capabilities.append("combined_hab_screening")

    new_state = dict(state)

    new_state["requested_agents"] = requested_agents
    new_state["requested_capabilities"] = requested_capabilities
    new_state["agent_trace"] = add_trace(
        state,
        "Router Agent",
        "Completed",
        20,
    )

    return new_state


# ============================================================
# SST SPECIALIST
# ============================================================

def sst_specialist_node(state: ORCAState) -> ORCAState:
    min_lat, max_lat, min_lon, max_lon = bbox_values(state)

    try:
        result = get_sst_timeseries(
            min_lat,
            max_lat,
            min_lon,
            max_lon,
        )
    except Exception as exc:
        result = {
            "status": "error",
            "source": "NOAA OISST",
            "error": str(exc),
        }

    new_state = dict(state)
    new_state["sst_summary"] = result
    new_state["agent_trace"] = add_trace(
        state,
        "SST Specialist (Member 2)",
        "Completed",
        50,
    )

    return new_state


# ============================================================
# SST FORECAST SPECIALIST
# ============================================================

def sst_forecast_node(state: ORCAState) -> ORCAState:
    min_lat, max_lat, min_lon, max_lon = bbox_values(state)

    try:
        result = get_sst_trend_forecast(
            min_lat,
            max_lat,
            min_lon,
            max_lon,
            forecast_days=7,
            lookback_days=14,
        )
    except Exception as exc:
        result = {
            "status": "error",
            "source": "NOAA OISST",
            "error": str(exc),
        }

    new_state = dict(state)
    new_state["sst_forecast"] = result
    new_state["agent_trace"] = add_trace(
        state,
        "SST Forecast Specialist (Member 2)",
        "Completed",
        65,
    )

    return new_state


# ============================================================
# CHLOROPHYLL SPECIALIST
# ============================================================

def chl_specialist_node(state: ORCAState) -> ORCAState:
    min_lat, max_lat, min_lon, max_lon = bbox_values(state)

    try:
        result = get_chlorophyll_bbox(
            min_lat,
            max_lat,
            min_lon,
            max_lon,
        )
    except Exception as exc:
        result = {
            "status": "error",
            "source": "Copernicus Marine",
            "error": str(exc),
        }

    new_state = dict(state)
    new_state["chl_summary"] = result
    new_state["agent_trace"] = add_trace(
        state,
        "Chlorophyll Specialist (Member 3)",
        "Completed",
        80,
    )

    return new_state


# ============================================================
# DETERMINISTIC ADVISORY
# ============================================================

def build_deterministic_advisory(state: ORCAState) -> str:
    sst = state.get("sst_summary")
    forecast = state.get("sst_forecast")
    chl = state.get("chl_summary")

    requested_agents = state.get("requested_agents", [])

    lines = ["Marine condition summary:"]

    # --------------------------------------------------------
    # SST
    # --------------------------------------------------------

    if "sst" in requested_agents and sst:
        if sst.get("status") == "success":
            metrics = sst.get("metrics", {})

            avg_sst = metrics.get("average_sst_celsius")
            anomaly = metrics.get("temperature_anomaly_celsius")
            heat_stress = metrics.get("heat_stress_indicator")

            if avg_sst is not None:
                lines.append(
                    f"- Average SST: {avg_sst} C"
                )

            if anomaly is not None:
                lines.append(
                    f"- SST anomaly: {anomaly} C"
                )
            else:
                lines.append(
                    "- SST anomaly: Not available"
                )

            if heat_stress is not None:
                lines.append(
                    f"- Heat-stress indicator: {heat_stress}"
                )
            else:
                lines.append(
                    "- Heat-stress indicator: Not available"
                )

    # --------------------------------------------------------
    # SST FORECAST
    # --------------------------------------------------------

    if forecast:
        if forecast.get("status") == "success":
            trend = forecast.get("trend", {})
            outlook = forecast.get("outlook", {})

            direction = trend.get("direction")
            weekly_change = trend.get("celsius_per_week")
            first_day = outlook.get("first_day_sst_celsius")
            last_day = outlook.get("last_day_sst_celsius")
            change = outlook.get("change_over_outlook_celsius")

            lines.append("")
            lines.append("7-day SST outlook:")

            if direction:
                lines.append(
                    f"- Trend direction: {direction}"
                )

            if weekly_change is not None:
                lines.append(
                    f"- Estimated weekly change: "
                    f"{weekly_change} C"
                )

            if first_day is not None:
                lines.append(
                    f"- First forecast day: "
                    f"{first_day} C"
                )

            if last_day is not None:
                lines.append(
                    f"- Last forecast day: "
                    f"{last_day} C"
                )

            if change is not None:
                lines.append(
                    f"- Change across outlook: "
                    f"{change} C"
                )

            lines.append(
                "- This is a trend-based project outlook, "
                "not an operational ocean forecast."
            )

    # --------------------------------------------------------
    # CHLOROPHYLL
    # --------------------------------------------------------

    if "chlorophyll" in requested_agents and chl:
        if chl.get("status") == "success":
            chl_value = chl.get("chlor_a_mg_m3")
            classification = chl.get("bloom_risk")

            if chl_value is not None:
                lines.append("")
                lines.append(
                    f"- Chlorophyll-a: {chl_value} mg/m3"
                )

            if classification:
                lines.append(
                    f"- Chlorophyll classification: "
                    f"{classification}"
                )

    # --------------------------------------------------------
    # COMBINED INTERPRETATION
    # --------------------------------------------------------

    capabilities = state.get(
        "requested_capabilities",
        [],
    )

    if "combined_hab_screening" in capabilities:
        lines.append("")
        lines.append("Combined screening interpretation:")

        chl_classification = None

        if chl:
            chl_classification = chl.get("bloom_risk")

        if chl_classification:
            classification_text = chl_classification.lower()

            elevated = (
                "elevated" in classification_text
                or "high" in classification_text
                or "risk" in classification_text
            )

            if elevated:
                lines.append(
                    "The available temperature and chlorophyll "
                    "indicators warrant increased monitoring."
                )
                lines.append(
                    "This is a screening signal only and does "
                    "not confirm a harmful algal bloom."
                )
            else:
                lines.append(
                    "The retrieved SST and chlorophyll indicators "
                    "do not currently show a combined elevated-risk "
                    "signal."
                )
        else:
            lines.append(
                "A combined HAB screening interpretation could "
                "not be completed because chlorophyll evidence "
                "was unavailable."
            )

    # --------------------------------------------------------
    # DATA SOURCE STATEMENT
    # --------------------------------------------------------

    sources = []

    if "sst" in requested_agents:
        sources.append("NOAA OISST")

    if "chlorophyll" in requested_agents:
        sources.append("Copernicus Marine")

    if sources:
        lines.append("")
        lines.append(
            "Data sources used: " + ", ".join(sources) + "."
        )

    lines.append("")
    lines.append(
        "This advisory is based only on the retrieved "
        "specialist evidence."
    )

    return "\n".join(lines)


# ============================================================
# ADVISORY AGENT
# ============================================================

def advisory_node(state: ORCAState) -> ORCAState:
    deterministic = build_deterministic_advisory(state)

    new_state = dict(state)

    new_state["deterministic_advisory"] = deterministic
    new_state["advisory_output"] = deterministic

    # Try LLM synthesis if available.
    if generate_llm_advisory is not None:
        try:
            llm_result = generate_llm_advisory(
                user_query=state.get("user_query", ""),
                sst_summary=state.get("sst_summary"),
                sst_forecast=state.get("sst_forecast"),
                chl_summary=state.get("chl_summary"),
            )

            if isinstance(llm_result, dict):
                new_state["llm_output"] = llm_result.get(
                    "output",
                    "",
                )

                if (
                    llm_result.get("status") == "success"
                    and llm_result.get("output")
                ):
                    new_state["advisory_output"] = (
                        llm_result["output"]
                    )

        except Exception as exc:
            new_state["llm_output"] = (
                f"LLM advisory unavailable: {exc}"
            )

    new_state["agent_trace"] = add_trace(
        state,
        "Marine Advisory Agent",
        "Synthesized",
        100,
    )

    return new_state


# ============================================================
# ROUTING FUNCTIONS
# ============================================================

def route_after_router(state: ORCAState) -> str:
    requested = state.get("requested_agents", [])

    if "sst" in requested:
        return "sst"

    if "chlorophyll" in requested:
        return "chlorophyll"

    return "advisory"


def route_after_sst(state: ORCAState) -> str:
    capabilities = state.get(
        "requested_capabilities",
        [],
    )

    requested = state.get(
        "requested_agents",
        [],
    )

    if "sst_forecast" in capabilities:
        return "forecast"

    if "chlorophyll" in requested:
        return "chlorophyll"

    return "advisory"


def route_after_forecast(state: ORCAState) -> str:
    requested = state.get(
        "requested_agents",
        [],
    )

    if "chlorophyll" in requested:
        return "chlorophyll"

    return "advisory"


# ============================================================
# BUILD LANGGRAPH
# ============================================================

builder = StateGraph(ORCAState)

builder.add_node("router", router_node)
builder.add_node("sst", sst_specialist_node)
builder.add_node("forecast", sst_forecast_node)
builder.add_node("chlorophyll", chl_specialist_node)
builder.add_node("advisory", advisory_node)

builder.set_entry_point("router")

builder.add_conditional_edges(
    "router",
    route_after_router,
    {
        "sst": "sst",
        "chlorophyll": "chlorophyll",
        "advisory": "advisory",
    },
)

builder.add_conditional_edges(
    "sst",
    route_after_sst,
    {
        "forecast": "forecast",
        "chlorophyll": "chlorophyll",
        "advisory": "advisory",
    },
)

builder.add_conditional_edges(
    "forecast",
    route_after_forecast,
    {
        "chlorophyll": "chlorophyll",
        "advisory": "advisory",
    },
)

builder.add_edge("chlorophyll", "advisory")
builder.add_edge("advisory", END)

memory = InMemorySaver()

orca_graph = builder.compile(
    checkpointer=memory
)