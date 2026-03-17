#pragma once
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <commctrl.h>
#include <string>
#include <vector>
#include <map>
#include <functional>
#include "adapter.h"

// --- Colors ---
#define CLR_BG          RGB(10, 14, 26)
#define CLR_PANEL       RGB(13, 18, 32)
#define CLR_HEADER      RGB(12, 20, 36)
#define CLR_BORDER      RGB(26, 39, 68)
#define CLR_BORDER_HI   RGB(30, 58, 95)
#define CLR_TEXT         RGB(200, 214, 229)
#define CLR_TEXT_DIM     RGB(90, 106, 128)
#define CLR_TEXT_LABEL   RGB(122, 141, 160)
#define CLR_CYAN         RGB(0, 212, 255)
#define CLR_GREEN        RGB(0, 255, 136)
#define CLR_ORANGE       RGB(255, 170, 0)
#define CLR_RED          RGB(255, 68, 102)
#define CLR_INPUT_BG     RGB(8, 12, 25)
#define CLR_ROW_HOVER    RGB(14, 20, 35)

// --- Control IDs ---
#define ID_ADAPTER_COMBO    1001
#define ID_BTN_OPEN         1002
#define ID_BTN_APPLY_ALL    1003
#define ID_BTN_RESTART      1004
#define ID_BTN_OPACITY      1005

// Sections start IDs (each section gets 200 IDs)
#define ID_RSS_BASE         2000
#define ID_GLOBAL_BASE      2200
#define ID_IFACE_BASE       2400
#define ID_ADV_BASE         2600
#define ID_TWEAK_BASE       2800
#define ID_POWER_BASE       3000
#define ID_INTERRUPT_BASE   3200

#define ID_BTN_RSS_APPLY    4001
#define ID_BTN_RSS_UNLOCK   4002
#define ID_BTN_GLOBAL_APPLY 4003
#define ID_BTN_IFACE_APPLY  4004
#define ID_BTN_ADV_APPLY    4005
#define ID_BTN_TWEAK_APPLY  4006
#define ID_BTN_POWER_APPLY  4007
#define ID_CHK_IPV4         4010
#define ID_CHK_IPV6         4011

// --- Panel layout ---
struct SettingControl {
    std::wstring key;
    std::wstring label;
    HWND hCtrl = nullptr;      // ComboBox or Edit
    HWND hLabel = nullptr;     // Static label
    bool isCombo = false;
};

struct PanelInfo {
    std::wstring title;
    HWND hPanel = nullptr;
    HWND hHeader = nullptr;
    HWND hBody = nullptr;
    std::vector<SettingControl> controls;
    int scrollY = 0;
    int contentHeight = 0;
};

// --- App Window ---
class AppWindow {
public:
    HWND hWnd = nullptr;
    HWND hAdapterCombo = nullptr;
    HWND hRegLabel = nullptr;
    HWND hNdisLabel = nullptr;

    std::vector<AdapterInfo> adapterList;
    std::wstring currentAdapter;
    std::vector<AdvProperty> advProps;

    // Data
    std::map<std::wstring, std::wstring> rssData;
    std::map<std::wstring, std::wstring> globalData;
    std::map<std::wstring, std::wstring> ifaceData;
    std::map<std::wstring, std::wstring> tweakData;

    bool ipv4Selected = true;

    HFONT hFont = nullptr;
    HFONT hFontBold = nullptr;
    HFONT hFontMono = nullptr;
    HFONT hFontSmall = nullptr;
    HBRUSH hBrBg = nullptr;
    HBRUSH hBrPanel = nullptr;
    HBRUSH hBrHeader = nullptr;
    HBRUSH hBrInput = nullptr;
    HBRUSH hBrBorder = nullptr;

    bool Create(HINSTANCE hInst);
    void LoadAdapters();
    void SelectAdapter(const std::wstring& name);
    void RefreshAll();
    void BuildPanels();

    // Apply handlers
    void ApplyRss();
    void ApplyGlobal();
    void ApplyInterface();
    void ApplyAdv();
    void ApplyTweaks();
    void ApplyPower();
    void ApplyAll();
    void DoRestart();
    void DoUnlockRss();

    void ShowStatus(const std::wstring& msg, bool isError = false);

    static LRESULT CALLBACK WndProc(HWND, UINT, WPARAM, LPARAM);
    LRESULT HandleMsg(UINT msg, WPARAM wParam, LPARAM lParam);
};

void InitApp(HINSTANCE hInst);
int RunMessageLoop();
