-- Thor Bottom Companion
--
-- The engine's "Separate Screens" display (src/render/DesktopScreen.lua) runs the
-- second screen as a second copy of this same app, started with
-- `--display-companion=<port>,<token>` by HostShell.spawnSelfDetached. That copy
-- opens on the DISPLAY it inherits, which in Game Mode is the top screen.
--
-- Armada OS runs a second gamescope for the bottom panel and ships
-- `armada-run-bottom -- <cmd>`, which starts <cmd> as a client of it. This mod
-- wraps spawnSelfDetached so the companion goes through that wrapper. Every other
-- spawn, and every case where the bottom screen is not available or not switched
-- on, goes to the original function untouched.
--
-- The switch is a file, `~/.config/kanto-gear-bottom/enabled`, created by the
-- Kanto Gear Bottom Decky plugin. The decision is made in the shell command so
-- the mod needs no io/os access of its own.

return function(mod)
  local HostShell = require("src.core.HostShell")

  -- A second load of this mod in the same process must not wrap the wrapper.
  if HostShell._thorBottomCompanionOriginal then return end

  local original = HostShell.spawnSelfDetached
  HostShell._thorBottomCompanionOriginal = original

  -- Prints "bottom" after starting the companion on the bottom screen, "top"
  -- when the caller should use the normal path. $APPIMAGE is exported by the
  -- AppImage runtime; without it the original function resolves the executable
  -- itself, so this stays out of the way.
  local SCRIPT = [[
flag="$HOME/.config/kanto-gear-bottom/enabled"
env_file="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/armada-bottom-env"
if [ -n "$APPIMAGE" ] && [ -f "$flag" ] && [ -r "$env_file" ] && [ -x /usr/bin/armada-run-bottom ]; then
  (setsid /usr/bin/armada-run-bottom -- "$APPIMAGE" "$@" >/dev/null 2>&1 &)
  echo bottom
else
  echo top
fi
]]

  HostShell.spawnSelfDetached = function(args)
    local companion = type(args) == "table" and type(args[1]) == "string"
      and args[1]:find("^%-%-display%-companion=") ~= nil
    if not companion or HostShell.isWindows() then return original(args) end

    local command = "sh -c " .. HostShell.quote(SCRIPT) .. " sh"
    for _, value in ipairs(args) do command = command .. " " .. HostShell.quote(value) end

    local ok, answer = pcall(function()
      local pipe = HostShell.popen(command, "r")
      if not pipe then return nil end
      local line = pipe:read("*l")
      HostShell.pclose(pipe)
      return line
    end)
    if ok and answer == "bottom" then
      mod.log:info("second-screen window started on the bottom screen")
      return true
    end
    if not ok then mod.log:warn("bottom screen launch failed: %s", tostring(answer):sub(1, 120)) end
    return original(args)
  end
end
