"""
Network Adapter Tweaker v2 — World-Class Edition
Dense dark UI matching the original screenshot pixel-for-pixel.
Uses ttk with custom dark theme for maximum speed + density.
"""
import sys, os, threading, tkinter as tk
from tkinter import ttk, messagebox, filedialog

if sys.platform != "win32":
    root = tk.Tk(); root.withdraw()
    messagebox.showerror("Error", "Windows only."); sys.exit(1)

import adapter as B

# ══════════════════════════════════════════════════
#  Theme
# ══════════════════════════════════════════════════
BG       = "#080c18"
PANEL    = "#0b1022"
HEADER   = "#0e1528"
BORDER   = "#162040"
INPUT_BG = "#060a14"
TXT      = "#b0c4de"
DIM      = "#4a5a70"
LBL      = "#7a8da0"
CYAN     = "#00d4ff"
GREEN    = "#00ff88"
ORANGE   = "#ffaa00"
RED      = "#ff4466"
BLUE     = "#3388ff"
PURPLE   = "#aa66ff"
YELLOW   = "#eedd44"
HOVER    = "#0f1a30"
ROW_H    = 22
FONT     = ("Segoe UI", 9)
FONT_B   = ("Segoe UI", 9, "bold")
FONT_M   = ("Consolas", 9)
FONT_S   = ("Segoe UI", 8)
FONT_H   = ("Consolas", 10, "bold")

def apply_dark_theme(root):
    s = ttk.Style(root)
    s.theme_use("clam")
    s.configure(".", background=BG, foreground=TXT, fieldbackground=INPUT_BG,
                borderwidth=0, font=FONT)
    s.configure("TFrame", background=BG)
    s.configure("TLabel", background=BG, foreground=TXT, font=FONT)
    s.configure("TButton", background=HEADER, foreground=CYAN, font=FONT_B,
                borderwidth=1, relief="solid", padding=(8,2))
    s.map("TButton", background=[("active", HOVER)], foreground=[("active", CYAN)])
    s.configure("TCombobox", fieldbackground=INPUT_BG, background=BORDER,
                foreground=CYAN, arrowcolor=CYAN, font=FONT_M, padding=1)
    s.map("TCombobox", fieldbackground=[("readonly", INPUT_BG)],
          foreground=[("readonly", CYAN)])
    s.configure("TEntry", fieldbackground=INPUT_BG, foreground=CYAN, font=FONT_M,
                insertcolor=CYAN, padding=1)
    s.configure("TCheckbutton", background=BG, foreground=TXT, font=FONT_S)
    s.map("TCheckbutton", background=[("active", BG)])
    s.configure("Vertical.TScrollbar", background=BORDER, troughcolor=BG,
                arrowcolor=DIM, borderwidth=0, width=8)
    s.map("Vertical.TScrollbar", background=[("active", CYAN)])
    # Section header styles
    for name, color in [("RSS",CYAN),("Global",PURPLE),("Iface",GREEN),
                         ("Adv",CYAN),("Tweak",ORANGE),("Power",RED)]:
        s.configure(f"{name}.TLabel", foreground=color, font=FONT_H, background=HEADER)
        s.configure(f"{name}Btn.TButton", foreground=color, background=INPUT_BG, font=FONT_S)
        s.map(f"{name}Btn.TButton", foreground=[("active", color)], background=[("active", HOVER)])
    root.option_add("*TCombobox*Listbox.background", INPUT_BG)
    root.option_add("*TCombobox*Listbox.foreground", CYAN)
    root.option_add("*TCombobox*Listbox.selectBackground", BORDER)
    root.option_add("*TCombobox*Listbox.font", FONT_M)

