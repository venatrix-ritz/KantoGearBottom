"""Kanto Gear Bottom: Decky plugin backend for the AYN Thor (Armada OS).

Puts Kanto Gear's second-screen window (Gen1Recomp "Separate Screens") on the bottom panel.

How it works, in three parts:
  1. mod/thor_bottom_companion, a small Gen1Recomp mod, starts the companion window through Armada's `armada-run-bottom`
     instead of in the top screen's session. It acts only while the flag file below exists.
  2. This backend owns that flag file and installs the mod next to the game.
  3. Ratatoskr (touch-master.service) holds the bottom touchscreen exclusively, so while a companion window is open on
     the bottom screen the backend parks it and brings it back when the window closes. The same swap the Minecraft HUD
     plugin does.
"""
from __future__ import annotations

import asyncio
import functools
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Callable

# The user whose session owns the screens. KGB_HOME exists so tests can point everything at a temp directory.
HOME = Path(os.environ.get("KGB_HOME", "/var/home/armada"))
UID = int(os.environ.get("KGB_UID", "1000"))
PROC = Path(os.environ.get("KGB_PROC", "/proc"))
PLUGIN_DIR = Path(__file__).resolve().parent

FLAG = HOME / ".config/kanto-gear-bottom/enabled"
MOD_ID = "thor_bottom_companion"
MOD_SRC = PLUGIN_DIR / "mod" / MOD_ID
SHORTCUTS_GLOB = ".local/share/Steam/userdata/*/config/shortcuts.vdf"
DEFAULT_GAME_DIR = HOME / "Games/Gen1Recomp/linux"

COMPANION_ARG = "--display-companion="
# Matches an argument after argv[0] that starts with COMPANION_ARG; every such argument follows a NUL in /proc cmdline.
COMPANION_MARK = b"\0" + COMPANION_ARG.encode()
GAME_APPIMAGE = re.compile(r"gen1recomp.*\.AppImage$", re.IGNORECASE)
BOTTOM_X_DISPLAY = ":2"  # the DISPLAY armada-run-bottom exports; read from the env file at runtime when present
RATATOSKR = "touch-master.service"
STOCK_BOTTOM = "armada-bottom-screen.service"
# A companion that drops and restarts (the engine respawns it with a new port) must not bounce Ratatoskr.
RELEASE_AFTER_TICKS = 4

USER_ENV = {
    "XDG_RUNTIME_DIR": f"/run/user/{UID}",
    "DBUS_SESSION_BUS_ADDRESS": f"unix:path=/run/user/{UID}/bus",
}


# --- pure helpers (unit-tested without a device) ---

def parse_shortcuts(data: bytes) -> list[dict[str, str]]:
    """Name/Exe/StartDir of each non-Steam shortcut in a shortcuts.vdf."""
    rows: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for m in re.finditer(rb"\x01(AppName|Exe|StartDir)\x00([^\x00]*)\x00", data):
        key, value = m.group(1).decode(), m.group(2).decode(errors="replace")
        if key == "AppName" and current:
            rows.append(current)
            current = {}
        current[key] = value
    if current:
        rows.append(current)
    return rows


def find_game_dir(home: Path = HOME) -> Path:
    """Directory that holds the Gen1Recomp AppImage, from the Steam shortcut; the usual location if there is none."""
    for vdf in sorted(home.glob(SHORTCUTS_GLOB)):
        try:
            rows = parse_shortcuts(vdf.read_bytes())
        except OSError:
            continue
        for row in rows:
            exe = row.get("Exe", "").strip('"')
            if GAME_APPIMAGE.search(exe):
                return Path(exe).parent
    return home / "Games/Gen1Recomp/linux"


def env_value(pid_dir: str, key: str) -> str:
    """One variable from /proc/<pid>/environ ("" when unset or unreadable); the last entry wins, as in a dict."""
    try:
        with open(f"{pid_dir}/environ", "rb") as f:
            raw = b"\0" + f.read()
    except OSError:
        return ""
    mark = b"\0" + key.encode() + b"="
    start = raw.rfind(mark)
    if start < 0:
        return ""
    start += len(mark)
    end = raw.find(b"\0", start)
    return raw[start:end if end >= 0 else len(raw)].decode(errors="replace")


