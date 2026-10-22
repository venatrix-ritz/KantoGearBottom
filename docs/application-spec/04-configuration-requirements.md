# 04 - Configuration and requirements

## Constants in `main.py`
| Name | Value | Line | Used |
|---|---|---|---|
| `HOME` | `KGB_HOME` env, default `/var/home/armada` | `main.py:24` | yes |
| `UID` | `KGB_UID` env, default `1000` | `main.py:25` | yes |
| `PROC` | `KGB_PROC` env, default `/proc` | `main.py:26` | yes |
| `PLUGIN_DIR` | directory of `main.py` | `main.py:27` | yes |
| `FLAG` | `HOME/.config/kanto-gear-bottom/enabled` | `main.py:29` | yes |
| `MOD_ID` | `thor_bottom_companion` | `main.py:30` | yes |
| `MOD_SRC` | `PLUGIN_DIR/mod/thor_bottom_companion` | `main.py:31` | yes |
| `SHORTCUTS_GLOB` | `.local/share/Steam/userdata/*/config/shortcuts.vdf` | `main.py:32` | yes |
| `DEFAULT_GAME_DIR` | `HOME/Games/Gen1Recomp/linux` | `main.py:33` | **no** (see [06](06-limitations-glossary.md)); `find_game_dir` repeats the literal at `main.py:76` |
| `COMPANION_ARG` | `--display-companion=` | `main.py:35` | yes |
| `BOTTOM_X_DISPLAY` | `:2` | `main.py:36` | **no** |
| `RATATOSKR` | `touch-master.service` | `main.py:37` | yes |
| `STOCK_BOTTOM` | `armada-bottom-screen.service` | `main.py:38` | yes |
| `RELEASE_AFTER_TICKS` | `4` | `main.py:40` | yes |
| `USER_ENV` | `XDG_RUNTIME_DIR=/run/user/<UID>`, `DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/<UID>/bus` | `main.py:42-45` | yes |

Watcher interval: one tick per second (`main.py:221`). Systemctl timeout: 6.0 s (`main.py:183`).

## Constants in the Lua mod
| Name | Value | Line |
|---|---|---|
| Flag path | `$HOME/.config/kanto-gear-bottom/enabled` | `main.lua:32` |
| Env file | `${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/armada-bottom-env` | `main.lua:33` |
| Launcher | `/usr/bin/armada-run-bottom` | `main.lua:34-35` |
| Guard key | `HostShell._thorBottomCompanionOriginal` | `main.lua:22`, `:25` |

## Environment variables
| Variable | Read by | Default | Purpose |
|---|---|---|---|
| `KGB_HOME` | `main.py:24` | `/var/home/armada` | Home used for flag, shortcuts, game folder. Set by `tests/test_backend.py:13`. |
| `KGB_UID` | `main.py:25` | `1000` | Owner for files written by the backend, and the UID in `USER_ENV` |
| `KGB_PROC` | `main.py:26` | `/proc` | Process table root for tests |
| `XDG_RUNTIME_DIR` | `main.lua:33` (shell) | `/run/user/$(id -u)` | Env-file location |
| `APPIMAGE` | `main.lua:34` (shell) | set by the AppImage runtime | Game executable |
| `WAYLAND_DISPLAY` | `main.py:109` (read from `/proc/<pid>/environ`) | n/a | Must equal `gamescope-secondary` for a bottom companion |
| `THOR_HOST`, `THOR_ENV_FILE` | `scripts/deploy.sh:7-12` | none | Deploy target (developer machine only) |

## Deploy host resolution
Order (`scripts/deploy.sh:8-13`):
1. Command-line argument 1.
2. `THOR_HOST` environment variable.
3. The first existing file of `$THOR_ENV_FILE`, `./local/thor.env`, `../AynThor/local/thor.env`. Line `THOR_HOST=` is read from it.

If none resolves, the script exits with status 2 (`scripts/deploy.sh:13`). `local/` is git-ignored (`.gitignore:4`). The script comment says to keep the address out of tracked files (`scripts/deploy.sh:3`).

## Filesystem layout on the device
| Path | Owner | Written by | Source |
|---|---|---|---|
| `/home/armada/homebrew/plugins/kanto-gear-bottom/` | root:root, 755 | `deploy.sh` | `scripts/deploy.sh:15, 35-36` |
| `.../main.py`, `plugin.json`, `package.json`, `dist/index.js`, `mod/` | root | `deploy.sh` | `scripts/deploy.sh:28-34` |
| `/tmp/kgb-plugin-backup-<stamp>` | root | `deploy.sh` (only when a previous `main.py` exists) | `scripts/deploy.sh:27` |
| `$HOME/.config/kanto-gear-bottom/enabled` | armada | plugin on toggle | `main.py:163-173` |
| `<game_dir>/mods/thor_bottom_companion/` | armada (chowned) | plugin on enable or install | `main.py:139-152` |

`game_dir` comes from the Steam shortcut's AppImage, else `$HOME/Games/Gen1Recomp/linux` (`main.py:65-76`).

## Requirements

### Device (AYN Thor, Armada OS)
| Requirement | Evidence in repo |
|---|---|
| Decky Loader with a plugin loader service named `plugin_loader.service` | `scripts/deploy.sh:37` |
| Decky plugin running as root (`flags: ["root"]`) | `plugin.json:4` |
| Python 3 (no version pinned; `from __future__ import annotations` at `main.py:13`) | `scripts/deploy.sh:24`, `README.md` Tests |
| LuaJIT (for the mod test and the byte-compile check) | `scripts/deploy.sh:24`, `README.md` Tests |
| `systemctl --user` with a user `armada` session and `touch-master.service` present | `main.py:37`, `main.py:178-190` |
| Gen1Recomp AppImage with `$APPIMAGE` exported | `main.lua:34`, `main.py:111` |
| Kanto Gear inside Gen1Recomp, Display Mode "Separate Screens" | `README.md` Install step 3 |
| `/usr/bin/armada-run-bottom` (executable) and the env file at runtime | `main.lua:34-35` |
| `setsid`, `id`, `sh` on the PATH | `main.lua:33, 35` |
| `sudo` for the deploy user | `scripts/deploy.sh:27, 31-37` |

### Developer machine
| Requirement | Evidence |
|---|---|
| `bash` (script), `ssh`, `scp` | `scripts/deploy.sh` |
| Node.js for `node --check dist/index.js` | `README.md` Tests |
| Python 3 and LuaJIT, only if you run the tests locally | `README.md` Tests |

### Not required
- No build tool, package manager lock file, or bundler (`package.json` has no `scripts`, `dependencies` or `devDependencies`; no lock file in the repo).
- No network access at runtime. The plugin makes no outbound calls (no network code in `main.py` or `dist/index.js`).

## Git and line endings
`.gitattributes` forces LF for `*.py`, `*.sh`, `*.lua`, `*.js`, `*.json`, `*.card` (`.gitattributes:1-8`). `.gitignore` excludes `__pycache__/`, `*.py[cod]`, `node_modules/`, `local/`, `release/`, `*.log` (`.gitignore:1-6`).
