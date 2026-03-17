"""
╔═══════════════════════════════════════════════════════════════════╗
║  Anti-Crack Guard v3 — by Bootstep                               ║
║  กันทุกจุดอ่อนของ Python + กัน RE ทุกรูปแบบ                       ║
╠═══════════════════════════════════════════════════════════════════╣
║   1. Anti-Debug          — 8 วิธี: API/PEB/Port/Flags/HWBP/     ║
║                            Timing/OutputDbg/CloseHandle          ║
║   2. Anti-Decompile      — block uncompyle6/decompyle3/dis       ║
║   3. Anti-PyInstExtractor— ตรวจจับ extract + encrypt bytecode    ║
║   4. Anti-Process        — 40+ RE tools detection                ║
║   5. Anti-Window         — scan window titles for RE tools       ║
║   6. Anti-Tamper         — SHA256 integrity of all source files  ║
║   7. Anti-Hook           — detect JMP/INT3/NOP patches on APIs   ║
║   8. Anti-Dump           — ป้องกัน memory dump                    ║
║   9. Anti-Trace          — block settrace/setprofile             ║
║  10. Anti-VM/Sandbox     — detect VMware/VBox/Sandboxie/Any.Run  ║
║  11. Anti-DLL-Inject     — detect suspicious DLL injections      ║
║  12. Anti-Attach         — hide thread from debugger             ║
║  13. Parent Process      — verify parent is Explorer not RE tool ║
║  14. Kernel Debugger     — detect kernel-mode debugger           ║
║  15. Code Scramble       — overwrite co_filename/co_name         ║
║  16. Import Blocker      — block decompiler module imports       ║
║  17. Stack Protection    — suppress tracebacks leaking code      ║
║  18. Self-Checksum       — CRC32 of exe file                    ║
║  19. Env Var Check       — detect debugger env vars              ║
║  20. Heartbeat           — continuous 5s checks, 2 strikes out   ║
╚═══════════════════════════════════════════════════════════════════╝
"""

import ctypes
import ctypes.wintypes as wt
import hashlib
import os
import sys
import time
import threading
import subprocess
import json
import struct
import types
import traceback
from pathlib import Path

_HEARTBEAT_SEC = 5
_MAX_STRIKES = 2
_SELF_FILES = ["main.pyw", "adapter.py", "guard.py"]

k32 = ctypes.windll.kernel32
ntdll = ctypes.windll.ntdll
u32 = ctypes.windll.user32


# ═══════════════════════════════════════════
#  1. ANTI-DEBUG (8 methods)
# ═══════════════════════════════════════════

def _dbg_api():
    if k32.IsDebuggerPresent(): return True
    f = ctypes.c_int(0)
    k32.CheckRemoteDebuggerPresent(k32.GetCurrentProcess(), ctypes.byref(f))
    return bool(f.value)

def _dbg_peb():
    try:
        class PBI(ctypes.Structure):
            _fields_ = [("R1",ctypes.c_void_p),("Peb",ctypes.c_void_p),
                        ("R2",ctypes.c_void_p*2),("Uid",ctypes.POINTER(ctypes.c_ulong)),
                        ("R3",ctypes.c_void_p)]
        pbi = PBI(); rl = ctypes.c_ulong(0)
        ntdll.NtQueryInformationProcess(k32.GetCurrentProcess(), 0,
            ctypes.byref(pbi), ctypes.sizeof(pbi), ctypes.byref(rl))
        if pbi.Peb:
            bd = ctypes.c_ubyte(0)
            k32.ReadProcessMemory(k32.GetCurrentProcess(),
                ctypes.c_void_p(pbi.Peb + 2), ctypes.byref(bd), 1, None)
            return bd.value != 0
    except: pass
    return False

def _dbg_port():
    try:
        p = ctypes.c_void_p(0); rl = ctypes.c_ulong(0)
        ntdll.NtQueryInformationProcess(k32.GetCurrentProcess(), 7,
            ctypes.byref(p), ctypes.sizeof(p), ctypes.byref(rl))
        return p.value != 0
    except: pass
    return False

def _dbg_flags():
    try:
        f = ctypes.c_ulong(0); rl = ctypes.c_ulong(0)
        ntdll.NtQueryInformationProcess(k32.GetCurrentProcess(), 0x1F,
            ctypes.byref(f), ctypes.sizeof(f), ctypes.byref(rl))
        return f.value == 0
    except: pass
    return False

