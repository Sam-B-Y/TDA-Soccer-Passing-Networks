from statsbombpy import sb
import pandas as pd
import os
from mplsoccer import Sbopen

competitionId = 12
seasonId = 27

matches = sb.matches(competition_id = competitionId, season_id = seasonId)
match_ids = matches['match_id'].tolist()

competitions = sb.competitions()

competition_row = competitions[
        (competitions['competition_id'] == competitionId) & 
        (competitions['season_id'] == seasonId)
    ]

competitionName = competition_row['competition_name'].values[0].replace(" ", "-").replace(".", "")
seasonName = competition_row['season_name'].values[0].replace("/", "-")


def saveFile(df, location):
    players = {}
    for _, row in df.iterrows():
        player_a = row['player_a']
        player_b = row['player_b']

        if player_a not in players:
            players[player_a] = {
                'x': row['x'],
                'y': row['y'],
                'passes': []
            }
        
        players[player_a]['passes'].append({
            'player_b': player_b,
            'count': row['pass_count']
        })


    with open(f'{location}.json', 'w') as f:
        f.write('[')
        for player in players:
            f.write('{')
            f.write(f'"name": "{player}",')
            f.write(f'"x": {players[player]["x"]},')
            f.write(f'"y": {players[player]["y"]},')
            f.write('"passes": [')
            for i, pass_ in enumerate(players[player]['passes']):
                f.write('{')
                f.write(f'"name": "{pass_["player_b"]}",')
                f.write(f'"count": {pass_["count"]}')
                f.write('}')
                if i != len(players[player]['passes']) - 1:
                    f.write(',')
            f.write(']')
            f.write('}')
            if player != list(players.keys())[-1]:
                f.write(',')
        f.write(']')


def processTeam(df, teamLineup, teamName, folderName, team1name):
    passesTeam1 = df[df['type_name'] == 'Pass']
    passesTeam1 = passesTeam1[['id','minute','player_id','player_name','x','y','end_x', 'end_y','pass_recipient_id','pass_recipient_name','outcome_id','outcome_name']]
    successfulPassesTeam1 = passesTeam1[passesTeam1['outcome_name'].isnull()]
    subsTeam1 = df[df['type_name'] == 'Substitution']
    firstSubTeam1 = subsTeam1['minute'].min() if not subsTeam1.empty else 150
    successfulPassesTeam1 = successfulPassesTeam1[successfulPassesTeam1['minute'] < firstSubTeam1]

    if successfulPassesTeam1.empty:
        print(f"No passes for {teamName}, therefore not saving data")
        return

    averagePosTeam1 = successfulPassesTeam1.groupby('player_name').agg({'x':'mean', 'y':['mean', 'count'] }).reset_index()
    averagePosTeam1.columns = ['player_name', 'x', 'y', 'count']
    passesToTeam1 = successfulPassesTeam1.groupby(['player_name','pass_recipient_name']).id.count().reset_index()
    passesToTeam1.rename(columns={'id':'pass_count'},inplace=True)
    passesToTeam1['sorted_pair'] = passesToTeam1.apply(
        lambda row: tuple(sorted([row['player_name'], row['pass_recipient_name']])),
        axis=1
    )
    grouped = passesToTeam1.groupby('sorted_pair', as_index=False)['pass_count'].sum()
    grouped[['player_a', 'player_b']] = pd.DataFrame(grouped['sorted_pair'].tolist(), index=grouped.index)
    passesBetweenTeam1 = grouped[['player_a', 'player_b', 'pass_count']]
    passesBetweenTeam1 = passesBetweenTeam1.sort_values(by=['player_a', 'player_b']).reset_index(drop=True)
    passesBetweenTeam1 = pd.merge(passesBetweenTeam1, averagePosTeam1, left_on='player_a', right_on='player_name')
    passesBetweenTeam1 = pd.merge(passesBetweenTeam1, averagePosTeam1, left_on='player_b', right_on='player_name', suffixes=('', '_end'))
    averagePosTeam1 = pd.merge(averagePosTeam1, teamLineup, on='player_name', how='left')
    
    if not os.path.exists(folderName):
        os.makedirs(folderName)

    if firstSubTeam1 >= 45:
        saveFile(passesBetweenTeam1.drop(columns=['count', 'count_end', 'x_end', 'y_end']), f'{folderName}/{team1name}')
    else:
        print(f"First sub before 45 minutes for {teamName}, therefore not saving data")

def saveGameStats(matchId):
    parser = Sbopen()
    df, _, _, _ = parser.event(matchId)

    teams = df['team_name'].unique()

    team1 = df[df['team_name'] == teams[0]]
    team2 = df[df['team_name'] == teams[1]]

    goals = df[df['type_name'] == 'Shot']
    goals = goals[goals['outcome_name'] == 'Goal']
    goals = goals[['minute', 'team_name']]

    team1Goals = goals[goals['team_name'] == teams[0]]
    team2Goals = goals[goals['team_name'] == teams[1]]

    subsTeam1 = team1[team1['type_name'] == 'Substitution']
    subsTeam2 = team2[team2['type_name'] == 'Substitution']

    firstSubTeam1 = subsTeam1['minute'].min() if not subsTeam1.empty else 150
    firstSubTeam2 = subsTeam2['minute'].min() if not subsTeam2.empty else 150

    team1Goals = team1Goals[team1Goals['minute'] < firstSubTeam1]
    team2Goals = team2Goals[team2Goals['minute'] < firstSubTeam2]

    team1Goals = len(team1Goals)
    team2Goals = len(team2Goals)

    lineup = parser.lineup(matchId)
    team1Lineup = lineup[lineup['team_name'] == teams[0]]
    team2Lineup = lineup[lineup['team_name'] == teams[1]]

    team1Lineup = team1Lineup[['player_name', 'player_nickname']]
    team2Lineup = team2Lineup[['player_name', 'player_nickname']]

    name = f"{matchId}_"
    folderName = f'data/{seasonName}/{competitionName}'

    team1name = name + (team1[team1['team_name'] == teams[0]]['team_name'].values[0]).replace(" ", "-") + f"_{team1Goals}_{firstSubTeam1}"
    team2name = name + (team2[team2['team_name'] == teams[1]]['team_name'].values[0]).replace(" ", "-") + f"_{team2Goals}_{firstSubTeam2}"

    processTeam(team1, team1Lineup, teams[0], folderName, team1name)
    processTeam(team2, team2Lineup, teams[1], folderName, team2name)

for matchId in match_ids:
    print(f"Processing match {matchId}")
    saveGameStats(matchId)