def scan_processes(proc: Path = PROC, find_game: bool = True) -> dict:
    """Running Gen1Recomp processes: the game itself and any second-screen companion windows.

    A companion counts as "on the bottom" when it runs against the bottom gamescope (WAYLAND_DISPLAY
    gamescope-secondary, which armada-run-bottom sets), not the top one. Runs every second under FEX (PluginLoader
    is x86-64): one cmdline read per process; environ only for companions, or for all processes when find_game.
    """
    game, companions = [], []
    root = str(proc)
    for name in os.listdir(root):
        if not name.isdigit():
            continue
        pid_dir = f"{root}/{name}"
        try:
            with open(f"{pid_dir}/cmdline", "rb") as f:
                argv = f.read()
        except OSError:
            continue
        if not argv:  # kernel threads and zombies: no cmdline, no environ
            continue
        if COMPANION_MARK in argv:
            bottom = env_value(pid_dir, "WAYLAND_DISPLAY") == "gamescope-secondary"
            companions.append({"pid": int(name), "bottom": bottom})
        elif find_game and GAME_APPIMAGE.search(env_value(pid_dir, "APPIMAGE")):
            game.append({"pid": int(name)})
    return {"game": game, "companions": companions}


def mod_enabled_in_options(options_lua: Path) -> bool:
    """True when options.lua turns the helper mod on in some profile. A text check; the file is the game's own."""
    try:
        text = options_lua.read_text(errors="replace")
    except OSError:
        return False
    return re.search(rf"\b{MOD_ID}\s*=\s*true\b", text) is not None


def files_differ(src: Path, dst: Path) -> bool:
    try:
        return src.read_bytes() != dst.read_bytes()
    except OSError:
        return True


def install_mod(src: Path, mods_dir: Path, uid: int = UID) -> dict:
    """Copy the helper mod into the game's mods folder when missing or different. Returns what changed."""
    changed, errors = [], []
    if not src.is_dir():
        return {"changed": [], "errors": [f"mod source missing: {src}"]}
    if not mods_dir.is_dir():
        return {"changed": [], "errors": [f"game mods folder not found: {mods_dir}"]}
    dest = mods_dir / src.name
    try:
        dest.mkdir(exist_ok=True)
        _chown(dest, uid)
        for file in sorted(p for p in src.rglob("*") if p.is_file()):
            target = dest / file.relative_to(src)
            target.parent.mkdir(parents=True, exist_ok=True)
            if files_differ(file, target):
                shutil.copyfile(file, target)
                changed.append(str(target.relative_to(mods_dir)))
            _chown(target, uid)
    except OSError as err:
        errors.append(str(err))
    return {"changed": changed, "errors": errors}


def _chown(path: Path, uid: int) -> None:
    # The backend runs as root; the game runs as the user and must be able to read what is written here.
    try:
        os.chown(path, uid, uid)
    except (AttributeError, PermissionError, OSError):
        pass


def set_flag(on: bool, uid: int = UID) -> None:
    if on:
        FLAG.parent.mkdir(parents=True, exist_ok=True)
        _chown(FLAG.parent, uid)
        FLAG.touch()
        _chown(FLAG, uid)
    else:
        try:
            FLAG.unlink()
        except FileNotFoundError:
            pass


# --- systemd (user units, from a root process) ---

def run_systemctl(action: str, unit: str) -> tuple[int, str]:
    env = {**os.environ, **USER_ENV}
    last = (1, "")
    for cmd in (["systemctl", "--machine=armada@.host", "--user", action, unit], ["systemctl", "--user", action, unit]):
        try:
            res = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=6.0)
        except Exception as err:  # noqa: BLE001 - a missing binary or a timeout falls through to the next form
            last = (1, str(err))
            continue
        if res.returncode == 0:
            return 0, res.stdout
        last = (res.returncode, res.stdout + res.stderr)
    return last


def unit_active(unit: str, systemctl: Callable[[str, str], tuple[int, str]] = run_systemctl) -> bool:
    rc, out = systemctl("is-active", unit)
    return rc == 0 and out.strip() == "active"


