import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import pandas as pd

from src.tower_opt.config import DATA_PROCESSED
from src.tower_opt.coverage import build_coverage_matrix
from src.tower_opt.optimize_greedy import greedy_mclp
from src.tower_opt.optimize_mclp import solve_mclp_exact
from src.tower_opt.visualize import build_map

st.set_page_config(page_title="Cell Tower Placement Optimizer", layout="wide")
st.title("Cell Tower Placement Optimizer")

budget = st.sidebar.slider("Number of new towers", 1, 20, 5)
radius = st.sidebar.slider("Coverage radius (km)", 0.5, 10.0, 3.0)
method = st.sidebar.radio("Solver", ["Exact (ILP)", "Greedy heuristic"])

if st.sidebar.button("Run optimization"):
    demand_df = pd.read_csv(DATA_PROCESSED / "demand_points.csv")
    candidate_df = pd.read_csv(DATA_PROCESSED / "candidate_sites.csv")
    existing_towers_df = pd.read_csv(DATA_PROCESSED / "existing_towers.csv")

    if method == "Exact (ILP)":
        result = solve_mclp_exact(demand_df, candidate_df, radius, budget)
    else:
        coverage_matrix = build_coverage_matrix(demand_df, candidate_df, radius)
        result = greedy_mclp(coverage_matrix, demand_df["population"].values, budget)

    st.metric("Population covered", f"{result['coverage_pct']:.1f}%")
    st.metric("Runtime", f"{result['runtime_sec']:.3f}s")

    map_path = build_map(demand_df, candidate_df, existing_towers_df,
                          result["selected_indices"], radius)
    with open(map_path) as f:
        st.components.v1.html(f.read(), height=600)