def _dbg_hwbp():
    try:
        class CTX(ctypes.Structure):
            _fields_ = [("F",ctypes.c_ulong),("P",ctypes.c_ubyte*200),
                        ("Dr0",ctypes.c_ulonglong),("Dr1",ctypes.c_ulonglong),
                        ("Dr2",ctypes.c_ulonglong),("Dr3",ctypes.c_ulonglong)]
        c = CTX(); c.F = 0x00010010
        if k32.GetThreadContext(k32.GetCurrentThread(), ctypes.byref(c)):
            return any([c.Dr0, c.Dr1, c.Dr2, c.Dr3])
    except: pass
    return False

def _dbg_timing():
    t1 = time.perf_counter_ns()
    x = sum(i*i for i in range(5000))
    t2 = time.perf_counter_ns()
    return (t2-t1)/1_000_000 > 150

def _dbg_output():
    try:
        k32.SetLastError(0)
        k32.OutputDebugStringW("bstep")
        return k32.GetLastError() != 0
    except: pass
    return False

def _dbg_close_handle():
    """CloseHandle trick — invalid handle raises exception under debugger."""
    try:
        k32.CloseHandle(ctypes.c_void_p(0x99999999))
        return False  # no exception = no debugger
    except:
        return True   # exception = debugger

def check_debug():
    for fn in [_dbg_api, _dbg_peb, _dbg_port, _dbg_flags,
               _dbg_hwbp, _dbg_timing, _dbg_output, _dbg_close_handle]:
        try:
            if fn(): return True
        except: pass
    return False


# ═══════════════════════════════════════════
#  2. ANTI-DECOMPILE + IMPORT BLOCKER
# ═══════════════════════════════════════════

_BLOCKED = frozenset({
    'uncompyle6','decompyle3','xdis','spark_parser','pycdc','pydumpck',
    'pycdas','bytecode','dis','inspect','pdb','bdb','trace','pydevd',
    'debugpy','_pydevd_bundle','pyinstxtractor','code','codeop',
    'compileall','py_compile',
})

class _ImportBlocker:
    def find_module(self, name, path=None):
        if name.split('.')[0] in _BLOCKED: return self
    def load_module(self, name):
        raise ImportError(f"Blocked: {name}")

def protect_imports():
    sys.meta_path.insert(0, _ImportBlocker())

def protect_trace():
    noop = lambda *a, **kw: None
    sys.settrace = noop
    sys.setprofile = noop
    try: threading.settrace = noop; threading.setprofile = noop
    except: pass


# ═══════════════════════════════════════════
#  3. ANTI-PYINSTEXTRACTOR
# ═══════════════════════════════════════════

def check_pyinstxtractor():
    if not getattr(sys, 'frozen', False): return False
    mei = getattr(sys, '_MEIPASS', '')
    if not mei: return False
    import tempfile
    if not mei.startswith(tempfile.gettempdir()): return True
    # Check extraction artifacts
    parent = os.path.dirname(mei)
    for name in ["PYZ-00.pyz_extracted","pyimod01_os_path.pyc",
                 "pyimod02_archive.pyc","pyimod03_importers.pyc"]:
        if os.path.exists(os.path.join(parent, name)): return True
    return False

def protect_pyinstaller():
    if not getattr(sys, 'frozen', False): return
    # Verify exe integrity
    try:
        if not os.path.isfile(sys.executable): os._exit(1)
    except: pass


# ═══════════════════════════════════════════
#  4. ANTI-PROCESS (40+ tools)
# ═══════════════════════════════════════════

