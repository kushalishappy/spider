import os
import urllib.request
import xarray as xr

# Ensure data directory exists
os.makedirs("data", exist_ok=True)
output_path = "data/regional_oisst.nc"

# Direct ERDDAP NetCDF API download link
erddap_url = (
    "https://coastwatch.pfeg.noaa.gov/erddap/griddap/ncdcOisst21Agg_LonPM180.nc?"
    "sst%5B(2026-08-01T12:00:00Z):1:(2026-08-25T12:00:00Z)%5D"
    "%5B(0.0):1:(0.0)%5D"
    "%5B(4.0):1:(25.0)%5D"
    "%5B(65.0):1:(95.0)%5D"
)

print("Downloading NetCDF file directly from NOAA ERDDAP...")

try:
    # Download file directly to local disk
    urllib.request.urlretrieve(erddap_url, output_path)
    print(f"File downloaded successfully to: {output_path}")

    # Verify file integrity with xarray
    ds = xr.open_dataset(output_path)
    print("Dataset verification successful!")
    print(ds)
except Exception as e:
    print(f"Download or reading failed: {e}")