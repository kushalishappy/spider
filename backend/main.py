from typing import Dict, Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.graph import orca_graph


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="ORCA - Ocean Reasoning & Coastal Advisor",
    description=(
        "Multi-agent marine advisory backend using "
        "NOAA OISST and Copernicus Marine chlorophyll data."
    ),
    version="1.0.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# REQUEST MODEL
# ============================================================

class QueryPayload(BaseModel):
    query: str = Field(
        ...,
        min_length=1,
        description="Natural-language marine question",
    )

    bbox: Dict[str, float] = Field(
        ...,
        description=(
            "Geographic bounding box containing "
            "lat_min, lat_max, lon_min and lon_max"
        ),
    )


# ============================================================
# VALIDATE BBOX
# ============================================================

def validate_bbox(bbox: Dict[str, float]) -> None:
    required = [
        "lat_min",
        "lat_max",
        "lon_min",
        "lon_max",
    ]

    missing = [
        key for key in required
        if key not in bbox
    ]

    if missing:
        raise ValueError(
            "Missing bbox fields: "
            + ", ".join(missing)
        )

    if bbox["lat_min"] >= bbox["lat_max"]:
        raise ValueError(
            "lat_min must be smaller than lat_max"
        )

    if bbox["lon_min"] >= bbox["lon_max"]:
        raise ValueError(
            "lon_min must be smaller than lon_max"
        )

    if not -90 <= bbox["lat_min"] <= 90:
        raise ValueError("lat_min must be between -90 and 90")

    if not -90 <= bbox["lat_max"] <= 90:
        raise ValueError("lat_max must be between -90 and 90")

    if not -180 <= bbox["lon_min"] <= 180:
        raise ValueError(
            "lon_min must be between -180 and 180"
        )

    if not -180 <= bbox["lon_max"] <= 180:
        raise ValueError(
            "lon_max must be between -180 and 180"
        )


# ============================================================
# HEALTH
# ============================================================

@app.get("/")
def root():
    return {
        "status": "online",
        "project": "ORCA",
        "name": "Ocean Reasoning & Coastal Advisor",
        "version": "1.0.0",
    }


@app.get("/api/health")
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
        },
    }


# ============================================================
# CHAT ENDPOINT
# ============================================================

@app.post("/api/chat")
async def chat(payload: QueryPayload):

    try:
        validate_bbox(payload.bbox)

        # A unique thread ID lets LangGraph's checkpointer
        # safely handle each request.
        thread_id = (
            f"orca-"
            f"{payload.bbox['lat_min']}-"
            f"{payload.bbox['lat_max']}-"
            f"{payload.bbox['lon_min']}-"
            f"{payload.bbox['lon_max']}"
        )

        result = await orca_graph.ainvoke(
            {
                "user_query": payload.query,
                "location_bbox": payload.bbox,
                "agent_trace": [],
            },
            config={
                "configurable": {
                    "thread_id": thread_id
                }
            },
        )

        return {
            "status": "success",

            # User question
            "query": payload.query,

            # Routing information
            "requested_agents": result.get(
                "requested_agents",
                [],
            ),

            "requested_capabilities": result.get(
                "requested_capabilities",
                [],
            ),

            # Final answer
            "advisory": result.get(
                "advisory_output",
                "",
            ),

            "deterministic_advisory": result.get(
                "deterministic_advisory",
                "",
            ),

            "llm_output": result.get(
                "llm_output",
                "",
            ),

            # Specialist evidence
            "results": {
                "sst": result.get("sst_summary"),
                "sst_forecast": result.get(
                    "sst_forecast"
                ),
                "chlorophyll": result.get(
                    "chl_summary"
                ),
            },

            # Backwards-compatible fields
            "sst_summary": result.get(
                "sst_summary"
            ),

            "sst_forecast": result.get(
                "sst_forecast"
            ),

            "chl_summary": result.get(
                "chl_summary"
            ),

            # Explainable agent execution
            "agent_trace": result.get(
                "agent_trace",
                [],
            ),

            # Data sources
            "sources": [
                "NOAA OISST",
                "Copernicus Marine",
            ],
        }

    except ValueError as exc:
        return {
            "status": "error",
            "error_type": "validation_error",
            "message": str(exc),
        }

    except Exception as exc:
        return {
            "status": "error",
            "error_type": "backend_error",
            "message": str(exc),
        }