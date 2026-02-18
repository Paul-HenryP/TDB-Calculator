import streamlit as st
import numpy as np
import plotly.graph_objects as go

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="TDB Calculator",
    page_icon="📉",
    layout="wide"
)

# --- INPUTS ---
st.sidebar.header("1. Profile")
current_age = st.sidebar.number_input("Current Age", 18, 90, 22)
retire_age = st.sidebar.number_input("Target Retirement Age", current_age + 1, 100, 40)
death_age = st.sidebar.number_input("Target Depletion Age (Die With Zero)", retire_age + 1, 120, 105)

st.sidebar.header("2. Financials")
currency_symbol = st.sidebar.selectbox("Currency", ["$", "€", "£"], index=1)
annual_spend = st.sidebar.number_input(f"Desired Annual Spend (Real {currency_symbol})", 10000, 1000000, 24000,
                                       step=1000)
annual_savings = st.sidebar.number_input(f"Current Annual Savings (Accumulation Rate)", 0, 500000, 12000, step=1000)

st.sidebar.header("3. Assumptions (Real Returns)")
with st.sidebar.expander("Advanced Settings", expanded=True):
    r_coast = st.number_input("Growth Rate (Coasting Phase)", 0.0, 0.15, 0.07, format="%.2f")
    r_dec = st.number_input("Growth Rate (Retirement Phase)", 0.0, 0.15, 0.04, format="%.2f")
    safety_buffer = st.number_input("Safety Buffer (Sequence Risk)", 1.0, 1.5, 1.15, format="%.2f")
    longevity_insurance = st.number_input("Longevity Insurance Cost", 0, 200000, 50000, step=5000)

# --- CORE CALCULATIONS ---

# 1. Terminal Capital (W_ret)
# Uses PV of Annuity Due formula + Safety Buffer + Insurance
years_in_retirement = death_age - retire_age

if r_dec == 0:
    base_capital_needed = annual_spend * years_in_retirement
else:
    # Annuity Due formula (payments at start of period)
    base_capital_needed = annual_spend * ((1 - (1 + r_dec) ** (-years_in_retirement)) / r_dec) * (1 + r_dec)

w_ret = (base_capital_needed * safety_buffer) + longevity_insurance

# 2. Benchmark Today (W_tdb)
# Discount W_ret back to present using coasting rate
years_to_coast = max(0, retire_age - current_age)
w_tdb = w_ret / ((1 + r_coast) ** years_to_coast)

# 3. Traditional Model Comparison
# Adjust Safe Withdrawal Rate (SWR) based on retirement duration
if years_in_retirement > 50:
    swr = 0.0325  # Conservative rate for early retirement
    swr_label = "3.25% (Early Retirement Safe Rate)"
elif years_in_retirement > 35:
    swr = 0.035
    swr_label = "3.5% (Extended Safe Rate)"
else:
    swr = 0.04
    swr_label = "4.0% (Standard Bengen Rule)"

w_trad_ret = annual_spend / swr
w_trad_today = w_trad_ret / ((1 + r_coast) ** years_to_coast)


# 4. Life Energy Analysis
# NPER calculation to determine years saved
def years_to_reach_target(target, rate, contribution):
    if contribution <= 0 or target <= 0: return 0
    if rate == 0: return target / contribution
    return np.log((target * rate + contribution) / contribution) / np.log(1 + rate)


years_to_tdb = years_to_reach_target(w_tdb, r_coast, annual_savings)
years_to_trad = years_to_reach_target(w_trad_today, r_coast, annual_savings)
years_saved = max(0, years_to_trad - years_to_tdb)

# --- SIMULATION (CHARTS) ---

ages = list(range(current_age, death_age + 5))
tdb_balance = []
trad_balance = []
waste_balance = []

current_tdb = w_tdb
current_trad = w_trad_today
current_waste = w_tdb

