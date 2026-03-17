#include "gui.h"
#include <windowsx.h>
#include <algorithm>

#pragma comment(lib, "comctl32.lib")
#pragma comment(linker, "\"/manifestdependency:type='win32' name='Microsoft.Windows.Common-Controls' version='6.0.0.0' processorArchitecture='*' publicKeyToken='6595b64144ccf1df' language='*'\"")

static AppWindow* g_app = nullptr;

// --- Setting field definitions ---
struct FieldDef {
    const wchar_t* key;
    const wchar_t* label;
    bool isCombo;
    std::vector<std::wstring> options;
    const wchar_t* suffix;
};

static std::vector<FieldDef> RSS_FIELDS = {
    {L"Enabled",                L"Status:",               true, {L"True",L"False"}, nullptr},
    {L"NumberOfReceiveQueues",  L"NumberOfReceiveQueues:", false, {}, nullptr},
    {L"Profile",                L"Profile:",              true, {L"NUMAStatic",L"NUMAScalingStatic",L"ConservativeScaling",L"ClosestProcessor"}, nullptr},
    {L"BaseProcessorNumber",    L"BaseProcessor:",        false, {}, nullptr},
    {L"MaxProcessorNumber",     L"MaxProcessor:",         false, {}, nullptr},
    {L"MaxProcessors",          L"MaxProcessors:",        false, {}, nullptr},
};

static std::vector<FieldDef> GLOBAL_FIELDS = {
    {L"ReceiveSideScaling",              L"ReceiveSideScaling:",            true, {L"Enabled",L"Disabled"}, nullptr},
    {L"ReceiveSegmentCoalescing",        L"ReceiveSegmentCoalescing:",      true, {L"Enabled",L"Disabled"}, nullptr},
    {L"Chimney",                         L"Chimney:",                       true, {L"Enabled",L"Disabled",L"Automatic"}, nullptr},
    {L"TaskOffload",                     L"TaskOffload:",                   true, {L"Enabled",L"Disabled"}, nullptr},
    {L"NetworkDirect",                   L"NetworkDirect:",                 true, {L"Enabled",L"Disabled"}, nullptr},
    {L"NetworkDirectAcrossIPSubnets",    L"NetworkDirectAcrossIPSubnets:",  true, {L"Allowed",L"Blocked"}, nullptr},
    {L"PacketCoalescingFilter",          L"PacketCoalescingFilter:",        true, {L"Enabled",L"Disabled"}, nullptr},
};

static std::vector<FieldDef> IFACE_FIELDS = {
    {L"AdvertiseDefaultRoute",   L"AdvertiseDefaultRoute:",   true, {L"Enabled",L"Disabled"}, nullptr},
    {L"Advertising",             L"Advertising:",             true, {L"Enabled",L"Disabled"}, nullptr},
    {L"AutomaticMetric",         L"AutomaticMetric:",         true, {L"Enabled",L"Disabled"}, nullptr},
    {L"ClampMss",                L"ClampMss:",                true, {L"Enabled",L"Disabled"}, nullptr},
    {L"DirectedMacWolPattern",   L"DirectedMacWolPattern:",   true, {L"Enabled",L"Disabled"}, nullptr},
    {L"EcnMarking",              L"EcnMarking:",              true, {L"Disabled",L"UseEct1",L"UseEct0",L"AppDecide"}, nullptr},
    {L"ForceArpNdWolPattern",    L"ForceArpNdWolPattern:",    true, {L"Enabled",L"Disabled"}, nullptr},
    {L"Forwarding",              L"Forwarding:",              true, {L"Enabled",L"Disabled"}, nullptr},
    {L"IgnoreDefaultRoutes",     L"IgnoreDefaultRoutes:",     true, {L"Enabled",L"Disabled"}, nullptr},
    {L"ManagedAddressConfiguration", L"ManagedAddressConfiguration:", true, {L"Enabled",L"Disabled"}, nullptr},
    {L"NeighborDiscoverySupported",  L"NeighborDiscoverySupported:",  true, {L"Yes",L"No"}, nullptr},
    {L"NeighborUnreachabilityDetection", L"NeighborUnreachDetection:", true, {L"Enabled",L"Disabled"}, nullptr},
    {L"OtherStatefulConfiguration",  L"OtherStatefulConfiguration:",  true, {L"Enabled",L"Disabled"}, nullptr},
    {L"RouterDiscovery",         L"RouterDiscovery:",         true, {L"Enabled",L"Disabled",L"ControlledByDHCP"}, nullptr},
    {L"Store",                   L"Store:",                   true, {L"ActiveStore",L"PersistentStore"}, nullptr},
    {L"WeakHostReceive",         L"WeakHostReceive:",         true, {L"Enabled",L"Disabled"}, nullptr},
    {L"WeakHostSend",            L"WeakHostSend:",            true, {L"Enabled",L"Disabled"}, nullptr},
    {L"CurrentHopLimit",         L"CurrentHopLimit:",         false, {}, nullptr},
    {L"BaseReachableTime",       L"BaseReachableTime:",       false, {}, L"ms"},
    {L"RetransmitTime",          L"RetransmitTime:",          false, {}, L"ms"},
    {L"ReachableTime",           L"ReachableTime:",           false, {}, L"ms"},
    {L"DadRetransmitTime",       L"DadRetransmitTime:",       false, {}, nullptr},
    {L"DadTransmits",            L"DadTransmits:",            false, {}, nullptr},
    {L"NlMtu",                   L"NlMtu:",                   false, {}, L"bytes"},
};