# --- the plugin ---

class Plugin:
    def __init__(self) -> None:
        self.parked = False  # True while Ratatoskr is stopped because a companion window is on the bottom screen
        self.quiet_ticks = 0
        self.last_scan: dict = {"game": [], "companions": []}
        self.systemctl: Callable[[str, str], tuple[int, str]] = run_systemctl
        self.scan: Callable[[], dict] = scan_processes
        # The watcher only needs companions; finding the game means reading every process's environ.
        self.scan_companions: Callable[[], dict] = functools.partial(scan_processes, find_game=False)

    # Decky calls these two.
    async def _main(self) -> None:
        asyncio.create_task(self._watch())

    async def _unload(self) -> None:
        await asyncio.to_thread(self._restore)

    async def _watch(self) -> None:
        while True:
            try:
                await asyncio.to_thread(self.tick)
            except Exception:  # noqa: BLE001 - the watcher must outlive any one bad tick
                pass
            await asyncio.sleep(1.0)

    def on_bottom(self) -> bool:
        return any(c.get("bottom") for c in self.last_scan["companions"])

    def tick(self) -> None:
        """Park Ratatoskr while a companion window is on the bottom screen; bring it back after it has been gone a while."""
        if not FLAG.exists():
            # Switched off: the mod sends no companion to the bottom, so there is nothing to scan for.
            self._restore()
            return
        self.last_scan = self.scan_companions()
        if self.on_bottom():
            self.quiet_ticks = 0
            if not self.parked:
                if unit_active(RATATOSKR, self.systemctl):
                    self.systemctl("stop", RATATOSKR)
                    self.parked = True
            return
        if self.parked:
            self.quiet_ticks += 1
            if self.quiet_ticks >= RELEASE_AFTER_TICKS:
                self._restore()

    def _restore(self) -> None:
        if not self.parked:
            return
        rc, _ = self.systemctl("start", RATATOSKR)
        if rc != 0:
            self.systemctl("start", STOCK_BOTTOM)
        self.parked = False
        self.quiet_ticks = 0

    def _status(self) -> dict:
        game_dir = find_game_dir()
        scan = self.scan()
        self.last_scan = scan
        installed = (game_dir / "mods" / MOD_ID / "main.lua").is_file()
        in_options = mod_enabled_in_options(game_dir / "options.lua")
        enabled = FLAG.exists()
        if not game_dir.is_dir():
            note = "Gen1Recomp was not found (looked for the Steam shortcut's AppImage)"
        elif not installed:
            note = "Helper mod is not installed yet"
        elif not in_options:
            note = "Enable 'Thor Bottom Companion' in the Gen1Recomp mod manager, then set Kanto Gear to Separate Screens"
        elif not enabled:
            note = "Off: the second-screen window opens on the top screen"
        elif self.on_bottom():
            note = "Kanto Gear is on the bottom screen"
        elif scan["game"]:
            note = "On, but no second-screen window is open (set Kanto Gear's Display Mode to Separate Screens)"
        else:
            note = "On: Kanto Gear will open on the bottom screen when the game starts"
        return {
            "enabled": enabled,
            "mod_installed": installed,
            "mod_enabled_in_game": in_options,
            "game_dir": str(game_dir),
            "game_running": bool(scan["game"]),
            "on_bottom": self.on_bottom(),
            "touch_parked": self.parked,
            "description": note,
        }

    async def get_status(self) -> dict:
        return await asyncio.to_thread(self._status)

    async def set_enabled(self, enabled: bool) -> dict:
        def apply() -> dict:
            if enabled:
                game_dir = find_game_dir()
                result = install_mod(MOD_SRC, game_dir / "mods")
                set_flag(True)
                status = self._status()
                status["install"] = result
                return status
            set_flag(False)
            self._restore()
            return self._status()
        return await asyncio.to_thread(apply)

    async def install_mod(self) -> dict:
        def apply() -> dict:
            result = install_mod(MOD_SRC, find_game_dir() / "mods")
            status = self._status()
            status["install"] = result
            return status
        return await asyncio.to_thread(apply)
