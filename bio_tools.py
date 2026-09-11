import os
from pathlib import Path

import numpy as np
import xarray as xr
from dotenv import load_dotenv
from google import genai


# ============================================================
# ENVIRONMENT / GEMINI
# ============================================================

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent

DATA_PATH = PROJECT_ROOT / "india_chlorophyll.nc"


# ============================================================
# DATASET HELPERS
# ============================================================

def _find_coordinate(ds, names):
    """Find the first matching coordinate/dimension name."""

    for name in names:
        if name in ds.coords or name in ds.dims:
            return name

    return None


def _find_chlorophyll_variable(ds):
    """Find the chlorophyll data variable."""

    preferred_names = [
        "CHL",
        "chlor_a",
        "chlorophyll",
        "chlorophyll_a",
        "CHLA",
    ]

    for name in preferred_names:
        if name in ds.data_vars:
            return name

    if ds.data_vars:
        return list(ds.data_vars.keys())[0]

    return None


# ============================================================
# CHLOROPHYLL CLASSIFICATION
# ============================================================

def _classify_chlorophyll(value):
    """
    Simple project screening classification.

    These thresholds are NOT an official HAB diagnosis.
    """

    if value >= 5.0:
        return "High chlorophyll screening level"

    elif value >= 2.0:
        return "Elevated chlorophyll screening level"

    else:
        return "Normal chlorophyll screening level"


# ============================================================
# CHLOROPHYLL POINT
# ============================================================

def get_chlorophyll_context(
    lat: float,
    lon: float,
    nc_path: str | None = None
) -> dict:
    """
    Extract chlorophyll near a single coordinate.
    """

    path = Path(nc_path) if nc_path else DATA_PATH

    if not path.exists():
        return {
            "status": "error",
            "message": f"Chlorophyll dataset missing at {path}"
        }

    try:

        with xr.open_dataset(path) as ds:

            lat_name = _find_coordinate(
                ds,
                ["latitude", "lat", "y"]
            )

            lon_name = _find_coordinate(
                ds,
                ["longitude", "lon", "x"]
            )

            var_name = _find_chlorophyll_variable(ds)

            if not lat_name or not lon_name:
                return {
                    "status": "error",
                    "message": "Latitude/longitude coordinates not found."
                }

            if not var_name:
                return {
                    "status": "error",
                    "message": "Chlorophyll variable not found."
                }

            pixel = ds[var_name].sel(
                {
                    lat_name: float(lat),
                    lon_name: float(lon)
                },
                method="nearest"
            )

            values = np.asarray(
                pixel.values,
                dtype=float
            )

            valid_values = values[
                np.isfinite(values)
            ]

            if valid_values.size == 0:
                return {
                    "status": "no_data",
                    "coordinates": {
                        "lat": float(lat),
                        "lon": float(lon)
                    },
                    "chlor_a_mg_m3": None,
                    "bloom_risk": "Indeterminate"
                }

            value = float(
                np.nanmean(valid_values)
            )

            return {
                "status": "success",
                "source": "Copernicus Marine",
                "coordinates": {
                    "lat": float(lat),
                    "lon": float(lon)
                },
                "chlor_a_mg_m3": round(value, 2),
                "bloom_risk": _classify_chlorophyll(value),
                "analysis_type": "nearest valid pixel"
            }

    except Exception as e:

        return {
            "status": "error",
            "message": (
                f"Failed to parse chlorophyll data: {str(e)}"
            )
        }


# ============================================================
# CHLOROPHYLL BOUNDING BOX
# ============================================================

