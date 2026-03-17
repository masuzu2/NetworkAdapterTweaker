"""
╔══════════════════════════════════════════════════════╗
║   Network Adapter Tweaker — by Bootstep             ║
║   The most beautiful NIC tweaker in the world.      ║
╚══════════════════════════════════════════════════════╝
"""
import sys, os, threading, tkinter as tk
from tkinter import ttk, messagebox, filedialog

if sys.platform != "win32":
    root = tk.Tk(); root.withdraw()
    messagebox.showerror("Error", "Windows only."); sys.exit(1)

import adapter as B

# ══════════════════════════════════════════════════════
#  Color Palette — Cyber Neon
# ══════════════════════════════════════════════════════
BG        = "#06090f"
BG2       = "#080d16"
PANEL     = "#0a1020"
HEADER    = "#0c1428"
HEADER2   = "#101830"
BORDER    = "#14253d"
GLOW      = "#0d2847"
INPUT_BG  = "#050810"
TXT       = "#c0d4ea"
DIM       = "#3d5068"
LBL       = "#6882a0"
CYAN      = "#00d4ff"
GREEN     = "#00ff88"
ORANGE    = "#ff9f1c"
RED       = "#ff3355"
BLUE      = "#2e86ff"
PURPLE    = "#8b5cf6"
PINK      = "#f472b6"
YELLOW    = "#fbbf24"
HOVER     = "#0e1a33"
ACCENT1   = "#00d4ff"  # primary accent
ACCENT2   = "#8b5cf6"  # secondary
BRAND_BG  = "#0a0f1e"
BRAND_FG  = "#00d4ff"

ROW_H = 22
FONT   = ("Segoe UI", 9)
FONT_B = ("Segoe UI", 9, "bold")
FONT_M = ("Consolas", 9)
FONT_S = ("Segoe UI", 8)
FONT_H = ("Consolas", 10, "bold")
FONT_T = ("Segoe UI", 7)

# Section config: (style_name, color, icon)
SEC = {
    "RSS":    (CYAN,   "\u2630"),   # ☰
    "Global": (PURPLE, "\u2699"),   # ⚙
    "Iface":  (GREEN,  "\u21c4"),   # ⇄
    "Adv":    (BLUE,   "\u2638"),   # ☸
    "Tweak":  (ORANGE, "\u2692"),   # ⚒
    "Power":  (RED,    "\u26a1"),   # ⚡
}

# ══════════════════════════════════════════════════════
#  Dark Theme
# ══════════════════════════════════════════════════════
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
    s.configure("TCheckbutton", background=BG, foreground=TXT, font=FONT_S,
                indicatorcolor=INPUT_BG)
    s.map("TCheckbutton", background=[("active", BG)],
          indicatorcolor=[("selected", CYAN)])
    s.configure("Vertical.TScrollbar", background=BORDER, troughcolor=BG,
                arrowcolor=DIM, borderwidth=0, width=6)
    s.map("Vertical.TScrollbar", background=[("active", CYAN)])
    # Per-section button styles
    for name, (color, _) in SEC.items():
        s.configure(f"{name}Btn.TButton", foreground=color, background=INPUT_BG,
                    font=("Segoe UI", 7, "bold"), padding=(6,1))
        s.map(f"{name}Btn.TButton", foreground=[("active", color)],
              background=[("active", HOVER)])
    # Treeview
    s.configure("Treeview", background=INPUT_BG, foreground=CYAN,
                fieldbackground=INPUT_BG, font=FONT_M, rowheight=24, borderwidth=0)
    s.configure("Treeview.Heading", background=HEADER, foreground=LBL,
                font=FONT_B, borderwidth=0, relief="flat")
    s.map("Treeview", background=[("selected", GLOW)], foreground=[("selected", "#fff")])
    # Combobox popdown
    root.option_add("*TCombobox*Listbox.background", INPUT_BG)
    root.option_add("*TCombobox*Listbox.foreground", CYAN)
    root.option_add("*TCombobox*Listbox.selectBackground", GLOW)
    root.option_add("*TCombobox*Listbox.font", FONT_M)


# ══════════════════════════════════════════════════════
#  Glow Button (tk.Canvas based)
# ══════════════════════════════════════════════════════
class GlowButton(tk.Canvas):
    """A beautiful button with glow border effect."""
    def __init__(self, master, text="", fg=CYAN, bg_normal="#0a1428",
                 bg_hover="#0f1e3a", glow_color=None, command=None, width=80, height=24, **kw):
        super().__init__(master, width=width, height=height, bg=master["bg"],
                         highlightthickness=0, cursor="hand2", **kw)
        self.fg = fg
        self.bg_n = bg_normal
        self.bg_h = bg_hover
        self.glow = glow_color or fg
        self.cmd = command
        self.w = width
        self.h = height
        self.text = text
        self._hovering = False
        self._draw()
        self.bind("<Enter>", self._enter)
        self.bind("<Leave>", self._leave)
        self.bind("<Button-1>", self._click)

    def _draw(self):
        self.delete("all")
        bg = self.bg_h if self._hovering else self.bg_n
        # Glow border when hovering
        if self._hovering:
            self.create_rectangle(0, 0, self.w, self.h, fill=bg, outline=self.glow, width=1)
        else:
            self.create_rectangle(0, 0, self.w, self.h, fill=bg, outline=BORDER, width=1)
        self.create_text(self.w//2, self.h//2, text=self.text, fill=self.fg,
                         font=("Segoe UI", 8, "bold"))

    def _enter(self, e): self._hovering = True; self._draw()
    def _leave(self, e): self._hovering = False; self._draw()
    def _click(self, e):
        if self.cmd: self.cmd()


