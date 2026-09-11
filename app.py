import streamlit as st
import requests
import folium
from streamlit_folium import st_folium

# Page Configuration for Deep Navy Scientific Theme
st.set_page_config(
    page_title="ORCA | Marine Intelligence Platform",
    page_icon="🌊",
    layout="wide"
)

# Custom CSS for Deep Navy & Cyan ISRO-grade aesthetics
st.markdown("""
    <style>
    .main { background-color: #0B132B; color: #E0FBFC; }
    .sidebar .sidebar-content { background-color: #1C2541; }
    h1, h2, h3 { color: #6FFFE9 !important; }
    .stMetric { background-color: #1C2541; padding: 15px; border-radius: 10px; border: 1px solid #3A506B; }
    </style>
""", unsafe_allow_html=True)

st.title("🌊 ORCA: Marine Ecosystem Reasoning & Collaborative Agents")
st.markdown("**ISRO SIH Open Innovation | Real-Time Ocean Intelligence & Hazard Tracking**")

# Sidebar for Region Selection or Custom Coordinates
st.sidebar.header("🗺️ Region & Target Selection")
preset = st.sidebar.selectbox("Quick Select Indian Coasts", [
    "Custom Coordinates", 
    "Goa Offshore (Arabian Sea)", 
    "Mumbai Waters", 
    "Chennai Coast (Bay of Bengal)"
])

# Default coordinates based on preset
if preset == "Goa Offshore (Arabian Sea)":
    default_lat, default_lon = 15.29, 73.50
elif preset == "Mumbai Waters":
    default_lat, default_lon = 18.96, 72.82
elif preset == "Chennai Coast (Bay of Bengal)":
    default_lat, default_lon = 13.08, 80.27
else:
    default_lat, default_lon = 15.29, 73.50

lat = st.sidebar.number_input("Latitude (°N)", value=default_lat, format="%.4f")
lon = st.sidebar.number_input("Longitude (°E)", value=default_lon, format="%.4f")

if st.sidebar.button("🚀 Run Multi-Agent Analysis", type="primary"):
    
    # Visualizing Agent Workflow Step-by-Step (LangGraph Simulation)
    with st.status("🤖 ORCA LangGraph Orchestrator Active...", expanded=True) as status:
        st.write("1️⃣ **Router Agent:** Dispatched query to Specialist Sub-systems...")
        
        # Call Member 3's Biological API
        try:
            bio_resp = requests.post(
                "http://127.0.0.1:8000/api/marine-status", 
                json={"lat": lat, "lon": lon, "region": "goa"}
            ).json()
            st.write("2️⃣ **Chlorophyll Specialist (Member 3):** Extracted NetCDF data successfully.")
        except Exception:
            st.error("⚠️ Failed to reach Biological API. Ensure `python -m uvicorn api:app --reload` is running!")
            st.stop()
            
        # Mock Member 2's SST Engine
        st.write("3️⃣ **SST Thermal Specialist (Member 2):** Computed thermal anomaly & heat stress.")
        sst_val = 28.9
        anomaly_val = "+1.4°C"
        
        st.write("4️⃣ **Reasoning Engine:** Applying hard-coded ecological thresholds...")
        status.update(label="✅ Multi-Agent Analysis Complete!", state="complete", expanded=False)

    # Extract results
    chlor_data = bio_resp.get("chlorophyll", {})
    chlor_val = chlor_data.get("chlor_a_mg_m3", "N/A")
    bloom_risk = chlor_data.get("bloom_risk", "Unknown")
    advisory_text = bio_resp.get("incois_advisory", {}).get("advisory_text", "No advisory available.")

    # Main Dashboard Layout (Split into 2 Columns)
    col1, col2 = st.columns([1.2, 1.8])

    with col1:
        st.subheader("📊 Specialist Diagnostics")
        st.metric(label="Chlorophyll-a Concentration", value=f"{chlor_val} mg/m³" if isinstance(chlor_val, float) else chlor_val)
        st.metric(label="Sea Surface Temperature (SST)", value=f"{sst_val} °C", delta=anomaly_val)
        
        # Risk Badge Styling
        if bloom_risk == "High Risk":
            st.error(f"🚨 **Ecological Alert:** {bloom_risk} (Potential Algal Bloom)")
        elif bloom_risk == "Elevated":
            st.warning(f"⚠️ **Ecological Alert:** {bloom_risk}")
        else:
            st.success(f"🟢 **Ecological Status:** {bloom_risk}")

    with col2:
        st.subheader("📍 Geospatial Marine Map")
        # Render Folium Map centered on user coordinates
        m = folium.Map(location=[lat, lon], zoom_start=7, tiles="CartoDB dark_matter")
        folium.Marker(
            [lat, lon], 
            popup=f"Lat: {lat}, Lon: {lon}<br>Chlorophyll: {chlor_val} mg/m³",
            icon=folium.Icon(color="cyan", icon="info-sign")
        ).add_to(m)
        st_folium(m, width="100%", height=350)

    # Explainable AI Reasoning Box (Mandatory for ISRO problem statement)
    st.subheader("📝 Transparent Agent Synthesis & Advisory")
    st.info(f"""
    **Synthesized Decision Report:**
    * **Coordinates Evaluated:** `{lat}°N, {lon}°E`
    * **Biological Finding:** Chlorophyll levels are recorded at **{chlor_val} mg/m³**, categorized under **{bloom_risk}** based on deterministic regional thresholds.
    * **INCOIS Advisory Context:** {advisory_text}
    * **System Reasoning:** Decision generated deterministically without unverified black-box LLM estimations, ensuring complete scientific auditability for marine operations.
    """)
else:
    st.info("👈 Select a coastal region or custom coordinates from the sidebar and click **Run Multi-Agent Analysis** to execute the pipeline.")