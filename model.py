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
    IsBehind[i,j] == 1 <==>
        (Pts[i] < Pts[j]) or
        (Pts[i] == Pts[j] and H2H_Pts[i,j] < H2H_Pts[j,i]) or
        (Pts[i] == Pts[j] and H2H_Pts[i,j] == H2H_Pts[j,i] and H2H_GD[i,j] < H2H_GD[j,i]) or
        (Pts[i] == Pts[j] and H2H_Pts[i,j] == H2H_Pts[j,i] and H2H_GD[i,j] == H2H_GD[j,i] and H2H_GS[i,j] < H2H_GS[j,i]) or
        (Pts[i] == Pts[j] and H2H_Pts[i,j] == H2H_Pts[j,i] and H2H_GD[i,j] == H2H_GD[j,i] and H2H_GS[i,j] == H2H_GS[j,i] and GD[i] < GD[j]) or
        (Pts[i] == Pts[j] and H2H_Pts[i,j] == H2H_Pts[j,i] and H2H_GD[i,j] == H2H_GD[j,i] and H2H_GS[i,j] == H2H_GS[j,i] and GD[i] == GD[j] and GS[i] < GS[j]) or
        (Pts[i] == Pts[j] and H2H_Pts[i,j] == H2H_Pts[j,i] and H2H_GD[i,j] == H2H_GD[j,i] and H2H_GS[i,j] == H2H_GS[j,i] and GD[i] == GD[j] and GS[i] == GS[j] and ord(i) > ord(j));

subject to GlobalIsBehindLogic {i in TEAMS, j in TEAMS: i != j}:
    GlobalIsBehind[i,j] == 1 <==>
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

def run_optimization(df_teams, df_fixture, target_team, objective_name, solver_name="highs"):
    ampl = AMPL()
    ampl.eval(AMPL_MODEL)
    
    # Ordering teams is crucial for ranking tiebreaker.
    df_teams_solver = df_teams.copy()
    df_teams_solver.sort_values(by='ranking', inplace=True)

    # Pre-process fixtures to match AMPL expectations
    df_fix_solver = df_fixture.copy()
    df_fix_solver.set_index(['team1','team2'], inplace=True)
    df_fix_solver.loc[df_fix_solver['goals1'].notna(),'played'] = 1
    
    ampl.set["TEAMS"] = df_teams_solver['team'].tolist()
    ampl.set["GROUPS"] = df_teams_solver['group'].unique().tolist()
    ampl.set["MATCHES"] = df_fix_solver.index.tolist()
    
    ampl.set_data(df_teams_solver[['team', 'group']].set_index('team').rename(columns={'group': 'team_group'}))
    
    match_data = df_fix_solver.loc[df_fix_solver['played']==1,['played','goals1','goals2']].rename(columns={'goals1':'actual_goals1','goals2':'actual_goals2'})
    ampl.set_data(match_data)
    
    ampl.param['target_team'] = target_team
    
    ampl.eval(f"objective {objective_name};")
    ampl.option["solver"] = solver_name.lower()
    
    try:
        ampl.solve()
    except Exception as e:
        return {"error": str(e)}
    
    # Extract results
    standings = ampl.get_data('''team_group, 
                              Qualifies, 
                              Pts, 
                              GS, 
                              GC, 
                              GD, 
                              GroupRank, 
                              {t in TEAMS} if GroupRank[t]==3 then 1+ThirdPlacesAhead[t] else 0''').to_pandas()
    standings.columns = ['Group', 'Qualified', 'Points', 'GS', 'GC', 'GD', 'Rank', 'ThirdPlaceRank']
    standings.reset_index(names='Team', inplace=True)


    match_results = ampl.get_data('''{(i,j) in MATCHES} 
                                  (team_group[i], 
                                  Goals1[i,j], 
                                  Goals2[i,j], 
                                  Win1[i,j], 
                                  Draw[i,j],
                                  Win2[i,j])''').to_pandas()
    match_results.columns = ['Group', 'Goals1', 'Goals2', 'Win1', 'Draw', 'Win2']
    match_results.reset_index(names=['Team1','Team2'], inplace=True)

    
    return {
        'standings': standings,
        'matches': match_results,
        'target_qualified': bool(standings.loc[standings['Team'] == target_team, 'Qualified'].values[0] > 0.5)
    }
