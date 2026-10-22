# 05 - Testing and verification

This spec was written without running anything. The commands below are what the repo documents, not results from this pass (**not run**).

## How to run (as documented)
| Command | Where | Source |
|---|---|---|
| `python tests/test_backend.py` | any machine, no device | `README.md` Tests; `tests/test_backend.py:1` |
| `luajit tests/test_mod.lua` | run from the repo root (`loadfile` uses a relative path), any LuaJIT | `README.md` Tests; `tests/test_mod.lua:1, 21` |
| `node --check dist/index.js` | any machine with Node | `README.md` Tests |
| Pre-flight on the device during deploy | on the Thor, from `/tmp/kgb-preflight` | `scripts/deploy.sh:19-24` |

The deploy pre-flight copies `main.py`, both tests, and the mod into `/tmp/kgb-preflight`, runs `python3 tests/test_backend.py`, `luajit tests/test_mod.lua`, and `luajit -bl` on the mod, then prints `preflight-ok` (`scripts/deploy.sh:20-24`). A failure stops the deploy (`set -euo pipefail` at `scripts/deploy.sh:4`).

## Backend tests (`tests/test_backend.py`)
Fakes `/proc`, home, and `systemctl` (`tests/test_backend.py:1-2`). Thirteen test methods:

| Test (line) | What it asserts |
|---|---|
| `test_parse_shortcuts_and_find_game_dir` (67) | Names parsed from a synthetic `shortcuts.vdf`; game folder resolved from the AppImage path |
| `test_find_game_dir_default_without_shortcut` (76) | Fallback folder when no shortcut exists |
| `test_scan_separates_game_and_companions` (79) | Game PID vs companion PIDs; `bottom` flag per companion |
| `test_mod_enabled_in_options` (89) | Text match of `thor_bottom_companion = true` only |
| `test_install_mod_copies_once` (97) | First install reports changed files; second reports none |
| `test_install_mod_reports_missing_folder` (106) | Missing mods folder gives an error |
| `test_flag` (110) | Set, unset, and double unset |
| `test_tick_parks_and_restores_ratatoskr` (122) | Stop on bottom companion; start after `RELEASE_AFTER_TICKS` quiet ticks |
| `test_companion_respawn_does_not_bounce_ratatoskr` (136) | One stop and no start across a companion gap of one tick |
| `test_tick_leaves_ratatoskr_alone_when_off` (146) | No park when flag is absent |
| `test_tick_does_not_start_ratatoskr_it_did_not_stop` (152) | Inactive Ratatoskr is not started |
| `test_restore_falls_back_to_stock_bottom_screen` (160) | If `touch-master` start fails, `armada-bottom-screen.service` is started |
| `test_turning_off_restores_immediately` (175) | Flag removal restores Ratatoskr on the next tick |

Note that the flag tests write to the fake `FLAG` path because `load_backend` points `KGB_HOME` at a temp directory before import (`tests/test_backend.py:12-17`).

## Mod tests (`tests/test_mod.lua`)
Loads the real `main.lua` against a stub `HostShell` (`tests/test_mod.lua:2-23`). Seven numbered cases:

| # | Case (line) | Asserts |
|---|---|---|
| 1 | Non-companion spawn (27) | Original called; no shell run |
| 2 | Companion, bottom answer (33) | Returns `true`; no top spawn; command contains the companion argument and `armada-run-bottom` |
| 3 | Companion, `top` answer (40) | Original called |
| 4 | `popen` error or `nil` (43-47) | Original called |
| 5 | Windows (49) | Original called |
| 6 | Second load (54) | Wrapper not wrapped again |
| 7 | Apostrophe in an argument (60) | Shell quoting produces `'\''` |

## What is not covered
| Area | Covered by tests? | Evidence |
|---|---|---|
| `Plugin.set_enabled`, `get_status`, `install_mod` methods | no | no reference to them in `tests/` (grep of `tests/`) |
| `Plugin._status` note strings | no | same |
| `Plugin._main`, `_watch`, `_unload` | no | same |
| `run_systemctl` with the real `systemctl` | no (replaced by a fake) | `tests/test_backend.py:51-59` |
| `read_env` / `read_cmdline` on real `/proc` | no (fake files only) | `tests/test_backend.py:30-34` |
| `_chown` on the device | no | `main.py:155-160` swallows errors; no test asserts ownership |
| `dist/index.js` behaviour | syntax only (`node --check`) | `README.md` Tests |
| Real Gen1Recomp spawn, real `armada-run-bottom`, real Ratatoskr stop | no; device-only | **unverified** on device in this pass |

## Verification on a device (manual, from the README)
The README gives no manual checklist. The steps in [02](02-users-workflows.md) are the only user-facing steps. Device checks are **unverified** beyond these.
