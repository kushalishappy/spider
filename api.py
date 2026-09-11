from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bio_tools import get_chlorophyll_context, get_incois_advisory
from tools.sst_engine import get_sst_timeseries

app = FastAPI(title="ORCA Biological Advisory API")

# Allow the frontend map to request data without CORS blocks
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MarineRequest(BaseModel):
    lat: float
    lon: float
    min_lat: float
    max_lat: float
    min_lon: float
    max_lon: float
    region: str = "goa"

@app.post("/api/marine-status")
def fetch_marine_status(req: MarineRequest):

    # Member 2 — SST specialist
    sst_data = get_sst_timeseries(
        min_lat=req.min_lat,
        max_lat=req.max_lat,
        min_lon=req.min_lon,
        max_lon=req.max_lon
    )

    # Member 3 — Chlorophyll specialist
    chlorophyll_data = get_chlorophyll_context(
        req.lat,
        req.lon
    )

    # Member 3 — Advisory
    advisory_data = get_incois_advisory(req.region)

    return {
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
        "incois_advisory": advisory_data
    }
@app.post("/api/chat")
async def process_chat(payload: QueryPayload):

    required = [
        "lat_min",
        "lat_max",
        "lon_min",
        "lon_max"
    ]

    if not all(
        key in payload.bbox
        for key in required
    ):
        return {
            "status": "error",
            "message": (
                "bbox must contain "
                "lat_min, lat_max, "
                "lon_min and lon_max."
            )
        }

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

    return {
        "status": "success",
        "advisory": final_state.get(
            "advisory_output"
        ),
        "sst_summary": final_state.get(
            "sst_summary"
        ),
        "chl_summary": final_state.get(
            "chl_summary"
        ),
        "agent_trace": final_state.get(
            "agent_trace"
        )
    }