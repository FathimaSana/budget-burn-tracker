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

# ── Custom Corporate Light CSS ────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'IBM Plex Sans', sans-serif;
    }
    .stApp {
        background-color: #f8fafc;
        color: #0f172a;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    h1, h2, h3 {
        font-family: 'IBM Plex Mono', monospace !important;
        color: #1e3a8a !important;
        letter-spacing: -0.5px;
    }
    .metric-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-left: 4px solid #2563eb;
        border-radius: 6px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .metric-card-alert {
        background: #fef2f2;
        border: 1px solid #fee2e2;
        border-left: 4px solid #dc2626;
        border-radius: 6px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .metric-value {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 2.2rem;
        font-weight: 600;
        color: #0f172a;
        line-height: 1;
    }
    .metric-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color: #64748b;
        margin-top: 0.5rem;
    }
    .section-divider {
        border: none;
        border-top: 1px solid #e2e8f0;
        margin: 1.5rem 0;
    }
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
    }
    .stSelectbox, .stNumberInput {
        color: #0f172a !important;
    }
</style>
""", unsafe_allow_html=True)

# ── Dynamic Department Default Budgets ──────────────────────────────────────────
DEFAULT_BUDGETS = {
    "Marketing": 180000.0,
    "IT & Infrastructure": 550000.0,
    "Human Resources": 120000.0,
    "Operations & Supply": 350000.0
}

# ── Data Generation Engine (Simulating Variable Month-to-Month Spends) ────────
def generate_spending_data(department: str) -> pd.DataFrame:
    np.random.seed(42 + len(department))
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
    
    base_budget = DEFAULT_BUDGETS[department]
    avg_monthly_target = (base_budget / 12)
    
    # MODIFIED: Creates highly realistic, fluctuating month-to-month swings
    # Marketing spikes in March, IT spikes in June, etc.
    actual_spends = []
    for m in months:
        if department == "Marketing" and m == "Mar":
            swing = np.random.uniform(1.4, 1.7) # Big campaign spike
        elif department == "IT & Infrastructure" and m == "Jun":
            swing = np.random.uniform(1.5, 1.9) # Big renewal spike
        else:
            swing = np.random.uniform(0.85, 1.25) # Normal variable monthly noise
            
        spend = avg_monthly_target * swing
        actual_spends.append(round(spend, 2))
        
    return pd.DataFrame({"Month": months, "Spend (QAR)": actual_spends})

# ── Sidebar Configurations ─────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ DEPT OPTIONS")
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    
    selected_dept = st.selectbox("Select Department Focus", list(DEFAULT_BUDGETS.keys()))
    
    allocated_budget = st.number_input(
        "Set Custom Annual Budget (QAR)",
        min_value=10000.0,
        max_value=5000000.0,
        value=DEFAULT_BUDGETS[selected_dept],
        step=25000.0
    )
    
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    
    # Simulation Tool: What-if slider
    burn_modifier = st.slider(
        "Simulated Spending Shift (%)", 
        min_value=-50, max_value=50, value=0, step=5,
        help="Simulate cost reduction (-) or budget increase (+)"
    )

# ── Business Logic Processing & Dynamic Projections ──────────────────────────
raw_data = generate_spending_data(selected_dept)
current_months_count = len(raw_data)

# Calculate Base Burn Metrics
total_ytd_spent = raw_data["Spend (QAR)"].sum()

# MODIFIED: Instead of a flat average, use a weighted run-rate prioritizing recent months
# Weights for Jan-Jun: Jan(1), Feb(2), Mar(3), Apr(4), May(5), Jun(6) -> Most recent months matter more
weights = np.arange(1, current_months_count + 1)
weighted_avg_burn = np.average(raw_data["Spend (QAR)"], weights=weights)

# Apply the Slider adjustment modifier to future pacing projections
projected_monthly_burn = weighted_avg_burn * (1 + (burn_modifier / 100))

# Project out the rest of the calendar year (Jul - Dec)
future_months = ["Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
all_months = list(raw_data["Month"]) + future_months

# Construct Cumulative Trackers
cumulative_spend = list(np.cumsum(raw_data["Spend (QAR)"]))
projection_line = [None] * (current_months_count - 1) + [cumulative_spend[-1]]

current_cum = cumulative_spend[-1]
for i in range(len(future_months)):
    current_cum += projected_monthly_burn
    projection_line.append(current_cum)

actual_line = cumulative_spend + [None] * len(future_months)

# Calculate Risk Trigger parameters
remaining_allowance = allocated_budget - total_ytd_spent
months_left_before_exhaustion = remaining_allowance / projected_monthly_burn if projected_monthly_burn > 0 else 999

# Determine precise target depletion boundary
exhaustion_index = current_months_count - 1 + months_left_before_exhaustion
exhaustion_alert = exhaustion_index < 11.0  

if exhaustion_alert:
    status_color = "#dc2626"
    month_idx = int(np.floor(exhaustion_index))
    target_month = all_months[min(max(month_idx, 0), 11)]
    exhaustion_status = f"RUN OUT ({target_month})"
else:
    status_color = "#16a34a"
    exhaustion_status = "SAFE (Dec+)"

# ── Executive Header Render ────────────────────────────────────────────────────
st.markdown(f'<h1 style="margin-bottom:0;">📊 BUDGET BURN-RATE FORECASTER</h1>', unsafe_allow_html=True)
st.markdown(
    f'<p style="color:#64748b;font-size:0.85rem;font-family:\'IBM Plex Mono\',monospace;margin-top:4px;">'
    f'Strategic Predictive Run-Rate Monitor &nbsp;&nbsp;|&nbsp;&nbsp; Scope: <span style="color:#2563eb;">{selected_dept}</span>'
    f"</p>",
    unsafe_allow_html=True,
)
st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

# ── Dynamic High-Fidelity KPI Row (Formatted in QAR) ───────────────────────────
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(
        f'<div class="metric-card"><div class="metric-value">{allocated_budget:,.0f} QAR</div>'
        '<div class="metric-label">Total Annual Limit</div></div>',
        unsafe_allow_html=True,
    )
with col2:
    st.markdown(
        f'<div class="metric-card"><div class="metric-value">{total_ytd_spent:,.0f} QAR</div>'
        '<div class="metric-label">YTD Capital Utilized</div></div>',
        unsafe_allow_html=True,
    )
with col3:
    st.markdown(
        f'<div class="metric-card"><div class="metric-value">{projected_monthly_burn:,.0f} QAR</div>'
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
    line=dict(color="#2563eb", width=3.5),
    mode="lines+markers"
))

# Plot predictive projection dotted segment line extension
fig.add_trace(go.Scatter(
    x=all_months, y=projection_line,
    name="Predictive Projection Pacing",
    line=dict(color="#dc2626", width=3, dash="dot"),
    mode="lines"
))

# Plot Horizontal Static Budget Boundary Cap line reference
fig.add_trace(go.Scatter(
    x=all_months, y=[float(allocated_budget)]*12,
    name="Total Budget Ceiling",
    line=dict(color="rgba(220, 38, 38, 0.3)", width=2, dash="dash"),
    mode="lines",
    showlegend=True
))

fig.update_layout(
    plot_bgcolor="#ffffff",
    paper_bgcolor="#f8fafc",
    font=dict(family="IBM Plex Sans", color="#334155"),
    xaxis=dict(gridcolor="#e2e8f0", linecolor="#cbd5e1"),
    yaxis=dict(
        title="Total Spending Vol (QAR)",
        title_font=dict(size=12, family="IBM Plex Mono"),
        gridcolor="#e2e8f0", linecolor="#cbd5e1"
    ),
    margin=dict(t=20, b=40, l=40, r=20),
    height=450,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

st.plotly_chart(fig, use_container_width=True)

# ── Data Ledger Segment Breakdown View ─────────────────────────────────────────
st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
with st.expander("📋 Data Ledger Breakdown View (QAR)"):
    st.dataframe(raw_data.set_index("Month"), use_container_width=True)
