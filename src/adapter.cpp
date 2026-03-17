#include "adapter.h"
#include <sstream>
#include <algorithm>

// --- Run PowerShell and capture stdout ---
std::wstring RunPS(const std::wstring& cmd, int timeoutMs) {
    std::wstring fullCmd = L"powershell.exe -NoProfile -ExecutionPolicy Bypass -Command \"" + cmd + L"\"";

    SECURITY_ATTRIBUTES sa{sizeof(sa), nullptr, TRUE};
    HANDLE hReadPipe, hWritePipe;
    if (!CreatePipe(&hReadPipe, &hWritePipe, &sa, 0)) return L"";
    SetHandleInformation(hReadPipe, HANDLE_FLAG_INHERIT, 0);

    STARTUPINFOW si{};
    si.cb = sizeof(si);
    si.dwFlags = STARTF_USESTDHANDLES | STARTF_USESHOWWINDOW;
    si.hStdOutput = hWritePipe;
    si.hStdError = hWritePipe;
    si.wShowWindow = SW_HIDE;

    PROCESS_INFORMATION pi{};
    BOOL ok = CreateProcessW(nullptr, fullCmd.data(), nullptr, nullptr, TRUE,
                             CREATE_NO_WINDOW, nullptr, nullptr, &si, &pi);
    CloseHandle(hWritePipe);

    if (!ok) { CloseHandle(hReadPipe); return L""; }

    WaitForSingleObject(pi.hProcess, (DWORD)timeoutMs);

    std::string buf;
    char tmp[4096];
    DWORD bytesRead;
    while (ReadFile(hReadPipe, tmp, sizeof(tmp) - 1, &bytesRead, nullptr) && bytesRead > 0) {
        tmp[bytesRead] = 0;
        buf += tmp;
    }

    CloseHandle(hReadPipe);
    CloseHandle(pi.hProcess);
    CloseHandle(pi.hThread);

    // Convert UTF-8 to wstring
    if (buf.empty()) return L"";
    int sz = MultiByteToWideChar(CP_UTF8, 0, buf.c_str(), (int)buf.size(), nullptr, 0);
    std::wstring result(sz, 0);
    MultiByteToWideChar(CP_UTF8, 0, buf.c_str(), (int)buf.size(), result.data(), sz);

    // Trim
    while (!result.empty() && (result.back() == L'\r' || result.back() == L'\n' || result.back() == L' '))
        result.pop_back();
    return result;
}

std::wstring PSGetValue(const std::wstring& expr) {
    return RunPS(expr);
}

// --- Parse simple "Name : Value" PowerShell output ---
static std::map<std::wstring, std::wstring> ParseFlat(const std::wstring& text) {
    std::map<std::wstring, std::wstring> m;
    std::wistringstream ss(text);
    std::wstring line;
    while (std::getline(ss, line)) {
        auto pos = line.find(L':');
        if (pos == std::wstring::npos) continue;
        std::wstring key = line.substr(0, pos);
        std::wstring val = (pos + 1 < line.size()) ? line.substr(pos + 1) : L"";
        // Trim
        auto trim = [](std::wstring& s) {
            while (!s.empty() && (s.front() == L' ' || s.front() == L'\t')) s.erase(s.begin());
            while (!s.empty() && (s.back() == L' ' || s.back() == L'\t' || s.back() == L'\r')) s.pop_back();
        };
        trim(key); trim(val);
        if (!key.empty()) m[key] = val;
    }
    return m;
}

// --- Parse CSV-like PowerShell output (Format-List) ---
static std::vector<std::wstring> SplitLines(const std::wstring& text) {
    std::vector<std::wstring> lines;
    std::wistringstream ss(text);
    std::wstring line;
    while (std::getline(ss, line)) {
        while (!line.empty() && (line.back() == L'\r' || line.back() == L'\n')) line.pop_back();
        lines.push_back(line);
    }
    return lines;
}

// --- Get Adapters ---
std::vector<AdapterInfo> GetAdapters() {
    std::vector<AdapterInfo> result;
    std::wstring raw = RunPS(
        L"Get-NetAdapter | Format-List Name, InterfaceDescription, Status, MacAddress, LinkSpeed, DriverVersion, NdisVersion, InterfaceGuid"
    );
    if (raw.empty()) return result;

    // Parse blocks separated by blank lines
    auto lines = SplitLines(raw);
    AdapterInfo cur{};
    bool hasData = false;

    for (auto& line : lines) {
        if (line.empty()) {
            if (hasData && !cur.name.empty()) result.push_back(cur);
            cur = {};
            hasData = false;
            continue;
        }
        auto pos = line.find(L':');
        if (pos == std::wstring::npos) continue;
        std::wstring key = line.substr(0, pos);
        std::wstring val = (pos + 1 < line.size()) ? line.substr(pos + 1) : L"";
        auto trim = [](std::wstring& s) {
            while (!s.empty() && (s.front() == L' ' || s.front() == L'\t')) s.erase(s.begin());
            while (!s.empty() && (s.back() == L' ' || s.back() == L'\t' || s.back() == L'\r')) s.pop_back();
        };
        trim(key); trim(val);
        hasData = true;

        if (key == L"Name") cur.name = val;
        else if (key == L"InterfaceDescription") cur.description = val;
        else if (key == L"Status") cur.status = val;
        else if (key == L"MacAddress") cur.macAddress = val;
        else if (key == L"LinkSpeed") cur.linkSpeed = val;
        else if (key == L"DriverVersion") cur.driverVersion = val;
        else if (key == L"NdisVersion") cur.ndisVersion = val;
        else if (key == L"InterfaceGuid") cur.guid = val;
    }
    if (hasData && !cur.name.empty()) result.push_back(cur);
    return result;
}

