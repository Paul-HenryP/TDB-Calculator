import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

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
    st.markdown(f"[📄 **Read the Research Paper on SSRN**](https://ssrn.com/abstract=6556206)")
    st.divider()
    st.header("1. Profile Parameters")
    current_age = st.number_input("Current Age", 20, 80, 25)
    retirement_age = st.number_input("Target Retirement Age", current_age + 1, 100, 60)
    death_age = st.number_input("Target Depletion Age", retirement_age + 1, 120, 100)

    st.header("2. Financials")
    annual_spend = st.number_input("Annual Retirement Spend (€)", 10000, 1000000, 40000, step=1000)
    current_portfolio = st.number_input("Current Portfolio Balance (€)", 0, 5000000, 0, step=1000, help="How much you already have invested today.")
    current_savings_rate = st.number_input("Current Annual Savings (€)", 0, 500000, 15000, step=500, help="How much you contribute per year.")

    st.header("3. Market Assumptions (Real)")
    r_coast = st.slider("Coast Growth Rate (%)", 1.0, 12.0, 7.0) / 100
    r_retire = st.slider("Decumulation Growth Rate (%)", 1.0, 10.0, 4.0) / 100

    st.header("4. Risk Controls")
    safety_buffer = st.slider("Safety Buffer (λ)", 1.0, 1.5, 1.1, help="1.1 = 10% extra capital for sequence of returns risk")
    longevity_insurance = st.number_input("Longevity Insurance (€)", 0, 200000, 50000, help="Cost of deferred annuity at death age")
    

# --- Core Logic ---

# 1. TDB Targets Calculate
n_years_retirement = death_age - retirement_age
annuity_factor = (1 - (1 + r_retire) ** -n_years_retirement) / r_retire
w_ret_needed = (annual_spend * annuity_factor * safety_buffer) + longevity_insurance

years_to_coast = retirement_age - current_age
w_tdb_today = w_ret_needed / ((1 + r_coast) ** years_to_coast)

# 2. Traditional "4% Rule" Targets
w_trad_ret = annual_spend / 0.04
w_trad_today = w_trad_ret / ((1 + r_coast) ** years_to_coast)

# 3. How many years to reach these targets?
def calc_years_to_target(target_today, current_bal, savings_rate, r):
    gap = target_today - current_bal
    if gap <= 0:
        return 0.0
    if savings_rate == 0:
        return np.inf
    
    # Check if target is unreachable because interest on the gap outpaces savings
    if (gap * r / savings_rate) >= 1:
         return np.inf 
        
    return -np.log(1 - (gap * r / savings_rate)) / np.log(1 + r)

years_to_tdb = calc_years_to_target(w_tdb_today, current_portfolio, current_savings_rate, r_coast)
years_to_trad = calc_years_to_target(w_trad_today, current_portfolio, current_savings_rate, r_coast)

# 4. Life Energy Calculation & Context Messages
life_energy_saved = 0.0
time_context_msg = ""

if current_savings_rate == 0:
    time_context_msg = "Input an annual savings rate > €0 to calculate time."
elif years_to_tdb == np.inf:
    time_context_msg = "Your savings rate is too low to catch up to the compounding target curve."
elif w_tdb_today >= w_trad_today:
    time_context_msg = "Your TDB constraints are so defensive it costs more than the traditional 4% rule."
else:
    life_energy_saved = max(0.0, years_to_trad - years_to_tdb)
    
    if life_energy_saved < 3.0 and life_energy_saved > 0:
        time_context_msg = "A very long retirement horizon combined with safety buffers makes TDB converge mathematically with the 4% rule, reducing the time difference."
    else:
        time_context_msg = "Years of labor you don't need to do."

age_tdb_hit = min(retirement_age, current_age + int(np.ceil(years_to_tdb)) if years_to_tdb != np.inf else retirement_age)

# --- Metrics Display ---
st.divider()
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(label="Your TDB Baseline (Today)", value=f"€{w_tdb_today:,.0f}", delta=f"{years_to_tdb:.1f} Yrs to Goal" if years_to_tdb != np.inf else "Unreachable", delta_color="off")
    st.caption("Capital needed **today** to Coast + Die with Zero.")

with col2:
    # FIXED: Positive sign and 'inverse' color makes it show up as a RED penalty.
    st.metric(label="Traditional Baseline (Today)", value=f"€{w_trad_today:,.0f}", delta=f"+€{w_trad_today - w_tdb_today:,.0f} (Extra Cost)", delta_color="inverse")
    st.caption("Capital needed today for 4% Rule (Perpetuity).")

with col3:
    st.metric(label="Life Energy Saved", value=f"{life_energy_saved:.1f} Years")
    st.caption(f"**Note:** {time_context_msg}" if "converge" in time_context_msg or "0" in time_context_msg or "too low" in time_context_msg else time_context_msg)

st.divider()

# --- Educational Expanders ---
colA, colB = st.columns(2)
with colA:
    with st.expander("⏱️ What are the 3 Lifecycle Phases?"):
        st.write("""
        The TDB model divides your financial life into three distinct phases to maximize efficiency:
        
        1. **Phase 1: Accumulation (The Grind).** You work and save aggressively. In the chart below, this is the period where you are actively adding your annual savings to your current portfolio. You stop *the moment* you cross the TDB target curve.
        2. **Phase 2: Coasting (The Growth).** You stop saving for retirement. You can spend 100% of your earnings on your current lifestyle while your portfolio grows purely through compound interest in the background.
        3. **Phase 3: Decumulation (Die With Zero).** You retire and begin withdrawing funds. The math is optimized to slowly deplete the account, aiming safely for zero exactly at your target age.
        """)

