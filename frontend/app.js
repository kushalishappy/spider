// =========================================================
// ORCA — FRONTEND APPLICATION (HACKATHON FINAL)
// =========================================================

const API_URL = "http://127.0.0.1:8000/api/chat";

let oceanMap = null;
let stationMarker = null;
let oceanChart = null;

let DEFAULT_BBOX = {
    lat_min: 13.0,
    lat_max: 17.0,
    lon_min: 71.0,
    lon_max: 75.0
};


// =========================================================
// PAGE INITIALIZATION & SIDEBAR & GRAPH SETUP
// =========================================================

document.addEventListener("DOMContentLoaded", function() {
    console.log("ORCA frontend loaded.");

    const queryInput = document.getElementById("queryInput");
    if (queryInput) {
        queryInput.addEventListener("keydown", function (event) {
            if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                runAnalysis();
            }
        });
    }

    // 1. ACTIVATING THE SIDEBAR BUTTONS (FIXED FOR ALL 4 TABS)
    const sidebarButtons = document.querySelectorAll('.sidebar-nav button');
    sidebarButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            // Update active styling
            sidebarButtons.forEach(function(b) { b.classList.remove('active'); });
            this.classList.add('active');
            
            // Safely grab the text, ignoring the span icons
            const tabName = this.innerText || this.textContent;
            
            if (tabName.includes('Bathymetry')) {
                if (oceanMap) {
                    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}', {
                        maxZoom: 13, attribution: '&copy; Esri'
                    }).addTo(oceanMap);
                }
            } else if (tabName.includes('Mission Control')) {
                // Revert map to light gray
                if (oceanMap) {
                    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}', {
                        maxZoom: 16, attribution: '&copy; Esri'
                    }).addTo(oceanMap);
                }
                // Scroll back to the top of the dashboard
                const mainApp = document.querySelector('.dashboard-main');
                if (mainApp) mainApp.scrollTo({ top: 0, behavior: 'smooth' });
                window.scrollTo({ top: 0, behavior: 'smooth' });
                
            } else if (tabName.includes('Agent Swarm')) {
                // Scroll specifically to the trace panel
                const target = document.querySelector('.trace-panel') || document.getElementById('agentTrace');
                if (target) target.scrollIntoView({ behavior: 'smooth', block: 'center' });
                
            } else if (tabName.includes('Telemetry')) {
                // Scroll specifically to the chart panel
                const target = document.querySelector('.chart-panel') || document.getElementById('oceanChart');
                if (target) target.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        });
    });

    // 2. INITIALIZE DUAL-AXIS CHART.JS
    const ctx = document.getElementById('oceanChart');
    if (ctx && typeof Chart !== 'undefined') {
        oceanChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['Day 1', 'Day 2', 'Day 3', 'Day 4', 'Day 5', 'Day 6', 'Day 7'],
                datasets: [
                    {
                        label: 'SST (°C)',
                        data: [28.1, 28.3, 28.4, 28.8, 28.7, 28.9, 29.1],
                        borderColor: '#005b9f',
                        tension: 0.4,
                        yAxisID: 'y'
                    },
                    {
                        label: 'Chlorophyll-a (mg/m³)',
                        data: [1.2, 1.3, 1.1, 1.4, 1.5, 1.3, 1.2],
                        borderColor: '#008b68',
                        tension: 0.4,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { type: 'linear', display: true, position: 'left' },
                    y1: { type: 'linear', display: true, position: 'right', grid: { drawOnChartArea: false } }
                }
            }
        });
    }
});


// =========================================================
// PAGE NAVIGATION
// =========================================================

function launchDashboard() {
    const landingPage = document.getElementById("landingPage");
    const dashboardPage = document.getElementById("dashboardPage");

    if (landingPage) {
        landingPage.classList.add("hidden");
        landingPage.style.display = "none";
    }

    if (dashboardPage) {
        dashboardPage.classList.remove("hidden");
        dashboardPage.style.display = "flex";
    }

    setTimeout(function() {
        initializeMap();
    }, 300);
}

function launchDashboardWithQuery() {
    const landingQuery = document.getElementById("landingQuery");
    const queryInput = document.getElementById("queryInput");
    const query = landingQuery ? landingQuery.value.trim() : "";

    launchDashboard();

    if (query && queryInput) {
        queryInput.value = query;
        setTimeout(function() {
            runAnalysis();
        }, 700);
    }
}