std::wstring GetAdapterRegistryPath(const std::wstring& adapterName) {
    return RunPS(
        L"$items = Get-ChildItem 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Class\\{4D36E972-E325-11CE-BFC1-08002BE10318}' -EA SilentlyContinue; "
        L"$guid = (Get-NetAdapter -Name '" + adapterName + L"').InterfaceGuid; "
        L"foreach($i in $items){ $g = (Get-ItemProperty $i.PSPath -Name 'NetCfgInstanceId' -EA SilentlyContinue).NetCfgInstanceId; "
        L"if($g -eq $guid){ $i.PSPath -replace 'Microsoft.PowerShell.Core\\\\Registry::',''; break } }"
    );
}

// --- RSS ---
std::map<std::wstring, std::wstring> GetRssSettings(const std::wstring& adapterName) {
    std::wstring raw = RunPS(
        L"Get-NetAdapterRss -Name '" + adapterName + L"' -EA SilentlyContinue | Format-List"
    );
    return ParseFlat(raw);
}

// --- Global ---
std::map<std::wstring, std::wstring> GetGlobalSettings() {
    std::wstring raw = RunPS(L"Get-NetOffloadGlobalSetting | Format-List");
    return ParseFlat(raw);
}

// --- Interface ---
std::map<std::wstring, std::wstring> GetInterfaceSettings(const std::wstring& adapterName, const std::wstring& family) {
    std::wstring raw = RunPS(
        L"Get-NetIPInterface -InterfaceAlias '" + adapterName + L"' -AddressFamily " + family + L" -EA SilentlyContinue | Format-List"
    );
    return ParseFlat(raw);
}

// --- Advanced Properties ---
std::vector<AdvProperty> GetAdvancedProperties(const std::wstring& adapterName) {
    std::vector<AdvProperty> result;
    std::wstring raw = RunPS(
        L"Get-NetAdapterAdvancedProperty -Name '" + adapterName + L"' -EA SilentlyContinue "
        L"| Format-List RegistryKeyword, DisplayName, DisplayValue, RegistryValue, ValidDisplayValues, ValidRegistryValues"
    );
    if (raw.empty()) return result;

    auto lines = SplitLines(raw);
    AdvProperty cur{};
    bool hasData = false;

    auto splitArray = [](const std::wstring& s) -> std::vector<std::wstring> {
        std::vector<std::wstring> v;
        // Format: {val1, val2, val3}
        std::wstring cleaned = s;
        // Remove { }
        size_t start = cleaned.find(L'{');
        size_t end = cleaned.rfind(L'}');
        if (start != std::wstring::npos && end != std::wstring::npos && end > start)
            cleaned = cleaned.substr(start + 1, end - start - 1);
        std::wistringstream ss(cleaned);
        std::wstring item;
        while (std::getline(ss, item, L',')) {
            while (!item.empty() && item.front() == L' ') item.erase(item.begin());
            while (!item.empty() && item.back() == L' ') item.pop_back();
            if (!item.empty()) v.push_back(item);
        }
        return v;
    };

    for (auto& line : lines) {
        if (line.empty()) {
            if (hasData && !cur.keyword.empty()) result.push_back(cur);
            cur = {};
            hasData = false;
            continue;
        }
        auto pos = line.find(L':');
        if (pos == std::wstring::npos) continue;
        std::wstring key = line.substr(0, pos);
        std::wstring val = (pos + 1 < line.size()) ? line.substr(pos + 1) : L"";
        auto trim = [](std::wstring& s) {
            while (!s.empty() && (s.front() == L' ' || s.front() == L'\t')) s.erase(s.begin());
            while (!s.empty() && (s.back() == L' ' || s.back() == L'\t' || s.back() == L'\r')) s.pop_back();
        };
        trim(key); trim(val);
        hasData = true;

        if (key == L"RegistryKeyword") cur.keyword = val;
        else if (key == L"DisplayName") cur.displayName = val;
        else if (key == L"DisplayValue") cur.displayValue = val;
        else if (key == L"RegistryValue") cur.regValue = val;
        else if (key == L"ValidDisplayValues") cur.validDisplay = splitArray(val);
        else if (key == L"ValidRegistryValues") cur.validRegistry = splitArray(val);
    }
    if (hasData && !cur.keyword.empty()) result.push_back(cur);
    return result;
}