_BAD = [
    # Debuggers
    "x64dbg.exe","x32dbg.exe","ollydbg.exe","windbg.exe","immunitydebugger.exe",
    "idaq.exe","idaq64.exe","ida.exe","ida64.exe",
    # RE
    "ghidra.exe","ghidrarun.exe","radare2.exe","r2.exe","rizin.exe",
    "cutter.exe","binaryninja.exe","hopper.exe",
    # Memory
    "cheatengine-x86_64.exe","cheatengine.exe","artmoney.exe","tsearch.exe",
    "processhacker.exe","procmon.exe","procmon64.exe",
    "procexp.exe","procexp64.exe","systemexplorer.exe",
    # Dumpers
    "procdump.exe","procdump64.exe","dumpcap.exe","rawshark.exe",
    # .NET/Python decompilers
    "dnspy.exe","dnspy-x86.exe","ilspy.exe","dotpeek.exe","justdecompile.exe",
    "de4dot.exe","pyinstxtractor.exe",
    # Patchers/Hex
    "lordpe.exe","pe-bear.exe","pestudio.exe","cff explorer.exe",
    "hxd.exe","010editor.exe","hexworkshop.exe",
    # API monitors
    "apimonitor-x64.exe","apimonitor-x86.exe","rohitab.exe",
    # HTTP
    "fiddler.exe","charles.exe","httpdebuggerpro.exe","httpdebuggerui.exe",
    # Import reconstructors
    "scylla.exe","scylla_x64.exe","importrec.exe",
    # Sniffers
    "wireshark.exe","tcpview.exe","tcpvcon.exe",
    # Sandboxes
    "sandboxie.exe","sbiectrl.exe","sbiedll.dll",
    # Misc RE
    "resourcehacker.exe","reshacker.exe","depends.exe","dumpbin.exe",
]

_BAD_TITLES = [
    "x64dbg","x32dbg","ollydbg","windbg","immunity","ida ",
    "ghidra","cheat engine","process hacker","process monitor",
    "process explorer","system explorer",
    "dnspy","dotpeek","ilspy","de4dot","api monitor",
    "http debugger","scylla","import reconstructor",
    "pyinstxtractor","uncompyle","decompyle","binary ninja",
    "hopper","radare","rizin","cutter",
    "resource hacker","hex workshop","010 editor",
]

def check_processes():
    try:
        out = subprocess.run(["tasklist","/FO","CSV","/NH"],
            capture_output=True, text=True, timeout=5,
            creationflags=0x08000000).stdout.lower()
        for p in _BAD:
            if p.lower() in out: return True
    except: pass
    return False

def check_windows():
    found = [False]
    def cb(hwnd, _):
        if not u32.IsWindowVisible(hwnd): return True
        n = u32.GetWindowTextLengthW(hwnd)
        if n == 0: return True
        buf = ctypes.create_unicode_buffer(n+1)
        u32.GetWindowTextW(hwnd, buf, n+1)
        t = buf.value.lower()
        for b in _BAD_TITLES:
            if b in t: found[0] = True; return False
        return True
    WEP = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    try: u32.EnumWindows(WEP(cb), 0)
    except: pass
    return found[0]


# ═══════════════════════════════════════════
#  5. ANTI-TAMPER (SHA256)
# ═══════════════════════════════════════════

_hashes = {}

def init_integrity():
    global _hashes
    base = os.path.dirname(os.path.abspath(__file__))
    for f in _SELF_FILES:
        fp = os.path.join(base, f)
        if os.path.exists(fp):
            with open(fp, "rb") as fh:
                _hashes[f] = hashlib.sha256(fh.read()).hexdigest()

def check_integrity():
    if not _hashes: return False
    base = os.path.dirname(os.path.abspath(__file__))
    for f, h in _hashes.items():
        fp = os.path.join(base, f)
        if os.path.exists(fp):
            with open(fp, "rb") as fh:
                if hashlib.sha256(fh.read()).hexdigest() != h: return True
    return False


# ═══════════════════════════════════════════
#  6. ANTI-HOOK (API integrity)
# ═══════════════════════════════════════════

def check_hooks():
    try:
        for fn in [k32.IsDebuggerPresent, ntdll.NtQueryInformationProcess,
                   k32.CheckRemoteDebuggerPresent, k32.GetThreadContext,
                   ntdll.NtClose, k32.CloseHandle]:
            addr = ctypes.cast(fn, ctypes.POINTER(ctypes.c_ubyte))
            # JMP=0xE9, INT3=0xCC, NOP=0x90, PUSH+RET=0x68
            if addr[0] in (0xE9, 0xCC, 0x90, 0x68): return True
    except: pass
    return False


# ═══════════════════════════════════════════
#  7. ANTI-DUMP (memory protection)
# ═══════════════════════════════════════════

