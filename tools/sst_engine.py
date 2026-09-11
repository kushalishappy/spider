import os
import xarray as xr
import numpy as np

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "regional_oisst.nc")

def get_sst_timeseries(min_lat: float, max_lat: float, min_lon: float, max_lon: float) -> dict:
    if not os.path.exists(DATA_PATH):
        return {"status": "error", "message": f"Dataset missing at {DATA_PATH}"}

    try:
        # 1. Coordinate Normalization & Clamping
        lat_bottom, lat_top = sorted([float(min_lat), float(max_lat)])
        lon_left, lon_right = sorted([float(min_lon), float(max_lon)])

        lat_bottom = max(lat_bottom, 4.0)
        lat_top = min(lat_top, 25.0)
        lon_left = max(lon_left, 65.0)
        lon_right = min(lon_right, 95.0)

        # 2. Dataset Slicing
        ds = xr.open_dataset(DATA_PATH)
        sliced = ds.sel(
            latitude=slice(lat_bottom, lat_top),
            longitude=slice(lon_left, lon_right)
        )

        if sliced['sst'].size == 0:
            return {"status": "error", "message": "Selected bounding box returned no data cells."}

        # 3. Safe Statistical Calculations (NaN Handling)
        sst_mean = float(np.nanmean(sliced['sst'].values))
        sst_min = float(np.nanmin(sliced['sst'].values))
        sst_max = float(np.nanmax(sliced['sst'].values))

        if 'anom' in sliced:
            anom_mean = float(np.nanmean(sliced['anom'].values))
        else:
            anom_mean = round(sst_mean - 28.0, 2)

        # 4. Degree Heating Weeks (DHW) Calculation
        daily_spatial_mean = sliced['sst'].mean(dim=['latitude', 'longitude'], skipna=True)
        hot_spots = daily_spatial_mean - 29.5
        valid_hot_spots = xr.where(hot_spots >= 1.0, hot_spots, 0.0)
        dhw_value = float((valid_hot_spots.sum() / 7.0).values)

        return {
            "status": "success",
            "function_name": "get_sst_timeseries",
            "requested_bounds": [lat_bottom, lat_top, lon_left, lon_right],
            "metrics": {
                "average_sst_celsius": round(sst_mean, 2),
                "min_sst_celsius": round(sst_min, 2),
                "max_sst_celsius": round(sst_max, 2),
                "temperature_anomaly_celsius": round(anom_mean, 2),
                "degree_heating_weeks_dhw": round(dhw_value, 2),
                "heat_stress_alert": bool(dhw_value > 4.0 or anom_mean > 1.0)
            }
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}

# Execution block for local testing
if __name__ == "__main__":
    print("--- FINAL INTEGRATION TEST ---")
    print(get_sst_timeseries(min_lat=8.0, max_lat=15.0, min_lon=70.0, max_lon=78.0))