/* =========================================================
   ORCA — COMPLETE FRONTEND/BACKEND CONNECTION
   ========================================================= */

const API_URL = "http://127.0.0.1:8000/api/chat";

const DEFAULT_BBOX = {
    lat_min: 10.0,
    lat_max: 20.0,
    lon_min: 72.0,
    lon_max: 82.0
};

let oceanMap = null;
let sstChart = null;
let regionRectangle = null;
let regionMarker = null;
let stationMarker = null;


/* =========================================================
   PAGE NAVIGATION
   ========================================================= */

function launchDashboard() {
    const landingPage = document.getElementById("landingPage");
    const dashboardPage = document.getElementById("dashboardPage");

    if (landingPage) {
        landingPage.classList.add("hidden");
    }

    if (dashboardPage) {
        dashboardPage.classList.remove("hidden");
    }

    setTimeout(() => {
        initializeMap();

        if (oceanMap) {
            oceanMap.invalidateSize(true);
        }
    }, 150);

    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });
}


function launchDashboardWithQuery() {
    const input = document.getElementById("landingQuery");

    const query = input
        ? input.value.trim()
        : "";

    launchDashboard();

    if (query) {
        const queryInput =
            document.getElementById("queryInput");

        if (queryInput) {
            queryInput.value = query;
        }

        setTimeout(() => {
            runAnalysis();
        }, 700);
    }
}


