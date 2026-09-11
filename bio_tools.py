from pathlib import Path

import xarray as xr
import numpy as np


# Project root: E:\ORCA
PROJECT_ROOT = Path(__file__).resolve().parent

# Chlorophyll dataset
DATA_PATH = PROJECT_ROOT / "india_chlorophyll.nc"


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

    # Fallback: first data variable
    if ds.data_vars:
        return list(ds.data_vars.keys())[0]

    return None


def _classify_chlorophyll(value):
    """
    Simple screening classification.

    NOTE:
    These thresholds are project screening thresholds,
    not an official HAB diagnostic.
    """

    if value >= 5.0:
        return "High chlorophyll screening level"
    elif value >= 2.0:
        return "Elevated chlorophyll screening level"
    else:
        return "Normal chlorophyll screening level"


def get_chlorophyll_context(
    lat: float,
    lon: float,
    nc_path: str | None = None
) -> dict:
    """
    Extract chlorophyll near a single coordinate.

    Kept for point-based queries.
    For map/bounding-box queries use get_chlorophyll_bbox().
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

            values = np.asarray(pixel.values, dtype=float)

            valid_values = values[np.isfinite(values)]

            if valid_values.size == 0:
                return {
                    "status": "no_data",
                    "coordinates": {
                        "lat": lat,
                        "lon": lon
                    },
                    "chlor_a_mg_m3": None,
                    "bloom_risk": "Indeterminate"
                }

            value = float(np.nanmean(valid_values))

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
            "message": f"Failed to parse chlorophyll data: {str(e)}"
        }


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
            [float(min_lat), float(max_lat)]
        )

        lon_left, lon_right = sorted(
            [float(min_lon), float(max_lon)]
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

            # Handle datasets where latitude is descending
            lat_values = ds[lat_name].values
            lon_values = ds[lon_name].values

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
                "chlor_a_mg_m3": round(mean_value, 2),
                "min_chlor_a_mg_m3": round(min_value, 2),
                "max_chlor_a_mg_m3": round(max_value, 2),
                "valid_pixel_count": int(
                    valid_values.size
                ),
                "bloom_risk": _classify_chlorophyll(
                    mean_value
                ),
                "analysis_type": "regional bounding-box mean",
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