from statsbombpy import sb
import pandas as pd
import os
from mplsoccer import Sbopen

competitionId = 9
seasonId = 281

matches = sb.matches(competition_id = competitionId, season_id = seasonId)
match_ids = matches['match_id'].tolist()

def saveGameStats(matchId):
    parser = Sbopen()
    df, _, _, _ = parser.event(matchId)

    teams = df['team_name'].unique()

    team1 = df[df['team_name'] == teams[0]]
    team2 = df[df['team_name'] == teams[1]]

    passesTeam1 = team1[team1['type_name'] == 'Pass']
    passesTeam2 = team2[team2['type_name'] == 'Pass']

    passesTeam1 = passesTeam1[['id','minute','player_id','player_name','x','y','end_x', 'end_y','pass_recipient_id','pass_recipient_name','outcome_id','outcome_name']]
    passesTeam2 = passesTeam2[['id','minute','player_id','player_name','x','y','end_x', 'end_y','pass_recipient_id','pass_recipient_name','outcome_id','outcome_name']]

    successfulPassesTeam1 = passesTeam1[passesTeam1['outcome_name'].isnull()]
    successfulPassesTeam2 = passesTeam2[passesTeam2['outcome_name'].isnull()]

    subsTeam1 = team1[team1['type_name'] == 'Substitution']
    subsTeam2 = team2[team2['type_name'] == 'Substitution']

    firstSubTeam1 = subsTeam1['minute'].min()
    firstSubTeam2 = subsTeam2['minute'].min()

    successfulPassesTeam1 = successfulPassesTeam1[successfulPassesTeam1['minute'] < firstSubTeam1]
    successfulPassesTeam2 = successfulPassesTeam2[successfulPassesTeam2['minute'] < firstSubTeam2]

    averagePosTeam1 = successfulPassesTeam1.groupby('player_name').agg({'x':'mean', 'y':['mean', 'count'] }).reset_index()
    averagePosTeam2 = successfulPassesTeam2.groupby('player_name').agg({'x':'mean', 'y':['mean', 'count']}).reset_index()

    averagePosTeam1.columns = ['player_name', 'x', 'y', 'count']
    averagePosTeam2.columns = ['player_name', 'x', 'y', 'count']

    passesToTeam1 = successfulPassesTeam1.groupby(['player_name','pass_recipient_name']).id.count().reset_index()
    passesToTeam1.rename(columns={'id':'pass_count'},inplace=True)

    passesToTeam2 = successfulPassesTeam2.groupby(['player_name','pass_recipient_name']).id.count().reset_index()
    passesToTeam2.rename(columns={'id':'pass_count'},inplace=True)

    passesToTeam1['sorted_pair'] = passesToTeam1.apply(
        lambda row: tuple(sorted([row['player_name'], row['pass_recipient_name']])),
        axis=1
    )

    grouped = passesToTeam1.groupby('sorted_pair', as_index=False)['pass_count'].sum()
    grouped[['player_a', 'player_b']] = pd.DataFrame(grouped['sorted_pair'].tolist(), index=grouped.index)
    passesBetweenTeam1 = grouped[['player_a', 'player_b', 'pass_count']]
    passesBetweenTeam1 = passesBetweenTeam1.sort_values(by=['player_a', 'player_b']).reset_index(drop=True)

    passesToTeam2['sorted_pair'] = passesToTeam2.apply(
        lambda row: tuple(sorted([row['player_name'], row['pass_recipient_name']])),
        axis=1
    )

    grouped = passesToTeam2.groupby('sorted_pair', as_index=False)['pass_count'].sum()
    grouped[['player_a', 'player_b']] = pd.DataFrame(grouped['sorted_pair'].tolist(), index=grouped.index)
    passesBetweenTeam2 = grouped[['player_a', 'player_b', 'pass_count']]
    passesBetweenTeam2 = passesBetweenTeam2.sort_values(by=['player_a', 'player_b']).reset_index(drop=True)

    passesBetweenTeam1 = pd.merge(passesBetweenTeam1, averagePosTeam1, left_on='player_a', right_on='player_name')
    passesBetweenTeam2 = pd.merge(passesBetweenTeam2, averagePosTeam2, left_on='player_a', right_on='player_name')

    passesBetweenTeam1 = pd.merge(passesBetweenTeam1, averagePosTeam1, left_on='player_b', right_on='player_name', suffixes=('', '_end'))
    passesBetweenTeam2 = pd.merge(passesBetweenTeam2, averagePosTeam2, left_on='player_b', right_on='player_name', suffixes=('', '_end'))

    passesBetweenTeam1 = passesBetweenTeam1[['player_a', 'x', 'y', 'count', 'player_b', 'x_end', 'y_end', 'count_end', 'pass_count']]
    passesBetweenTeam2 = passesBetweenTeam2[['player_a', 'x', 'y', 'count', 'player_b', 'x_end', 'y_end', 'count_end', 'pass_count']]

    lineup = parser.lineup(matchId)
    team1Lineup = lineup[lineup['team_name'] == teams[0]]
    team2Lineup = lineup[lineup['team_name'] == teams[1]]

    team1Lineup = team1Lineup[['player_name', 'player_nickname']]
    team2Lineup = team2Lineup[['player_name', 'player_nickname']]

    averagePosTeam1 = pd.merge(averagePosTeam1, team1Lineup, on='player_name', how='left')
    averagePosTeam2 = pd.merge(averagePosTeam2, team2Lineup, on='player_name', how='left')

    goals = df[df['type_name'] == 'Shot']
    goals = goals[goals['outcome_name'] == 'Goal']
    goals = goals[['minute', 'team_name']]

    team1Goals = goals[goals['team_name'] == teams[0]]
    team2Goals = goals[goals['team_name'] == teams[1]]

    team1Goals = team1Goals[team1Goals['minute'] < firstSubTeam1]
    team2Goals = team2Goals[team2Goals['minute'] < firstSubTeam2]

    team1Goals = len(team1Goals)
    team2Goals = len(team2Goals)

    name = f"{matchId}_"

    team1name = name + (team1[team1['team_name'] == teams[0]]['team_name'].values[0]).replace(" ", "-") + f"_{team1Goals}_{firstSubTeam1}"
    team2name = name + (team2[team2['team_name'] == teams[1]]['team_name'].values[0]).replace(" ", "-") + f"_{team2Goals}_{firstSubTeam2}"

    if not os.path.exists(f'data/{competitionId}/{seasonId}'):
        os.makedirs(f'data/{competitionId}/{seasonId}')

    if firstSubTeam1 > 30:
        passesBetweenTeam1.drop(columns=['count', 'count_end', 'x_end', 'y_end']).to_csv(f'data/{competitionId}/{seasonId}/{team1name}.csv', index=False)
    else:
        print(f"First sub before 30 minutes for {(team1[team1['team_name'] == teams[0]]['team_name'].values[0])} for match {matchId}, therefore not saving data")

    if firstSubTeam2 > 30:
        passesBetweenTeam2.drop(columns=['count', 'count_end', 'x_end', 'y_end']).to_csv(f'data/{competitionId}/{seasonId}/{team2name}.csv', index=False)
    else:
        print(f"First sub before 30 minutes for {(team2[team2['team_name'] == teams[1]]['team_name'].values[0])} for match {matchId}, therefore not saving data")
        
for matchId in match_ids:
    saveGameStats(matchId)