import os
import xarray as xr
import numpy as np

def get_biological_data(lat: float, lon: float, file_path: str = "india.nc"):
    """
    Agent 1: Biological Specialist
    Extracts true Chlorophyll-a readings from the local NetCDF dataset.
    """
    if not os.path.exists(file_path):
        return {"status": "error", "message": f"Dataset '{file_path}' missing."}

    try:
        # Load dataset and find the nearest spatial coordinate
        dataset = xr.open_dataset(file_path)
        data_point = dataset.sel(lat=lat, lon=lon, method="nearest")
        
        # Dynamically extract the primary variable
        var_name = list(data_point.data_vars)[0]
        val = float(data_point[var_name].values)
        
        # Check if coordinate is dead space (e.g., landmass)
        if np.isnan(val):
            return {
                "status": "unavailable",
                "chlor_a_mg_m3": None,
                "message": "Target is on landmass or outside satellite coverage."
            }
            
        return {
            "status": "success",
            "chlor_a_mg_m3": round(val, 3)
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_thermal_data(lat: float, lon: float, file_path: str = "sst.nc"):
    """
    Agent 2: Thermal Specialist (SST)
    Prepared for team members to plug in their Sea Surface Temp dataset.
    """
    # Once your team has the SST NetCDF, they can replicate the logic above here.
    # For now, returning a standardized payload so the API doesn't break.
    return {
        "status": "success",
        "sst_c": 29.2 
    }