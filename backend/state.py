from typing import TypedDict, List, Dict, Any


class ORCAState(TypedDict, total=False):
    # User input
    user_query: str
    location_bbox: Dict[str, float]

    # Routing decisions
    requested_agents: List[str]
    requested_capabilities: List[str]

    # Specialist outputs
    sst_summary: Dict[str, Any]
    sst_forecast: Dict[str, Any]
    chl_summary: Dict[str, Any]

    # Final outputs
    advisory_output: str
    deterministic_advisory: str
    llm_output: str

    # Explainability / UI trace
    agent_trace: List[dict[str, Any]]