"""
Network Adapter Tweaker — Backend Engine
Direct registry access + PowerShell for NIC settings.
"""

import subprocess
import json
import winreg
import logging
import os
import ctypes
from typing import Dict, List, Optional, Tuple, Any

log = logging.getLogger("NATweaker")

# ───────────────────────────────────────────────────────
#  Helpers
# ───────────────────────────────────────────────────────

def is_admin() -> bool:
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def run_as_admin():
    """Re-launch the current script as admin."""
    import sys
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, " ".join(sys.argv), None, 1
    )
    sys.exit(0)


def ps(cmd: str, timeout: int = 15) -> str:
    """Run a PowerShell command, return stdout."""
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", cmd],
            capture_output=True, text=True, timeout=timeout, creationflags=0x08000000
        )
        return r.stdout.strip()
    except Exception as e:
        log.warning("PS error: %s", e)
        return ""


def ps_json(cmd: str, timeout: int = 15) -> list:
    """Run PS command → JSON → list of dicts."""
    raw = ps(cmd + " | ConvertTo-Json -Depth 4 -Compress", timeout)
    if not raw:
        return []
    try:
        data = json.loads(raw)
        return data if isinstance(data, list) else [data]
    except json.JSONDecodeError:
        return []


# ───────────────────────────────────────────────────────
#  Registry helpers (direct, no PowerShell)
# ───────────────────────────────────────────────────────

def reg_read_dword(hive, path: str, name: str) -> Optional[int]:
    try:
        with winreg.OpenKey(hive, path, 0, winreg.KEY_READ) as key:
            val, typ = winreg.QueryValueEx(key, name)
            if typ == winreg.REG_DWORD:
                return val
    except OSError:
        pass
    return None


def reg_write_dword(hive, path: str, name: str, value: int) -> bool:
    try:
        with winreg.CreateKeyEx(hive, path, 0, winreg.KEY_WRITE) as key:
            winreg.SetValueEx(key, name, 0, winreg.REG_DWORD, value)
        return True
    except OSError as e:
        log.error("reg_write_dword %s\\%s = %d failed: %s", path, name, value, e)
        return False


def reg_read_string(hive, path: str, name: str) -> Optional[str]:
    try:
        with winreg.OpenKey(hive, path, 0, winreg.KEY_READ) as key:
            val, typ = winreg.QueryValueEx(key, name)
            return str(val)
    except OSError:
        pass
    return None


# ───────────────────────────────────────────────────────
#  Adapter Info
# ───────────────────────────────────────────────────────

class AdapterInfo:
    __slots__ = ("name", "description", "status", "mac", "speed", "driver", "ndis", "guid", "if_index")

    def __init__(self, **kw):
        for s in self.__slots__:
            setattr(self, s, kw.get(s, ""))

    def display(self) -> str:
        s = self.description or self.name
        if self.status and self.status != "Up":
            s += f" ({self.status})"
        return s


def get_adapters() -> List[AdapterInfo]:
    """Get all network adapters."""
    data = ps_json(
        "Get-NetAdapter | Select-Object Name, InterfaceDescription, Status, "
        "MacAddress, LinkSpeed, DriverVersion, NdisVersion, InterfaceGuid, ifIndex"
    )
    result = []
    for d in data:
        result.append(AdapterInfo(
            name=d.get("Name", ""),
            description=d.get("InterfaceDescription", ""),
            status=d.get("Status", ""),
            mac=d.get("MacAddress", ""),
            speed=d.get("LinkSpeed", ""),
            driver=d.get("DriverVersion", ""),
            ndis=str(d.get("NdisVersion", "")),
            guid=d.get("InterfaceGuid", ""),
            if_index=str(d.get("ifIndex", "")),
        ))
    # Sort: Up first, then by name
    result.sort(key=lambda a: (0 if a.status == "Up" else 1, a.name))
    return result


