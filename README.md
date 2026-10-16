# Kanto Gear Bottom

Opens [Kanto Gear](https://github.com/AverageConsumer/kanto-gear)'s second-screen window on the **bottom screen of an AYN Thor** running Armada OS. A Decky plugin plus a small Gen1Recomp mod.

## How it works
- Kanto Gear's **Separate Screens** mode makes [Gen1Recomp](https://github.com/bryanthaboi/gen1recomp) start a second copy of itself (`--display-companion=<port>,<token>`, `src/render/DesktopScreen.lua`) and stream frames to it. That copy opens in whatever session the game is in: the top screen.
- Armada runs a second gamescope for the bottom panel and ships `armada-run-bottom -- <cmd>` to start a client on it.
- The helper mod `thor_bottom_companion` wraps `HostShell.spawnSelfDetached` so the companion is started through `armada-run-bottom`. It acts only while `~/.config/kanto-gear-bottom/enabled` exists and the bottom session is up; otherwise the original spawn runs.
- Ratatoskr holds the bottom touchscreen exclusively, so while a companion window is on the bottom screen the plugin stops `touch-master.service` and starts it again a few seconds after the window closes (the same swap the Minecraft HUD plugin does).

## Install
```bash
scripts/deploy.sh            # host from local/thor.env, ../AynThor/local/thor.env, $THOR_HOST or argument 1
```
Then, once:
1. Quick Access menu, **Kanto Gear Bottom**, switch it on (this copies the helper mod into the game's `mods/` folder).
2. In Gen1Recomp's mod manager, enable **Thor Bottom Companion**.
3. In Kanto Gear's settings set **Display Mode** to **Separate Screens**.

## Limits
- The engine's companion window forwards touch **down and up only**, never moves (`src/render/DesktopCompanion.lua`). Taps work; drags and swipes that depend on movement may not.
- Ratatoskr's bottom-screen dimming and trackpad are off while the companion window is open.
- The mod patches engine code (Gen1Recomp labels it "PATCHES ENGINE CODE"). It touches nothing but the companion spawn.

## Tests
```bash
python tests/test_backend.py      # backend, no device
luajit tests/test_mod.lua         # the mod's wrapper against a stub HostShell (run on the Thor or any LuaJIT)
node --check dist/index.js
```

## Credits
Kanto Gear by AverageConsumer; Gen1Recomp by the Pokemon Gen 1 Recompilation Project (bryanthaboi); `armada-run-bottom` and the dual-screen setup by Armada OS; the loader/unloader pattern follows the Minecraft HUD plugin. No code from those projects is copied here.
