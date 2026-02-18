# Targeted Depletion Benchmark (TDB) Calculator

An interactive tool based on the research paper **"The Targeted Depletion Benchmark (TDB): A Constraint-Optimization Model for Labor Cessation"** by Paul-Henry Paltmann.

This calculator helps users identify their "Minimum Critical Capital Threshold" which is the exact investment amount needed today to stop contributing to savings, coast to retirement via compound interest, and deplete assets optimally ("Die With Zero") while maintaining a safety buffer.

## The Research
You can read the full research note on SSRN: [Link]

## How to Run Locally

1. **Clone the repository**
   ```bash
   git clone https://github.com/Paul-HenryP/TDB-Calculator.git

Install requirements

```bash
pip install -r requirements.txt
```
Run the app

```bash
streamlit run app.py
```
## Methodology
The model compares two financial paths:
- The Traditional Model: Accumulating enough capital to sustain a 4% withdrawal rate in perpetuity (preserving principal).


- The TDB Model: Accumulating just enough capital to fund consumption until a specific age (e.g., 95), ending with zero, utilizing a safety buffer and longevity insurance to manage risk.
The difference between these two numbers represents "Life Energy" which is years of labor that can be reclaimed.