# ══════════════════════════════════════════════════
#  Setting Definitions
# ══════════════════════════════════════════════════
# (key, label, is_combo, options, tooltip)
RSS_FIELDS = [
    ("Enabled",              "Status:",              True, ["True","False"], "Enable/Disable RSS"),
    ("NumberOfReceiveQueues", "NumberOfReceiveQueues:", False, [], "Number of RSS queues"),
    ("Profile",              "Profile:",             True, ["NUMAStatic","NUMAScalingStatic","ConservativeScaling","ClosestProcessor"], "RSS CPU assignment profile"),
    ("BaseProcessorNumber",  "BaseProcessor:",       False, [], "First CPU core for RSS"),
    ("MaxProcessorNumber",   "MaxProcessor:",        False, [], "Last CPU core for RSS"),
    ("MaxProcessors",        "MaxProcessors:",       False, [], "Max CPUs per RSS queue"),
]
GLOBAL_FIELDS = [
    ("ReceiveSideScaling",           "ReceiveSideScaling:",          True, ["Enabled","Disabled"], "RSS global switch"),
    ("ReceiveSegmentCoalescing",     "ReceiveSegmentCoalescing:",    True, ["Enabled","Disabled"], "RSC — merges packets (disable for gaming)"),
    ("Chimney",                      "Chimney:",                     True, ["Enabled","Disabled","Automatic"], "TCP Chimney offload (deprecated)"),
    ("TaskOffload",                  "TaskOffload:",                 True, ["Enabled","Disabled"], "Hardware task offload"),
    ("NetworkDirect",                "NetworkDirect:",               True, ["Enabled","Disabled"], "RDMA support"),
    ("NetworkDirectAcrossIPSubnets", "NetworkDirectAcrossIPSubnets:",True, ["Allowed","Blocked"], "RDMA across subnets"),
    ("PacketCoalescingFilter",       "PacketCoalescingFilter:",      True, ["Enabled","Disabled"], "Coalesce packets (disable for gaming)"),
]
IFACE_FIELDS = [
    ("AdvertiseDefaultRoute",  "AdvertiseDefaultRoute:",  True, ["Enabled","Disabled"], ""),
    ("Advertising",            "Advertising:",            True, ["Enabled","Disabled"], ""),
    ("AutomaticMetric",        "AutomaticMetric:",        True, ["Enabled","Disabled"], "Auto metric for routing"),
    ("ClampMss",               "ClampMss:",               True, ["Enabled","Disabled"], ""),
    ("DirectedMacWolPattern",  "DirectedMacWolPattern:",  True, ["Enabled","Disabled"], ""),
    ("EcnMarking",             "EcnMarking:",             True, ["Disabled","UseEct1","UseEct0","AppDecide"], "Explicit Congestion Notification"),
    ("ForceArpNdWolPattern",   "ForceArpNdWolPattern:",   True, ["Enabled","Disabled"], ""),
    ("Forwarding",             "Forwarding:",             True, ["Enabled","Disabled"], "IP forwarding (router mode)"),
    ("IgnoreDefaultRoutes",    "IgnoreDefaultRoutes:",    True, ["Enabled","Disabled"], ""),
    ("ManagedAddressConfiguration","ManagedAddressConfig:", True, ["Enabled","Disabled"], ""),
    ("NeighborDiscoverySupported","NeighborDiscovery:",   True, ["Yes","No"], ""),
    ("NeighborUnreachabilityDetection","NeighborUnreachDet:", True, ["Enabled","Disabled"], ""),
    ("OtherStatefulConfiguration","OtherStatefulConfig:", True, ["Enabled","Disabled"], ""),
    ("RouterDiscovery",        "RouterDiscovery:",        True, ["Enabled","Disabled","ControlledByDHCP"], ""),
    ("Store",                  "Store:",                  True, ["ActiveStore","PersistentStore"], ""),
    ("WeakHostReceive",        "WeakHostReceive:",        True, ["Enabled","Disabled"], ""),
    ("WeakHostSend",           "WeakHostSend:",           True, ["Enabled","Disabled"], ""),
    ("CurrentHopLimit",        "CurrentHopLimit:",        False, [], "TTL value"),
    ("BaseReachableTime",      "BaseReachableTime:",      False, [], "ms"),
    ("RetransmitTime",         "RetransmitTime:",         False, [], "ms"),
    ("ReachableTime",          "ReachableTime:",          False, [], "ms"),
    ("DadRetransmitTime",      "DadRetransmitTime:",      False, [], ""),
    ("DadTransmits",           "DadTransmits:",           False, [], ""),
    ("NlMtu",                  "NlMtu:",                  False, [], "bytes"),
]
ADV_KEYS = [
    ("*FlowControl",           "FlowControl:",            "Flow control on NIC"),
    ("*IPChecksumOffloadIPv4",  "IPChecksumOffloadIPv4:",   "Hardware IP checksum"),
    ("*TCPChecksumOffloadIPv4", "TCPChecksumOffloadIPv4:",  "Hardware TCP checksum v4"),
    ("*TCPChecksumOffloadIPv6", "TCPChecksumOffloadIPv6:",  "Hardware TCP checksum v6"),
    ("*UDPChecksumOffloadIPv4", "UDPChecksumOffloadIPv4:",  "Hardware UDP checksum v4"),
    ("*UDPChecksumOffloadIPv6", "UDPChecksumOffloadIPv6:",  "Hardware UDP checksum v6"),
    ("*LsoV1IPv4",              "LsoV1IPv4:",               "Large Send Offload v1"),
    ("*LsoV2IPv4",              "LsoV2IPv4:",               "Large Send Offload v2 IPv4"),
    ("*LsoV2IPv6",              "LsoV2IPv6:",               "Large Send Offload v2 IPv6"),
    ("*PMARPOffload",           "PMARPOffload:",             "ARP offload for power mgmt"),
    ("*PMNSOffload",            "PMNSOffload:",              "NS offload for power mgmt"),
    ("*PriorityVLANTag",        "PriorityVLANTag:",          "802.1p/Q tagging"),
    ("*ReceiveBuffers",         "ReceiveBuffers:",            "RX ring buffer size"),
    ("*TransmitBuffers",        "TransmitBuffers:",           "TX ring buffer size"),
    ("*InterruptModeration",    "InterruptModeration:",       "Coalesce interrupts (off = low latency)"),
    ("ITR",                     "InterruptModerationRate:",   "Interrupts per second"),
    ("TxIntDelay",              "TxIntDelay:",                "TX interrupt delay"),
    ("PacketDirect",            "PacketDirect:",              "Kernel-bypass packets"),
    ("*RSS",                    "RSS:",                       "Receive Side Scaling on NIC"),
]
TWEAK_KEYS = [
    ("DefaultReceiveWindow",    "DefaultReceiveWindow:",     "AFD receive buffer (bytes)"),
    ("DefaultSendWindow",       "DefaultSendWindow:",        "AFD send buffer (bytes)"),
    ("BufferMultiplier",        "BufferMultiplier:",          "Buffer size multiplier"),
    ("BufferAlignment",         "BufferAlignment:",           "Memory alignment (bytes)"),
    ("DoNotHoldNicBuffers",     "DoNotHoldNICBuffers:",       "Release NIC buffers faster"),
    ("SmallBufferSize",         "SmallBufferSize:",           "Small buffer pool size"),
    ("MediumBufferSize",        "MediumBufferSize:",          "Medium buffer pool size"),
    ("LargeBufferSize",         "LargeBufferSize:",           "Large buffer pool size"),
    ("HugeBufferSize",          "HugeBufferSize:",            "Huge buffer pool size"),
    ("SmallBufferListDepth",    "SmallBufferListDepth:",      "Small buffer count"),
    ("MediumBufferListDepth",   "MediumBufferListDepth:",     "Medium buffer count"),
    ("LargeBufferListDepth",    "LargeBufferListDepth:",      "Large buffer count"),
    ("DisableAddressSharing",   "DisableAddressSharing:",     ""),
    ("DisableChainedReceive",   "DisableChainedReceive:",     ""),
    ("DisableDirectAcceptEx",   "DisableDirectAcceptEx:",     ""),
    ("DisableRawSecurity",      "DisableRawSecurity:",        ""),
    ("DynamicSendBufferDisable","DynamicSendBufferDisable:",  "Disable dynamic send buffer"),
    ("FastSendDatagramThreshold","FastSendDatagramThreshold:",""),
    ("FastCopyReceiveThreshold","FastCopyReceiveThreshold:",  ""),
    ("IgnorePushBitOnReceives", "IgnorePushBitOnReceives:",   "Ignore TCP PSH flag"),
    ("IgnoreOrderlyRelease",   "IgnoreOrderlyRelease:",      ""),
    ("TransmitWorker",          "TransmitWorker:",            ""),
    ("PriorityBoost",           "PriorityBoost:",             "Boost NIC thread priority"),
]
POWER_KEYS = [
    ("*PMAPowerManagement",     "(APM) sleep states:",        "Allow adapter to sleep"),
    ("DynamicPowerGating",      "DynamicPowerGating:",        "Dynamic power gating"),
    ("ConnectedPowerGating",    "ConnectedPowerGating:",      "Connected standby power"),
    ("AutoPowerSaveModeEnabled","AutoPowerSaveMode:",         "Auto power save"),
    ("NicAutoPowerSaver",       "NicAutoPowerSaver:",         "NIC auto power saver"),
    ("DelayedPowerUpEn",        "DelayedPowerUp:",            "Delay power up"),
    ("ReduceSpeedOnPowerDown",  "ReduceSpeedOnPowerDown:",    "Reduce link speed on sleep"),
    ("*WakeOnMagicPacket",      "WakeOnMagicPacket:",         "Wake-on-LAN magic packet"),
    ("*WakeOnPattern",          "WakeOnPattern:",             "Wake on pattern match"),
    ("WakeOnLink",              "WakeOnLink:",                "Wake on link change"),
    ("*EEE",                    "Energy Efficient Ethernet:", "IEEE 802.3az EEE"),
    ("EnableGreenEthernet",     "GreenEthernet:",             "Green Ethernet mode"),
]