static const wchar_t* ADV_KEYS[] = {
    L"*FlowControl", L"*IPChecksumOffloadIPv4",
    L"*TCPChecksumOffloadIPv4", L"*TCPChecksumOffloadIPv6",
    L"*UDPChecksumOffloadIPv4", L"*UDPChecksumOffloadIPv6",
    L"*LsoV1IPv4", L"*LsoV2IPv4", L"*LsoV2IPv6",
    L"*PMARPOffload", L"*PMNSOffload", L"*PriorityVLANTag",
    L"*ReceiveBuffers", L"*TransmitBuffers",
    L"*InterruptModeration", L"ITR", L"TxIntDelay",
    L"PacketDirect", L"Coalesce", L"CoalesceBufferSize", L"UdpTxScaling",
};

static const wchar_t* TWEAK_KEYS[] = {
    L"DefaultReceiveWindow", L"DefaultSendWindow", L"BufferMultiplier", L"BufferAlignment",
    L"DoNotHoldNicBuffers", L"SmallBufferSize", L"MediumBufferSize", L"LargeBufferSize", L"HugeBufferSize",
    L"SmallBufferListDepth", L"MediumBufferListDepth", L"LargeBufferListDepth",
    L"DisableAddressSharing", L"DisableChainedReceive", L"DisableDirectAcceptEx", L"DisableRawSecurity",
    L"DynamicSendBufferDisable", L"FastSendDatagramThreshold", L"FastCopyReceiveThreshold",
    L"IgnorePushBitOnReceives", L"IgnoreOrderlyRelease", L"TransmitWorker", L"PriorityBoost",
};

static const wchar_t* POWER_KEYS[] = {
    L"*PMAPowerManagement", L"DynamicPowerGating", L"ConnectedPowerGating",
    L"AutoPowerSaveModeEnabled", L"NicAutoPowerSaver", L"DelayedPowerUpEn",
    L"ReduceSpeedOnPowerDown", L"*WakeOnMagicPacket", L"*WakeOnPattern",
    L"WakeOnLink", L"*EEE", L"EnableGreenEthernet",
};

// Human-readable labels for adv keys
static std::map<std::wstring, std::wstring> ADV_LABELS = {
    {L"*FlowControl", L"FlowControl:"},
    {L"*IPChecksumOffloadIPv4", L"IPChecksumOffloadIPv4:"},
    {L"*TCPChecksumOffloadIPv4", L"TCPChecksumOffloadIPv4:"},
    {L"*TCPChecksumOffloadIPv6", L"TCPChecksumOffloadIPv6:"},
    {L"*UDPChecksumOffloadIPv4", L"UDPChecksumOffloadIPv4:"},
    {L"*UDPChecksumOffloadIPv6", L"UDPChecksumOffloadIPv6:"},
    {L"*LsoV1IPv4", L"LsoV1IPv4:"},
    {L"*LsoV2IPv4", L"LsoV2IPv4:"},
    {L"*LsoV2IPv6", L"LsoV2IPv6:"},
    {L"*PMARPOffload", L"PMARPOffload:"},
    {L"*PMNSOffload", L"PMNSOffload:"},
    {L"*PriorityVLANTag", L"PriorityVLANTag:"},
    {L"*ReceiveBuffers", L"ReceiveBuffers:"},
    {L"*TransmitBuffers", L"TransmitBuffers:"},
    {L"*InterruptModeration", L"InterruptModeration:"},
    {L"ITR", L"InterruptModerationRate:"},
    {L"TxIntDelay", L"TxIntDelay:"},
    {L"PacketDirect", L"PacketDirect:"},
    {L"Coalesce", L"Coalesce:"},
    {L"CoalesceBufferSize", L"CoalesceBufferSize:"},
    {L"UdpTxScaling", L"UdpTxScaling:"},
    {L"*PMAPowerManagement", L"(APM) sleep states:"},
    {L"DynamicPowerGating", L"DynamicPowerGating:"},
    {L"ConnectedPowerGating", L"ConnectedPowerGating:"},
    {L"AutoPowerSaveModeEnabled", L"AutoPowerSaveMode:"},
    {L"NicAutoPowerSaver", L"NicAutoPowerSaver:"},
    {L"DelayedPowerUpEn", L"DelayedPowerUp:"},
    {L"ReduceSpeedOnPowerDown", L"ReduceSpeedOnPowerDown:"},
    {L"*WakeOnMagicPacket", L"WakeOnMagicPacket:"},
    {L"*WakeOnPattern", L"WakeOnPattern:"},
    {L"WakeOnLink", L"WakeOnLink:"},
    {L"*EEE", L"Energy Efficient Ethernet:"},
    {L"EnableGreenEthernet", L"GreenEthernet:"},
};

