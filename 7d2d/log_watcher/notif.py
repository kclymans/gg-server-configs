from apprise import Apprise
from config import discord_user_webhook, discord_system_webhook

def send_msg(msg):
    assert discord_user_webhook is not None
    apobj = Apprise()
    apobj.add(discord_user_webhook)
    apobj.notify(
        body=msg,
        # title="7 Days to Die",
    )
def send_sys_msg(msg):
    assert discord_system_webhook is not None
    apobj = Apprise()
    apobj.add(discord_system_webhook)
    apobj.notify(
        body=msg,
        # title="7 Days to Die",
    )