def get_adapter_reg_path(adapter_name: str) -> str:
    """Find the adapter's registry path under Class\\{4D36E972...}."""
    return ps(
        "$items = Get-ChildItem 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Class\\"
        "{4D36E972-E325-11CE-BFC1-08002BE10318}' -EA SilentlyContinue; "
        f"$guid = (Get-NetAdapter -Name '{adapter_name}').InterfaceGuid; "
        "foreach($i in $items){ $g = (Get-ItemProperty $i.PSPath -Name "
        "'NetCfgInstanceId' -EA SilentlyContinue).NetCfgInstanceId; "
        "if($g -eq $guid){ $i.PSPath -replace "
        "'Microsoft.PowerShell.Core\\\\Registry::',''; break } }"
    )


# ───────────────────────────────────────────────────────
#  Advanced Properties
# ───────────────────────────────────────────────────────

class AdvProperty:
    __slots__ = ("keyword", "display_name", "display_value", "reg_value",
                 "valid_display", "valid_registry")

    def __init__(self, **kw):
        self.keyword = kw.get("keyword", "")
        self.display_name = kw.get("display_name", "")
        self.display_value = kw.get("display_value", "")
        self.reg_value = kw.get("reg_value", "")
        self.valid_display = kw.get("valid_display", [])
        self.valid_registry = kw.get("valid_registry", [])


def get_adv_properties(adapter_name: str) -> List[AdvProperty]:
    """Get all advanced properties for an adapter."""
    data = ps_json(
        f"Get-NetAdapterAdvancedProperty -Name '{adapter_name}' -EA SilentlyContinue "
        "| Select-Object RegistryKeyword, DisplayName, DisplayValue, RegistryValue, "
        "ValidDisplayValues, ValidRegistryValues"
    )
    result = []
    for d in data:
        result.append(AdvProperty(
            keyword=d.get("RegistryKeyword", ""),
            display_name=d.get("DisplayName", ""),
            display_value=str(d.get("DisplayValue", "")),
            reg_value=str(d.get("RegistryValue", "")),
            valid_display=d.get("ValidDisplayValues") or [],
            valid_registry=d.get("ValidRegistryValues") or [],
        ))
    return result


# ───────────────────────────────────────────────────────
#  Read Settings
# ───────────────────────────────────────────────────────

def get_rss(adapter_name: str) -> Dict[str, str]:
    data = ps_json(f"Get-NetAdapterRss -Name '{adapter_name}' -EA SilentlyContinue | Select-Object *")
    if not data:
        return {}
    r = data[0]
    keys = ["Enabled", "NumberOfReceiveQueues", "Profile", "BaseProcessorNumber",
            "MaxProcessorNumber", "MaxProcessors", "BaseProcessorGroup"]
    return {k: str(r.get(k, "")) for k in keys if k in r}


def get_global() -> Dict[str, str]:
    data = ps_json("Get-NetOffloadGlobalSetting | Select-Object *")
    if not data:
        return {}
    r = data[0]
    keys = ["ReceiveSideScaling", "ReceiveSegmentCoalescing", "Chimney",
            "TaskOffload", "NetworkDirect", "NetworkDirectAcrossIPSubnets",
            "PacketCoalescingFilter"]
    return {k: str(r.get(k, "")) for k in keys if k in r}


def get_interface(adapter_name: str, family: str = "IPv4") -> Dict[str, str]:
    data = ps_json(
        f"Get-NetIPInterface -InterfaceAlias '{adapter_name}' "
        f"-AddressFamily {family} -EA SilentlyContinue | Select-Object *"
    )
    if not data:
        return {}
    r = data[0]
    keys = [
        "AdvertiseDefaultRoute", "Advertising", "AutomaticMetric", "ClampMss",
        "DirectedMacWolPattern", "EcnMarking", "ForceArpNdWolPattern", "Forwarding",
        "IgnoreDefaultRoutes", "ManagedAddressConfiguration", "NeighborDiscoverySupported",
        "NeighborUnreachabilityDetection", "OtherStatefulConfiguration", "RouterDiscovery",
        "Store", "WeakHostReceive", "WeakHostSend", "CurrentHopLimit",
        "BaseReachableTime", "RetransmitTime", "ReachableTime",
        "DadRetransmitTime", "DadTransmits", "NlMtu",
    ]
    return {k: str(r.get(k, "")) for k in keys if k in r}


