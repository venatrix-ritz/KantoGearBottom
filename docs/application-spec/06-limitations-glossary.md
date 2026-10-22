# 06 - Known limitations, open questions, glossary

Items marked **code** are visible from the source. Items marked **readme** are repeated from the README and depend on code outside this repo (**unverified**).

## Known limitations

| # | Limitation | Evidence | Kind |
|---|---|---|---|
| L1 | Install errors do not block switching on. `set_enabled(True)` sets the flag after `install_mod` whether or not `errors` is empty. | `main.py:287-290` | code |
| L2 | The UI does not show install errors. Toast text is the success message whenever no exception is thrown. `status.install` is never read by the UI. | `dist/index.js:43-54`, `:63-64`; no `.install` reference in `dist/index.js` | code |
| L3 | The toggle does not verify the bottom session. The shell gate checks the env file and the launcher, not that the bottom gamescope is up. The launch is detached and its output is discarded, so `bottom` is printed even if `armada-run-bottom` later fails. | `mod/thor_bottom_companion/main.lua:34-36`, `:35` | code |
| L4 | Parked state is shared across threads without a lock. `_watch` runs `tick` in a worker thread every second; `set_enabled`, `get_status`, and `_unload` each run in their own worker thread, and all of them can touch `parked`, `quiet_ticks`, and `last_scan`. | `main.py:213`, `:218`, `:283`, `:297`, `:226-248` | code. Consequences **unverified**. |
| L5 | `_restore` ignores the return code of the fallback start of `armada-bottom-screen.service` and clears `parked` regardless. | `main.py:244-248` | code |
| L6 | Turning off does not remove the copied mod. | `main.py:294-296` (no removal call) | code. Gen1Recomp behaviour **unverified**. |
| L7 | Two constants are defined but unused: `DEFAULT_GAME_DIR` and `BOTTOM_X_DISPLAY`. The comment on `BOTTOM_X_DISPLAY` says it is read from the env file at runtime, and nothing reads it. | `main.py:33`, `:36` (grep of repo) | code |
| L8 | Shortcut parsing is a byte regex, not a VDF parser. Rows start at each `AppName`, so a row whose `Exe` appears before its `AppName` would be attached to the previous shortcut. Steam's actual key order is **unverified**. | `main.py:50-62` | code |
| L9 | No test covers the `Plugin` methods the UI calls (see [05](05-testing-verification.md#what-is-not-covered)). | `tests/test_backend.py` | code |
| L10 | Manifest lists `gen1`, `gen2`, `gen3` as games, while the README and the deploy target are Gen1Recomp only. Support for gen2 and gen3 is **unverified**. | `mod/thor_bottom_companion/manifest.json:9`; `README.md` | code |
| L11 | `plugin.json` says `api_version: 1`. `dist/index.js` connects with `API_VERSION = 2` and falls back to 1. Which the installed Decky loader needs is **unverified**. | `plugin.json:5`; `dist/index.js:2`, `:8-12` | code |
| L12 | The mod patches engine code. Its only guard is the `isWindows()` check and the flag. The engine's `HostShell` API is not in the repo, so the stub in `tests/test_mod.lua` is the only contract check. | `mod/thor_bottom_companion/main.lua:19-24`, `:45`; `tests/test_mod.lua:9-16`; README "Limits" | code, engine side **unverified** |
| L13 | Touch forwarding is down and up only, with no move events. | README "Limits" | readme. Engine file `src/render/DesktopCompanion.lua` is not in this repo. **unverified** |
| L14 | Ratatoskr bottom-screen dimming and trackpad are off while a companion window is open. | README "Limits" | readme. Not verifiable here. **unverified** |
| L15 | A companion that is not on `gamescope-secondary` is ignored for parking, so Ratatoskr keeps running. | `main.py:223-224`, `:228-233` | code |
| L16 | Every UI poll (every 2 s) and every watcher tick (every 1 s) re-scans `/proc` and reads `shortcuts.vdf` for status. Cost **unverified**. | `dist/index.js:39`; `main.py:215-221`, `:250-253` | code |
| L17 | The deploy pre-flight runs tests on the device and needs `sudo` for install, which is a manual prerequisite. | `scripts/deploy.sh:19-37` | code |

## Open questions (not answered by the repo)
- Which Decky loader version the plugin targets (see L11).
- Whether `armada-run-bottom` returns a non-zero code on failure. The mod does not check it (L3).
- The contents and lifecycle of `armada-bottom-env`, and whether it is always present when the bottom session is up.
- Whether Gen1Recomp's `options.lua` text format is stable across the version range (`main.py:116-122` depends on it).
- What `HostShell.spawnSelfDetached` returns to its caller in the engine when the mod returns `true` (`main.lua:57-60`).

## Glossary

| Term | Meaning in this repo |
|---|---|
| **AYN Thor** | The handheld device this plugin targets. Two screens: top and bottom. (`README.md`) |
| **Armada OS** | The OS on the Thor. Runs a second gamescope for the bottom panel. (`README.md`) |
| **armada-run-bottom** | Armada's launcher that starts a client on the bottom gamescope. Path `/usr/bin/armada-run-bottom` (`main.lua:35`). Behaviour **unverified**. |
| **Bottom gamescope** | The second gamescope session for the bottom panel. Identified by `WAYLAND_DISPLAY=gamescope-secondary` (`main.py:109`). |
| **Companion window** | The second-screen copy of Gen1Recomp started with `--display-companion=<port>,<token>` (`main.py:35`, `main.lua:3-6`). |
| **Decky Loader** | The plugin loader for the Steam Deck UI. The plugin runs under it (`plugin.json`, `dist/index.js:1-14`). |
| **Flag file** | `$HOME/.config/kanto-gear-bottom/enabled`. Its presence turns the feature on (`main.py:29`). |
| **Gen1Recomp** | The Pokemon Gen 1 recompilation engine that hosts Kanto Gear. Credited in `README.md`. |
| **Helper mod** | `thor_bottom_companion`, the Gen1Recomp mod in `mod/thor_bottom_companion/`. |
| **Kanto Gear** | The companion UI that shows on the second screen. Credited in `README.md`. |
| **Parked** | State where this backend has stopped Ratatoskr so the bottom touchscreen is free (`main.py:202`). |
| **Ratatoskr** | The bottom touchscreen driver, shipped as `touch-master.service` (`main.py:37`). The hub note records the rename to Ratatoskr with the unit name unchanged (context only, `G:\Projects\Hardware\AynThor` notes). |
| **Separate Screens** | Kanto Gear's display mode that starts the companion window (`README.md`, step 3). |
| **Stock bottom service** | `armada-bottom-screen.service`, the fallback started when Ratatoskr fails to start (`main.py:38`, `:246`). |
| **Helper mod folder** | `<game_dir>/mods/thor_bottom_companion/`. |
