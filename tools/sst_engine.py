from pathlib import Path

import xarray as xr
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_PATH = (
    PROJECT_ROOT /
    "data" /
    "regional_oisst.nc"
)


def _find_coordinate(ds, names):
    for name in names:
        if name in ds.coords or name in ds.dims:
            return name
    return None


def _find_sst_variable(ds):
    preferred = [
        "sst",
        "SST",
        "sea_surface_temperature"
    ]

    for name in preferred:
        if name in ds.data_vars:
            return name

    return None


def get_sst_timeseries(
    min_lat: float,
    max_lat: float,
    min_lon: float,
    max_lon: float
) -> dict:

    if not DATA_PATH.exists():
        return {
            "status": "error",
            "message": f"SST dataset missing at {DATA_PATH}"
        }

    try:

        lat_bottom, lat_top = sorted(
            [float(min_lat), float(max_lat)]
        )

        lon_left, lon_right = sorted(
            [float(min_lon), float(max_lon)]
        )

        # India-region safety bounds
        lat_bottom = max(lat_bottom, 4.0)
        lat_top = min(lat_top, 25.0)

        lon_left = max(lon_left, 65.0)
        lon_right = min(lon_right, 95.0)

        if lat_bottom >= lat_top:
            return {
                "status": "error",
                "message": "Invalid latitude bounding box."
            }

        if lon_left >= lon_right:
            return {
                "status": "error",
                "message": "Invalid longitude bounding box."
            }

        with xr.open_dataset(DATA_PATH) as ds:

            lat_name = _find_coordinate(
                ds,
                ["latitude", "lat"]
            )

            lon_name = _find_coordinate(
                ds,
                ["longitude", "lon"]
            )

            sst_name = _find_sst_variable(ds)

            if not lat_name or not lon_name:
                return {
                    "status": "error",
                    "message": (
                        "Latitude/longitude coordinates "
                        "not found in SST dataset."
                    )
                }

            if not sst_name:
                return {
                    "status": "error",
                    "message": (
                        "SST variable not found in "
                        "dataset."
                    )
                }

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

            sliced = ds[sst_name].sel(
                {
                    lat_name: lat_slice,
                    lon_name: lon_slice
                }
            )

            values = np.asarray(
                sliced.values,
                dtype=float
            )

            valid_values = values[
                np.isfinite(values)
            ]

            if valid_values.size == 0:
                return {
                    "status": "error",
                    "message": (
                        "Selected bounding box "
                        "contains no valid SST data."
                    )
                }

            sst_mean = float(
                np.nanmean(valid_values)
            )

            sst_min = float(
                np.nanmin(valid_values)
            )

            sst_max = float(
                np.nanmax(valid_values)
            )

            # Use actual anomaly if the dataset contains it.
            anomaly = None

            if "anom" in ds.data_vars:

                anom_region = ds["anom"].sel(
                    {
                        lat_name: lat_slice,
                        lon_name: lon_slice
                    }
                )

                anom_values = np.asarray(
                    anom_region.values,
                    dtype=float
                )

                valid_anom = anom_values[
                    np.isfinite(anom_values)
                ]

                if valid_anom.size > 0:
                    anomaly = float(
                        np.nanmean(valid_anom)
                    )

            metrics = {
                "average_sst_celsius": round(
                    sst_mean,
                    2
                ),
                "min_sst_celsius": round(
                    sst_min,
                    2
                ),
                "max_sst_celsius": round(
                    sst_max,
                    2
                )
            }

            if anomaly is not None:

                metrics[
                    "temperature_anomaly_celsius"
                ] = round(anomaly, 2)

                metrics[
                    "heat_stress_indicator"
                ] = bool(anomaly > 1.0)

            else:

                metrics[
                    "temperature_anomaly_celsius"
                ] = None

                metrics[
                    "heat_stress_indicator"
                ] = None

            return {
                "status": "success",
                "function_name": "get_sst_timeseries",
                "source": "NOAA OISST",
                "requested_bounds": [
                    lat_bottom,
                    lat_top,
                    lon_left,
                    lon_right
                ],
                "metrics": metrics,
                "valid_pixel_count": int(
                    valid_values.size
                ),
                "analysis_type": (
                    "regional bounding-box statistics"
                ),
                "note": (
                    "Heat-stress indicator uses the "
                    "available SST anomaly. It is not "
                    "a formal Degree Heating Week calculation."
                )
            }

    except Exception as e:

        return {
            "status": "error",
            "message": (
                f"Failed to process SST data: {str(e)}"
            )
        }


if __name__ == "__main__":

    print(
        get_sst_timeseries(
            10,
            20,
            72,
            82
        )
    )