let oceanMap = null;
let stationMarker = null;

let DEFAULT_BBOX = { lat_min: 13.0, lat_max: 17.0, lon_min: 71.0, lon_max: 75.0 };

document.addEventListener("DOMContentLoaded", () => {
    if (document.getElementById("oceanMap")) initializeMap();
    
    const queryInput = document.getElementById("queryInput");
    if (queryInput) {
        queryInput.addEventListener("keypress", function(event) {
            if (event.key === "Enter") { event.preventDefault(); runAnalysis(); }
        });
    }
});

function launchDashboard() {
    document.getElementById("landingPage").style.display = "none";
    document.getElementById("dashboardLayout").style.display = "flex";
    setTimeout(initializeMap, 100);
}

function initializeMap() {
    if (!document.getElementById("oceanMap") || oceanMap !== null) return;

    oceanMap = L.map("oceanMap", { zoomControl: true }).setView([15.49, 73.82], 6);

    // Light Map that bypasses API Blocks
    L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}", 
        { maxZoom: 16, attribution: "&copy; Esri" }
    ).addTo(oceanMap);

    // Click to Scan Logic
    oceanMap.on('click', function(e) {
        const lat = e.latlng.lat; const lon = e.latlng.lng;

        if (stationMarker !== null) oceanMap.removeLayer(stationMarker);

        stationMarker = L.circleMarker([lat, lon], {
            radius: 9, color: "#ffffff", weight: 3, fillColor: "#008b68", fillOpacity: 1
        }).addTo(oceanMap).bindPopup(`<b>Target</b><br>${lat.toFixed(2)}°N, ${lon.toFixed(2)}°E<br><small>Scanning...</small>`).openPopup();

        DEFAULT_BBOX = { lat_min: lat - 2, lat_max: lat + 2, lon_min: lon - 2, lon_max: lon + 2 };

        const queryInput = document.getElementById("queryInput");
        if (queryInput) queryInput.value = `Analyze marine conditions at ${lat.toFixed(2)}°N, ${lon.toFixed(2)}°E`;
        
        runAnalysis();
    });

    setTimeout(() => { oceanMap.invalidateSize(true); }, 500);
}

async function runAnalysis() {
    const query = document.getElementById("queryInput")?.value.trim();
    if (!query) return;

    // Show loading state (Optional, if you have elements for it)
    if (document.getElementById("advisoryText")) document.getElementById("advisoryText").innerText = "Agents are analyzing the sector...";

    try {
        const response = await fetch("http://127.0.0.1:8000/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query: query, bbox: DEFAULT_BBOX })
        });

        if (!response.ok) throw new Error("Backend connection failed.");
        const data = await response.json();
        
        // Populate UI with real AI data
        if (document.getElementById("advisoryText")) document.getElementById("advisoryText").innerText = data.advisory;
        
    } catch (error) {
        console.error(error);
        if (document.getElementById("advisoryText")) document.getElementById("advisoryText").innerText = "Error: Cannot connect to ORCA backend on 127.0.0.1:8000.";
    }
}