function scrollToAsk() {
    const section =
        document.getElementById("askSection");

    if (section) {
        section.scrollIntoView({
            behavior: "smooth"
        });/**
    }
}


function useLandingSuggestion(query) {
    const input =
        document.getElementById("landingQuery");

    if (input) {
        input.value = query;
        input.focus();
    }
}


/* =========================================================
   MAP
   ========================================================= *

function initializeMap() {

    const mapElement =
        document.getElementById("oceanMap");

    if (!mapElement) {
        console.error("ORCA: oceanMap element not found.");
        return;
    }

    if (typeof L === "undefined") {
        console.error("ORCA: Leaflet not loaded.");
        return;
    }

    if (oceanMap !== null) {
        setTimeout(() => {
            oceanMap.invalidateSize(true);
        }, 200);

        return;
    }

**/
    /* Create map */

    oceanMap = L.map("oceanMap", {
        zoomControl: true,
        attributionControl: true
    }).setView(
        [15.49, 73.82],
        6
    );


    /* =====================================================
       BASE MAP
       ===================================================== */

  const osmLayer = L.tileLayer(
    "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}",
    {
        maxZoom: 16,
        attribution: "Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ"
    }
);

    osmLayer.addTo(oceanMap);
       /* =====================================================
       DYNAMIC MAP INTERACTIVITY
    ===================================================== */
    oceanMap.on('click', function(e) {
        const lat = e.latlng.lat;
        const lon = e.latlng.lng;

        // 1. Remove the old marker if it exists
        if (stationMarker !== null) {
            oceanMap.removeLayer(stationMarker);
        }

        // 2. Drop a new interactive pin at the clicked location
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

        // 3. Update the global bounding box so the backend knows where to look
        DEFAULT_BBOX.lat_min = lat - 2.0;
        DEFAULT_BBOX.lat_max = lat + 2.0;
        DEFAULT_BBOX.lon_min = lon - 2.0;
        DEFAULT_BBOX.lon_max = lon + 2.0;

        // 4. Update the chat bar and automatically trigger the AI analysis
        const queryInput = document.getElementById("queryInput");
        if (queryInput) {
            queryInput.value = `Analyze marine conditions at ${lat.toFixed(2)}°N, ${lon.toFixed(2)}°E`;
        }
        
        runAnalysis();
    });


    /* =====================================================
       ANALYSIS REGION
       ===================================================== */

    regionRectangle = L.rectangle(
        [
            [
                DEFAULT_BBOX.lat_min,
                DEFAULT_BBOX.lon_min
            ],
            [
                DEFAULT_BBOX.lat_max,
                DEFAULT_BBOX.lon_max
            ]
        ],
        {
            color: "#0878c0",
            weight: 2,
            fillColor: "#35aeea",
            fillOpacity: 0.10
        }
    ).addTo(oceanMap);


    /* =====================================================
       GOA STATION
       ===================================================== */

    regionMarker = L.circleMarker(
        [15.49, 73.82],
        {
            radius: 9,
            color: "#ffffff",
            weight: 3,
            fillColor: "#0878c0",
            fillOpacity: 1
        }
    ).addTo(oceanMap);


    regionMarker.bindPopup(`
        <div style="font-family:Inter,sans-serif">
            <strong>Goa Offshore Node</strong><br>
            15.49°N, 73.82°E<br>
            <small>ORCA Analysis Station</small>
        </div>
    `);


    /* =====================================================
       CUSTOM GOA LABEL
       ===================================================== */

    const goaIcon = L.divIcon({
        className: "orca-goa-marker",
        html: `
            <div style="
                width:16px;
                height:16px;
                border-radius:50%;
                background:#008b68;
                border:3px solid white;
                box-shadow:0 2px 10px rgba(0,0,0,.30);
            "></div>
        `,
        iconSize: [16, 16],
        iconAnchor: [8, 8]
    });


    stationMarker = L.marker(
        [15.49, 73.82],
        {
            icon: goaIcon
        }
    )
        .addTo(oceanMap)
        .bindPopup(`
            <strong>Goa Offshore Node</strong><br>
            SST: <span id="popupSst">28.81°C</span><br>
            Chlorophyll-a:
            <span id="popupChl">1.34 mg/m³</span>
        `);


    /* =====================================================
       ADD SOME REFERENCE LOCATIONS
       ===================================================== */

    addMapLabel(
        [15.49, 73.82],
        "Goa Observation Node"
    );

    addMapLabel(
        [13.08, 80.27],
        "Chennai Shelf"
    );

    addMapLabel(
        [10.0, 72.0],
        "Lakshadweep Basin"
    );


    /* =====================================================
       MAP RESIZE
       ===================================================== */

    setTimeout(() => {
        oceanMap.invalidateSize(true);
    }, 500);
}


/* =========================================================
   MAP LABEL
   ========================================================= */

function addMapLabel(coords, text) {

    if (!oceanMap) {
        return;
    }

    const icon = L.divIcon({
        className: "orca-map-label",
        html: `
            <div style="
                background:white;
                padding:6px 10px;
                border-radius:8px;
                box-shadow:0 2px 8px rgba(0,0,0,.18);
                font-family:Inter,sans-serif;
                font-size:11px;
                font-weight:600;
                color:#123047;
                white-space:nowrap;
            ">
                <span style="
                    display:inline-block;
                    width:7px;
                    height:7px;
                    border-radius:50%;
                    background:#0878c0;
                    margin-right:5px;
                "></span>
                ${escapeHtml(text)}
            </div>
        `,
        iconSize: null
    });

    L.marker(coords, {
        icon: icon
    }).addTo(oceanMap);
}


/* =========================================================
   MAIN BACKEND CALL
   ========================================================= */

async function runAnalysis() {

    const input =
        document.getElementById("queryInput");

    const query =
        input
            ? input.value.trim()
            : "";

    const finalQuery =
        query ||
        "Analyze current marine conditions for this region.";


    showLoading(true);

    updatePrompt(finalQuery);

    try {

        console.log(
            "ORCA → Backend:",
            API_URL
        );

        console.log(
            "ORCA → Query:",
            finalQuery
        );


        const response = await fetch(
            API_URL,
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({
                    query: finalQuery,
                    bbox: DEFAULT_BBOX
                })
            }
        );


        if (!response.ok) {

            let errorMessage =
                `HTTP ${response.status}`;

            try {
                const errorData =
                    await response.json();

                errorMessage =
                    errorData.detail ||
                    errorData.message ||
                    errorMessage;

            } catch (_) {}

            throw new Error(errorMessage);
        }


        const data =
            await response.json();


        console.log(
            "ORCA ← Backend response:",
            data
        );


        updateDashboard(data);


    } catch (error) {

        console.error(
            "ORCA Backend Error:",
            error
        );

        showError(
            getFriendlyError(error)
        );

    } finally {

        showLoading(false);
    }
}


/* =========================================================
   NORMALIZE BACKEND RESPONSE
   ========================================================= */

function normalizeResponse(data) {

    const root =
        data || {};

    const results =
        root.results || {};

    const sst =
        root.sst_summary ||
        root.sst ||
        results.sst ||
        {};

    const chlorophyll =
        root.chl_summary ||
        root.chlorophyll ||
        results.chlorophyll ||
        results.chl ||
        {};

    const forecast =
        root.sst_forecast ||
        root.forecast ||
        results.sst_forecast ||
        {};

    const trace =
        root.agent_trace ||
        root.trace ||
        results.agent_trace ||
        [];

    const advisory =
        root.gemini_advisory?.advisory ||
        root.advisory ||
        root.deterministic_advisory ||
        root.llm_output ||
        results.advisory ||
        "Analysis completed successfully.";


    return {
        query:
            root.query ||
            root.user_query ||
            "",

        sst,
        chlorophyll,
        forecast,
        trace,
        advisory
    };
}