for age in ages:
    # A. Optimal TDB Path
    tdb_balance.append(current_tdb)
    if age < retire_age:
        current_tdb = current_tdb * (1 + r_coast)
    elif age < death_age:
        current_tdb = (current_tdb - annual_spend) * (1 + r_dec)
    else:
        current_tdb = 0  # Depletion target met

    # B. Traditional Path (Perpetuity)
    trad_balance.append(current_trad)
    if age < retire_age:
        current_trad = current_trad * (1 + r_coast)
    else:
        current_trad = (current_trad - annual_spend) * (1 + r_dec)

    # C. Waste Path (Continued Contributions)
    waste_balance.append(current_waste)
    if age < retire_age:
        current_waste = (current_waste * (1 + r_coast)) + annual_savings
    elif age < death_age:
        current_waste = (current_waste - annual_spend) * (1 + r_dec)
    else:
        current_waste = (current_waste - annual_spend) * (1 + r_dec)

# Value of unused wealth at target death age
excess_at_death = waste_balance[len(ages) - 5]

# --- DASHBOARD UI ---

st.title("Targeted Depletion Benchmark (TDB) Calculator")
st.markdown("**Based on the research paper by Paul-Henry Paltmann.**")
st.markdown(
    "Calculates the minimum invested assets required to stop saving for retirement today, assuming optimal depletion.")

st.divider()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(label="TDB Number (Today)", value=f"{currency_symbol}{w_tdb:,.0f}", delta="Goal")
    st.caption("Capital required today to coast.")

with col2:
    st.metric(label="Traditional Advice", value=f"{currency_symbol}{w_trad_today:,.0f}",
              delta=f"{currency_symbol}{w_tdb - w_trad_today:,.0f}", delta_color="inverse")
    st.caption(f"Based on {swr_label}")

with col3:
    st.metric(label="Life Energy Saved", value=f"{years_saved:.1f} Years")
    st.caption("Reduction in mandatory accumulation phase.")

with col4:
    st.metric(label="Potential Waste", value=f"{currency_symbol}{excess_at_death:,.0f}", delta="Unused")
    st.caption("Terminal wealth if savings continue.")

if w_tdb > w_trad_today and years_in_retirement > 40:
    st.warning(
        f"**Note:** Your TDB number is higher than the Traditional number because the model enforces a **{int((safety_buffer - 1) * 100)}% safety buffer** and **Insurance** for early retirement scenarios, whereas the standard 4% rule carries significant ruin risk over {years_in_retirement} years.")

st.divider()

# Plotting
fig = go.Figure()
fig.add_trace(
    go.Scatter(x=ages, y=tdb_balance, mode='lines', name='TDB Strategy (Optimal)', line=dict(color='#00CC96', width=4)))
fig.add_trace(go.Scatter(x=ages, y=trad_balance, mode='lines', name='Traditional (Perpetuity)',
                         line=dict(color='#EF553B', dash='dash')))
fig.add_trace(go.Scatter(x=ages, y=waste_balance, mode='lines', name='Continued Savings (Waste)',
                         line=dict(color='#AB63FA', width=3, dash='dot')))

fig.add_vline(x=retire_age, line_width=1, line_dash="dash", line_color="grey", annotation_text="Retirement")
fig.add_vline(x=death_age, line_width=1, line_dash="dash", line_color="grey", annotation_text="Target Depletion")

fig.update_layout(title="Wealth Trajectory & Opportunity Cost", xaxis_title="Age",
                  yaxis_title=f"Portfolio Value ({currency_symbol})", template="plotly_white")
st.plotly_chart(fig, use_container_width=True)

# Methodology Explanation
st.markdown("### Methodology")
st.info(f"""
**Model Logic:**
1.  **Target Calculation:** Determines capital required at age **{retire_age}** to fund {currency_symbol}{annual_spend:,}/year until age **{death_age}**.
2.  **Risk Management:** Applies a **{int((safety_buffer - 1) * 100)}%** sequence of returns buffer and reserves **{currency_symbol}{longevity_insurance:,}** for a longevity annuity.
3.  **Coasting:** Discounts the target capital back to the present using an aggressive growth rate ({r_coast * 100}%), assuming zero net contributions during the coasting phase.

*Note: For retirement durations exceeding 50 years, the comparative Traditional Model utilizes a adjusted Safe Withdrawal Rate of 3.25% rather than the standard 4%.*
""")

st.markdown("---")
st.caption("Research by Paul-Henry Paltmann. Tool provided for educational purposes.")