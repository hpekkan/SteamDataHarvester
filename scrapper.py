import requests
import pandas as pd
import os
import json
import re
from concurrent.futures import ThreadPoolExecutor


def fetch_user_profile(api_key, steam_id):
    """Fetches user profile information with error handling."""
    url = f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={api_key}&steamids={steam_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code
    except requests.exceptions.RequestException as e:
        print(f"Error fetching user profile: {e}")
        return None

    try:
        profile_data = response.json()
        if 'players' in profile_data.get('response', {}):
            return profile_data['response']['players'][0] if profile_data['response']['players'] else None
    except ValueError:
        print("Invalid JSON response")
    return None

def fetch_games(api_key, steam_id, game_names):
    """Fetches games for a given Steam ID and replaces AppIDs with game names, with error handling."""
    url = f"https://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={api_key}&steamid={steam_id}&format=json"
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching games: {e}")
        return None

    try:
        games_data = response.json()
        if 'games' in games_data.get('response', {}):
            for game in games_data['response']['games']:
                game['name'] = game_names.get(str(game['appid']), "Unknown Game")
            return games_data['response']['games']
    except ValueError:
        print("Invalid JSON response")
    return None

def fetch_friends(api_key, steam_id):
    """Fetches friends list for a given Steam ID with error handling."""
    url = f"https://api.steampowered.com/ISteamUser/GetFriendList/v0001/?key={api_key}&steamid={steam_id}&relationship=friend"
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching friends list: {e}")
        return None

    try:
        return response.json() if 'friendslist' in response.json() else None
    except ValueError:
        print("Invalid JSON response")
        return None

def sanitize_filename(filename):
    """Sanitizes the filename by removing or replacing invalid characters."""
    invalid_chars = r'<>:"/\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '')
    return filename

def save_games_to_csv(games, steam_id, username, folder):
    """Saves games to a CSV file in a specified folder."""
    sanitized_username = sanitize_filename(username)
    df = pd.DataFrame(games)
    file_path = os.path.join(folder, f'{sanitized_username}_{steam_id}_games.csv')
    df.to_csv(file_path, index=False)

def process_user(api_key, steam_id, game_names, folder_name, processed_users_file):
    """Process a single user - fetch games, save to CSV, and get friends."""
    if not is_user_processed(processed_users_file, steam_id):
        profile = fetch_user_profile(api_key, steam_id)
        if profile:
            username = profile.get('personaname', 'Unknown')
            print(f"Processing {username} ({steam_id})")
            update_processed_users(processed_users_file, steam_id)
            games = fetch_games(api_key, steam_id, game_names)
            if games:
                save_games_to_csv(games, steam_id, username, folder_name)
            return fetch_friends(api_key, steam_id)
    return None


def load_game_names(filename):
    """Loads the game names from a local file."""
    try:
        with open(filename, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        print("Game names file not found.")
        return {}

def update_processed_users(filename, steam_id):
    """Updates the file of processed users with a new Steam ID."""
    with open(filename, "a") as file:
        file.write(steam_id + "\n")

def is_user_processed(filename, steam_id):
    """Checks if a user has already been processed."""
    try:
        with open(filename, "r") as file:
            processed_ids = file.read().splitlines()
            return steam_id in processed_ids
    except FileNotFoundError:
        return False

folder_name = 'user_data'
os.makedirs(folder_name, exist_ok=True)
processed_users_file = os.path.join(folder_name, 'processed_users.txt')

game_names = load_game_names('steam_games_list.json')

api_key = 'YOUR_API_KEY'
initial_steam_id = 'INITIAL_STEAM_ID'
folder_name = 'user_data'
os.makedirs(folder_name, exist_ok=True)
processed_users_file = os.path.join(folder_name, 'processed_users.txt')
game_names = load_game_names('steam_games_list.json')

# Use ThreadPoolExecutor to handle threading
with ThreadPoolExecutor(max_workers=10) as executor:
    future_to_steamid = {executor.submit(process_user, api_key, initial_steam_id, game_names, folder_name, processed_users_file): initial_steam_id}
    processed_users = set()

    while future_to_steamid:
        # Check for completed futures
        done = {future for future in future_to_steamid if future.done()}
        for future in done:
            steam_id = future_to_steamid[future]
            friends_data = future.result()
            processed_users.add(steam_id)
            del future_to_steamid[future]

            # Add new tasks for the friends
            if friends_data and 'friendslist' in friends_data:
                for friend in friends_data['friendslist']['friends']:
                    friend_id = friend['steamid']
                    if friend_id not in processed_users and not is_user_processed(processed_users_file, friend_id):
                        future_to_steamid[executor.submit(process_user, api_key, friend_id, game_names, folder_name, processed_users_file)] = friend_id