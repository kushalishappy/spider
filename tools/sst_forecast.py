from pathlib import Path
from typing import Any, Dict

import numpy as np
import xarray as xr


# ============================================================
# ORCA - SST Trend-Based Outlook
# Data source: NOAA OISST
# ============================================================

DATA_PATH = Path(r"E:\ORCA\data\regional_oisst.nc")


# ------------------------------------------------------------
# Helper: find a coordinate by common names
# ------------------------------------------------------------
def _find_coordinate(ds: xr.Dataset, candidates):
    """
    Find a coordinate/dimension using common possible names.
    """
    for name in candidates:
        if name in ds.coords:
            return name

    for name in candidates:
        if name in ds.dims:
            return name

    return None


# ------------------------------------------------------------
# Helper: find SST variable
# ------------------------------------------------------------
def _find_sst_variable(ds: xr.Dataset):
    """
    Find the SST variable using common NOAA OISST variable names.
    """
    candidates = [
        "sst",
        "SST",
        "sea_surface_temperature",
        "analysed_sst",
        "tos",
    ]

    for name in candidates:
        if name in ds.data_vars:
            return name

    # Fallback:
    # Look for a variable whose name contains 'sst'.
    for name in ds.data_vars:
        if "sst" in name.lower():
            return name

    return None


# ------------------------------------------------------------
# Helper: normalize longitude to [-180, 180]
# ------------------------------------------------------------
def _normalize_longitude(ds: xr.Dataset, lon_name: str):
    """
    Normalize longitude coordinates to [-180, 180].
    """
    lon = ds[lon_name]

    normalized_lon = ((lon + 180) % 360) - 180

    ds = ds.assign_coords(
        {
            lon_name: normalized_lon
        }
    )

    ds = ds.sortby(lon_name)

    return ds


# ------------------------------------------------------------
# Helper: convert SST to Celsius if needed
# ------------------------------------------------------------
def _convert_sst_to_celsius(
    data: xr.DataArray,
    variable_name: str,
) -> xr.DataArray:
    """
    Convert SST to Celsius when values appear to be Kelvin.

    NOAA OISST is normally represented in Celsius, but this
    function protects the pipeline against Kelvin-formatted
    datasets.
    """

    units = str(data.attrs.get("units", "")).lower()

    if "kelvin" in units or units in {"k", "degk"}:
        return data - 273.15

    # If metadata is missing, use a conservative value check.
    try:
        sample = float(data.mean(skipna=True).values)

        if sample > 100:
            return data - 273.15
    except Exception:
        pass

    return data


# ------------------------------------------------------------
# Helper: convert time coordinate to datetime
# ------------------------------------------------------------
def _prepare_time(ds: xr.Dataset, time_name: str):
    """
    Ensure the time coordinate can be sorted chronologically.
    """
    try:
        ds = ds.sortby(time_name)
    except Exception:
        pass

    return ds


# ------------------------------------------------------------
# Helper: regional mean
# ------------------------------------------------------------
def _regional_mean_timeseries(
    data: xr.DataArray,
    lat_name: str,
    lon_name: str,
):
    """
    Calculate spatial mean for every time step.

    The result should contain one SST value per time step.
    """

    spatial_dims = [
        dim
        for dim in [lat_name, lon_name]
        if dim in data.dims
    ]

    if not spatial_dims:
        raise ValueError(
            "Latitude/longitude dimensions were not found in SST data."
        )

    return data.mean(
        dim=spatial_dims,
        skipna=True,
    )


