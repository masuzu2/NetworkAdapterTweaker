"""
Network Adapter Tweaker — Main GUI
The best NIC tweaker. Period.
"""

import sys
import os
import threading
import json
import time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

try:
    import customtkinter as ctk
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    CTK = True
except ImportError:
    CTK = False

# ── Platform guard ──
if sys.platform != "win32":
    if CTK:
        root = ctk.CTk()
        root.withdraw()
    else:
        root = tk.Tk()
        root.withdraw()
    messagebox.showerror("Error", "This tool only works on Windows.")
    sys.exit(1)

import adapter as backend

# ── Colors ──
C = {
    "bg":       "#0a0e1a",
    "panel":    "#0d1220",
    "header":   "#0f1729",
    "border":   "#1a2744",
    "input":    "#080c19",
    "text":     "#c8d6e5",
    "dim":      "#5a6a80",
    "label":    "#8899aa",
    "cyan":     "#00d4ff",
    "green":    "#00ff88",
    "orange":   "#ffaa00",
    "red":      "#ff4466",
    "blue":     "#3388ff",
    "purple":   "#aa66ff",
    "yellow":   "#ffdd00",
    "hover":    "#111d33",
}

# ── Setting definitions ──
RSS_FIELDS = [
    ("Enabled",               "Status",                True, ["True", "False"]),
    ("NumberOfReceiveQueues",  "NumberOfReceiveQueues",  False, []),
    ("Profile",                "Profile",               True, ["NUMAStatic", "NUMAScalingStatic", "ConservativeScaling", "ClosestProcessor"]),
    ("BaseProcessorNumber",    "BaseProcessor",          False, []),
    ("MaxProcessorNumber",     "MaxProcessor",           False, []),
    ("MaxProcessors",          "MaxProcessors",          False, []),
]

GLOBAL_FIELDS = [
    ("ReceiveSideScaling",           "ReceiveSideScaling",          True, ["Enabled", "Disabled"]),
    ("ReceiveSegmentCoalescing",     "ReceiveSegmentCoalescing",    True, ["Enabled", "Disabled"]),
    ("Chimney",                      "Chimney",                     True, ["Enabled", "Disabled", "Automatic"]),
    ("TaskOffload",                  "TaskOffload",                 True, ["Enabled", "Disabled"]),
    ("NetworkDirect",                "NetworkDirect",               True, ["Enabled", "Disabled"]),
    ("NetworkDirectAcrossIPSubnets", "NetworkDirectAcrossIPSubnets",True, ["Allowed", "Blocked"]),
    ("PacketCoalescingFilter",       "PacketCoalescingFilter",      True, ["Enabled", "Disabled"]),
]

IFACE_FIELDS = [
    ("AdvertiseDefaultRoute",   "AdvertiseDefaultRoute",   True, ["Enabled", "Disabled"]),
    ("Advertising",             "Advertising",             True, ["Enabled", "Disabled"]),
    ("AutomaticMetric",         "AutomaticMetric",         True, ["Enabled", "Disabled"]),
    ("ClampMss",                "ClampMss",                True, ["Enabled", "Disabled"]),
    ("DirectedMacWolPattern",   "DirectedMacWolPattern",   True, ["Enabled", "Disabled"]),
    ("EcnMarking",              "EcnMarking",              True, ["Disabled", "UseEct1", "UseEct0", "AppDecide"]),
    ("ForceArpNdWolPattern",    "ForceArpNdWolPattern",    True, ["Enabled", "Disabled"]),
    ("Forwarding",              "Forwarding",              True, ["Enabled", "Disabled"]),
    ("IgnoreDefaultRoutes",     "IgnoreDefaultRoutes",     True, ["Enabled", "Disabled"]),
    ("ManagedAddressConfiguration","ManagedAddressConfiguration", True, ["Enabled", "Disabled"]),
    ("NeighborDiscoverySupported", "NeighborDiscoverySupported",   True, ["Yes", "No"]),
    ("NeighborUnreachabilityDetection","NeighborUnreachDetection", True, ["Enabled", "Disabled"]),
    ("OtherStatefulConfiguration","OtherStatefulConfiguration",    True, ["Enabled", "Disabled"]),
    ("RouterDiscovery",         "RouterDiscovery",         True, ["Enabled", "Disabled", "ControlledByDHCP"]),
    ("Store",                   "Store",                   True, ["ActiveStore", "PersistentStore"]),
    ("WeakHostReceive",         "WeakHostReceive",         True, ["Enabled", "Disabled"]),
    ("WeakHostSend",            "WeakHostSend",            True, ["Enabled", "Disabled"]),
    ("CurrentHopLimit",         "CurrentHopLimit",         False, []),
    ("BaseReachableTime",       "BaseReachableTime (ms)",  False, []),
    ("RetransmitTime",          "RetransmitTime (ms)",     False, []),
    ("ReachableTime",           "ReachableTime (ms)",      False, []),
    ("DadRetransmitTime",       "DadRetransmitTime",       False, []),
    ("DadTransmits",            "DadTransmits",            False, []),
    ("NlMtu",                   "NlMtu (bytes)",           False, []),
]

