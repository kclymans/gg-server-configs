#!/usr/bin/env python3
import threading
import json
import yaml
import re
import time
import os
from apprise import Apprise
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess
import requests

UPDATE_INTERVAL=300 # seconds

def check_for_updates(app_id : str, state_file :str, restart_callback, webhook_url: str):
    """
    app_id:       Steam App ID (string or int)
    state_file:   Where we store last known change_number (e.g. '/tmp/app_state.json')
    restart_callback: Function to call when update is needed
    """

    # Load previous change_number (if exists)
    last_change_number = None
    if os.path.exists(state_file):
        try:
            with open(state_file, "r") as f:
                data = json.load(f)
                last_change_number = data.get("change_number")
        except:
            pass
    while True:
        try:
            response = requests.get(f"https://api.steamcmd.net/v1/info/{app_id}",timeout=10)
            response.raise_for_status()
            api_data = response.json()
            change_number = (
                api_data.get("data", {})
                .get(str(app_id), {})
                .get("_change_number")
            )
            if change_number is None:
                print("Warning: '_change_number' missing from API response")
            else:
                print(f"Current change_number = {change_number}")

                # Compare
                if last_change_number is not None and change_number != last_change_number:
                    print("Update detected! Triggering restart...")
                    print(f"Detected new change_number = {change_number} different from {last_change_number}")
                    send_webhook(webhook_url=webhook_url,player_name="SYSTEM",msg_kind="updating & restarting, kindly update your clients")
                    restart_callback(webhook_url)

                # Store this value for next loop
                last_change_number = change_number
                with open(state_file, "w") as f:
                    json.dump({"change_number": change_number}, f)

        except Exception as e:
            print(f"Error checking for updates: {e}")
        time.sleep(UPDATE_INTERVAL)
def restart_program(webhook: str):
    print("Restarting pod...")
    try:
        os.remove("/var/lib/containers/storage/volumes/systemd-enshrouded-base/_data/steamapps/appmanifest_2278520.acf")
        os.remove("/var/lib/containers/storage/volumes/systemd-enshrouded-base/_data/steamapps/appmanifest_228980.acf")
    except:
        print("Unable to remove file")
        pass
    try:
        subprocess.run(["systemctl","restart","enshrouded"])
        # FIXME
        #output = subprocess.run(["systemctl","status" "enshrouded"], capture_output=True)
        #status = output.stdout.decode().strip()
        #print(status)
    except:
        print("well thats not good")
        send_webhook(webhook_url=webhook,player_name="SYSTEM",msg_kind="Well there goes that SLA. Someone might want to ping an admin. Server might be in trouble")
        pass

class LogFileHandler(FileSystemEventHandler):
    def __init__(self, log_file, pattern, apprise_client):
        super().__init__()
        self.log_file = os.path.abspath(log_file)
        self.pattern = pattern
        self.apprise_client = apprise_client
        self._file_position = 0
        self._ensure_start_position()

    def _ensure_start_position(self):
        """Ensure starting position at end of file, or 0 if file is empty."""
        if os.path.exists(self.log_file):
            self._file_position = os.path.getsize(self.log_file)
        else:
            self._file_position = 0

    def _read_new_lines(self):
        """Read newly appended lines and process matches."""
        if not os.path.exists(self.log_file):
            return

        with open(self.log_file, "r") as f:
            f.seek(self._file_position)
            new_data = f.read()
            self._file_position = f.tell()

        #for line in new_data.splitlines():
        #    if self.pattern.search(line):
        #        message = f"**Log Alert:**\n```\n{line.strip()}\n```"
        #        self.apprise_client.notify(title="Log Watcher Alert", body=message)
        #        print(f"Matched pattern and sent notification: {line.strip()}")
        for line in new_data.splitlines():
            res = self.pattern.search(line)
            if res:
                #message = f"**Log Alert:**\n```\n{line.strip()}\n```"
                message = f"Player {res.group(1)} is online!"
                #self.apprise_client.notify(title="Log Watcher Alert", body=message)
                self.apprise_client.notify(body=message)
                print(f"Matched pattern and sent notification: {line.strip()}")

    def on_modified(self, event):
        """Triggered when log file is modified (new lines appended)."""
        if event.src_path == self.log_file:
            self._read_new_lines()

    def on_created(self, event):
        """Triggered when a new file is created (log rotated and recreated)."""
        if event.src_path == self.log_file:
            print(f"Log file {self.log_file} was recreated. Resetting position.")
            self._file_position = 0
            self._read_new_lines()

    def on_moved(self, event):
        """Triggered when the log file is rotated (moved to a new name)."""
        if event.src_path == self.log_file:
            print(f"Log file {self.log_file} was moved to {event.dest_path}. Waiting for recreation.")
            self._file_position = 0


def load_config(config_path="config.yaml"):
    """Load configuration from YAML file."""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def local_file(log_file:str,pattern:str, discord_url:str):
    if not os.path.exists(os.path.dirname(log_file)):
        raise FileNotFoundError(f"Directory does not exist: {os.path.dirname(log_file)}")

    apobj = Apprise()
    apobj.add(discord_url)

    print(f"Monitoring {log_file} for pattern: {pattern.pattern}")

    # Watch the directory instead of just the file
    directory_to_watch = os.path.dirname(log_file) or "."
    event_handler = LogFileHandler(log_file, pattern, apobj)

    observer = Observer()
    observer.schedule(event_handler, path=directory_to_watch, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()
def send_webhook(webhook_url: str, player_name: str, msg_kind: str):
    """Send a webhook with player info. Not sure how Bob pub/sub thing did this otherwise I would reuse it"""
    data = {"content":f"{player_name} is {msg_kind}"}
    try:
        response = requests.post(webhook_url, json=data, timeout=5)
        response.raise_for_status()
        print(f"[+] Webhook sent for {player_name}")
    except requests.RequestException as e:
        print(f"[!] Failed to send webhook: {e}")

def tail_journalctl(service:str, pattern:str, logout_pattern:str, discord_url:str):
    """And in the first circle of hell you must read logs from journalctl FOREVER!!!!"""
    cmd = ["journalctl","-u",service,"-f","-n","0"]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    print(f"Monitoring {service} for pattern: {pattern.pattern}")
    for line in iter(process.stdout.readline,""):
        line = line.strip()
        match = pattern.search(line)
        logout = logout_pattern.search(line)
        if match:
            player_name = match.group(1)
            print(f"[+] Detected login: {player_name}")
            send_webhook(discord_url, f"Player: {player_name}", "online!")
        if logout:
            player_name = logout.group(1)
            print(f"[+] Detected logout :{player_name}")
            send_webhook(discord_url, f"Player: {player_name}", "logged off!")


def main():
    config = load_config()

    pattern = re.compile(config["pattern"], re.IGNORECASE)
    logout_pattern = re.compile(config["logout_pattern"], re.IGNORECASE)
    discord_url = config["discord_webhook"]

    # Start background update check
    update_thread = threading.Thread(
        target=check_for_updates,
        args=(
            config["app_id"],
            config["appinfo_file_new"],
            restart_program,
            config["discord_webhook_url"]
        ),
        daemon=True
    )
    update_thread.start()


    if "log_file" in config:
        log_file = config["log_file"]
        local_file(log_file, pattern, discord_url)
    elif "journalctl" in config:
        service = config["journalctl"]
        tail_journalctl(service,pattern,logout_pattern,config["discord_webhook_url"])
    else:
        print("log_file or journalctl required")

if __name__ == "__main__":
    main()