/* =========================================================
   GLOBAL STATE & INITIALIZATION
========================================================= */
let oceanMap = null;
let stationMarker = null;

// Default bounding box for the AI agents
let DEFAULT_BBOX = {
    lat_min: 13.0,
    lat_max: 17.0,
    lon_min: 71.0,
    lon_max: 75.0
};

document.addEventListener("DOMContentLoaded", () => {
    // If the map div exists on load, initialize it
    if (document.getElementById("oceanMap")) {
        initializeMap();
    }

    // Allow pressing "Enter" in the chat box to submit
    const queryInput = document.getElementById("queryInput");
    if (queryInput) {
        queryInput.addEventListener("keypress", function(event) {
            if (event.key === "Enter") {
                event.preventDefault();
                runAnalysis();
            }
        });
    }
});

/* =========================================================
   UI NAVIGATION HELPERS
========================================================= */
function launchDashboard() {
    const landing = document.getElementById("landingPage");
    const dashboard = document.getElementById("dashboardLayout");
    if (landing && dashboard) {
        landing.style.display = "none";
        dashboard.style.display = "flex";
        setTimeout(() => {
            initializeMap();
        }, 100);
    }
}

function useLandingSuggestion(query) {
    const input = document.getElementById("landingQuery");
    if (input) {
        input.value = query;
        input.focus();
    }
}

function exploreFromLanding() {
    const query = document.getElementById("landingQuery") ? document.getElementById("landingQuery").value.trim() : "";
    launchDashboard();
    if (query) {
        const queryInput = document.getElementById("queryInput");
        if (queryInput) {
            queryInput.value = query;
        }
        setTimeout(() => {
            runAnalysis();
        }, 700);
    }
}

function scrollToAsk() {
    const section = document.getElementById("askSection");
    if (section) {
        section.scrollIntoView({ behavior: "smooth" });
    }
}

/* =========================================================
   MAP INITIALIZATION & INTERACTIVITY
========================================================= */
function initializeMap() {
    const mapElement = document.getElementById("oceanMap");
    if (!mapElement) { console.error("ORCA: oceanMap element not found."); return; }
    if (typeof L === "undefined") { console.error("ORCA: Leaflet not loaded."); return; }
    
    if (oceanMap !== null) {
        setTimeout(() => { oceanMap.invalidateSize(true); }, 200);
        return;
    }

    /* Create map */
    oceanMap = L.map("oceanMap", { zoomControl: true, attributionControl: true }).setView([15.49, 73.82], 6);

    /* Base Map - Esri Light (Bypasses API Key Blocks) */
    const osmLayer = L.tileLayer(
        "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}",
        { maxZoom: 16, attribution: "Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ" }
    );
    osmLayer.addTo(oceanMap);

    /* Dynamic Map Interactivity: Click to Scan */
    oceanMap.on('click', function(e) {
        const lat = e.latlng.lat;
        const lon = e.latlng.lng;

        // Remove old interactive pin
        if (stationMarker !== null) {
            oceanMap.removeLayer(stationMarker);
        }

        // Drop new pin at clicked location
        stationMarker = L.circleMarker([lat, lon], {
            radius: 9, 
            color: "#ffffff", 
            weight: 3, 
            fillColor: "#008b68", 
            fillOpacity: 1
        }).addTo(oceanMap);
        
        stationMarker.bindPopup(`
            <div style="font-family:Inter,sans-serif">
                <strong>Selected Target</strong><br>
                ${lat.toFixed(2)}°N, ${lon.toFixed(2)}°E<br>
                <small>Scanning sector...</small>
            </div>
        `).openPopup();

        // Update backend coordinates based on where the user clicked
        DEFAULT_BBOX.lat_min = lat - 2.0;
        DEFAULT_BBOX.lat_max = lat + 2.0;
        DEFAULT_BBOX.lon_min = lon - 2.0;
        DEFAULT_BBOX.lon_max = lon + 2.0;

        // Trigger AI analysis automatically
        const queryInput = document.getElementById("queryInput");
        if (queryInput) {
            queryInput.value = `Analyze marine conditions at ${lat.toFixed(2)}°N, ${lon.toFixed(2)}°E`;
        }
        
        runAnalysis();
    });

    /* Map Resize Fix */
    setTimeout(() => { oceanMap.invalidateSize(true); }, 500);
}

/* =========================================================
   BACKEND COMMUNICATION ENGINE
========================================================= */
async function runAnalysis() {
    const queryInput = document.getElementById("queryInput");
    if (!queryInput) return;
    
    const query = queryInput.value.trim();
    if (!query) return;

    try {
        // Send request to your local FastAPI server
        const response = await fetch("http://127.0.0.1:8000/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query: query, bbox: DEFAULT_BBOX })
        });

        if (!response.ok) {
            throw new Error("Backend connection failed.");
        }
        
        const data = await response.json();
        console.log("ORCA Analysis Complete:", data);
        
        // Populate UI with Backend Data (if the elements exist in your HTML)
        if (document.getElementById("advisoryText")) {
            document.getElementById("advisoryText").innerText = data.advisory || "Analysis complete.";
        }
        
    } catch (error) {
        console.error("ORCA Connection Error:", error);
        // Show error message on the frontend if the server isn't running
        if (document.getElementById("advisoryText")) {
            document.getElementById("advisoryText").innerText = "Error: Cannot connect to ORCA backend. Ensure FastAPI is running on 127.0.0.1:8000.";
        }
    }
}
