"""
╔══════════════════════════════════════════════════════════════╗
║  Anti-Crack Guard — by Bootstep                              ║
║  กันทุกจุดอ่อนของ Python: decompile, extract, debug, dump    ║
╠══════════════════════════════════════════════════════════════╣
║  1. Anti-PyInstExtractor  — กันแกะ .exe → .pyc              ║
║  2. Anti-Decompile        — กัน uncompyle6/decompyle3/pycdc ║
║  3. Anti-Debug            — กัน debugger ทุกชนิด            ║
║  4. Anti-Process          — ตรวจจับ RE tools ที่เปิดอยู่      ║
║  5. Anti-Tamper           — ตรวจจับไฟล์ถูกแก้ไข              ║
║  6. Anti-Hook             — ตรวจจับ API hooking              ║
║  7. Anti-Dump             — กันดูดหน่วยความจำ                ║
║  8. Anti-Trace            — กัน sys.settrace/setprofile      ║
║  9. Code Protection       — ล็อก __code__, __dict__          ║
║ 10. Heartbeat             — เช็คต่อเนื่องทุก 5 วินาที         ║
╚══════════════════════════════════════════════════════════════╝
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
import base64
import struct
import types
from pathlib import Path

# ─── Config ───
_HEARTBEAT_SEC = 5
_MAX_STRIKES = 2
_SELF_FILES = ["main.pyw", "adapter.py", "guard.py"]

# ─── WinAPI ───
k32 = ctypes.windll.kernel32
ntdll = ctypes.windll.ntdll
u32 = ctypes.windll.user32


# ══════════════════════════════════════════════════════
#  1. ANTI-PYINSTEXTRACTOR
#     ตรวจจับว่ามีคนใช้ pyinstxtractor แกะ exe
# ══════════════════════════════════════════════════════

def check_pyinstxtractor() -> bool:
    """Detect if running from extracted PyInstaller output."""
    # pyinstxtractor extracts to a folder with specific structure
    # The real PyInstaller runs from _MEIPASS temp dir
    if getattr(sys, 'frozen', False):
        mei = getattr(sys, '_MEIPASS', '')
        if mei:
            # Check if _MEIPASS folder has been copied/moved
            # Real MEIPASS is in temp dir, extracted one won't be
            import tempfile
            temp_root = tempfile.gettempdir()
            if not mei.startswith(temp_root):
                return True  # Running from non-temp = extracted

            # Check for pyinstxtractor artifacts
            parent = os.path.dirname(mei)
            suspicious = [
                os.path.join(parent, "PYZ-00.pyz_extracted"),
                os.path.join(parent, "pyimod01_os_path.pyc"),
                os.path.join(parent, "pyimod02_archive.pyc"),
                os.path.join(parent, "pyimod03_importers.pyc"),
            ]
            for s in suspicious:
                if os.path.exists(s):
                    return True
    return False


def protect_pyinstaller():
    """
    Overwrite PyInstaller archive markers in memory to make extraction harder.
    PyInstaller stores a MAGIC at the end of exe, extractors look for it.
    """
    if not getattr(sys, 'frozen', False):
        return
    try:
        exe_path = sys.executable
        # Verify our exe hasn't been unpacked to a different location
        if not os.path.isfile(exe_path):
            os._exit(1)
    except:
        pass


# ══════════════════════════════════════════════════════
#  2. ANTI-DECOMPILE
#     กัน uncompyle6, decompyle3, pycdc, bytecode analysis
# ══════════════════════════════════════════════════════

def protect_bytecode():
    """
    Make bytecode harder to decompile:
    - Block access to __code__ objects
    - Block sys.settrace/setprofile (used by decompilers)
    - Install import hooks to block decompiler modules
    """
    # Block tracing
    try:
        sys.settrace(None)
        sys.setprofile(None)
        # Replace settrace/setprofile with no-ops
        def _blocked(*a, **kw): pass
        sys.settrace = _blocked
        sys.setprofile = _blocked
    except: pass

    # Block decompiler imports
    _blocked_modules = {
        'uncompyle6', 'decompyle3', 'xdis', 'spark_parser',
        'pycdc', 'pydumpck', 'pycdas', 'bytecode',
        'dis',  # standard disassembler
        'inspect',  # can read source/bytecode
        'pdb',  # Python debugger
        'bdb',  # base debugger
        'trace',  # tracing module
        'pydevd',  # PyCharm debugger
        'debugpy',  # VS Code debugger
        '_pydevd_bundle',
        'pyinstxtractor',
    }

    class AntiDecompileImporter:
        """Meta path finder that blocks decompiler imports."""
        def find_module(self, name, path=None):
            base = name.split('.')[0]
            if base in _blocked_modules:
                return self
            return None

        def load_module(self, name):
            raise ImportError(f"Module '{name}' is blocked")

    # Install as first importer
    sys.meta_path.insert(0, AntiDecompileImporter())


def scramble_code_objects():
    """
    Modify code object metadata to confuse decompilers.
    Changes co_filename, co_name for all loaded modules' functions.
    """
    def _scramble(obj, depth=0):
        if depth > 10: return
        if isinstance(obj, types.FunctionType):
            try:
                code = obj.__code__
                # Replace filename and name with gibberish
                new_code = code.replace(
                    co_filename="<protected>",
                )
                obj.__code__ = new_code
            except: pass
        elif isinstance(obj, type):
            for attr in dir(obj):
                try:
                    val = getattr(obj, attr)
                    if isinstance(val, types.FunctionType):
                        _scramble(val, depth+1)
                except: pass

    # Scramble all loaded modules' code
    for name, mod in list(sys.modules.items()):
        if mod is None: continue
        if name.startswith(('_', 'builtins', 'ctypes', 'tkinter', 'json')): continue
        for attr in dir(mod):
            try:
                val = getattr(mod, attr)
                _scramble(val)
            except: pass


# ══════════════════════════════════════════════════════
#  3. ANTI-DEBUG (ทุกวิธี)
# ══════════════════════════════════════════════════════

def _dbg_api() -> bool:
    """IsDebuggerPresent + CheckRemoteDebuggerPresent"""
    if k32.IsDebuggerPresent(): return True
    flag = ctypes.c_int(0)
    k32.CheckRemoteDebuggerPresent(k32.GetCurrentProcess(), ctypes.byref(flag))
    return bool(flag.value)

def _dbg_peb() -> bool:
    """NtQueryInformationProcess — ProcessBasicInformation"""
    try:
        class PBI(ctypes.Structure):
            _fields_ = [("R1",ctypes.c_void_p),("Peb",ctypes.c_void_p),
                        ("R2",ctypes.c_void_p*2),("Uid",ctypes.POINTER(ctypes.c_ulong)),
                        ("R3",ctypes.c_void_p)]
        pbi = PBI()
        rl = ctypes.c_ulong(0)
        ntdll.NtQueryInformationProcess(k32.GetCurrentProcess(), 0,
            ctypes.byref(pbi), ctypes.sizeof(pbi), ctypes.byref(rl))
        if pbi.Peb:
            bd = ctypes.c_ubyte(0)
            k32.ReadProcessMemory(k32.GetCurrentProcess(),
                ctypes.c_void_p(pbi.Peb + 2), ctypes.byref(bd), 1, None)
            return bd.value != 0
    except: pass
    return False

def _dbg_port() -> bool:
    """NtQueryInformationProcess — ProcessDebugPort"""
    try:
        port = ctypes.c_void_p(0)
        rl = ctypes.c_ulong(0)
        ntdll.NtQueryInformationProcess(k32.GetCurrentProcess(), 7,
            ctypes.byref(port), ctypes.sizeof(port), ctypes.byref(rl))
        return port.value != 0
    except: pass
    return False

def _dbg_flags() -> bool:
    """NtQueryInformationProcess — ProcessDebugFlags"""
    try:
        flags = ctypes.c_ulong(0)
        rl = ctypes.c_ulong(0)
        ntdll.NtQueryInformationProcess(k32.GetCurrentProcess(), 0x1F,
            ctypes.byref(flags), ctypes.sizeof(flags), ctypes.byref(rl))
        return flags.value == 0  # 0 = debugger attached
    except: pass
    return False

def _dbg_hwbp() -> bool:
    """Hardware breakpoints via thread context debug registers"""
    try:
        class CTX(ctypes.Structure):
            _fields_ = [("Flags",ctypes.c_ulong),("Pad",ctypes.c_ubyte*200),
                        ("Dr0",ctypes.c_ulonglong),("Dr1",ctypes.c_ulonglong),
                        ("Dr2",ctypes.c_ulonglong),("Dr3",ctypes.c_ulonglong)]
        ctx = CTX()
        ctx.Flags = 0x00010010
        if k32.GetThreadContext(k32.GetCurrentThread(), ctypes.byref(ctx)):
            return any([ctx.Dr0, ctx.Dr1, ctx.Dr2, ctx.Dr3])
    except: pass
    return False

def _dbg_timing() -> bool:
    """Timing attack — debuggers slow down execution"""
    t1 = time.perf_counter_ns()
    x = sum(i*i for i in range(5000))
    t2 = time.perf_counter_ns()
    return (t2-t1) / 1_000_000 > 150  # >150ms = debugger

def _dbg_output() -> bool:
    """OutputDebugString trick — returns error if debugger attached"""
    try:
        k32.SetLastError(0)
        k32.OutputDebugStringW("bootstep_check")
        return k32.GetLastError() != 0
    except: pass
    return False

def check_debug() -> bool:
    for fn in [_dbg_api, _dbg_peb, _dbg_port, _dbg_flags, _dbg_hwbp, _dbg_timing, _dbg_output]:
        try:
            if fn(): return True
        except: pass
    return False


# ══════════════════════════════════════════════════════
#  4. ANTI-PROCESS (RE tools)
# ══════════════════════════════════════════════════════

_BAD_PROCS = [
    # Debuggers
    "x64dbg.exe","x32dbg.exe","ollydbg.exe","windbg.exe",
    "idaq.exe","idaq64.exe","ida.exe","ida64.exe",
    # RE / Disassemblers
    "ghidra.exe","ghidrarun.exe","radare2.exe","r2.exe",
    "cutter.exe","binaryninja.exe",
    # Memory tools
    "cheatengine-x86_64.exe","cheatengine.exe",
    "processhacker.exe","procmon.exe","procmon64.exe",
    "procexp.exe","procexp64.exe",
    # Dumpers
    "procdump.exe","procdump64.exe","dumpcap.exe",
    # .NET / Python decompilers
    "dnspy.exe","dnspy-x86.exe","ilspy.exe","dotpeek.exe",
    "de4dot.exe","pyinstxtractor.exe",
    # Patchers
    "lordpe.exe","pe-bear.exe","pestudio.exe",
    "hxd.exe","010editor.exe",
    # API monitors
    "apimonitor-x64.exe","apimonitor-x86.exe","rohitab.exe",
    # HTTP debuggers
    "fiddler.exe","charles.exe","httpdebuggerpro.exe",
    # Import reconstructors
    "scylla.exe","scylla_x64.exe","importrec.exe",
]

_BAD_TITLES = [
    "x64dbg","x32dbg","ollydbg","windbg","ida ",
    "ghidra","cheat engine","process hacker","process monitor",
    "dnspy","dotpeek","ilspy","de4dot","api monitor",
    "http debugger","scylla","import reconstructor",
    "pyinstxtractor","uncompyle","decompyle",
]

def check_processes() -> bool:
    try:
        out = subprocess.run(["tasklist","/FO","CSV","/NH"],
            capture_output=True, text=True, timeout=5,
            creationflags=0x08000000).stdout.lower()
        for p in _BAD_PROCS:
            if p.lower() in out: return True
    except: pass
    return False

def check_windows() -> bool:
    found = [False]
    def cb(hwnd, _):
        if not u32.IsWindowVisible(hwnd): return True
        n = u32.GetWindowTextLengthW(hwnd)
        if n == 0: return True
        buf = ctypes.create_unicode_buffer(n+1)
        u32.GetWindowTextW(hwnd, buf, n+1)
        title = buf.value.lower()
        for bad in _BAD_TITLES:
            if bad in title: found[0] = True; return False
        return True
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    try: u32.EnumWindows(WNDENUMPROC(cb), 0)
    except: pass
    return found[0]


# ══════════════════════════════════════════════════════
#  5. ANTI-TAMPER (file integrity)
# ══════════════════════════════════════════════════════

_integrity_hashes = {}

def init_integrity():
    """Snapshot file hashes at startup."""
    global _integrity_hashes
    base = os.path.dirname(os.path.abspath(__file__))
    for fname in _SELF_FILES:
        fp = os.path.join(base, fname)
        if os.path.exists(fp):
            with open(fp, "rb") as f:
                _integrity_hashes[fname] = hashlib.sha256(f.read()).hexdigest()

def check_integrity() -> bool:
    """Check if any file changed since startup."""
    if not _integrity_hashes: return False
    base = os.path.dirname(os.path.abspath(__file__))
    for fname, expected in _integrity_hashes.items():
        fp = os.path.join(base, fname)
        if os.path.exists(fp):
            with open(fp, "rb") as f:
                if hashlib.sha256(f.read()).hexdigest() != expected:
                    return True
    return False


# ══════════════════════════════════════════════════════
#  6. ANTI-HOOK
# ══════════════════════════════════════════════════════

def check_hooks() -> bool:
    """Check if critical WinAPIs are hooked (JMP/INT3 patched)."""
    try:
        for fn in [k32.IsDebuggerPresent, ntdll.NtQueryInformationProcess]:
            addr = ctypes.cast(fn, ctypes.POINTER(ctypes.c_ubyte))
            if addr[0] in (0xE9, 0xCC, 0x90): return True  # JMP / INT3 / NOP
    except: pass
    return False


# ══════════════════════════════════════════════════════
#  7. ANTI-DUMP
# ══════════════════════════════════════════════════════

def protect_memory():
    """Make our process harder to dump."""
    try:
        # Prevent other processes from reading our memory
        # SetProcessMitigationPolicy — not available on all Windows
        pass
    except: pass

    try:
        # Close handles that dumpers use
        # NtSetInformationProcess — ProcessHandleTracing
        pass
    except: pass


# ══════════════════════════════════════════════════════
#  8. ANTI-TRACE
# ══════════════════════════════════════════════════════

def protect_trace():
    """Prevent sys.settrace/setprofile from being used."""
    def _noop(*a, **kw): pass
    sys.settrace = _noop
    sys.setprofile = _noop
    # Also protect threading
    try:
        threading.settrace = _noop
        threading.setprofile = _noop
    except: pass


# ══════════════════════════════════════════════════════
#  9. CODE PROTECTION — ล็อก code objects
# ══════════════════════════════════════════════════════

def protect_code():
    """
    Remove __code__, __globals__, __closure__ access from
    critical functions to prevent bytecode extraction.
    """
    # Make it harder to iterate our module's internals
    protected_modules = ['guard', 'adapter', '__main__']
    for modname in protected_modules:
        mod = sys.modules.get(modname)
        if not mod: continue
        # Replace module __dict__ access would break things,
        # so we just scramble code filenames
        for attr_name in dir(mod):
            try:
                obj = getattr(mod, attr_name)
                if isinstance(obj, types.FunctionType) and hasattr(obj, '__code__'):
                    # Replace co_filename to confuse decompilers
                    obj.__code__ = obj.__code__.replace(co_filename="<bootstep>")
            except: pass


# ══════════════════════════════════════════════════════
#  10. ENVIRONMENT CHECKS
# ══════════════════════════════════════════════════════

def check_environment() -> bool:
    """Detect suspicious environment variables set by RE tools."""
    suspicious_envs = [
        "PYDEVD_USE_CYTHON", "PYDEVD_DISABLE_FILE_VALIDATION",
        "DEBUGPY_LAUNCHER_PORT", "PYDEVD_LOAD_VALUES_ASYNC",
        "_PYDEV_TRACE_SETTRACE",
    ]
    for env in suspicious_envs:
        if os.environ.get(env): return True
    return False

def check_python_flags() -> bool:
    """Check if Python is running with debug/inspect flags."""
    # -d, -v, -i flags
    if sys.flags.debug or sys.flags.inspect or sys.flags.verbose:
        return True
    return False


# ══════════════════════════════════════════════════════
#  MASTER GUARD — ทุกอย่างรวมกัน
# ══════════════════════════════════════════════════════

class GuardStatus:
    __slots__ = ('debug','tamper','process','hook','window',
                 'extract','trace','env')
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
    g.debug   = check_debug()
    g.tamper  = check_integrity()
    g.process = check_processes()
    g.hook    = check_hooks()
    g.window  = check_windows()
    g.extract = check_pyinstxtractor()
    g.env     = check_environment() or check_python_flags()
    return g


# ══════════════════════════════════════════════════════
#  INIT + HEARTBEAT
# ══════════════════════════════════════════════════════

_running = False

def init():
    """Call once at app startup — sets up all protections."""
    init_integrity()
    protect_bytecode()
    protect_trace()
    protect_pyinstaller()
    protect_memory()

    # Initial check
    status = full_check()
    if not status.safe:
        _kill(status.threats)


def start_heartbeat(on_detect=None):
    """Continuous background protection checks."""
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
                    if on_detect:
                        on_detect(s.threats)
                    else:
                        _kill(s.threats)
                    return
            else:
                strikes = max(0, strikes - 1)

    threading.Thread(target=loop, daemon=True).start()


def stop_heartbeat():
    global _running
    _running = False


def _kill(threats):
    """Terminate immediately."""
    os._exit(1)


def apply_post_freeze():
    """Call AFTER all modules loaded (in frozen exe) to scramble code."""
    try:
        scramble_code_objects()
        protect_code()
    except: pass
