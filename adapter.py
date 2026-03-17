"""
Network Adapter Tweaker — Backend Engine v2
Direct registry + PowerShell hybrid for maximum performance.
"""
import subprocess, json, winreg, ctypes, sys, os, logging, time
from typing import Dict, List, Optional, Tuple
from datetime import datetime

log = logging.getLogger("NATweaker")

# ─── Admin ───
def is_admin() -> bool:
    try: return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except: return False

def run_as_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit(0)

# ─── PowerShell ───
_PS_FLAGS = 0x08000000  # CREATE_NO_WINDOW

def ps(cmd: str, timeout: int = 20) -> str:
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", cmd],
            capture_output=True, text=True, timeout=timeout, creationflags=_PS_FLAGS)
        return r.stdout.strip()
    except: return ""

def ps_json(cmd: str) -> list:
    raw = ps(cmd + " | ConvertTo-Json -Depth 4 -Compress")
    if not raw: return []
    try:
        d = json.loads(raw)
        return d if isinstance(d, list) else [d]
    except: return []

# ─── Registry (direct — fast) ───
def reg_read(hive, path, name, expect_type=None):
    try:
        with winreg.OpenKey(hive, path, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as k:
            val, typ = winreg.QueryValueEx(k, name)
            return val
    except: return None

def reg_write_dword(hive, path, name, value):
    try:
        with winreg.CreateKeyEx(hive, path, 0, winreg.KEY_WRITE | winreg.KEY_WOW64_64KEY) as k:
            winreg.SetValueEx(k, name, 0, winreg.REG_DWORD, int(value))
        return True
    except: return False

def reg_delete(hive, path, name):
    try:
        with winreg.OpenKey(hive, path, 0, winreg.KEY_WRITE | winreg.KEY_WOW64_64KEY) as k:
            winreg.DeleteValue(k, name)
        return True
    except: return False

# ─── Adapter Discovery ───
class Adapter:
    def __init__(self, **kw):
        self.name = kw.get("name", "")
        self.desc = kw.get("desc", "")
        self.status = kw.get("status", "")
        self.mac = kw.get("mac", "")
        self.speed = kw.get("speed", "")
        self.driver = kw.get("driver", "")
        self.ndis = kw.get("ndis", "")
        self.guid = kw.get("guid", "")
        self.ifindex = kw.get("ifindex", "")
        self.reg_path = ""

    def label(self):
        s = self.desc or self.name
        if self.status != "Up": s += f" ({self.status})"
        return s

def get_adapters() -> List[Adapter]:
    data = ps_json(
        "Get-NetAdapter | Select-Object Name,InterfaceDescription,Status,"
        "MacAddress,LinkSpeed,DriverVersion,NdisVersion,InterfaceGuid,ifIndex"
    )
    out = []
    for d in data:
        out.append(Adapter(
            name=d.get("Name",""), desc=d.get("InterfaceDescription",""),
            status=d.get("Status",""), mac=d.get("MacAddress",""),
            speed=d.get("LinkSpeed",""), driver=d.get("DriverVersion",""),
            ndis=str(d.get("NdisVersion","")), guid=d.get("InterfaceGuid",""),
            ifindex=str(d.get("ifIndex","")),
        ))
    out.sort(key=lambda a: (0 if a.status == "Up" else 1, a.name))
    return out

def get_reg_path(name: str) -> str:
    return ps(
        "$items=Get-ChildItem 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Class\\"
        "{4D36E972-E325-11CE-BFC1-08002BE10318}' -EA SilentlyContinue;"
        f"$guid=(Get-NetAdapter -Name '{name}').InterfaceGuid;"
        "foreach($i in $items){{$g=(Get-ItemProperty $i.PSPath -Name "
        "'NetCfgInstanceId' -EA SilentlyContinue).NetCfgInstanceId;"
        "if($g -eq $guid){{$i.PSPath -replace "
        "'Microsoft.PowerShell.Core\\\\Registry::','';break}}}}"
    )

# ─── Advanced Properties ───
class AdvProp:
    __slots__ = ("keyword","display_name","display_value","reg_value","valid_display","valid_reg")
    def __init__(self, **kw):
        self.keyword = kw.get("keyword","")
        self.display_name = kw.get("display_name","")
        self.display_value = kw.get("display_value","")
        self.reg_value = kw.get("reg_value","")
        self.valid_display = kw.get("valid_display",[])
        self.valid_reg = kw.get("valid_reg",[])

    def display_to_reg(self, display_val):
        for i, dv in enumerate(self.valid_display):
            if dv == display_val and i < len(self.valid_reg):
                return self.valid_reg[i]
        return display_val

def get_adv_props(name: str) -> List[AdvProp]:
    data = ps_json(
        f"Get-NetAdapterAdvancedProperty -Name '{name}' -EA SilentlyContinue "
        "| Select-Object RegistryKeyword,DisplayName,DisplayValue,RegistryValue,"
        "ValidDisplayValues,ValidRegistryValues"
    )
    return [AdvProp(
        keyword=d.get("RegistryKeyword",""),
        display_name=d.get("DisplayName",""),
        display_value=str(d.get("DisplayValue","")),
        reg_value=str(d.get("RegistryValue","")),
        valid_display=d.get("ValidDisplayValues") or [],
        valid_reg=d.get("ValidRegistryValues") or [],
    ) for d in data]

# ─── Read settings ───
def get_rss(name): return {k:str(v) for k,v in (ps_json(f"Get-NetAdapterRss -Name '{name}' -EA SilentlyContinue | Select-Object *") or [{}])[0].items()}
def get_global(): return {k:str(v) for k,v in (ps_json("Get-NetOffloadGlobalSetting | Select-Object *") or [{}])[0].items()}
def get_iface(name, fam="IPv4"): return {k:str(v) for k,v in (ps_json(f"Get-NetIPInterface -InterfaceAlias '{name}' -AddressFamily {fam} -EA SilentlyContinue | Select-Object *") or [{}])[0].items()}

AFD_PATH = r"SYSTEM\CurrentControlSet\Services\AFD\Parameters"
AFD_KEYS = [
    "DefaultReceiveWindow","DefaultSendWindow","BufferMultiplier","BufferAlignment",
    "DoNotHoldNicBuffers","SmallBufferSize","MediumBufferSize","LargeBufferSize",
    "HugeBufferSize","SmallBufferListDepth","MediumBufferListDepth","LargeBufferListDepth",
    "DisableAddressSharing","DisableChainedReceive","DisableDirectAcceptEx",
    "DisableRawSecurity","DynamicSendBufferDisable","FastSendDatagramThreshold",
    "FastCopyReceiveThreshold","IgnorePushBitOnReceives","IgnoreOrderlyRelease",
    "TransmitWorker","PriorityBoost",
]

def get_afd():
    out = {}
    for k in AFD_KEYS:
        v = reg_read(winreg.HKEY_LOCAL_MACHINE, AFD_PATH, k)
        out[k] = str(v) if v is not None else ""
    return out

# ─── Write settings ───
def set_rss(name, vals):
    parts = " ".join(f"-{k} {v}" for k,v in vals.items() if v)
    return ps(f"Set-NetAdapterRss -Name '{name}' {parts} -NoRestart") if parts else ""

def set_global(vals):
    parts = " ".join(f"-{k} {v}" for k,v in vals.items() if v)
    return ps(f"Set-NetOffloadGlobalSetting {parts}") if parts else ""

def set_iface(name, fam, vals):
    parts = " ".join(f"-{k} {v}" for k,v in vals.items() if v)
    return ps(f"Set-NetIPInterface -InterfaceAlias '{name}' -AddressFamily {fam} {parts}") if parts else ""

def set_adv(name, keyword, reg_value):
    return ps(f"Set-NetAdapterAdvancedProperty -Name '{name}' -RegistryKeyword '{keyword}' -RegistryValue '{reg_value}' -NoRestart")

def set_afd(key, value):
    return reg_write_dword(winreg.HKEY_LOCAL_MACHINE, AFD_PATH, key, value)

def restart(name):
    ps(f"Disable-NetAdapter -Name '{name}' -Confirm:$false")
    ps(f"Enable-NetAdapter -Name '{name}' -Confirm:$false")

def unlock_rss(name):
    ps(f"Set-NetAdapterRss -Name '{name}' -NumberOfReceiveQueues (Get-NetAdapterRss -Name '{name}').IndirectionTableEntryCount -NoRestart -EA SilentlyContinue")

# ─── Presets ───
PRESETS = {
    "gaming": {
        "name": "Gaming (Low Latency)",
        "desc": "Disable offloads, power saving, interrupt moderation — lowest ping",
        "global": {"ReceiveSideScaling":"Enabled","ReceiveSegmentCoalescing":"Disabled",
                   "Chimney":"Disabled","TaskOffload":"Disabled","NetworkDirect":"Disabled",
                   "PacketCoalescingFilter":"Disabled"},
        "adv": {"*FlowControl":"0","*InterruptModeration":"0","*PMARPOffload":"0",
                "*PMNSOffload":"0","*WakeOnMagicPacket":"0","*WakeOnPattern":"0",
                "WakeOnLink":"0","*EEE":"0","EnableGreenEthernet":"0",
                "ReduceSpeedOnPowerDown":"0","*PMAPowerManagement":"0",
                "AutoPowerSaveModeEnabled":"0","NicAutoPowerSaver":"0"},
        "afd": {"DefaultReceiveWindow":512,"DefaultSendWindow":512,"BufferMultiplier":1,
                "DynamicSendBufferDisable":0,"IgnorePushBitOnReceives":1},
    },
    "streaming": {
        "name": "Streaming (High Throughput)",
        "desc": "Maximize bandwidth — enable offloads, large buffers",
        "global": {"ReceiveSideScaling":"Enabled","ReceiveSegmentCoalescing":"Enabled",
                   "TaskOffload":"Enabled","PacketCoalescingFilter":"Enabled"},
        "adv": {"*FlowControl":"3","*InterruptModeration":"1",
                "*LsoV2IPv4":"1","*LsoV2IPv6":"1"},
        "afd": {"DefaultReceiveWindow":65535,"DefaultSendWindow":65535},
    },
    "default": {
        "name": "Windows Default",
        "desc": "Reset to Windows default values",
        "global": {"ReceiveSideScaling":"Enabled","ReceiveSegmentCoalescing":"Enabled",
                   "Chimney":"Disabled","TaskOffload":"Enabled","NetworkDirect":"Enabled",
                   "PacketCoalescingFilter":"Enabled"},
        "adv": {"*FlowControl":"3","*InterruptModeration":"1"},
    },
}

def apply_preset(name, preset_key):
    p = PRESETS[preset_key]
    results = []
    if "global" in p: set_global(p["global"]); results.append("Global")
    if "adv" in p:
        for kw,v in p["adv"].items(): set_adv(name, kw, v)
        results.append(f"Adv({len(p['adv'])})")
    if "afd" in p:
        for k,v in p["afd"].items(): set_afd(k, v)
        results.append(f"AFD({len(p['afd'])})")
    return results

# ─── Export / Import ───
def export_all(name, filepath):
    data = {"_meta":{"adapter":name,"exported":datetime.now().isoformat(),"tool":"NATweaker"},
            "rss":get_rss(name),"global":get_global(),
            "iface_v4":get_iface(name,"IPv4"),"iface_v6":get_iface(name,"IPv6"),
            "adv":{p.keyword:{"display":p.display_value,"reg":p.reg_value} for p in get_adv_props(name)},
            "afd":get_afd()}
    with open(filepath,"w",encoding="utf-8") as f: json.dump(data,f,indent=2,ensure_ascii=False)

def import_all(name, filepath):
    with open(filepath,"r",encoding="utf-8") as f: data=json.load(f)
    n=0
    if "global" in data: set_global(data["global"]); n+=1
    if "adv" in data:
        for kw,info in data["adv"].items():
            rv=info.get("reg",info.get("display",""))
            if rv: set_adv(name,kw,rv); n+=1
    if "afd" in data:
        for k,v in data["afd"].items():
            if v:
                try: set_afd(k,int(v)); n+=1
                except: pass
    return n

# ─── Auto backup ───
BACKUP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backups")

def auto_backup(name):
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(BACKUP_DIR, f"{name}_{ts}.json")
    export_all(name, path)
    return path

# ─── Network stats (live) ───
def get_net_stats(name):
    data = ps_json(f"Get-NetAdapterStatistics -Name '{name}' -EA SilentlyContinue | Select-Object *")
    if not data: return {}
    d = data[0]
    return {
        "rx_bytes": d.get("ReceivedBytes",0), "tx_bytes": d.get("SentBytes",0),
        "rx_pkts": d.get("ReceivedUnicastPackets",0), "tx_pkts": d.get("SentUnicastPackets",0),
        "rx_errs": d.get("ReceivedPacketErrors",0), "tx_errs": d.get("OutboundPacketErrors",0),
        "rx_disc": d.get("ReceivedDiscards",0), "tx_disc": d.get("OutboundDiscards",0),
    }
