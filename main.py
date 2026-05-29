import pandas as pd
from amplpy import AMPL

# Model creation
ampl = AMPL()
ampl.read("world_cup.mod")

# Reading data
df_teams = pd.read_excel("fifa_world_cup_2026.xlsx", sheet_name="teams")
df_teams.sort_values(by='ranking', inplace=True)

df_fixture = pd.read_excel("fifa_world_cup_2026.xlsx", sheet_name="fixture")
df_fixture.set_index(['team1','team2'], inplace=True)
df_fixture.loc[df_fixture['goals1'].notna(),'played'] = 1

# Loading data to model
ampl.set["TEAMS"] = df_teams['team'].tolist()
ampl.set["GROUPS"] = df_teams['group'].unique().tolist()
ampl.set["MATCHES"] = df_fixture.index.tolist()

ampl.set_data(df_teams[['team','group']].set_index('team').rename(columns={'group':'team_group'}))
ampl.set_data(df_fixture.loc[df_fixture['played']==1,['played','goals1','goals2']].rename(columns={'goals1':'actual_goals1','goals2':'actual_goals2'}))

ampl.param['target_team'] = 'New Zealand'

# Solving the model
ampl.eval("objective WorstCase;")
options = {
    "solver":"highs",
    "mp_options":"outlev=1"
}
ampl.solve(**options)
print("Fin")


# ampl.get_data('{(i,j) in MATCHES} (Goals1[i,j], Goals2[i,j], Win1[i,j], Draw[i,j]);').to_pandas()
# ampl.get_data('{(i,j) in MATCHES: i == "Colombia" or j == "Colombia"} (Goals1[i,j], Goals2[i,j], Win1[i,j], Draw[i,j]);').to_pandas()
# ampl.get_data("Pts").to_pandas()
# ampl.get_data('{i in TEAMS,j in TEAMS: (i,j) in MATCHES and team_group[i]=="G"} (Pts[i],H2H_Pts[i,j],H2H_Pts[j,i],H2H_GD[i,j],H2H_GD[j,i],H2H_GS[i,j],H2H_GS[j,i],GD[i],GD[j],GS[i],GS[j],ord(i), ord(j),IsBehind[i,j],GroupRank[i])').to_pandas()