# 04 - Error handling and device constraints

## 1. Error handling by location

| Where | What can fail | What the code does | Source |
|---|---|---|---|
| `_chown` | `os.chown` missing (Windows), or permission denied | Swallows `AttributeError`, `PermissionError`, `OSError`. Files stay owned by root. | `main.py:155-160` |
| `install_mod` | Source missing, mods folder missing, any `OSError` during copy | Returns `errors` list; the copy loop stops at the first `OSError` | `main.py:132-152` |
| `files_differ` | Either file unreadable | Returns True, so the copy is attempted | `main.py:125-129` |
| `set_flag(False)` | Flag already absent | `FileNotFoundError` ignored | `main.py:170-173` |
| `run_systemctl` | Missing binary, timeout, any exception | Next command form is tried; last failure returned as `(1, message)` | `main.py:183-190` |
| `unit_active` | Non-zero rc or stdout not `active` | Returns False | `main.py:193-195` |
| `_restore` | Start of `touch-master.service` fails | Starts `armada-bottom-screen.service` instead; the rc of that call is ignored | `main.py:244-247` |
| `read_cmdline`, `read_env` | Process exits during scan, permission denied | Returns empty list or dict | `main.py:79-91` |
| `scan_processes` | A `/proc` entry with empty argv | Skipped | `main.py:105-106` |
| `parse_shortcuts`, `find_game_dir` | Unreadable `shortcuts.vdf` | `OSError` skips that file | `main.py:68-71` |
| `_watch` | Any exception in `tick` | Caught and ignored; loop continues after 1 s | `main.py:215-221` |
| `get_status` in UI | Backend call fails | `console.error`; status unchanged | `dist/index.js:28-35` |
| `act` in UI | Backend call fails | Red toast "Kanto Gear Bottom error" with the error text | `dist/index.js:43-54` |
| Lua `popen` | Exception or nil pipe | `pcall` catches, warns, falls back to original | `main.lua:50-62` |
| Lua shell | Any gate fails | Prints `top`, no error logged | `main.lua:34-39`, `:62` |
| Shell launch | `armada-run-bottom` fails after start | Output discarded (`>/dev/null 2>&1`). Not reported. | `main.lua:35` |

Note the asymmetry: the Lua side logs failures (`main.lua:58`, `:61`) but the shell's own gate failures are silent (`main.lua:38`). The backend reports problems only through the `description` string (`main.py:257-270`).

## 2. Failure-safe defaults
- If the flag is missing, the mod runs the original spawn (`main.lua:34`, `:62`). The feature is off by default.
- The watcher loop catches any `Exception` from `tick` and keeps going (`main.py:217-221`). Nothing restarts `_watch` if it exits by any other route; the code has no such path except task cancellation.
- On unload, `_restore` runs so Ratatoskr is not left stopped (`main.py:212-213`).
- Restore on turn-off happens immediately (`main.py:294-296`).
- Ratatoskr is only stopped when the backend has seen it active (`main.py:231-234`) and only started by the backend when the backend stopped it (`main.py:236`, `:241-242`). Test `test_tick_does_not_start_ratatoskr_it_did_not_stop` covers this.

## 3. Privilege model

| Actor | Identity | Evidence |
|---|---|---|
| Decky plugin backend | root (`flags: ["root"]`) | `plugin.json:4` |
| Game and mod | `armada` (UID 1000) | `main.py:24-25`, `main.py:42-45` |
| Systemctl calls | `--user` for `armada`, via `--machine=armada@.host` first | `main.py:181` |
| Deploy | `ssh` to the Thor, `sudo` for the install steps | `scripts/deploy.sh:27`, `:31-37` |

Files the backend writes for the game (mod copy, flag, flag directory) are chowned to the user (`main.py:141-142`, `:149`, `:165-168`). The comment says why: "The backend runs as root; the game runs as the user and must be able to read what is written here." (`main.py:156-157`).

`USER_ENV` (`main.py:42-45`) sets the user's runtime variables for systemctl calls. No comment in `main.py` gives the reason. The hub note (`project-aynthor.md`, Decky lifecycle entry, context only) attributes it to Decky not passing those variables; that is **unverified** here.

## 4. Device and OS constraints the code relies on

| Constraint | Used by | Evidence |
|---|---|---|
| Two gamescope sessions, bottom one identified by `WAYLAND_DISPLAY=gamescope-secondary` | Companion classification | `main.py:109`, `:97-99` |
| `armada-run-bottom` at `/usr/bin` | Launch | `main.lua:35` |
| Env file under `XDG_RUNTIME_DIR` | Shell gate | `main.lua:33` |
| User systemd units `touch-master.service`, `armada-bottom-screen.service` | Park, restore | `main.py:37-38` |
| `/var/home/armada` as home | Default `HOME` | `main.py:24` |
| `/home/armada/homebrew/plugins/...` as plugin path | Deploy | `scripts/deploy.sh:15` |
| `setsid`, `sh`, `id` present | Launch | `main.lua:33`, `:35` |
| Game folder under the Steam library or `~/Games/Gen1Recomp/linux` | Mod copy | `main.py:65-76` |
| Ratatoskr may be absent, so `start` can fail | Restore fallback | `main.py:244-247` |

Armada's own limits (for example a read-only `/usr`) are recorded in the hub note as context only (`project-aynthor.md`, Armada section). This repo does not check them, and they are **unverified** here.

## 5. Platform guard
The mod does nothing on Windows (`main.lua:45`). The test suite uses this to run the wrapper logic on a development machine (`tests/test_mod.lua:49-52`). The Python backend guards `os.chown` with `AttributeError` (`main.py:159`), which lets the tests run on Windows (**unverified**; not run in this pass).

## 6. Timeouts and bounded waits
| Wait | Bound | Source |
|---|---|---|
| Each systemctl call | 6.0 s | `main.py:183` |
| Watcher period | 1.0 s | `main.py:221` |
| Park grace | 4 ticks (about 4 s) | `main.py:40`, `:236-238` |
| UI poll | 2.0 s | `dist/index.js:39` |
| Shell launch | none (detached) | `main.lua:35` |
| `popen` read | none (blocks until the script writes its line or exits) | `main.lua:53` |

`popen` read has no timeout. The script exits quickly after the detached launch, so the read returns (**unverified** timing).
