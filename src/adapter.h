#pragma once
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <string>
#include <vector>
#include <map>

struct AdapterInfo {
    std::wstring name;
    std::wstring description;
    std::wstring status;
    std::wstring macAddress;
    std::wstring linkSpeed;
    std::wstring driverVersion;
    std::wstring ndisVersion;
    std::wstring guid;
    std::wstring registryPath;
};

struct AdvProperty {
    std::wstring keyword;
    std::wstring displayName;
    std::wstring displayValue;
    std::wstring regValue;
    std::vector<std::wstring> validDisplay;
    std::vector<std::wstring> validRegistry;
};

// Run PowerShell, return stdout
std::wstring RunPS(const std::wstring& cmd, int timeoutMs = 15000);

// Get all network adapters
std::vector<AdapterInfo> GetAdapters();

// Get registry path for adapter
std::wstring GetAdapterRegistryPath(const std::wstring& adapterName);

// Read a single value via PowerShell expression
std::wstring PSGetValue(const std::wstring& expr);

// Get all advanced properties for an adapter
std::vector<AdvProperty> GetAdvancedProperties(const std::wstring& adapterName);

// Get RSS settings as key-value
std::map<std::wstring, std::wstring> GetRssSettings(const std::wstring& adapterName);

// Get global offload settings
std::map<std::wstring, std::wstring> GetGlobalSettings();

// Get interface settings (IPv4 or IPv6)
std::map<std::wstring, std::wstring> GetInterfaceSettings(const std::wstring& adapterName, const std::wstring& family);

// Get AFD registry tweaks
std::map<std::wstring, std::wstring> GetAfdTweaks();

// --- Setters ---
bool SetRss(const std::wstring& adapterName, const std::map<std::wstring, std::wstring>& vals);
bool SetGlobal(const std::map<std::wstring, std::wstring>& vals);
bool SetInterface(const std::wstring& adapterName, const std::wstring& family, const std::map<std::wstring, std::wstring>& vals);
bool SetAdvProperty(const std::wstring& adapterName, const std::wstring& keyword, const std::wstring& value);
bool SetAfdTweak(const std::wstring& key, const std::wstring& value);
bool RestartAdapter(const std::wstring& adapterName);
bool UnlockRssQueues(const std::wstring& adapterName);