ADV_KEYS = [
    ("*FlowControl",            "FlowControl"),
    ("*IPChecksumOffloadIPv4",   "IPChecksumOffloadIPv4"),
    ("*TCPChecksumOffloadIPv4",  "TCPChecksumOffloadIPv4"),
    ("*TCPChecksumOffloadIPv6",  "TCPChecksumOffloadIPv6"),
    ("*UDPChecksumOffloadIPv4",  "UDPChecksumOffloadIPv4"),
    ("*UDPChecksumOffloadIPv6",  "UDPChecksumOffloadIPv6"),
    ("*LsoV1IPv4",               "LsoV1IPv4"),
    ("*LsoV2IPv4",               "LsoV2IPv4"),
    ("*LsoV2IPv6",               "LsoV2IPv6"),
    ("*PMARPOffload",            "PMARPOffload"),
    ("*PMNSOffload",             "PMNSOffload"),
    ("*PriorityVLANTag",         "PriorityVLANTag"),
    ("*ReceiveBuffers",          "ReceiveBuffers"),
    ("*TransmitBuffers",         "TransmitBuffers"),
    ("*InterruptModeration",     "InterruptModeration"),
    ("ITR",                      "InterruptModerationRate"),
    ("TxIntDelay",               "TxIntDelay"),
    ("PacketDirect",             "PacketDirect"),
    ("*RSS",                     "RSS"),
]

TWEAK_KEYS = [
    "DefaultReceiveWindow", "DefaultSendWindow", "BufferMultiplier", "BufferAlignment",
    "DoNotHoldNicBuffers", "SmallBufferSize", "MediumBufferSize", "LargeBufferSize",
    "HugeBufferSize", "SmallBufferListDepth", "MediumBufferListDepth", "LargeBufferListDepth",
    "DisableAddressSharing", "DisableChainedReceive", "DisableDirectAcceptEx",
    "DisableRawSecurity", "DynamicSendBufferDisable", "FastSendDatagramThreshold",
    "FastCopyReceiveThreshold", "IgnorePushBitOnReceives", "IgnoreOrderlyRelease",
    "TransmitWorker", "PriorityBoost",
]

POWER_KEYS = [
    ("*PMAPowerManagement",    "(APM) sleep states"),
    ("DynamicPowerGating",     "DynamicPowerGating"),
    ("ConnectedPowerGating",   "ConnectedPowerGating"),
    ("AutoPowerSaveModeEnabled","AutoPowerSaveMode"),
    ("NicAutoPowerSaver",      "NicAutoPowerSaver"),
    ("DelayedPowerUpEn",       "DelayedPowerUp"),
    ("ReduceSpeedOnPowerDown", "ReduceSpeedOnPowerDown"),
    ("*WakeOnMagicPacket",     "WakeOnMagicPacket"),
    ("*WakeOnPattern",         "WakeOnPattern"),
    ("WakeOnLink",             "WakeOnLink"),
    ("*EEE",                   "Energy Efficient Ethernet"),
    ("EnableGreenEthernet",    "GreenEthernet"),
]