# ══════════════════════════════════════════════════
#  Scrollable Panel
# ══════════════════════════════════════════════════
class ScrollPanel(tk.Frame):
    """A scrollable frame for dense setting rows."""
    def __init__(self, master, **kw):
        super().__init__(master, bg=PANEL, **kw)
        self.canvas = tk.Canvas(self, bg=PANEL, highlightthickness=0, bd=0)
        self.sb = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = tk.Frame(self.canvas, bg=PANEL)
        self.inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0,0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.sb.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.sb.pack(side="right", fill="y")
        self.canvas.bind_all("<MouseWheel>", self._on_mouse, add="+")
        self.widgets = {}

    def _on_mouse(self, e):
        # Only scroll if mouse is over this canvas
        w = e.widget
        while w:
            if w == self.canvas:
                self.canvas.yview_scroll(int(-1*(e.delta/120)), "units")
                return
            w = getattr(w, "master", None)

    def add_row(self, key, label_text, value="", is_combo=False, options=None, color=CYAN, tooltip=""):
        row = tk.Frame(self.inner, bg=PANEL, height=ROW_H)
        row.pack(fill="x", padx=0, pady=0)
        row.pack_propagate(False)
        # Hover
        def enter(e): row.configure(bg=HOVER); lbl.configure(bg=HOVER)
        def leave(e): row.configure(bg=PANEL); lbl.configure(bg=PANEL)
        row.bind("<Enter>", enter); row.bind("<Leave>", leave)

        lbl = tk.Label(row, text=label_text, font=FONT_S, fg=LBL, bg=PANEL, anchor="w")
        lbl.pack(side="left", padx=(6,2), fill="x", expand=True)
        lbl.bind("<Enter>", enter); lbl.bind("<Leave>", leave)

        if tooltip:
            self._add_tooltip(lbl, tooltip)

        if is_combo and options:
            var = tk.StringVar(value=value if value in options else (options[0] if options else ""))
            if value and value not in options:
                options = list(options) + [value]
                var.set(value)
            w = ttk.Combobox(row, textvariable=var, values=options, width=18,
                             state="readonly", font=FONT_M)
            w.pack(side="right", padx=(2,4), pady=1)
            self.widgets[key] = var
        else:
            var = tk.StringVar(value=value)
            w = ttk.Entry(row, textvariable=var, width=18, font=FONT_M, justify="right")
            w.pack(side="right", padx=(2,4), pady=1)
            self.widgets[key] = var

        # Separator line
        sep = tk.Frame(self.inner, bg=BORDER, height=1)
        sep.pack(fill="x")

    def _add_tooltip(self, widget, text):
        tip = None
        def show(e):
            nonlocal tip
            tip = tk.Toplevel(widget)
            tip.wm_overrideredirect(True)
            tip.wm_geometry(f"+{e.x_root+12}+{e.y_root+8}")
            tk.Label(tip, text=text, bg="#1a2a44", fg=CYAN, font=FONT_S,
                     padx=6, pady=3, relief="solid", bd=1).pack()
        def hide(e):
            nonlocal tip
            if tip: tip.destroy(); tip = None
        widget.bind("<Enter>", show, add="+")
        widget.bind("<Leave>", hide, add="+")

    def get_values(self):
        return {k: v.get() for k, v in self.widgets.items()}


