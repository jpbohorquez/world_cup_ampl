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
        options=["Highs", "Gurobi"],# "Cplex", "Xpress", "Scip"],
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

# --- Helpers ---
def get_flag(team_name):
    # Mapping of common team names to their flags
    flags = {
        "Argentina": "🇦🇷", "Australia": "🇦🇺", "Austria": "🇦🇹", "Belgium": "🇧🇪",
        "Brazil": "🇧🇷", "Canada": "🇨🇦", "Colombia": "🇨🇴", "Croatia": "🇭🇷",
        "Czechia": "🇨🇿", "Denmark": "🇩🇰", "Ecuador": "🇪🇨", "Egypt": "🇪🇬",
        "England": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "France": "🇫🇷", "Germany": "🇩🇪", "Ghana": "🇬🇭",
        "Hungary": "🇭🇺", "Iran": "🇮🇷", "Iraq": "🇮🇶", "Italy": "🇮🇹",
        "Japan": "🇯🇵", "Mexico": "🇲🇽", "Morocco": "🇲🇦", "Netherlands": "🇳🇱",
        "New Zealand": "🇳🇿", "Nigeria": "🇳🇬", "Norway": "🇳🇴", "Panama": "🇵🇦",
        "Paraguay": "🇵🇾", "Poland": "🇵🇱", "Portugal": "🇵🇹", "Qatar": "🇶🇦",
        "Saudi Arabia": "🇸🇦", "Scotland": "🏴󠁧󠁢󠁳󠁣󠁴󠁿", "Senegal": "🇸🇳", "Serbia": "🇷🇸",
        "Slovakia": "🇸🇰", "Spain": "🇪🇸", "Sweden": "🇸🇪", "Switzerland": "🇨🇭",
        "Tunisia": "🇹🇳", "Türkiye": "🇹🇷", "USA": "🇺🇸", "Uruguay": "🇺🇾",
        "Wales": "🏴󠁧󠁢󠁷󠁬󠁳󠁿", "South Africa": "🇿🇦", "South Korea": "🇰🇷", "Bosnia-Herzegovina": "🇧🇦",
        "Haiti": "🇭🇹", "Curacao": "🇨🇼", "Côte d'Ivoire": "🇨🇮", "Algeria": "🇩🇿",
        "Congo DR": "🇨🇩", "Uzbekistan": "🇺🇿", "Jordan": "🇯🇴", "Cabo Verde": "🇨🇻",
        "Ukraine": "🇺🇦", "Venezuela": "🇻🇪"
    }
    return flags.get(team_name, "🏳️")

def highlight_rows(row, target):
    # Highlight qualified in light green
    # Highlight target in a subtle red/blue
    colors = []
    is_qualified = row.get('Qualified', 0) == 1
    is_target = row.get('Team') == target
    
    for _ in row:
        if is_target:
            colors.append('background-color: #ff4b4b44; font-weight: bold')
        elif is_qualified:
            colors.append('background-color: #d1fae5')
        else:
            colors.append('')
    return colors

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

    st.markdown(f"""
        <div style='background-color: #e1f5fe; padding: 15px; border-radius: 10px; margin-bottom: 20px; text-align: center;'>
            <span style='font-size: 40px; margin-right: 10px;'>{get_flag(target_team)}</span>
            <span style='font-size: 20px;'>Team: <b>{target_team}</b> | Group: <b>{target_group}</b></span>
        </div>
    """, unsafe_allow_html=True)

    if st.button("🚀 Run Scenarios", type="primary", width='content'):
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

        # --- Creative Group Table View ---
        st.write(f"#### Group {target_group} Standings (Current/Best Case)")
        group_data = br['standings'][br['standings']['Group'] == target_group].sort_values('Rank')
        
        def highlight_target(row):
            return ['background-color: #ff4b4b22' if row.Team == target_team else '' for _ in row]

        # Centering the target group table using columns
        _, cent_col, _ = st.columns([0.05, 0.9, 0.05])
        with cent_col:
            st.dataframe(
                group_data[['Rank', 'Team', 'Points', 'GD', 'GS', 'GC']].style.apply(highlight_target, axis=1),
                hide_index=True,
                width='content'
            )

def update_fixture_data():
    # The data_editor stores edits in session state under its key.
    # Format: {"edited_rows": {"0": {"goals1": 2}}, "added_rows": [], "deleted_rows": []}
    editor_state = st.session_state["fixture_editor"]
    
    # We must map the editor's visual row index back to the master dataframe's index
    for row_pos_str, changes in editor_state["edited_rows"].items():
        row_pos = int(row_pos_str)
        # Get the actual index from the filtered dataframe we saved in session state
        actual_index = st.session_state.current_filtered_df.index[row_pos]
        
        # Apply each changed column to the master dataframe
        for col, new_val in changes.items():
            st.session_state.df_fixture.loc[actual_index, col] = new_val
            
