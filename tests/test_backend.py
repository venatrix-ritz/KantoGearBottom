"""Backend tests. No device needed: /proc, home and systemctl are all faked."""
import importlib
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_backend(home: Path, proc: Path):
    os.environ["KGB_HOME"] = str(home)
    os.environ["KGB_PROC"] = str(proc)
    sys.path.insert(0, str(ROOT))
    sys.modules.pop("main", None)
    return importlib.import_module("main")


def vdf(*shortcuts):
    out = b"\x00shortcuts\x00"
    for i, (name, exe, start) in enumerate(shortcuts):
        out += b"\x00" + str(i).encode() + b"\x00"
        for key, value in (("AppName", name), ("Exe", exe), ("StartDir", start)):
            out += b"\x01" + key.encode() + b"\x00" + value.encode() + b"\x00"
        out += b"\x08"
    return out + b"\x08\x08"


def fake_proc(proc: Path, pid: int, argv: list[str], env: dict[str, str]):
    d = proc / str(pid)
    d.mkdir(parents=True)
    (d / "cmdline").write_bytes(b"\0".join(a.encode() for a in argv) + b"\0")
    (d / "environ").write_bytes(b"\0".join(f"{k}={v}".encode() for k, v in env.items()) + b"\0")


APP = "/var/home/armada/Games/Gen1Recomp/linux/gen1recomp-0.3.80-linux-arm64.AppImage"


class BackendTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name) / "home"
        self.proc = Path(self.tmp.name) / "proc"
        self.home.mkdir()
        self.proc.mkdir()
        self.m = load_backend(self.home, self.proc)
        self.calls = []
        self.active = {"touch-master.service": True}

        def systemctl(action, unit):
            self.calls.append((action, unit))
            if action == "is-active":
                return (0, "active\n") if self.active.get(unit) else (3, "inactive\n")
            if action == "stop":
                self.active[unit] = False
            if action == "start":
                self.active[unit] = True
            return 0, ""

        self.plugin = self.m.Plugin()
        self.plugin.systemctl = systemctl

    def tearDown(self):
        self.tmp.cleanup()

    def test_parse_shortcuts_and_find_game_dir(self):
        data = vdf(("Artemis", '"/x/artemis"', '"/x/"'), ("G1R Deluxe", f'"{APP}"', '"/y/"'))
        rows = self.m.parse_shortcuts(data)
        self.assertEqual([r["AppName"] for r in rows], ["Artemis", "G1R Deluxe"])
        vdf_path = self.home / ".local/share/Steam/userdata/1/config/shortcuts.vdf"
        vdf_path.parent.mkdir(parents=True)
        vdf_path.write_bytes(data)
        self.assertEqual(self.m.find_game_dir(self.home), Path(APP).parent)

    def test_find_game_dir_default_without_shortcut(self):
        self.assertEqual(self.m.find_game_dir(self.home), self.home / "Games/Gen1Recomp/linux")

    def test_scan_separates_game_and_companions(self):
        fake_proc(self.proc, 10, ["/tmp/.mount_x/usr/bin/gen1recomp"], {"APPIMAGE": APP})
        fake_proc(self.proc, 11, [APP, "--display-companion=49999,abc"], {"WAYLAND_DISPLAY": "gamescope-secondary"})
        fake_proc(self.proc, 12, [APP, "--display-companion=50000,def"], {"WAYLAND_DISPLAY": "gamescope-0"})
        fake_proc(self.proc, 13, ["/usr/bin/python3", "other.py"], {"APPIMAGE": "/x/other.AppImage"})
        (self.proc / "self").mkdir()
        scan = self.m.scan_processes(self.proc)
        self.assertEqual([g["pid"] for g in scan["game"]], [10])
        self.assertEqual({c["pid"]: c["bottom"] for c in scan["companions"]}, {11: True, 12: False})

    def test_mod_enabled_in_options(self):
        opts = self.home / "options.lua"
        self.assertFalse(self.m.mod_enabled_in_options(opts))
        opts.write_text("enabled = { kanto_gear = true, thor_bottom_companion = false }")
        self.assertFalse(self.m.mod_enabled_in_options(opts))
        opts.write_text("enabled = { kanto_gear = true, thor_bottom_companion = true }")
        self.assertTrue(self.m.mod_enabled_in_options(opts))

    def test_install_mod_copies_once(self):
        mods = self.home / "mods"
        mods.mkdir()
        first = self.m.install_mod(self.m.MOD_SRC, mods)
        self.assertEqual(first["errors"], [])
        self.assertIn(f"{self.m.MOD_ID}/main.lua".replace("/", os.sep), first["changed"])
        self.assertTrue((mods / self.m.MOD_ID / "manifest.json").is_file())
        self.assertEqual(self.m.install_mod(self.m.MOD_SRC, mods)["changed"], [])

    def test_install_mod_reports_missing_folder(self):
        result = self.m.install_mod(self.m.MOD_SRC, self.home / "nope")
        self.assertTrue(result["errors"])

    def test_flag(self):
        self.assertFalse(self.m.FLAG.exists())
        self.m.set_flag(True)
        self.assertTrue(self.m.FLAG.exists())
        self.m.set_flag(False)
        self.m.set_flag(False)  # twice is fine
        self.assertFalse(self.m.FLAG.exists())

    def set_scan(self, bottom_companion: bool):
        scan = {"game": [{"pid": 1}], "companions": [{"pid": 2, "bottom": True}] if bottom_companion else []}
        self.plugin.scan = lambda: scan

    def test_tick_parks_and_restores_ratatoskr(self):
        self.m.set_flag(True)
        self.set_scan(True)
        self.plugin.tick()
        self.assertTrue(self.plugin.parked)
        self.assertFalse(self.active["touch-master.service"])
        self.set_scan(False)
        for _ in range(self.m.RELEASE_AFTER_TICKS - 1):
            self.plugin.tick()
            self.assertTrue(self.plugin.parked, "must wait out a companion respawn")
        self.plugin.tick()
        self.assertFalse(self.plugin.parked)
        self.assertTrue(self.active["touch-master.service"])

    def test_companion_respawn_does_not_bounce_ratatoskr(self):
        self.m.set_flag(True)
        self.set_scan(True)
        self.plugin.tick()
        self.set_scan(False)
        self.plugin.tick()
        self.set_scan(True)
        self.plugin.tick()
        self.assertEqual([c for c in self.calls if c[0] in ("stop", "start")], [("stop", "touch-master.service")])

    def test_tick_leaves_ratatoskr_alone_when_off(self):
        self.set_scan(True)  # a bottom companion exists but the switch is off
        self.plugin.tick()
        self.assertFalse(self.plugin.parked)
        self.assertTrue(self.active["touch-master.service"])

    def test_tick_does_not_start_ratatoskr_it_did_not_stop(self):
        self.active["touch-master.service"] = False
        self.m.set_flag(True)
        self.set_scan(True)
        self.plugin.tick()
        self.assertFalse(self.plugin.parked)
        self.assertNotIn(("start", "touch-master.service"), self.calls)

    def test_restore_falls_back_to_stock_bottom_screen(self):
        self.plugin.parked = True
        original = self.plugin.systemctl

        def failing(action, unit):
            if (action, unit) == ("start", "touch-master.service"):
                self.calls.append((action, unit))
                return 1, "nope"
            return original(action, unit)

        self.plugin.systemctl = failing
        self.plugin._restore()
        self.assertIn(("start", "armada-bottom-screen.service"), self.calls)
        self.assertFalse(self.plugin.parked)

    def test_turning_off_restores_immediately(self):
        self.m.set_flag(True)
        self.set_scan(True)
        self.plugin.tick()
        self.assertTrue(self.plugin.parked)
        self.m.set_flag(False)
        self.plugin.tick()
        self.assertFalse(self.plugin.parked)
        self.assertTrue(self.active["touch-master.service"])


if __name__ == "__main__":
    unittest.main()