def get_chlorophyll_bbox(
    min_lat: float,
    max_lat: float,
    min_lon: float,
    max_lon: float,
    nc_path: str | None = None
) -> dict:
    """
    Calculate regional chlorophyll statistics
    for a selected latitude/longitude bounding box.
    """

    path = Path(nc_path) if nc_path else DATA_PATH

    if not path.exists():
        return {
            "status": "error",
            "message": f"Chlorophyll dataset missing at {path}"
        }

    try:

        # Normalize coordinates
        lat_bottom, lat_top = sorted(
            [
                float(min_lat),
                float(max_lat)
            ]
        )

        lon_left, lon_right = sorted(
            [
                float(min_lon),
                float(max_lon)
            ]
        )

        with xr.open_dataset(path) as ds:

            lat_name = _find_coordinate(
                ds,
                ["latitude", "lat", "y"]
            )

            lon_name = _find_coordinate(
                ds,
                ["longitude", "lon", "x"]
            )

            var_name = _find_chlorophyll_variable(ds)

            if not lat_name or not lon_name:
                return {
                    "status": "error",
                    "message": "Latitude/longitude coordinates not found."
                }

            if not var_name:
                return {
                    "status": "error",
                    "message": "Chlorophyll variable not found."
                }

            data = ds[var_name]

            lat_values = ds[lat_name].values
            lon_values = ds[lon_name].values

            # Latitude direction
            if lat_values[0] <= lat_values[-1]:

                lat_slice = slice(
                    lat_bottom,
                    lat_top
                )

            else:

                lat_slice = slice(
                    lat_top,
                    lat_bottom
                )

            # Longitude direction
            if lon_values[0] <= lon_values[-1]:

                lon_slice = slice(
                    lon_left,
                    lon_right
                )

            else:

                lon_slice = slice(
                    lon_right,
                    lon_left
                )

            region = data.sel(
                {
                    lat_name: lat_slice,
                    lon_name: lon_slice
                }
            )

            values = np.asarray(
                region.values,
                dtype=float
            )

            valid_values = values[
                np.isfinite(values)
            ]

            if valid_values.size == 0:
                return {
                    "status": "no_data",
                    "requested_bounds": [
                        lat_bottom,
                        lat_top,
                        lon_left,
                        lon_right
                    ],
                    "chlor_a_mg_m3": None,
                    "bloom_risk": "Indeterminate",
                    "valid_pixel_count": 0
                }

            mean_value = float(
                np.nanmean(valid_values)
            )

            min_value = float(
                np.nanmin(valid_values)
            )

            max_value = float(
                np.nanmax(valid_values)
            )

            return {
                "status": "success",
                "source": "Copernicus Marine",
                "requested_bounds": [
                    lat_bottom,
                    lat_top,
                    lon_left,
                    lon_right
                ],
                "chlor_a_mg_m3": round(
                    mean_value,
                    2
                ),
                "min_chlor_a_mg_m3": round(
                    min_value,
                    2
                ),
                "max_chlor_a_mg_m3": round(
                    max_value,
                    2
                ),
                "valid_pixel_count": int(
                    valid_values.size
                ),
                "bloom_risk": _classify_chlorophyll(
                    mean_value
                ),
                "analysis_type": (
                    "regional bounding-box mean"
                ),
                "screening_note": (
                    "Classification is a simple project "
                    "screening indicator and is not a "
                    "confirmed harmful algal bloom diagnosis."
                )
            }

    except Exception as e:

        return {
            "status": "error",
            "message": (
                f"Failed to calculate regional "
                f"chlorophyll: {str(e)}"
            )
        }


# ============================================================
# RULE-BASED MARINE ADVISORY
# ============================================================

