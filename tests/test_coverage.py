import numpy as np
import pandas as pd
from src.tower_opt.coverage import haversine_matrix, build_coverage_matrix


def test_haversine_known_distance():
    # NYC to LA ~= 3936 km
    d = haversine_matrix(np.array([40.7128]), np.array([-74.0060]),
                          np.array([34.0522]), np.array([-118.2437]))
    assert abs(d[0, 0] - 3936) < 50


def test_coverage_matrix_shapes():
    demand = pd.DataFrame({"lat": [30.0, 30.01], "lon": [-97.0, -97.01]})
    candidates = pd.DataFrame({"lat": [30.0], "lon": [-97.0]})
    cov = build_coverage_matrix(demand, candidates, radius_km=5)
    assert cov.shape == (1, 2)
    assert cov.all()  # both demand points within 5km