// =====================================================================
// Stored control handles per section for reading values
// =====================================================================
struct SectionCtrl {
    std::wstring key;
    HWND hCtrl;
    bool isCombo;
};
static std::vector<SectionCtrl> g_rssCtrl, g_globalCtrl, g_ifaceCtrl;
static std::vector<SectionCtrl> g_advCtrl, g_tweakCtrl, g_powerCtrl;

// Scrollable panel struct
struct ScrollPanel {
    HWND hScroll;
    HWND hContent;
    int totalH;
};
static std::map<std::wstring, ScrollPanel> g_panels;

// =====================================================================
// Helper: create a row (label + control) inside a parent, return y offset
// =====================================================================
static int ROW_H = 22;
static int LABEL_W = 180;
static int CTRL_W = 140;

static HWND CreateRow(HWND parent, int x, int& y, const wchar_t* label,
                       const wchar_t* value, bool isCombo,
                       const std::vector<std::wstring>& options,
                       int id, HFONT hFont, HFONT hFontMono,
                       std::vector<SectionCtrl>& out, const std::wstring& key,
                       int panelW)
{
    int lw = panelW / 2 - 4;
    int cw = panelW / 2 - 8;
    int cx = lw + 4;

    // Label
    HWND hLbl = CreateWindowExW(0, L"STATIC", label,
        WS_CHILD | WS_VISIBLE | SS_LEFT | SS_NOPREFIX,
        x + 6, y + 2, lw - 8, ROW_H - 4, parent, nullptr, nullptr, nullptr);
    SendMessageW(hLbl, WM_SETFONT, (WPARAM)hFont, TRUE);

    HWND hCtrl;
    if (isCombo) {
        hCtrl = CreateWindowExW(0, L"COMBOBOX", L"",
            WS_CHILD | WS_VISIBLE | CBS_DROPDOWNLIST | WS_VSCROLL,
            cx, y, cw, 200, parent, (HMENU)(INT_PTR)id, nullptr, nullptr);
        SendMessageW(hCtrl, WM_SETFONT, (WPARAM)hFontMono, TRUE);
        for (auto& o : options) {
            int idx = (int)SendMessageW(hCtrl, CB_ADDSTRING, 0, (LPARAM)o.c_str());
            if (o == value) SendMessageW(hCtrl, CB_SETCURSEL, idx, 0);
        }
        // If current value not in options, add it
        if (SendMessageW(hCtrl, CB_GETCURSEL, 0, 0) == CB_ERR && value && value[0]) {
            int idx = (int)SendMessageW(hCtrl, CB_ADDSTRING, 0, (LPARAM)value);
            SendMessageW(hCtrl, CB_SETCURSEL, idx, 0);
        }
    } else {
        hCtrl = CreateWindowExW(WS_EX_CLIENTEDGE, L"EDIT", value ? value : L"",
            WS_CHILD | WS_VISIBLE | ES_AUTOHSCROLL | ES_RIGHT,
            cx, y + 1, cw, ROW_H - 4, parent, (HMENU)(INT_PTR)id, nullptr, nullptr);
        SendMessageW(hCtrl, WM_SETFONT, (WPARAM)hFontMono, TRUE);
    }

    out.push_back({key, hCtrl, isCombo});
    y += ROW_H;
    return hCtrl;
}

// =====================================================================
// Collect values from controls
// =====================================================================
static std::map<std::wstring, std::wstring> CollectValues(const std::vector<SectionCtrl>& ctrls) {
    std::map<std::wstring, std::wstring> m;
    wchar_t buf[512];
    for (auto& c : ctrls) {
        if (c.isCombo) {
            int idx = (int)SendMessageW(c.hCtrl, CB_GETCURSEL, 0, 0);
            if (idx != CB_ERR) {
                SendMessageW(c.hCtrl, CB_GETLBTEXT, idx, (LPARAM)buf);
                m[c.key] = buf;
            }
        } else {
            GetWindowTextW(c.hCtrl, buf, 512);
            m[c.key] = buf;
        }
    }
    return m;
}

// =====================================================================
// Section builder with scrolling
// =====================================================================
static HWND MakeHeader(HWND parent, int x, int y, int w, const wchar_t* title, HFONT hBold) {
    HWND h = CreateWindowExW(0, L"STATIC", title,
        WS_CHILD | WS_VISIBLE | SS_LEFT | SS_NOPREFIX,
        x, y, w, 20, parent, nullptr, nullptr, nullptr);
    SendMessageW(h, WM_SETFONT, (WPARAM)hBold, TRUE);
    return h;
}

static HWND MakeButton(HWND parent, int x, int y, int w, int h, const wchar_t* text, int id, HFONT hFont) {
    HWND btn = CreateWindowExW(0, L"BUTTON", text,
        WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON,
        x, y, w, h, parent, (HMENU)(INT_PTR)id, nullptr, nullptr);
    SendMessageW(btn, WM_SETFONT, (WPARAM)hFont, TRUE);
    return btn;
}

