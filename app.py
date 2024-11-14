from flask import Flask, render_template, jsonify
from datetime import datetime, timedelta
import pandas as pd
import requests
import io
from functools import lru_cache

app = Flask(__name__)

@lru_cache(maxsize=1)
def fetch_google_sheet_data_cached(cache_key):
    """Fetch data from Google Sheets with caching"""
    sheet_url = "https://docs.google.com/spreadsheets/d/1FS9Dej3jq0BuCQGPjzCIJH1_WI9ddHgS6n_00NjsEJw/edit?gid=217936795"
    file_id = sheet_url.split('/')[5]
    export_url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=csv"
    
    try:
        response = requests.get(export_url)
        response.raise_for_status()
        data = pd.read_csv(io.StringIO(response.text))
        return data
    except Exception as e:
        print(f"Error fetching sheet data: {e}")
        return None

def parse_game_data(df):
    """Parse the game data DataFrame into a structured format"""
    rows = []
    
    for _, row in df.iterrows():
        try:
            timestamp = datetime.strptime(row['Timestamp'], '%d/%m/%Y %H:%M:%S')
            game_type = row['What game did you play?']
            winner = row['Who won the game?']
            if game_type == 'Durak':
                loser = row['If you played Durak, who lost?']
                winner = f"All except {loser}"
            else:
                players = [col for col in df.columns if col.startswith('Other player')]
                for player_col in players:
                    if pd.notna(row[player_col]):
                        #winner = row[player_col]
                        break
            
            rows.append({
                'timestamp': timestamp,
                'game': game_type,
                'winner': winner
            })
        except Exception as e:
            print(f"Error parsing row: {e}")
            continue
            
    return pd.DataFrame(rows)

@app.route('/get_winners')
def get_winners():
    # Create cache key based on current minute
    cache_key = datetime.now().strftime('%Y%m%d%H%M')
    
    # Fetch and parse data
    raw_data = fetch_google_sheet_data_cached(cache_key)
    if raw_data is None:
        return jsonify({'error': 'Failed to fetch data'}), 500
    
    df = parse_game_data(raw_data)
    
    # Get today's date and yesterday's date
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    
    # Filter data for today and yesterday
    today_games = df[df['timestamp'].dt.date == today].to_dict('records')
    yesterday_games = df[df['timestamp'].dt.date == yesterday].to_dict('records')
    
    return jsonify({
        'today_games': today_games,
        'yesterday_games': yesterday_games,
        'today': today.strftime('%d/%m/%Y'),
        'yesterday': yesterday.strftime('%d/%m/%Y')
    })

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)