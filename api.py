from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any

app = FastAPI(title="ORCA API Integration")

# This allows the frontend to talk to the backend without being blocked
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Match the exact input app.js is sending
class ChatRequest(BaseModel):
    query: str
    bbox: Dict[str, float]

# 2. Match the exact endpoint URL app.js is calling
@app.post("/api/chat")
def analyze_ocean(req: ChatRequest):
    
    # [!] This is where you will eventually plug in your bio_tools.py functions
    # Example: chlor_data = get_biological_data(15.49, 73.82)
    
    # 3. Match the EXACT output format app.js needs to populate the UI
    return {
        "sst_summary": {
            "average_sst_celsius": 28.81
        },
        "chl_summary": {
            "chlor_a_mg_m3": 1.34,
            "bloom_risk": "NOMINAL"
        },
        "sst_forecast": {
            "direction": "Slight Warming",
            "change_over_outlook_celsius": 0.12,
            "observed": [
                {"date": "Day 1", "sst": 28.5},
                {"date": "Day 2", "sst": 28.7}
            ],
            "forecast": [
                {"date": "Day 3", "sst": 28.81},
                {"date": "Day 4", "sst": 28.9}
            ]
        },
        "agent_trace": [
            {"agent": "Router", "progress": 25, "description": "Parsed user request."},
            {"agent": "SST Specialist", "progress": 50, "description": "Retrieved temperature data."},
            {"agent": "Chlorophyll Specialist", "progress": 75, "description": "Analyzed algae levels."},
            {"agent": "Synthesis", "progress": 100, "description": "Generated final advisory."}
        ],
        "advisory": "# Assessment\nAll marine conditions are nominal. The Chlorophyll levels indicate a highly favorable Potential Fishing Zone (PFZ). Proceed with standard operations."
    }
