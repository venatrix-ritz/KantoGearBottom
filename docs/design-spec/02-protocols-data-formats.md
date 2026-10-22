# 02 - Protocols and data formats

## 1. Flag file
| Item | Value | Source |
|---|---|---|
| Path | `$HOME/.config/kanto-gear-bottom/enabled` (`KGB_HOME` overrides `$HOME`) | `main.py:29`, `:24` |
| Content | Not read. Presence only. Created empty by `Path.touch()`. | `main.py:163-173` |
| Create | `mkdir(parents=True)`, chown parent and file to UID | `main.py:165-168` |
| Remove | `unlink`, `FileNotFoundError` ignored | `main.py:170-173` |
| Readers | Python `FLAG.exists()` (`main.py:229`, `:238`, `:256`); shell `[ -f "$flag" ]` (`main.lua:34`) | |

The shell gate and the Python check read the same path. Only the backend writes it.

## 2. Status dictionary (Decky RPC response)
Returned by `get_status`, `set_enabled`, `install_mod` (all built by `_status`, `main.py:250-280`). Types are as built in Python.

| Key | Type | Source expression |
|---|---|---|
| `enabled` | bool | `FLAG.exists()` (`main.py:256`) |
| `mod_installed` | bool | `(game_dir/mods/MOD_ID/main.lua).is_file()` (`main.py:254`) |
| `mod_enabled_in_game` | bool | `mod_enabled_in_options(game_dir/options.lua)` (`main.py:255`) |
| `game_dir` | string | `str(find_game_dir())` (`main.py:275`) |
| `game_running` | bool | `bool(scan["game"])` (`main.py:276`) |
| `on_bottom` | bool | `self.on_bottom()` (`main.py:277`) |
| `touch_parked` | bool | `self.parked` (`main.py:278`) |
| `description` | string | Selected message (`main.py:257-270`) |
| `install` | object, optional | Added by `set_enabled` (on) and `install_mod` (`main.py:292`, `:302`) |

`install` object (`main.py:132-152`):
```
{ "changed": ["<MOD_ID>/<relative path>", ...], "errors": ["<message>", ...] }
```
Changed paths are relative to the mods folder, using OS separators (`main.py:148`).

## 3. Companion launch contract (Lua to shell)

### Input
The engine calls `HostShell.spawnSelfDetached(args)`. The wrapper handles it only when:
- `args` is a table, and
- `args[1]` is a string starting with `--display-companion=` (`main.lua:43-44`),
- and the host is not Windows (`main.lua:45`).

Other calls go to the original function unchanged (`main.lua:45`, `:62`).

### Command the mod builds
```
sh -c <quote(SCRIPT)> sh <quote(args[1])> <quote(args[2])> ...
```
(`main.lua:47-48`). `HostShell.quote` is applied to the script and each argument.

### Output
One line on stdout, read with `pipe:read("*l")` (`main.lua:53`):

| Line | Meaning | Mod action |
|---|---|---|
| `bottom` | Launcher was started in the background | Log info, return `true` (`main.lua:57-60`) |
| `top` (or anything else, including nil) | Gate failed | Call original spawn (`main.lua:62`) |
| Error in `popen` | `pcall` caught it | Warn with at most 120 chars of the error, call original (`main.lua:50-56`, `:61-62`) |

### Gate and launch inside the shell script (`main.lua:32-39`)
1. `$APPIMAGE` non-empty.
2. `$HOME/.config/kanto-gear-bottom/enabled` exists.
3. `${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/armada-bottom-env` is readable.
4. `/usr/bin/armada-run-bottom` is executable.

If all four pass: `setsid /usr/bin/armada-run-bottom -- "$APPIMAGE" "$@" >/dev/null 2>&1 &`, then echo `bottom`. Otherwise echo `top`.

The `--` separates the launcher's options from the command, so `"$@"` (the engine's own arguments, including `--display-companion=...`) is passed to the AppImage unchanged.

## 4. Companion detection (from `/proc`)

| Field | Read from | Rule | Source |
|---|---|---|---|
| PID | Directory name of `/proc/<pid>` | Digits only | `main.py:101-102` |
| argv | `/proc/<pid>/cmdline`, NUL-split | Empty means skip | `main.py:79-83`, `:103-106` |
| Companion | argv[1:] | Any element starts with `--display-companion=` | `main.py:108` |
| `bottom` | `/proc/<pid>/environ`, key `WAYLAND_DISPLAY` | Equals `gamescope-secondary` | `main.py:109`, `:86-91` |
| Game | `/proc/<pid>/environ`, key `APPIMAGE` | Matches `gen1recomp.*\.AppImage$`, case-insensitive | `main.py:111` |