/* =========================================================
   UPDATE EVERYTHING
   ========================================================= */

function updateDashboard(data) {

    const normalized =
        normalizeResponse(data);


    console.log(
        "ORCA normalized:",
        normalized
    );


    updateMetrics(
        normalized.sst,
        normalized.forecast,
        normalized.chlorophyll
    );


    updateAgentTrace(
        normalized.trace,
        normalized.query
    );


    updateAdvisory(
        normalized.advisory
    );


    updateChart(
        normalized.forecast
    );


    updateMapValues(
        normalized.sst,
        normalized.chlorophyll
    );
}


/* =========================================================
   METRICS
   ========================================================= */

function updateMetrics(
    sst,
    forecast,
    chlorophyll
) {

    /* ---------------- SST ---------------- */

    const sstValue =
        extractSstValue(sst);

    if (sstValue !== null) {

        const element =
            document.getElementById(
                "sstValue"
            );

        if (element) {
            element.textContent =
                formatNumber(
                    sstValue,
                    2
                );
        }


        const status =
            document.getElementById(
                "sstStatus"
            );

        if (status) {
            status.textContent =
                "AVAILABLE";
        }


        const progress =
            document.getElementById(
                "sstProgress"
            );

        if (progress) {

            const percentage =
                Math.min(
                    Math.max(
                        ((sstValue - 20) / 15) * 100,
                        8
                    ),
                    100
                );

            progress.style.width =
                `${percentage}%`;
        }
    }


    /* ---------------- SST TREND ---------------- */

    const direction =
        extractTrendDirection(
            forecast
        );

    const delta =
        document.getElementById(
            "sstDelta"
        );

    if (delta) {
        delta.textContent =
            direction;
    }


    /* ---------------- CHLOROPHYLL ---------------- */

    const chlValue =
        extractChlorophyllValue(
            chlorophyll
        );

    if (chlValue !== null) {

        const element =
            document.getElementById(
                "chlValue"
            );

        if (element) {

            element.textContent =
                formatNumber(
                    chlValue,
                    2
                );
        }


        const status =
            document.getElementById(
                "chlStatus"
            );

        if (status) {

            status.textContent =
                chlorophyll.bloom_risk ||
                chlorophyll.risk ||
                "AVAILABLE";
        }


        const progress =
            document.getElementById(
                "chlProgress"
            );

        if (progress) {

            const percentage =
                Math.min(
                    Math.max(
                        (chlValue / 5) * 100,
                        8
                    ),
                    100
                );

            progress.style.width =
                `${percentage}%`;
        }
    }
}


/* =========================================================
   EXTRACT SST
   ========================================================= */

function extractSstValue(sst) {

    if (!sst) {
        return null;
    }

    const candidates = [

        sst.metrics?.average_sst_celsius,

        sst.metrics?.mean_sst_celsius,

        sst.average_sst_celsius,

        sst.mean_sst_celsius,

        sst.avg_sst,

        sst.value,

        sst.sst_celsius,

        sst.temperature

    ];


    for (const value of candidates) {

        const number =
            Number(value);

        if (
            Number.isFinite(number)
        ) {
            return number;
        }
    }

    return null;
}


/* =========================================================
   EXTRACT CHLOROPHYLL
   ========================================================= */

function extractChlorophyllValue(
    chlorophyll
) {

    if (!chlorophyll) {
        return null;
    }

    const candidates = [

        chlorophyll.chlor_a_mg_m3,

        chlorophyll.chlorophyll_a_mg_m3,

        chlorophyll.mean_chlor_a_mg_m3,

        chlorophyll.average_chlor_a_mg_m3,

        chlorophyll.value,

        chlorophyll.chlor_a,

        chlorophyll.chlorophyll

    ];


    for (const value of candidates) {

        const number =
            Number(value);

        if (
            Number.isFinite(number)
        ) {
            return number;
        }
    }

    return null;
}


/* =========================================================
   MAP VALUES
   ========================================================= */