def protect_memory():
    """Erase PE header from memory — dump tools get corrupt exe."""
    try:
        if not getattr(sys, 'frozen', False): return
        # Get base address of our exe in memory
        base = k32.GetModuleHandleW(None)
        if not base: return
        # Read DOS header to find PE header size
        old = ctypes.c_ulong(0)
        # Change first page to RW, zero it, restore protection
        # This erases DOS/PE header so memory dumps are invalid
        if k32.VirtualProtect(base, 4096, 0x04, ctypes.byref(old)):  # PAGE_READWRITE
            ctypes.memset(base, 0, 4096)
            k32.VirtualProtect(base, 4096, old.value, ctypes.byref(old))
    except: pass


# ═══════════════════════════════════════════
#  8. ANTI-VM / SANDBOX
# ═══════════════════════════════════════════

def check_vm():
    """Detect if running in VM/Sandbox (crackers often use VMs)."""
    # Registry keys that indicate VM
    import winreg
    vm_keys = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\VMware, Inc.\VMware Tools"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Oracle\VirtualBox Guest Additions"),
        (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\VBoxGuest"),
        (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\vmci"),
        (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\vmhgfs"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Virtual Machine\Guest\Parameters"),
    ]
    for hive, path in vm_keys:
        try:
            winreg.OpenKey(hive, path, 0, winreg.KEY_READ)
            return True
        except: pass

    # Check for VM-specific files
    vm_files = [
        r"C:\Windows\System32\drivers\vmmouse.sys",
        r"C:\Windows\System32\drivers\vmhgfs.sys",
        r"C:\Windows\System32\drivers\VBoxMouse.sys",
        r"C:\Windows\System32\drivers\VBoxGuest.sys",
        r"C:\Windows\System32\VBoxService.exe",
        r"C:\Windows\System32\vboxdisp.dll",
    ]
    for f in vm_files:
        if os.path.exists(f): return True

    # Check MAC address prefix (VM vendors have known prefixes)
    try:
        out = subprocess.run(["getmac","/FO","CSV","/NH"],
            capture_output=True, text=True, timeout=5,
            creationflags=0x08000000).stdout.upper()
        vm_macs = ["00-05-69","00-0C-29","00-1C-14","00-50-56",  # VMware
                   "08-00-27","0A-00-27",  # VirtualBox
                   "00-15-5D",  # Hyper-V
                   "00-16-3E"]  # Xen
        for mac in vm_macs:
            if mac in out: return True
    except: pass

    # Check for Sandboxie
    try:
        sbie = ctypes.windll.LoadLibrary("SbieDll.dll")
        if sbie: return True
    except: pass

    return False


# ═══════════════════════════════════════════
#  9. ANTI-DLL-INJECTION
# ═══════════════════════════════════════════

_SUSPICIOUS_DLLS = [
    "sbiedll.dll",       # Sandboxie
    "dbghelp.dll",       # Debugger helper (normal but suspicious if injected)
    "api_log.dll",       # API logging
    "dir_watch.dll",     # Directory watcher
    "pstorec.dll",       # Password store
    "vmcheck.dll",       # VM check
    "cmdvrt32.dll",      # Comodo sandbox
    "cmdvrt64.dll",
    "cuckoomon.dll",     # Cuckoo sandbox
    "guard32.dll",       # Comodo
    "sample.dll",        # Generic suspicious
    "snxhk.dll",         # Avast sandbox
    "snxhk64.dll",
]

def check_dll_injection():
    """Check for suspicious DLLs loaded in our process."""
    try:
        import ctypes.wintypes
        h_snap = k32.CreateToolhelp32Snapshot(0x00000008, 0)  # TH32CS_SNAPMODULE
        if h_snap == -1: return False

        class MODULEENTRY32W(ctypes.Structure):
            _fields_ = [("dwSize", ctypes.c_ulong),
                        ("th32ModuleID", ctypes.c_ulong),
                        ("th32ProcessID", ctypes.c_ulong),
                        ("GlblcntUsage", ctypes.c_ulong),
                        ("ProccntUsage", ctypes.c_ulong),
                        ("modBaseAddr", ctypes.c_void_p),
                        ("modBaseSize", ctypes.c_ulong),
                        ("hModule", ctypes.c_void_p),
                        ("szModule", ctypes.c_wchar * 256),
                        ("szExePath", ctypes.c_wchar * 260)]

        me = MODULEENTRY32W()
        me.dwSize = ctypes.sizeof(me)
        if k32.Module32FirstW(h_snap, ctypes.byref(me)):
            while True:
                mod_name = me.szModule.lower()
                for sus in _SUSPICIOUS_DLLS:
                    if sus in mod_name:
                        k32.CloseHandle(h_snap)
                        return True
                if not k32.Module32NextW(h_snap, ctypes.byref(me)):
                    break
        k32.CloseHandle(h_snap)
    except: pass
    return False


# ═══════════════════════════════════════════
# 10. ANTI-ATTACH (hide from debugger)
# ═══════════════════════════════════════════

def protect_anti_attach():
    """
    NtSetInformationThread — ThreadHideFromDebugger
    Once set, the thread becomes invisible to debuggers.
    Attaching a debugger after this = instant crash.
    """
    try:
        # ThreadHideFromDebugger = 0x11
        ntdll.NtSetInformationThread(
            k32.GetCurrentThread(),
            0x11,  # ThreadHideFromDebugger
            None,
            0
        )
    except: pass


# ═══════════════════════════════════════════
# 11. PARENT PROCESS CHECK
# ═══════════════════════════════════════════

def check_parent():
    """Verify parent process is not a RE tool."""
    try:
        # Get parent PID via NtQueryInformationProcess
        class PBI(ctypes.Structure):
            _fields_ = [("R1",ctypes.c_void_p),("Peb",ctypes.c_void_p),
                        ("R2",ctypes.c_void_p*2),("Uid",ctypes.c_void_p),
                        ("InheritedFromUniqueProcessId",ctypes.c_void_p)]
        pbi = PBI(); rl = ctypes.c_ulong(0)
        ntdll.NtQueryInformationProcess(k32.GetCurrentProcess(), 0,
            ctypes.byref(pbi), ctypes.sizeof(pbi), ctypes.byref(rl))
        ppid = pbi.InheritedFromUniqueProcessId

        if ppid:
            # Open parent and get its name
            h = k32.OpenProcess(0x0400 | 0x0010, False, ppid)  # PROCESS_QUERY_INFORMATION | PROCESS_VM_READ
            if h:
                buf = ctypes.create_unicode_buffer(260)
                size = ctypes.c_ulong(260)
                k32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(size))
                k32.CloseHandle(h)
                pname = os.path.basename(buf.value).lower()
                bad_parents = ["x64dbg.exe","x32dbg.exe","ollydbg.exe","windbg.exe",
                               "ida.exe","ida64.exe","idaq.exe","idaq64.exe",
                               "ghidra.exe","radare2.exe","processhacker.exe",
                               "dnspy.exe","binaryninja.exe"]
                return pname in bad_parents
    except: pass
    return False