with colB:
    with st.expander("ℹ️ What is the traditional 4% Rule?"):
        st.write("""
        The **4% Rule** (created by William Bengen in 1994) is a popular rule of thumb in personal finance. 
        It states mathematically that if you accumulate **25 times your annual expenses**, you can withdraw 4% in year one, 
        adjust for inflation every year thereafter, and never run out of money. 
        
        Because it calculates off *perpetuity* (preserving the principal forever so the portfolio never dies), 
        the TDB model argues that it forces you to over-save and work longer than necessary. 
        TDB aims to optimize depletion instead of preserving infinite wealth.
        """)

# --- Simulation for Charting ---

ages = list(range(current_age, death_age + 1))
tdb_path =[]
trad_path = []
oversaver_path =[]

# Start all paths at the USER'S CURRENT BALANCE
bal_tdb = current_portfolio
bal_trad = current_portfolio
bal_oversaver = current_portfolio

for age in ages:
    tdb_path.append(bal_tdb)
    trad_path.append(bal_trad)
    oversaver_path.append(bal_oversaver)
    
    # Calculate the dynamically moving target bounds for this specific age
    years_left_to_retire = max(0, retirement_age - age)
    target_tdb_now = w_ret_needed / ((1 + r_coast) ** years_left_to_retire)
    target_trad_now = w_trad_ret / ((1 + r_coast) ** years_left_to_retire)

    if age < retirement_age:
        # 1. TDB Strategy (Stop saving once we cross the dynamic TDB target curve)
        if bal_tdb >= target_tdb_now:
            bal_tdb = bal_tdb * (1 + r_coast) # Phase 2 (Coast)
        else:
            bal_tdb = (bal_tdb * (1 + r_coast)) + current_savings_rate # Phase 1
            
        # 2. Traditional Strategy (Stop saving once we cross the 4% rule curve)
        if bal_trad >= target_trad_now:
            bal_trad = bal_trad * (1 + r_coast) 
        else:
            bal_trad = (bal_trad * (1 + r_coast)) + current_savings_rate
            
        # 3. Oversaver (Never stops saving until retirement day)
        bal_oversaver = (bal_oversaver * (1 + r_coast)) + current_savings_rate
        
    else:
        # Decumulation Phase for everyone
        bal_tdb = (bal_tdb * (1 + r_retire)) - annual_spend
        bal_trad = (bal_trad * (1 + r_retire)) - annual_spend
        bal_oversaver = (bal_oversaver * (1 + r_retire)) - annual_spend

chart_df = pd.DataFrame({
    "Age": ages,
    "TDB Strategy (Optimal)": tdb_path,
    "Traditional Strategy (Perpetuity)": trad_path,
    "Continued Saving (Overshoot)": oversaver_path
})

# --- Plotly Visualization ---
st.subheader("Simulated Lifecycle Trajectory from Today")

fig = go.Figure()

fig.add_trace(go.Scatter(x=chart_df["Age"], y=chart_df["TDB Strategy (Optimal)"], 
                         mode='lines', name='TDB Strategy (Optimal)', line=dict(color='#1f77b4', width=3)))
fig.add_trace(go.Scatter(x=chart_df["Age"], y=chart_df["Continued Saving (Overshoot)"], 
                         mode='lines', name='Continued Saving (Overshoot)', line=dict(color='#2ca02c', width=3, dash='dot')))
fig.add_trace(go.Scatter(x=chart_df["Age"], y=chart_df["Traditional Strategy (Perpetuity)"], 
                         mode='lines', name='Traditional Strategy (Perpetuity)', line=dict(color='#d62728', width=3)))

# Define Regions
# Phase 1: Accumulation
fig.add_vrect(x0=current_age, x1=age_tdb_hit, 
              fillcolor="lightgreen", opacity=0.15, layer="below", line_width=0,
              annotation_text="Phase 1: Accumulation", annotation_position="top left",
              annotation_font_size=13, annotation_font_color="green")

# Phase 2: Coasting
if age_tdb_hit < retirement_age:
    fig.add_vrect(x0=age_tdb_hit, x1=retirement_age, 
                  fillcolor="lightblue", opacity=0.15, layer="below", line_width=0,
                  annotation_text="Phase 2: Coasting", annotation_position="top left",
                  annotation_font_size=13, annotation_font_color="blue")

# Phase 3: Decumulation
fig.add_vrect(x0=retirement_age, x1=death_age, 
              fillcolor="lightcoral", opacity=0.15, layer="below", line_width=0,
              annotation_text="Phase 3: Decumulation", annotation_position="top right",
              annotation_font_size=13, annotation_font_color="red")

fig.update_layout(
    xaxis_title="Age",
    yaxis_title="Portfolio Value (€)",
    hovermode="x unified",
    legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01, bgcolor="rgba(255,255,255,0.8)"),
    margin=dict(l=0, r=0, t=30, b=0)
)

st.plotly_chart(fig, use_container_width=True)

with st.expander("📝 How to interpret this chart"):
    st.write("""
    1. **Blue Line (TDB Strategy):** You actively save money in the green zone. The moment it enters the blue zone, **you stop saving**. Notice how it continues to grow on its own, hits your retirement target, and then safely drains toward zero.
    2. **Red Line (Traditional):** The traditional 4% rule forces you to stay in the green "saving" zone for significantly longer. You hit retirement with a massive surplus that never gets spent.
    3. **Green Dotted Line (Continued Saving):** This shows what happens if you never transition to Phase 2, and just keep mindlessly saving until the day you retire. The gap between the Green and Blue lines at the end of your life is wasted labor.
    """)
