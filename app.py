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
    current_age = st.number_input("Current Age", 20, 80, 22)
    retirement_age = st.number_input("Target Retirement Age", current_age + 1, 100, 60)
    death_age = st.number_input("Target Depletion Age", retirement_age + 1, 120, 100)

    st.header("2. Financials")
    annual_spend = st.number_input("Annual Retirement Spend (€)", 10000, 1000000, 40000, step=1000)
    current_savings_rate = st.number_input("Current Annual Savings (€)", 0, 500000, 1000, step=500,
                                           help="Used to calculate the 'Oversaver' trajectory")

    st.header("3. Market Assumptions (Real)")
    r_coast = st.slider("Coast Growth Rate (%)", 1.0, 12.0, 7.0) / 100
    r_retire = st.slider("Decumulation Growth Rate (%)", 1.0, 10.0, 4.0) / 100

    st.header("4. Risk Controls")
    safety_buffer = st.slider("Safety Buffer (λ)", 1.0, 1.5, 1.1,
                              help="1.1 = 10% extra capital for sequence of returns risk")
    longevity_insurance = st.number_input("Longevity Insurance (€)", 0, 200000, 4999,
                                          help="Cost of deferred annuity at death age")
    

# --- Core Logic ---

# 1. TDB Calculation
n_years_retirement = death_age - retirement_age
annuity_factor = (1 - (1 + r_retire) ** -n_years_retirement) / r_retire
w_ret_needed = (annual_spend * annuity_factor * safety_buffer) + longevity_insurance

years_to_coast = retirement_age - current_age
w_tdb_today = w_ret_needed / ((1 + r_coast) ** years_to_coast)

# 2. Traditional "4% Rule" Calculation
w_trad_ret = annual_spend / 0.04
w_trad_today = w_trad_ret / ((1 + r_coast) ** years_to_coast)

# 3. Life Energy Calculation
life_energy_saved = 0.0
time_context_msg = ""

if current_savings_rate == 0:
    time_context_msg = "Input an annual savings rate > €0 to calculate time."
elif w_tdb_today >= w_trad_today:
    time_context_msg = "Your TDB constraints are so defensive it costs more than the traditional 4% rule."
else:
    # FV of Annuity formula reversed to find N (years)
    years_to_tdb = np.log((w_tdb_today * r_coast / current_savings_rate) + 1) / np.log(1 + r_coast)
    years_to_trad = np.log((w_trad_today * r_coast / current_savings_rate) + 1) / np.log(1 + r_coast)
    life_energy_saved = max(0.0, years_to_trad - years_to_tdb)
    
    # Explain small gaps dynamically
    if life_energy_saved < 3.0 and life_energy_saved > 0:
        time_context_msg = "A very long retirement horizon (e.g., 35+ years) combined with safety buffers makes TDB converge mathematically with the 4% rule, reducing the time difference."
    else:
        time_context_msg = "Years of labor you don't need to do."

# --- Metrics Display ---
st.divider()
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(label="Your TDB Number (Today)", value=f"€{w_tdb_today:,.0f}", delta="Phase 1 Complete")
    st.caption("Capital needed **today** to Coast + Die with Zero.")

with col2:
    st.metric(label="Traditional Advice", value=f"€{w_trad_today:,.0f}", delta=f"-€{w_trad_today - w_tdb_today:,.0f}",
              delta_color="inverse")
    st.caption("Capital needed today for 4% Rule (Perpetuity).")

with col3:
    st.metric(label="Life Energy Saved", value=f"{life_energy_saved:.1f} Years")
    st.caption(f"**Note:** {time_context_msg}" if "converge" in time_context_msg or "0" in time_context_msg else time_context_msg)

st.divider()

# --- Educational Expanders ---
colA, colB = st.columns(2)
with colA:
    with st.expander("⏱️ What are the 3 Lifecycle Phases?"):
        st.write("""
        The TDB model divides your financial life into three distinct phases to maximize efficiency:
        
        1. **Phase 1: Accumulation (The Grind).** You work and save aggressively until your portfolio hits exactly your TDB Number. The chart assumes you are standing at the finish line of Phase 1 today.
        2. **Phase 2: Coasting (The Growth).** You stop saving for retirement. You can spend 100% of your earnings on your current lifestyle while your portfolio grows purely through compound interest in the background.
        3. **Phase 3: Decumulation (Die With Zero).** You retire and begin withdrawing funds. The math is optimized to slowly deplete the account, aiming safely for zero exactly at your target age (leaving only your safety buffer).
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
tdb_path = []
trad_path =[]
oversaver_path =[]

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

# --- Plotly Visualization ---
st.subheader("Comparison of Strategies & Lifecycle Phases")

# Initialize Plotly Figure
fig = go.Figure()

# Add Traces (Lines)
fig.add_trace(go.Scatter(x=chart_df["Age"], y=chart_df["TDB Strategy (Optimal)"], 
                         mode='lines', name='TDB Strategy (Optimal)', line=dict(color='#1f77b4', width=3)))
fig.add_trace(go.Scatter(x=chart_df["Age"], y=chart_df["Continued Saving (Overshoot)"], 
                         mode='lines', name='Continued Saving (Overshoot)', line=dict(color='#2ca02c', width=3, dash='dot')))
fig.add_trace(go.Scatter(x=chart_df["Age"], y=chart_df["Traditional Strategy (Perpetuity)"], 
                         mode='lines', name='Traditional Strategy (Perpetuity)', line=dict(color='#d62728', width=3)))

# Add Phase Regions (Shaded Backgrounds)
# Phase 2: Coasting
fig.add_vrect(x0=current_age, x1=retirement_age, 
              fillcolor="lightblue", opacity=0.15, layer="below", line_width=0,
              annotation_text="Phase 2: Coasting", annotation_position="top left",
              annotation_font_size=14, annotation_font_color="blue")

# Phase 3: Decumulation
fig.add_vrect(x0=retirement_age, x1=death_age, 
              fillcolor="lightcoral", opacity=0.15, layer="below", line_width=0,
              annotation_text="Phase 3: Decumulation", annotation_position="top left",
              annotation_font_size=14, annotation_font_color="red")

# Add Phase 1 Marker
fig.add_vline(x=current_age, line_width=2, line_dash="dash", line_color="black",
              annotation_text="← Phase 1 (Accumulation) Complete", annotation_position="bottom right",
              annotation_font_size=12)

# Update Layout to look clean and act responsive
fig.update_layout(
    xaxis_title="Age",
    yaxis_title="Portfolio Value (€)",
    hovermode="x unified",
    legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01, bgcolor="rgba(255,255,255,0.8)"),
    margin=dict(l=0, r=0, t=30, b=0)
)

# Display the Plotly chart in Streamlit
st.plotly_chart(fig, use_container_width=True)

with st.expander("📝 How to interpret this chart"):
    st.write("""
    1. **Blue Line (TDB Strategy):** This is the efficient frontier. You hit your TDB number today, Coast to retirement without contributing another cent, and spend down to zero. *(Notice it ends slightly above zero? That is your Safety Buffer surviving!)*
    2. **Red Line (Traditional):** This assumes you aim for the rigid 4% rule. Notice how you die with a massive surplus? That is unspent life energy.
    3. **Green Dotted Line (Continued Saving):** This shows your trajectory if you hit your TDB number today but *keep saving* your current savings rate anyway out of habit. The massive vertical gap between the Green and Blue lines represents the "Waste."
    """)
