"""Vectorized haversine distance and coverage/cost matrix construction."""
import numpy as np
from .config import EARTH_RADIUS_KM


def haversine_matrix(lat1, lon1, lat2, lon2) -> np.ndarray:
    """Pairwise great-circle distance (km) between every point in
    (lat1, lon1) and every point in (lat2, lon2). Returns a
    len(lat1) x len(lat2) matrix."""
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    lat1 = lat1.reshape(-1, 1)
    lon1 = lon1.reshape(-1, 1)
    dlat = lat2.reshape(1, -1) - lat1
    dlon = lon2.reshape(1, -1) - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2.reshape(1, -1)) * np.sin(dlon / 2) ** 2
    c = 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))
    return EARTH_RADIUS_KM * c


def build_coverage_matrix(demand_df, candidate_df, radius_km: float) -> np.ndarray:
    """Boolean matrix: rows = candidate sites, cols = demand points.
    True if that candidate covers that demand point within radius_km."""
    dist = haversine_matrix(
        candidate_df["lat"].values, candidate_df["lon"].values,
        demand_df["lat"].values, demand_df["lon"].values,
    )
    return dist <= radius_km