# --- Fixtures Management (Right Column) ---
with col_fixtures:
    st.subheader("📅 Fixture Management")
    
    # Filtering UI
    f_col1, f_col2 = st.columns(2)
    # Default filter by target team's group
    filter_group = f_col1.multiselect(
        "Filter by Group", 
        options=sorted(st.session_state.df_teams['group'].unique()), 
        default=[target_group] if target_group in st.session_state.df_teams['group'].unique() else [],
        help="Focus on specific groups."
    )
    filter_team = f_col2.multiselect("Filter by Team", options=sorted(st.session_state.df_teams['team'].unique()), help="Search for a specific country's matches.")
    
    # Filter logic
    df_f = st.session_state.df_fixture.copy()
    if filter_group:
        df_f = df_f[df_f['group'].isin(filter_group)]
    if filter_team:
        df_f = df_f[(df_f['team1'].isin(filter_team)) | (df_f['team2'].isin(filter_team))]
    
    st.session_state.current_filtered_df = df_f

    st.caption("Edit results below (Goals) to lock in actual or simulated scores.")
    _, c_tab, _ = st.columns([0.25, 0.7, 0.25])
    with c_tab:
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
            width='content',
            key="fixture_editor",
            on_change=update_fixture_data
        )

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
            # Centering the table using columns
            _, c_tab, _ = st.columns([0.1, 0.8, 0.1])
            with c_tab:
                st.dataframe(
                    g_stand[['Rank', 'Team', 'Points', 'GD', 'GS', 'GC', 'Qualified']].style.apply(highlight_rows, target=target_team, axis=1),
                    hide_index=True, 
                    width='content',
                    column_config={"Qualified": None} # This hides the column but style.apply still has access to it
                )
            
            st.write("**Classification of 3rd Place Teams**")
            # Extract 3rd places
            third_places = res['standings'][res['standings']['Rank'] == 3].copy()
            third_places = third_places.sort_values('ThirdPlaceRank')            
            # Centering the table using columns
            _, c_3rd, _ = st.columns([0.1, 0.8, 0.1])
            with c_3rd:
                st.dataframe(
                    third_places[['ThirdPlaceRank', 'Team', 'Group', 'Points', 'GD', 'GS', 'Qualified']].style.apply(highlight_rows, target=target_team, axis=1),
                    hide_index=True, 
                    width='content',
                    column_config={"Qualified": None}
                )

        with sc_col2:
            st.write(f"**Group {sel_group} Projected Results**")
            
            # Map solver results by original order in session state
            solver_lookup = res['matches'].set_index(['Team1', 'Team2']).to_dict('index')
            
            # Filter original fixtures for this group
            orig_fixtures = st.session_state.df_fixture[st.session_state.df_fixture['group'] == sel_group]
            
            # Larger flag and goal size
            f_size = "32px"
            g_size = "36px"
            
            # Formatting match display in original order
            for _, row in orig_fixtures.iterrows():
                t1, t2 = row['team1'], row['team2']
                m = solver_lookup.get((t1, t2))
                if not m: continue
                
                # Highlight match if target team is playing
                prefix = "👉 " if (t1 == target_team or t2 == target_team) else ""
                
                # HTML for custom positioning and sizing (Centered)
                match_html = f"""
                <div style='display: flex; align-items: center; justify-content: center; margin-bottom: 10px; font-weight: {'bold' if prefix else 'normal'};'>
                    <div style='text-align: right; flex: 1; margin-right: 15px;'>{prefix}{t1}</div>
                    <div style='font-size: {f_size}; margin-right: 8px;'>{get_flag(t1)}</div>
                    <div style='font-size: {g_size}; min-width: 45px; text-align: center; background: #f0f2f6; border-radius: 5px; padding: 2px;'>{int(m['Goals1'])}</div>
                    <div style='font-size: {g_size}; margin: 0 10px;'>-</div>
                    <div style='font-size: {g_size}; min-width: 45px; text-align: center; background: #f0f2f6; border-radius: 5px; padding: 2px;'>{int(m['Goals2'])}</div>
                    <div style='font-size: {f_size}; margin-left: 8px;'>{get_flag(t2)}</div>
                    <div style='text-align: left; flex: 1; margin-left: 15px;'>{t2}</div>
                </div>
                """
                st.markdown(match_html, unsafe_allow_html=True)
    
    with tab_best:
        render_scenario(st.session_state.best_results, "Best")
        
    with tab_worst:
        render_scenario(st.session_state.worst_results, "Worst")