def get_afd_tweaks() -> Dict[str, str]:
    """Read AFD parameters directly from registry (fast, no PowerShell)."""
    path = r"SYSTEM\CurrentControlSet\Services\AFD\Parameters"
    keys = [
        "DefaultReceiveWindow", "DefaultSendWindow", "BufferMultiplier", "BufferAlignment",
        "DoNotHoldNicBuffers", "SmallBufferSize", "MediumBufferSize", "LargeBufferSize",
        "HugeBufferSize", "SmallBufferListDepth", "MediumBufferListDepth", "LargeBufferListDepth",
        "DisableAddressSharing", "DisableChainedReceive", "DisableDirectAcceptEx",
        "DisableRawSecurity", "DynamicSendBufferDisable", "FastSendDatagramThreshold",
        "FastCopyReceiveThreshold", "IgnorePushBitOnReceives", "IgnoreOrderlyRelease",
        "TransmitWorker", "PriorityBoost",
    ]
    result = {}
    for k in keys:
        val = reg_read_dword(winreg.HKEY_LOCAL_MACHINE, path, k)
        result[k] = str(val) if val is not None else ""
    return result


# ───────────────────────────────────────────────────────
#  Write Settings
# ───────────────────────────────────────────────────────

def set_rss(adapter_name: str, settings: Dict[str, str]) -> Tuple[bool, str]:
    parts = " ".join(f"-{k} {v}" for k, v in settings.items() if v)
    if not parts:
        return False, "No settings"
    out = ps(f"Set-NetAdapterRss -Name '{adapter_name}' {parts} -NoRestart")
    return True, out or "OK"


def set_global(settings: Dict[str, str]) -> Tuple[bool, str]:
    parts = " ".join(f"-{k} {v}" for k, v in settings.items() if v)
    if not parts:
        return False, "No settings"
    out = ps(f"Set-NetOffloadGlobalSetting {parts}")
    return True, out or "OK"


def set_interface(adapter_name: str, family: str, settings: Dict[str, str]) -> Tuple[bool, str]:
    parts = " ".join(f"-{k} {v}" for k, v in settings.items() if v)
    if not parts:
        return False, "No settings"
    out = ps(f"Set-NetIPInterface -InterfaceAlias '{adapter_name}' -AddressFamily {family} {parts}")
    return True, out or "OK"


def set_adv_property(adapter_name: str, keyword: str, reg_value: str) -> Tuple[bool, str]:
    out = ps(
        f"Set-NetAdapterAdvancedProperty -Name '{adapter_name}' "
        f"-RegistryKeyword '{keyword}' -RegistryValue '{reg_value}' -NoRestart"
    )
    return True, out or "OK"


def set_afd_tweak(key: str, value: int) -> bool:
    return reg_write_dword(
        winreg.HKEY_LOCAL_MACHINE,
        r"SYSTEM\CurrentControlSet\Services\AFD\Parameters",
        key, value
    )


def restart_adapter(adapter_name: str) -> Tuple[bool, str]:
    ps(f"Disable-NetAdapter -Name '{adapter_name}' -Confirm:$false")
    ps(f"Enable-NetAdapter -Name '{adapter_name}' -Confirm:$false")
    return True, "Adapter restarted"


def unlock_rss(adapter_name: str) -> Tuple[bool, str]:
    ps(f"Set-NetAdapterRss -Name '{adapter_name}' "
       f"-NumberOfReceiveQueues (Get-NetAdapterRss -Name '{adapter_name}')"
       f".IndirectionTableEntryCount -NoRestart -EA SilentlyContinue")
    return True, "RSS Queues unlocked"


# ───────────────────────────────────────────────────────
#  Presets
# ───────────────────────────────────────────────────────

