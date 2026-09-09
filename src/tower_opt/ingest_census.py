"""Pull tract-level population (demand) for a state/county and join to
Gazetteer centroids to produce demand points: (GEOID, lat, lon, population).
"""
import requests
import pandas as pd

from .config import CENSUS_API_KEY, ACS_YEAR, DATA_PROCESSED


def fetch_population(state_fips: str, county_fips: str) -> pd.DataFrame:
    """ACS5 total population (B01003_001E) per census tract."""
    url = (
        f"https://api.census.gov/data/{ACS_YEAR}/acs/acs5"
        f"?get=NAME,B01003_001E&for=tract:*"
        f"&in=state:{state_fips}+county:{county_fips}"
        f"&key={CENSUS_API_KEY}"
    )
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    rows = resp.json()
    header, *data = rows
    df = pd.DataFrame(data, columns=header)
    df["population"] = df["B01003_001E"].astype(int)
    df["GEOID"] = df["state"] + df["county"] + df["tract"]
    return df[["GEOID", "NAME", "population"]]


def load_gazetteer_centroids(gazetteer_path: str) -> pd.DataFrame:
    """Parse the national tracts Gazetteer file (tab-delimited .txt)
    downloaded from census.gov into GEOID/lat/lon."""
    df = pd.read_csv(gazetteer_path, sep="|", dtype=str)
    df.columns = [c.strip() for c in df.columns]
    df = df.rename(columns={"GEOID": "GEOID", "INTPTLAT": "lat", "INTPTLONG": "lon"})
    df["lat"] = df["lat"].astype(float)
    df["lon"] = df["lon"].astype(float)
    return df[["GEOID", "lat", "lon"]]


def build_demand_points(state_fips: str, county_fips: str, gazetteer_path: str) -> pd.DataFrame:
    pop = fetch_population(state_fips, county_fips)
    geo = load_gazetteer_centroids(gazetteer_path)
    merged = pop.merge(geo, on="GEOID", how="inner")
    merged = merged[merged["population"] > 0].reset_index(drop=True)
    out_path = DATA_PROCESSED / "demand_points.csv"
    merged.to_csv(out_path, index=False)
    print(f"Wrote {len(merged)} demand points -> {out_path}")
    return merged


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--state", required=True, help="2-digit state FIPS, e.g. 48 for TX")
    p.add_argument("--county", required=True, help="3-digit county FIPS, e.g. 453 for Travis County")
    p.add_argument("--gazetteer", required=True, help="path to downloaded Gazetteer tracts .txt")
    args = p.parse_args()
    build_demand_points(args.state, args.county, args.gazetteer)