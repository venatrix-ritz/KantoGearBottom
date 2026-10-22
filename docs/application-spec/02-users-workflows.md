# 02 - Users and workflows

## Users
| User | What they do | Evidence |
|---|---|---|
| The device owner (repo author, Ven) | Installs, switches on, and debugs the plugin on their own Thor | Author fields in `plugin.json:3`, `mod.card:4`; deploy target is a single host (`scripts/deploy.sh:3`) |
| Any Decky user on a Thor | Uses the Quick Access toggle | `dist/index.js:56-68` |

No multi-user, account, or network-facing feature exists. The only network-facing action is the SSH deploy, run from a developer machine (`scripts/deploy.sh`).

## Workflow 1: first install (from the README)
1. Deploy from a developer machine: `scripts/deploy.sh [host]` (`README.md`, "Install"; `scripts/deploy.sh:8-13` for host resolution).
   - Pre-flight runs both test files and a LuaJIT byte-compile on the device before anything is installed (`scripts/deploy.sh:19-24`).
   - Existing plugin is backed up to `/tmp/kgb-plugin-backup-<stamp>` (`scripts/deploy.sh:27`).
   - Files are placed under `/home/armada/homebrew/plugins/kanto-gear-bottom`, owned by root, mode 755, and `plugin_loader.service` is restarted (`scripts/deploy.sh:15, 31-37`).
2. In the Quick Access menu, open **Kanto Gear Bottom** and switch it on (`scripts/deploy.sh:39`; `README.md` step 1).
   - Switching on runs `install_mod` (copies the helper mod into `<game dir>/mods/thor_bottom_companion`), then writes the flag file (`main.py:285-293`).
3. In Gen1Recomp's mod manager, enable **Thor Bottom Companion** (`README.md` step 2). The backend only detects this by a text match of `thor_bottom_companion = true` in `options.lua` (`main.py:116-122`).
4. In Kanto Gear's settings, set **Display Mode** to **Separate Screens** (`README.md` step 3). This setting lives in Kanto Gear; the repo never reads it.

Step 1 says the plugin copies the mod "when you switch it on" (`scripts/deploy.sh:40`). This matches `set_enabled(True)` (`main.py:287-293`).

## Workflow 2: daily use
1. Start Gen1Recomp from Game Mode (the game process is found by `APPIMAGE` env matching `gen1recomp.*\.AppImage`, `main.py:111`).
2. The Lua mod intercepts the engine's companion spawn (`--display-companion=<port>,<token>`). If all four shell gates pass (the flag is one of them), `armada-run-bottom` is used; otherwise the engine's own spawn runs (`main.lua:43-62`).
3. The backend polls once per second. When a companion reports `WAYLAND_DISPLAY=gamescope-secondary`, it stops `touch-master.service` (`main.py:215-239`).
4. When the companion window is gone for about four ticks (`main.py:40`, `main.py:236-239`), or the flag is removed (`main.py:238`), Ratatoskr is started again.

## Workflow 3: switching off
- Turning the toggle off removes the flag and immediately restarts Ratatoskr if it was parked (`main.py:294-296`, `main.py:241-248`).
- The helper mod stays installed in the game's `mods` folder. Nothing removes it (`main.py:294-296` does not touch the mod folder; **unverified** whether Gen1Recomp disables it on its own).

## Workflow 4: reinstall the helper mod
- The UI shows an install button when the mod is missing, or when it is installed but not enabled in the game (`dist/index.js:83-92`). Labels: "Install helper mod" or "Reinstall helper mod".
- The button calls `install_mod`, which copies only files whose bytes differ (`main.py:146-147`, `main.py:299-304`).
- This path does not touch the flag file (`main.py:299-304`).

## Status messages a user sees
The backend returns one `description` string (`main.py:258-270`). The UI shows it as the toggle's description (`dist/index.js:61`). The full list is in [03](03-features-interfaces.md#status-description-strings).

## Failure paths a user can hit
| Symptom | Where the code reports it |
|---|---|
| Gen1Recomp not found | "Gen1Recomp was not found (looked for the Steam shortcut's AppImage)" (`main.py:257-258`) |
| Mod not copied | "Helper mod is not installed yet" (`main.py:259-260`) |
| Mod not enabled in game | "Enable 'Thor Bottom Companion' ..." (`main.py:261-262`) |
| Flag on but no companion window | "On, but no second-screen window is open ..." (`main.py:267-268`) |
| Error during toggle or install | A red toast "Kanto Gear Bottom error" only on a thrown exception (`dist/index.js:49-50`). See [06](06-limitations-glossary.md) for the install-error gap. |
