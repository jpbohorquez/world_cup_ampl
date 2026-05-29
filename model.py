import pandas as pd
from amplpy import AMPL
import numpy as np

AMPL_MODEL = r"""
### SETS 
set GROUPS;
set TEAMS ordered;
param team_group {TEAMS} symbolic in GROUPS;
set MATCHES within {i in TEAMS, j in TEAMS: team_group[i] == team_group[j]};

### PARAMETERS
param played {MATCHES} binary default 0;
param actual_goals1 {MATCHES} integer >= 0 default 0;
param actual_goals2 {MATCHES} integer >= 0 default 0;
param target_team symbolic in TEAMS;

### VARIABLES
var Goals1 {(i,j) in MATCHES} integer >= 0, <= 10;
var Goals2 {(i,j) in MATCHES} integer >= 0, <= 10;

var Win1 {(i,j) in MATCHES} binary;
var Win2 {(i,j) in MATCHES} binary;
var Draw {(i,j) in MATCHES} binary;

var Pts {t in TEAMS} = 
    sum {(t,j) in MATCHES} (3 * Win1[t,j] + Draw[t,j]) + 
    sum {(i,t) in MATCHES} (3 * Win2[i,t] + Draw[i,t]);

var GS {t in TEAMS} = 
    sum {(t,j) in MATCHES} Goals1[t,j] + 
    sum {(i,t) in MATCHES} Goals2[i,t];

var GC {t in TEAMS} = 
    sum {(t,j) in MATCHES} Goals2[t,j] + 
    sum {(i,t) in MATCHES} Goals1[i,t];
    
var GD {t in TEAMS} = GS[t] - GC[t];

var H2H_Pts {i in TEAMS, j in TEAMS: team_group[i] == team_group[j] and i != j} =
    if (i,j) in MATCHES then (3 * Win1[i,j] + Draw[i,j]) else (3 * Win2[j,i] + Draw[j,i]);

var H2H_GD {i in TEAMS, j in TEAMS: team_group[i] == team_group[j] and i != j} =
    if (i,j) in MATCHES then (Goals1[i,j] - Goals2[i,j]) else (Goals2[j,i] - Goals1[j,i]);

var H2H_GS {i in TEAMS, j in TEAMS: team_group[i] == team_group[j] and i != j} =
    if (i,j) in MATCHES then Goals1[i,j] else Goals2[j,i];

var IsBehind {i in TEAMS, j in TEAMS: team_group[i] == team_group[j] and i != j} binary;
var GroupRank {t in TEAMS} = 1 + sum {j in TEAMS: team_group[t] == team_group[j] and t != j} IsBehind[t, j];

var GlobalIsBehind {i in TEAMS, j in TEAMS: i != j} binary;

var ThirdPlacesAhead {t in TEAMS} = 
    sum {j in TEAMS: j != t} (if GroupRank[j] == 3 and GlobalIsBehind[t, j] then 1 else 0);

var Qualifies {t in TEAMS} binary;

### CONSTRAINTS
subject to LockPlayedGoals1 {(i,j) in MATCHES: played[i,j] == 1}:
    Goals1[i,j] == actual_goals1[i,j];
    
subject to LockPlayedGoals2 {(i,j) in MATCHES: played[i,j] == 1}:
    Goals2[i,j] == actual_goals2[i,j];

subject to MatchOutcome {(i,j) in MATCHES}:
    Win1[i,j] + Win2[i,j] + Draw[i,j] == 1;

subject to Win1Logic {(i,j) in MATCHES}:
    Win1[i,j] == 1 ==> Goals1[i,j] >= Goals2[i,j] + 1;
    
subject to Win2Logic {(i,j) in MATCHES}:
    Win2[i,j] == 1 ==> Goals2[i,j] >= Goals1[i,j] + 1;
    
subject to DrawLogic {(i,j) in MATCHES}:
    Draw[i,j] == 1 ==> Goals1[i,j] == Goals2[i,j];

subject to IsBehindLogic {i in TEAMS, j in TEAMS: team_group[i] == team_group[j] and i != j}:
    IsBehind[i,j] == 1 ==>
        (Pts[i] < Pts[j]) or
        (Pts[i] == Pts[j] and H2H_Pts[i,j] < H2H_Pts[j,i]) or
        (Pts[i] == Pts[j] and H2H_Pts[i,j] == H2H_Pts[j,i] and H2H_GD[i,j] < H2H_GD[j,i]) or
        (Pts[i] == Pts[j] and H2H_Pts[i,j] == H2H_Pts[j,i] and H2H_GD[i,j] == H2H_GD[j,i] and H2H_GS[i,j] < H2H_GS[j,i]) or
        (Pts[i] == Pts[j] and H2H_Pts[i,j] == H2H_Pts[j,i] and H2H_GD[i,j] == H2H_GD[j,i] and H2H_GS[i,j] == H2H_GS[j,i] and GD[i] < GD[j]) or
        (Pts[i] == Pts[j] and H2H_Pts[i,j] == H2H_Pts[j,i] and H2H_GD[i,j] == H2H_GD[j,i] and H2H_GS[i,j] == H2H_GS[j,i] and GD[i] == GD[j] and GS[i] < GS[j]) or
        (Pts[i] == Pts[j] and H2H_Pts[i,j] == H2H_Pts[j,i] and H2H_GD[i,j] == H2H_GD[j,i] and H2H_GS[i,j] == H2H_GS[j,i] and GD[i] == GD[j] and GS[i] == GS[j] and ord(i) > ord(j));

subject to GlobalIsBehindLogic {i in TEAMS, j in TEAMS: i != j}:
    GlobalIsBehind[i,j] == 1 ==>
        (Pts[i] < Pts[j]) or
        (Pts[i] == Pts[j] and GD[i] < GD[j]) or
        (Pts[i] == Pts[j] and GD[i] == GD[j] and GS[i] < GS[j]) or
        (Pts[i] == Pts[j] and GD[i] == GD[j] and GS[i] == GS[j] and ord(i) > ord(j));

subject to QualifyingLogic {t in TEAMS}:
    Qualifies[t] == 1 <==> (GroupRank[t] <= 2) or (GroupRank[t] == 3 and ThirdPlacesAhead[t] < 8);

### OBJECTIVES
minimize WorstCase: Qualifies[target_team] + 0.5 * (sum {(i,j) in MATCHES} (Goals1[i,j] + Goals2[i,j]) / (card(MATCHES) * 20));
maximize BestCase: Qualifies[target_team] - 0.5 * (sum {(i,j) in MATCHES} (Goals1[i,j] + Goals2[i,j]) / (card(MATCHES) * 20));
"""

