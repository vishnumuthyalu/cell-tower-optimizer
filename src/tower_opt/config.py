import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parents[2]
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
OUTPUTS = ROOT / "outputs"

CENSUS_API_KEY = os.getenv("CENSUS_API_KEY", "")
ACS_YEAR = 2023  # check https://www.census.gov/data/developers/data-sets/acs-5year.html for the latest available year
EARTH_RADIUS_KM = 6371.0

for d in (DATA_RAW, DATA_PROCESSED, OUTPUTS):
    d.mkdir(parents=True, exist_ok=True)