# ═══════════════════════════════════════════
# 12. KERNEL DEBUGGER DETECTION
# ═══════════════════════════════════════════

def check_kernel_debugger():
    """Detect kernel-mode debugger (WinDbg kernel mode)."""
    try:
        class SYSTEM_KERNEL_DEBUGGER_INFORMATION(ctypes.Structure):
            _fields_ = [("KernelDebuggerEnabled", ctypes.c_ubyte),
                        ("KernelDebuggerNotPresent", ctypes.c_ubyte)]
        info = SYSTEM_KERNEL_DEBUGGER_INFORMATION()
        rl = ctypes.c_ulong(0)
        # SystemKernelDebuggerInformation = 0x23
        ntdll.NtQuerySystemInformation(0x23, ctypes.byref(info),
            ctypes.sizeof(info), ctypes.byref(rl))
        return info.KernelDebuggerEnabled != 0
    except: pass
    return False


# ═══════════════════════════════════════════
# 13. SELF-CHECKSUM (exe integrity)
# ═══════════════════════════════════════════

_exe_hash = ""

def init_exe_checksum():
    """Hash our own exe at startup."""
    global _exe_hash
    if getattr(sys, 'frozen', False):
        try:
            with open(sys.executable, "rb") as f:
                _exe_hash = hashlib.sha256(f.read()).hexdigest()
        except: pass

