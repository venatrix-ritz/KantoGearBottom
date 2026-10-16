const manifest = { "name": "Kanto Gear Bottom" };
const API_VERSION = 2;
const internalAPIConnection = window.__DECKY_SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED_deckyLoaderAPIInit;
if (!internalAPIConnection) {
    throw new Error('[@decky/api]: Failed to connect to loader API.');
}
let api;
try {
    api = internalAPIConnection.connect(API_VERSION, manifest.name);
} catch {
    api = internalAPIConnection.connect(1, manifest.name);
}
const call = api.call;
const toaster = api.toaster;
const definePlugin = (fn) => (...args) => fn(...args);

const getStatus = () => call("get_status");
const setEnabled = (enabled) => call("set_enabled", enabled);
const installMod = () => call("install_mod");

const h = SP_JSX.jsx;
const hs = SP_JSX.jsxs;

function Content() {
    const [status, setStatus] = SP_REACT.useState({ enabled: false, description: "Checking..." });
    const [busy, setBusy] = SP_REACT.useState(false);

    const refresh = SP_REACT.useCallback(async () => {
        try {
            const s = await getStatus();
            if (s) setStatus(s);
        } catch (e) {
            console.error("[kanto-gear-bottom] refresh failed:", e);
        }
    }, []);

    SP_REACT.useEffect(() => {
        refresh();
        const interval = setInterval(refresh, 2000);
        return () => clearInterval(interval);
    }, [refresh]);

    const act = async (fn, okMsg) => {
        setBusy(true);
        try {
            const res = await fn();
            if (res) setStatus(res);
            if (okMsg) toaster.toast({ title: "Kanto Gear Bottom", body: okMsg });
        } catch (e) {
            toaster.toast({ title: "Kanto Gear Bottom error", body: String(e) });
        } finally {
            setBusy(false);
        }
    };

    const rows = [
        h(DFL.PanelSectionRow, {
            children: h(DFL.ToggleField, {
                label: "Kanto Gear on the bottom screen",
                description: status.description,
                checked: !!status.enabled,
                disabled: busy,
                onChange: (value) => act(() => setEnabled(value),
                    value ? "On: the next second-screen window opens on the bottom screen" : "Off: bottom screen left alone")
            })
        }),
        h(DFL.PanelSectionRow, {
            children: h(DFL.Field, {
                label: "Helper mod",
                description: !status.mod_installed ? "Not installed"
                    : status.mod_enabled_in_game ? "Installed and enabled in Gen1Recomp"
                    : "Installed - enable 'Thor Bottom Companion' in the Gen1Recomp mod manager"
            })
        }),
        h(DFL.PanelSectionRow, {
            children: h(DFL.Field, {
                label: "Second-screen window",
                description: status.on_bottom ? "Open on the bottom screen"
                    : status.game_running ? "Game running, no second-screen window" : "Game not running"
            })
        })
    ];
    if (!status.mod_installed || (status.mod_installed && !status.mod_enabled_in_game)) {
        rows.push(h(DFL.PanelSectionRow, {
            children: h(DFL.ButtonItem, {
                layout: "below",
                disabled: busy,
                onClick: () => act(installMod, "Helper mod copied into Gen1Recomp"),
                children: status.mod_installed ? "Reinstall helper mod" : "Install helper mod"
            })
        }));
    }
    return hs(SP_JSX.Fragment, {
        children: [h(DFL.PanelSection, { title: "Second Screen", children: rows })]
    });
}

const index = definePlugin((serverApi) => {
    return {
        name: "Kanto Gear Bottom",
        content: h(Content, {}),
        icon: h("svg", {
            xmlns: "http://www.w3.org/2000/svg",
            viewBox: "0 0 24 24",
            width: "24",
            height: "24",
            fill: "none",
            stroke: "currentColor",
            strokeWidth: "2",
            strokeLinecap: "round",
            strokeLinejoin: "round",
            children: [
                h("rect", { x: "5", y: "2", width: "14", height: "20", rx: "2" }),
                h("line", { x1: "5", y1: "12", x2: "19", y2: "12" }),
                h("circle", { cx: "12", cy: "17", r: "1.5" })
            ]
        }),
        onDismount() {}
    };
});

export { index as default };
