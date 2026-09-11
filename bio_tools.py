import xarray as xr
import numpy as np

def get_chlorophyll_context(lat: float, lon: float, nc_path: str = "india_chlorophyll.nc") -> dict:
    try:
        ds = xr.open_dataset(nc_path)
        
        # Identify the chlorophyll variable (usually 'CHL' or similar)
        var_name = "CHL" if "CHL" in ds.data_vars else list(ds.data_vars.keys())[0]
        
        # Select nearest pixel by latitude and longitude
        pixel = ds[var_name].sel(latitude=lat, longitude=lon, method="nearest")
        
        # Flatten array to handle the extra 'time' dimension
        raw_val = float(pixel.values.flatten()[0])

        # Handle land pixels or nodata
        if np.isnan(raw_val):
            return {
                "source": "Copernicus Marine L4",
                "coordinates": {"lat": lat, "lon": lon},
                "status": "No data (land pixel or obstruction)",
                "chlor_a_mg_m3": None,
                "bloom_risk": "Indeterminate"
            }

        val = round(raw_val, 2)
        
        # Ecological risk thresholds
        if val >= 5.0:
            risk = "High Risk (Algal bloom likely)"
        elif val >= 2.0:
            risk = "Elevated (Moderate plankton concentration)"
        else:
            risk = "Normal (Baseline coastal level)"

        return {
            "source": "Copernicus Marine L4",
            "coordinates": {"lat": lat, "lon": lon},
            "chlor_a_mg_m3": val,
            "bloom_risk": risk
        }

    except Exception as e:
        return {"error": f"Failed to parse Chlorophyll data: {str(e)}"}

def get_incois_advisory(region_name: str) -> dict:
    advisories = {
        "goa": {
            "zone": "Goa Coastal Waters",
            "pfz_status": "Favorable",
            "advisory_text": "Nutrient upwelling detected; favorable pelagic schooling.",
            "safety_alert": "Normal operations; no severe weather warnings."
        },
        "default": {
            "zone": "General Indian EEZ",
            "pfz_status": "Standard",
            "advisory_text": "Seasonal conditions normal for post-monsoon fishing.",
            "safety_alert": "None"
        }
    }
    key = region_name.strip().lower()
    return advisories.get(key, advisories["default"])

if __name__ == "__main__":
    print("Testing Chlorophyll Extraction:")
    print(get_chlorophyll_context(15.29, 73.50))
    
    print("\nTesting INCOIS Advisory:")
    print(get_incois_advisory("goa"))