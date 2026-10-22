# 03 - Features and interfaces

## 1. Features

| # | Feature | Where |
|---|---|---|
| F1 | Single Quick Access toggle "Kanto Gear on the bottom screen" | `dist/index.js:56-68` |
| F2 | Live status (polls every 2 s) | `dist/index.js:37-41` |
| F3 | Helper mod install and reinstall button | `dist/index.js:83-92`, `main.py:299-304` |
| F4 | Process scan: finds the game and any companion windows and whether a companion is on the bottom gamescope | `main.py:94-113` |
| F5 | Ratatoskr park and restore with a grace period of about 4 s | `main.py:215-248` |
| F6 | Bottom-screen launch of companion windows through `armada-run-bottom` | `mod/thor_bottom_companion/main.lua:31-62` |
| F7 | Fallback to the engine's own spawn on any failure | `mod/thor_bottom_companion/main.lua:61-62` |
| F8 | Deploy script with on-device pre-flight | `scripts/deploy.sh:19-24` |

## 2. Decky UI

Frontend calls and their backend methods:

| UI call | Backend method | Caller line |
|---|---|---|
| `getStatus()` | `get_status` | `dist/index.js:17`, `:30` |
| `setEnabled(value)` | `set_enabled` (arg: bool) | `dist/index.js:18`, `:63` |
| `installMod()` | `install_mod` | `dist/index.js:19`, `:88` |

UI rows (all rendered inside one section titled "Second Screen", `dist/index.js:93-94`):

| Row | Shown value |
|---|---|
| Toggle | label "Kanto Gear on the bottom screen", description = `status.description`, checked = `status.enabled` (`dist/index.js:57-65`) |
| Helper mod | "Not installed" / "Installed and enabled in Gen1Recomp" / "Installed - enable 'Thor Bottom Companion' in the Gen1Recomp mod manager" (`dist/index.js:69-73`) |
| Second-screen window | "Open on the bottom screen" / "Game running, no second-screen window" / "Game not running" (`dist/index.js:77-79`) |
| Install button | Shown when not installed, or installed but not enabled in game (`dist/index.js:83-92`) |

Toast texts: "On: the next second-screen window opens on the bottom screen" and "Off: bottom screen left alone" for the toggle (`dist/index.js:64`), and "Helper mod copied into Gen1Recomp" for install (`dist/index.js:88`).

The icon is an inline SVG of a phone-style rectangle with a line and dot (`dist/index.js:98-117`).

## 3. Backend methods (Decky `Plugin` class, `main.py:200-304`)

| Method | Async | Input | Output | Side effects |
|---|---|---|---|---|
| `_main` | yes | none | none | starts `_watch` (`main.py:209-210`) |
| `_unload` | yes | none | none | calls `_restore` in a thread (`main.py:212-213`) |
| `get_status` | yes | none | status dict (below) | none beyond scan and file reads (`main.py:282-283`) |
| `set_enabled` | yes | `enabled: bool` | status dict with `install` key when turning on | turning on: copies mod, writes flag. Turning off: removes flag, restores Ratatoskr (`main.py:285-297`) |
| `install_mod` | yes | none | status dict with `install` key | copies mod (`main.py:299-304`) |

Decky methods are called by name from the UI (`dist/index.js:17-19`). The Decky loader's exact dispatch rules are **unverified**; the repo only shows the names.

### Status dict (returned by `get_status`, `set_enabled`, `install_mod`)
Built in `_status` (`main.py:271-280`):

| Key | Type | Meaning |
|---|---|---|
| `enabled` | bool | flag file exists |
| `mod_installed` | bool | `<game_dir>/mods/thor_bottom_companion/main.lua` is a file |
| `mod_enabled_in_game` | bool | `options.lua` has `thor_bottom_companion = true` |
| `game_dir` | string | resolved Gen1Recomp folder |
| `game_running` | bool | a game process was found by `scan_processes` |
| `on_bottom` | bool | a companion on the bottom gamescope was found in the last scan |
| `touch_parked` | bool | this backend stopped Ratatoskr and has not restored it yet |
| `description` | string | one of the messages below |
| `install` | object | only from `set_enabled` (on) and `install_mod`: `{"changed": [paths], "errors": [strings]}` (`main.py:132-152`) |

### Status description strings
Chosen in order, first match wins (`main.py:257-270`):

1. "Gen1Recomp was not found (looked for the Steam shortcut's AppImage)"
2. "Helper mod is not installed yet"
3. "Enable 'Thor Bottom Companion' in the Gen1Recomp mod manager, then set Kanto Gear to Separate Screens"
4. "Off: the second-screen window opens on the top screen"
5. "Kanto Gear is on the bottom screen"
6. "On, but no second-screen window is open (set Kanto Gear's Display Mode to Separate Screens)"
7. "On: Kanto Gear will open on the bottom screen when the game starts"

