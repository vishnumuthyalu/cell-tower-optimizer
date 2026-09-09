"""Load OpenCelliD CSV exports for all US MCCs and filter to a bounding box.

The US is split across five Mobile Country Codes (310-314) because carriers
exhausted the MNC pool under a single MCC. Notably, Verizon's primary
MCC/MNC pairing (311/480) falls outside MCC 310, which AT&T and T-Mobile
mostly use — so all five are combined here to avoid under-representing any
major carrier's tower footprint.
"""
import pandas as pd
from .config import DATA_RAW, DATA_PROCESSED

COLUMNS = ["radio", "mcc", "net", "area", "cell", "unit", "lon", "lat",
           "range", "samples", "changeable", "created", "updated", "averageSignal"]

# All five OpenCelliD exports covering United States MCCs.
# Download each from https://www.opencellid.org/downloads.php and place
# them in data/raw/ under these exact filenames.
TOWER_FILES = [
    DATA_RAW / "cell_towers_310.csv",
    DATA_RAW / "cell_towers_311.csv",
    DATA_RAW / "cell_towers_312.csv",
    DATA_RAW / "cell_towers_313.csv",
    DATA_RAW / "cell_towers_314.csv",
]


def load_existing_towers(bbox: tuple, files: list = None) -> pd.DataFrame:
    """bbox = (min_lat, min_lon, max_lat, max_lon).
    Reads each OpenCelliD CSV export in `files`, filters to the bounding
    box, and combines the results into one deduplicated tower list."""
    files = files or TOWER_FILES
    min_lat, min_lon, max_lat, max_lon = bbox

    frames = []
    for csv_path in files:
        df = pd.read_csv(csv_path, names=COLUMNS, header=None)
        mask = df["lat"].between(min_lat, max_lat) & df["lon"].between(min_lon, max_lon)
        frames.append(df.loc[mask, ["radio", "lat", "lon", "range"]])
        print(f"{csv_path.name}: {int(mask.sum())} towers in bbox")

    combined = pd.concat(frames, ignore_index=True).drop_duplicates()
    out_path = DATA_PROCESSED / "existing_towers.csv"
    combined.to_csv(out_path, index=False)
    print(f"Wrote {len(combined)} existing towers -> {out_path}")
    return combined


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--min-lat", type=float, required=True)
    p.add_argument("--min-lon", type=float, required=True)
    p.add_argument("--max-lat", type=float, required=True)
    p.add_argument("--max-lon", type=float, required=True)
    args = p.parse_args()
    load_existing_towers((args.min_lat, args.min_lon, args.max_lat, args.max_lon))