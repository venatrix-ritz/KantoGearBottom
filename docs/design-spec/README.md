# Kanto Gear Bottom Design Spec

How the plugin and the helper mod are built, how they talk to each other and to the device, how errors are handled, and why the main choices were made.
Companion to the [application spec](../application-spec/README.md). Facts come from reading the repo on 2026-10-22 (`origin/main`, `d147e91`). `file:line` anchors are exact for that commit. Anything not traced in the repo is marked **unverified**.

| # | File | Subsystem / topic |
|---|---|---|
| 01 | [01-architecture-modules.md](01-architecture-modules.md) | Components, modules, processes, threads, state |
| 02 | [02-protocols-data-formats.md](02-protocols-data-formats.md) | Flag file, status dict, companion launch contract, `/proc` and systemctl forms, file formats |
| 03 | [03-data-flow.md](03-data-flow.md) | Mermaid flow, launch sequence, parking state machine |
| 04 | [04-error-handling-constraints.md](04-error-handling-constraints.md) | Failure handling and device, OS, and privilege constraints |
| 05 | [05-design-decisions.md](05-design-decisions.md) | Decisions evidenced in code, with the reason where the code states one |
| 06 | [06-roadmap.md](06-roadmap.md) | Open items visible in the repo; no roadmap file exists |