// =====================================================================
// AppWindow
// =====================================================================
bool AppWindow::Create(HINSTANCE hInst) {
    // Fonts
    hFont = CreateFontW(-11, 0, 0, 0, FW_NORMAL, 0, 0, 0, DEFAULT_CHARSET,
        0, 0, CLEARTYPE_QUALITY, 0, L"Segoe UI");
    hFontBold = CreateFontW(-11, 0, 0, 0, FW_BOLD, 0, 0, 0, DEFAULT_CHARSET,
        0, 0, CLEARTYPE_QUALITY, 0, L"Segoe UI");
    hFontMono = CreateFontW(-11, 0, 0, 0, FW_NORMAL, 0, 0, 0, DEFAULT_CHARSET,
        0, 0, CLEARTYPE_QUALITY, 0, L"Consolas");
    hFontSmall = CreateFontW(-10, 0, 0, 0, FW_NORMAL, 0, 0, 0, DEFAULT_CHARSET,
        0, 0, CLEARTYPE_QUALITY, 0, L"Segoe UI");

    // Brushes
    hBrBg = CreateSolidBrush(CLR_BG);
    hBrPanel = CreateSolidBrush(CLR_PANEL);
    hBrHeader = CreateSolidBrush(CLR_HEADER);
    hBrInput = CreateSolidBrush(CLR_INPUT_BG);
    hBrBorder = CreateSolidBrush(CLR_BORDER);

    WNDCLASSEXW wc{sizeof(wc)};
    wc.lpfnWndProc = WndProc;
    wc.hInstance = hInst;
    wc.lpszClassName = L"NATweaker";
    wc.hbrBackground = hBrBg;
    wc.hCursor = LoadCursor(nullptr, IDC_ARROW);
    wc.style = CS_HREDRAW | CS_VREDRAW;
    RegisterClassExW(&wc);

    hWnd = CreateWindowExW(0, L"NATweaker", L"Network Adapter - Tweaker",
        WS_OVERLAPPEDWINDOW | WS_CLIPCHILDREN,
        CW_USEDEFAULT, CW_USEDEFAULT, 1420, 900,
        nullptr, nullptr, hInst, this);

    if (!hWnd) return false;
    ShowWindow(hWnd, SW_SHOW);
    UpdateWindow(hWnd);
    return true;
}

void AppWindow::LoadAdapters() {
    adapterList = GetAdapters();
    SendMessageW(hAdapterCombo, CB_RESETCONTENT, 0, 0);
    for (auto& a : adapterList) {
        std::wstring text = a.description.empty() ? a.name : a.description;
        if (a.status != L"Up") text += L" (" + a.status + L")";
        SendMessageW(hAdapterCombo, CB_ADDSTRING, 0, (LPARAM)text.c_str());
    }
    // Select first Up adapter
    for (int i = 0; i < (int)adapterList.size(); i++) {
        if (adapterList[i].status == L"Up") {
            SendMessageW(hAdapterCombo, CB_SETCURSEL, i, 0);
            SelectAdapter(adapterList[i].name);
            return;
        }
    }
    if (!adapterList.empty()) {
        SendMessageW(hAdapterCombo, CB_SETCURSEL, 0, 0);
        SelectAdapter(adapterList[0].name);
    }
}

void AppWindow::SelectAdapter(const std::wstring& name) {
    currentAdapter = name;
    if (name.empty()) return;

    // Update registry path + NDIS
    auto regPath = GetAdapterRegistryPath(name);
    SetWindowTextW(hRegLabel, (L"Registry: " + regPath).c_str());

    auto it = std::find_if(adapterList.begin(), adapterList.end(),
        [&](auto& a){ return a.name == name; });
    if (it != adapterList.end()) {
        SetWindowTextW(hNdisLabel, (L"NDIS:  " + it->ndisVersion).c_str());
    }

    RefreshAll();
}

void AppWindow::RefreshAll() {
    if (currentAdapter.empty()) return;

    rssData = GetRssSettings(currentAdapter);
    globalData = GetGlobalSettings();
    ifaceData = GetInterfaceSettings(currentAdapter, ipv4Selected ? L"IPv4" : L"IPv6");
    advProps = GetAdvancedProperties(currentAdapter);
    tweakData = GetAfdTweaks();

    // Rebuild the panels with fresh data
    BuildPanels();
}

