import requests
import json

def fetch_steam_games_list():
    """Fetches the list of all games from the Steam API."""
    url = "http://api.steampowered.com/ISteamApps/GetAppList/v0002/"
    response = requests.get(url)
    if response.status_code == 200:
        apps = response.json()['applist']['apps']
        return {app['appid']: app['name'] for app in apps}
    else:
        return None

def save_games_list_to_file(games_list, filename):
    """Saves the games list to a file."""
    with open(filename, 'w') as file:
        json.dump(games_list, file)

steam_games_list = fetch_steam_games_list()
if steam_games_list:
    save_games_list_to_file(steam_games_list, 'steam_games_list.json')
    print("Steam games list saved successfully.")
else:
    print("Failed to fetch Steam games list.")