`read_env` splits on the first `=` per item (`main.py:91`). Items without `=` are dropped.

Result shape (`main.py:113`):
```
{"game": [{"pid": int}], "companions": [{"pid": int, "bottom": bool}]}
```
(`bottom` is present on companion entries only.)

## 5. systemctl invocation
Built in `run_systemctl` (`main.py:178-190`):

| Attempt | argv | Notes |
|---|---|---|
| 1 | `systemctl --machine=armada@.host --user <action> <unit>` | Tried first |
| 2 | `systemctl --user <action> <unit>` | Tried if attempt 1 fails or raises |

Environment: `os.environ` merged with `USER_ENV` (`main.py:179`). Each attempt: `capture_output`, text mode, `timeout=6.0`. Return value `(rc, stdout)` on success, `(rc, stdout+stderr)` on failure, `(1, str(err))` when an exception is raised (`main.py:183-190`).

`unit_active` returns true only when rc is 0 and stripped stdout is `active` (`main.py:193-195`).

## 6. Shortcut file parsing
Pattern (`main.py:54`): `rb"\x01(AppName|Exe|StartDir)\x00([^\x00]*)\x00"`. Each match is a key-value pair. A new row starts when `AppName` is seen and the current row is non-empty (`main.py:56-59`). Keys decode strictly as UTF-8; values decode with `errors="replace"` (`main.py:55`).

Game lookup (`main.py:72-75`): first row whose `Exe`, with surrounding double quotes removed, matches `gen1recomp.*\.AppImage$` (case-insensitive). The folder of that path is the game folder. Files are visited in sorted order (`main.py:67`).

## 7. options.lua check
A text match, not a Lua parse (`main.py:116-122`):
```
\b<MOD_ID>\s*=\s*true\b
```
Any profile that enables the mod matches. The regex is applied with `errors="replace"` (`main.py:119`).

## 8. Mod install protocol
Copy rules (`main.py:132-152`):
- Source: every regular file under `mod/thor_bottom_companion/` (`rglob`, `main.py:143`).
- Destination: `<mods>/thor_bottom_companion/<relative path>`. Parent directories created (`main.py:145`).
- Copy only if bytes differ (`files_differ`, `main.py:125-129`, `:146-147`).
- Each written path and the destination folder get owner `UID:UID` (`main.py:141-142`, `:149`).
- Missing source or missing mods folder returns an `errors` entry and no copy (`main.py:135-138`).

## 9. Decky RPC surface

| Method | Arguments | Returns |
|---|---|---|
| `get_status` | none | status dict |
| `set_enabled` | `enabled: bool` | status dict (+ `install` when enabling) |
| `install_mod` | none | status dict + `install` |

Methods are plain `async def` on `Plugin` (`main.py:282-304`). The frontend calls them with `call(name, ...args)` (`dist/index.js:17-19`).

## 10. Manifest and metadata formats

### `mod/thor_bottom_companion/manifest.json`
| Key | Value | Used by |
|---|---|---|
| `id` | `thor_bottom_companion` | Mod loader; equals `MOD_ID` (`main.py:30`) |
| `version` | `0.1.0` | Mod loader |
| `api` | `2` | Mod loader |
| `entry` | `main.lua` | Mod loader |
| `games` | `gen1`, `gen2`, `gen3` | Mod loader (**unverified**) |
| `game_version` | `>=0.3.20 <2.0.0` | Mod loader (**unverified**) |
| `optional_dependencies` | `["kanto_gear"]` | Mod loader (**unverified**) |
| `permissions` | `["engine_internals"]` | Mod loader (**unverified**) |
| `priority` | `100` | Mod loader (**unverified**) |

Values are as declared (`manifest.json:1-17`). Meanings are **unverified** because the loader is not in the repo.

### `mod/thor_bottom_companion/mod.card`
A Lua table returned by the file: `summary`, `author`, `contact`, `tags`, `differences` (`changed`, `added`, `known`), `credits` (list of `{who, for_}`), `compat` (`engine`, `modApi`). Manager metadata. The repo does not read it (`mod.card:1-19`).

### `plugin.json`
`name`, `author`, `flags: ["root"]`, `api_version: 1` (`plugin.json:1-6`). `flags` gives root (see [04](04-error-handling-constraints.md)).

### `package.json`
Metadata only: `name`, `version` `0.1.0`, `type: "module"`, `license: "MIT"` (`package.json:1-9`). No scripts, dependencies, or entry point.
