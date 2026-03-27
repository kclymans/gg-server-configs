import os
from dotenv import load_dotenv
load_dotenv()

discord_user_webhook = os.getenv("DISCORD_USER_WEBHOOK")
discord_system_webhook = os.getenv("DISCORD_SYSTEM_WEBHOOK")

#LOG_DIR = "/7d2d/7DaysToDieServer_Data"
LOG_DIR = "/7d2d_run2/7DaysToDieServer_Data"
LOG_MATCH = "output_log__20*_Rebirth_run_2.txt"

DEATH_MESSAGES=[
    "Player {player} died!",
    "Player {player} hit the dust",
    "Player {player} is now wormfood",
    "Player {player} is now a floor inspector.",
    "Player {player} took a permanent nap.",
    "Player {player} ran out of hit points and excuses.",
    "Player {player} is testing the respawn mechanic.",
    "Player {player} found out.",
    "Player {player} might have a skill issue.",
    "Player {player} rolled a natural 1 on survival.",
    "Player {player} is now part of the scenery.",
    "Player {player} became loot.",
    "Player {player} took a calculated risk, but appears to suck at math.",
    "Player {player} tried to tank with their face.",
    "Player {player} has been removed from the gene pool.",
    "Player {player} mistook confidence for skill.",
    "Player {player} has achieved peak oof.",
    "Player {player} forgot to tap out.",
    "Player {player} counted on his team to be a team.",
    "Player {player} shouldn't have insulted the medic.",
    "Player {player} shouldn't have trusted the medic.",
]
