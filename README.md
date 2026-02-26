# Targeted Depletion Benchmark (TDB) Calculator

An interactive tool based on the research paper **"The Targeted Depletion Benchmark (TDB): A Constraint-Optimization Model for Labor Cessation"** by Paul-Henry Paltmann.

This calculator helps users identify their "Minimum Critical Capital Threshold" which is the exact investment amount needed today to stop contributing to savings, coast to retirement via compound interest, and deplete assets optimally ("Die With Zero") while maintaining a safety buffer.

## The Research

- SSRN (in review): *Link will be added when published*
- Local PDF: [Targeted Depletion Benchmark.pdf](https://github.com/Paul-HenryP/TDB-Calculator/blob/433f3eacf35de07a764d331071814b995c84e616/Targeted_Depletion_Benchmark.pdf)


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

## Disclaimer
For Educational and Research Purposes Only.
This tool represents a theoretical model based on the Life-Cycle Hypothesis and does not constitute financial advice. Actual investment returns are uncertain and markets are volatile. The model assumes constant returns which do not reflect real-world sequence of returns risk. Users should consult a qualified financial advisor before making major financial decisions.
