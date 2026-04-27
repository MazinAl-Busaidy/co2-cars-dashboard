import streamlit as st
import pandas as pd
import plotly.express as px

#page configuration
st.set_page_config(
    page_title="EU CO2 Cars Dashboard",
    page_icon="🚗",
    layout="wide",
)

#Data loading
@st.cache_data
def load_data():
    df = pd.read_csv("data/co2_cars.csv")
    df["obs_value"] = pd.to_numeric(df["obs_value"], errors="coerce")
    df = df.dropna(subset=["obs_value"])
    df["time"] = df["time"].astype(int)
    return df

df = load_data()

# Separate country rows from EU aggregates
EU_AGGREGATES = {"EU27_2020", "EU28", "EU27", "EA", "EA19", "EA20"}
df_countries = df[~df["geo"].isin(EU_AGGREGATES)].copy()

# Sidebar filters
st.sidebar.title("Filters")
st.sidebar.markdown("Configure the dashboard view.")

min_year = int(df_countries["time"].min())
max_year = int(df_countries["time"].max())
year_range = st.sidebar.slider(
    "Year range",
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year),
)

all_countries = sorted(df_countries["geo_label"].unique())
preferred = ["Germany", "France", "Italy", "Spain", "Poland", "Netherlands"]
default_countries = [c for c in preferred if c in all_countries] or all_countries[:6]
selected_countries = st.sidebar.multiselect(
    "Countries (for trend chart)",
    options=all_countries,
    default=default_countries,
)

#apply year filter
mask = df_countries["time"].between(*year_range)
filtered = df_countries[mask].copy()

#headerr
st.title("🚗 EU New Passenger Cars CO₂ Dashboard")
st.markdown(
    "Analysis of average CO₂ emissions per kilometre from newly registered "
    "passenger cars across European countries. "
    "Data source: [European Environment Agency]"
    "(https://www.eea.europa.eu/en/datahub/datahubitem-view/5d252092-d328-40d8-bca2-c0734bd6143b)"
)

# KPI metrics
latest_year = int(filtered["time"].max())
earliest_year = int(filtered["time"].min())
latest = filtered[filtered["time"] == latest_year]
earliest = filtered[filtered["time"] == earliest_year]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Latest year", latest_year)
if not latest.empty:
    col2.metric(f"Avg CO₂ ({latest_year})", f"{latest['obs_value'].mean():.1f} g/km")
if not earliest.empty and not latest.empty:
    delta = latest["obs_value"].mean() - earliest["obs_value"].mean()
    delta_pct = (delta / earliest["obs_value"].mean()) * 100
    col3.metric(
        f"Change since {earliest_year}",
        f"{delta:+.1f} g/km",
        f"{delta_pct:+.1f}%",
        delta_color="inverse",
    )
if not latest.empty:
    best = latest.loc[latest["obs_value"].idxmin()]
    col4.metric(f"Lowest in {latest_year}", best["geo_label"], f"{best['obs_value']:.1f} g/km")

st.markdown("---")

# trend line chart
st.subheader("Trends over time")
trend_data = filtered[filtered["geo_label"].isin(selected_countries)]
if not trend_data.empty:
    fig_line = px.line(
        trend_data.sort_values(["geo_label", "time"]),
        x="time",
        y="obs_value",
        color="geo_label",
        labels={"time": "Year", "obs_value": "CO₂ (g/km)", "geo_label": "Country"},
        markers=True,
    )
    fig_line.update_layout(
        height=500,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
    )
    st.plotly_chart(fig_line, use_container_width=True)
else:
    st.info("Select at least one country in the sidebar to view the trend chart.")

#map and bar chart side-by-side
col_map, col_bar = st.columns([3, 2])

with col_map:
    st.subheader(f"Europe map ({latest_year})")
    if not latest.empty:
        fig_map = px.choropleth(
            latest,
            locations="geo_label",
            locationmode="country names",
            color="obs_value",
            color_continuous_scale="RdYlGn_r",
            scope="europe",
            labels={"obs_value": "CO₂ (g/km)"},
        )
        fig_map.update_layout(height=500, margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig_map, use_container_width=True)

with col_bar:
    st.subheader(f"Country ranking ({latest_year})")
    if not latest.empty:
        sorted_latest =latest.sort_values("obs_value")
        fig_bar = px.bar(
            sorted_latest,
            x="obs_value",
            y="geo_label",
            orientation="h",
            color="obs_value",
            color_continuous_scale="RdYlGn_r",
            labels={"obs_value": "CO₂ (g/km)", "geo_label": ""},
        )
        fig_bar.update_layout(height=500, showlegend=False, coloraxis_showscale=False)
        st.plotly_chart(fig_bar, use_container_width=True)

#ddata table and download
with st.expander("View underlying data"):
    display_df = filtered[["geo_label", "time", "obs_value"]].rename(
        columns={"geo_label": "Country", "time": "Year", "obs_value": "CO2 g/km"}
    )
    st.dataframe(display_df, use_container_width=True)
    csv = display_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download filtered data as CSV",
        data=csv,
        file_name="co2_cars_filtered.csv",
        mime="text/csv",
    )

#footer
st.markdown("---")
st.caption(
    "5DATA004W Data Science Project Lifecycle • Coursework dashboard • "
    "Data: European Environment Agency SDG 13_31 indicator"
)
