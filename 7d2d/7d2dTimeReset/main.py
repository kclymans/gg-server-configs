#!/usr/bin/env python3

import asyncio
import telnetlib3 # type: ignore
import logging
import re
import sys
import os
from dotenv import load_dotenv # type: ignore
load_dotenv()

logger = logging.getLogger("7D2D-TimeReset")
logger.setLevel(logging.INFO)
FORMAT = '%(asctime)s %(levelname)s %(message)s'
formatter = logging.Formatter(FORMAT)
# 2026-03-14T21:52:08
formatter_loki = logging.Formatter(FORMAT,"%Y-%m-%dT%H:%M:%S")

# stdout handler (systemd/journald)
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setFormatter(formatter)

# file handler
file_handler = logging.FileHandler('/7d2d/7DaysToDieServer_Data/output_log__TimeReset.txt')
file_handler.setFormatter(formatter_loki)

logger.addHandler(stdout_handler)
logger.addHandler(file_handler)


HOST = "127.0.0.1"
PORT = 8081
PASSWORD = os.getenv("TNP")
# [1-MAX_PLAYERS] will reset time
MAX_PLAYERS = 3
# Zero leading military time
RESET_TRIGGER_HOUR=21
RESET_HOUR=6
RESET_MINUTE=0

async def send_command(writer, reader, command):
    writer.write(command + "\n")
    await writer.drain()
    await asyncio.sleep(1)
    return await reader.read(4096)

def count_players(output):
    # Total of 1 in the game
    # Total of 0 in the game
    logger.debug(f"count_players output: {output}")
    match = re.search(r"Total of (\d+) in the game", output, re.MULTILINE)
    if match:
        return int(match.group(1))
    return 0

def get_datetime(output):
    logger.debug(f"get_datetime output: {output}")
    # Day 13, 06:18
    match = re.search(r"Day (\d+), (\d+):(\d+)", output)
    if match:
        return int(match.group(1)),int(match.group(2)),int(match.group(3))
    return None, None, None

def check_settime(output):
    # Set time to 294000
    logger.debug(f"check_settime output: {output}")
    match = re.search(r"Set time to (\d+)", output)
    if match:
        return int(match.group(1))
    return None

def check_say(output):
    # INF Chat (from '-non-player-', entity id '-1', to 'Global'): hello everyone
    logger.debug(f"check_say output: {output}")
    match = re.search(r"Chat .from.*\): (.*)", output)
    if match:
        return int(match.group(1))
    return None

async def main():
    ## Connecting
    logger.debug(f"Attempting telnet connection to {HOST}:{PORT}...")
    try:
        reader, writer = await telnetlib3.open_connection(HOST, PORT)
    except Exception as e:
        # server unavailable → just exit (systemd will try again later)
        logger.critical(f"Connection failed: {e}")
        sys.exit(0)
    logger.debug("Connection successful")

    ## Logging in
    try:
        await reader.readuntil(b"Please enter password:")
        assert PASSWORD is not None
        auth_output = await send_command(writer, reader, PASSWORD)
        logger.debug(f"auth_output: {auth_output}")
        if "Password incorrect" in auth_output:
            logger.critical("Telnet authentication failed")
            writer.close()
            await writer.wait_closed()
            sys.exit(1)
    except Exception as e:
        logger.critical(f"Password failed: {e}")
        writer.close()
        sys.exit(1)

    ## Getting players
    players = None
    logger.debug("Getting number of online players")
    try:
        list_output = await send_command(writer, reader, "listplayers")
        players = count_players(list_output)
        logger.info(f"There are {players} players online")
    except Exception as e:
        logger.critical(f"Getting players failed: {e}")
        writer.close()
    logger.debug(f"players has type {type(players)}")
    assert isinstance(players, int), f"players should be an int, got {type(players)}"

    ## Getting time
    day = None
    hour = None
    min = None
    try:
        logger.debug("Getting day and time")
        time_output = await send_command(writer, reader, "gettime")
        day,hour,min = get_datetime(time_output)
        logger.info(f"Detected day {day}, hour {hour}, minute {min}")
    except Exception as e:
        logger.critical(f"Getting time failed: {e}")
        writer.close()
        sys.exit(1)
    logger.debug(f"day has type {type(day)}")
    logger.debug(f"hour has type {type(hour)}")
    logger.debug(f"min has type {type(min)}")
    assert isinstance(day, int), f"day should be an int, got {type(day)}"
    assert isinstance(hour, int), f"hour should be an int, got {type(hour)}"
    assert isinstance(min, int), f"min should be an int, got {type(min)}"
    
    ## Main Logic
    if players == 0:
        logger.debug("No players online, quitting...")
        sys.exit(0)
    elif players > MAX_PLAYERS:
        logger.debug(f"More then {MAX_PLAYERS} players online, quitting...")
        sys.exit(0)
    
    if hour == RESET_TRIGGER_HOUR:
        logger.info(f"{players} players online, resetting day {day} time {hour}:{min} to day {day} time {RESET_HOUR}:{RESET_MINUTE}")
        assert day > 0, f"day should be greater than 0, got {day}"
        ## Reset Time
        try:
            settime_output = await send_command(writer, reader, f"settime {day} {RESET_HOUR} {RESET_MINUTE}")
            res_settime = check_settime(settime_output)
            if res_settime:
                logger.info(f"Set time to {res_settime}")
            else:
                logger.warning(f"Failed to set time: {settime_output}")
            writer.close()
            await writer.wait_closed()
        except Exception as e:
            logger.critical(f"settime failed: {e}")
            writer.close()
            await writer.wait_closed()
        ## Send message
        try:
            say_output = await send_command(writer, reader, f"say \"Resetting time to 06:00\"")
            res_say = check_settime(say_output)
            if res_say:
                logger.info(f"Sent message: {res_say}")
            else:
                logger.warning(f"Failed to send message: {say_output}")
        except Exception as e:
            logger.critical(f"say failed: {e}")
    else:
        logger.debug(f"Not {RESET_TRIGGER_HOUR} hour, quitting...")

if __name__ == "__main__":
    asyncio.run(main())
