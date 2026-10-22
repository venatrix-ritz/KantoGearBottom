# 03 - Data flow

## 1. Enable path (user switches the toggle on)

```mermaid
sequenceDiagram
  participant U as User
  participant UI as dist/index.js
  participant BE as main.py Plugin
  participant FS as Game folder and flag
  U->>UI: toggle on
  UI->>BE: set_enabled(true)
  BE->>BE: find_game_dir() (Steam shortcut or default)
  BE->>FS: install_mod(MOD_SRC, game/mods)
  FS-->>BE: {changed, errors} (errors not checked)
  BE->>FS: set_flag(True) (touch flag)
  BE->>BE: _status() (reads flag, options.lua, /proc)
  BE-->>UI: status + install
  UI-->>U: toast "On: the next second-screen window opens on the bottom screen"
```
Source: `main.py:285-293`, `dist/index.js:63-64`.

## 2. Companion launch path (game running, engine opens companion)

```mermaid
sequenceDiagram
  participant E as Gen1Recomp engine
  participant M as main.lua wrapper
  participant SH as sh -c SCRIPT
  participant L as armada-run-bottom
  participant C as companion (bottom gamescope)
  participant O as original spawn
  E->>M: spawnSelfDetached(args)
  alt args[1] starts with --display-companion= and not Windows
    M->>SH: popen "sh -c SCRIPT ... args"
    SH->>SH: check $APPIMAGE, flag, env file, launcher
    alt all gates pass
      SH->>L: setsid armada-run-bottom -- $APPIMAGE args (detached)
      SH-->>M: "bottom"
      M-->>E: true
      L->>C: start companion on gamescope-secondary
    else any gate fails
      SH-->>M: "top"
      M->>O: original(args)
      O-->>E: companion on the top screen
    end
  else other spawns or Windows
    M->>O: original(args)
  end
```
Source: `main.lua:42-62`, `main.lua:31-40`. The return value of the original function is not known to the mod (**unverified** engine contract).

## 3. Park and restore (Ratatoskr)

```mermaid
stateDiagram-v2
  [*] --> Idle
  Idle --> Parked: flag set AND companion on bottom AND touch-master active - systemctl stop
  Idle --> Idle: flag set AND companion on bottom AND touch-master not active - no change
  Parked --> Parked: companion on bottom - quiet_ticks reset to 0
  Parked --> Parked: no bottom companion and quiet_ticks below 4
  Parked --> Idle: no bottom companion for 4 ticks - systemctl start touch-master, else stock bottom
  Parked --> Idle: flag removed - immediate restore on next tick or on set_enabled false
```
Source: `main.py:226-248`. Thresholds: `RELEASE_AFTER_TICKS = 4` (`main.py:40`), tick interval 1 s (`main.py:221`).

Ticks checked by `tests/test_backend.py:122-183`: park, release after the grace period, no bounce on a one-tick gap, no park when the flag is off, no start of a unit the backend did not stop, fallback to the stock bottom service, and immediate restore when the flag is cleared.

## 4. Status poll

```mermaid
flowchart LR
  T["UI timer every 2 s"] -->|get_status| S["_status()"]
  S --> SCAN["scan_processes() reads /proc"]
  S --> GD["find_game_dir() reads shortcuts.vdf"]
  S --> OPT["options.lua text read"]
  S --> FLAG["flag exists"]
  S --> R["dict to UI"]
```
Source: `dist/index.js:37-41`, `main.py:250-280`. Cost **unverified**. The watcher also calls `scan_processes` once a second (`main.py:228`).

## 5. Install path (button)

```mermaid
flowchart LR
  B["Install button"] -->|install_mod| IM["Plugin.install_mod"]
  IM --> FG["find_game_dir()"]
  FG --> CP["install_mod(MOD_SRC, game/mods)"]
  CP -->|copy only changed files| MODS["game/mods/thor_bottom_companion/"]
  CP --> ST["_status() + install"]
  ST --> UI["toast 'Helper mod copied into Gen1Recomp'"]
```
Source: `main.py:299-304`, `dist/index.js:83-92`. The flag is not changed on this path.

## 6. Data at rest and in transit

| Data | Location | Format | Crosses a boundary |
|---|---|---|---|
| Switch | `$HOME/.config/kanto-gear-bottom/enabled` | empty file | Read by backend and shell |
| Mod | Repo `mod/` to game `mods/` | files, byte copy | Plugin to game (same device) |
| Status | Backend to UI | JSON-compatible dict | Decky RPC |
| Companion argv | Engine to mod to shell | string array, shell-quoted | In-process to child process |
| Process table | Kernel `/proc` | NUL-separated | Read-only |
| Systemd state | `systemctl` output | text | Subprocess |

No network, no database, no persisted logs written by the plugin (the Lua mod logs via `mod.log`, destination **unverified**).
