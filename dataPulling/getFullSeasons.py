from statsbombpy import sb
import pandas as pd

competitions = sb.competitions()

seasons_over_100_games = []

for _, comp in competitions.iterrows():
    competition_id = comp['competition_id']
    season_id = comp['season_id']
    
    matches = sb.matches(competition_id=competition_id, season_id=season_id)
    
    if len(matches) > 100:
        seasons_over_100_games.append({
            'competition': comp['competition_name'],
            'season': comp['season_name'],
            'competition_id': competition_id,
            'season_id': season_id
        })

pd.DataFrame(seasons_over_100_games).to_json('full_seasons.json', orient='records')