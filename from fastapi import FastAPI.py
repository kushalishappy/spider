from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bio_tools import get_chlorophyll_context, get_incois_advisory

app = FastAPI(title="ORCA Biological Advisory API")

# Allow the frontend map to request data without being blocked
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CoordinateRequest(BaseModel):
    lat: float
    lon: float
    region: str = "goa"

@app.post("/api/marine-status")
def fetch_marine_status(req: CoordinateRequest):
    bio_data = get_chlorophyll_context(req.lat, req.lon)
    advisory_data = get_incois_advisory(req.region)
    
    return {
        "agent_name": "Chlorophyll & Rules Specialist",
        "coordinates": {"lat": req.lat, "lon": req.lon},
        "chlorophyll": bio_data,
        "incois_advisory": advisory_data
    }