// =====================================================================
// Build all panels (destroy old controls, recreate)
// =====================================================================
void AppWindow::BuildPanels() {
    RECT rc;
    GetClientRect(hWnd, &rc);
    int clientW = rc.right - rc.left;
    int clientH = rc.bottom - rc.top;
    int topH = 56; // top bar height
    int bodyH = clientH - topH;

    // We have 4 columns
    int colW = clientW / 4;
    int col0 = 0, col1 = colW, col2 = colW * 2, col3 = colW * 3;

    // Destroy existing section children (below top bar)
    // Simple approach: destroy all children that aren't top bar controls
    // We'll use a container panel per column that we recreate

    // Actually let's use a simpler approach: use static-id panels
    // For now, just destroy everything below topH and recreate
    HWND child = GetWindow(hWnd, GW_CHILD);
    std::vector<HWND> toDestroy;
    while (child) {
        RECT cr;
        GetWindowRect(child, &cr);
        POINT pt = {cr.left, cr.top};
        ScreenToClient(hWnd, &pt);
        int id = GetDlgCtrlID(child);
        // Keep top-bar controls (ID 1001-1005 and the labels)
        if (pt.y >= topH && id != ID_ADAPTER_COMBO && id != ID_BTN_OPEN &&
            id != ID_BTN_APPLY_ALL && id != ID_BTN_RESTART && id != ID_BTN_OPACITY) {
            toDestroy.push_back(child);
        }
        child = GetWindow(child, GW_HWNDNEXT);
    }
    for (auto h : toDestroy) DestroyWindow(h);

    g_rssCtrl.clear();
    g_globalCtrl.clear();
    g_ifaceCtrl.clear();
    g_advCtrl.clear();
    g_tweakCtrl.clear();
    g_powerCtrl.clear();

    int idCounter = 10000;
    auto nextId = [&]() { return idCounter++; };

    // ==================== COLUMN 0: RSS ====================
    int y = topH + 2;
    MakeHeader(hWnd, col0 + 4, y, colW - 8, L"RSS Settings", hFontBold);
    y += 22;

    for (auto& f : RSS_FIELDS) {
        std::wstring val = rssData.count(f.key) ? rssData[f.key] : L"";
        CreateRow(hWnd, col0, y, f.label, val.c_str(), f.isCombo, f.options,
                  nextId(), hFontSmall, hFontMono, g_rssCtrl, f.key, colW);
    }
    MakeButton(hWnd, col0 + 6, y + 4, 55, 20, L"Apply", ID_BTN_RSS_APPLY, hFontSmall);
    MakeButton(hWnd, col0 + 66, y + 4, 100, 20, L"Unlock RSSQueues", ID_BTN_RSS_UNLOCK, hFontSmall);
    y += 30;

    // RSS Global sub-section
    MakeHeader(hWnd, col0 + 4, y, colW - 8, L"RSS Global", hFontBold);
    y += 20;
    // These are simple static info, editable
    {
        std::vector<std::wstring> dummy;
        CreateRow(hWnd, col0, y, L"TCP/IP_RssBaseCpu:", L"0", false, dummy, nextId(), hFontSmall, hFontMono, g_rssCtrl, L"TCP_RssBaseCpu", colW);
        CreateRow(hWnd, col0, y, L"NDIS_RssBaseCpu:", L"0", false, dummy, nextId(), hFontSmall, hFontMono, g_rssCtrl, L"NDIS_RssBaseCpu", colW);
    }

    // Interrupt Settings sub-section
    y += 6;
    MakeHeader(hWnd, col0 + 4, y, colW - 8, L"Interrupt Settings", hFontBold);
    y += 20;
    {
        // MSI Mode from adv props
        auto findAdv = [&](const std::wstring& kw) -> AdvProperty* {
            for (auto& p : advProps) if (p.keyword == kw) return &p;
            return nullptr;
        };
        // MSISupported
        auto msi = findAdv(L"*InterruptModeration");
        std::wstring msiVal = msi ? msi->displayValue : L"";
        std::vector<std::wstring> msiOpts = msi ? msi->validDisplay : std::vector<std::wstring>{L"Enabled", L"Disabled"};
        CreateRow(hWnd, col0, y, L"MSI Mode:", msiVal.c_str(), true, msiOpts,
                  nextId(), hFontSmall, hFontMono, g_rssCtrl, L"MSIMode", colW);
    }

    // ==================== COLUMN 1: Global + Interface ====================
    y = topH + 2;
    MakeHeader(hWnd, col1 + 4, y, colW - 8, L"Global Settings", hFontBold);
    y += 22;

    for (auto& f : GLOBAL_FIELDS) {
        std::wstring val = globalData.count(f.key) ? globalData[f.key] : L"";
        CreateRow(hWnd, col1, y, f.label, val.c_str(), f.isCombo, f.options,
                  nextId(), hFontSmall, hFontMono, g_globalCtrl, f.key, colW);
    }
    MakeButton(hWnd, col1 + 6, y + 4, 55, 20, L"Apply", ID_BTN_GLOBAL_APPLY, hFontSmall);

    // IPv4/IPv6 checkboxes
    {
        HWND chk4 = CreateWindowExW(0, L"BUTTON", L"IPv4",
            WS_CHILD | WS_VISIBLE | BS_AUTOCHECKBOX,
            col1 + 70, y + 4, 50, 18, hWnd, (HMENU)ID_CHK_IPV4, nullptr, nullptr);
        SendMessageW(chk4, WM_SETFONT, (WPARAM)hFontSmall, TRUE);
        SendMessageW(chk4, BM_SETCHECK, ipv4Selected ? BST_CHECKED : BST_UNCHECKED, 0);

        HWND chk6 = CreateWindowExW(0, L"BUTTON", L"IPv6",
            WS_CHILD | WS_VISIBLE | BS_AUTOCHECKBOX,
            col1 + 124, y + 4, 50, 18, hWnd, (HMENU)ID_CHK_IPV6, nullptr, nullptr);
        SendMessageW(chk6, WM_SETFONT, (WPARAM)hFontSmall, TRUE);
        SendMessageW(chk6, BM_SETCHECK, ipv4Selected ? BST_UNCHECKED : BST_CHECKED, 0);
    }
    y += 30;

    // Interface Settings
    MakeHeader(hWnd, col1 + 4, y, colW - 8, L"Interface Settings", hFontBold);
    y += 22;

    for (auto& f : IFACE_FIELDS) {
        std::wstring val = ifaceData.count(f.key) ? ifaceData[f.key] : L"";
        CreateRow(hWnd, col1, y, f.label, val.c_str(), f.isCombo, f.options,
                  nextId(), hFontSmall, hFontMono, g_ifaceCtrl, f.key, colW);
    }
    MakeButton(hWnd, col1 + 6, y + 4, 55, 20, L"Apply", ID_BTN_IFACE_APPLY, hFontSmall);

    // ==================== COLUMN 2: Adv Adapter + Power ====================
    y = topH + 2;
    MakeHeader(hWnd, col2 + 4, y, colW - 8, L"Adv. Adapter", hFontBold);
    y += 22;

    auto findAdv = [&](const std::wstring& kw) -> AdvProperty* {
        for (auto& p : advProps) if (p.keyword == kw) return &p;
        return nullptr;
    };

    for (auto& kw : ADV_KEYS) {
        auto* prop = findAdv(kw);
        std::wstring label = ADV_LABELS.count(kw) ? ADV_LABELS[kw] : std::wstring(kw) + L":";
        std::wstring val = prop ? prop->displayValue : L"";
        bool combo = prop && !prop->validDisplay.empty();
        auto opts = prop ? prop->validDisplay : std::vector<std::wstring>{};
        CreateRow(hWnd, col2, y, label.c_str(), val.c_str(), combo, opts,
                  nextId(), hFontSmall, hFontMono, g_advCtrl, kw, colW);
    }
    MakeButton(hWnd, col2 + 6, y + 4, 55, 20, L"Apply", ID_BTN_ADV_APPLY, hFontSmall);
    y += 30;

    // PowerSaving
    MakeHeader(hWnd, col2 + 4, y, colW - 8, L"PowerSaving Settings", hFontBold);
    y += 22;

    for (auto& kw : POWER_KEYS) {
        auto* prop = findAdv(kw);
        std::wstring label = ADV_LABELS.count(kw) ? ADV_LABELS[kw] : std::wstring(kw) + L":";
        std::wstring val = prop ? prop->displayValue : L"";
        bool combo = prop && !prop->validDisplay.empty();
        auto opts = prop ? prop->validDisplay : std::vector<std::wstring>{};
        CreateRow(hWnd, col2, y, label.c_str(), val.c_str(), combo, opts,
                  nextId(), hFontSmall, hFontMono, g_powerCtrl, kw, colW);
    }
    MakeButton(hWnd, col2 + 6, y + 4, 55, 20, L"Apply", ID_BTN_POWER_APPLY, hFontSmall);

    // ==================== COLUMN 3: Tweaks ====================
    y = topH + 2;
    MakeHeader(hWnd, col3 + 4, y, colW - 8, L"Tweaks", hFontBold);
    y += 22;

    for (auto& kw : TWEAK_KEYS) {
        std::wstring val = tweakData.count(kw) ? tweakData[kw] : L"";
        std::wstring label = std::wstring(kw) + L":";
        std::vector<std::wstring> dummy;
        CreateRow(hWnd, col3, y, label.c_str(), val.c_str(), false, dummy,
                  nextId(), hFontSmall, hFontMono, g_tweakCtrl, kw, colW);
    }
    MakeButton(hWnd, col3 + 6, y + 4, 55, 20, L"Apply", ID_BTN_TWEAK_APPLY, hFontSmall);

    InvalidateRect(hWnd, nullptr, TRUE);
}

