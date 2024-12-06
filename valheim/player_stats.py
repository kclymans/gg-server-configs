import os
from collections import defaultdict
import re
import requests
import json
from dotenv import load_dotenv


def load_secrets(secrets_file='.secrets'):
    load_dotenv(secrets_file)
    return os.getenv('DISCORD_WEBHOOK')

def send_to_discord(webhook_url, player_stats):
    message = "Player ZDOID Stats:\n"
    for player, count in player_stats.items():
        message += f"{player}: {count} entries\n"

    payload = {
        "content": message
    }

    response = requests.post(webhook_url, json=payload)
    return response.status_code == 204

def count_zdoid_entries_by_player(log_file_path):
    """
    Group players found and count entries
    """

    pattern = r'^\d\d\/\d\d\/\d\d\d\d \d\d:\d\d:\d\d: Got character ZDOID from (.*?) : 0:0$'
    player_counts = defaultdict(int)

    with open(log_file_path, 'r') as file:
        for line in file:
            match = re.search(pattern, line)
            if match:
                player = match.group(1)
                player_counts[player] += 1

    return dict(player_counts)
def patrick():
    """
    Is this main

    No this is Patrick!
    """
    webhook_url = load_secrets("/home/valheim/.secrets")
    file_path = '/home/valheim/valheim-plus-server/data/character_logins.txt'
    player_stats = count_zdoid_entries_by_player(file_path)
    for player, count in player_stats.items():
        print(f"{player}: {count} entries")
    send_to_discord(webhook_url, player_stats)

if __name__ == "__main__":
    patrick()