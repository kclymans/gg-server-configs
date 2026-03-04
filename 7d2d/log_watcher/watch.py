import signal
import os
import glob
import random
import re
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from notif import send_msg, send_sys_msg
from config import LOG_DIR, LOG_PREFIX, DEATH_MESSAGES

class LogEventHandler(FileSystemEventHandler):
    def __init__(self):
        self.current_file = None
        self.file_handle = None
        self.seek_end = True
        self.update_current_file(init=True)

    def update_current_file(self, init=False):
        """Finds the latest log file and opens it."""
        search_path = os.path.join(LOG_DIR, f"{LOG_PREFIX}*")
        files = glob.glob(search_path)

        if not files:
            return

        # Find the most recently modified file
        latest_file = max(files, key=os.path.getmtime)

        if latest_file != self.current_file:
            if not init==True:
                send_sys_msg(f"New log file detected, server restarted? {latest_file}")
            else:
                send_sys_msg(f"Log watcher process stated. Using {latest_file}")
            # print(f"Switching to new log file: {latest_file}")
            if self.file_handle:
                self.file_handle.close()

            self.current_file = latest_file
            try:
                self.file_handle = open(self.current_file, 'r', encoding='utf-8', errors='ignore')
                if self.seek_end:
                    self.file_handle.seek(0, os.SEEK_END)
                    # Only seek to end on the very first load
                    self.seek_end = False
            except OSError as e:
                print(f"Failed to open file {self.current_file}: {e}")

    def on_created(self, event):
        """Called when a file or directory is created."""
        if not event.is_directory and os.path.basename(event.src_path).startswith(LOG_PREFIX):
            self.update_current_file(init=False)

    def on_modified(self, event):
        """Called when a file or directory is modified."""
        if not event.is_directory and event.src_path == self.current_file:
            self.process_lines()

    def process_lines(self):
        """Reads new lines from the current file."""
        if not self.file_handle:
            return
       while True:
            where = self.file_handle.tell()
            line = self.file_handle.readline()
            if not line:
                break

            # If line is incomplete (no newline), wait for more data
            if not line.endswith('\n'):
                self.file_handle.seek(where)
                break

            self.parse_line(line.strip())

    def randomDied(self, player_name):
        message_template = random.choice(DEATH_MESSAGES)
        return message_template.replace("{player}", player_name)

    def parse_line(self, line):
        """Parses a single line for events."""
        # Login detection
        if "PlayerSpawnedInWorld (reason: JoinMultiplayer" in line \
        or "PlayerSpawnedInWorld (reason: EnterMultiplayer" in line:
            match = re.search(r"PlayerName='(.*?)'", line)
            if match:
                name = match.group(1)
                send_msg(f"Player {name} logged in")

        # Logout detection
        if "disconnected after" in line:
            match = re.search(r"Player (.*?) disconnected after", line)
            if match:
                name = match.group(1)
                send_msg(f"Player {name} logged out")

        # You died
        if 'GMSG: Player' in line \
        and 'died' in line:
            match = re.search(r"Player '(.*?)' died", line)
            if match:
                name = match.group(1)
                send_msg(self.randomDied(name))

        # Server ready
        if '[EOS] Server registered, session:' in line:
            send_sys_msg("Server registered, it should be ready now")

if __name__ == "__main__":
    event_handler = LogEventHandler()
    observer = Observer()
    observer.schedule(event_handler, path=LOG_DIR, recursive=False)
    observer.start()
    print(f"Monitoring {LOG_DIR} for {LOG_PREFIX}...")

    def teardown(signum, frame):
        observer.stop()

    signal.signal(signal.SIGTERM, teardown)
    signal.signal(signal.SIGINT, teardown)

    observer.join()