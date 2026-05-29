### SETS 
set GROUPS;
set TEAMS ordered;
# Special parameter to make sure we only consider matches within the same group.
param team_group {TEAMS} symbolic in GROUPS;
set MATCHES within {i in TEAMS, j in TEAMS: team_group[i] == team_group[j]};


### PARAMETERS

# Fixed data for matches that have already been played or simulated.
param played {MATCHES} binary default 0;
param actual_goals1 {MATCHES} integer >= 0 default 0;
param actual_goals2 {MATCHES} integer >= 0 default 0;

param target_team symbolic in TEAMS;


### VARIABLES
# Using reasonable bounds. Unplayed matches will be explored between 0 and 10 goals.
var Goals1 {(i,j) in MATCHES} integer >= 0, <= 10;
var Goals2 {(i,j) in MATCHES} integer >= 0, <= 10;

### AMPL MP DEFINED VARIABLES
# Instead of managing binary constraints, we define boolean variables directly

# 1. Match Outcomes
var Win1 {(i,j) in MATCHES} binary;
var Win2 {(i,j) in MATCHES} binary;
var Draw {(i,j) in MATCHES} binary;

# 2. Overall Aggregates
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

# 3. Head-to-Head (H2H) Variables (Step One Criteria)
# Symmetrical lookups to safely compare team i vs team j regardless of lexicographical order
var H2H_Pts {i in TEAMS, j in TEAMS: team_group[i] == team_group[j] and i != j} =
    if (i,j) in MATCHES then (3 * Win1[i,j] + Draw[i,j]) else (3 * Win2[j,i] + Draw[j,i]);

var H2H_GD {i in TEAMS, j in TEAMS: team_group[i] == team_group[j] and i != j} =
    if (i,j) in MATCHES then (Goals1[i,j] - Goals2[i,j]) else (Goals2[j,i] - Goals1[j,i]);

var H2H_GS {i in TEAMS, j in TEAMS: team_group[i] == team_group[j] and i != j} =
    if (i,j) in MATCHES then Goals1[i,j] else Goals2[j,i];

# 4. Lexicographical Sorting Operator (The Core Logic)
# IsBehind evaluates to 1 if team i is strictly ranked below team j in the group.
var IsBehind {i in TEAMS, j in TEAMS: team_group[i] == team_group[j] and i != j} binary;

# 5. Group Ranking
var GroupRank {t in TEAMS} = 1 + sum {j in TEAMS: team_group[t] == team_group[j] and t != j} IsBehind[t, j];

# 6. Global 3rd-Place Qualification Logic
# Compares any two teams in the tournament purely on 3rd-place criteria
var GlobalIsBehind {i in TEAMS, j in TEAMS: i != j} binary;

# Counts how many OTHER 3rd-place teams are globally ranked ahead of team t
var ThirdPlacesAhead {t in TEAMS} = 
    sum {j in TEAMS: j != t} (if GroupRank[j] == 3 and GlobalIsBehind[t, j] then 1 else 0);

# 7. Final Qualification
var Qualifies {t in TEAMS} binary;


### CONSTRAINTS
# Lock in the results of already played matches
subject to LockPlayedGoals1 {(i,j) in MATCHES: played[i,j] == 1}:
    Goals1[i,j] == actual_goals1[i,j];
    
subject to LockPlayedGoals2 {(i,j) in MATCHES: played[i,j] == 1}:
    Goals2[i,j] == actual_goals2[i,j];

# Match outcome definition logic
# Only one outcome is possible
subject to MatchOutcome {(i,j) in MATCHES}:
    Win1[i,j] + Win2[i,j] + Draw[i,j] == 1;

# Indicator constraints enforcing the goal logic
subject to Win1Logic {(i,j) in MATCHES}:
    Win1[i,j] == 1 ==> Goals1[i,j] >= Goals2[i,j] + 1;
    
subject to Win2Logic {(i,j) in MATCHES}:
    Win2[i,j] == 1 ==> Goals2[i,j] >= Goals1[i,j] + 1;
    
subject to DrawLogic {(i,j) in MATCHES}:
    Draw[i,j] == 1 ==> Goals1[i,j] == Goals2[i,j];

# IsBehind Logic.
# This mirrors the FIFA official criteria for World Cup 2026 (exlucing the team conduct score).
subject to IsBehindLogic {i in TEAMS, j in TEAMS: team_group[i] == team_group[j] and i != j}:
    IsBehind[i,j] == 1 <==>
        (Pts[i] < Pts[j]) or
        
        # Step One
        (Pts[i] == Pts[j] and H2H_Pts[i,j] < H2H_Pts[j,i]) or
        (Pts[i] == Pts[j] and H2H_Pts[i,j] == H2H_Pts[j,i] and H2H_GD[i,j] < H2H_GD[j,i]) or
        (Pts[i] == Pts[j] and H2H_Pts[i,j] == H2H_Pts[j,i] and H2H_GD[i,j] == H2H_GD[j,i] and H2H_GS[i,j] < H2H_GS[j,i]) or
        
        # Step Two
        (Pts[i] == Pts[j] and H2H_Pts[i,j] == H2H_Pts[j,i] and H2H_GD[i,j] == H2H_GD[j,i] and H2H_GS[i,j] == H2H_GS[j,i] and GD[i] < GD[j]) or
        (Pts[i] == Pts[j] and H2H_Pts[i,j] == H2H_Pts[j,i] and H2H_GD[i,j] == H2H_GD[j,i] and H2H_GS[i,j] == H2H_GS[j,i] and GD[i] == GD[j] and GS[i] < GS[j]) or

        # Step Three
        (Pts[i] == Pts[j] and H2H_Pts[i,j] == H2H_Pts[j,i] and H2H_GD[i,j] == H2H_GD[j,i] and H2H_GS[i,j] == H2H_GS[j,i] and GD[i] == GD[j] and GS[i] == GS[j] and ord(i) > ord(j));

subject to GlobalIsBehindLogic {i in TEAMS, j in TEAMS: i != j}:
    GlobalIsBehind[i,j] == 1 <==>
        (Pts[i] < Pts[j]) or
        (Pts[i] == Pts[j] and GD[i] < GD[j]) or
        (Pts[i] == Pts[j] and GD[i] == GD[j] and GS[i] < GS[j]) or
        (Pts[i] == Pts[j] and GD[i] == GD[j] and GS[i] == GS[j] and ord(i) > ord(j));

# Qualifying logic
subject to QualifyingLogic {t in TEAMS}:
    Qualifies[t] == 1 <==> (GroupRank[t] <= 2) or (GroupRank[t] == 3 and ThirdPlacesAhead[t] < 8);


### OBJECTIVES
# Includes a normalized total number of goals so tightest margins are always preferred.
minimize WorstCase: Qualifies[target_team] + 0.5 * (sum {(i,j) in MATCHES} (Goals1[i,j] + Goals2[i,j]) / (card(MATCHES) * 20));
maximize BestCase: Qualifies[target_team] - 0.5 * (sum {(i,j) in MATCHES} (Goals1[i,j] + Goals2[i,j]) / (card(MATCHES) * 20));