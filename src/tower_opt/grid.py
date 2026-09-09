"""Generate a candidate grid of new-tower sites across a bounding box."""
import numpy as np
import pandas as pd
from .config import DATA_PROCESSED

KM_PER_DEG_LAT = 111.0


def generate_candidate_grid(bbox: tuple, spacing_km: float = 1.5) -> pd.DataFrame:
    """bbox = (min_lat, min_lon, max_lat, max_lon). Returns candidate site points."""
    min_lat, min_lon, max_lat, max_lon = bbox
    lat_step = spacing_km / KM_PER_DEG_LAT
    mean_lat_rad = np.radians((min_lat + max_lat) / 2)
    km_per_deg_lon = KM_PER_DEG_LAT * np.cos(mean_lat_rad)
    lon_step = spacing_km / km_per_deg_lon

    lats = np.arange(min_lat, max_lat, lat_step)
    lons = np.arange(min_lon, max_lon, lon_step)
    grid = [(lat, lon) for lat in lats for lon in lons]

    df = pd.DataFrame(grid, columns=["lat", "lon"])
    df["site_id"] = [f"C{i}" for i in range(len(df))]
    out_path = DATA_PROCESSED / "candidate_sites.csv"
    df.to_csv(out_path, index=False)
    print(f"Generated {len(df)} candidate sites -> {out_path}")
    return df