PRESET_GAMING = {
    "rss": {"Enabled": "True", "Profile": "NUMAStatic"},
    "global": {
        "ReceiveSideScaling": "Enabled",
        "ReceiveSegmentCoalescing": "Disabled",
        "Chimney": "Disabled",
        "TaskOffload": "Disabled",
        "NetworkDirect": "Disabled",
        "PacketCoalescingFilter": "Disabled",
    },
    "adv": {
        "*FlowControl": "0",           # Disabled
        "*InterruptModeration": "0",    # Disabled
        "*PMARPOffload": "0",           # Disabled
        "*PMNSOffload": "0",            # Disabled
        "*WakeOnMagicPacket": "0",
        "*WakeOnPattern": "0",
        "WakeOnLink": "0",
        "*EEE": "0",
        "EnableGreenEthernet": "0",
        "ReduceSpeedOnPowerDown": "0",
        "*PMAPowerManagement": "0",
        "AutoPowerSaveModeEnabled": "0",
        "NicAutoPowerSaver": "0",
    },
    "tweaks": {
        "DefaultReceiveWindow": 512,
        "DefaultSendWindow": 512,
        "BufferMultiplier": 1,
        "DynamicSendBufferDisable": 0,
        "IgnorePushBitOnReceives": 1,
    },
}

PRESET_DEFAULT = {
    "global": {
        "ReceiveSideScaling": "Enabled",
        "ReceiveSegmentCoalescing": "Enabled",
        "Chimney": "Disabled",
        "TaskOffload": "Enabled",
        "NetworkDirect": "Enabled",
        "PacketCoalescingFilter": "Enabled",
    },
    "adv": {
        "*FlowControl": "3",
        "*InterruptModeration": "1",
    },
}


def apply_preset(adapter_name: str, preset: dict) -> List[str]:
    """Apply a preset, return list of results."""
    results = []
    if "rss" in preset:
        ok, msg = set_rss(adapter_name, preset["rss"])
        results.append(f"RSS: {msg}")
    if "global" in preset:
        ok, msg = set_global(preset["global"])
        results.append(f"Global: {msg}")
    if "adv" in preset:
        for kw, val in preset["adv"].items():
            ok, msg = set_adv_property(adapter_name, kw, val)
            results.append(f"Adv {kw}: {msg}")
    if "tweaks" in preset:
        for k, v in preset["tweaks"].items():
            ok = set_afd_tweak(k, v)
            results.append(f"Tweak {k}: {'OK' if ok else 'FAIL'}")
    return results


# ───────────────────────────────────────────────────────
#  Export / Import
# ───────────────────────────────────────────────────────

def export_settings(adapter_name: str, filepath: str) -> bool:
    """Export all current settings to JSON."""
    data = {
        "adapter": adapter_name,
        "rss": get_rss(adapter_name),
        "global": get_global(),
        "interface_v4": get_interface(adapter_name, "IPv4"),
        "interface_v6": get_interface(adapter_name, "IPv6"),
        "adv": {p.keyword: {"value": p.display_value, "reg": p.reg_value}
                for p in get_adv_properties(adapter_name)},
        "tweaks": get_afd_tweaks(),
    }
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        log.error("Export failed: %s", e)
        return False


def import_settings(adapter_name: str, filepath: str) -> List[str]:
    """Import settings from JSON and apply."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return [f"Import failed: {e}"]

    results = []
    if "rss" in data:
        ok, msg = set_rss(adapter_name, data["rss"])
        results.append(f"RSS: {msg}")
    if "global" in data:
        ok, msg = set_global(data["global"])
        results.append(f"Global: {msg}")
    if "adv" in data:
        for kw, info in data["adv"].items():
            reg_val = info.get("reg", info.get("value", ""))
            if reg_val:
                ok, msg = set_adv_property(adapter_name, kw, reg_val)
                results.append(f"Adv {kw}: {msg}")
    if "tweaks" in data:
        for k, v in data["tweaks"].items():
            if v:
                ok = set_afd_tweak(k, int(v))
                results.append(f"Tweak {k}: {'OK' if ok else 'FAIL'}")
    return results
