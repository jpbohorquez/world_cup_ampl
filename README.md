# ⚽ FIFA World Cup 2026 Projection Engine

## Overview
This application is a sophisticated tournament scenario planner designed for the 48-team FIFA World Cup 2026 format. It leverages **Mathematical Optimization** (Mixed-Integer Programming) via the **AMPL** modeling language to calculate the precise qualification boundaries for any team.

## Purpose
In the expanded 48-team format, determining if a team is "mathematically alive" or "guaranteed to qualify" is complex due to intricate tie-breaking rules and the 3rd-place qualification paths. This tool solves for the **Best-Case** and **Worst-Case** scenarios across billions of possible future match outcomes, providing absolute certainty on a team's status.

## Key Features

### 🎯 Strategic Analysis
- **Target Selection**: Pick any of the 48 nations to analyze their specific mathematical path to the Round of 32.
- **Qualification Status**: Instant visual feedback (Success/Warning/Error) showing if a team is **CLASSIFIED**, **ALIVE**, or **ELIMINATED**.

### 📅 Interactive Fixture Management
- **Manual Score Entry**: Use the interactive data grid to input real-world results or "what-if" scores.
- **Advanced Filtering**: Quickly find matches by Group or by specific Team.
- **Persistence**: Edits are maintained in the session state, allowing for iterative analysis.

### 🎲 Probabilistic Simulation
- **Batch Simulation**: Randomly generate results for Round 1 or Rounds 1 & 2.
- **Rank-Biased Logic**: Outcomes are weighted based on FIFA World Rankings. Higher-ranked teams have a mathematically higher probability of winning, creating realistic tournament trajectories.
- **Logical Constraints**: All simulated matches follow realistic bounds (Max 5 goals per team, Max 5 goal difference).

### 🚀 Optimization Core
- **AMPL Integration**: Built on a robust optimization model that implements official FIFA tie-breaking criteria (Points, Goal Difference, Goals Scored, Head-to-Head).
- **Solver Support**: Supports high-performance solvers including **Highs** and **Gurobi**.

### 📊 Professional Visualization
- **Centered Scoreboards**: High-impact match results with large national flags (32px) and bold scores (36px).
- **Dynamic Standings**: Real-time group tables and 3rd-place rankings with automatic **green highlighting** for qualified teams and distinct highlighting for the target team.
- **Scenario Deep-Dive**: Side-by-side tabs comparing the tournament's final state under the best and worst possible outcomes.

## Tech Stack
- **Frontend**: Streamlit
- **Optimization Engine**: AMPL (amplpy)
- **Data Engine**: Pandas
- **Excel Support**: Openpyxl

## Installation & Usage

### Prerequisites
- Python 3.10+
- An AMPL installation or cloud license.

### Setup
1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install streamlit amplpy pandas openpyxl
   ```

### Running the Application
```bash
streamlit run app.py
```

### Typical Workflow
1. **Select Analysis Target**: Choose your team in the sidebar.
2. **Define Tournament State**: Manually edit the fixtures or use the **Simulation Tools** to populate the first rounds.
3. **Calculate Bounds**: Hit **"Run Scenarios"** to trigger the optimization engine.
4. **Analyze Results**: Review the generated scoreboards and tables in the scenario tabs to see the exact results needed for qualification.

---
*Designed for Operations Research and Sports Analytics.*
