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
*Note: All monetary outputs and inputs are in today's purchasing power (inflation-adjusted).*
""")

# --- DISCLAIMER ---
st.warning("""
**Disclaimer:** This tool is for educational and research purposes only. 
It represents a theoretical model based on the Life-Cycle Hypothesis and does not constitute financial advice. 
Actual investment returns are uncertain. Users should consult a qualified financial advisor before making decisions.
""")

# --- Sidebar: User Inputs ---
with st.sidebar:
    st.markdown("[📄 **Read the Research Paper on SSRN**](https://ssrn.com/abstract=6556206)")
    st.divider()
    
    st.header("1. Profile Parameters")
    current_age = st.number_input("Current Age", 20, 80, 25, 
                                  help="Your current age, marking the start of Phase 1 (Accumulation/The Grind).")
    retirement_age = st.number_input("Target Retirement Age", current_age + 1, 100, 60, 
                                     help="The age you plan to stop working and begin drawing down your portfolio (Start of Phase 3).")
    death_age = st.number_input("Target Depletion Age", retirement_age + 1, 120, 100, 
                                help="The exact age your portfolio mathematically hits €0. TDB uses this finite life horizon to prevent over-saving. To mitigate longevity risk, this is paired with the Longevity Insurance parameter below.")

    st.header("2. Financials")
    annual_spend = st.number_input("Annual Retirement Spend (€)", 10000, 1000000, 40000, step=1000, 
                                   help="Your desired yearly spending in retirement, expressed in today's purchasing power (inflation-adjusted).")
    current_portfolio = st.number_input("Current Portfolio Balance (€)", 0, 5000000, 0, step=1000, 
                                        help="The capital you have completely invested today. The TDB model calculates the gap between this and your Coast target.")
    current_savings_rate = st.number_input("Current Annual Savings (€)", 0, 500000, 15000, step=500, 
                                           help="Your yearly contribution speed. Used to calculate how many 'Years of Labor' (Life Energy) you have left until you hit the exact TDB benchmark.")

    st.header("3. Market Assumptions (Real)")
    r_coast = st.slider("Coast Growth Rate (%)", 1.0, 12.0, 7.0, 
                        help="Expected real (after-inflation) return during the Accumulation & Coasting phases. This usually assumes a more aggressive, equity-heavy portfolio.") / 100
    r_retire = st.slider("Decumulation Growth Rate (%)", 1.0, 10.0, 4.0, 
                         help="Expected real return during retirement. Usually lower (e.g., 4%) to reflect a conservative, bond-weighted portfolio designed to limit volatility.") / 100

    st.header("4. Risk Controls")
    safety_buffer = st.slider("Safety Buffer (λ)", 1.0, 1.5, 1.1, 
                              help="A mathematical multiplier (e.g., 1.10 = 10% extra capital) that acts as a structural defense against Sequence of Returns Risk (SRR). It buffers the portfolio so an early market crash doesn't ruin the depletion plan.")
    longevity_insurance = st.number_input("Longevity Insurance (€)", 0, 200000, 50000, 
                                          help="The estimated cost of a Deferred Income Annuity (DIA) purchased at retirement. It pays out only if you live PAST your Target Depletion Age, acting as a tail-risk hedge so you can safely aim for a zero terminal wealth without fear of starvation.")

# --- Core Logic ---

n_years_retirement = death_age - retirement_age
annuity_factor = (1 - (1 + r_retire) ** -n_years_retirement) / r_retire
w_ret_needed = (annual_spend * annuity_factor * safety_buffer) + longevity_insurance

years_to_coast = retirement_age - current_age
w_tdb_today = w_ret_needed / ((1 + r_coast) ** years_to_coast)

w_trad_ret = annual_spend / 0.04
w_trad_today = w_trad_ret / ((1 + r_coast) ** years_to_coast)

def calc_years_to_target(target_today, current_bal, savings_rate, r):
    gap = target_today - current_bal
    if gap <= 0:
        return 0.0
    if savings_rate == 0 or (gap * r / savings_rate) >= 1:
        return np.inf 
    return -np.log(1 - (gap * r / savings_rate)) / np.log(1 + r)

years_to_tdb = calc_years_to_target(w_tdb_today, current_portfolio, current_savings_rate, r_coast)
years_to_trad = calc_years_to_target(w_trad_today, current_portfolio, current_savings_rate, r_coast)

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
    if 0 < life_energy_saved < 3.0:
        time_context_msg = "A very long retirement horizon combined with high safety buffers makes TDB converge mathematically with the 4% rule."
    else:
        time_context_msg = "Years of labor you don't need to do."

age_tdb_hit = min(retirement_age, current_age + int(np.ceil(years_to_tdb)) if years_to_tdb != np.inf else retirement_age)
age_trad_hit = min(retirement_age, current_age + int(np.ceil(years_to_trad)) if years_to_trad != np.inf else retirement_age)

# --- Metrics Display ---
st.divider()
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(label="Your TDB Baseline (Today)", value=f"€{w_tdb_today:,.0f}", delta=f"{years_to_tdb:.1f} Yrs to Goal" if years_to_tdb != np.inf else "Unreachable", delta_color="off")
    st.caption("Capital needed **today** to Coast + Die with Zero.")

with col2:
    st.metric(label="Traditional Baseline (Today)", value=f"€{w_trad_today:,.0f}", delta=f"+€{w_trad_today - w_tdb_today:,.0f} (Extra Cost)", delta_color="inverse")
    st.caption("Capital needed today for 4% Rule (Perpetuity).")

with col3:
    st.metric(label="Life Energy Saved", value=f"{life_energy_saved:.1f} Years")
    st.caption(f"**Note:** {time_context_msg}" if "converge" in time_context_msg or "0" in time_context_msg or "too low" in time_context_msg else time_context_msg)

st.divider()

colA, colB = st.columns(2)
with colA:
    with st.expander("⏱️ What are the 3 Lifecycle Phases?"):
        st.write("""
        1. **Phase 1: Accumulation (The Grind).** You work and save aggressively. You stop *the moment* you cross the target curve.
        2. **Phase 2: Coasting (The Growth).** You stop saving for retirement and spend 100% of your earnings on current lifestyle while your portfolio grows through compound interest.
        3. **Phase 3: Decumulation (Die With Zero).** You retire and begin withdrawing funds. The math is optimized to slowly deplete the account towards zero at your target age.
        """)
with colB:
    with st.expander("ℹ️ What is the traditional 4% Rule?"):
        st.write("""
        The **4% Rule** (Bengen, 1994) assumes you accumulate **25 times your annual expenses** so you can withdraw funds in perpetuity without running out.
        Because it optimizes for infinite wealth preservation, the TDB model demonstrates it forces individuals to over-save and work unnecessarily long.
        """)

# --- Simulation for Charting ---
ages = list(range(current_age, death_age + 1))
tdb_path, trad_path, oversaver_path = [], [],[]
bal_tdb = bal_trad = bal_oversaver = current_portfolio

for age in ages:
    tdb_path.append(bal_tdb)
    trad_path.append(bal_trad)
    oversaver_path.append(bal_oversaver)
    
    years_left_to_retire = max(0, retirement_age - age)
    target_tdb_now = w_ret_needed / ((1 + r_coast) ** years_left_to_retire)
    target_trad_now = w_trad_ret / ((1 + r_coast) ** years_left_to_retire)

    if age < retirement_age:
        bal_tdb = bal_tdb * (1 + r_coast) if bal_tdb >= target_tdb_now else (bal_tdb * (1 + r_coast)) + current_savings_rate
        bal_trad = bal_trad * (1 + r_coast) if bal_trad >= target_trad_now else (bal_trad * (1 + r_coast)) + current_savings_rate
        bal_oversaver = (bal_oversaver * (1 + r_coast)) + current_savings_rate
    else:
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

fig.add_trace(go.Scatter(x=[None], y=[None], mode='lines', name='TDB Goal Reached (Stop Saving)', 
                         line=dict(color='#1f77b4', width=2, dash='dash')))

if age_trad_hit < retirement_age and age_trad_hit != age_tdb_hit:
    fig.add_trace(go.Scatter(x=[None], y=[None], mode='lines', name='4% Rule Goal Reached', 
                             line=dict(color='#d62728', width=2, dash='dash')))

fig.add_vrect(x0=current_age, x1=age_tdb_hit, 
              fillcolor="lightgreen", opacity=0.15, layer="below", line_width=0,
              annotation_text="Phase 1: Accumulation", annotation_position="top left",
              annotation_font_size=13, annotation_font_color="green")

if age_tdb_hit < retirement_age:
    fig.add_vrect(x0=age_tdb_hit, x1=retirement_age, 
                  fillcolor="lightblue", opacity=0.15, layer="below", line_width=0,
                  annotation_text="Phase 2: Coasting", annotation_position="top left",
                  annotation_font_size=13, annotation_font_color="blue")

fig.add_vrect(x0=retirement_age, x1=death_age, 
              fillcolor="lightcoral", opacity=0.15, layer="below", line_width=0,
              annotation_text="Phase 3: Decumulation", annotation_position="top right",
              annotation_font_size=13, annotation_font_color="red")

fig.add_vline(x=age_tdb_hit, line_width=2, line_dash="dash", line_color="#1f77b4")

if age_trad_hit < retirement_age and age_trad_hit != age_tdb_hit:
    fig.add_vline(x=age_trad_hit, line_width=2, line_dash="dash", line_color="#d62728")

fig.update_layout(
    xaxis_title="Age",
    yaxis_title="Portfolio Value (€)",
    hovermode="x unified",
    legend=dict(
        orientation="h",
        yanchor="bottom", y=1.05,
        xanchor="center", x=0.5
    ),
    margin=dict(l=0, r=0, t=50, b=0)
)

st.plotly_chart(fig, use_container_width=True)

with st.expander("📝 How to interpret this chart"):
    st.write("""
    1. **Blue Line (TDB Strategy):** You actively save money in the green zone. The moment you hit the target (dashed blue line), you stop saving, coast to retirement, and safely deplete towards zero.
    2. **Red Line (Traditional):** The traditional 4% rule forces you to save for significantly longer (dashed red line). You hit retirement with a massive surplus that never gets spent.
    3. **Green Dotted Line (Continued Saving):** This shows what happens if you never transition to Phase 2 and keep mindlessly saving until retirement. The gap between the Green and Blue lines represents wasted labor.
    """)

st.divider()

with st.expander("💡 Why does TDB only save me 1-2 years? (The TDB 'Sweet Spot')"):
    st.markdown("""
    If you are in your 20s and planning an early retirement, you might notice the "Life Energy Saved" is only 1 or 2 years. Did the math fail? No! 
    
    You have discovered a fundamental mathematical truth about compound interest. Here is why it happens, and who TDB actually helps the most.
    
    ### 1. The Annuity Trap (Too long in retirement)
    If you retire at 40 and plan to live to 100, your portfolio has to last **60 years**. In finance, the cost of a 60-year annuity is mathematically almost identical to the cost of a perpetuity (an account that lasts forever). Because the timelines are so long, the TDB Target simply converges with the Traditional 4% Rule.
    
    ### 2. The Discount Trap (Too much time to compound)
    Even if the Traditional method requires €300,000 more than TDB at age 65, if you are 25 today, that €300,000 gap is heavily discounted by 40 years of 7% compound growth. The actual difference *today* between the two targets might only be €15,000. If you are saving €15,000 a year, you bridge that gap with just 1 year of extra work.
    
    ### The TDB Sweet Spot
    This model is not a cheat code for 25-year-olds to retire at 30. **TDB is a mathematical exit strategy for mid-career professionals (age 40-55) looking to escape the "One More Year" syndrome.** 
    
    **Example: The 45-Year-Old Manager**
    * **Profile:** Age 45, Retire at 65, Die at 95. Target Spend: €40k/yr. Current Savings Rate: €10k/yr.
    * **TDB Target Today:** ~€196,000
    * **Traditional Target Today:** ~€258,000
    * **Life Energy Saved: 19+ Years!**
    
    For this 45-year-old, trying to reach the Traditional €258k target on a €10k savings rate is a punishing 20-year grind because the goal keeps compounding away from them. TDB proves mathematically that if they have €196k today, they can quit their stressful job, take a low-stress "Coast" job to just cover their daily bills, and effectively reclaim nearly two decades of their life!
    """)