def run_optimization(df_teams, df_fixture, target_team, objective_name):
    ampl = AMPL()
    ampl.eval(AMPL_MODEL)
    
    # Pre-process fixtures to match AMPL expectations
    # Filter only relevant columns for solver
    df_fix_solver = df_fixture.copy()
    # Ensure team1, team2 are strings
    df_fix_solver['team1'] = df_fix_solver['team1'].astype(str)
    df_fix_solver['team2'] = df_fix_solver['team2'].astype(str)
    
    # Played flag based on whether goals are provided
    df_fix_solver['played'] = df_fix_solver.apply(
        lambda x: 1 if pd.notna(x['goals1']) and pd.notna(x['goals2']) else 0, axis=1
    )
    
    # Filter matches to only those within same group (model constraint)
    # Actually, teams_df defines which teams are in which group
    team_to_group = df_teams.set_index('team')['group'].to_dict()
    df_fix_solver['group1'] = df_fix_solver['team1'].map(team_to_group)
    df_fix_solver['group2'] = df_fix_solver['team2'].map(team_to_group)
    df_fix_solver = df_fix_solver[df_fix_solver['group1'] == df_fix_solver['group2']]
    
    # Load Sets
    ampl.set["TEAMS"] = df_teams['team'].tolist()
    ampl.set["GROUPS"] = df_teams['group'].unique().tolist()
    ampl.set["MATCHES"] = df_fix_solver[['team1', 'team2']].values.tolist()
    
    # Load Parameters
    ampl.set_data(df_teams[['team', 'group']].set_index('team').rename(columns={'group': 'team_group'}))
    
    # Match data
    match_data = df_fix_solver.set_index(['team1', 'team2'])[['played', 'goals1', 'goals2']].fillna(0)
    match_data = match_data.rename(columns={'goals1': 'actual_goals1', 'goals2': 'actual_goals2'})
    ampl.set_data(match_data)
    
    # Target team
    ampl.param['target_team'] = target_team
    
    # Solve
    ampl.eval(f"objective {objective_name};")
    options = {
        "solver": "highs",
        "highs_options": "outlev=0"
    }
    ampl.solve(**options)
    
    # Extract results
    qualifies = ampl.get_variable('Qualifies').get_values().to_pandas()
    pts = ampl.get_variable('Pts').get_values().to_pandas()
    gs = ampl.get_variable('GS').get_values().to_pandas()
    gc = ampl.get_variable('GC').get_values().to_pandas()
    gd = ampl.get_variable('GD').get_values().to_pandas()
    ranks = ampl.get_variable('GroupRank').get_values().to_pandas()
    
    match_results = ampl.get_data('{(i,j) in MATCHES} (Goals1[i,j], Goals2[i,j])').to_pandas()
    
    # Assemble standings
    standings = df_teams.set_index('team').copy()
    standings['Points'] = pts
    standings['GS'] = gs
    standings['GC'] = gc
    standings['GD'] = gd
    standings['Rank'] = ranks
    standings['Qualified'] = qualifies
    
    return {
        'standings': standings.reset_index(),
        'matches': match_results.reset_index(),
        'target_qualified': bool(qualifies.loc[target_team].values[0] > 0.5)
    }