# ══════════════════════════════════════════════════════
#  Scrollable Panel
# ══════════════════════════════════════════════════════
class ScrollPanel(tk.Frame):
    def __init__(self, master, **kw):
        super().__init__(master, bg=PANEL, **kw)
        self.canvas = tk.Canvas(self, bg=PANEL, highlightthickness=0, bd=0)
        self.sb = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = tk.Frame(self.canvas, bg=PANEL)
        self.inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self._win = self.canvas.create_window((0,0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.sb.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.sb.pack(side="right", fill="y")
        # Resize inner to match canvas width
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self._win, width=e.width))
        self.bind_all("<MouseWheel>", self._on_mouse, add="+")
        self.widgets = {}

    def _on_mouse(self, e):
        w = e.widget
        while w:
            if w == self.canvas:
                self.canvas.yview_scroll(int(-1*(e.delta/120)), "units")
                return
            w = getattr(w, "master", None)

    def add_row(self, key, label_text, value="", is_combo=False, options=None,
                color=CYAN, tooltip=""):
        row = tk.Frame(self.inner, bg=PANEL, height=ROW_H)
        row.pack(fill="x")
        row.pack_propagate(False)

        def enter(e):
            row.configure(bg=HOVER)
            for c in row.winfo_children():
                if isinstance(c, tk.Label): c.configure(bg=HOVER)
        def leave(e):
            row.configure(bg=PANEL)
            for c in row.winfo_children():
                if isinstance(c, tk.Label): c.configure(bg=PANEL)
        row.bind("<Enter>", enter); row.bind("<Leave>", leave)

        lbl = tk.Label(row, text=label_text, font=FONT_S, fg=LBL, bg=PANEL, anchor="w")
        lbl.pack(side="left", padx=(8,2), fill="x", expand=True)
        lbl.bind("<Enter>", enter); lbl.bind("<Leave>", leave)
        if tooltip:
            self._tip(lbl, tooltip)

        if is_combo and options:
            var = tk.StringVar(value=value if value in options else (options[0] if options else ""))
            if value and value not in options:
                options = list(options) + [value]
                var.set(value)
            w = ttk.Combobox(row, textvariable=var, values=options, width=17,
                             state="readonly", font=FONT_M)
            w.pack(side="right", padx=(2,6), pady=1)
            self.widgets[key] = var
        else:
            var = tk.StringVar(value=value)
            w = ttk.Entry(row, textvariable=var, width=17, font=FONT_M, justify="right")
            w.pack(side="right", padx=(2,6), pady=1)
            self.widgets[key] = var

        tk.Frame(self.inner, bg=BORDER, height=1).pack(fill="x")

    def _tip(self, widget, text):
        tip = [None]
        def show(e):
            t = tk.Toplevel(widget); tip[0] = t
            t.wm_overrideredirect(True)
            t.wm_geometry(f"+{e.x_root+14}+{e.y_root+10}")
            f = tk.Frame(t, bg=CYAN, padx=1, pady=1)
            f.pack()
            tk.Label(f, text=f" {text} ", bg="#0a1a2e", fg=CYAN, font=FONT_S,
                     padx=6, pady=3).pack()
        def hide(e):
            if tip[0]: tip[0].destroy(); tip[0] = None
        widget.bind("<Enter>", show, add="+")
        widget.bind("<Leave>", hide, add="+")

    def get_values(self):
        return {k: v.get() for k, v in self.widgets.items()}


# ══════════════════════════════════════════════════════
#  Section Card — with glow header
# ══════════════════════════════════════════════════════
class SectionCard(tk.Frame):
    def __init__(self, master, title, style_name="RSS", **kw):
        super().__init__(master, bg=BG, **kw)
        color, icon = SEC.get(style_name, (CYAN, "\u2630"))

        # Glow top line
        tk.Frame(self, bg=color, height=2).pack(fill="x")

        # Header
        hdr = tk.Frame(self, bg=HEADER, height=28)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        tk.Label(hdr, text=f" {icon} ", font=("Segoe UI", 11), fg=color,
                 bg=HEADER).pack(side="left")
        tk.Label(hdr, text=title, font=FONT_H, fg=color,
                 bg=HEADER, anchor="w").pack(side="left", fill="x", expand=True)

        self.apply_btn = ttk.Button(hdr, text="\u2713 Apply", style=f"{style_name}Btn.TButton", width=8)
        self.apply_btn.pack(side="right", padx=4, pady=3)

        # Body
        self.panel = ScrollPanel(self)
        self.panel.pack(fill="both", expand=True)

        # Bottom border
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", side="bottom")

    def set_command(self, cmd):
        self.apply_btn.configure(command=cmd)


