# 06 - Roadmap and open items

The repo has no roadmap, TODO list, or issue file. Nothing here is a commitment. Each item is a gap visible in the code or README, with the place it shows up. Owner and priority are **unverified**.

## Repository state at spec time
| Item | Value | Source |
|---|---|---|
| Default branch | `origin/main` at `d147e91` (merge of PR #1) | `git log origin/main` |
| Feature branch | `feat/initial-plugin` at `a8585cc`, already contained in `origin/main` | `git log origin/main..feat/initial-plugin` is empty |
| Local `main` | at `caaa24a`, behind `origin/main` | `git log main` (not updated by this spec pass) |
| `docs/` folder | does not exist on `origin/main` before this spec | `git ls-tree origin/main` |

## Candidate items

| # | Item | Why | Where |
|---|---|---|---|
| R1 | Surface install errors in the UI, or stop turning on when the install reports errors | Currently ignored (application spec L1, L2) | `main.py:287-290`; `dist/index.js:43-54` |
| R2 | Remove or use `DEFAULT_GAME_DIR` and `BOTTOM_X_DISPLAY` | Defined, unused. The `BOTTOM_X_DISPLAY` comment describes behaviour that does not exist. | `main.py:33`, `:36` |
| R3 | Guard the shared `Plugin` state with a lock, or run park and restore on one thread | Several worker threads touch `parked`, `quiet_ticks`, `last_scan` (L4) | `main.py:200-248` |
| R4 | Check the return code of the stock-bottom fallback in `_restore` | Currently ignored (L5) | `main.py:244-247` |
| R5 | Add tests for `set_enabled`, `get_status`, `install_mod` on `Plugin`, and for `_status` text | No coverage today (L9) | `tests/test_backend.py` |
| R6 | Confirm the supported game range and whether gen2 and gen3 are real targets | Manifest lists them; docs say Gen1Recomp only (L10) | `manifest.json:9`; `README.md` |
| R7 | Decide the Decky API version and make `plugin.json` and `dist/index.js` agree | `api_version: 1` vs `API_VERSION = 2` (L11) | `plugin.json:5`; `dist/index.js:2` |
| R8 | Decide what turning off should do with the copied mod | Mod stays in the game folder (L6) | `main.py:294-296` |
| R9 | Check the `bottom` answer against the real bottom session before printing it | Gate checks files, not the running session (L3) | `main.lua:34-36` |
| R10 | Parse `shortcuts.vdf` with a real VDF reader if more fields are needed | Byte regex (L8) | `main.py:50-62` |
| R11 | Reduce `/proc` and file reads per poll if they show up in profiling | Cost not measured (L16) | `dist/index.js:39`; `main.py:250-253` |

## Out of this repo
These are noted in the README "Limits" section. Their fix belongs to other repos (**unverified**).

| Item | Owner per README |
|---|---|
| Companion forwards touch down and up only | Gen1Recomp engine (`src/render/DesktopCompanion.lua`) |
| Ratatoskr bottom dimming and trackpad off while the companion is open | Ratatoskr |

## Not in the repo
- Any user-facing change log. There is no `CHANGELOG` file. The version `0.1.0` appears in `package.json:3`, `plugin.json` (no version), and `manifest.json:4`.
- Release process. `.gitignore` lists `release/` (`.gitignore:5`), but no release script exists in the repo.
