from backend.graph import orca_graph


BBOX = {
    "lat_min": 10.0,
    "lat_max": 20.0,
    "lon_min": 72.0,
    "lon_max": 82.0,
}


def run_test(title, query):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)

    result = orca_graph.invoke(
        {
            "user_query": query,
            "location_bbox": BBOX,
            "agent_trace": [],
        },
        config={
            "configurable": {
                "thread_id": title
            }
        },
    )

    print("\nQUERY:")
    print(query)

    print("\nREQUESTED AGENTS:")
    print(result.get("requested_agents"))

    print("\nREQUESTED CAPABILITIES:")
    print(result.get("requested_capabilities"))

    print("\n--- SST RESULT ---")
    print(result.get("sst_summary"))

    print("\n--- SST FORECAST RESULT ---")
    print(result.get("sst_forecast"))

    print("\n--- CHLOROPHYLL RESULT ---")
    print(result.get("chl_summary"))

    print("\n--- ADVISORY ---")
    print(result.get("advisory_output"))

    print("\n--- AGENT TRACE ---")
    for item in result.get("agent_trace", []):
        print(
            f"[{item['progress']}%] "
            f"{item['agent']} -> {item['status']}"
        )

    return result


# ============================================================
# TEST 1 — SST ONLY
# ============================================================

run_test(
    "TEST 1 - SST ONLY",
    "What is the sea surface temperature in this region?",
)


# ============================================================
# TEST 2 — CHLOROPHYLL ONLY
# ============================================================

run_test(
    "TEST 2 - CHLOROPHYLL ONLY",
    "What is the chlorophyll level in this region?",
)


# ============================================================
# TEST 3 — HAB + FORECAST
# ============================================================

run_test(
    "TEST 3 - HAB NEXT WEEK",
    "Will conditions favor a harmful algal bloom near this coast next week?",
)