# ══════════════════════════════════════════════════
#  Section Card
# ══════════════════════════════════════════════════
class SectionCard(tk.Frame):
    def __init__(self, master, title, style_name="RSS", **kw):
        super().__init__(master, bg=BG, **kw)
        self.style_name = style_name
        # Header
        hdr = tk.Frame(self, bg=HEADER, height=26)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text=f" {title}", font=FONT_H, fg={"RSS":CYAN,"Global":PURPLE,"Iface":GREEN,"Adv":CYAN,"Tweak":ORANGE,"Power":RED}.get(style_name,CYAN), bg=HEADER, anchor="w").pack(side="left", fill="x", expand=True)
        self.apply_btn = ttk.Button(hdr, text="Apply", style=f"{style_name}Btn.TButton", width=6)
        self.apply_btn.pack(side="right", padx=3, pady=2)
        # Body
        self.panel = ScrollPanel(self)
        self.panel.pack(fill="both", expand=True)
        # Border
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", side="bottom")

    def set_command(self, cmd):
        self.apply_btn.configure(command=cmd)


# ══════════════════════════════════════════════════
#  Main App
# ══════════════════════════════════════════════════
class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Network Adapter - Tweaker")
        self.root.geometry("1420x880")
        self.root.minsize(1000, 500)
        self.root.configure(bg=BG)
        apply_dark_theme(self.root)

        self.adapters = []
        self.cur = ""  # current adapter name
        self.adv_map = {}  # keyword -> AdvProp
        self.ipv4 = True

        self._build_topbar()
        self._build_statusbar()
        self._build_columns()
        self._load_adapters()

    # ── Top Bar ──
    def _build_topbar(self):
        top = tk.Frame(self.root, bg=HEADER, height=54)
        top.pack(fill="x")
        top.pack_propagate(False)

        r1 = tk.Frame(top, bg=HEADER)
        r1.pack(fill="x", padx=6, pady=(5,0))

        tk.Label(r1, text="Adapter:", font=FONT_B, fg=DIM, bg=HEADER).pack(side="left")
        self.adapter_var = tk.StringVar()
        self.adapter_cb = ttk.Combobox(r1, textvariable=self.adapter_var, width=38,
                                       state="readonly", font=("Segoe UI", 10, "bold"))
        self.adapter_cb.pack(side="left", padx=(4,8))
        self.adapter_cb.bind("<<ComboboxSelected>>", self._on_select)

        btns = [
            ("Open", self._open_ncpa, TXT, HEADER),
            ("Apply All", self._apply_all, GREEN, "#002211"),
            ("Restart Adapter", self._restart, ORANGE, "#221100"),
            ("Gaming", lambda: self._preset("gaming"), PURPLE, "#110022"),
            ("Streaming", lambda: self._preset("streaming"), BLUE, "#001122"),
            ("Default", lambda: self._preset("default"), DIM, HEADER),
            ("Export", self._export, YELLOW, "#222200"),
            ("Import", self._import, CYAN, "#002222"),
        ]
        for text, cmd, fg, bg_c in btns:
            b = tk.Button(r1, text=text, font=FONT_S, fg=fg, bg=bg_c, bd=1,
                          activebackground=HOVER, activeforeground=fg, cursor="hand2",
                          relief="solid", padx=6, pady=1, command=cmd)
            b.pack(side="left", padx=1)

        r2 = tk.Frame(top, bg=HEADER)
        r2.pack(fill="x", padx=8, pady=(3,0))
        self.meta_lbl = tk.Label(r2, text="Select an adapter...", font=("Consolas",8),
                                  fg=DIM, bg=HEADER, anchor="w")
        self.meta_lbl.pack(side="left", fill="x")

    # ── Status Bar ──
    def _build_statusbar(self):
        bar = tk.Frame(self.root, bg=HEADER, height=20)
        bar.pack(side="bottom", fill="x")
        bar.pack_propagate(False)
        self.status_lbl = tk.Label(bar, text="  Ready", font=("Consolas",8),
                                    fg=DIM, bg=HEADER, anchor="w")
        self.status_lbl.pack(side="left", fill="x")
        self.admin_lbl = tk.Label(bar, text="ADMIN" if B.is_admin() else "USER",
                                   font=("Consolas",8,"bold"),
                                   fg=GREEN if B.is_admin() else RED, bg=HEADER)
        self.admin_lbl.pack(side="right", padx=8)

    # ── 4 Columns ──
    def _build_columns(self):
        self.main = tk.Frame(self.root, bg=BG)
        self.main.pack(fill="both", expand=True)
        for i in range(4): self.main.columnconfigure(i, weight=1)
        self.main.rowconfigure(0, weight=1)

    def _build_sections(self, rss, glob, iface, afd):
        for w in self.main.winfo_children(): w.destroy()

        # ── Col 0: RSS ──
        c0 = tk.Frame(self.main, bg=BG)
        c0.grid(row=0, column=0, sticky="nsew", padx=(1,0))
        self.sec_rss = SectionCard(c0, "RSS Settings", "RSS")
        self.sec_rss.pack(fill="both", expand=True)
        for key, label, is_combo, opts, tip in RSS_FIELDS:
            self.sec_rss.panel.add_row(key, label, rss.get(key,""), is_combo, opts, CYAN, tip)
        self.sec_rss.set_command(self._apply_rss)

        # Extra: Unlock button
        bf = tk.Frame(c0, bg=PANEL, height=28)
        bf.pack(fill="x")
        bf.pack_propagate(False)
        tk.Button(bf, text="Unlock RSSQueues", font=FONT_S, fg=CYAN, bg=INPUT_BG,
                  bd=1, relief="solid", cursor="hand2", command=self._unlock_rss,
                  activebackground=HOVER, activeforeground=CYAN).pack(side="left", padx=4, pady=3)

        # ── Col 1: Global + Interface ──
        c1 = tk.Frame(self.main, bg=BG)
        c1.grid(row=0, column=1, sticky="nsew")
        # Global
        self.sec_global = SectionCard(c1, "Global Settings", "Global")
        self.sec_global.pack(fill="x")
        for key, label, is_combo, opts, tip in GLOBAL_FIELDS:
            self.sec_global.panel.add_row(key, label, glob.get(key,""), is_combo, opts, PURPLE, tip)
        self.sec_global.set_command(self._apply_global)

        # IPv4/IPv6
        pf = tk.Frame(c1, bg=PANEL, height=24)
        pf.pack(fill="x")
        pf.pack_propagate(False)
        self.ipv4_var = tk.BooleanVar(value=self.ipv4)
        tk.Checkbutton(pf, text="IPv4", variable=self.ipv4_var, font=FONT_S,
                       fg=TXT, bg=PANEL, selectcolor=INPUT_BG, activebackground=PANEL,
                       command=self._toggle_proto).pack(side="left", padx=6)

        # Interface
        self.sec_iface = SectionCard(c1, "Interface Settings", "Iface")
        self.sec_iface.pack(fill="both", expand=True)
        for key, label, is_combo, opts, tip in IFACE_FIELDS:
            self.sec_iface.panel.add_row(key, label, iface.get(key,""), is_combo, opts, GREEN, tip)
        self.sec_iface.set_command(self._apply_iface)

        # ── Col 2: Adv + Power ──
        c2 = tk.Frame(self.main, bg=BG)
        c2.grid(row=0, column=2, sticky="nsew")
        self.sec_adv = SectionCard(c2, "Adv. Adapter", "Adv")
        self.sec_adv.pack(fill="both", expand=True)
        for kw, label, tip in ADV_KEYS:
            prop = self.adv_map.get(kw)
            val = prop.display_value if prop else ""
            is_c = bool(prop and prop.valid_display)
            opts = prop.valid_display if prop else []
            self.sec_adv.panel.add_row(kw, label, val, is_c, opts, CYAN, tip)
        self.sec_adv.set_command(self._apply_adv)

        self.sec_power = SectionCard(c2, "PowerSaving Settings", "Power")
        self.sec_power.pack(fill="x")
        for kw, label, tip in POWER_KEYS:
            prop = self.adv_map.get(kw)
            val = prop.display_value if prop else ""
            is_c = bool(prop and prop.valid_display)
            opts = prop.valid_display if prop else []
            self.sec_power.panel.add_row(kw, label, val, is_c, opts, RED, tip)
        self.sec_power.set_command(self._apply_power)

        # ── Col 3: Tweaks ──
        c3 = tk.Frame(self.main, bg=BG)
        c3.grid(row=0, column=3, sticky="nsew", padx=(0,1))
        self.sec_tweak = SectionCard(c3, "Tweaks (AFD Registry)", "Tweak")
        self.sec_tweak.pack(fill="both", expand=True)
        for key, label, tip in TWEAK_KEYS:
            self.sec_tweak.panel.add_row(key, label, afd.get(key,""), False, [], ORANGE, tip)
        self.sec_tweak.set_command(self._apply_tweaks)

        # Separators between columns
        for i in range(1, 4):
            sep = tk.Frame(self.main, bg=BORDER, width=1)
            sep.place(relx=i/4, rely=0, relheight=1)

    # ── Data ──
    def _load_adapters(self):
        self._status("Loading adapters...")
        def work():
            self.adapters = B.get_adapters()
            self.root.after(0, self._populate)
        threading.Thread(target=work, daemon=True).start()

    def _populate(self):
        labels = [a.label() for a in self.adapters]
        self.adapter_cb["values"] = labels
        if self.adapters:
            self.adapter_var.set(labels[0])
            self._select(self.adapters[0].name)
        else:
            self._status("No adapters found")

    def _on_select(self, *_):
        disp = self.adapter_var.get()
        for a in self.adapters:
            if a.label() == disp:
                self._select(a.name); return

    def _select(self, name):
        self.cur = name
        self._status(f"Loading {name}...")
        def work():
            rss = B.get_rss(name)
            glob = B.get_global()
            iface = B.get_iface(name, "IPv4" if self.ipv4 else "IPv6")
            adv = B.get_adv_props(name)
            self.adv_map = {p.keyword: p for p in adv}
            afd = B.get_afd()
            reg = B.get_reg_path(name)
            info = next((a for a in self.adapters if a.name == name), None)
            self.root.after(0, lambda: self._loaded(rss, glob, iface, afd, info, reg))
        threading.Thread(target=work, daemon=True).start()

    def _loaded(self, rss, glob, iface, afd, info, reg):
        meta = f"Registry: {reg}"
        if info:
            meta += f"  |  NDIS: {info.ndis}  |  MAC: {info.mac}  |  Speed: {info.speed}  |  Driver: {info.driver}"
        self.meta_lbl.configure(text=meta)
        self._build_sections(rss, glob, iface, afd)
        self._status("Ready")

    def _toggle_proto(self):
        self.ipv4 = self.ipv4_var.get()
        if self.cur: self._select(self.cur)

    # ── Apply ──
    def _threaded(self, label, fn, *args, reload=False):
        self._status(f"Applying {label}...")
        def work():
            try:
                fn(*args)
                self.root.after(0, lambda: self._status(f"{label} applied!"))
                if reload:
                    import time; time.sleep(0.3)
                    self.root.after(0, lambda: self._select(self.cur))
            except Exception as e:
                self.root.after(0, lambda: self._status(f"{label} ERROR: {e}"))
        threading.Thread(target=work, daemon=True).start()

    def _apply_rss(self):
        vals = self.sec_rss.panel.get_values()
        self._threaded("RSS", B.set_rss, self.cur, vals)

    def _apply_global(self):
        vals = self.sec_global.panel.get_values()
        self._threaded("Global", B.set_global, vals)

    def _apply_iface(self):
        vals = self.sec_iface.panel.get_values()
        fam = "IPv4" if self.ipv4 else "IPv6"
        self._threaded("Interface", B.set_iface, self.cur, fam, vals)

    def _apply_adv(self):
        vals = self.sec_adv.panel.get_values()
        def do():
            for kw, dv in vals.items():
                prop = self.adv_map.get(kw)
                rv = prop.display_to_reg(dv) if prop else dv
                B.set_adv(self.cur, kw, rv)
        self._threaded("Adv. Adapter", do)

    def _apply_power(self):
        vals = self.sec_power.panel.get_values()
        def do():
            for kw, dv in vals.items():
                prop = self.adv_map.get(kw)
                rv = prop.display_to_reg(dv) if prop else dv
                B.set_adv(self.cur, kw, rv)
        self._threaded("PowerSaving", do)

    def _apply_tweaks(self):
        vals = self.sec_tweak.panel.get_values()
        def do():
            for k, v in vals.items():
                if v:
                    try: B.set_afd(k, int(v))
                    except: pass
        self._threaded("Tweaks", do)

    def _apply_all(self):
        self._status("Auto-backup + Apply All...")
        def do():
            B.auto_backup(self.cur)
            self._apply_rss()
            self._apply_global()
            self._apply_iface()
            self._apply_adv()
            self._apply_tweaks()
            self._apply_power()
            import time; time.sleep(1)
            self.root.after(0, lambda: self._status("All applied! (backup saved)"))
        threading.Thread(target=do, daemon=True).start()

    def _restart(self):
        if not self.cur: return
        self._status("Restarting adapter...")
        self._threaded("Restart", B.restart, self.cur, reload=True)

    def _unlock_rss(self):
        if not self.cur: return
        self._threaded("Unlock RSS", B.unlock_rss, self.cur, reload=True)

    def _preset(self, key):
        if not self.cur: return
        p = B.PRESETS[key]
        if messagebox.askyesno("Preset", f"Apply preset: {p['name']}?\n\n{p['desc']}\n\nAuto-backup will be created first."):
            self._status(f"Applying {p['name']}...")
            def do():
                B.auto_backup(self.cur)
                B.apply_preset(self.cur, key)
                import time; time.sleep(0.5)
                self.root.after(0, lambda: self._select(self.cur))
                self.root.after(0, lambda: self._status(f"Preset '{p['name']}' applied!"))
            threading.Thread(target=do, daemon=True).start()

    def _export(self):
        if not self.cur: return
        path = filedialog.asksaveasfilename(defaultextension=".json",
            filetypes=[("JSON","*.json")], initialfile=f"{self.cur}_settings.json")
        if path:
            B.export_all(self.cur, path)
            self._status(f"Exported to {path}")

    def _import(self):
        if not self.cur: return
        path = filedialog.askopenfilename(filetypes=[("JSON","*.json")])
        if path:
            self._status("Importing...")
            def do():
                B.auto_backup(self.cur)
                n = B.import_all(self.cur, path)
                self.root.after(0, lambda: self._select(self.cur))
                self.root.after(0, lambda: self._status(f"Imported {n} settings"))
            threading.Thread(target=do, daemon=True).start()

    def _open_ncpa(self): os.system("start ncpa.cpl")

    def _status(self, msg):
        self.status_lbl.configure(text=f"  {msg}")

    def run(self):
        self.root.mainloop()


# ══════════════════════════════════════════════════
if __name__ == "__main__":
    if not B.is_admin():
        try: B.run_as_admin()
        except: pass
        sys.exit(0)
    App().run()
