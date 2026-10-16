-- Runs the helper mod's wrapper against a stub HostShell. Usage: luajit tests/test_mod.lua  (from the repo root)
local calls
local function fresh(popenAnswer, popenFails)
  calls = { original = {}, popen = {}, logs = {} }
  local HostShell = {}
  function HostShell.spawnSelfDetached(args) calls.original[#calls.original + 1] = args; return "original" end
  function HostShell.isWindows() return false end
  function HostShell.quote(s) return "'" .. tostring(s):gsub("'", "'\\''") .. "'" end
  function HostShell.popen(command)
    calls.popen[#calls.popen + 1] = command
    if popenFails == "error" then error("boom") end
    if popenFails == "nil" then return nil end
    return { read = function() return popenAnswer end }
  end
  function HostShell.pclose() end
  package.loaded["src.core.HostShell"] = HostShell
  local mod = { log = {
    info = function(_, fmt, ...) calls.logs[#calls.logs + 1] = fmt:format(...) end,
    warn = function(_, fmt, ...) calls.logs[#calls.logs + 1] = fmt:format(...) end,
  } }
  assert(loadfile("mod/thor_bottom_companion/main.lua"))()(mod)
  return HostShell
end

local function check(cond, message) if not cond then error("FAIL: " .. message, 2) end end

-- 1. other spawns are untouched
local H = fresh("bottom")
check(H.spawnSelfDetached({ "--restart" }) == "original", "non-companion spawn goes to the original")
check(#calls.popen == 0, "non-companion spawn runs no shell")

-- 2. companion, bottom screen available
H = fresh("bottom")
check(H.spawnSelfDetached({ "--display-companion=49999,abc" }) == true, "bottom launch reports success")
check(#calls.original == 0, "bottom launch does not also spawn on top")
check(calls.popen[1]:find("--display-companion=49999,abc", 1, true), "companion argument is passed through")
check(calls.popen[1]:find("armada-run-bottom", 1, true), "launch goes through armada-run-bottom")

-- 3. companion, switch off or no bottom screen
H = fresh("top")
check(H.spawnSelfDetached({ "--display-companion=1,x" }) == "original", "'top' answer uses the original")

-- 4. shell failures fall back
H = fresh(nil, "error")
check(H.spawnSelfDetached({ "--display-companion=1,x" }) == "original", "popen error uses the original")
H = fresh(nil, "nil")
check(H.spawnSelfDetached({ "--display-companion=1,x" }) == "original", "popen nil uses the original")

-- 5. windows is never touched
H = fresh("bottom")
H.isWindows = function() return true end
check(H.spawnSelfDetached({ "--display-companion=1,x" }) == "original", "windows uses the original")

-- 6. loading twice does not wrap twice
H = fresh("bottom")
local wrapped = H.spawnSelfDetached
assert(loadfile("mod/thor_bottom_companion/main.lua"))()({ log = { info = function() end, warn = function() end } })
check(H.spawnSelfDetached == wrapped, "second load leaves the wrapper alone")

-- 7. quoting survives an apostrophe
H = fresh("bottom")
H.spawnSelfDetached({ "--display-companion=1,a'b" })
check(calls.popen[1]:find("a'\\''b", 1, true), "arguments are shell-quoted")

print("ok")