def get_incois_advisory(
    sst_summary=None,
    chlorophyll_summary=None,
    forecast_summary=None,
):
    """
    Generate a marine advisory from SST,
    chlorophyll, and forecast information.
    """

    advisories = []

    # --------------------------------------------------------
    # SST
    # --------------------------------------------------------

    if isinstance(sst_summary, dict):

        avg_sst = (
            sst_summary.get("mean")
            or sst_summary.get("avg_sst")
            or sst_summary.get("average")
        )

        if avg_sst is not None:

            try:

                avg_sst = float(avg_sst)

                if avg_sst >= 30:

                    advisories.append(
                        "Elevated sea-surface temperature detected."
                    )

                elif avg_sst >= 28:

                    advisories.append(
                        "Sea-surface temperature is relatively warm."
                    )

                else:

                    advisories.append(
                        "Sea-surface temperature is within a moderate range."
                    )

            except (ValueError, TypeError):

                pass

    # --------------------------------------------------------
    # CHLOROPHYLL
    # --------------------------------------------------------

    if isinstance(chlorophyll_summary, dict):

        chl = (
            chlorophyll_summary.get("mean")
            or chlorophyll_summary.get("avg_chlorophyll")
            or chlorophyll_summary.get("chlorophyll")
            or chlorophyll_summary.get("chlor_a_mg_m3")
        )

        if chl is not None:

            try:

                chl = float(chl)

                if chl >= 10:

                    advisories.append(
                        "High chlorophyll concentration detected. "
                        "Monitor for possible algal-bloom conditions."
                    )

                elif chl >= 5:

                    advisories.append(
                        "Elevated chlorophyll concentration detected."
                    )

                else:

                    advisories.append(
                        "Chlorophyll concentration does not indicate "
                        "an elevated bloom signal."
                    )

            except (ValueError, TypeError):

                pass

    # --------------------------------------------------------
    # FORECAST
    # --------------------------------------------------------

    if isinstance(forecast_summary, dict):

        trend = str(
            forecast_summary.get("trend")
            or forecast_summary.get("forecast_trend")
            or ""
        ).lower()

        if (
            "increas" in trend
            or "warming" in trend
        ):

            advisories.append(
                "Forecast indicates a warming tendency. "
                "Continue monitoring the region."
            )

    # --------------------------------------------------------
    # DEFAULT
    # --------------------------------------------------------

    if not advisories:

        advisories.append(
            "No major combined ocean-condition signal was identified."
        )

    return {
        "status": "success",
        "advisory": " ".join(advisories),
        "recommendation": (
            "Continue monitoring SST and chlorophyll conditions "
            "and consult official INCOIS advisories for "
            "operational decisions."
        ),
    }


# ============================================================
# GEMINI AI MARINE ADVISORY
# ============================================================

def generate_gemini_advisory(
    sst_summary=None,
    chlorophyll_summary=None,
    forecast_summary=None,
):
    """
    Generate an AI-assisted marine advisory using
    the current Google GenAI Python SDK.

    Gemini receives only the specialist evidence
    retrieved by ORCA.
    """

    if not GEMINI_API_KEY:

        return {
            "status": "error",
            "message": "GEMINI_API_KEY not found in .env"
        }

    prompt = f"""
You are ORCA, an ocean reasoning and coastal advisory assistant.

Generate a concise marine advisory using ONLY the evidence below.

SST specialist evidence:
{sst_summary}

Chlorophyll specialist evidence:
{chlorophyll_summary}

SST forecast evidence:
{forecast_summary}

Requirements:

1. Summarize the observed marine conditions.
2. Mention SST and chlorophyll when available.
3. Mention the forecast trend when available.
4. Assess whether the evidence suggests elevated marine/HAB concern.
5. Do NOT claim a confirmed harmful algal bloom.
6. Do NOT invent missing measurements.
7. Clearly state that this is a screening-level advisory.
8. Recommend consulting official INCOIS advisories for operational decisions.

Return exactly these sections:

Marine condition:
Risk assessment:
Forecast outlook:
Recommendation:
"""

    try:

        # Current Google GenAI SDK
        client = genai.Client(
            api_key=GEMINI_API_KEY
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        text = getattr(
            response,
            "text",
            None
        )

        if not text:

            return {
                "status": "error",
                "message": "Gemini returned an empty response."
            }

        return {
            "status": "success",
            "provider": "Google Gemini",
            "advisory": text.strip()
        }

    except Exception as e:

        return {
            "status": "error",
            "message": (
                f"Gemini advisory generation failed: {str(e)}"
            )
        }


# ============================================================
# LOCAL TEST
# ============================================================

if __name__ == "__main__":

    print("\n--- POINT TEST ---")

    print(
        get_chlorophyll_context(
            15.29,
            73.50
        )
    )

    print("\n--- BBOX TEST ---")

    print(
        get_chlorophyll_bbox(
            10,
            20,
            72,
            82
        )
    )