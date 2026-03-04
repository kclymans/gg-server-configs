from apprise import Apprise
from config import discord_user_webhook, discord_system_webhook

def send_msg(msg):
    apobj = Apprise()
    apobj.add(discord_user_webhook)
    apobj.notify(
        body=msg,
        # title="7 Days to Die",
    )
def send_sys_msg(msg):
    apobj = Apprise()
    apobj.add(discord_system_webhook)
    apobj.notify(
        body=msg,
        # title="7 Days to Die",
    )