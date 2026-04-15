from heatmap_data import HEATMAP_DATA
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import streamlit as st

def render_heatmap():
    st.markdown("### National Government Employee Density")
    st.caption("Government employees per 1,000 residents by county — darker = higher government density")

    df = pd.DataFrame(HEATMAP_DATA)

    # ── Controls ──────────────────────────────────────────────────────────────
    col_filter, col_range = st.columns([2, 2])
    with col_filter:
        states = sorted(df["state"].unique())
        selected_states = st.multiselect(
            "Filter by state",
            options=states,
            default=[],
            placeholder="All states"
        )
    with col_range:
        min_emp, max_emp = int(df["employees_per_1k"].min()), int(df["employees_per_1k"].max())
        emp_range = st.slider(
            "Employees per 1,000 range",
            min_value=min_emp,
            max_value=max_emp,
            value=(min_emp, max_emp)
        )

    # Apply filters
    filtered = df.copy()
    if selected_states:
        filtered = filtered[filtered["state"].isin(selected_states)]
    filtered = filtered[
        (filtered["employees_per_1k"] >= emp_range[0]) &
        (filtered["employees_per_1k"] <= emp_range[1])
    ]

    if filtered.empty:
        st.warning("No counties match the current filters.")
        return

    # ── Choropleth map ────────────────────────────────────────────────────────
    fig = px.choropleth(
        filtered,
        geojson="https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json",
        locations="fips",
        color="employees_per_1k",
        color_continuous_scale=[
            [0.0,  "#EAF2FB"],
            [0.3,  "#85B7EB"],
            [0.6,  "#378ADD"],
            [0.85, "#185FA5"],
            [1.0,  "#042C53"],
        ],
        range_color=(30, 90),
        scope="usa",
        labels={"employees_per_1k": "Employees/1k"},
        hover_name="name",
        hover_data={
            "fips": False,
            "state": False,
            "employees_per_1k": True,
            "pop": ":,",
        },
        custom_data=["name", "employees_per_1k", "pop"]
    )

    fig.update_traces(
        hovertemplate="<b>%{customdata[0]}</b><br>Govt employees/1k: %{customdata[1]}<br>Population: %{customdata[2]:,}<extra></extra>"
    )

    fig.update_layout(
        height=520,
        margin=dict(t=10, b=10, l=0, r=0),
        coloraxis_colorbar=dict(
            title="Per 1,000<br>residents",
            thickness=14,
            len=0.6,
            tickvals=[30, 45, 60, 75, 90],
            ticktext=["30 (lean)", "45", "60 (avg)", "75", "90 (heavy)"],
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        geo=dict(
            bgcolor="rgba(0,0,0,0)",
            lakecolor="rgba(0,0,0,0)",
            landcolor="#f5f5f5",
            showlakes=True,
            showland=True,
            subunitcolor="#dddddd",
        )
    )

    st.plotly_chart(fig, use_container_width=True)

    # ── Rankings table ────────────────────────────────────────────────────────
    st.markdown("---")
    col_top, col_bot = st.columns(2)

    with col_top:
        st.markdown("**Highest government density**")
        top10 = filtered.nlargest(8, "employees_per_1k")[["name", "employees_per_1k"]].reset_index(drop=True)
        top10.index += 1
        top10.columns = ["County", "Employees / 1k"]
        st.dataframe(top10, use_container_width=True, hide_index=False)

    with col_bot:
        st.markdown("**Lowest government density**")
        bot10 = filtered.nsmallest(8, "employees_per_1k")[["name", "employees_per_1k"]].reset_index(drop=True)
        bot10.index += 1
        bot10.columns = ["County", "Employees / 1k"]
        st.dataframe(bot10, use_container_width=True, hide_index=False)

    # ── Summary stats ─────────────────────────────────────────────────────────
    st.markdown("---")
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Counties shown",    len(filtered))
    s2.metric("Avg employees/1k",  round(filtered["employees_per_1k"].mean(), 1))
    s3.metric("Highest",           f"{filtered['employees_per_1k'].max()} — {filtered.loc[filtered['employees_per_1k'].idxmax(), 'name'].split(',')[0]}")
    s4.metric("Lowest",            f"{filtered['employees_per_1k'].min()} — {filtered.loc[filtered['employees_per_1k'].idxmin(), 'name'].split(',')[0]}")

    st.caption("Source: BLS Quarterly Census of Employment & Wages 2024 + U.S. Census Bureau population estimates 2024 · 2,370 counties")