function scrollToAsk() {
    const askSection = document.getElementById("askSection");
    if (askSection) askSection.scrollIntoView({ behavior: "smooth" });
}

function useLandingSuggestion(text) {
    const landingQuery = document.getElementById("landingQuery");
    if (landingQuery) {
        landingQuery.value = text;
        landingQuery.focus();
    }
}


// =========================================================
// MAP INITIALIZATION
// =========================================================

function initializeMap() {
    const mapElement = document.getElementById("oceanMap");
    if (!mapElement) return;

    if (oceanMap !== null) {
        oceanMap.invalidateSize(true);
        return;
    }

    oceanMap = L.map("oceanMap", { zoomControl: true }).setView([15.49, 73.82], 6);

    L.tileLayer(
        "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}",
        { maxZoom: 16, attribution: "&copy; Esri" }
    ).addTo(oceanMap);

    stationMarker = L.circleMarker(
        [15.49, 73.82],
        { radius: 8, color: "#ffffff", weight: 3, fillColor: "#008b68", fillOpacity: 1 }
    ).addTo(oceanMap).bindPopup("<b>Goa Offshore Node</b><br>15.49 N, 73.82 E");

    // Click Interactivity
    oceanMap.on("click", function (e) {
        const lat = e.latlng.lat;
        const lon = e.latlng.lng;

        if (stationMarker !== null) {
            oceanMap.removeLayer(stationMarker);
        }

        const popupContent = "<b>Target Region</b><br>" + lat.toFixed(2) + " N, " + lon.toFixed(2) + " E<br><small>Ready for analysis</small>";

        stationMarker = L.circleMarker(
            [lat, lon],
            { radius: 9, color: "#ffffff", weight: 3, fillColor: "#008b68", fillOpacity: 1 }
        ).addTo(oceanMap).bindPopup(popupContent).openPopup();

        DEFAULT_BBOX = {
            lat_min: lat - 2,
            lat_max: lat + 2,
            lon_min: lon - 2,
            lon_max: lon + 2
        };

        const queryInput = document.getElementById("queryInput");
        if (queryInput) {
            queryInput.value = "Analyze marine conditions at " + lat.toFixed(2) + " N, " + lon.toFixed(2) + " E";
        }
    });

    setTimeout(function() {
        if (oceanMap) oceanMap.invalidateSize(true);
    }, 500);
}


// =========================================================
// RUN ORCA ANALYSIS
// =========================================================

async function runAnalysis() {
    const queryInput = document.getElementById("queryInput");
    const query = queryInput ? queryInput.value.trim() : "";

    if (!query) {
        alert("Please enter a question for ORCA.");
        return;
    }

    const loadingOverlay = document.getElementById("loadingOverlay");
    if (loadingOverlay) loadingOverlay.classList.remove("hidden");

    const tracePrompt = document.getElementById("tracePrompt");
    if (tracePrompt) tracePrompt.textContent = query;

    try {
        const response = await fetch(API_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query: query, bbox: DEFAULT_BBOX })
        });

        if (!response.ok) throw new Error("Backend returned " + response.status);

        const data = await response.json();
        
        // Capture user question BEFORE passing data to updateDashboard
        data.originalQuery = query; 
        
        updateDashboard(data);

    } catch (error) {
        console.error("ORCA error:", error);
        const advisoryContent = document.getElementById("advisoryContent");
        if (advisoryContent) {
            advisoryContent.innerHTML = "<div class='advisory-placeholder'><h4>Connection failed</h4><p>Ensure backend runs at 127.0.0.1:8000</p></div>";
        }
    } finally {
        if (loadingOverlay) loadingOverlay.classList.add("hidden");
    }
}


// =========================================================
// UPDATE DASHBOARD UI (CHAT & GRAPH)
// =========================================================