# ══════════════════════════════════════════════════════
#  Setting Field Definitions
# ══════════════════════════════════════════════════════
RSS_FIELDS = [
    ("Enabled",              "Status",                True, ["True","False"], "Enable/Disable RSS"),
    ("NumberOfReceiveQueues", "NumberOfReceiveQueues",  False, [], "Number of RSS queues"),
    ("Profile",              "Profile",               True, ["NUMAStatic","NUMAScalingStatic","ConservativeScaling","ClosestProcessor"], "RSS CPU assignment profile"),
    ("BaseProcessorNumber",  "BaseProcessor",          False, [], "First CPU core for RSS"),
    ("MaxProcessorNumber",   "MaxProcessor",           False, [], "Last CPU core for RSS"),
    ("MaxProcessors",        "MaxProcessors",          False, [], "Max CPUs per RSS queue"),
]
GLOBAL_FIELDS = [
    ("ReceiveSideScaling",           "ReceiveSideScaling",          True, ["Enabled","Disabled"], "RSS global switch"),
    ("ReceiveSegmentCoalescing",     "ReceiveSegmentCoalescing",    True, ["Enabled","Disabled"], "RSC merges packets (off=gaming)"),
    ("Chimney",                      "Chimney",                     True, ["Enabled","Disabled","Automatic"], "TCP Chimney (deprecated)"),
    ("TaskOffload",                  "TaskOffload",                 True, ["Enabled","Disabled"], "Hardware task offload"),
    ("NetworkDirect",                "NetworkDirect",               True, ["Enabled","Disabled"], "RDMA support"),
    ("NetworkDirectAcrossIPSubnets", "NetworkDirectAcrossIPSubnets",True, ["Allowed","Blocked"], "RDMA across subnets"),
    ("PacketCoalescingFilter",       "PacketCoalescingFilter",      True, ["Enabled","Disabled"], "Coalesce pkts (off=gaming)"),
]
IFACE_FIELDS = [
    ("AdvertiseDefaultRoute",  "AdvertiseDefaultRoute",  True, ["Enabled","Disabled"], ""),
    ("Advertising",            "Advertising",            True, ["Enabled","Disabled"], ""),
    ("AutomaticMetric",        "AutomaticMetric",        True, ["Enabled","Disabled"], "Auto metric for routing"),
    ("ClampMss",               "ClampMss",               True, ["Enabled","Disabled"], ""),
    ("DirectedMacWolPattern",  "DirectedMacWolPattern",  True, ["Enabled","Disabled"], ""),
    ("EcnMarking",             "EcnMarking",             True, ["Disabled","UseEct1","UseEct0","AppDecide"], "ECN marking"),
    ("ForceArpNdWolPattern",   "ForceArpNdWolPattern",   True, ["Enabled","Disabled"], ""),
    ("Forwarding",             "Forwarding",             True, ["Enabled","Disabled"], "IP forwarding (router)"),
    ("IgnoreDefaultRoutes",    "IgnoreDefaultRoutes",    True, ["Enabled","Disabled"], ""),
    ("ManagedAddressConfiguration","ManagedAddrConfig",  True, ["Enabled","Disabled"], ""),
    ("NeighborDiscoverySupported","NeighborDiscovery",   True, ["Yes","No"], ""),
    ("NeighborUnreachabilityDetection","NeighborUnreachDet", True, ["Enabled","Disabled"], ""),
    ("OtherStatefulConfiguration","OtherStatefulConfig",  True, ["Enabled","Disabled"], ""),
    ("RouterDiscovery",        "RouterDiscovery",        True, ["Enabled","Disabled","ControlledByDHCP"], ""),
    ("Store",                  "Store",                  True, ["ActiveStore","PersistentStore"], ""),
    ("WeakHostReceive",        "WeakHostReceive",        True, ["Enabled","Disabled"], ""),
    ("WeakHostSend",           "WeakHostSend",           True, ["Enabled","Disabled"], ""),
    ("CurrentHopLimit",        "CurrentHopLimit",        False, [], "TTL value"),
    ("BaseReachableTime",      "BaseReachableTime (ms)", False, [], "ms"),
    ("RetransmitTime",         "RetransmitTime (ms)",    False, [], "ms"),
    ("ReachableTime",          "ReachableTime (ms)",     False, [], "ms"),
    ("DadRetransmitTime",      "DadRetransmitTime",      False, [], ""),
    ("DadTransmits",           "DadTransmits",           False, [], ""),
    ("NlMtu",                  "NlMtu (bytes)",          False, [], "bytes"),
]
ADV_KEYS = [
    ("*FlowControl",            "FlowControl",            "Flow control"),
    ("*IPChecksumOffloadIPv4",   "IPChecksumOffloadIPv4",   "HW IP checksum"),
    ("*TCPChecksumOffloadIPv4",  "TCPChecksumOffloadIPv4",  "HW TCP chksum v4"),
    ("*TCPChecksumOffloadIPv6",  "TCPChecksumOffloadIPv6",  "HW TCP chksum v6"),
    ("*UDPChecksumOffloadIPv4",  "UDPChecksumOffloadIPv4",  "HW UDP chksum v4"),
    ("*UDPChecksumOffloadIPv6",  "UDPChecksumOffloadIPv6",  "HW UDP chksum v6"),
    ("*LsoV1IPv4",               "LsoV1IPv4",               "Large Send v1"),
    ("*LsoV2IPv4",               "LsoV2IPv4",               "Large Send v2 IPv4"),
    ("*LsoV2IPv6",               "LsoV2IPv6",               "Large Send v2 IPv6"),
    ("*PMARPOffload",            "PMARPOffload",             "ARP offload (power)"),
    ("*PMNSOffload",             "PMNSOffload",              "NS offload (power)"),
    ("*PriorityVLANTag",         "PriorityVLANTag",          "802.1p/Q tagging"),
    ("*ReceiveBuffers",          "ReceiveBuffers",            "RX ring buffer"),
    ("*TransmitBuffers",         "TransmitBuffers",           "TX ring buffer"),
    ("*InterruptModeration",     "InterruptModeration",       "Coalesce IRQ (off=low latency)"),
    ("ITR",                      "InterruptModerationRate",   "IRQ per second"),
    ("TxIntDelay",               "TxIntDelay",                "TX interrupt delay"),
    ("PacketDirect",             "PacketDirect",              "Kernel-bypass"),
    ("*RSS",                     "RSS",                       "Receive Side Scaling"),
]
TWEAK_KEYS = [
    ("DefaultReceiveWindow",     "DefaultReceiveWindow",    "AFD receive buffer"),
    ("DefaultSendWindow",        "DefaultSendWindow",       "AFD send buffer"),
    ("BufferMultiplier",         "BufferMultiplier",         "Buffer multiplier"),
    ("BufferAlignment",          "BufferAlignment",          "Memory alignment"),
    ("DoNotHoldNicBuffers",      "DoNotHoldNICBuffers",      "Release NIC buffers"),
    ("SmallBufferSize",          "SmallBufferSize",          "Small buffer pool"),
    ("MediumBufferSize",         "MediumBufferSize",         "Medium buffer pool"),
    ("LargeBufferSize",          "LargeBufferSize",          "Large buffer pool"),
    ("HugeBufferSize",           "HugeBufferSize",           "Huge buffer pool"),
    ("SmallBufferListDepth",     "SmallBufferListDepth",     "Small buffer count"),
    ("MediumBufferListDepth",    "MediumBufferListDepth",    "Medium buffer count"),
    ("LargeBufferListDepth",     "LargeBufferListDepth",     "Large buffer count"),
    ("DisableAddressSharing",    "DisableAddressSharing",    ""),
    ("DisableChainedReceive",    "DisableChainedReceive",    ""),
    ("DisableDirectAcceptEx",    "DisableDirectAcceptEx",    ""),
    ("DisableRawSecurity",       "DisableRawSecurity",       ""),
    ("DynamicSendBufferDisable", "DynamicSendBufferDisable", "Disable dynamic send"),
    ("FastSendDatagramThreshold","FastSendDatagramThreshold",""),
    ("FastCopyReceiveThreshold", "FastCopyReceiveThreshold", ""),
    ("IgnorePushBitOnReceives",  "IgnorePushBitOnReceives",  "Ignore TCP PSH"),
    ("IgnoreOrderlyRelease",     "IgnoreOrderlyRelease",     ""),
    ("TransmitWorker",           "TransmitWorker",           ""),
    ("PriorityBoost",            "PriorityBoost",            "Boost NIC priority"),
]
POWER_KEYS = [
    ("*PMAPowerManagement",      "(APM) sleep states",       "Allow adapter sleep"),
    ("DynamicPowerGating",       "DynamicPowerGating",       "Dynamic power gate"),
    ("ConnectedPowerGating",     "ConnectedPowerGating",     "Connected standby"),
    ("AutoPowerSaveModeEnabled", "AutoPowerSaveMode",        "Auto power save"),
    ("NicAutoPowerSaver",        "NicAutoPowerSaver",        "NIC auto saver"),
    ("DelayedPowerUpEn",         "DelayedPowerUp",           "Delay power up"),
    ("ReduceSpeedOnPowerDown",   "ReduceSpeedOnPowerDown",   "Reduce speed on sleep"),
    ("*WakeOnMagicPacket",       "WakeOnMagicPacket",        "WOL magic packet"),
    ("*WakeOnPattern",           "WakeOnPattern",            "Wake on pattern"),
    ("WakeOnLink",               "WakeOnLink",               "Wake on link"),
    ("*EEE",                     "Energy Efficient Ethernet", "802.3az EEE"),
    ("EnableGreenEthernet",      "GreenEthernet",            "Green Ethernet"),
]


