# 01 - Purpose and scope

## Purpose
Put Kanto Gear's second-screen window on the bottom display of an AYN Thor, so that Kanto Gear appears on the lower screen while Gen1Recomp plays on the top one (`README.md`, first paragraph).

## What is in the repo
| Part | Path | Role |
|---|---|---|
| Decky backend | `main.py` | Owns the flag file, installs the mod, parks and restores Ratatoskr, exposes status (`main.py:1-12`) |
| Decky UI | `dist/index.js` | Single toggle, status rows, install/reinstall button (`dist/index.js:24-96`) |
| Plugin manifest | `plugin.json` | Name, author, `flags: ["root"]`, `api_version: 1` (`plugin.json:1-6`) |
| Helper mod | `mod/thor_bottom_companion/main.lua` | Wraps `HostShell.spawnSelfDetached` for companion launches (`main.lua:18-63`) |
| Mod manifest | `mod/thor_bottom_companion/manifest.json` | Mod id, version `0.1.0`, `api: 2`, game and permission declarations (`manifest.json:1-17`) |
| Mod card | `mod/thor_bottom_companion/mod.card` | Manager detail-pane metadata: summary, credits, compatibility (`mod.card:1-19`). Not read by any code in the repo. |
| Deploy script | `scripts/deploy.sh` | Pushes the plugin and mod to a Thor over SSH and restarts the plugin loader (`scripts/deploy.sh:1-40`) |
| Tests | `tests/test_backend.py`, `tests/test_mod.lua` | Backend and mod tests (see [05](05-testing-verification.md)) |
| Package metadata | `package.json`, `LICENSE`, `.gitattributes`, `.gitignore` | `package.json` declares no scripts and no dependencies (`package.json:1-9`). MIT license is stated in `package.json:8` and `LICENSE`. |

## In scope
- Switching the bottom-screen behaviour on and off from the Quick Access menu (`dist/index.js:56-68`).
- Copying the helper mod into the game's `mods` folder (`main.py:132-152`, `main.py:299-304`).
- Launching the Separate Screens companion through `armada-run-bottom` while the flag is set (`mod/thor_bottom_companion/main.lua:31-40`).
- Stopping `touch-master.service` while a companion window is on the bottom screen and starting it again afterwards (`main.py:226-248`).
- Deploying to a Thor over SSH (`scripts/deploy.sh`).

## Out of scope (by what the code does)
- Kanto Gear itself, the Gen1Recomp engine, and the Gen1Recomp mod manager. The repo contains none of their source. The README credits them and says no code from them is copied (`README.md`, "Credits").
- Armada's `armada-run-bottom` and the bottom gamescope. The mod calls `/usr/bin/armada-run-bottom` (`main.lua:34-35`); its behaviour is not in the repo (**unverified**).
- Ratatoskr (`touch-master.service`). The backend only starts and stops that unit by name (`main.py:37`, `main.py:232-244`).
- Building or packaging. No build step exists in the repo: `dist/index.js` is hand-written and deployed as-is (`scripts/deploy.sh:29`).
- Any non-Thor device. Paths and the `armada` user are hard-coded (`main.py:24`, `scripts/deploy.sh:15`).

## Target hardware and OS
| Item | Value | Source |
|---|---|---|
| Device | AYN Thor | `README.md` title and first paragraph |
| OS | Armada OS (bottom panel run by a second gamescope on `gamescope-secondary`) | `README.md`; `main.py:109` |
| Game | Gen1Recomp, AppImage, `arm64` file name in the test fixture | `tests/test_backend.py:37` |
| Game user | `armada`, UID 1000 by default | `main.py:24-25`, `main.py:42-45` |
| Plugin loader | Decky Loader, plugin runs as root | `plugin.json:4` (`flags: ["root"]`) |
| Game version range | `>=0.3.20 <2.0.0` | `manifest.json:10`, `mod.card:18` |

Game versions and Armada versions beyond these declarations are **unverified**.
