#!/usr/bin/env bash
# Deploy Kanto Gear Bottom to the AYN Thor over SSH: the Decky plugin, then the helper mod into Gen1Recomp's mods folder.
# Host: arg 1, $THOR_HOST, ./local/thor.env, or ../AynThor/local/thor.env. Keep the address out of tracked files.
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
if [ -z "${THOR_HOST:-}" ]; then
    for f in "${THOR_ENV_FILE:-}" "${ROOT}/local/thor.env" "${ROOT}/../AynThor/local/thor.env"; do
        if [ -n "$f" ] && [ -f "$f" ]; then THOR_HOST="$(sed -n 's/^THOR_HOST=//p' "$f" | head -1)"; break; fi
    done
fi
THOR_HOST="${1:-${THOR_HOST:-}}"
[ -n "$THOR_HOST" ] || { echo "ERROR: no Thor host. Pass it as arg 1, set THOR_HOST, or fill local/thor.env." >&2; exit 2; }

PLUGIN_DIR="/home/armada/homebrew/plugins/kanto-gear-bottom"
STAMP="$(date +%Y%m%d-%H%M%S)"
cd "$ROOT"

echo "==> Pre-flight on the Thor (tests run in /tmp, nothing installed yet)..."
ssh "$THOR_HOST" "rm -rf /tmp/kgb-preflight && mkdir -p /tmp/kgb-preflight/tests /tmp/kgb-preflight/mod"
scp -q main.py "$THOR_HOST:/tmp/kgb-preflight/"
scp -q tests/test_backend.py tests/test_mod.lua "$THOR_HOST:/tmp/kgb-preflight/tests/"
scp -qr mod/thor_bottom_companion "$THOR_HOST:/tmp/kgb-preflight/mod/"
ssh "$THOR_HOST" "cd /tmp/kgb-preflight && python3 tests/test_backend.py && luajit tests/test_mod.lua && luajit -bl mod/thor_bottom_companion/main.lua >/dev/null && echo preflight-ok"

echo "==> Installing the Decky plugin..."
ssh "$THOR_HOST" "sudo mkdir -p '${PLUGIN_DIR}/dist' && if [ -d '${PLUGIN_DIR}' ] && [ -f '${PLUGIN_DIR}/main.py' ]; then sudo cp -a '${PLUGIN_DIR}' '/tmp/kgb-plugin-backup-${STAMP}'; fi"
scp -q plugin.json package.json main.py "$THOR_HOST:/tmp/"
scp -q dist/index.js "$THOR_HOST:/tmp/kgb-index.js"
scp -qr mod "$THOR_HOST:/tmp/kgb-mod"
ssh "$THOR_HOST" "
    sudo mv /tmp/plugin.json /tmp/package.json /tmp/main.py '${PLUGIN_DIR}/'
    sudo mv /tmp/kgb-index.js '${PLUGIN_DIR}/dist/index.js'
    sudo rm -rf '${PLUGIN_DIR}/mod' && sudo mv /tmp/kgb-mod '${PLUGIN_DIR}/mod'
    sudo chown -R root:root '${PLUGIN_DIR}'
    sudo chmod -R 755 '${PLUGIN_DIR}'
    sudo systemctl restart plugin_loader.service
"
echo "==> Done. Open the Quick Access menu (...), find 'Kanto Gear Bottom', and switch it on."
echo "    The plugin copies the helper mod into Gen1Recomp's mods folder when you switch it on."