## 4. Inputs and outputs

| Kind | Path or source | Read or written | Notes |
|---|---|---|---|
| Flag file | `$HOME/.config/kanto-gear-bottom/enabled` (`main.py:29`) | read by `FLAG.exists()`, written by `set_flag` (`main.py:163-173`) | Empty file. Presence is the switch. Also read by the shell script in the mod (`main.lua:32`). |
| Steam shortcuts | `$HOME/.local/share/Steam/userdata/*/config/shortcuts.vdf` (`main.py:32`) | read | Used to find the Gen1Recomp AppImage (`main.py:65-76`) |
| Game mods folder | `<game_dir>/mods/thor_bottom_companion/` (`main.py:139-152`) | written | Files copied from `mod/thor_bottom_companion/` |
| Game options | `<game_dir>/options.lua` (`main.py:255`) | read-only text match | Repo does not write it |
| Game process table | `/proc/<pid>/cmdline`, `/proc/<pid>/environ` (`main.py:79-91`) | read | Backend runs as root (`plugin.json:4`) |
| Ratatoskr service | user unit `touch-master.service`, via `systemctl` (`main.py:37`, `main.py:178-190`) | start, stop, is-active | |
| Stock bottom fallback | user unit `armada-bottom-screen.service` (`main.py:38`, `main.py:246`) | start only if Ratatoskr start fails | |
| Bottom env file | `${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/armada-bottom-env` (`main.lua:33`) | read-only test (`-r`) | Written by Armada (**unverified**). Only its existence and readability are checked. |
| Bottom launcher | `/usr/bin/armada-run-bottom` (`main.lua:34-35`) | executed, detached, output to `/dev/null` | |

## 5. Protocols and commands from the code

### 5a. Companion launch contract (Lua mod to shell)
- Trigger: `HostShell.spawnSelfDetached(args)` where `args[1]` starts with `--display-companion=` (`main.lua:43-44`). Non-table args, and Windows (`HostShell.isWindows()`), go to the original function (`main.lua:45`).
- The mod builds: `sh -c <SCRIPT> sh <quoted args...>` (`main.lua:47-48`). Each value is shell-quoted by `HostShell.quote` (`main.lua:48`).
- The script prints one word on stdout (`main.lua:36`, `:38`):
  - `bottom`: the launcher was started. The mod logs "second-screen window started on the bottom screen" and returns `true` (`main.lua:57-60`).
  - `top`: any of the four gates failed. The mod calls the original spawn (`main.lua:62`).
- Gates in the script (`main.lua:34`): `$APPIMAGE` is non-empty, the flag file exists, the env file is readable, and `/usr/bin/armada-run-bottom` is executable.
- Launch line (`main.lua:35`): `setsid /usr/bin/armada-run-bottom -- "$APPIMAGE" "$@" >/dev/null 2>&1 &`, inside a subshell.
- Errors inside `popen` make the mod log a warning and call the original (`main.lua:50-56`, `:61-62`).

### 5b. Companion detection (backend)
| Signal | Source | Use |
|---|---|---|
| argv contains `--display-companion=` | `/proc/<pid>/cmdline` (`main.py:108`) | marks a companion |
| env `WAYLAND_DISPLAY == "gamescope-secondary"` | `/proc/<pid>/environ` (`main.py:109`) | marks the companion as on the bottom |
| env `APPIMAGE` matches `gen1recomp.*\.AppImage$` (case-insensitive) | `main.py:111` | marks the game process |

### 5c. Systemctl forms (`main.py:181`)
Each call tries these two forms in order and returns on the first zero exit status:
1. `systemctl --machine=armada@.host --user <action> <unit>`
2. `systemctl --user <action> <unit>`

Environment: `XDG_RUNTIME_DIR=/run/user/1000`, `DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus` (`main.py:42-45`). Timeout 6 s (`main.py:183`).

### 5d. Shortcut file format
`parse_shortcuts` does not parse binary VDF. It scans bytes for `\x01AppName\x00`, `\x01Exe\x00`, `\x01StartDir\x00` with a regex and starts a new row on each `AppName` (`main.py:50-62`). Consequence: rows are only as correct as that pattern (see [06](06-limitations-glossary.md)).

### 5e. Flag file
Empty file at `$HOME/.config/kanto-gear-bottom/enabled`, created with `Path.touch()` and chowned to the user (`main.py:163-168`).

## 6. Configuration surface
See [04](04-configuration-requirements.md). Environment variables `KGB_HOME`, `KGB_UID`, `KGB_PROC` override the home, uid, and proc root (`main.py:24-26`).