def check_exe_checksum():
    """Verify exe hasn't been patched."""
    if not _exe_hash: return False
    try:
        with open(sys.executable, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest() != _exe_hash
    except: return False


# ═══════════════════════════════════════════
# 14. ENV VAR + PYTHON FLAG CHECKS
# ═══════════════════════════════════════════

def check_env():
    dbg_envs = [
        "PYDEVD_USE_CYTHON","PYDEVD_DISABLE_FILE_VALIDATION",
        "DEBUGPY_LAUNCHER_PORT","PYDEVD_LOAD_VALUES_ASYNC",
        "_PYDEV_TRACE_SETTRACE","PYCHARM_DEBUG",
        "VSCODE_PID","TERM_PROGRAM_VERSION",
    ]
    for e in dbg_envs:
        if os.environ.get(e): return True
    return sys.flags.debug or sys.flags.inspect


# ═══════════════════════════════════════════
# 15. CODE SCRAMBLE
# ═══════════════════════════════════════════

def scramble_code():
    """Overwrite co_filename on all loaded function objects."""
    for name, mod in list(sys.modules.items()):
        if mod is None or name.startswith(('_','builtins','ctypes','tkinter','json','os','sys')): continue
        for attr in dir(mod):
            try:
                obj = getattr(mod, attr)
                if isinstance(obj, types.FunctionType) and hasattr(obj, '__code__'):
                    obj.__code__ = obj.__code__.replace(co_filename="<\u2588>")
            except: pass


# ═══════════════════════════════════════════
# 16. STACK PROTECTION
# ═══════════════════════════════════════════

def protect_exceptions():
    """Install exception hook that suppresses file paths in tracebacks."""
    def _hook(exc_type, exc_value, exc_tb):
        # Only show exception type and message, no file paths
        sys.stderr.write(f"Error: {exc_type.__name__}: {exc_value}\n")
    sys.excepthook = _hook


# ═══════════════════════════════════════════
# 17. ADDITIONAL: Prevent __code__ access
# ═══════════════════════════════════════════

def protect_code_access():
    """Make it harder to read function bytecode."""
    try:
        # Delete __code__ attribute from builtins
        # (won't fully work but adds friction)
        pass
    except: pass
    # Disable compile() for arbitrary code
    import builtins
    _orig_compile = builtins.compile
    def _safe_compile(source, filename, mode, *args, **kwargs):
        # Block compiling our protected files
        if isinstance(filename, str) and any(f in filename for f in _SELF_FILES):
            raise PermissionError("Access denied")
        return _orig_compile(source, filename, mode, *args, **kwargs)
    builtins.compile = _safe_compile


# ═══════════════════════════════════════════
#  MASTER CHECK
# ═══════════════════════════════════════════

class GuardStatus:
    __slots__ = ('debug','tamper','process','hook','window','extract',
                 'env','vm','dll_inject','parent','kernel_dbg','exe_patch')
    def __init__(self):
        for s in self.__slots__: setattr(self, s, False)

    @property
    def safe(self):
        return not any(getattr(self, s) for s in self.__slots__)

    @property
    def threats(self):
        return [s for s in self.__slots__ if getattr(self, s)]


def full_check() -> GuardStatus:
    g = GuardStatus()
    g.debug      = check_debug()
    g.tamper     = check_integrity()
    g.process    = check_processes()
    g.hook       = check_hooks()
    g.window     = check_windows()
    g.extract    = check_pyinstxtractor()
    g.env        = check_env()
    g.dll_inject = check_dll_injection()
    g.parent     = check_parent()
    g.kernel_dbg = check_kernel_debugger()
    g.exe_patch  = check_exe_checksum()
    # VM check is optional — uncomment if you want to block VMs too:
    # g.vm       = check_vm()
    return g


# ═══════════════════════════════════════════
#  INIT + HEARTBEAT
# ═══════════════════════════════════════════

_running = False

def init():
    """Call once at startup — arm all protections."""
    init_integrity()
    init_exe_checksum()
    protect_imports()
    protect_trace()
    protect_pyinstaller()
    protect_anti_attach()
    protect_exceptions()
    protect_code_access()
    protect_memory()

    # Initial scan
    s = full_check()
    if not s.safe:
        os._exit(1)


def start_heartbeat(on_detect=None):
    global _running
    if _running: return
    _running = True

    def loop():
        strikes = 0
        while _running:
            time.sleep(_HEARTBEAT_SEC)
            s = full_check()
            if not s.safe:
                strikes += 1
                if strikes >= _MAX_STRIKES:
                    if on_detect: on_detect(s.threats)
                    else: os._exit(1)
                    return
            else:
                strikes = max(0, strikes - 1)

    threading.Thread(target=loop, daemon=True).start()


def stop_heartbeat():
    global _running; _running = False


def apply_post_freeze():
    """Call after all modules loaded."""
    try: scramble_code()
    except: pass
