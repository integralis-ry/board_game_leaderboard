from flask import Flask, render_template, jsonify
from datetime import datetime, timedelta
import pandas as pd
import requests
import io
from functools import lru_cache
from collections import Counter, defaultdict

app = Flask(__name__)

GAME_SHEETS = {
    'liar': {
        'file_id': '1iP6HM9LD83HjD8re67HQXv3mvMsT2WhlhCJbxtdM50I',
        'gid': '2070149683',
        'is_other': False
    },
    'exploding_kittens': {
        'file_id': '1iP6HM9LD83HjD8re67HQXv3mvMsT2WhlhCJbxtdM50I',
        'gid': '2019478915',
        'is_other': False
    },
    'catan': {
        'file_id': '1iP6HM9LD83HjD8re67HQXv3mvMsT2WhlhCJbxtdM50I',
        'gid': '1688842077',
        'is_other': False
    },
    'durak': {
        'file_id': '1iP6HM9LD83HjD8re67HQXv3mvMsT2WhlhCJbxtdM50I',
        'gid': '155829382',
        'is_other': False
    },
    'toots': {
        'file_id': '1iP6HM9LD83HjD8re67HQXv3mvMsT2WhlhCJbxtdM50I',
        'gid': '7347227',
        'is_other': False
    },
    'chess': {
        'file_id': '1iP6HM9LD83HjD8re67HQXv3mvMsT2WhlhCJbxtdM50I',
        'gid': '711787286',
        'is_other': False
    },
    'other': {
        'file_id': '1iP6HM9LD83HjD8re67HQXv3mvMsT2WhlhCJbxtdM50I',
        'gid': '1630488011',
        'is_other': True
    }
}

STANDARD_COLUMNS = [
    'Timestamp',
    'Winner',
    'Player1',
    'Player2',
    'Player3',
    'Player4',
    'Player5',
    'Player6',
    'Player7',
    'Player8',
    'Player9',
    'Player10',
    'Strategy',
    'Shenanigans'
]

OTHER_COLUMNS = [
    'Timestamp',
    'GameType',
    'Winner',
    'Player1',
    'Player2',
    'Player3',
    'Player4',
    'Player5',
    'Player6',
    'Player7',
    'Player8',
    'Player9',
    'Player10',
    'Strategy',
    'Shenanigans',
    'ExtraColumn1',
    'ExtraColumn2'
]

@lru_cache(maxsize=len(GAME_SHEETS))
def fetch_sheet_data_cached(game_type, cache_key):
    sheet_config = GAME_SHEETS.get(game_type)
    if not sheet_config:
        return create_empty_dataframe(game_type)
        
    export_url = f"https://docs.google.com/spreadsheets/d/{sheet_config['file_id']}/export?format=csv&gid={sheet_config['gid']}"
    
    try:
        response = requests.get(export_url)
        response.raise_for_status()
        if not response.text.strip():
            return create_empty_dataframe(game_type)
            
        df = pd.read_csv(io.StringIO(response.text))
        
        if df.empty:
            return create_empty_dataframe(game_type)
        
        if sheet_config['is_other']:
            df.columns = OTHER_COLUMNS[:len(df.columns)]
        else:
            df.columns = STANDARD_COLUMNS[:len(df.columns)]
            df['GameType'] = game_type
            
        return df
    except Exception as e:
        print(f"Error fetching {game_type} sheet data: {e}")
        return create_empty_dataframe(game_type)

def create_empty_dataframe(game_type):
    if game_type == 'other':
        columns = OTHER_COLUMNS
    else:
        columns = STANDARD_COLUMNS + ['GameType']
    return pd.DataFrame(columns=columns)

def get_funny_comments(dfs):
    comments = []
    for game_type, df in dfs.items():
        if df is not None and 'Shenanigans' in df.columns:
            shenanigans = df['Shenanigans'].dropna().tolist()
            for comment in shenanigans:
                if isinstance(comment, str) and comment.strip():
                    game = game_type if game_type != 'other' else df.loc[df['Shenanigans'] == comment, 'GameType'].iloc[0]
                    comments.append(f"{game.upper()}: {comment}")
    return comments or ["No shenanigans recorded yet!"]

def create_placeholder_winners(num_places=10):
    return [
        {
            'name': f'Position {i+1}',
            'wins': 0,
            'game_breakdown': {}
        }
        for i in range(num_places)
    ]

def parse_game_data(dfs):
    rows = []
    winner_counts = Counter()
    game_specific_wins = defaultdict(Counter)
    
    empty_data = True
    for game_type, df in dfs.items():
        if df is None or df.empty:
            continue
            
        empty_data = False
        for _, row in df.iterrows():
            try:
                timestamp_str = row['Timestamp']
                if pd.isna(timestamp_str):
                    continue
                    
                Timestamp = datetime.strptime(timestamp_str, '%d/%m/%Y %H:%M:%S')
                winner = row['Winner']
                actual_game = row['GameType'] if game_type == 'other' else game_type
                
                if pd.notna(winner):
                    winner_counts[winner] += 1
                    game_specific_wins[actual_game][winner] += 1
                
                rows.append({
                    'Timestamp': Timestamp,
                    'game': actual_game,
                    'winner': winner,
                })
            except Exception as e:
                print(f"Error parsing row in {game_type}: {e}")
                continue
    
    if empty_data:
        return pd.DataFrame(columns=['Timestamp', 'game', 'winner']), create_placeholder_winners()
    
    sorted_winners = [
        {
            'name': name,
            'wins': count,
            'game_breakdown': {
                game: game_specific_wins[game][name]
                for game in set(game_specific_wins.keys())
                if game_specific_wins[game][name] > 0
            }
        }
        for name, count in sorted(winner_counts.items(), key=lambda x: (-x[1], x[0]))
    ]
    
    # Pad with placeholder entries if needed
    while len(sorted_winners) < 10:
        sorted_winners.append({
            'name': f'Position {len(sorted_winners) + 1}',
            'wins': 0,
            'game_breakdown': {}
        })
    
    return pd.DataFrame(rows), sorted_winners

@app.route('/get_data')
def get_data():
    cache_key = datetime.now().strftime('%Y%m%d%H%M')
    
    sheet_data = {
        game_type: fetch_sheet_data_cached(game_type, cache_key)
        for game_type in GAME_SHEETS.keys()
    }
    
    df, winner_counts = parse_game_data(sheet_data)
    funny_comments = get_funny_comments(sheet_data)
    
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    
    today_games = df[df['Timestamp'].dt.date == today].to_dict('records') if not df.empty else []
    yesterday_games = df[df['Timestamp'].dt.date == yesterday].to_dict('records') if not df.empty else []
    
    return jsonify({
        'today_games': today_games,
        'yesterday_games': yesterday_games,
        'today': today.strftime('%d/%m/%Y'),
        'yesterday': yesterday.strftime('%d/%m/%Y'),
        'winner_counts': winner_counts,
        'funny_comments': funny_comments
    })

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)