// =====================================================================
// Apply handlers
// =====================================================================
void AppWindow::ApplyRss() {
    auto vals = CollectValues(g_rssCtrl);
    // Remove non-RSS keys
    vals.erase(L"TCP_RssBaseCpu");
    vals.erase(L"NDIS_RssBaseCpu");
    vals.erase(L"MSIMode");
    SetRss(currentAdapter, vals);
    ShowStatus(L"RSS applied!");
}

void AppWindow::ApplyGlobal() {
    auto vals = CollectValues(g_globalCtrl);
    SetGlobal(vals);
    ShowStatus(L"Global applied!");
}

void AppWindow::ApplyInterface() {
    auto vals = CollectValues(g_ifaceCtrl);
    SetInterface(currentAdapter, ipv4Selected ? L"IPv4" : L"IPv6", vals);
    ShowStatus(L"Interface applied!");
}

void AppWindow::ApplyAdv() {
    auto vals = CollectValues(g_advCtrl);
    // Find registry value for each
    for (auto& [kw, displayVal] : vals) {
        if (displayVal.empty()) continue;
        // Find the registry value matching this display value
        std::wstring regVal = displayVal;
        for (auto& p : advProps) {
            if (p.keyword == kw) {
                for (size_t i = 0; i < p.validDisplay.size(); i++) {
                    if (p.validDisplay[i] == displayVal && i < p.validRegistry.size()) {
                        regVal = p.validRegistry[i];
                        break;
                    }
                }
                break;
            }
        }
        SetAdvProperty(currentAdapter, kw, regVal);
    }
    ShowStatus(L"Adv. Adapter applied!");
}