function updateMapValues(
    sst,
    chlorophyll
) {

    const sstValue =
        extractSstValue(sst);

    const chlValue =
        extractChlorophyllValue(
            chlorophyll
        );


    if (sstValue !== null) {

        const element =
            document.getElementById(
                "mapSst"
            );

        if (element) {

            element.textContent =
                `${formatNumber(
                    sstValue,
                    2
                )}°C`;
        }

        const popup =
            document.getElementById(
                "popupSst"
            );

        if (popup) {

            popup.textContent =
                `${formatNumber(
                    sstValue,
                    2
                )}°C`;
        }
    }


    if (chlValue !== null) {

        const element =
            document.getElementById(
                "mapChl"
            );

        if (element) {

            element.textContent =
                `${formatNumber(
                    chlValue,
                    2
                )} mg/m³`;
        }

        const popup =
            document.getElementById(
                "popupChl"
            );

        if (popup) {

            popup.textContent =
                `${formatNumber(
                    chlValue,
                    2
                )} mg/m³`;
        }
    }
}


/* =========================================================
   AGENT TRACE
   ========================================================= */

function updateAgentTrace(
    trace,
    query
) {

    const container =
        document.getElementById(
            "agentTrace"
        );

    const prompt =
        document.getElementById(
            "tracePrompt"
        );

    const count =
        document.getElementById(
            "agentCount"
        );


    if (prompt) {
        prompt.textContent =
            query ||
            "Analyze current marine conditions.";
    }


    if (!Array.isArray(trace)) {
        trace = [];
    }


    if (count) {
        count.textContent =
            trace.length;
    }


    if (!container) {
        return;
    }


    if (!trace.length) {

        container.innerHTML = `
            <div class="trace-empty">
                Analysis completed. No detailed
                agent trace was returned by backend.
            </div>
        `;

        return;
    }


    container.innerHTML = "";


    trace.forEach(
        (item, index) => {

            const wrapper =
                document.createElement(
                    "div"
                );

            wrapper.className =
                "trace-item";


            const agentName =
                item.agent ||
                item.agent_name ||
                item.name ||
                `Agent ${index + 1}`;


            const progress =
                item.progress ??
                item.percentage ??
                ((index + 1) / trace.length) * 100;


            wrapper.innerHTML = `

                <div class="trace-card">

                    <div class="trace-card-header">

                        <strong>
                            ${escapeHtml(
                                agentName
                            )}
                        </strong>

                        <span>
                            ${Math.round(
                                Number(progress)
                            )}%
                        </span>

                    </div>

                    <p>
                        ${escapeHtml(
                            item.description ||
                            getAgentDescription(
                                agentName
                            )
                        )}
                    </p>

                </div>
            `;


            container.appendChild(
                wrapper
            );
        }
    );
}


/* =========================================================
   AGENT DESCRIPTIONS
   ========================================================= */

function getAgentDescription(
    agentName
) {

    const name =
        String(
            agentName || ""
        ).toLowerCase();


    if (name.includes("router")) {

        return (
            "Parsed the user request and selected " +
            "the required marine specialists."
        );
    }


    if (
        name.includes("sst") &&
        name.includes("forecast")
    ) {

        return (
            "Generated the SST trend outlook " +
            "from marine observations."
        );
    }


    if (name.includes("sst")) {

        return (
            "Retrieved regional sea-surface " +
            "temperature statistics."
        );
    }


    if (
        name.includes("chlorophyll") ||
        name.includes("chl")
    ) {

        return (
            "Retrieved regional chlorophyll-a " +
            "evidence."
        );
    }


    if (
        name.includes("advisory") ||
        name.includes("reason") ||
        name.includes("synthesis")
    ) {

        return (
            "Synthesized specialist evidence " +
            "into the final marine advisory."
        );
    }


    return (
        "Completed its assigned marine-analysis task."
    );
}


/* =========================================================
   ADVISORY
   ========================================================= */

function updateAdvisory(
    advisory
) {

    const container =
        document.getElementById(
            "advisoryContent"
        );

    if (!container) {
        return;
    }


    if (
        typeof advisory === "object"
    ) {

        advisory =
            advisory.text ||
            advisory.message ||
            JSON.stringify(
                advisory,
                null,
                2
            );
    }


    const sections =
        parseAdvisory(
            advisory
        );


    let html = `
        <div class="advisory-heading">
            Marine Advisory
        </div>
    `;


    sections.forEach(
        section => {

            html += `
                <div class="advisory-section">

                    <strong>
                        ${escapeHtml(
                            section.title
                        )}
                    </strong>

                    <span>
                        ${escapeHtml(
                            section.body
                        ).replace(
                            /\n/g,
                            "<br>"
                        )}
                    </span>

                </div>
            `;
        }
    );


    container.innerHTML =
        html;
}