# ------------------------------------------------------------
# Main function
# ------------------------------------------------------------
def get_sst_trend_forecast(
    min_lat: float,
    max_lat: float,
    min_lon: float,
    max_lon: float,
    forecast_days: int = 7,
    lookback_days: int = 14,
) -> Dict[str, Any]:
    """
    Generate a short-term SST trend-based outlook.

    This is NOT an operational numerical weather/ocean forecast.

    It:
      1. Loads NOAA OISST data.
      2. Extracts the requested bounding box.
      3. Calculates regional mean SST over time.
      4. Uses the most recent observations.
      5. Fits a simple linear trend.
      6. Extrapolates that trend for the requested number
         of future days.

    Parameters
    ----------
    min_lat : float
        Minimum latitude.

    max_lat : float
        Maximum latitude.

    min_lon : float
        Minimum longitude.

    max_lon : float
        Maximum longitude.

    forecast_days : int
        Number of future days to extrapolate.

    lookback_days : int
        Number of recent days used to calculate the trend.

    Returns
    -------
    dict
        JSON-compatible forecast result.
    """

    # ========================================================
    # Validate inputs
    # ========================================================

    try:
        min_lat = float(min_lat)
        max_lat = float(max_lat)
        min_lon = float(min_lon)
        max_lon = float(max_lon)
        forecast_days = int(forecast_days)
        lookback_days = int(lookback_days)
    except (TypeError, ValueError) as exc:
        return {
            "status": "error",
            "source": "NOAA OISST",
            "error": f"Invalid input parameters: {exc}",
        }

    if min_lat > max_lat:
        min_lat, max_lat = max_lat, min_lat

    if min_lon > max_lon:
        min_lon, max_lon = max_lon, min_lon

    if forecast_days <= 0:
        return {
            "status": "error",
            "source": "NOAA OISST",
            "error": "forecast_days must be greater than zero.",
        }

    if lookback_days < 2:
        return {
            "status": "error",
            "source": "NOAA OISST",
            "error": "lookback_days must be at least 2.",
        }

    # Keep forecast length reasonable for this simple
    # trend-based method.
    forecast_days = min(forecast_days, 30)

    # ========================================================
    # Check dataset
    # ========================================================

    if not DATA_PATH.exists():
        return {
            "status": "error",
            "source": "NOAA OISST",
            "error": f"Dataset not found: {DATA_PATH}",
        }

    # ========================================================
    # Open dataset
    # ========================================================

    try:
        ds = xr.open_dataset(DATA_PATH)
    except Exception as exc:
        return {
            "status": "error",
            "source": "NOAA OISST",
            "error": f"Could not open NOAA OISST dataset: {exc}",
        }

    try:
        # ====================================================
        # Detect coordinates
        # ====================================================

        lat_name = _find_coordinate(
            ds,
            [
                "lat",
                "latitude",
                "Latitude",
                "LAT",
            ],
        )

        lon_name = _find_coordinate(
            ds,
            [
                "lon",
                "longitude",
                "Longitude",
                "LON",
            ],
        )

        time_name = _find_coordinate(
            ds,
            [
                "time",
                "Time",
                "TIME",
                "date",
            ],
        )

        if lat_name is None:
            return {
                "status": "error",
                "source": "NOAA OISST",
                "error": "Latitude coordinate not found.",
            }

        if lon_name is None:
            return {
                "status": "error",
                "source": "NOAA OISST",
                "error": "Longitude coordinate not found.",
            }

        if time_name is None:
            return {
                "status": "error",
                "source": "NOAA OISST",
                "error": "Time coordinate not found.",
            }

        # ====================================================
        # Detect SST variable
        # ====================================================

        sst_name = _find_sst_variable(ds)

        if sst_name is None:
            return {
                "status": "error",
                "source": "NOAA OISST",
                "error": "SST variable not found in dataset.",
            }

        # ====================================================
        # Normalize longitude
        # ====================================================

        ds = _normalize_longitude(
            ds,
            lon_name,
        )

        # ====================================================
        # Prepare time
        # ====================================================

        ds = _prepare_time(
            ds,
            time_name,
        )

        # ====================================================
        # Normalize longitude request
        # ====================================================

        min_lon = ((min_lon + 180) % 360) - 180
        max_lon = ((max_lon + 180) % 360) - 180

        # ====================================================
        # Check requested region against dataset
        # ====================================================

        lat_values = np.asarray(
            ds[lat_name].values,
            dtype=float,
        )

        lon_values = np.asarray(
            ds[lon_name].values,
            dtype=float,
        )

        dataset_min_lat = float(np.nanmin(lat_values))
        dataset_max_lat = float(np.nanmax(lat_values))

        dataset_min_lon = float(np.nanmin(lon_values))
        dataset_max_lon = float(np.nanmax(lon_values))

        # Clamp latitude to dataset bounds.
        clipped_min_lat = max(
            min_lat,
            dataset_min_lat,
        )

        clipped_max_lat = min(
            max_lat,
            dataset_max_lat,
        )

        # Clamp longitude to dataset bounds.
        clipped_min_lon = max(
            min_lon,
            dataset_min_lon,
        )

        clipped_max_lon = min(
            max_lon,
            dataset_max_lon,
        )

        if clipped_min_lat > clipped_max_lat:
            return {
                "status": "error",
                "source": "NOAA OISST",
                "error": "Requested latitude range does not overlap dataset.",
            }

        if clipped_min_lon > clipped_max_lon:
            return {
                "status": "error",
                "source": "NOAA OISST",
                "error": "Requested longitude range does not overlap dataset.",
            }

        # ====================================================
        # Extract requested bounding box
        # ====================================================

        regional = ds[sst_name].sel(
            {
                lat_name: slice(
                    clipped_min_lat,
                    clipped_max_lat,
                ),
                lon_name: slice(
                    clipped_min_lon,
                    clipped_max_lon,
                ),
            }
        )

        if regional.size == 0:
            return {
                "status": "error",
                "source": "NOAA OISST",
                "error": "No SST data found inside requested bounding box.",
            }

        # ====================================================
        # Convert SST to Celsius
        # ====================================================

        regional = _convert_sst_to_celsius(
            regional,
            sst_name,
        )

        # ====================================================
        # Calculate regional time series
        # ====================================================

        regional_series = _regional_mean_timeseries(
            regional,
            lat_name,
            lon_name,
        )

        # Remove completely invalid time steps.
        try:
            regional_series = regional_series.dropna(
                dim=time_name,
                how="all",
            )
        except Exception:
            pass

        if regional_series.size == 0:
            return {
                "status": "error",
                "source": "NOAA OISST",
                "error": "No valid SST observations were found.",
            }

        # ====================================================
        # Extract time values and SST values
        # ====================================================

        time_values = np.asarray(
            regional_series[time_name].values
        )

        sst_values = np.asarray(
            regional_series.values,
            dtype=float,
        )

        # Flatten in case xarray retains an unexpected
        # singleton dimension.
        sst_values = np.asarray(
            sst_values
        ).reshape(-1)

        time_values = np.asarray(
            time_values
        ).reshape(-1)

        # ====================================================
        # Remove NaN / infinite values
        # ====================================================

        valid_mask = (
            np.isfinite(sst_values)
        )

        sst_values = sst_values[valid_mask]
        time_values = time_values[valid_mask]

        if len(sst_values) < 2:
            return {
                "status": "error",
                "source": "NOAA OISST",
                "error": (
                    "Insufficient valid SST observations "
                    "to calculate a trend."
                ),
            }

        # ====================================================
        # Keep the most recent observations
        # ====================================================

        # The dataset is expected to be daily, but we do not
        # assume perfect daily spacing.
        recent_count = min(
            lookback_days,
            len(sst_values),
        )

        recent_sst = sst_values[-recent_count:]
        recent_time = time_values[-recent_count:]

        if len(recent_sst) < 2:
            return {
                "status": "error",
                "source": "NOAA OISST",
                "error": "Not enough recent observations for trend analysis.",
            }

        # ====================================================
        # Convert times to datetime64
        # ====================================================

        try:
            recent_time_dt = np.asarray(
                recent_time,
                dtype="datetime64[ns]",
            )
        except Exception as exc:
            return {
                "status": "error",
                "source": "NOAA OISST",
                "error": f"Could not interpret time values: {exc}",
            }

        # ====================================================
        # Calculate elapsed days
        # ========================================================

        elapsed_days = (
            (
                recent_time_dt
                - recent_time_dt[0]
            )
            / np.timedelta64(1, "D")
        ).astype(float)

        # Remove duplicate timestamps if present.
        unique_mask = np.concatenate(
            [
                np.array([True]),
                np.diff(elapsed_days) > 0,
            ]
        )

        elapsed_days = elapsed_days[unique_mask]
        recent_sst = recent_sst[unique_mask]
        recent_time_dt = recent_time_dt[unique_mask]

        if len(recent_sst) < 2:
            return {
                "status": "error",
                "source": "NOAA OISST",
                "error": "Insufficient unique timestamps for trend analysis.",
            }

        # ====================================================
        # Linear regression
        # ====================================================

        try:
            slope, intercept = np.polyfit(
                elapsed_days,
                recent_sst,
                1,
            )
        except Exception as exc:
            return {
                "status": "error",
                "source": "NOAA OISST",
                "error": f"Trend calculation failed: {exc}",
            }

        # ====================================================
        # Calculate trend information
        # ====================================================

        trend_c_per_day = float(slope)

        trend_c_per_week = float(
            slope * 7.0
        )

        if trend_c_per_day > 0.02:
            trend_direction = "warming"
        elif trend_c_per_day < -0.02:
            trend_direction = "cooling"
        else:
            trend_direction = "approximately stable"

        # ====================================================
        # Generate future dates
        # ====================================================

        last_observation_date = recent_time_dt[-1]

        forecast_dates = [
            last_observation_date
            + np.timedelta64(day, "D")
            for day in range(
                1,
                forecast_days + 1,
            )
        ]

        # ====================================================
        # Generate trend-based forecast
        # ====================================================

        last_elapsed = elapsed_days[-1]

        forecast_elapsed = (
            last_elapsed
            + np.arange(
                1,
                forecast_days + 1,
                dtype=float,
            )
        )

        forecast_values = (
            intercept
            + slope * forecast_elapsed
        )

        forecast_values = np.asarray(
            forecast_values,
            dtype=float,
        )

        # ====================================================
        # Recent observed values
        # ====================================================

        observed_series = []

        for date_value, temperature in zip(
            recent_time_dt,
            recent_sst,
        ):
            observed_series.append(
                {
                    "date": str(
                        date_value.astype(
                            "datetime64[D]"
                        )
                    ),
                    "sst_celsius": round(
                        float(temperature),
                        3,
                    ),
                }
            )

        # ====================================================
        # Forecast values
        # ====================================================

        forecast_series = []

        for date_value, temperature in zip(
            forecast_dates,
            forecast_values,
        ):
            forecast_series.append(
                {
                    "date": str(
                        date_value.astype(
                            "datetime64[D]"
                        )
                    ),
                    "sst_celsius": round(
                        float(temperature),
                        3,
                    ),
                }
            )

        # ====================================================
        # Calculate start/end outlook values
        # ====================================================

        current_sst = float(
            recent_sst[-1]
        )

        first_forecast_sst = float(
            forecast_values[0]
        )

        last_forecast_sst = float(
            forecast_values[-1]
        )

        forecast_change = (
            last_forecast_sst
            - current_sst
        )

        # ====================================================
        # Final result
        # ====================================================

        return {
            "status": "success",
            "source": "NOAA OISST",
            "analysis_type": "regional SST trend-based outlook",
            "requested_bounds": [
                min_lat,
                max_lat,
                min_lon,
                max_lon,
            ],
            "used_bounds": [
                clipped_min_lat,
                clipped_max_lat,
                clipped_min_lon,
                clipped_max_lon,
            ],
            "lookback_days": int(
                recent_count
            ),
            "forecast_days": int(
                forecast_days
            ),
            "last_observation_date": str(
                last_observation_date.astype(
                    "datetime64[D]"
                )
            ),
            "current_sst_celsius": round(
                current_sst,
                3,
            ),
            "trend": {
                "direction": trend_direction,
                "celsius_per_day": round(
                    trend_c_per_day,
                    5,
                ),
                "celsius_per_week": round(
                    trend_c_per_week,
                    4,
                ),
            },
            "outlook": {
                "first_day_sst_celsius": round(
                    first_forecast_sst,
                    3,
                ),
                "last_day_sst_celsius": round(
                    last_forecast_sst,
                    3,
                ),
                "change_over_outlook_celsius": round(
                    forecast_change,
                    3,
                ),
            },
            "observed_recent": observed_series,
            "forecast": forecast_series,
            "method": (
                "Linear trend extrapolation using recent "
                "regional NOAA OISST observations."
            ),
            "scientific_note": (
                "This is a project-level trend-based outlook, "
                "not an operational ocean forecast. "
                "It should be interpreted together with "
                "the observed data and its uncertainty."
            ),
        }

    except Exception as exc:
        return {
            "status": "error",
            "source": "NOAA OISST",
            "error": str(exc),
        }

    finally:
        # Always close the dataset.
        try:
            ds.close()
        except Exception:
            pass


# ------------------------------------------------------------
# Local test
# ------------------------------------------------------------
if __name__ == "__main__":
    result = get_sst_trend_forecast(
        10.0,
        20.0,
        72.0,
        82.0,
        forecast_days=7,
        lookback_days=14,
    )

    print("\n" + "=" * 60)
    print("ORCA - SST TREND-BASED OUTLOOK TEST")
    print("=" * 60)

    print(result)

    print("=" * 60)