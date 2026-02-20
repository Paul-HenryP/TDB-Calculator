import streamlit as st
import pandas as pd
import numpy as np

# --- Page Configuration ---
st.set_page_config(
    page_title="TDB Calculator",
    page_icon="📉",
    layout="wide"
)

# --- Header & Intro ---
st.title("Targeted Depletion Benchmark (TDB)")
st.markdown("""
**A Constraint-Optimization Model for Labor Cessation.**  
Based on the research by *Paul-Henry Paltmann*.
""")

# --- DISCLAIMER (Crucial) ---
st.warning("""
**Disclaimer:** This tool is for educational and research purposes only. 
It represents a theoretical model based on the Life-Cycle Hypothesis and does not constitute financial advice. 
Actual investment returns are uncertain. Users should consult a qualified financial advisor before making decisions.
""")

# --- Sidebar: User Inputs ---
with st.sidebar:
    st.header("1. Profile Parameters")
    current_age = st.number_input("Current Age", 20, 80, 30)
    retirement_age = st.number_input("Target Retirement Age", current_age + 1, 100, 60)
    death_age = st.number_input("Target Depletion Age", retirement_age + 1, 110, 95)

    st.header("2. Financials")
    annual_spend = st.number_input("Annual Retirement Spend ($)", 10000, 1000000, 50000, step=1000)
    current_savings_rate = st.number_input("Current Annual Savings ($)", 0, 500000, 20000, step=500,
                                           help="Used to calculate the 'Oversaver' trajectory")

    st.header("3. Market Assumptions (Real)")
    r_coast = st.slider("Coast Growth Rate (%)", 1.0, 12.0, 7.0) / 100
    r_retire = st.slider("Decumulation Growth Rate (%)", 1.0, 10.0, 4.0) / 100

    st.header("4. Risk Controls")
    safety_buffer = st.slider("Safety Buffer (λ)", 1.0, 1.5, 1.1,
                              help="1.1 = 10% extra capital for sequence of returns risk")
    longevity_insurance = st.number_input("Longevity Insurance ($)", 0, 200000, 50000,
                                          help="Cost of deferred annuity at death age")

# --- Core Logic ---

n_years_retirement = death_age - retirement_age
annuity_factor = (1 - (1 + r_retire) ** -n_years_retirement) / r_retire
w_ret_needed = (annual_spend * annuity_factor * safety_buffer) + longevity_insurance

years_to_coast = retirement_age - current_age
w_tdb_today = w_ret_needed / ((1 + r_coast) ** years_to_coast)

w_trad_ret = annual_spend / 0.04
w_trad_today = w_trad_ret / ((1 + r_coast) ** years_to_coast)

if current_savings_rate > 0:
    years_to_tdb = np.log((w_tdb_today * r_coast / current_savings_rate) + 1) / np.log(1 + r_coast)
    years_to_trad = np.log((w_trad_today * r_coast / current_savings_rate) + 1) / np.log(1 + r_coast)
    life_energy_saved = max(0, years_to_trad - years_to_tdb)
else:
    life_energy_saved = 0

# --- Metrics Display ---
st.divider()
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(label="Your TDB Number (Today)", value=f"${w_tdb_today:,.0f}", delta="Stop Saving Here")
    st.caption("Capital needed **today** to Coast + Die with Zero.")

with col2:
    st.metric(label="Traditional Advice", value=f"${w_trad_today:,.0f}", delta=f"-${w_trad_today - w_tdb_today:,.0f}",
              delta_color="inverse")
    st.caption("Capital needed today for 4% Rule (Perpetuity).")

with col3:
    st.metric(label="Life Energy Saved", value=f"{life_energy_saved:.1f} Years")
    st.caption("Years of labor you don't need to do.")

st.divider()

# --- Simulation for Charting ---

ages = list(range(current_age, death_age + 1))
tdb_path = []
trad_path = []
oversaver_path = []

bal_tdb = w_tdb_today
bal_trad = w_trad_today
bal_oversaver = w_tdb_today  # Starts with TDB amount but KEEPS saving

for age in ages:
    tdb_path.append(bal_tdb)
    trad_path.append(bal_trad)
    oversaver_path.append(bal_oversaver)

    if age < retirement_age:
        # Accumulation / Coast Phase
        bal_tdb = bal_tdb * (1 + r_coast)
        bal_trad = bal_trad * (1 + r_coast)
        bal_oversaver = (bal_oversaver * (1 + r_coast)) + current_savings_rate
    else:
        # Decumulation Phase
        bal_tdb = (bal_tdb * (1 + r_retire)) - annual_spend
        bal_trad = (bal_trad * (1 + r_retire)) - annual_spend
        bal_oversaver = (bal_oversaver * (1 + r_retire)) - annual_spend

chart_df = pd.DataFrame({
    "Age": ages,
    "TDB Strategy (Optimal)": tdb_path,
    "Traditional Strategy (Perpetuity)": trad_path,
    "Continued Saving (Overshoot)": oversaver_path
})

# --- Visualization ---
st.subheader("Comparison of Strategies")
st.line_chart(chart_df, x="Age",
              y=["TDB Strategy (Optimal)", "Traditional Strategy (Perpetuity)", "Continued Saving (Overshoot)"],
              color=["#0000FF", "#FF0000", "#00FF00"])

with st.expander("📝 How to interpret this chart"):
    st.write("""
    1. **Blue Line (TDB Strategy):** This is the efficient frontier. You stop saving today, coast to retirement, and spend down to zero (with a safety buffer).
    2. **Red Line (Traditional):** This assumes you aim for the 4% rule. Notice how you die with a massive surplus? That is unspent life energy.
    3. **Green Line (Continued Saving):** This shows what happens if you hit your TDB number today but *keep saving* anyway. The massive gap between the Green and Blue lines represents the "Waste."
    """)