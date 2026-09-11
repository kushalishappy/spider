from typing import Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from bio_tools import (
    get_chlorophyll_context,
    get_chlorophyll_bbox,
    get_incois_advisory,
    generate_gemini_advisory,
)

from tools.sst_engine import get_sst_timeseries
from backend.graph import orca_graph


app = FastAPI(title="ORCA Biological Advisory API")


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# MODELS
# ============================================================

class MarineRequest(BaseModel):
    lat: float
    lon: float
    min_lat: float
    max_lat: float
    min_lon: float
    max_lon: float
    region: str = "goa"


class QueryPayload(BaseModel):
    query: str
    bbox: Dict[str, float]


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "status": "success",
        "service": "ORCA backend",
        "message": "ORCA Ocean Reasoning & Coastal Advisor API is running."
    }


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "ORCA backend",
        "components": {
            "langgraph": "available",
            "sst_specialist": "available",
            "sst_forecast": "available",
            "chlorophyll_specialist": "available",
            "marine_advisory": "available",
            "gemini": "available"
        }
    }


# ============================================================
# MARINE STATUS
# ============================================================

@app.post("/api/marine-status")
def fetch_marine_status(req: MarineRequest):

    # SST
    sst_data = get_sst_timeseries(
        min_lat=req.min_lat,
        max_lat=req.max_lat,
        min_lon=req.min_lon,
        max_lon=req.max_lon
    )

    # Chlorophyll point
    chlorophyll_data = get_chlorophyll_context(
        req.lat,
        req.lon
    )

    # Chlorophyll regional bbox
    chlorophyll_bbox = get_chlorophyll_bbox(
        req.min_lat,
        req.max_lat,
        req.min_lon,
        req.max_lon
    )

    # Rule-based advisory
    advisory_data = get_incois_advisory(
        sst_summary=sst_data,
        chlorophyll_summary=chlorophyll_bbox,
        forecast_summary=None
    )

    return {
        "status": "success",

        "coordinates": {
            "lat": req.lat,
            "lon": req.lon
        },

        "bounding_box": {
            "min_lat": req.min_lat,
            "max_lat": req.max_lat,
            "min_lon": req.min_lon,
            "max_lon": req.max_lon
        },

        "sst": sst_data,

        "chlorophyll": chlorophyll_data,

        "chlorophyll_bbox": chlorophyll_bbox,

        "incois_advisory": advisory_data
    }


# ============================================================
# CHAT / ORCA AGENT
# ============================================================

@app.post("/api/chat")
async def process_chat(payload: QueryPayload):

    required = [
        "lat_min",
        "lat_max",
        "lon_min",
        "lon_max"
    ]

    if not all(key in payload.bbox for key in required):
        return {
            "status": "error",
            "message": (
                "bbox must contain "
                "lat_min, lat_max, lon_min and lon_max."
            )
        }

    # --------------------------------------------------------
    # LangGraph
    # --------------------------------------------------------

    config = {
        "configurable": {
            "thread_id": "orca-session-1"
        }
    }

    initial_state = {
        "user_query": payload.query,
        "location_bbox": payload.bbox,
        "agent_trace": []
    }

    final_state = await orca_graph.ainvoke(
        initial_state,
        config=config
    )

    # --------------------------------------------------------
    # Extract specialist results
    # --------------------------------------------------------

    sst_summary = final_state.get("sst_summary")
    chl_summary = final_state.get("chl_summary")
    forecast_summary = final_state.get("sst_forecast")
    advisory = final_state.get("advisory_output")

    # --------------------------------------------------------
    # Gemini advisory
    # --------------------------------------------------------

    gemini_advisory = generate_gemini_advisory(
        sst_summary=sst_summary,
        chlorophyll_summary=chl_summary,
        forecast_summary=forecast_summary
    )

    # --------------------------------------------------------
    # Final response
    # --------------------------------------------------------

    return {
        "status": "success",

        "query": payload.query,

        "advisory": advisory,

        "gemini_advisory": gemini_advisory,

        "sst_summary": sst_summary,

        "sst_forecast": forecast_summary,

        "chl_summary": chl_summary,

        "agent_trace": final_state.get("agent_trace", [])
    }