# Cell Tower Placement Optimizer

![Python](https://img.shields.io/badge/python-3.11-blue?logo=python&logoColor=white)
![License: MIT](https://img.shields.io/badge/license-MIT-green)
![Tests](https://github.com/<your-github-username>/cell-tower-optimizer/actions/workflows/tests.yml/badge.svg)
![Optimization](https://img.shields.io/badge/optimization-Integer%20Programming-orange)
![API](https://img.shields.io/badge/API-FastAPI-009688?logo=fastapi&logoColor=white)
![Dashboard](https://img.shields.io/badge/Dashboard-Streamlit-FF4B4B?logo=streamlit&logoColor=white)
![Data](https://img.shields.io/badge/Data-US%20Census%20%2B%20OpenCelliD-lightgrey)

An end-to-end geospatial optimization system that determines where a telecom carrier should build new cell towers to maximize population coverage under a fixed budget — using real U.S. Census population data and real OpenCelliD tower infrastructure data, solved with integer linear programming and benchmarked against a hand-built greedy heuristic.

---

## Problem Statement

Cellular carriers routinely face a capital-planning decision: given a limited budget for new cell towers, where should they be built to serve the most people? Coverage isn't unlimited — every tower has a finite service radius, every build has a cost, and population is never distributed evenly across a service area. Choosing sites badly means paying for infrastructure that leaves large populations underserved while other areas get redundant coverage.

This is a well-studied problem in operations research called the **Maximal Covering Location Problem (MCLP)**: given a set of weighted demand points and a set of candidate facility sites, select a fixed number of sites that maximize the total weighted demand covered within a service radius.

This project solves that exact problem for a real U.S. county, using real population and cellular infrastructure data rather than synthetic inputs, and treats it as both an optimization problem (how do you actually solve MCLP well?) and a software engineering problem (how do you turn that into something usable, testable, and demoable?).

## Approach

**Demand modeling.** Population is pulled from the U.S. Census Bureau's ACS5 API at the census-tract level and joined to tract centroid coordinates from the Census Gazetteer files, producing ~289 weighted demand points for Travis County, TX (Austin).

**Existing infrastructure.** Real cell tower locations come from [OpenCelliD](https://www.opencellid.org/). The U.S. is split across five Mobile Country Codes (310–314) because carriers exhausted the MNC pool under a single MCC — Verizon's primary pairing (311/480) in particular falls outside MCC 310, which AT&T and T-Mobile mostly use — so all five are combined to avoid under-representing any major carrier's footprint (2,659 existing towers found in this county alone).

**Candidate sites.** Since real zoning/parcel data is out of scope for a project like this, new-tower candidates are generated as a regular 1.5 km grid across the county's bounding box (962 candidate sites) — the standard simplification used in academic facility-location work.

**Optimization — two solvers, compared head-to-head:**
- **Exact solver:** formulates MCLP as an integer linear program using [`spopt`](https://pysal.org/spopt/notebooks/mclp.html) (PySAL's spatial-optimization library) and solves it to global optimality with PuLP's bundled CBC solver.
- **Greedy heuristic:** a hand-written baseline that iteratively picks the candidate site covering the most currently-uncovered weighted demand — the classic fast approximation algorithm for covering problems.

Both solvers run against the *same* haversine great-circle distance matrix, so the comparison is apples-to-apples: any difference in coverage is a genuine measure of solution quality, not an artifact of inconsistent distance math.

**Delivery.** The pipeline is exposed two ways: a **FastAPI** service (`POST /optimize`) with auto-generated interactive docs, and a **Streamlit** dashboard where budget, coverage radius, and solver choice are adjustable sliders, rendering results on a live Folium map.

## Architecture

```
Census ACS5 API + Gazetteer centroids ──┐
                                          ├──▶ demand_points.csv (289 tracts, weighted by population)
OpenCelliD (MCC 310–314, combined) ──▶ existing_towers.csv (2,659 towers)
Generated 1.5km grid ──▶ candidate_sites.csv (962 candidate sites)

demand_points + candidate_sites ──▶ haversine cost/coverage matrix
                                          │
                    ┌─────────────────────┴─────────────────────┐
                    ▼                                            ▼
      exact ILP solve (spopt MCLP + PuLP/CBC)         greedy heuristic (hand-written)
                    │                                            │
                    └─────────────────────┬──────────────────────┘
                                           ▼
                          evaluate.py — coverage %, runtime, optimality gap
                                           ▼
                          visualize.py — clustered Folium map
                                           ▼
                  FastAPI service   +   Streamlit dashboard  (both call the same pipeline)
```

## Results

Optimizing an 8-tower budget with a 3 km service radius over Travis County's 1,307,625 residents:

| Method | Population Covered | Coverage % | Runtime |
|---|---|---|---|
| **Exact (MCLP / Integer Programming)** | 556,532 | **42.6%** | 0.169s |
| Greedy heuristic | 510,204 | 39.0% | 0.006s |

The exact solver finds a solution covering **3.6 percentage points more population** than the greedy baseline — a real, measurable optimality gap, not just a rounding difference — while the greedy heuristic returns a result **~28x faster**. That tradeoff is the headline finding: for a one-time capital-planning decision, the extra ~160ms to guarantee the mathematically optimal answer is trivial; for a use case needing thousands of what-if scenarios evaluated interactively, the greedy approximation's near-instant runtime for a ~92%-as-good answer becomes the more practical choice.

Spatially, the eight selected sites span the Austin metro's actual population corridor — from Round Rock/Pflugerville in the north, through central Austin, down to Dripping Springs in the south — with sites spaced further apart at the edges and deliberately overlapping in the dense urban core, where the optimizer determined the marginal population gained from redundant coverage still outweighs the "waste."

### Optimized coverage map (exact solver)

![Optimized tower placement covering Travis County](Screenshot%202026-09-09%20115252.png)

*Red markers are the 8 optimally-sited new towers with their 3km coverage radius; blue clusters are the 2,659 existing towers (clustered for readability), color-coded and counted by density.*

### Interactive Streamlit dashboard

![Interactive dashboard exploring a different budget/radius configuration](Screenshot%202026-09-09%20115609.png)

*Budget, coverage radius, and solver choice (exact vs. greedy) are all adjustable in real time, with the map and coverage metrics re-rendering on each run.*

## Design Decisions

Three choices shape how this system behaves, each made to close off a failure mode rather than to react to one:

**One distance metric, shared by both solvers.** Both the exact ILP and the greedy heuristic consume the same haversine great-circle matrix, computed once in `coverage.py`. The alternative — reprojecting to Web Mercator (EPSG:3857) and treating the service radius as flat Euclidean distance — distorts real-world distance by ~15% at Austin's latitude, which shrinks the coverage radius the solver actually applies and quietly invalidates its "optimal" answer. Sharing one metric removes that class of error entirely and makes the exact-vs-greedy comparison rigorously apples-to-apples: any coverage difference is solution quality, never distance math. The invariant this buys is worth stating, because it doubles as a correctness check — an exact solver can never score below a heuristic on the same problem, so if it ever does, the distance matrix is wrong. `tests/test_coverage.py` pins that math directly, asserting NYC→LA at 3,936 km.

**A tile provider with no key dependency.** Basemap tiles come from OpenStreetMap rather than CARTO, which moved to requiring an API key partway through development. For a project meant to be cloned and run by anyone, a basemap that degrades into an "API KEY REQUIRED" watermark on someone else's machine is a reproducibility failure, not a cosmetic one.

**Clustered rendering at point-set scale.** All 2,659 existing towers render through Folium's `MarkerCluster` rather than as individual pins. At this density individual markers collapse into an unreadable wall of icons; clustering groups them into count-labeled bubbles that expand on zoom — the standard approach for point sets of this size, and the reason the map stays legible as the tower count grows.

The last two decisions are easiest to see side by side — a keyed basemap with unclustered markers on the left, the shipped configuration on the right:

| Without these choices | As shipped |
|---|---|
| ![Keyed basemap and unclustered marker overload](Screenshot%202026-09-09%20114251.png) | ![Clean, clustered, correctly-scaled map](Screenshot%202026-09-09%20115252.png) |

## Tech Stack

| Layer | Choice |
|---|---|
| Data ingestion | US Census ACS5 API, Census Gazetteer files, OpenCelliD |
| Geospatial math | NumPy (vectorized haversine distance) |
| Exact optimization | [`spopt`](https://pysal.org/spopt/) (MCLP) + PuLP (CBC solver) |
| Heuristic baseline | Hand-written greedy algorithm |
| Map visualization | Folium + MarkerCluster |
| API | FastAPI + Uvicorn |
| Dashboard | Streamlit |
| Testing | pytest |
| CI | GitHub Actions |

## Getting Started

```bash
git clone https://github.com/<your-github-username>/cell-tower-optimizer.git
cd cell-tower-optimizer
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env            # add your Census API key
```

**Get the data:**
1. Census API key (free, instant): https://api.census.gov/data/key_signup.html
2. Census Gazetteer tracts file: https://www.census.gov/geographies/reference-files/time-series/geo/gazetteer-files.html — download the current year's national tracts file into `data/raw/`
3. OpenCelliD tower exports (free registration): https://www.opencellid.org/downloads.php — download CSVs for MCCs 310–314 into `data/raw/` as `cell_towers_310.csv` … `cell_towers_314.csv`

**Run the pipeline:**
```bash
python -m src.tower_opt.ingest_census --state 48 --county 453 --gazetteer data/raw/<gazetteer_file>.txt
python -m src.tower_opt.ingest_towers --min-lat 30.05 --min-lon -97.95 --max-lat 30.55 --max-lon -97.55
python -c "from src.tower_opt.grid import generate_candidate_grid; generate_candidate_grid(bbox=(30.05, -97.95, 30.55, -97.55), spacing_km=1.5)"
python -m src.tower_opt.pipeline --budget 8 --radius 3.0
```

**Or run it interactively:**
```bash
streamlit run app/dashboard.py
```

**Or serve it as an API:**
```bash
uvicorn api.main:app --reload
# interactive docs at http://127.0.0.1:8000/docs
```

**Run the tests:**
```bash
pytest -v
```

## Project Structure

```
cell-tower-optimizer/
├── src/tower_opt/       # core package: ingestion, coverage math, both solvers, evaluation, visualization
├── api/                 # FastAPI service
├── app/                 # Streamlit dashboard
├── tests/               # pytest unit tests
├── data/                # raw downloads + pipeline outputs (gitignored — see Getting Started)
├── outputs/              # generated maps and results.json (gitignored)
└── .github/workflows/    # CI: runs the test suite on every push
```

## Future Work

Add a cost dimension so candidate sites have different costs (rooftop lease vs. greenfield build), turning the budget constraint into a knapsack-style variant instead of a flat count. Replace the flat-radius coverage assumption with a log-distance path-loss model so coverage isn't a perfect circle — the change that would most improve realism from an RF-engineering perspective. Add a capacitated constraint so each tower can only serve a maximum population (`spopt` supports this natively). Subtract population already served by existing towers before optimizing new sites, so the model targets coverage *gaps* rather than raw density. Combine with a customer churn dataset to test whether coverage gaps predict churn risk in underserved tracts.

## Conclusion

This project models a real capital-planning problem telecom carriers solve — where to site new towers under a fixed budget — end to end: real Census and OpenCelliD data in, a rigorously-compared exact-vs-heuristic optimization core, and a working API and dashboard out. What makes it hold up is that the hard parts are handled by design rather than by patching: one distance metric shared across both solvers so no comparison can be corrupted by projection error, five Mobile Country Codes combined so no carrier's footprint is under-counted, and a pinned regression test on the geospatial math so the invariant stays enforced as the code changes. That combination — real-world data engineering, correct operations-research modeling, and shipped software — is the intersection of software engineering and data science that network infrastructure teams actually work in.

## License

MIT — see [LICENSE](LICENSE).

## Author

**Vishnu Muthyalu**