/* =========================================================
   PARSE ADVISORY
   ========================================================= */

function parseAdvisory(
    text
) {

    const lines =
        String(text || "")
            .split("\n")
            .map(
                line =>
                    line.trim()
            )
            .filter(Boolean);


    if (!lines.length) {

        return [
            {
                title: "Assessment",
                body:
                    "No advisory information returned."
            }
        ];
    }


    const result = [];

    let current = {
        title: "Assessment",
        body: ""
    };


    lines.forEach(
        line => {

            const heading =
                line.match(
                    /^#+\s*(.+)$/
                );


            if (
                heading ||
                (
                    line.endsWith(":") &&
                    !line.startsWith("-")
                )
            ) {

                if (
                    current.body.trim()
                ) {

                    result.push({
                        ...current
                    });
                }


                current = {
                    title:
                        heading
                            ? heading[1]
                            : line.replace(
                                /:$/,
                                ""
                            ),

                    body: ""
                };

                return;
            }


            const cleaned =
                line
                    .replace(
                        /^[-*]\s*/,
                        ""
                    );


            if (current.body) {
                current.body += "\n";
            }


            current.body += cleaned;
        }
    );


    if (
        current.body.trim()
    ) {

        result.push(
            current
        );
    }


    return result;
}


/* =========================================================
   CHART
   ========================================================= */

function updateChart(
    forecast
) {

    if (
        typeof Chart === "undefined"
    ) {

        console.warn(
            "ORCA: Chart.js not loaded."
        );

        return;
    }


    if (!forecast) {
        return;
    }


    const forecastArray =
        forecast.forecast ||
        forecast.predictions ||
        forecast.data ||
        [];


    const observedArray =
        forecast.observed_recent ||
        forecast.observed ||
        [];


    if (
        !forecastArray.length &&
        !observedArray.length
    ) {

        return;
    }


    const getDate =
        item =>
            item.date ||
            item.time ||
            item.timestamp ||
            "";


    const getSst =
        item =>
            Number(
                item.sst_celsius ??
                item.sst ??
                item.temperature
            );


    const observedDates =
        observedArray.map(getDate);

    const forecastDates =
        forecastArray.map(getDate);


    const observedValues =
        observedArray.map(getSst);

    const forecastValues =
        forecastArray.map(getSst);


    const labels = [
        ...observedDates,
        ...forecastDates
    ];


    const observedData = [
        ...observedValues,
        ...new Array(
            forecastValues.length
        ).fill(null)
    ];


    const forecastData = [
        ...new Array(
            observedValues.length
        ).fill(null),
        ...forecastValues
    ];


    const canvas =
        document.getElementById(
            "sstChart"
        );


    if (!canvas) {
        return;
    }


    if (sstChart) {
        sstChart.destroy();
    }


    sstChart =
        new Chart(
            canvas,
            {
                type: "line",

                data: {

                    labels: labels,

                    datasets: [

                        {
                            label:
                                "Observed SST",

                            data:
                                observedData,

                            borderColor:
                                "#0878c0",

                            backgroundColor:
                                "rgba(8,120,192,.08)",

                            borderWidth: 2,

                            pointRadius: 3,

                            tension: 0.35,

                            fill: true
                        },

                        {
                            label:
                                "SST Forecast",

                            data:
                                forecastData,

                            borderColor:
                                "#008764",

                            borderDash:
                                [5, 4],

                            borderWidth: 2,

                            pointRadius: 3,

                            tension: 0.25,

                            fill: false
                        }
                    ]
                },

                options: {

                    responsive: true,

                    maintainAspectRatio: false,

                    interaction: {
                        mode: "index",
                        intersect: false
                    },

                    plugins: {

                        legend: {
                            display: false
                        },

                        tooltip: {
                            backgroundColor:
                                "#082438",

                            padding: 10
                        }
                    },

                    scales: {

                        x: {

                            grid: {
                                display: false
                            },

                            ticks: {
                                color:
                                    "#758494",

                                maxTicksLimit: 10
                            }
                        },

                        y: {

                            grid: {
                                color:
                                    "#e7eef4"
                            },

                            ticks: {
                                color:
                                    "#758494"
                            },

                            title: {

                                display: true,

                                text:
                                    "SST °C",

                                color:
                                    "#687889"
                            }
                        }
                    }
                }
            }
        );


    const change =
        forecast.outlook
            ?.change_over_outlook_celsius ??
        forecast.change_over_outlook_celsius ??
        null;


    const direction =
        extractTrendDirection(
            forecast
        );


    const summary =
        document.getElementById(
            "trendSummary"
        );


    if (summary) {

        if (change !== null) {

            summary.textContent =
                `${direction} • ${
                    formatNumber(
                        change,
                        3
                    )
                }°C outlook change`;

        } else {

            summary.textContent =
                `${direction} • Forecast available`;
        }
    }
}


