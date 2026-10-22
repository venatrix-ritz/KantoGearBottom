# Kanto Gear Bottom Application Spec

What Kanto Gear Bottom is, what it does on the AYN Thor, what it reads and writes, and the rules it follows.
Written from a line-by-line read of the repo on 2026-10-22 (branch `origin/main`, commit `d147e91`). Every statement is anchored to `file:line` or marked **unverified**. Paths are relative to the repo root unless shown otherwise.
The companion [design spec](../design-spec/README.md) explains how each part works.

| # | File | Topic |
|---|---|---|
| 01 | [01-purpose-scope.md](01-purpose-scope.md) | Purpose, scope, what is in and out |
| 02 | [02-users-workflows.md](02-users-workflows.md) | Who uses it and the install and daily workflows |
| 03 | [03-features-interfaces.md](03-features-interfaces.md) | Features, the Decky UI, backend calls, status fields, the Lua spawn contract |
| 04 | [04-configuration-requirements.md](04-configuration-requirements.md) | Paths, flag file, environment overrides, deploy host, requirements |
| 05 | [05-testing-verification.md](05-testing-verification.md) | What the tests cover, what they do not, how they run |
| 06 | [06-limitations-glossary.md](06-limitations-glossary.md) | Known limitations, unused code, open questions, glossary |

**Summary.** Kanto Gear Bottom is a Decky Loader plugin plus a small Gen1Recomp mod. When switched on, the second-screen window that Kanto Gear opens in Gen1Recomp's "Separate Screens" mode is started on the bottom panel of an AYN Thor running Armada OS instead of the top screen (`README.md`, "How it works"; `mod/thor_bottom_companion/main.lua:8-12`). It is off by default and does nothing until the flag file exists (`main.py:29`, `mod/thor_bottom_companion/main.lua:31-36`).
