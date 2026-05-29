import streamlit as st
import pandas as pd
from model import run_optimization

# --- Page Config ---
st.set_page_config(page_title="World Cup 2026 Qualification Dashboard", layout="wide")

# --- Initial Data Handling ---
DEFAULT_FILE = 'fifa_world_cup_2026.xlsx'

def load_data(file):
    df_teams = pd.read_excel(file, sheet_name='teams')
    df_fixture = pd.read_excel(file, sheet_name='fixture')
    return df_teams, df_fixture

# --- Session State Initialization ---
if 'df_teams' not in st.session_state:
    df_teams, df_fixture = load_data(DEFAULT_FILE)
    st.session_state.df_teams = df_teams
    st.session_state.df_fixture = df_fixture

# --- Sidebar: Data Ingestion ---
with st.sidebar:
    st.title("Settings")
    uploaded_file = st.file_uploader("Upload tournament Excel", type=["xlsx"])
    if uploaded_file:
        df_teams, df_fixture = load_data(uploaded_file)
        st.session_state.df_teams = df_teams
        st.session_state.df_fixture = df_fixture
        st.success("File uploaded successfully!")

    st.divider()
    if st.button("Reset to Default"):
        df_teams, df_fixture = load_data(DEFAULT_FILE)
        st.session_state.df_teams = df_teams
        st.session_state.df_fixture = df_fixture
        st.rerun()

# --- Main Layout ---
st.title("🏆 FIFA World Cup 2026 Qualification Bounds")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Match Fixtures")
    st.info("Edit goals below to simulate played matches.")
    # Editable match entry UI
    edited_fixture = st.data_editor(
        st.session_state.df_fixture,
        column_config={
            "goals1": st.column_config.NumberColumn("Goals 1", min_value=0, max_value=10, step=1),
            "goals2": st.column_config.NumberColumn("Goals 2", min_value=0, max_value=10, step=1),
            "played": st.column_config.CheckboxColumn("Played")
        },
        disabled=["team1", "team2", "group", "stadium"],
        hide_index=True,
        width='stretch',
        key="fixture_editor"
    )
    # Sync edited data back to session state
    st.session_state.df_fixture = edited_fixture

with col2:
    st.subheader("Analysis Target")
    target_team = st.selectbox(
        "Select team to analyze:", 
        options=sorted(st.session_state.df_teams['team'].unique()),
        index=sorted(st.session_state.df_teams['team'].unique()).index("Colombia") if "Colombia" in st.session_state.df_teams['team'].unique() else 0
    )
    
    # Run Optimization
    if st.button("Calculate Qualification Bounds", type="primary"):
        with st.spinner("Solving optimization scenarios..."):
            worst_results = run_optimization(st.session_state.df_teams, st.session_state.df_fixture, target_team, "WorstCase")
            best_results = run_optimization(st.session_state.df_teams, st.session_state.df_fixture, target_team, "BestCase")
            
            # --- Analytics Panel ---
            st.divider()
            
            # Status Badge Logic
            if worst_results['target_qualified']:
                st.success("### Status: CLASSIFIED")
            elif best_results['target_qualified']:
                st.warning("### Status: MATHEMATICALLY ALIVE")
            else:
                st.error("### Status: ELIMINATED")
            
            # Dynamic Metrics (Current standing in Worst Case scenario)
            target_data = worst_results['standings'][worst_results['standings']['team'] == target_team].iloc[0]
            m1, m2, m3 = st.columns(3)
            m1.metric("Points", int(target_data['Points']))
            m2.metric("GD", int(target_data['GD']))
            m3.metric("Group Rank", int(target_data['Rank']))
            
            # Save results to session state for display in tabs
            st.session_state.worst_results = worst_results
            st.session_state.best_results = best_results

# --- Scenario Projection Matrix ---
if 'worst_results' in st.session_state:
    st.divider()
    st.subheader("Scenario Projection Matrix")
    tab1, tab2 = st.tabs(["Worst-Case Scenario Scoreboard", "Best-Case Scenario Scoreboard"])
    
    with tab1:
        st.write("Full standings if things go as poorly as possible for your team:")
        st.dataframe(
            st.session_state.worst_results['standings'].sort_values(['group', 'Rank']),
            width='stretch',
            hide_index=True
        )
        
    with tab2:
        st.write("Full standings if everything works in your team's favor:")
        st.dataframe(
            st.session_state.best_results['standings'].sort_values(['group', 'Rank']),
            width='stretch',
            hide_index=True
        )