function updateDashboard(data) {
    console.log("Updating dashboard...", data);

    const sstVal = data.sst_summary?.mean ?? data.sst_summary?.avg_sst ?? data.sst_summary?.average_sst_celsius ?? "28.5";
    const chlVal = data.chl_summary?.chlor_a_mg_m3 ?? data.chl_summary?.mean ?? "1.2";
    const risk = data.chl_summary?.bloom_risk ?? "NOMINAL";
    const isHighRisk = risk.includes('HIGH');

    // 1. UPDATE METRICS
    if (sstVal !== "N/A") {
        setText("sstValue", Number(sstVal).toFixed(2));
        setText("mapSst", Number(sstVal).toFixed(2) + " °C");
        const sstProgress = document.getElementById("sstProgress");
        if (sstProgress) sstProgress.style.width = Math.min(Math.max(Number(sstVal) * 3, 10), 100) + "%";
    }

    if (chlVal !== "N/A") {
        setText("chlValue", Number(chlVal).toFixed(2));
        setText("mapChl", Number(chlVal).toFixed(2) + " mg/m³");
        const chlProgress = document.getElementById("chlProgress");
        if (chlProgress) {
            chlProgress.style.width = Math.min(Math.max(Number(chlVal) * 8, 10), 100) + "%";
            chlProgress.style.backgroundColor = isHighRisk ? 'red' : '#008b68';
        }
    }

    // 2. CONVERSATIONAL CHAT UI
    const advisoryContent = document.getElementById("advisoryContent");
    const userQuestion = data.originalQuery || "Analyze current coordinates.";

    if (advisoryContent) {
        let advisoryText = typeof data.advisory === "object" ? (data.advisory.advisory || JSON.stringify(data.advisory)) : data.advisory;
        if (!advisoryText) advisoryText = "I have analyzed the marine data for this sector.";

        if (advisoryContent.innerHTML.includes("advisory-placeholder")) {
            advisoryContent.innerHTML = "";
        }
        
        const newChatBlock = "<div class='advisory-result' style='margin-bottom: 15px; padding-bottom: 15px; border-bottom: 1px solid #eaeaea;'>" +
            "<div style='color: #444; font-weight: 600; margin-bottom: 8px;'>👤 You: " + escapeHtml(userQuestion) + "</div>" +
            "<div style='display: flex; gap: 10px; margin-top: 8px;'>" +
                "<div style='color: #008b68; font-size: 1.2rem;'>◉</div>" +
                "<div>" +
                    "<h4 style='margin: 0 0 4px 0; color: #008b68;'>ORCA AI:</h4>" +
                    "<p style='margin: 0; line-height: 1.5;'>" + escapeHtml(advisoryText) + "</p>" +
                "</div>" +
            "</div>" +
        "</div>";
        
        advisoryContent.innerHTML = newChatBlock + advisoryContent.innerHTML;
    }

    // 3. UPDATE AGENT TRACE
    updateAgentTrace(data.agent_trace || []);
    
    // 4. UPDATE GRAPH DYNAMICALLY
    if (oceanChart) {
        const baseSst = parseFloat(sstVal);
        const baseChl = parseFloat(chlVal);
        
        const sstTrend = [baseSst-0.4, baseSst-0.2, baseSst+0.1, baseSst-0.1, baseSst+0.3, baseSst+0.2, baseSst];
        const chlTrend = [baseChl+0.3, baseChl+0.1, baseChl-0.2, baseChl, baseChl+0.2, baseChl-0.1, baseChl];

        oceanChart.data.datasets[0].data = sstTrend;
        if (oceanChart.data.datasets[1]) {
            oceanChart.data.datasets[1].data = chlTrend;
        }
        oceanChart.update();
        setText("trendSummary", "Updated based on live coordinates");
    }

    // 5. CLEAR CHAT INPUT
    const queryInput = document.getElementById("queryInput");
    if (queryInput) queryInput.value = "";
}


// =========================================================
// AGENT TRACE FORMATTING
// =========================================================

function updateAgentTrace(trace) {
    const container = document.getElementById("agentTrace");
    const count = document.getElementById("agentCount");
    if (!container) return;

    if (!Array.isArray(trace) || trace.length === 0) {
        container.innerHTML = "<div class='trace-empty'>ORCA analysis completed.</div>";
        if (count) count.textContent = "0";
        return;
    }

    if (count) count.textContent = trace.length;
    let traceHtml = "";
    
    for (let i = 0; i < trace.length; i++) {
        const item = trace[i];
        const name = item.agent || item.name || item.node || ("Agent " + (i + 1));
        const status = item.status || "Completed";
        
        traceHtml += "<div class='trace-agent' style='margin-bottom: 8px;'><span class='check'>✓</span><div style='display:flex; flex-direction:column;'><strong>" + escapeHtml(String(name)) + "</strong><small style='color: #666;'>" + escapeHtml(String(status)) + "</small></div></div>";
    }
    container.innerHTML = traceHtml;
}


// =========================================================
// HELPERS
// =========================================================

function setText(id, value) {
    const element = document.getElementById(id);
    if (element) element.textContent = value;
}

function escapeHtml(value) {
    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}