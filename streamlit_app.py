import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
import numpy as np

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Budget Burn-Rate Tracker",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom Cyber-Dark CSS ─────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'IBM Plex Sans', sans-serif;
    }
    .stApp {
        background-color: #0b0f19;
        color: #f0f4f8;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    h1, h2, h3 {
        font-family: 'IBM Plex Mono', monospace !important;
        color: #38bdf8 !important;
        letter-spacing: -0.5px;
    }
    .metric-card {
        background: #111827;
        border: 1px solid #1f2937;
        border-left: 4px solid #38bdf8;
        border-radius: 6px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 1rem;
    }
    .metric-card-alert {
        background: #1e1b4b;
        border: 1px solid #311042;
        border-left: 4px solid #ef4444;
        border-radius: 6px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 1rem;
    }
    .metric-value {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 2.2rem;
        font-weight: 600;
        color: #f3f4f6;
        line-height: 1;
    }
    .metric-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color: #9ca3af;
        margin-top: 0.5rem;
    }
    .section-divider {
        border: none;
        border-top: 1px solid #1f2937;
        margin: 1.5rem 0;
    }
    [data-testid="stSidebar"] {
        background-color: #030712;
        border-right: 1px solid #1f2937;
    }
</style>
""", unsafe_allow_html=True)

# ── Dynamic Department Default Budgets ──────────────────────────────────────────
DEFAULT_BUDGETS = {
    "Marketing": 50000.0,
    "IT & Infrastructure": 150000.0,
    "Human Resources": 35000.0,
    "Operations & Supply": 95000.0
}

# ── Data Generation Engine (Simulating Year 2026 Spending) ─────────────────────
def generate_spending_data(department: str) -> pd.DataFrame:
    np.random.seed(42 + len(department))
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
    
    # Use a generic mid-scale baseline profile for simulation data
    avg_monthly_target = 6500.0
    
    actual_spends = []
    for i, m in enumerate(months):
        multiplier = 1.0 + (i * 0.12)  # Simulated spending increase over months
        spend = np.random.uniform(avg_monthly_target * 0.9, avg_monthly_target * 1.3) * multiplier
        actual_spends.append(round(spend, 2))
        
    return pd.DataFrame({"Month": months, "Spend": actual_spends})

# ── Sidebar Configurations ─────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ DEPT OPTIONS")
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    
    # Department Switcher
    selected_dept = st.selectbox("Select Department Focus", list(DEFAULT_BUDGETS.keys()))
    
    # MODIFIED: Team can now type in or adjust the budget limit directly!
    allocated_budget = st.number_input(
        "Set Custom Annual Budget ($)",
        min_value=1000.0,
        max_value=1000000.0,
        value=DEFAULT_BUDGETS[selected_dept],
        step=5000.0,
        help="Change this value to adjust the spending target ceiling dynamically."
    )
    
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    
    # Simulation Tool: What-if slider to manipulate trajectory adjustments live
    burn_modifier = st.slider(
        "Simulated Spending Shift (%)", 
        min_value=-50, max_value=50, value=0, step=5,
        help="Simulate cost reduction (-) or budget increase (+)"
    )

# ── Business Logic Processing & Projections ──────────────────────────────────
raw_data = generate_spending_data(selected_dept)
current_months_count = len(raw_data)

# Calculate Base Burn Metrics
total_ytd_spent = raw_data["Spend"].sum()
base_avg_burn = total_ytd_spent / current_months_count

# Apply the Slider adjustment modifier to future pacing projections
projected_monthly_burn = base_avg_burn * (1 + (burn_modifier / 100))

# Project out the rest of the calendar year (Jul - Dec)
future_months = ["Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
all_months = list(raw_data["Month"]) + future_months

# Construct Cumulative Trackers
cumulative_spend = list(np.cumsum(raw_data["Spend"]))
projection_line = [None] * (current_months_count - 1) + [cumulative_spend[-1]]

current_cum = cumulative_spend[-1]
for i in range(len(future_months)):
    current_cum += projected_monthly_burn
    projection_line.append(current_cum)

# Pad actuals with None for future slots to isolate formatting cleanly
actual_line = cumulative_spend + [None] * len(future_months)

# Calculate Risk Trigger parameters
remaining_allowance = allocated_budget - total_ytd_spent
months_left_before_exhaustion = remaining_allowance / projected_monthly_burn if projected_monthly_burn > 0 else 999

# Determine precise target depletion boundary
exhaustion_index = current_months_count - 1 + months_left_before_exhaustion
exhaustion_alert = exhaustion_index < 11.0  # Runs out before Dec end

if exhaustion_alert:
    status_color = "#ef4444"
    month_idx = int(np.floor(exhaustion_index))
    target_month = all_months[min(max(month_idx, 0), 11)]
    exhaustion_status = f"RUN OUT ({target_month})"
else:
    status_color = "#10b981"
    exhaustion_status = "SAFE (Dec+)"

# ── Executive Header Render ────────────────────────────────────────────────────
st.markdown(f'<h1 style="margin-bottom:0;">📊 BUDGET BURN-RATE FORECASTER</h1>', unsafe_allow_html=True)
st.markdown(
    f'<p style="color:#64748b;font-size:0.85rem;font-family:\'IBM Plex Mono\',monospace;margin-top:4px;">'
    f'Strategic Predictive Run-Rate Monitor &nbsp;&nbsp;|&nbsp;&nbsp; Scope: <span style="color:#38bdf8;">{selected_dept}</span>'
    f"</p>",
    unsafe_allow_html=True,
)
st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

# ── Dynamic High-Fidelity KPI Row ──────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(
        f'<div class="metric-card"><div class="metric-value">${allocated_budget:,.0f}</div>'
        '<div class="metric-label">Total Annual Limit</div></div>',
        unsafe_allow_html=True,
    )
with col2:
    st.markdown(
        f'<div class="metric-card"><div class="metric-value">${total_ytd_spent:,.0f}</div>'
        '<div class="metric-label">YTD Capital Utilized</div></div>',
        unsafe_allow_html=True,
    )
with col3:
    st.markdown(
        f'<div class="metric-card"><div class="metric-value">${projected_monthly_burn:,.0f}</div>'
        '<div class="metric-label">Projected Burn / Mo</div></div>',
        unsafe_allow_html=True,
    )
with col4:
    card_class = "metric-card-alert" if exhaustion_alert else "metric-card"
    st.markdown(
        f'<div class="{card_class}"><div class="metric-value" style="color:{status_color};">{exhaustion_status}</div>'
        '<div class="metric-label">Exhaustion Horizon</div></div>',
        unsafe_allow_html=True,
    )

# ── Core Visual Forecast Chart Line Render ─────────────────────────────────────
st.markdown("### Cumulative Budget Burn Path & Linear Projections")

fig = go.Figure()

# Plot line for Year-To-Date Actual spending path
fig.add_trace(go.Scatter(
    x=all_months, y=actual_line,
    name="Actual Cumulative Spend",
    line=dict(color="#38bdf8", width=3.5),
    mode="lines+markers"
))

# Plot predictive projection dotted segment line extension
fig.add_trace(go.Scatter(
    x=all_months, y=projection_line,
    name="Predictive Projection Pacing",
    line=dict(color="#ef4444", width=3, dash="dot"),
    mode="lines"
))

# Plot Horizontal Static Budget Boundary Cap line reference
fig.add_trace(go.Scatter(
    x=all_months, y=[allocated_budget]*12,
    name="Total Budget Ceiling",
    line=dict(color="rgba(239, 68, 68, 0.4)", width=2, style="dash"),
    mode="lines",
    showlegend=True
))

fig.update_layout(
    plot_bgcolor="#0b0f19",
    paper_bgcolor="#0b0f19",
    font=dict(family="IBM Plex Sans", color="#9ca3af"),
    xaxis=dict(gridcolor="#1f2937", linecolor="#1f2937"),
    yaxis=dict(
        title="Total Spending Vol ($)",
        title_font=dict(size=12, family="IBM Plex Mono"),
        gridcolor="#1f2937", linecolor="#1f2937"
    ),
    margin=dict(t=20, b=40, l=40, r=20),
    height=450,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

st.plotly_chart(fig, use_container_width=True)

# ── Data Ledger Segment Breakdown View ─────────────────────────────────────────
st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
with st.expander("📋 Data Ledger Breakdown View"):
    st.dataframe(raw_data.set_index("Month"), use_container_width=True)