/* =========================================================
   TREND
   ========================================================= */

function extractTrendDirection(
    forecast
) {

    return (
        forecast?.trend?.direction ||
        forecast?.trend_direction ||
        forecast?.direction ||
        "Stable"
    );
}


/* =========================================================
   PROMPT
   ========================================================= */

function updatePrompt(
    query
) {

    const element =
        document.getElementById(
            "tracePrompt"
        );

    if (element) {
        element.textContent =
            query;
    }
}


/* =========================================================
   LOADING
   ========================================================= */

function showLoading(
    visible
) {

    const overlay =
        document.getElementById(
            "loadingOverlay"
        );

    if (!overlay) {
        return;
    }


    if (visible) {
        overlay.classList.remove(
            "hidden"
        );
    } else {
        overlay.classList.add(
            "hidden"
        );
    }
}


/* =========================================================
   ERROR
   ========================================================= */

function showError(
    message
) {

    const container =
        document.getElementById(
            "advisoryContent"
        );

    if (!container) {
        return;
    }


    container.innerHTML = `
        <div
            class="advisory-section"
            style="
                border-left-color:#d9534f;
                background:#fff3f2;
            "
        >

            <strong>
                ORCA Backend Error
            </strong>

            <span>
                ${escapeHtml(message)}
            </span>

        </div>
    `;
}


function getFriendlyError(
    error
) {

    const message =
        error?.message ||
        String(error);


    if (
        message.includes(
            "Failed to fetch"
        )
    ) {

        return (
            "Cannot connect to FastAPI. " +
            "Start the ORCA backend on " +
            "127.0.0.1:8000."
        );
    }


    return message;
}


/* =========================================================
   HELPERS
   ========================================================= */

function formatNumber(
    value,
    decimals = 2
) {

    const number =
        Number(value);

    if (
        !Number.isFinite(number)
    ) {

        return "—";
    }


    return number.toFixed(
        decimals
    );
}


function escapeHtml(
    value
) {

    return String(value ?? "")
        .replace(
            /&/g,
            "&amp;"
        )
        .replace(
            /</g,
            "&lt;"
        )
        .replace(
            />/g,
            "&gt;"
        )
        .replace(
            /"/g,
            "&quot;"
        )
        .replace(
            /'/g,
            "&#039;"
        );
}


/* =========================================================
   GLOBAL FUNCTIONS
   ========================================================= */

window.launchDashboard =
    launchDashboard;

window.launchDashboardWithQuery =
    launchDashboardWithQuery;

window.scrollToAsk =
    scrollToAsk;

window.useLandingSuggestion =
    useLandingSuggestion;

window.runAnalysis =
    runAnalysis;


/* =========================================================
   INITIALIZATION
   ========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    () => {

        console.log(
            "================================="
        );

        console.log(
            "ORCA FRONTEND ONLINE"
        );

        console.log(
            "API:",
            API_URL
        );

        console.log(
            "================================="
        );


        /* Landing query */

        const landingQuery =
            document.getElementById(
                "landingQuery"
            );


        if (landingQuery) {

            landingQuery.addEventListener(
                "keydown",
                event => {

                    if (
                        event.key === "Enter" &&
                        !event.shiftKey
                    ) {

                        event.preventDefault();

                        launchDashboardWithQuery();
                    }
                }
            );
        }


        /* Dashboard query */

        const queryInput =
            document.getElementById(
                "queryInput"
            );


        if (queryInput) {

            queryInput.addEventListener(
                "keydown",
                event => {

                    if (
                        event.key === "Enter" &&
                        !event.shiftKey
                    ) {

                        event.preventDefault();

                        runAnalysis();
                    }
                }
            );
        }


        /* If dashboard is already visible */

        const dashboard =
            document.getElementById(
                "dashboardPage"
            );


        if (
            dashboard &&
            !dashboard.classList.contains(
                "hidden"
            )
        ) {

            setTimeout(
                initializeMap,
                300
            );
        }
    }
);