# ╔═══════════════════════════════════════════════════════╗
#  ScrollableSection — a panel with header + scrollable rows
# ╚═══════════════════════════════════════════════════════╝
class ScrollableSection(ctk.CTkFrame if CTK else tk.Frame):
    def __init__(self, master, title, color=None, **kw):
        bg = C["panel"]
        super().__init__(master, fg_color=bg, corner_radius=6, **kw) if CTK else super().__init__(master, bg=bg, **kw)
        self.color = color or C["cyan"]
        self.widgets = {}  # key -> widget (CTkComboBox / CTkEntry)

        # Header
        hdr = ctk.CTkFrame(self, fg_color=C["header"], corner_radius=0, height=28) if CTK else tk.Frame(self, bg=C["header"], height=28)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        lbl = ctk.CTkLabel(hdr, text=f"  {title}", font=("Consolas", 12, "bold"), text_color=self.color, anchor="w") if CTK else tk.Label(hdr, text=f"  {title}", font=("Consolas", 10, "bold"), fg=self.color, bg=C["header"], anchor="w")
        lbl.pack(side="left", fill="x", expand=True)
        self.apply_btn = ctk.CTkButton(hdr, text="Apply", width=50, height=22, font=("Segoe UI", 10, "bold"), fg_color=C["input"], hover_color=C["hover"], text_color=self.color, border_width=1, border_color=self.color, corner_radius=3) if CTK else tk.Button(hdr, text="Apply", font=("Segoe UI", 8), fg=self.color, bg=C["input"])
        self.apply_btn.pack(side="right", padx=4, pady=2)

        # Scrollable body
        self.body = ctk.CTkScrollableFrame(self, fg_color=bg, corner_radius=0, scrollbar_button_color=C["border"], scrollbar_button_hover_color=C["cyan"]) if CTK else tk.Frame(self, bg=bg)
        self.body.pack(fill="both", expand=True, padx=1, pady=(0, 1))

    def add_row(self, key, label, value="", is_combo=False, options=None, color=None):
        """Add a setting row. Returns the widget."""
        clr = color or self.color
        row = ctk.CTkFrame(self.body, fg_color="transparent", height=24) if CTK else tk.Frame(self.body, bg=C["panel"], height=24)
        row.pack(fill="x", padx=2, pady=0)

        lbl = ctk.CTkLabel(row, text=label, font=("Segoe UI", 11), text_color=C["label"], anchor="w", width=160) if CTK else tk.Label(row, text=label, font=("Segoe UI", 9), fg=C["label"], bg=C["panel"], anchor="w", width=20)
        lbl.pack(side="left", padx=(6, 4))

        if is_combo and options:
            w = ctk.CTkComboBox(row, values=options, width=140, height=22, font=("Consolas", 11), dropdown_font=("Consolas", 11), fg_color=C["input"], border_color=C["border"], button_color=C["border"], button_hover_color=C["cyan"], text_color=clr, dropdown_fg_color=C["input"], dropdown_text_color=clr, dropdown_hover_color=C["hover"], corner_radius=3, state="readonly") if CTK else ttk.Combobox(row, values=options, width=18, state="readonly")
            if value and value in options:
                w.set(value)
            elif value:
                # Add current value if not in options
                new_opts = list(options) + [value]
                if CTK:
                    w.configure(values=new_opts)
                else:
                    w["values"] = new_opts
                w.set(value)
            elif options:
                w.set(options[0])
        else:
            w = ctk.CTkEntry(row, width=140, height=22, font=("Consolas", 11), fg_color=C["input"], border_color=C["border"], text_color=clr, corner_radius=3, justify="right") if CTK else tk.Entry(row, width=18, font=("Consolas", 9), bg=C["input"], fg=clr, justify="right", insertbackground=clr)
            if value:
                w.insert(0, value)

        w.pack(side="right", padx=(4, 6))
        self.widgets[key] = w
        return w

    def get_values(self) -> dict:
        result = {}
        for key, w in self.widgets.items():
            if CTK:
                val = w.get()
            elif isinstance(w, ttk.Combobox):
                val = w.get()
            else:
                val = w.get()
            if val:
                result[key] = val
        return result

    def set_apply_command(self, cmd):
        if CTK:
            self.apply_btn.configure(command=cmd)
        else:
            self.apply_btn.configure(command=cmd)