# ══════════════════════════════════════════════════════
#  Main App
# ══════════════════════════════════════════════════════
class App:
    VERSION = "2.0"

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Network Adapter Tweaker — by Bootstep")
        self.root.geometry("1440x900")
        self.root.minsize(1000, 500)
        self.root.configure(bg=BG)
        apply_dark_theme(self.root)

        self.adapters = []
        self.cur = ""
        self.adv_map = {}
        self.ipv4 = True

        self._build_brand_header()
        self._build_topbar()
        self._build_statusbar()
        self._build_columns()
        self._load_adapters()

    # ── Brand Header ──
    def _build_brand_header(self):
        bh = tk.Frame(self.root, bg=BRAND_BG, height=36)
        bh.pack(fill="x")
        bh.pack_propagate(False)

        # Left: logo + title
        left = tk.Frame(bh, bg=BRAND_BG)
        left.pack(side="left", padx=10)

        # Logo box
        logo = tk.Canvas(left, width=24, height=24, bg=BRAND_BG, highlightthickness=0)
        logo.pack(side="left", pady=5)
        logo.create_rectangle(1, 1, 23, 23, fill="#0d2847", outline=CYAN, width=1)
        logo.create_text(12, 12, text="N", fill=CYAN, font=("Consolas", 12, "bold"))

        tk.Label(left, text=" Network Adapter Tweaker", font=("Segoe UI", 11, "bold"),
                 fg="#ffffff", bg=BRAND_BG).pack(side="left")
        tk.Label(left, text=f"  v{self.VERSION}", font=("Consolas", 8),
                 fg=DIM, bg=BRAND_BG).pack(side="left", pady=(2,0))

        # Right: branding
        right = tk.Frame(bh, bg=BRAND_BG)
        right.pack(side="right", padx=12)

        tk.Label(right, text="by ", font=("Segoe UI", 9),
                 fg=DIM, bg=BRAND_BG).pack(side="left")
        tk.Label(right, text="Bootstep", font=("Segoe UI", 11, "bold"),
                 fg=CYAN, bg=BRAND_BG).pack(side="left")
        tk.Label(right, text=" \u2022 ", font=("Segoe UI", 8),
                 fg=BORDER, bg=BRAND_BG).pack(side="left")

        # Admin badge
        is_adm = B.is_admin()
        badge_fg = GREEN if is_adm else RED
        badge_text = "\u2713 ADMIN" if is_adm else "\u2717 USER"
        badge = tk.Label(right, text=f" {badge_text} ", font=("Consolas", 8, "bold"),
                         fg=badge_fg, bg=BRAND_BG)
        badge.pack(side="left")

        # Glow line under header
        glow = tk.Canvas(self.root, height=2, bg=BG, highlightthickness=0)
        glow.pack(fill="x")
        glow.bind("<Configure>", lambda e: self._draw_gradient_line(glow, e.width))

    def _draw_gradient_line(self, canvas, width):
        canvas.delete("all")
        mid = width // 2
        for i in range(width):
            dist = abs(i - mid) / max(mid, 1)
            r = int(0 + (13 - 0) * dist)
            g = int(212 - 212 * dist * 0.7)
            b = int(255 - 100 * dist)
            color = f"#{r:02x}{g:02x}{b:02x}"
            canvas.create_line(i, 0, i, 2, fill=color)

    # ── Top Bar ──
    def _build_topbar(self):
        top = tk.Frame(self.root, bg=HEADER, height=50)
        top.pack(fill="x")
        top.pack_propagate(False)

        r1 = tk.Frame(top, bg=HEADER)
        r1.pack(fill="x", padx=8, pady=(5,0))

        tk.Label(r1, text="Adapter:", font=FONT_B, fg=LBL, bg=HEADER).pack(side="left")
        self.adapter_var = tk.StringVar()
        self.adapter_cb = ttk.Combobox(r1, textvariable=self.adapter_var, width=36,
                                       state="readonly", font=("Segoe UI", 9, "bold"))
        self.adapter_cb.pack(side="left", padx=(4,10))
        self.adapter_cb.bind("<<ComboboxSelected>>", self._on_select)

        # Buttons with icons
        btns = [
            ("\u2630 Open",      self._open_ncpa,                     TXT,    HEADER),
            ("\u2713 Apply All", self._apply_all,                     GREEN,  "#002211"),
            ("\u21bb Restart",   self._restart,                       ORANGE, "#1a1000"),
            ("\u2694 Gaming",    lambda: self._preset("gaming"),      PURPLE, "#0f0020"),
            ("\u2601 Stream",    lambda: self._preset("streaming"),   BLUE,   "#000f22"),
            ("\u21a9 Default",   lambda: self._preset("default"),     DIM,    HEADER),
            ("\u2191 Export",    self._export,                        YELLOW, "#1a1800"),
            ("\u2193 Import",    self._import,                        CYAN,   "#001a22"),
            ("\u2605 Profiles",  self._open_profiles,                 PINK,   "#1a0011"),
        ]
        for text, cmd, fg, bg_c in btns:
            b = tk.Button(r1, text=text, font=("Segoe UI", 8, "bold"), fg=fg, bg=bg_c,
                          bd=0, activebackground=HOVER, activeforeground=fg, cursor="hand2",
                          relief="flat", padx=7, pady=2, command=cmd)
            b.pack(side="left", padx=1)
            # Hover effect
            b.bind("<Enter>", lambda e, btn=b, c=fg: btn.configure(bg=GLOW))
            b.bind("<Leave>", lambda e, btn=b, c=bg_c: btn.configure(bg=c))

        # Meta info row
        r2 = tk.Frame(top, bg=HEADER)
        r2.pack(fill="x", padx=10, pady=(3,0))
        self.meta_lbl = tk.Label(r2, text="\u2500 Select an adapter to begin \u2500",
                                  font=("Consolas", 8), fg=DIM, bg=HEADER, anchor="w")
        self.meta_lbl.pack(side="left", fill="x")

    # ── Status Bar ──
    def _build_statusbar(self):
        bar = tk.Frame(self.root, bg=HEADER2, height=22)
        bar.pack(side="bottom", fill="x")
        bar.pack_propagate(False)

        # Left: status
        self.status_dot = tk.Canvas(bar, width=8, height=8, bg=HEADER2, highlightthickness=0)
        self.status_dot.pack(side="left", padx=(8,4), pady=7)
        self.status_dot.create_oval(1, 1, 7, 7, fill=GREEN, outline="")
        self.status_lbl = tk.Label(bar, text="Ready", font=("Consolas", 8),
                                    fg=DIM, bg=HEADER2, anchor="w")
        self.status_lbl.pack(side="left", fill="x")

        # Right: branding
        tk.Label(bar, text="Bootstep \u00a9 2024  ", font=("Segoe UI", 7),
                 fg="#2a3a50", bg=HEADER2).pack(side="right")

    # ── Columns ──
    def _build_columns(self):
        self.main = tk.Frame(self.root, bg=BG)
        self.main.pack(fill="both", expand=True)
        for i in range(4): self.main.columnconfigure(i, weight=1)
        self.main.rowconfigure(0, weight=1)

    def _build_sections(self, rss, glob, iface, afd):
        for w in self.main.winfo_children(): w.destroy()

        # ── Col 0: RSS ──
        c0 = tk.Frame(self.main, bg=BG)
        c0.grid(row=0, column=0, sticky="nsew", padx=(2,0), pady=2)
        self.sec_rss = SectionCard(c0, "RSS Settings", "RSS")
        self.sec_rss.pack(fill="both", expand=True)
        for key, label, is_combo, opts, tip in RSS_FIELDS:
            self.sec_rss.panel.add_row(key, label, rss.get(key,""), is_combo, opts, CYAN, tip)
        self.sec_rss.set_command(self._apply_rss)

        bf = tk.Frame(c0, bg=PANEL, height=30)
        bf.pack(fill="x"); bf.pack_propagate(False)
        GlowButton(bf, text="\u26a1 Unlock RSS", fg=CYAN, width=100, height=22,
                   command=self._unlock_rss).pack(side="left", padx=6, pady=3)

        # ── Col 1: Global + Interface ──
        c1 = tk.Frame(self.main, bg=BG)
        c1.grid(row=0, column=1, sticky="nsew", padx=1, pady=2)

        self.sec_global = SectionCard(c1, "Global Settings", "Global")
        self.sec_global.pack(fill="x")
        for key, label, is_combo, opts, tip in GLOBAL_FIELDS:
            self.sec_global.panel.add_row(key, label, glob.get(key,""), is_combo, opts, PURPLE, tip)
        self.sec_global.set_command(self._apply_global)

        pf = tk.Frame(c1, bg=PANEL, height=26)
        pf.pack(fill="x"); pf.pack_propagate(False)
        self.ipv4_var = tk.BooleanVar(value=self.ipv4)
        cb = ttk.Checkbutton(pf, text=" IPv4", variable=self.ipv4_var, command=self._toggle_proto)
        cb.pack(side="left", padx=8, pady=2)

        self.sec_iface = SectionCard(c1, "Interface Settings", "Iface")
        self.sec_iface.pack(fill="both", expand=True)
        for key, label, is_combo, opts, tip in IFACE_FIELDS:
            self.sec_iface.panel.add_row(key, label, iface.get(key,""), is_combo, opts, GREEN, tip)
        self.sec_iface.set_command(self._apply_iface)

        # ── Col 2: Adv + Power ──
        c2 = tk.Frame(self.main, bg=BG)
        c2.grid(row=0, column=2, sticky="nsew", padx=1, pady=2)

        self.sec_adv = SectionCard(c2, "Adv. Adapter", "Adv")
        self.sec_adv.pack(fill="both", expand=True)
        for kw, label, tip in ADV_KEYS:
            prop = self.adv_map.get(kw)
            val = prop.display_value if prop else ""
            is_c = bool(prop and prop.valid_display)
            opts = prop.valid_display if prop else []
            self.sec_adv.panel.add_row(kw, label, val, is_c, opts, BLUE, tip)
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
        c3.grid(row=0, column=3, sticky="nsew", padx=(0,2), pady=2)

        self.sec_tweak = SectionCard(c3, "Tweaks (AFD Registry)", "Tweak")
        self.sec_tweak.pack(fill="both", expand=True)
        for key, label, tip in TWEAK_KEYS:
            self.sec_tweak.panel.add_row(key, label, afd.get(key,""), False, [], ORANGE, tip)
        self.sec_tweak.set_command(self._apply_tweaks)

        # Column separator lines
        for i in range(1, 4):
            sep = tk.Frame(self.main, bg=BORDER, width=1)
            sep.place(relx=i/4, rely=0, relheight=1)

    # ── Data Loading ──
    def _load_adapters(self):
        self._status("Scanning adapters...", CYAN)
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
            self._status("No adapters found", RED)

    def _on_select(self, *_):
        disp = self.adapter_var.get()
        for a in self.adapters:
            if a.label() == disp: self._select(a.name); return

    def _select(self, name):
        self.cur = name
        self._status(f"Loading {name}...", CYAN)
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
            meta += f"  \u2502  NDIS: {info.ndis}  \u2502  MAC: {info.mac}  \u2502  Speed: {info.speed}  \u2502  Driver: {info.driver}"
        self.meta_lbl.configure(text=meta)
        self._build_sections(rss, glob, iface, afd)
        self._status("Ready", GREEN)

    def _toggle_proto(self):
        self.ipv4 = self.ipv4_var.get()
        if self.cur: self._select(self.cur)

    # ── Apply ──
    def _threaded(self, label, fn, *args, reload=False):
        self._status(f"Applying {label}...", ORANGE)
        def work():
            try:
                fn(*args)
                self.root.after(0, lambda: self._status(f"\u2713 {label} applied!", GREEN))
                if reload:
                    import time; time.sleep(0.3)
                    self.root.after(0, lambda: self._select(self.cur))
            except Exception as e:
                self.root.after(0, lambda: self._status(f"\u2717 {label}: {e}", RED))
        threading.Thread(target=work, daemon=True).start()

    def _apply_rss(self):
        self._threaded("RSS", B.set_rss, self.cur, self.sec_rss.panel.get_values())
    def _apply_global(self):
        self._threaded("Global", B.set_global, self.sec_global.panel.get_values())
    def _apply_iface(self):
        fam = "IPv4" if self.ipv4 else "IPv6"
        self._threaded("Interface", B.set_iface, self.cur, fam, self.sec_iface.panel.get_values())
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
        self._status("Auto-backup + Apply All...", ORANGE)
        def do():
            B.auto_backup(self.cur)
            for fn in [self._apply_rss, self._apply_global, self._apply_iface,
                       self._apply_adv, self._apply_tweaks, self._apply_power]:
                fn()
            import time; time.sleep(1)
            self.root.after(0, lambda: self._status("\u2713 All applied! (backup saved)", GREEN))
        threading.Thread(target=do, daemon=True).start()

    def _restart(self):
        if self.cur: self._threaded("Restart", B.restart, self.cur, reload=True)
    def _unlock_rss(self):
        if self.cur: self._threaded("Unlock RSS", B.unlock_rss, self.cur, reload=True)

    def _preset(self, key):
        if not self.cur: return
        p = B.PRESETS[key]
        if messagebox.askyesno("Preset", f"Apply: {p['name']}?\n\n{p['desc']}\n\nAuto-backup first."):
            self._status(f"Applying {p['name']}...", PURPLE)
            def do():
                B.auto_backup(self.cur)
                B.apply_preset(self.cur, key)
                import time; time.sleep(0.5)
                self.root.after(0, lambda: self._select(self.cur))
                self.root.after(0, lambda: self._status(f"\u2713 {p['name']} applied!", GREEN))
            threading.Thread(target=do, daemon=True).start()

    def _export(self):
        if not self.cur: return
        path = filedialog.asksaveasfilename(defaultextension=".json",
            filetypes=[("JSON","*.json")], initialfile=f"{self.cur}_settings.json")
        if path: B.export_all(self.cur, path); self._status(f"\u2713 Exported: {path}", GREEN)

    def _import(self):
        if not self.cur: return
        path = filedialog.askopenfilename(filetypes=[("JSON","*.json")])
        if path:
            self._status("Importing...", CYAN)
            def do():
                B.auto_backup(self.cur)
                n = B.import_all(self.cur, path)
                self.root.after(0, lambda: self._select(self.cur))
                self.root.after(0, lambda: self._status(f"\u2713 Imported {n} settings", GREEN))
            threading.Thread(target=do, daemon=True).start()

    def _open_ncpa(self): os.system("start ncpa.cpl")

    def _open_profiles(self):
        if not self.cur: return
        ProfileDialog(self.root, self.cur, self._select)

    def _status(self, msg, color=DIM):
        self.status_lbl.configure(text=msg, fg=color)
        self.status_dot.delete("all")
        self.status_dot.create_oval(1, 1, 7, 7, fill=color, outline="")

    def run(self):
        self.root.mainloop()


