import pandas as pd
from amplpy import AMPL
import numpy as np

AMPL_MODEL_FILE = r"world_cup.mod"

def run_optimization(df_teams, df_fixture, target_team, objective_name, solver_name="highs"):
    ampl = AMPL()
    ampl.read(AMPL_MODEL_FILE)
    
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
    ampl.option["mp_options"] = "outlev=1 mipgapabs=0.05"
    
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