void AppWindow::ApplyTweaks() {
    auto vals = CollectValues(g_tweakCtrl);
    for (auto& [k, v] : vals) {
        if (!v.empty()) SetAfdTweak(k, v);
    }
    ShowStatus(L"Tweaks applied!");
}

void AppWindow::ApplyPower() {
    auto vals = CollectValues(g_powerCtrl);
    for (auto& [kw, displayVal] : vals) {
        if (displayVal.empty()) continue;
        std::wstring regVal = displayVal;
        for (auto& p : advProps) {
            if (p.keyword == kw) {
                for (size_t i = 0; i < p.validDisplay.size(); i++) {
                    if (p.validDisplay[i] == displayVal && i < p.validRegistry.size()) {
                        regVal = p.validRegistry[i];
                        break;
                    }
                }
                break;
            }
        }
        SetAdvProperty(currentAdapter, kw, regVal);
    }
    ShowStatus(L"Power settings applied!");
}

void AppWindow::ApplyAll() {
    ApplyRss();
    ApplyGlobal();
    ApplyInterface();
    ApplyAdv();
    ApplyTweaks();
    ApplyPower();
    ShowStatus(L"All settings applied!");
}

void AppWindow::DoRestart() {
    ShowStatus(L"Restarting adapter...");
    RestartAdapter(currentAdapter);
    ShowStatus(L"Adapter restarted!");
}

void AppWindow::DoUnlockRss() {
    UnlockRssQueues(currentAdapter);
    ShowStatus(L"RSS Queues unlocked!");
    RefreshAll();
}

void AppWindow::ShowStatus(const std::wstring& msg, bool isError) {
    MessageBoxW(hWnd, msg.c_str(), isError ? L"Error" : L"Network Adapter Tweaker",
                MB_OK | (isError ? MB_ICONERROR : MB_ICONINFORMATION));
}

// =====================================================================
// WndProc
// =====================================================================
LRESULT CALLBACK AppWindow::WndProc(HWND hwnd, UINT msg, WPARAM wParam, LPARAM lParam) {
    AppWindow* self;
    if (msg == WM_CREATE) {
        auto cs = (CREATESTRUCTW*)lParam;
        self = (AppWindow*)cs->lpCreateParams;
        SetWindowLongPtrW(hwnd, GWLP_USERDATA, (LONG_PTR)self);
        self->hWnd = hwnd;
    } else {
        self = (AppWindow*)GetWindowLongPtrW(hwnd, GWLP_USERDATA);
    }
    if (self) return self->HandleMsg(msg, wParam, lParam);
    return DefWindowProcW(hwnd, msg, wParam, lParam);
}

