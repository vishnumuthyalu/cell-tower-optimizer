import folium
from .config import OUTPUTS


def build_map(demand_df, candidate_df, existing_towers_df, selected_indices,
              radius_km: float, out_name: str = "coverage_map.html"):
    center = [demand_df["lat"].mean(), demand_df["lon"].mean()]
    m = folium.Map(location=center, zoom_start=11, tiles="cartodbpositron")

    # population as circle markers sized by population
    max_pop = demand_df["population"].max()
    for _, row in demand_df.iterrows():
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=2 + 6 * (row["population"] / max_pop),
            color="#5b6dfa",
            fill=True,
            fill_opacity=0.3,
            weight=0,
            tooltip=f"Pop: {int(row['population'])}",
        ).add_to(m)

    for _, row in existing_towers_df.iterrows():
        folium.Marker(
            location=[row["lat"], row["lon"]],
            icon=folium.Icon(color="blue", icon="signal", prefix="fa"),
            tooltip="Existing tower",
        ).add_to(m)

    for idx in selected_indices:
        row = candidate_df.iloc[idx]
        folium.Marker(
            location=[row["lat"], row["lon"]],
            icon=folium.Icon(color="red", icon="tower-broadcast", prefix="fa"),
            tooltip=f"New tower site {row['site_id']}",
        ).add_to(m)
        folium.Circle(
            location=[row["lat"], row["lon"]],
            radius=radius_km * 1000,
            color="red",
            fill=False,
            weight=1,
        ).add_to(m)

    out_path = OUTPUTS / out_name
    m.save(str(out_path))
    print(f"Map saved -> {out_path}")
    return out_path