# ══════════════════════════════════════════════════════
#  Profile Manager Dialog — by Bootstep
# ══════════════════════════════════════════════════════
class ProfileDialog(tk.Toplevel):
    def __init__(self, parent, adapter_name, reload_cb):
        super().__init__(parent)
        self.adapter = adapter_name
        self.reload_cb = reload_cb
        self.title("Profile Manager — by Bootstep")
        self.geometry("660x560")
        self.configure(bg=BG)
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()
        self._build()
        self._refresh()

    def _build(self):
        # Header with glow
        tk.Frame(self, bg=PINK, height=2).pack(fill="x")
        hdr = tk.Frame(self, bg=HEADER, height=44)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        tk.Label(hdr, text=" \u2605 ", font=("Segoe UI", 14), fg=PINK,
                 bg=HEADER).pack(side="left", padx=(8,0))
        tk.Label(hdr, text="Profile Manager", font=("Segoe UI", 13, "bold"),
                 fg="#ffffff", bg=HEADER).pack(side="left")
        tk.Label(hdr, text=f"   {self.adapter}", font=("Consolas", 9),
                 fg=DIM, bg=HEADER).pack(side="left")
        tk.Label(hdr, text="by Bootstep  ", font=("Segoe UI", 8),
                 fg=PINK, bg=HEADER).pack(side="right", padx=8)

        # Save section
        sf = tk.Frame(self, bg=PANEL, padx=10, pady=8)
        sf.pack(fill="x", padx=10, pady=(10,4))

        tk.Label(sf, text="\u2b50 Save Current Settings", font=FONT_B,
                 fg=CYAN, bg=PANEL).pack(anchor="w")
        row = tk.Frame(sf, bg=PANEL)
        row.pack(fill="x", pady=(6,0))

        tk.Label(row, text="Name:", font=FONT_S, fg=LBL, bg=PANEL).pack(side="left")
        self.name_var = tk.StringVar()
        ttk.Entry(row, textvariable=self.name_var, width=20, font=FONT_M).pack(side="left", padx=(4,10))

        tk.Label(row, text="Note:", font=FONT_S, fg=LBL, bg=PANEL).pack(side="left")
        self.desc_var = tk.StringVar()
        ttk.Entry(row, textvariable=self.desc_var, width=22, font=FONT_M).pack(side="left", padx=(4,10))

        tk.Button(row, text="\u2713 Save", font=FONT_B, fg=GREEN, bg="#002211",
                  bd=0, relief="flat", padx=12, cursor="hand2",
                  activebackground=HOVER, activeforeground=GREEN,
                  command=self._save).pack(side="right")

        # Separator
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=10, pady=4)

        # Profile list
        lf = tk.Frame(self, bg=BG)
        lf.pack(fill="both", expand=True, padx=10, pady=(0,4))

        tk.Label(lf, text="\u2630 Saved Profiles", font=FONT_B, fg=PINK, bg=BG).pack(anchor="w", pady=(4,4))

        cols = ("name","desc","adapter","created")
        self.tree = ttk.Treeview(lf, columns=cols, show="headings", selectmode="browse", height=12)
        self.tree.heading("name", text="\u2605 Name")
        self.tree.heading("desc", text="Description")
        self.tree.heading("adapter", text="Adapter")
        self.tree.heading("created", text="Created")
        self.tree.column("name", width=140); self.tree.column("desc", width=180)
        self.tree.column("adapter", width=130); self.tree.column("created", width=130)

        sb = ttk.Scrollbar(lf, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        # Actions
        af = tk.Frame(self, bg=BG)
        af.pack(fill="x", padx=10, pady=(4,10))

        acts = [
            ("\u2713 Load & Apply", self._load,   GREEN,  "#002211"),
            ("\u270e Rename",       self._rename, YELLOW, "#1a1800"),
            ("\u2717 Delete",       self._delete, RED,    "#1a0000"),
            ("\u2630 Open Folder",  self._folder, DIM,    HEADER),
        ]
        for text, cmd, fg, bg_c in acts:
            b = tk.Button(af, text=text, font=("Segoe UI", 9, "bold"), fg=fg, bg=bg_c,
                          bd=0, relief="flat", padx=10, pady=3, cursor="hand2",
                          activebackground=HOVER, activeforeground=fg, command=cmd)
            b.pack(side="left", padx=(0,4))
            b.bind("<Enter>", lambda e, btn=b: btn.configure(bg=GLOW))
            b.bind("<Leave>", lambda e, btn=b, c=bg_c: btn.configure(bg=c))

        tk.Button(af, text="Close", font=FONT_B, fg=TXT, bg=HEADER, bd=0, relief="flat",
                  padx=14, pady=3, cursor="hand2", command=self.destroy).pack(side="right")

    def _refresh(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        self.profiles = B.profile_list()
        for p in self.profiles:
            cr = p["created"][:16].replace("T"," ") if p["created"] else ""
            self.tree.insert("", "end", values=(p["name"], p["desc"], p["adapter"], cr))

    def _sel(self):
        s = self.tree.selection()
        if not s: messagebox.showwarning("Profile", "Select a profile.", parent=self); return None
        idx = self.tree.index(s[0])
        return self.profiles[idx] if idx < len(self.profiles) else None

    def _save(self):
        name = self.name_var.get().strip()
        if not name: messagebox.showwarning("Save", "Enter a name.", parent=self); return
        existing = [p for p in B.profile_list() if p["name"] == name]
        if existing:
            if not messagebox.askyesno("Overwrite", f"'{name}' exists. Overwrite?", parent=self): return
            B.profile_delete(existing[0]["path"])
        B.profile_save(self.adapter, name, self.desc_var.get().strip())
        self.name_var.set(""); self.desc_var.set("")
        self._refresh()
        messagebox.showinfo("Saved", f"\u2713 Profile '{name}' saved!", parent=self)

    def _load(self):
        p = self._sel()
        if not p: return
        if messagebox.askyesno("Load", f"Apply '{p['name']}'?\n\n{p['desc']}\n\nAuto-backup first.", parent=self):
            B.auto_backup(self.adapter)
            n = B.profile_load(self.adapter, p["path"])
            messagebox.showinfo("Done", f"\u2713 Applied! {n} settings.", parent=self)
            self.reload_cb(self.adapter)

    def _rename(self):
        p = self._sel()
        if not p: return
        dlg = tk.Toplevel(self); dlg.title("Rename"); dlg.geometry("360x110")
        dlg.configure(bg=BG); dlg.transient(self); dlg.grab_set()
        tk.Label(dlg, text=f"Rename '{p['name']}':", font=FONT_B, fg=CYAN, bg=BG).pack(padx=12, pady=(12,4), anchor="w")
        var = tk.StringVar(value=p["name"])
        ttk.Entry(dlg, textvariable=var, width=35, font=FONT_M).pack(padx=12)
        def do():
            n = var.get().strip()
            if n and n != p["name"]: B.profile_rename(p["path"], n); self._refresh()
            dlg.destroy()
        bf = tk.Frame(dlg, bg=BG); bf.pack(pady=8)
        tk.Button(bf, text="\u2713 Rename", font=FONT_B, fg=GREEN, bg="#002211", bd=0, padx=10, command=do).pack(side="left", padx=4)
        tk.Button(bf, text="Cancel", font=FONT_B, fg=TXT, bg=HEADER, bd=0, padx=10, command=dlg.destroy).pack(side="left")

    def _delete(self):
        p = self._sel()
        if not p: return
        if messagebox.askyesno("Delete", f"Delete '{p['name']}'?", parent=self):
            B.profile_delete(p["path"]); self._refresh()

    def _folder(self):
        B._ensure_profiles_dir(); os.startfile(B.PROFILES_DIR)


# ══════════════════════════════════════════════════════
if __name__ == "__main__":
    if not B.is_admin():
        try: B.run_as_admin()
        except: pass
        sys.exit(0)
    App().run()
