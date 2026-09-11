import requests
import json


URL = "http://127.0.0.1:8000/api/chat"

PAYLOAD = {
    "query": "Will conditions favor a harmful algal bloom near this coast next week?",
    "bbox": {
        "lat_min": 10.0,
        "lat_max": 20.0,
        "lon_min": 72.0,
        "lon_max": 82.0,
    },
}


print("=" * 70)
print("ORCA API INTEGRATION TEST")
print("=" * 70)

print("\nSending query:")
print(PAYLOAD["query"])

print("\nCalling:")
print(URL)

try:
    response = requests.post(
        URL,
        json=PAYLOAD,
        timeout=120,
    )

    print("\nHTTP STATUS:")
    print(response.status_code)

    data = response.json()

    print("\n" + "=" * 70)
    print("API RESPONSE")
    print("=" * 70)

    print(
        json.dumps(
            data,
            indent=2,
        )
    )

    print("\n" + "=" * 70)
    print("VALIDATION")
    print("=" * 70)

    if response.status_code != 200:
        print("❌ API request failed")
        raise SystemExit(1)

    if data.get("status") != "success":
        print("❌ API returned an error")
        raise SystemExit(1)

    required_agents = [
        "sst",
        "chlorophyll",
    ]

    agents = data.get(
        "requested_agents",
        [],
    )

    capabilities = data.get(
        "requested_capabilities",
        [],
    )

    trace = data.get(
        "agent_trace",
        [],
    )

    if not all(
        agent in agents
        for agent in required_agents
    ):
        print("❌ SST + Chlorophyll routing failed")
        raise SystemExit(1)

    if "sst_forecast" not in capabilities:
        print("❌ SST forecast capability missing")
        raise SystemExit(1)

    if "combined_hab_screening" not in capabilities:
        print("❌ HAB screening capability missing")
        raise SystemExit(1)

    if not data.get("sst_summary"):
        print("❌ SST result missing")
        raise SystemExit(1)

    if not data.get("sst_forecast"):
        print("❌ SST forecast result missing")
        raise SystemExit(1)

    if not data.get("chl_summary"):
        print("❌ Chlorophyll result missing")
        raise SystemExit(1)

    if not data.get("advisory"):
        print("❌ Advisory missing")
        raise SystemExit(1)

    print("\nAGENT TRACE:")

    for item in trace:
        print(
            f"[{item.get('progress')}%] "
            f"{item.get('agent')} -> "
            f"{item.get('status')}"
        )

    print("\n" + "=" * 70)
    print("✅ ORCA API INTEGRATION TEST PASSED")
    print("=" * 70)

except requests.exceptions.ConnectionError:
    print("\n❌ Could not connect to ORCA backend.")
    print("Make sure Uvicorn is running.")

except Exception as exc:
    print("\n❌ TEST FAILED")
    print(str(exc))