# ╔═══════════════════════════════════════════════════════╗
#  Main Application
# ╚═══════════════════════════════════════════════════════╝
class NATweakerApp:
    def __init__(self):
        # Window
        if CTK:
            self.root = ctk.CTk()
            self.root.configure(fg_color=C["bg"])
        else:
            self.root = tk.Tk()
            self.root.configure(bg=C["bg"])
        self.root.title("Network Adapter - Tweaker")
        self.root.geometry("1400x860")
        self.root.minsize(1000, 600)

        # State
        self.adapters = []
        self.current_adapter = ""
        self.adv_props = []
        self.ipv4 = True
        self.rss_data = {}
        self.global_data = {}
        self.iface_data = {}
        self.tweak_data = {}

        # Sections
        self.sec_rss = None
        self.sec_global = None
        self.sec_iface = None
        self.sec_adv = None
        self.sec_tweaks = None
        self.sec_power = None

        self._build_ui()
        self._load_adapters()

    def _build_ui(self):
        # ─── Top Bar ───
        top = ctk.CTkFrame(self.root, fg_color=C["header"], height=60, corner_radius=0) if CTK else tk.Frame(self.root, bg=C["header"], height=60)
        top.pack(fill="x")
        top.pack_propagate(False)

        # Row 1: Adapter + buttons
        row1 = ctk.CTkFrame(top, fg_color="transparent") if CTK else tk.Frame(top, bg=C["header"])
        row1.pack(fill="x", padx=8, pady=(6, 0))

        lbl = ctk.CTkLabel(row1, text="Adapter:", font=("Segoe UI", 12, "bold"), text_color=C["dim"]) if CTK else tk.Label(row1, text="Adapter:", font=("Segoe UI", 10, "bold"), fg=C["dim"], bg=C["header"])
        lbl.pack(side="left")

        self.adapter_var = tk.StringVar()
        if CTK:
            self.adapter_combo = ctk.CTkComboBox(row1, variable=self.adapter_var, width=320, height=26, font=("Segoe UI", 11, "bold"), fg_color=C["cyan"], text_color="#000000", button_color="#00aacc", dropdown_fg_color=C["panel"], dropdown_text_color=C["cyan"], dropdown_hover_color=C["hover"], corner_radius=4, state="readonly", command=self._on_adapter_change)
        else:
            self.adapter_combo = ttk.Combobox(row1, textvariable=self.adapter_var, width=40, state="readonly")
            self.adapter_combo.bind("<<ComboboxSelected>>", self._on_adapter_change)
        self.adapter_combo.pack(side="left", padx=(6, 8))

        btns = [
            ("Open",            self._open_ncpa,     C["text"],   C["border"]),
            ("Apply All",       self._apply_all,     C["green"],  "#003322"),
            ("Restart Adapter", self._restart,       C["orange"], "#332200"),
            ("Gaming Preset",   self._preset_gaming, C["purple"], "#220033"),
            ("Export",          self._export,        C["blue"],   "#001133"),
            ("Import",          self._import,        C["yellow"], "#332200"),
        ]
        for text, cmd, fg, bg in btns:
            if CTK:
                b = ctk.CTkButton(row1, text=text, width=len(text)*9+20, height=26, font=("Segoe UI", 11, "bold"), fg_color=bg, hover_color=C["hover"], text_color=fg, border_width=1, border_color=fg, corner_radius=4, command=cmd)
            else:
                b = tk.Button(row1, text=text, font=("Segoe UI", 8, "bold"), fg=fg, bg=bg, command=cmd, bd=1)
            b.pack(side="left", padx=2)

        # Row 2: Meta info
        row2 = ctk.CTkFrame(top, fg_color="transparent") if CTK else tk.Frame(top, bg=C["header"])
        row2.pack(fill="x", padx=8, pady=(2, 0))
        self.meta_lbl = ctk.CTkLabel(row2, text="Select an adapter to begin", font=("Consolas", 10), text_color=C["dim"], anchor="w") if CTK else tk.Label(row2, text="Select an adapter to begin", font=("Consolas", 8), fg=C["dim"], bg=C["header"], anchor="w")
        self.meta_lbl.pack(side="left")

        # ─── Status Bar ───
        self.status_bar = ctk.CTkLabel(self.root, text="Ready", font=("Consolas", 10), text_color=C["dim"], fg_color=C["header"], anchor="w", height=22) if CTK else tk.Label(self.root, text="Ready", font=("Consolas", 8), fg=C["dim"], bg=C["header"], anchor="w")
        self.status_bar.pack(side="bottom", fill="x")

        # ─── Main Columns ───
        self.main_frame = ctk.CTkFrame(self.root, fg_color=C["bg"], corner_radius=0) if CTK else tk.Frame(self.root, bg=C["bg"])
        self.main_frame.pack(fill="both", expand=True, padx=0, pady=0)
        for i in range(4):
            self.main_frame.columnconfigure(i, weight=1)
        self.main_frame.rowconfigure(0, weight=1)

    def _build_sections(self):
        """Build/rebuild all section panels with current data."""
        for w in self.main_frame.winfo_children():
            w.destroy()

        adv_map = {p.keyword: p for p in self.adv_props}

        # ── Column 0: RSS ──
        col0 = ctk.CTkFrame(self.main_frame, fg_color=C["bg"], corner_radius=0) if CTK else tk.Frame(self.main_frame, bg=C["bg"])
        col0.grid(row=0, column=0, sticky="nsew", padx=(2, 1), pady=2)

        self.sec_rss = ScrollableSection(col0, "RSS Settings", C["cyan"])
        self.sec_rss.pack(fill="both", expand=True, pady=(0, 2))
        for key, label, is_combo, opts in RSS_FIELDS:
            val = self.rss_data.get(key, "")
            self.sec_rss.add_row(key, label, val, is_combo, opts)
        self.sec_rss.set_apply_command(self._apply_rss)

        # RSS extra buttons
        btn_frame = ctk.CTkFrame(col0, fg_color=C["panel"], height=30, corner_radius=4) if CTK else tk.Frame(col0, bg=C["panel"], height=30)
        btn_frame.pack(fill="x", pady=(0, 2))
        if CTK:
            ctk.CTkButton(btn_frame, text="Unlock RSSQueues", width=130, height=22, font=("Segoe UI", 10, "bold"), fg_color=C["input"], hover_color=C["hover"], text_color=C["cyan"], border_width=1, border_color=C["cyan"], corner_radius=3, command=self._unlock_rss).pack(side="left", padx=4, pady=4)
        else:
            tk.Button(btn_frame, text="Unlock RSSQueues", command=self._unlock_rss).pack(side="left", padx=4)

        # ── Column 1: Global + Interface ──
        col1 = ctk.CTkFrame(self.main_frame, fg_color=C["bg"], corner_radius=0) if CTK else tk.Frame(self.main_frame, bg=C["bg"])
        col1.grid(row=0, column=1, sticky="nsew", padx=1, pady=2)

        self.sec_global = ScrollableSection(col1, "Global Settings", C["purple"])
        self.sec_global.pack(fill="x", pady=(0, 2))
        for key, label, is_combo, opts in GLOBAL_FIELDS:
            val = self.global_data.get(key, "")
            self.sec_global.add_row(key, label, val, is_combo, opts, C["purple"])
        self.sec_global.set_apply_command(self._apply_global)

        # IPv4/IPv6 toggle
        proto_frame = ctk.CTkFrame(col1, fg_color=C["panel"], height=28, corner_radius=4) if CTK else tk.Frame(col1, bg=C["panel"])
        proto_frame.pack(fill="x", pady=(0, 2))
        self.ipv4_var = tk.BooleanVar(value=self.ipv4)
        if CTK:
            ctk.CTkCheckBox(proto_frame, text="IPv4", variable=self.ipv4_var, font=("Segoe UI", 11), text_color=C["text"], command=self._toggle_proto, checkbox_width=16, checkbox_height=16, corner_radius=3).pack(side="left", padx=8, pady=4)
        else:
            tk.Checkbutton(proto_frame, text="IPv4", variable=self.ipv4_var, command=self._toggle_proto, bg=C["panel"], fg=C["text"], selectcolor=C["input"]).pack(side="left", padx=4)

        self.sec_iface = ScrollableSection(col1, "Interface Settings", C["green"])
        self.sec_iface.pack(fill="both", expand=True, pady=(0, 2))
        for key, label, is_combo, opts in IFACE_FIELDS:
            val = self.iface_data.get(key, "")
            self.sec_iface.add_row(key, label, val, is_combo, opts, C["green"])
        self.sec_iface.set_apply_command(self._apply_iface)

        # ── Column 2: Adv + Power ──
        col2 = ctk.CTkFrame(self.main_frame, fg_color=C["bg"], corner_radius=0) if CTK else tk.Frame(self.main_frame, bg=C["bg"])
        col2.grid(row=0, column=2, sticky="nsew", padx=1, pady=2)

        self.sec_adv = ScrollableSection(col2, "Adv. Adapter", C["cyan"])
        self.sec_adv.pack(fill="both", expand=True, pady=(0, 2))
        for kw, label in ADV_KEYS:
            prop = adv_map.get(kw)
            val = prop.display_value if prop else ""
            is_combo = bool(prop and prop.valid_display)
            opts = prop.valid_display if prop else []
            self.sec_adv.add_row(kw, label, val, is_combo, opts)
        self.sec_adv.set_apply_command(self._apply_adv)

        self.sec_power = ScrollableSection(col2, "PowerSaving Settings", C["red"])
        self.sec_power.pack(fill="x", pady=(0, 2))
        for kw, label in POWER_KEYS:
            prop = adv_map.get(kw)
            val = prop.display_value if prop else ""
            is_combo = bool(prop and prop.valid_display)
            opts = prop.valid_display if prop else []
            self.sec_power.add_row(kw, label, val, is_combo, opts, C["red"])
        self.sec_power.set_apply_command(self._apply_power)

        # ── Column 3: Tweaks ──
        col3 = ctk.CTkFrame(self.main_frame, fg_color=C["bg"], corner_radius=0) if CTK else tk.Frame(self.main_frame, bg=C["bg"])
        col3.grid(row=0, column=3, sticky="nsew", padx=(1, 2), pady=2)

        self.sec_tweaks = ScrollableSection(col3, "Tweaks (AFD Registry)", C["orange"])
        self.sec_tweaks.pack(fill="both", expand=True, pady=(0, 2))
        for key in TWEAK_KEYS:
            val = self.tweak_data.get(key, "")
            self.sec_tweaks.add_row(key, key, val, False, [], C["orange"])
        self.sec_tweaks.set_apply_command(self._apply_tweaks)

    # ─── Data Loading ───
    def _load_adapters(self):
        self._status("Loading adapters...")
        def work():
            self.adapters = backend.get_adapters()
            self.root.after(0, self._populate_adapters)
        threading.Thread(target=work, daemon=True).start()

    def _populate_adapters(self):
        names = [a.display() for a in self.adapters]
        if CTK:
            self.adapter_combo.configure(values=names)
        else:
            self.adapter_combo["values"] = names
        if self.adapters:
            first = self.adapters[0]
            self.adapter_var.set(first.display())
            self._select_adapter(first.name)
        else:
            self._status("No adapters found")

    def _on_adapter_change(self, *args):
        display = self.adapter_var.get()
        for a in self.adapters:
            if a.display() == display:
                self._select_adapter(a.name)
                return

    def _select_adapter(self, name):
        self.current_adapter = name
        self._status(f"Loading settings for {name}...")
        def work():
            self.rss_data = backend.get_rss(name)
            self.global_data = backend.get_global()
            self.iface_data = backend.get_interface(name, "IPv4" if self.ipv4 else "IPv6")
            self.adv_props = backend.get_adv_properties(name)
            self.tweak_data = backend.get_afd_tweaks()
            reg_path = backend.get_adapter_reg_path(name)
            info = next((a for a in self.adapters if a.name == name), None)
            self.root.after(0, lambda: self._on_data_loaded(info, reg_path))
        threading.Thread(target=work, daemon=True).start()

    def _on_data_loaded(self, info, reg_path):
        meta = f"Registry: {reg_path}"
        if info:
            meta += f"   |   NDIS: {info.ndis}   |   MAC: {info.mac}   |   Speed: {info.speed}   |   Driver: {info.driver}"
        if CTK:
            self.meta_lbl.configure(text=meta)
        else:
            self.meta_lbl.config(text=meta)
        self._build_sections()
        self._status("Ready")

    def _toggle_proto(self):
        self.ipv4 = self.ipv4_var.get()
        if self.current_adapter:
            self.iface_data = backend.get_interface(self.current_adapter, "IPv4" if self.ipv4 else "IPv6")
            self._build_sections()

    # ─── Apply handlers ───
    def _apply_in_thread(self, label, func, *args):
        self._status(f"Applying {label}...")
        def work():
            try:
                result = func(*args)
                self.root.after(0, lambda: self._status(f"{label}: Done!"))
            except Exception as e:
                self.root.after(0, lambda: self._status(f"{label}: Error - {e}"))
        threading.Thread(target=work, daemon=True).start()

    def _apply_rss(self):
        vals = self.sec_rss.get_values()
        self._apply_in_thread("RSS", backend.set_rss, self.current_adapter, vals)

    def _apply_global(self):
        vals = self.sec_global.get_values()
        self._apply_in_thread("Global", backend.set_global, vals)

    def _apply_iface(self):
        vals = self.sec_iface.get_values()
        fam = "IPv4" if self.ipv4 else "IPv6"
        self._apply_in_thread("Interface", backend.set_interface, self.current_adapter, fam, vals)

    def _apply_adv(self):
        vals = self.sec_adv.get_values()
        adv_map = {p.keyword: p for p in self.adv_props}
        def do():
            for kw, display_val in vals.items():
                prop = adv_map.get(kw)
                reg_val = display_val
                if prop:
                    for i, dv in enumerate(prop.valid_display):
                        if dv == display_val and i < len(prop.valid_registry):
                            reg_val = prop.valid_registry[i]
                            break
                backend.set_adv_property(self.current_adapter, kw, reg_val)
        self._apply_in_thread("Adv. Adapter", do)

    def _apply_power(self):
        vals = self.sec_power.get_values()
        adv_map = {p.keyword: p for p in self.adv_props}
        def do():
            for kw, display_val in vals.items():
                prop = adv_map.get(kw)
                reg_val = display_val
                if prop:
                    for i, dv in enumerate(prop.valid_display):
                        if dv == display_val and i < len(prop.valid_registry):
                            reg_val = prop.valid_registry[i]
                            break
                backend.set_adv_property(self.current_adapter, kw, reg_val)
        self._apply_in_thread("PowerSaving", do)

    def _apply_tweaks(self):
        vals = self.sec_tweaks.get_values()
        def do():
            for k, v in vals.items():
                if v:
                    try:
                        backend.set_afd_tweak(k, int(v))
                    except ValueError:
                        pass
        self._apply_in_thread("Tweaks", do)

    def _apply_all(self):
        self._status("Applying all settings...")
        def do():
            self._apply_rss()
            self._apply_global()
            self._apply_iface()
            self._apply_adv()
            self._apply_tweaks()
            self._apply_power()
            self.root.after(500, lambda: self._status("All settings applied!"))
        threading.Thread(target=do, daemon=True).start()

    def _restart(self):
        if not self.current_adapter:
            return
        self._apply_in_thread("Restart", backend.restart_adapter, self.current_adapter)

    def _unlock_rss(self):
        if not self.current_adapter:
            return
        self._apply_in_thread("Unlock RSS", backend.unlock_rss, self.current_adapter)
        self.root.after(2000, lambda: self._select_adapter(self.current_adapter))

    def _preset_gaming(self):
        if not self.current_adapter:
            return
        self._status("Applying Gaming preset...")
        def do():
            results = backend.apply_preset(self.current_adapter, backend.PRESET_GAMING)
            self.root.after(0, lambda: self._status(f"Gaming preset applied! ({len(results)} changes)"))
            self.root.after(500, lambda: self._select_adapter(self.current_adapter))
        threading.Thread(target=do, daemon=True).start()

    def _export(self):
        if not self.current_adapter:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".json", filetypes=[("JSON", "*.json")],
            initialfile=f"{self.current_adapter}_settings.json"
        )
        if path:
            ok = backend.export_settings(self.current_adapter, path)
            self._status(f"Export {'OK' if ok else 'FAILED'}: {path}")

    def _import(self):
        if not self.current_adapter:
            return
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if path:
            self._status("Importing settings...")
            def do():
                results = backend.import_settings(self.current_adapter, path)
                self.root.after(0, lambda: self._status(f"Import done! ({len(results)} changes)"))
                self.root.after(500, lambda: self._select_adapter(self.current_adapter))
            threading.Thread(target=do, daemon=True).start()

    def _open_ncpa(self):
        os.system("start ncpa.cpl")

    def _status(self, msg):
        if CTK:
            self.meta_lbl.configure(text=msg) if "Loading" in msg or "Select" in msg else None
            self.status_bar.configure(text=f"  {msg}")
        else:
            self.status_bar.config(text=f"  {msg}")

    def run(self):
        self.root.mainloop()


# ═══════════════════════════════════════════════════════
#  Entry
# ═══════════════════════════════════════════════════════
if __name__ == "__main__":
    # Request admin if not already
    if not backend.is_admin():
        try:
            backend.run_as_admin()
        except Exception:
            pass
        sys.exit(0)

    app = NATweakerApp()
    app.run()
