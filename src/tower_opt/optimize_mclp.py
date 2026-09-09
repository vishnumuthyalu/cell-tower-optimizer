"""Exact solve via spopt's MCLP (ILP under the hood, solved with PuLP/CBC)."""
import time
import geopandas as gpd
from shapely.geometry import Point
import pulp
from spopt.locate import MCLP


def solve_mclp_exact(demand_df, candidate_df, radius_km: float, p: int):
    demand_gdf = gpd.GeoDataFrame(
        demand_df,
        geometry=[Point(xy) for xy in zip(demand_df["lon"], demand_df["lat"])],
        crs="EPSG:4326",
    )
    candidate_gdf = gpd.GeoDataFrame(
        candidate_df,
        geometry=[Point(xy) for xy in zip(candidate_df["lon"], candidate_df["lat"])],
        crs="EPSG:4326",
    )

    # spopt's default distance metric works in projected units; reproject to
    # a meter-based CRS so the radius (converted to meters) is meaningful.
    demand_proj = demand_gdf.to_crs(epsg=3857)
    candidate_proj = candidate_gdf.to_crs(epsg=3857)
    radius_m = radius_km * 1000

    model = MCLP.from_geodataframe(
        demand_proj,
        candidate_proj,
        "geometry",
        "geometry",
        "population",
        radius_m,
        p_facilities=p,
        distance_metric="euclidean",
        name="tower-mclp",
    )

    start = time.time()
    solver = pulp.PULP_CBC_CMD(msg=False)
    model = model.solve(solver)
    runtime = time.time() - start

    selected = [i for i, v in enumerate(model.fac_vars) if v.value() == 1]
    total_weight = float(demand_df["population"].sum())
    covered_weight = total_weight * (model.perc_cov / 100)

    return {
        "selected_indices": selected,
        "coverage_pct": model.perc_cov,
        "covered_weight": covered_weight,
        "total_weight": total_weight,
        "runtime_sec": runtime,
    }