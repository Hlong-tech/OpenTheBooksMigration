import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from data import counties, NATIONAL_AVG
from heatmap import render_heatmap

st.set_page_config(
    page_title="Open The Books — County Dashboard",
    page_icon="🏛️",
    layout="wide"
)

st.markdown("""
<style>
    .main { background-color: #FAFAFA; }
    .block-container { padding-top: 2rem; }
    .otb-title { font-size: 28px; font-weight: 600; color: #1a1a1a; margin-bottom: 0; }
    .otb-sub { font-size: 15px; color: #666; margin-bottom: 1.5rem; }
    .snapshot-box {
        background: #fff;
        border: 1px solid #e0e0e0;
        border-left: 4px solid #1f4e79;
        border-radius: 6px;
        padding: 1rem 1.25rem;
        margin-top: 1rem;
        font-size: 15px;
        color: #333;
        line-height: 1.6;
    }
    .stMetric { background: #fff; border: 1px solid #e8e8e8; border-radius: 8px; padding: 1rem; }
</style>
""", unsafe_allow_html=True)

# ── Header ──────────────────────────────────────────────────────────────────
col_logo, col_title = st.columns([1, 8])
with col_title:
    st.markdown('<div class="otb-title">🏛️ Open The Books — County Snapshot</div>', unsafe_allow_html=True)
    st.markdown('<div class="otb-sub">Select a county to see how government size compares to economic outcomes.</div>', unsafe_allow_html=True)

st.divider()

tab1, tab2 = st.tabs(["🔍 County Lookup", "🗺️ National Heatmap"])

with tab2:
    render_heatmap()

with tab1:
    # ── County selector ───────────────────────────────────────────────────────
    df = pd.DataFrame(counties)
    county_options = df["name"] + ", " + df["state"]
    selected = st.selectbox("Choose a county", options=county_options, index=0)

    county_idx = county_options[county_options == selected].index[0]
    c = df.loc[county_idx]

    st.markdown(f"### {c['name']}, {c['state']}")
    st.markdown(f"*Population: {c['pop']:,}*")
    st.markdown("---")

    # ── Metric cards ──────────────────────────────────────────────────────────
    m1, m2, m3, m4 = st.columns(4)

    emp_delta   = c['employees'] - NATIONAL_AVG['employees']
    pov_delta   = round(c['poverty'] - NATIONAL_AVG['poverty'], 1)
    inc_delta   = c['median_income'] - NATIONAL_AVG['median_income']

    m1.metric("Govt Employees / 1,000", f"{c['employees']}",
              delta=f"{emp_delta:+} vs avg", delta_color="inverse")
    m2.metric("Net Migration", f"{c['migration']:+,}",
              delta="People moving in" if c['migration'] > 0 else "People moving out",
              delta_color="normal" if c['migration'] > 0 else "inverse")
    m3.metric("Poverty Rate", f"{c['poverty']}%",
              delta=f"{pov_delta:+}% vs avg", delta_color="inverse")
    m4.metric("Median Household Income", f"${c['median_income']:,.0f}",
              delta=f"${inc_delta:+,.0f} vs avg", delta_color="normal")

    st.markdown("---")

    # ── Charts ────────────────────────────────────────────────────────────────
    left, right = st.columns(2)

    with left:
        st.subheader("vs. National Average")
        metrics     = ["Employees/1k", "Poverty rate (%)"]
        county_vals = [c['employees'], c['poverty']]
        avg_vals    = [NATIONAL_AVG['employees'], NATIONAL_AVG['poverty']]

        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            name=c['name'], x=metrics, y=county_vals,
            marker_color='#1f4e79',
            text=[f"{v}%" if i == 1 else str(v) for i, v in enumerate(county_vals)],
            textposition='outside'
        ))
        fig_bar.add_trace(go.Bar(
            name="National avg", x=metrics, y=avg_vals,
            marker_color='#a8c4e0',
            text=[f"{v}%" if i == 1 else str(v) for i, v in enumerate(avg_vals)],
            textposition='outside'
        ))
        fig_bar.update_layout(
            barmode='group', height=360,
            margin=dict(t=30, b=10, l=10, r=10),
            legend=dict(orientation='h', y=-0.15),
            plot_bgcolor='white', paper_bgcolor='white',
            yaxis=dict(showgrid=True, gridcolor='#f0f0f0')
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with right:
        st.subheader("Median Income vs. Poverty")
        fig_gauge = go.Figure()
        fig_gauge.add_trace(go.Indicator(
            mode="gauge+number+delta",
            value=c['poverty'],
            delta={'reference': NATIONAL_AVG['poverty'], 'suffix': '%', 'valueformat': '.1f'},
            title={'text': "Poverty Rate (%)"},
            gauge={
                'axis': {'range': [0, 35]},
                'bar': {'color': "#c0392b" if c['poverty'] > NATIONAL_AVG['poverty'] else "#27ae60"},
                'steps': [
                    {'range': [0, 10], 'color': '#eafaf1'},
                    {'range': [10, 20], 'color': '#fef9e7'},
                    {'range': [20, 35], 'color': '#fdedec'},
                ],
                'threshold': {
                    'line': {'color': '#1f4e79', 'width': 3},
                    'thickness': 0.75,
                    'value': NATIONAL_AVG['poverty']
                }
            },
            domain={'x': [0, 1], 'y': [0.4, 1]}
        ))
        fig_gauge.add_trace(go.Indicator(
            mode="number+delta",
            value=c['median_income'],
            number={'prefix': "$", 'valueformat': ','},
            delta={'reference': NATIONAL_AVG['median_income'], 'prefix': "$", 'valueformat': ','},
            title={'text': "Median Household Income"},
            domain={'x': [0.1, 0.9], 'y': [0, 0.3]}
        ))
        fig_gauge.update_layout(
            height=360, margin=dict(t=30, b=10, l=10, r=10),
            paper_bgcolor='white'
        )
        st.plotly_chart(fig_gauge, use_container_width=True)

    # ── Snapshot sentence ─────────────────────────────────────────────────────
    issues, wins = [], []
    if c['migration'] < -5000:
        issues.append("losing residents at a significant rate")
    elif c['migration'] > 5000:
        wins.append("attracting new residents")
    if c['poverty'] > NATIONAL_AVG['poverty'] + 3:
        issues.append("a poverty rate well above the national average")
    elif c['poverty'] < NATIONAL_AVG['poverty'] - 2:
        wins.append("a low poverty rate")
    if c['median_income'] > NATIONAL_AVG['median_income'] + 10000:
        wins.append("strong median household income")
    elif c['median_income'] < NATIONAL_AVG['median_income'] - 10000:
        issues.append("median income below the national average")

    if len(wins) > len(issues):
        snapshot = f"✅ {c['name']} shows relative fiscal health — {', '.join(wins)}."
    elif issues:
        snapshot = f"⚠️ {c['name']} raises some concerns: {'; '.join(issues)}."
    else:
        snapshot = f"📊 {c['name']} is near the national average across most metrics."

    st.markdown(f'<div class="snapshot-box">{snapshot}</div>', unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("---")
    st.caption("Data sources: BLS QCEW 2024 (employee counts) · IRS SOI 2021–22 (migration) · USDA SAIPE 2023 (poverty, income) · U.S. Census Bureau 2024 (population)")