LRESULT AppWindow::HandleMsg(UINT msg, WPARAM wParam, LPARAM lParam) {
    switch (msg) {
    case WM_CREATE: {
        int y = 6;
        // Adapter label
        HWND lbl = CreateWindowExW(0, L"STATIC", L"Adapter:",
            WS_CHILD | WS_VISIBLE, 8, y + 2, 50, 18, hWnd, nullptr, nullptr, nullptr);
        SendMessageW(lbl, WM_SETFONT, (WPARAM)hFontBold, TRUE);

        // Adapter combo
        hAdapterCombo = CreateWindowExW(0, L"COMBOBOX", L"",
            WS_CHILD | WS_VISIBLE | CBS_DROPDOWNLIST | WS_VSCROLL,
            62, y, 300, 300, hWnd, (HMENU)ID_ADAPTER_COMBO, nullptr, nullptr);
        SendMessageW(hAdapterCombo, WM_SETFONT, (WPARAM)hFont, TRUE);

        // Buttons
        int bx = 370;
        MakeButton(hWnd, bx, y, 50, 22, L"Open", ID_BTN_OPEN, hFontSmall);
        MakeButton(hWnd, bx + 56, y, 65, 22, L"Apply All", ID_BTN_APPLY_ALL, hFontSmall);
        MakeButton(hWnd, bx + 127, y, 100, 22, L"Restart Adapter", ID_BTN_RESTART, hFontSmall);
        MakeButton(hWnd, bx + 233, y, 95, 22, L"Opacity On/Off", ID_BTN_OPACITY, hFontSmall);

        // Registry + NDIS labels
        y += 28;
        hRegLabel = CreateWindowExW(0, L"STATIC", L"Registry: -",
            WS_CHILD | WS_VISIBLE | SS_NOPREFIX, 8, y, 600, 14, hWnd, nullptr, nullptr, nullptr);
        SendMessageW(hRegLabel, WM_SETFONT, (WPARAM)hFontSmall, TRUE);

        hNdisLabel = CreateWindowExW(0, L"STATIC", L"NDIS:  -",
            WS_CHILD | WS_VISIBLE, 620, y, 150, 14, hWnd, nullptr, nullptr, nullptr);
        SendMessageW(hNdisLabel, WM_SETFONT, (WPARAM)hFontSmall, TRUE);

        // Load adapters after window is created
        PostMessageW(hWnd, WM_USER + 1, 0, 0);
        return 0;
    }

    case WM_USER + 1:
        LoadAdapters();
        return 0;

    case WM_SIZE:
        if (wParam != SIZE_MINIMIZED && !currentAdapter.empty()) {
            BuildPanels();
        }
        return 0;

    case WM_COMMAND: {
        int id = LOWORD(wParam);
        int code = HIWORD(wParam);

        if (id == ID_ADAPTER_COMBO && code == CBN_SELCHANGE) {
            int idx = (int)SendMessageW(hAdapterCombo, CB_GETCURSEL, 0, 0);
            if (idx >= 0 && idx < (int)adapterList.size()) {
                SelectAdapter(adapterList[idx].name);
            }
        }
        else if (id == ID_BTN_OPEN) {
            ShellExecuteW(nullptr, L"open", L"ncpa.cpl", nullptr, nullptr, SW_SHOW);
        }
        else if (id == ID_BTN_APPLY_ALL) { ApplyAll(); }
        else if (id == ID_BTN_RESTART) { DoRestart(); }
        else if (id == ID_BTN_OPACITY) {
            static bool opaque = false;
            opaque = !opaque;
            SetLayeredWindowAttributes(hWnd, 0, opaque ? 200 : 255, LWA_ALPHA);
            LONG ex = GetWindowLongW(hWnd, GWL_EXSTYLE);
            if (opaque) ex |= WS_EX_LAYERED; else ex &= ~WS_EX_LAYERED;
            SetWindowLongW(hWnd, GWL_EXSTYLE, ex);
        }
        else if (id == ID_BTN_RSS_APPLY) { ApplyRss(); }
        else if (id == ID_BTN_RSS_UNLOCK) { DoUnlockRss(); }
        else if (id == ID_BTN_GLOBAL_APPLY) { ApplyGlobal(); }
        else if (id == ID_BTN_IFACE_APPLY) { ApplyInterface(); }
        else if (id == ID_BTN_ADV_APPLY) { ApplyAdv(); }
        else if (id == ID_BTN_TWEAK_APPLY) { ApplyTweaks(); }
        else if (id == ID_BTN_POWER_APPLY) { ApplyPower(); }
        else if (id == ID_CHK_IPV4) {
            ipv4Selected = true;
            SendDlgItemMessageW(hWnd, ID_CHK_IPV6, BM_SETCHECK, BST_UNCHECKED, 0);
            ifaceData = GetInterfaceSettings(currentAdapter, L"IPv4");
            BuildPanels();
        }
        else if (id == ID_CHK_IPV6) {
            ipv4Selected = false;
            SendDlgItemMessageW(hWnd, ID_CHK_IPV4, BM_SETCHECK, BST_UNCHECKED, 0);
            ifaceData = GetInterfaceSettings(currentAdapter, L"IPv6");
            BuildPanels();
        }
        return 0;
    }

    case WM_CTLCOLORSTATIC: {
        HDC hdc = (HDC)wParam;
        SetTextColor(hdc, CLR_CYAN);
        SetBkColor(hdc, CLR_BG);
        return (LRESULT)hBrBg;
    }

    case WM_CTLCOLOREDIT: {
        HDC hdc = (HDC)wParam;
        SetTextColor(hdc, CLR_CYAN);
        SetBkColor(hdc, CLR_INPUT_BG);
        return (LRESULT)hBrInput;
    }

    case WM_CTLCOLORLISTBOX: {
        HDC hdc = (HDC)wParam;
        SetTextColor(hdc, CLR_CYAN);
        SetBkColor(hdc, CLR_INPUT_BG);
        return (LRESULT)hBrInput;
    }

    case WM_ERASEBKGND: {
        HDC hdc = (HDC)wParam;
        RECT rc;
        GetClientRect(hWnd, &rc);
        FillRect(hdc, &rc, hBrBg);

        // Draw column separators
        int colW = (rc.right - rc.left) / 4;
        HPEN pen = CreatePen(PS_SOLID, 1, CLR_BORDER);
        SelectObject(hdc, pen);
        for (int i = 1; i < 4; i++) {
            MoveToEx(hdc, colW * i, 56, nullptr);
            LineTo(hdc, colW * i, rc.bottom);
        }
        // Top bar border
        MoveToEx(hdc, 0, 55, nullptr);
        LineTo(hdc, rc.right, 55);
        DeleteObject(pen);
        return 1;
    }

    case WM_DESTROY:
        PostQuitMessage(0);
        return 0;
    }
    return DefWindowProcW(hWnd, msg, wParam, lParam);
}

// =====================================================================
// Init & Run
// =====================================================================
static AppWindow g_appWindow;

void InitApp(HINSTANCE hInst) {
    INITCOMMONCONTROLSEX icex{sizeof(icex), ICC_STANDARD_CLASSES | ICC_LISTVIEW_CLASSES};
    InitCommonControlsEx(&icex);
    g_app = &g_appWindow;
    g_appWindow.Create(hInst);
}

int RunMessageLoop() {
    MSG msg;
    while (GetMessageW(&msg, nullptr, 0, 0)) {
        TranslateMessage(&msg);
        DispatchMessageW(&msg);
    }
    return (int)msg.wParam;
}
