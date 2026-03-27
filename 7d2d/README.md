# Installation instructions

## SteamCMD (on RHEL)
Run as user "steam"

```bash
mkdir ~/Steam && cd ~/Steam
curl -sqL "https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz" | tar zxvf -
```

## Install 7D2D
Run as user "steam". The rebirth mod currently requires **7D2D V2.4**
```bash
cd ~/Steam
./steamcmd.sh
force_install_dir /7d2d
login anonymous
app_update 294420 -beta v2.4
```

## Rebirth
Installed version: **REBIRTH EXPERIMENTAL 2025.12.08 2115 - 7dtd v2.4 b7.zip**

Extract the zip file in /7d2d/Mods

## Rebirth - to be fixed?

```log
2026-03-26T00:07:48 236.332 WRN [TheDescent] no cavemap found for world 'West Gepokoje Valley'
[Rebirth] Failed to find HivePrefabs.xml
[Rebirth] Failed to find TraderPrefabs.xml
```

Fixed by last two by:

```bash
cd /7d2d_run2/Mods/zzz_REBIRTH__Utils/
sudo -u steam cp hivePrefabs.xml HivePrefabs.xml
sudo -u steam cp traderPrefabs.xml TraderPrefabs.xml
```

# Custom services

- 7d2d_notif.service: discord notifs for when ppl log in or die
- TimeReset: if only X players online, after 21:00 reset time to 06:00

# Other components

## Alloy / Loki / Grafana

- Alloy collects the logs
- Loki stores the logs
- Grafana for visualization
