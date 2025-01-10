import os

from datetime import datetime, timedelta
import re
from collections import defaultdict
import requests
from dotenv import load_dotenv

def analyze_user_trends(log_file_path, date_format="%m/%d/%Y %H:%M:%S"):
    """
    Analyzes a log file to identify users with increasing activity in the last 7 days.

    Args:
    log_file_path (str): Path to the log file
    date_format (str): Format of the datetime in the log file

    Returns:
    dict: Dictionary containing trend analysis for each user
    """
    # Store user activity counts
    user_activity = defaultdict(lambda: {"last_7_days": 0, "previous": 0})

    # Get the date of the most recent log entry
    most_recent_date = None
    with open(log_file_path, 'r') as file:
        for line in file:
            try:
                # Parse date from format: "12/05/2024 20:30:09: Got character..."
                date_str = line.split(": ")[0]
                current_date = datetime.strptime(date_str, date_format)
                if most_recent_date is None or current_date > most_recent_date:
                    most_recent_date = current_date
            except (ValueError, IndexError):
                continue

    if most_recent_date is None:
        return {}

    # Calculate the cutoff date for the last 7 days
    seven_days_ago = most_recent_date - timedelta(days=7)
    pattern = r'^\d\d\/\d\d\/\d\d\d\d \d\d:\d\d:\d\d: Got character ZDOID from (.*?) : 0:0$'
    with open(log_file_path, 'r') as file:
        for line in file:
            match = re.search(pattern, line)
            if match:
                try:
                    # Parse the line
                    # Split by ": " to handle the timestamp
                    parts = line.split(": ")
                    if len(parts) < 2:
                        continue

                    date_str = parts[0]
                    content = ": ".join(parts[1:])  # Rejoin the rest in case there are more colons

                    username = content.split("from ")[1].split(":")[0].strip()

                    # Convert date string to datetime
                    log_date = datetime.strptime(date_str, date_format)

                    # Count activity
                    if log_date >= seven_days_ago:
                        user_activity[username]["last_7_days"] += 1
                    else:
                        user_activity[username]["previous"] += 1

                except (ValueError, IndexError):
                    continue

    # Calculate trends
    trend_analysis = {}
    for username, counts in user_activity.items():
        # Calculate daily averages
        days_in_previous = (seven_days_ago - (most_recent_date - timedelta(days=30))).days
        if days_in_previous <= 0:
            days_in_previous = 1

        daily_avg_previous = counts["previous"] / days_in_previous
        daily_avg_recent = counts["last_7_days"] / 7

        # Calculate trend percentage
        trend_percentage = ((daily_avg_recent - daily_avg_previous) / daily_avg_previous * 100
                            if daily_avg_previous > 0 else float('inf'))

        trend_analysis[username] = {
            "last_7_days_total": counts["last_7_days"],
            "previous_total": counts["previous"],
            "daily_avg_last_7_days": daily_avg_recent,
            "daily_avg_previous": daily_avg_previous,
            "trend_percentage": trend_percentage
        }

    return trend_analysis

def print_trending_users(trend_analysis, min_trend_percentage=10):
    """
    Prints users with significant increasing activity.

    Args:
    trend_analysis (dict): Output from analyze_user_trends
    min_trend_percentage (float): Minimum percentage increase to be considered trending

    Returns:
    str: Message to ship off to discord
    """
    message = "\n\nTrending Users Analysis:\n"
    message += "-" * 80

    trending_users = {
        username: data for username, data in trend_analysis.items()
        if data["trend_percentage"] >= min_trend_percentage
        and data["last_7_days_total"] > 0
    }

    if not trending_users:
        message += "No users showing significant trending activity."
        return message

    # Sort by trend percentage
    for username, data in sorted(
        trending_users.items(),
        key=lambda x: x[1]["trend_percentage"],
        reverse=True
    ):
        message += f"\nUser: {username}\n"
        message += f"Last 7 days activity: {data['last_7_days_total']} events\n"
        message += f"Previous daily average: {data['daily_avg_previous']:.2f} events\n"
        message += f"Recent daily average: {data['daily_avg_last_7_days']:.2f} events\n"
        message += f"Trend: {data['trend_percentage']:.1f}% increase\n"

    return message

def load_secrets(secrets_file='.secrets'):
    load_dotenv(secrets_file)
    return os.getenv('DISCORD_WEBHOOK')

def send_to_discord(webhook_url, message):
    """
    Ship off to discord
    """

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

    message = "Player ZDOID Stats:\n"
    for player, count in dict(player_counts).items():
        message += f"{player}: {count} entries\n"

    return message

def patrick():
    """
    Is this main

    No this is Patrick!
    """
    webhook_url = load_secrets("/home/valheim/.secrets")
    file_path = '/home/valheim/valheim-plus-server/data/character_logins.txt'
    player_stats = count_zdoid_entries_by_player(file_path)
    print(player_stats)
    analysis = analyze_user_trends(file_path)
    trending_stats = print_trending_users(analysis, min_trend_percentage=10)
    print(trending_stats)
    send_to_discord(webhook_url, player_stats)
    send_to_discord(webhook_url, trending_stats)

if __name__ == "__main__":
    patrick()
