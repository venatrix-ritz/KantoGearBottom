# 05 - Design decisions

Each entry gives the decision, the evidence in the repo, and the reason. Where the repo gives no reason, the entry says so. **No rejected alternatives are recorded in the repo**; none are listed here.

| # | Decision | Evidence | Reason stated in repo |
|---|---|---|---|
| D1 | A flag file is the on/off switch | `main.py:29`, `main.lua:31-36` | `main.lua:14-16`: the decision is made in the shell command "so the mod needs no io/os access of its own" |
| D2 | The shell, not Lua, decides top or bottom | `main.lua:31-40` | Same comment, `main.lua:15-16` |
| D3 | Wrap the engine's spawn instead of changing engine files | `main.lua:24-25`, `:42-62`; `README.md` "Limits" | `main.lua:8-12`: the mod wraps `spawnSelfDetached`; "every other spawn" goes to the original untouched. README says the mod "patches engine code". |
| D4 | Fall back to the engine's own spawn on any failure | `main.lua:45`, `:57-62` | `main.lua:10-12`: "every case where the bottom screen is not available or not switched on, goes to the original function untouched" |
| D5 | Launch through `armada-run-bottom` with `setsid`, detached | `main.lua:35` | No reason in code. Detaching is the only visible effect. **Reason unverified.** |
| D6 | Park Ratatoskr instead of sharing the bottom touchscreen | `main.py:9-11`; `README.md` "How it works" | `main.py:9-11`: Ratatoskr "holds the bottom touchscreen exclusively"; the plugin does "the same swap the Minecraft HUD plugin does" (that plugin is not in the repo; **unverified**) |
| D7 | Grace period of 4 ticks before restore | `main.py:39-40`, `:236-238`; test at `tests/test_backend.py:136-144` | `main.py:39`: "A companion that drops and restarts (the engine respawns it with a new port) must not bounce Ratatoskr." |
| D8 | Detect companions by scanning `/proc`, not by stored PIDs | `main.py:94-113` | No reason in code. The scan is stateless, so a restarted backend sees the same picture. **Reason inferred; unverified.** |
| D9 | Companion is "bottom" by `WAYLAND_DISPLAY=gamescope-secondary` | `main.py:97-99`, `:109` | Docstring `main.py:97-99`: a companion "counts as 'on the bottom' when it runs against the bottom gamescope" |
| D10 | Copy the mod on enable and on reinstall; copy only changed files | `main.py:132-152`, `:286-304` | No reason in code. Byte compare avoids rewriting unchanged files. **Reason inferred.** |
| D11 | Mod copy is owned by the game user | `main.py:141-142`, `:149`, `:165-168` | `main.py:156-157`: "The backend runs as root; the game runs as the user and must be able to read what is written here." |
| D12 | Text check of `options.lua` rather than a Lua parse | `main.py:116-122` | `main.py:117`: "A text check; the file is the game's own." |
| D13 | `systemctl --machine=armada@.host --user` is tried first, then `--user` | `main.py:181` | No reason in code. Hub note (context only) describes the Decky permission drop. **Unverified here.** |
| D14 | On restore failure, start `armada-bottom-screen.service` | `main.py:244-247` | No reason in code. The unit is the stock bottom service (`main.py:38`). **Reason inferred.** |
| D15 | Turning off restores immediately, without the grace period | `main.py:238`, `:294-296` | `main.py:238`: restore happens when the flag is gone; the grace only applies while the flag is still set. Covered by `tests/test_backend.py:175-183`. |
| D16 | Idempotent wrap guard | `main.lua:21-22`, `:25` | `main.lua:21`: "A second load of this mod in the same process must not wrap the wrapper." Covered by `tests/test_mod.lua:54-58`. |
| D17 | Plugin runs as root | `plugin.json:4` | No reason in code. **Reason unverified.** |
| D18 | No build step; the shipped JS is the source | `package.json` (no `scripts`), `scripts/deploy.sh:29` | No reason in code. **Reason unverified.** |
| D19 | Deploy runs the tests on the device before installing | `scripts/deploy.sh:19-24` | Comment `scripts/deploy.sh:19`: "tests run in /tmp, nothing installed yet" |
| D20 | Host address stays out of tracked files | `scripts/deploy.sh:3`, `.gitignore:4` | Comment `scripts/deploy.sh:3`: "Keep the address out of tracked files." |
| D21 | No engine code copied; credits listed | `README.md` "Credits"; `mod/.../mod.card:14-17` | `README.md`: "No code from those projects is copied here." |
| D22 | Parse shortcuts with a byte regex, not a VDF parser | `main.py:50-62` | No reason in code. **Reason inferred** (a small surface that covers the one field needed). Known consequence: see application spec limitation L8. |