// --- AFD Tweaks ---
std::map<std::wstring, std::wstring> GetAfdTweaks() {
    const wchar_t* keys[] = {
        L"DefaultReceiveWindow", L"DefaultSendWindow", L"BufferMultiplier", L"BufferAlignment",
        L"DoNotHoldNicBuffers", L"SmallBufferSize", L"MediumBufferSize", L"LargeBufferSize", L"HugeBufferSize",
        L"SmallBufferListDepth", L"MediumBufferListDepth", L"LargeBufferListDepth",
        L"DisableAddressSharing", L"DisableChainedReceive", L"DisableDirectAcceptEx", L"DisableRawSecurity",
        L"DynamicSendBufferDisable", L"FastSendDatagramThreshold", L"FastCopyReceiveThreshold",
        L"IgnorePushBitOnReceives", L"IgnoreOrderlyRelease", L"TransmitWorker", L"PriorityBoost",
    };
    std::map<std::wstring, std::wstring> m;
    HKEY hKey;
    if (RegOpenKeyExW(HKEY_LOCAL_MACHINE, L"SYSTEM\\CurrentControlSet\\Services\\AFD\\Parameters", 0, KEY_READ, &hKey) == ERROR_SUCCESS) {
        for (auto& k : keys) {
            DWORD val = 0, sz = sizeof(val), type = 0;
            if (RegQueryValueExW(hKey, k, nullptr, &type, (BYTE*)&val, &sz) == ERROR_SUCCESS && type == REG_DWORD) {
                m[k] = std::to_wstring(val);
            } else {
                m[k] = L"";
            }
        }
        RegCloseKey(hKey);
    }
    return m;
}

// --- Setters ---
bool SetRss(const std::wstring& adapterName, const std::map<std::wstring, std::wstring>& vals) {
    std::wstring parts;
    for (auto& [k, v] : vals) {
        if (!v.empty()) parts += L" -" + k + L" " + v;
    }
    if (parts.empty()) return false;
    RunPS(L"Set-NetAdapterRss -Name '" + adapterName + L"'" + parts + L" -NoRestart");
    return true;
}

bool SetGlobal(const std::map<std::wstring, std::wstring>& vals) {
    std::wstring parts;
    for (auto& [k, v] : vals) {
        if (!v.empty()) parts += L" -" + k + L" " + v;
    }
    if (parts.empty()) return false;
    RunPS(L"Set-NetOffloadGlobalSetting" + parts);
    return true;
}

bool SetInterface(const std::wstring& adapterName, const std::wstring& family, const std::map<std::wstring, std::wstring>& vals) {
    std::wstring parts;
    for (auto& [k, v] : vals) {
        if (!v.empty()) parts += L" -" + k + L" " + v;
    }
    if (parts.empty()) return false;
    RunPS(L"Set-NetIPInterface -InterfaceAlias '" + adapterName + L"' -AddressFamily " + family + parts);
    return true;
}

bool SetAdvProperty(const std::wstring& adapterName, const std::wstring& keyword, const std::wstring& value) {
    RunPS(L"Set-NetAdapterAdvancedProperty -Name '" + adapterName + L"' -RegistryKeyword '" + keyword + L"' -RegistryValue '" + value + L"' -NoRestart");
    return true;
}

bool SetAfdTweak(const std::wstring& key, const std::wstring& value) {
    HKEY hKey;
    if (RegCreateKeyExW(HKEY_LOCAL_MACHINE, L"SYSTEM\\CurrentControlSet\\Services\\AFD\\Parameters",
                        0, nullptr, 0, KEY_WRITE, nullptr, &hKey, nullptr) == ERROR_SUCCESS) {
        DWORD val = (DWORD)std::stoul(value);
        RegSetValueExW(hKey, key.c_str(), 0, REG_DWORD, (BYTE*)&val, sizeof(val));
        RegCloseKey(hKey);
        return true;
    }
    return false;
}

bool RestartAdapter(const std::wstring& adapterName) {
    RunPS(L"Disable-NetAdapter -Name '" + adapterName + L"' -Confirm:$false");
    RunPS(L"Enable-NetAdapter -Name '" + adapterName + L"' -Confirm:$false");
    return true;
}

bool UnlockRssQueues(const std::wstring& adapterName) {
    RunPS(L"Set-NetAdapterRss -Name '" + adapterName +
          L"' -NumberOfReceiveQueues (Get-NetAdapterRss -Name '" + adapterName +
          L"').IndirectionTableEntryCount -NoRestart -EA SilentlyContinue");
    return true;
}
