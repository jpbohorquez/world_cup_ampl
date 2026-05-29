import streamlit as st
import pandas as pd
from model import run_optimization
import io

# --- Page Config ---
st.set_page_config(page_title="World Cup 2026 Optimization", layout="wide", page_icon="⚽")

# --- Custom Styling ---
st.markdown("""
    <style>
    .target-highlight {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 10px;
        border: 2px solid #ff4b4b;
    }
    .stDataFrame {
        border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# --- Initial Data Handling ---
DEFAULT_FILE = 'fifa_world_cup_2026.xlsx'

@st.cache_data
def load_data(file):
    df_teams = pd.read_excel(file, sheet_name='teams')
    df_fixture = pd.read_excel(file, sheet_name='fixture')
    return df_teams, df_fixture

# --- Session State ---
if 'df_teams' not in st.session_state:
    df_teams, df_fixture = load_data(DEFAULT_FILE)
    st.session_state.df_teams = df_teams
    st.session_state.df_fixture = df_fixture

# --- Sidebar ---
with st.sidebar:
    st.title("⚙️ Control Panel")
    
    st.subheader("Data Management")
    with open(DEFAULT_FILE, "rb") as f:
        st.download_button(
            label="📥 Download Excel Template",
            data=f,
            file_name="wc2026_template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            help="Download the base fixture list to fill in results locally."
        )
    
    uploaded_file = st.file_uploader("📤 Upload your results", type=["xlsx"], help="Upload an Excel with 'teams' and 'fixture' sheets.")
    if uploaded_file:
        df_teams_up, df_fixture_up = load_data(uploaded_file)
        st.session_state.df_teams = df_teams_up
        st.session_state.df_fixture = df_fixture_up
        st.success("Results imported!")

    st.divider()
    
    st.subheader("Solver Configuration")
    solver_choice = st.selectbox(
        "Choose Optimization Solver",
        options=["Highs", "Gurobi", "Cplex", "Xpress", "Cbc"],
        index=0,
        help="Select the mathematical engine to solve the scenarios. Highs is recommended for most cases."
    )
    
    if st.button("🔄 Reset Environment", help="Restore all data to original state."):
        df_teams, df_fixture = load_data(DEFAULT_FILE)
        st.session_state.df_teams = df_teams
        st.session_state.df_fixture = df_fixture
        if 'best_results' in st.session_state: del st.session_state.best_results
        if 'worst_results' in st.session_state: del st.session_state.worst_results
        st.rerun()

# --- Main Layout ---
st.title("🏆 FIFA World Cup 2026 Projection Engine")
st.markdown("Analyze mathematical qualification boundaries for any team based on current and future results.")

col_target, col_fixtures = st.columns([1, 2])

# --- Target Analytics (Left Column) ---
with col_target:
    st.subheader("🎯 Analysis Target")
    all_teams = sorted(st.session_state.df_teams['team'].unique())
    default_index = all_teams.index("New Zealand") if "New Zealand" in all_teams else 0
    target_team = st.selectbox("Select Team", options=all_teams, index=default_index, help="Pick the nation you want to analyze.")
    
    target_group = st.session_state.df_teams[st.session_state.df_teams['team'] == target_team]['group'].iloc[0]
    st.info(f"Team: **{target_team}** | Group: **{target_group}**")

    if st.button("🚀 Run Scenarios", type="primary", width='stretch'):
        with st.spinner("Solving the IP..."):
            best_results = run_optimization(st.session_state.df_teams, st.session_state.df_fixture, target_team, "BestCase", solver_choice)
            worst_results = run_optimization(st.session_state.df_teams, st.session_state.df_fixture, target_team, "WorstCase", solver_choice)
            
            if "error" in best_results:
                st.error(f"Solver Error: {best_results['error']}")
            else:
                st.session_state.best_results = best_results
                st.session_state.worst_results = worst_results
    
    if 'best_results' in st.session_state:
        st.divider()
        # Status Badge
        br = st.session_state.best_results
        wr = st.session_state.worst_results
        
        if wr['target_qualified']:
            st.success("### ✅ CLASSIFIED")
            st.caption("Mathematically guaranteed to advance regardless of other results.")
        elif br['target_qualified']:
            st.warning("### ⏳ MATHEMATICALLY ALIVE")
            st.caption("Can still qualify depending on future results.")
        else:
            st.error("### ❌ ELIMINATED")
            st.caption("No possible combination of results allows qualification.")

# --- Fixtures Management (Right Column) ---
with col_fixtures:
    st.subheader("📅 Fixture Management")
    
    # Filtering UI
    f_col1, f_col2 = st.columns(2)
    filter_group = f_col1.multiselect("Filter by Group", options=sorted(st.session_state.df_teams['group'].unique()), help="Focus on specific groups.")
    filter_team = f_col2.multiselect("Filter by Team", options=sorted(st.session_state.df_teams['team'].unique()), help="Search for a specific country's matches.")
    
    # Filter logic
    df_f = st.session_state.df_fixture.copy()
    if filter_group:
        df_f = df_f[df_f['group'].isin(filter_group)]
    if filter_team:
        df_f = df_f[(df_f['team1'].isin(filter_team)) | (df_f['team2'].isin(filter_team))]
    
    st.caption("Edit results below (Goals & Played checkbox) to lock in actual scores.")
    edited_fixture = st.data_editor(
        df_f,
        column_config={
            "team1": "Home",
            "goals1": st.column_config.NumberColumn("Goals", min_value=0, max_value=10, step=1, format="%d"),
            "goals2": st.column_config.NumberColumn("Goals", min_value=0, max_value=10, step=1, format="%d"),
            "team2": "Away",
            "group": "Group",
            "stadium": None,
        },
        disabled=["team1", "team2", "group"],
        hide_index=True,
        width='stretch',
        key="fixture_editor"
    )
    
    # Update global state from filtered editor
    if not edited_fixture.equals(df_f):
        # We need to update the original session_state.df_fixture with changes from edited_fixture
        # Match by an implicit index or just update rows that changed
        # For simplicity, we can use an index if we added one, but here we'll map back.
        # This is a bit tricky with filtering. Let's assume the user doesn't change teams.
        st.write('test')
        for idx, row in edited_fixture.iterrows():
            st.session_state.df_fixture.loc[idx, ['goals1', 'goals2']] = row[['goals1', 'goals2']]

# --- Scenario Tabs (Full Results) ---
if 'best_results' in st.session_state:
    st.divider()
    st.subheader("🔍 Full Scenario Deep Dive")
    
    tab_best, tab_worst = st.tabs(["🌟 Best-Case Projections", "🌑 Worst-Case Projections"])
    
    def render_scenario(res, scenario_key):
        sc_col1, sc_col2 = st.columns([1.5, 1])
        
        with sc_col1:
            sel_group = st.selectbox(f"Select Group to View ({scenario_key})", options=sorted(res['standings']['Group'].unique()), index=sorted(res['standings']['Group'].unique()).index(target_group))
            
            g_stand = res['standings'][res['standings']['Group'] == sel_group].sort_values('Rank')
            st.write(f"**Group {sel_group} Final Table**")
            st.dataframe(g_stand[['Rank', 'Team', 'Points', 'GD', 'GS', 'GC']], hide_index=True, width='stretch')
            
            st.write("**Classification of 3rd Place Teams**")
            # Extract 3rd places
            third_places = res['standings'][res['standings']['Rank'] == 3].copy()
            third_places = third_places.sort_values('ThirdPlaceRank')            
            st.dataframe(third_places[['ThirdPlaceRank', 'Team', 'Group', 'Points', 'GD', 'GS']], hide_index=True, width='stretch')

        with sc_col2:
            st.write(f"**Group {sel_group} Projected Results**")
            g_matches = res['matches'].copy()
            g_matches = g_matches[g_matches['Group'] == sel_group]
            # Formatting match display
            for _, m in g_matches.iterrows():
                st.markdown(f"**{m['Team1']}** {int(m['Goals1'])} - {int(m['Goals2'])} **{m['Team2']}**")
    
    with tab_best:
        render_scenario(st.session_state.best_results, "Best")
        
    with tab_worst:
        render_scenario(st.session_state.worst_results, "Worst")
