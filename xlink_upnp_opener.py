"""
Xlink Kai Port Opener v2 - Automatic UPnP port forwarder
Opens UDP 3074 & 30000 on your router for better Xlink Kai connectivity
Includes Router Setup Guide for first-time users
No external dependencies - pure Python 3
"""

import socket
import urllib.request
import xml.etree.ElementTree as ET
import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import time
import webbrowser
import re
import subprocess
import os
import sys

# ── Subprocess flag ────────────────────────────────────────────────────────────
NO_WIN = subprocess.CREATE_NO_WINDOW

# ── UI colour palette ──────────────────────────────────────────────────────────
BG   = "#1a1a2e"
CARD = "#16213e"
ACC  = "#0f3460"
GOLD = "#e94560"
FG   = "#eaeaea"
DIM  = "#8888aa"
GRN  = "#00ff88"

# ── Port definitions ───────────────────────────────────────────────────────────
PORTS = [
    (3074,  "UDP", "Xlink Kai Xbox"),
    (30000, "UDP", "Xlink Kai Tunnel"),
]

# ── SSDP discovery constants ───────────────────────────────────────────────────
SSDP_ADDR    = "239.255.255.250"
SSDP_PORT    = 1900
# Multiple service types tried in order; covers IGD v1/v2 and direct WAN services
SSDP_ST_LIST = [
    "urn:schemas-upnp-org:device:InternetGatewayDevice:1",
    "urn:schemas-upnp-org:device:InternetGatewayDevice:2",
    "urn:schemas-upnp-org:service:WANIPConnection:1",
    "urn:schemas-upnp-org:service:WANIPConnection:2",
    "ssdp:all",
]

def _ssdp_request(st):
    return (
        "M-SEARCH * HTTP/1.1\r\n"
        f"HOST: {SSDP_ADDR}:{SSDP_PORT}\r\n"
        "MAN: \"ssdp:discover\"\r\n"
        "MX: 3\r\n"
        f"ST: {st}\r\n\r\n"
    ).encode()

# ── Watermark Canvas Logo ─────────────────────────────────────────────────────
def draw_watermark(parent, bg="#1a1a2e"):
    """Draw a subtle R6 shield + XLink Kai watermark on a Canvas widget."""
    c = tk.Canvas(parent, width=460, height=68, bg=bg,
                  highlightthickness=0, bd=0)

    # ── R6 Shield (left side) ─────────────────────────────────────────────────
    sx, sy = 18, 8      # shield top-left origin
    sw, sh = 38, 48     # shield width/height
    # Shield outline points (classic hex-bottom shield shape)
    pts = [
        sx,        sy,
        sx+sw,     sy,
        sx+sw,     sy+sh*0.62,
        sx+sw//2,  sy+sh,
        sx,        sy+sh*0.62,
    ]
    c.create_polygon(pts, fill="#0f3460", outline="#e94560", width=2, smooth=False)
    # Inner shield
    m = 5
    ipts = [
        sx+m,        sy+m,
        sx+sw-m,     sy+m,
        sx+sw-m,     sy+sh*0.62-m*0.3,
        sx+sw//2,    sy+sh-m*1.8,
        sx+m,        sy+sh*0.62-m*0.3,
    ]
    c.create_polygon(ipts, fill="#16213e", outline="#e94560", width=1, smooth=False)
    # "R6" text on shield
    c.create_text(sx+sw//2, sy+sh*0.42, text="R6",
                  font=("Segoe UI", 13, "bold"), fill="#e94560", anchor="center")

    # ── Title text (centre-left of banner) ───────────────────────────────────
    c.create_text(68, 20, text="RAINBOW SIX 3: BLACK ARROW",
                  font=("Segoe UI", 11, "bold"), fill="#eaeaea", anchor="w")
    c.create_text(68, 38, text="ORIGINAL XBOX  ·  XLINK KAI PORT UTILITY",
                  font=("Segoe UI", 8), fill="#8888aa", anchor="w")
    c.create_text(68, 54, text="UDP 3074  &  UDP 30000",
                  font=("Segoe UI", 8, "bold"), fill="#e94560", anchor="w")

    # ── XLink Kai "signal" icon (right side) ─────────────────────────────────
    rx = 400; ry = 34    # centre of signal icon
    # Concentric arcs — signal bars style
    for i, (r, w) in enumerate([(22,2),(15,2),(8,2)]):
        c.create_arc(rx-r, ry-r, rx+r, ry+r,
                     start=30, extent=120,
                     style="arc", outline="#e94560", width=w)
    # Centre dot
    c.create_oval(rx-3, ry-3, rx+3, ry+3, fill="#e94560", outline="")
    # "KAI" label under icon
    c.create_text(rx, ry+16, text="XLINK KAI",
                  font=("Segoe UI", 7, "bold"), fill="#8888aa", anchor="center")

    return c



ROUTERS = {
    "--- Select your router brand ---": None,
    "ASUS (standard)": {
        "url": "http://192.168.1.1",
        "user": "admin", "password": "admin",
        "steps": [
            "1. Open browser: http://192.168.1.1",
            "2. Login: admin / admin  (or check bottom sticker)",
            "3. Left menu: click WAN",
            "4. Click the NAT Passthrough tab",
            "5. Set UPnP to Enable",
            "6. Click Apply",
            "7. Click Re-detect Router in this tool",
        ]
    },
    "ASUS BE9700 / newer": {
        "url": "http://router.asus.com",
        "user": "admin", "password": "admin",
        "steps": [
            "1. Open browser: http://router.asus.com",
            "   (or http://192.168.1.1)",
            "2. Login: admin / admin",
            "   (newer routers prompt password setup on first boot)",
            "3. Advanced Settings -> WAN -> NAT Passthrough tab",
            "4. Set UPnP to Enable -> Apply",
            "5. Click Re-detect Router in this tool",
        ]
    },
    "Netgear": {
        "url": "http://192.168.1.1",
        "user": "admin", "password": "password",
        "steps": [
            "1. Open browser: http://192.168.1.1",
            "   (or http://routerlogin.net)",
            "2. Login: admin / password  (check sticker if fails)",
            "3. Advanced -> Advanced Setup -> UPnP",
            "4. Check Turn UPnP On",
            "5. Click Apply",
            "6. Click Re-detect Router in this tool",
        ]
    },
    "Netgear Orbi": {
        "url": "http://orbilogin.com",
        "user": "admin", "password": "password",
        "steps": [
            "1. Open browser: http://orbilogin.com",
            "   (or http://192.168.1.1)",
            "2. Login: admin / password",
            "3. Advanced -> Advanced Setup -> UPnP",
            "4. Check Turn UPnP On -> Apply",
            "5. Click Re-detect Router in this tool",
        ]
    },
    "Linksys (standard)": {
        "url": "http://192.168.1.1",
        "user": "admin", "password": "(leave blank)",
        "steps": [
            "1. Open browser: http://192.168.1.1",
            "2. Login: admin / (leave password blank)",
            "   or try admin / admin",
            "3. Click Administration tab at the top",
            "4. Click Management sub-tab",
            "5. Find UPnP and select Enable",
            "6. Click Save Settings",
            "7. Click Re-detect Router in this tool",
        ]
    },
    "Linksys Velop / newer": {
        "url": "http://192.168.1.1",
        "user": "admin", "password": "admin",
        "steps": [
            "1. Open browser: http://192.168.1.1",
            "2. Login with your Linksys account credentials",
            "3. Connectivity -> Local Network",
            "4. Toggle UPnP to ON -> Apply",
            "5. Click Re-detect Router in this tool",
        ]
    },
    "TP-Link Archer": {
        "url": "http://192.168.0.1",
        "user": "admin", "password": "admin",
        "steps": [
            "1. Open browser: http://192.168.0.1",
            "   (or http://tplinkrouter.net)",
            "2. Login: admin / admin",
            "3. Advanced -> NAT Forwarding -> UPnP",
            "4. Toggle UPnP switch ON (turns blue)",
            "5. Applies instantly - no save needed",
            "6. Click Re-detect Router in this tool",
        ]
    },
    "TP-Link (older)": {
        "url": "http://192.168.1.1",
        "user": "admin", "password": "admin",
        "steps": [
            "1. Open browser: http://192.168.1.1",
            "2. Login: admin / admin",
            "3. Left menu: Forwarding -> UPnP",
            "4. Click Enable UPnP -> Save",
            "5. Click Re-detect Router in this tool",
        ]
    },
    "D-Link": {
        "url": "http://192.168.0.1",
        "user": "Admin", "password": "(leave blank)",
        "steps": [
            "1. Open browser: http://192.168.0.1",
            "2. Login: Admin (capital A) / (leave blank)",
            "3. Advanced tab at top -> Advanced Network in left menu",
            "4. Check Enable UPnP -> Save Settings",
            "5. Click Re-detect Router in this tool",
        ]
    },
    "Belkin": {
        "url": "http://192.168.2.1",
        "user": "(leave blank)", "password": "(leave blank)",
        "steps": [
            "1. Open browser: http://192.168.2.1",
            "2. No login needed by default",
            "   (leave both fields blank if prompted)",
            "3. Firewall -> UPnP in left menu",
            "4. Select Enable -> Apply Changes",
            "5. Click Re-detect Router in this tool",
        ]
    },
    "Motorola / Arris": {
        "url": "http://192.168.100.1",
        "user": "admin", "password": "motorola",
        "steps": [
            "1. Open browser: http://192.168.100.1",
            "   (or http://192.168.0.1)",
            "2. Login: admin / motorola",
            "   (ISP devices often have custom password on sticker)",
            "3. Advanced -> UPnP -> Enable -> Apply",
            "4. Click Re-detect Router in this tool",
        ]
    },
    "Xfinity / Comcast xFi": {
        "url": "http://10.0.0.1",
        "user": "admin", "password": "password",
        "steps": [
            "1. Open browser: http://10.0.0.1",
            "2. Login: admin / password  (or check gateway sticker)",
            "3. Advanced -> look for UPnP setting",
            "",
            "NOTE: Xfinity gateways often have UPnP locked.",
            "If you cannot find it, try the Xfinity app:",
            "  More -> Gateway -> Connection -> UPnP",
            "Or call Xfinity and ask them to enable UPnP.",
            "Best option: enable Bridge Mode on gateway",
            "and use your own router behind it.",
        ]
    },
    "AT&T BGW / NVG": {
        "url": "http://192.168.1.254",
        "user": "admin", "password": "(on device sticker)",
        "steps": [
            "1. Open browser: http://192.168.1.254",
            "2. Login: admin / (password on sticker on gateway)",
            "3. Firewall -> Advanced Firewall -> Enable UPnP -> Save",
            "4. Click Re-detect Router in this tool",
            "",
            "NOTE: AT&T gateways sometimes lock UPnP entirely.",
            "If locked, use IP Passthrough and connect your own router.",
        ]
    },
    "Verizon Fios G3100 / CR1000A": {
        "url": "http://192.168.1.1",
        "user": "admin", "password": "(on device sticker)",
        "steps": [
            "1. Open browser: http://192.168.1.1",
            "   (or http://myfiosgateway.com)",
            "2. Login: admin / (password on router sticker)",
            "3. Advanced -> UPnP -> Enable UPnP -> Apply",
            "4. Click Re-detect Router in this tool",
        ]
    },
    "Spectrum router": {
        "url": "http://192.168.1.1",
        "user": "admin", "password": "(on device sticker)",
        "steps": [
            "1. Open browser: http://192.168.1.1",
            "2. Login: admin / (password on sticker)",
            "3. Advanced Settings -> UPnP -> Enable -> Save",
            "4. Click Re-detect Router in this tool",
            "",
            "NOTE: Some Spectrum routers lock UPnP settings.",
            "If locked, call Spectrum or use your own router.",
        ]
    },
    "Cox Panoramic WiFi": {
        "url": "http://192.168.0.1",
        "user": "admin", "password": "(on device sticker)",
        "steps": [
            "1. Open browser: http://192.168.0.1",
            "2. Login with credentials from sticker on gateway",
            "3. Advanced Settings -> UPnP -> Enable -> Save",
            "4. Click Re-detect Router in this tool",
            "",
            "NOTE: Cox gateways may have limited exposed settings.",
            "Try the Panoramic WiFi app or call Cox if UPnP not visible.",
        ]
    },
    "Eero (Amazon)": {
        "url": "(no browser admin - use Eero app)",
        "user": "(Eero app)", "password": "(Eero app)",
        "steps": [
            "NOTE: Eero has NO browser admin page.",
            "Use the Eero mobile app only:",
            "",
            "1. Open Eero app on your phone",
            "2. Tap menu icon top-left",
            "3. Settings -> Network Settings",
            "4. Find UPnP and toggle ON",
            "5. Wait 10 seconds",
            "6. Click Re-detect Router in this tool",
        ]
    },
    "Google Nest WiFi / Google WiFi": {
        "url": "(no browser admin - use Google Home app)",
        "user": "(Google account)", "password": "(Google account)",
        "steps": [
            "NOTE: Google routers do NOT support UPnP at all.",
            "",
            "Your options:",
            "1. Manual port forwarding via Google Home app:",
            "   Home app -> Wi-Fi -> Settings",
            "   -> Advanced Networking -> Port Management",
            "   Add: UDP 3074 -> your PC IP",
            "   Add: UDP 30000 -> your PC IP",
            "",
            "2. Use a UPnP-capable router instead:",
            "   (ASUS, TP-Link, Netgear all work well)",
        ]
    },
    "I don't know my router brand": {
        "url": "(see steps to find it)",
        "user": "admin", "password": "admin (most common default)",
        "steps": [
            "FIND YOUR ROUTER ADDRESS:",
            "  1. Press Windows Key + R",
            "  2. Type: cmd  and press Enter",
            "  3. Type: ipconfig  and press Enter",
            "  4. Find Default Gateway - that is your router address",
            "  5. Type it in your browser e.g. http://192.168.1.1",
            "",
            "COMMON ADDRESSES TO TRY:",
            "  http://192.168.1.1   (ASUS, Netgear, Linksys - most common)",
            "  http://192.168.0.1   (TP-Link, D-Link)",
            "  http://10.0.0.1      (Xfinity)",
            "  http://192.168.100.1 (Motorola/Arris)",
            "  http://192.168.1.254 (AT&T)",
            "",
            "DEFAULT LOGIN:",
            "  Try: admin / admin",
            "  If that fails, check sticker on bottom of router",
            "",
            "FIND UPnP:",
            "  Look under Advanced, WAN, Firewall, or NAT settings",
            "  Enable UPnP and save, then click Re-detect Router",
        ]
    },
}


def _get_default_gateway():
    """Return the default gateway IP by parsing ipconfig output."""
    try:
        out = subprocess.check_output(
            ["ipconfig"], stderr=subprocess.DEVNULL, creationflags=NO_WIN
        ).decode(errors="ignore")
        for line in out.splitlines():
            if "Default Gateway" in line:
                m = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                if m and not m.group(1).startswith("0."):
                    return m.group(1)
    except Exception:
        pass
    return None


def discover_gateway(timeout=8):
    """Send M-SEARCH probes for multiple service types, retrying each twice.

    Strategy:
    - Bind to the local IP so the correct network interface is used
    - Send multicast AND unicast (to default gateway) for each service type —
      many routers ignore multicast but respond to unicast on port 1900
    - Each probe is sent twice to handle routers that drop the first packet
    - Responses are collected for the full timeout window
    """
    local_ip = get_local_ip()
    gateway_ip = _get_default_gateway()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 4)
    # Bind to the local IP so multicast/responses use the correct interface
    try:
        sock.bind((local_ip, 0))
    except Exception:
        try:
            sock.bind(('', 0))
        except Exception:
            pass

    # Build target list: always multicast, plus unicast to gateway if known
    targets = [(SSDP_ADDR, SSDP_PORT)]
    if gateway_ip:
        targets.append((gateway_ip, SSDP_PORT))

    try:
        for st in SSDP_ST_LIST:
            req = _ssdp_request(st)
            for target in targets:
                for _ in range(2):
                    try:
                        sock.sendto(req, target)
                    except Exception:
                        pass
                    time.sleep(0.05)

        # Collect responses until the deadline
        deadline = time.monotonic() + timeout
        seen = set()
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            sock.settimeout(remaining)
            try:
                data, addr = sock.recvfrom(65507)
                response = data.decode("utf-8", errors="ignore")
                for line in response.splitlines():
                    if line.strip().lower().startswith("location:"):
                        loc = line.split(":", 1)[1].strip()
                        if loc not in seen:
                            seen.add(loc)
                            return loc, addr[0]
            except socket.timeout:
                break
    finally:
        sock.close()
    return None, None


def get_service_url(location):
    with urllib.request.urlopen(location, timeout=5) as r:
        xml_str = r.read().decode("utf-8", errors="ignore")
    xml_str = re.sub(r'\s+xmlns[^"]*"[^"]*"', '', xml_str)
    xml_str = re.sub(r'<(\w+):([^>]*)>', r'<\2>', xml_str)
    xml_str = re.sub(r'</(\w+):([^>]*)>', r'</\2>', xml_str)
    root = ET.fromstring(xml_str)
    base_url = "/".join(location.split("/")[:3])
    for service in root.iter("service"):
        st = service.findtext("serviceType") or ""
        for target in ["WANIPConnection:1", "WANIPConnection:2", "WANPPPConnection:1"]:
            if target in st:
                ctrl = service.findtext("controlURL") or ""
                if not ctrl.startswith("http"):
                    ctrl = base_url + ("" if ctrl.startswith("/") else "/") + ctrl
                return ctrl, st
    raise RuntimeError("No WANIPConnection service found")


def soap_action(url, stype, action, args=""):
    body = (f'<?xml version="1.0"?>'
            f'<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"'
            f' s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">'
            f'<s:Body><u:{action} xmlns:u="{stype}">{args}</u:{action}></s:Body></s:Envelope>')
    encoded = body.encode()
    req = urllib.request.Request(url, data=encoded, method="POST",
        headers={"Content-Type": "text/xml; charset=utf-8",
                 "SOAPAction": f'"{stype}#{action}"',
                 "Content-Length": str(len(encoded))})
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            return r.read().decode("utf-8", errors="ignore"), r.status
    except urllib.error.HTTPError as e:
        return e.read().decode("utf-8", errors="ignore"), e.code
    except urllib.error.URLError as e:
        return f"URLError: {e.reason}", 0
    except Exception as e:
        return f"Error: {e}", 0


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


def add_port(ctrl, stype, lip, port, proto, desc):
    args = (f"<NewRemoteHost></NewRemoteHost>"
            f"<NewExternalPort>{port}</NewExternalPort>"
            f"<NewProtocol>{proto}</NewProtocol>"
            f"<NewInternalPort>{port}</NewInternalPort>"
            f"<NewInternalClient>{lip}</NewInternalClient>"
            f"<NewEnabled>1</NewEnabled>"
            f"<NewPortMappingDescription>{desc}</NewPortMappingDescription>"
            f"<NewLeaseDuration>0</NewLeaseDuration>")
    return soap_action(ctrl, stype, "AddPortMapping", args)


def del_port(ctrl, stype, port, proto):
    args = (f"<NewRemoteHost></NewRemoteHost>"
            f"<NewExternalPort>{port}</NewExternalPort>"
            f"<NewProtocol>{proto}</NewProtocol>")
    return soap_action(ctrl, stype, "DeletePortMapping", args)


def get_ext_ip(ctrl, stype):
    resp, status = soap_action(ctrl, stype, "GetExternalIPAddress")
    if status == 200:
        m = re.search(r"<NewExternalIPAddress>(.*?)</NewExternalIPAddress>", resp)
        if m:
            return m.group(1)
    return "Unknown"


class RouterGuideWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Router Setup Guide")
        self.resizable(False, False)
        self.configure(bg="#1a1a2e")
        self.grab_set()

        hdr = tk.Frame(self, bg=ACC, pady=10)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="Router Setup Guide",
                 font=("Segoe UI", 14, "bold"), bg=ACC, fg=FG).pack()
        tk.Label(hdr, text="Select your router to get default login info and UPnP enable steps",
                 font=("Segoe UI", 9), bg=ACC, fg=DIM).pack()

        sel = tk.Frame(self, bg=BG, padx=20, pady=12)
        sel.pack(fill=tk.X)
        tk.Label(sel, text="Router Brand:", font=("Segoe UI", 10, "bold"),
                 bg=BG, fg=FG).pack(side=tk.LEFT, padx=(0, 10))
        self.bvar = tk.StringVar(value="--- Select your router brand ---")
        cb = ttk.Combobox(sel, textvariable=self.bvar, values=list(ROUTERS.keys()),
                          state="readonly", width=36, font=("Segoe UI", 10))
        cb.pack(side=tk.LEFT)
        cb.bind("<<ComboboxSelected>>", self._sel)

        cf = tk.Frame(self, bg=CARD, padx=20, pady=12)
        cf.pack(fill=tk.X, padx=16, pady=4)

        def crow(lbl, var):
            f = tk.Frame(cf, bg=CARD); f.pack(fill=tk.X, pady=3)
            tk.Label(f, text=lbl, font=("Segoe UI", 9), bg=CARD,
                     fg=DIM, width=16, anchor="w").pack(side=tk.LEFT)
            tk.Label(f, textvariable=var, font=("Consolas", 10, "bold"),
                     bg=CARD, fg=GRN).pack(side=tk.LEFT)

        self.vurl  = tk.StringVar(value="—")
        self.vuser = tk.StringVar(value="—")
        self.vpass = tk.StringVar(value="—")
        crow("Admin URL:",  self.vurl)
        crow("Username:",   self.vuser)
        crow("Password:",   self.vpass)

        self.bbtn = tk.Button(cf, text="Open Router Login Page in Browser",
                              font=("Segoe UI", 9, "bold"), bg=GOLD, fg="white",
                              relief=tk.FLAT, padx=12, pady=5, cursor="hand2",
                              command=self._browse, state=tk.DISABLED)
        self.bbtn.pack(pady=(10, 0))

        tk.Label(self, text="Steps to enable UPnP:",
                 font=("Segoe UI", 9, "bold"), bg=BG, fg=FG,
                 anchor="w").pack(fill=tk.X, padx=16, pady=(8, 2))

        sf = tk.Frame(self, bg=BG, padx=16)
        sf.pack(fill=tk.BOTH, expand=True)
        self.sbox = scrolledtext.ScrolledText(sf, height=14, width=64,
                                              bg="#0d0d1a", fg="#aaccff",
                                              font=("Segoe UI", 9),
                                              relief=tk.FLAT, borderwidth=0,
                                              state=tk.DISABLED, wrap=tk.WORD)
        self.sbox.pack(fill=tk.BOTH, expand=True)

        tk.Button(self, text="Close", font=("Segoe UI", 10, "bold"),
                  bg="#333355", fg=FG, relief=tk.FLAT,
                  padx=18, pady=8, cursor="hand2",
                  command=self.destroy).pack(pady=10)
        self._url = None

    def _sel(self, _=None):
        info = ROUTERS.get(self.bvar.get())
        if not info:
            return
        self.vurl.set(info["url"])
        self.vuser.set(info["user"])
        self.vpass.set(info["password"])
        self._url = info["url"] if info["url"].startswith("http") else None
        self.bbtn.configure(state=tk.NORMAL if self._url else tk.DISABLED)
        self.sbox.configure(state=tk.NORMAL)
        self.sbox.delete("1.0", tk.END)
        for line in info["steps"]:
            self.sbox.insert(tk.END, line + "\n")
        self.sbox.configure(state=tk.DISABLED)

    def _browse(self):
        if self._url:
            webbrowser.open(self._url)


# ── Diagnostics checks ────────────────────────────────────────────────────────
def check_xlink_running():
    """Check if kaiEngine.exe or XLink Kai process is running."""
    try:
        out = subprocess.check_output(
            ["tasklist", "/FI", "IMAGENAME eq kaiEngine.exe", "/NH"],
            stderr=subprocess.DEVNULL, creationflags=NO_WIN).decode(errors="ignore")
        if "kaiEngine.exe" in out:
            return True, "kaiEngine.exe is running"
        # Also check for XLinkKai.exe
        out2 = subprocess.check_output(
            ["tasklist", "/FI", "IMAGENAME eq XLinkKai.exe", "/NH"],
            stderr=subprocess.DEVNULL, creationflags=NO_WIN).decode(errors="ignore")
        if "XLinkKai.exe" in out2:
            return True, "XLinkKai.exe is running"
        return False, "Xlink Kai is NOT running (kaiEngine.exe not found)"
    except Exception as e:
        return None, f"Could not check processes: {e}"


def check_xlink_webui():
    """Try to reach Xlink Kai web UI at localhost:34522."""
    try:
        urllib.request.urlopen("http://127.0.0.1:34522/", timeout=2)
        return True, "Xlink Kai web UI reachable at http://localhost:34522"
    except urllib.error.URLError:
        return False, "Xlink Kai web UI not reachable (port 34522 not responding)"
    except Exception as e:
        return False, f"Web UI check failed: {e}"


def get_all_firewall_rules():
    """Fetch all inbound Windows Firewall rules once and return the raw text.

    Both check_firewall_ports and check_kaiengine_firewall accept this cached
    text so the expensive netsh call is only made once per diagnostic run.
    Returns empty string on failure (callers handle the empty case).
    """
    try:
        return subprocess.check_output(
            ["netsh", "advfirewall", "firewall", "show", "rule", "name=all",
             "dir=in", "verbose"],
            stderr=subprocess.DEVNULL, creationflags=NO_WIN).decode(errors="ignore")
    except Exception:
        return ""


def check_firewall_ports(rules_text=None):
    """Check Windows Firewall for UDP 3074 and 30000 rules."""
    if rules_text is None:
        rules_text = get_all_firewall_rules()

    results = []
    if not rules_text:
        for port, _, _ in PORTS:
            results.append((None, port, f"Could not query firewall rules"))
        return results

    all_rules = rules_text.lower()
    blocks = all_rules.split("rule name:")

    for port, _, _ in PORTS:
        port_str = str(port)
        rule_name = f"xlink kai udp {port_str}"
        found = False
        enabled = False

        for block in blocks:
            # Use regex so whitespace differences between Windows versions don't matter
            has_port = bool(
                re.search(r'localport:\s+' + re.escape(port_str) + r'(,|\s|$)', block)
            ) or (
                re.search(r'localport:\s+any', block) and rule_name in block
            ) or rule_name in block
            if has_port and "udp" in block:
                found = True
                enabled = bool(re.search(r'enabled:\s+yes', block))
                break

        if found and enabled:
            results.append((True, port, f"Firewall rule active for UDP {port}"))
        elif found and not enabled:
            results.append((None, port, f"Firewall rule exists for UDP {port} but is disabled"))
        else:
            results.append((False, port, f"No firewall rule found for UDP {port}"))

    return results


def check_kaiengine_firewall(rules_text=None):
    """Check if kaiEngine.exe has a Windows Firewall exception."""
    if rules_text is None:
        rules_text = get_all_firewall_rules()
    if not rules_text:
        return None, "Could not query firewall rules"
    has_kai = "kaiengine" in rules_text.lower() or "xlink" in rules_text.lower()
    if has_kai:
        return True, "kaiEngine.exe has a Windows Firewall exception"
    return False, "No firewall exception found for kaiEngine.exe"


def check_network_adapters():
    """List network adapters and flag WiFi vs Ethernet."""
    try:
        out = subprocess.check_output(
            ["netsh", "interface", "show", "interface"],
            stderr=subprocess.DEVNULL, creationflags=NO_WIN).decode(errors="ignore")
        lines = [l for l in out.splitlines() if "Connected" in l]
        adapters = []
        for line in lines:
            parts = line.split()
            name = " ".join(parts[3:]) if len(parts) >= 4 else line
            is_wifi = any(w in name.lower() for w in ["wi-fi","wifi","wireless","wlan","802.11"])
            adapters.append((name, is_wifi))
        return adapters
    except Exception as e:
        return []


def check_xbox_on_network():
    """Attempt to detect an Xbox on the LAN via ARP table (MAC prefix check)."""
    xbox_prefixes = [
        "00:50:f2","00:0d:3a","00:12:5a","00:17:fa",
        "00:25:ae","28:18:78","60:45:cb","98:5f:d3",
    ]
    try:
        out = subprocess.check_output(
            ["arp", "-a"], stderr=subprocess.DEVNULL,
            creationflags=NO_WIN).decode(errors="ignore")
        found = []
        for line in out.splitlines():
            line_low = line.lower().replace("-",":")
            for pfx in xbox_prefixes:
                if pfx in line_low:
                    parts = line.split()
                    ip = parts[0] if parts else "unknown"
                    found.append(ip)
        if found:
            return True, f"Xbox detected on network at: {', '.join(found)}"
        return False, "No Xbox detected in ARP table (is Xbox on and connected?)"
    except Exception as e:
        return None, f"ARP check failed: {e}"


def check_orbital_ping():
    """Ping Xlink Kai orbital server."""
    orbital = "149.56.47.64"
    try:
        out = subprocess.check_output(
            ["ping", "-n", "3", "-w", "2000", orbital],
            stderr=subprocess.DEVNULL, creationflags=NO_WIN).decode(errors="ignore")
        if "TTL=" in out or "ttl=" in out.lower():
            # Extract avg ms
            m = re.search(r"Average = (\d+)ms", out)
            avg = m.group(1) + "ms" if m else "OK"
            return True, f"Xlink Kai orbital server reachable (avg {avg})"
        return False, "Xlink Kai orbital server not reachable (ping failed)"
    except Exception as e:
        return None, f"Ping check failed: {e}"


def check_connection_sharing():
    """Check if Internet Connection Sharing is enabled (can interfere with Xlink Kai)."""
    try:
        out = subprocess.check_output(
            ["netsh", "interface", "ipv4", "show", "addresses"],
            stderr=subprocess.DEVNULL, creationflags=NO_WIN).decode(errors="ignore")
        # ICS host typically assigns 192.168.137.x
        if "192.168.137" in out:
            return False, "Internet Connection Sharing (ICS) may be active - can interfere with Xlink Kai"
        return True, "No Internet Connection Sharing conflicts detected"
    except Exception as e:
        return None, f"ICS check failed: {e}"


def check_vpn_active():
    """Check if a VPN adapter is active (VPNs break Xlink Kai)."""
    vpn_keywords = ["vpn","nordvpn","expressvpn","proton","mullvad","wireguard","openvpn","tap-windows","tun"]
    try:
        out = subprocess.check_output(
            ["ipconfig", "/all"],
            stderr=subprocess.DEVNULL, creationflags=NO_WIN).decode(errors="ignore")
        found = []
        current = ""
        for line in out.splitlines():
            if "adapter" in line.lower():
                current = line
            if any(k in line.lower() or k in current.lower() for k in vpn_keywords):
                if "Media State" not in line and "disconnected" not in line.lower():
                    name = re.search(r"adapter (.+):", current)
                    if name and name.group(1) not in found:
                        found.append(name.group(1).strip())
        if found:
            return False, f"VPN adapter detected: {', '.join(found[:2])} - disable VPN before using Xlink Kai"
        return True, "No active VPN adapters detected"
    except Exception as e:
        return None, f"VPN check failed: {e}"


def add_firewall_rules():
    """Add Windows Firewall inbound rules for UDP 3074 and 30000."""
    results = []
    for port in [3074, 30000]:
        rule_name = f"Xlink Kai UDP {port}"
        try:
            # Delete existing rule first to avoid duplicates
            subprocess.run([
                "netsh", "advfirewall", "firewall", "delete", "rule",
                f"name={rule_name}"
            ], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
               creationflags=NO_WIN)
            # Add fresh rule
            subprocess.check_call([
                "netsh", "advfirewall", "firewall", "add", "rule",
                f"name={rule_name}",
                "dir=in", "action=allow", "protocol=UDP",
                f"localport={port}", "enable=yes",
                "profile=any"
            ], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
               creationflags=NO_WIN)
            results.append((True, port, f"Firewall rule added for UDP {port}"))
        except subprocess.CalledProcessError:
            results.append((False, port, f"Failed to add rule for UDP {port} (run as Administrator)"))
        except Exception as e:
            results.append((False, port, f"Error adding rule for UDP {port}: {e}"))
    return results


def add_kaiengine_exception():
    """Add Windows Firewall exception for kaiEngine.exe."""
    # Find kaiEngine.exe
    common_paths = [
        r"C:\Program Files (x86)\XLink Kai\kaiEngine.exe",
        r"C:\Program Files\XLink Kai\kaiEngine.exe",
        r"C:\XLink Kai\kaiEngine.exe",
    ]
    kai_path = None
    for p in common_paths:
        if os.path.exists(p):
            kai_path = p
            break
    if not kai_path:
        return None, "kaiEngine.exe not found in standard install locations"
    try:
        subprocess.check_call([
            "netsh", "advfirewall", "firewall", "add", "rule",
            "name=XLink Kai Engine",
            "dir=in", "action=allow", "protocol=any",
            f"program={kai_path}", "enable=yes", "profile=any"
        ], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
           creationflags=NO_WIN)
        return True, f"Firewall exception added for kaiEngine.exe"
    except Exception as e:
        return False, f"Failed to add exception: {e}"


# ── Diagnostics Window ────────────────────────────────────────────────────────
class DiagnosticsWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Xlink Kai Diagnostics")
        self.resizable(False, False)
        self.configure(bg="#1a1a2e")
        self.grab_set()

        self._log_tag = 0

        # Header
        hdr = tk.Frame(self, bg=ACC, pady=10)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="🔍  Xlink Kai Setup Diagnostics",
                 font=("Segoe UI", 14, "bold"), bg=ACC, fg=FG).pack()
        tk.Label(hdr, text="Automatic checks for common Xlink Kai / Rainbow Six setup issues",
                 font=("Segoe UI", 9), bg=ACC, fg=DIM).pack()

        # Check results area
        res_frame = tk.Frame(self, bg=BG, padx=16, pady=8)
        res_frame.pack(fill=tk.X)

        # Scrollable results list
        list_frame = tk.Frame(self, bg=BG, padx=16)
        list_frame.pack(fill=tk.BOTH, expand=True)

        self.result_canvas = tk.Canvas(list_frame, bg=BG, highlightthickness=0, height=340)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical",
                                   command=self.result_canvas.yview)
        self.result_canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.result_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.inner = tk.Frame(self.result_canvas, bg=BG)
        self.canvas_window = self.result_canvas.create_window(
            (0, 0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>", lambda e: self.result_canvas.configure(
            scrollregion=self.result_canvas.bbox("all")))
        self.result_canvas.bind("<Configure>",
            lambda e: self.result_canvas.itemconfig(
                self.canvas_window, width=e.width))

        # Progress / status bar
        self.progress_var = tk.StringVar(value="Click 'Run Diagnostics' to begin")
        prog_frame = tk.Frame(self, bg=CARD, padx=16, pady=6)
        prog_frame.pack(fill=tk.X)
        tk.Label(prog_frame, textvariable=self.progress_var,
                 font=("Segoe UI", 9), bg=CARD, fg=DIM).pack(side=tk.LEFT)

        # Log box for fix output
        tk.Label(self, text="Fix Log:", font=("Segoe UI", 9, "bold"),
                 bg=BG, fg=FG, anchor="w").pack(fill=tk.X, padx=16, pady=(6, 2))
        log_frame = tk.Frame(self, bg=BG, padx=16)
        log_frame.pack(fill=tk.X)
        self.flog = scrolledtext.ScrolledText(
            log_frame, height=5, width=70,
            bg="#0d0d1a", fg="#00ff88",
            font=("Consolas", 8), relief=tk.FLAT, borderwidth=0,
            state=tk.DISABLED)
        self.flog.pack(fill=tk.X)

        # Buttons
        bf = tk.Frame(self, bg=BG, padx=16, pady=10)
        bf.pack(fill=tk.X)
        s = {"font": ("Segoe UI", 10, "bold"), "relief": tk.FLAT,
             "padx": 14, "pady": 7, "cursor": "hand2"}

        self.btn_run = tk.Button(bf, text="▶  Run Diagnostics",
                                  bg=GOLD, fg="white",
                                  command=self._run_all, **s)
        self.btn_run.pack(side=tk.LEFT, padx=(0, 8))

        self.btn_fix = tk.Button(bf, text="🔧  Auto-Fix Issues",
                                  bg=ACC, fg=FG, state=tk.DISABLED,
                                  command=self._auto_fix, **s)
        self.btn_fix.pack(side=tk.LEFT, padx=(0, 8))

        tk.Button(bf, text="✕  Close", bg="#333355", fg=FG,
                  command=self.destroy, **s).pack(side=tk.RIGHT)

        # State
        self._rows = {}
        self._issues = []

    def _flog(self, msg, color="#00ff88"):
        self.flog.configure(state=tk.NORMAL)
        self._log_tag += 1
        tag = f"t{self._log_tag}"
        self.flog.insert(tk.END, msg + "\n", tag)
        self.flog.tag_config(tag, foreground=color)
        self.flog.see(tk.END)
        self.flog.configure(state=tk.DISABLED)

    def _clear_results(self):
        for w in self.inner.winfo_children():
            w.destroy()
        self._rows = {}
        self._issues = []

    def _add_row(self, key, label):
        """Add a check row with pending status."""
        frame = tk.Frame(self.inner, bg=CARD, pady=4, padx=12)
        frame.pack(fill=tk.X, pady=2, padx=4)

        icon_var = tk.StringVar(value="⏳")
        msg_var  = tk.StringVar(value="Checking...")

        tk.Label(frame, textvariable=icon_var, font=("Segoe UI", 11),
                 bg=CARD, width=2).pack(side=tk.LEFT, padx=(0, 8))
        tk.Label(frame, text=label, font=("Segoe UI", 9, "bold"),
                 bg=CARD, fg=FG, width=28, anchor="w").pack(side=tk.LEFT)
        tk.Label(frame, textvariable=msg_var, font=("Segoe UI", 9),
                 bg=CARD, fg=DIM, anchor="w").pack(side=tk.LEFT, fill=tk.X, expand=True)

        self._rows[key] = (icon_var, msg_var, frame)

    def _update_row(self, key, status, message):
        """Update a row: status = True/False/None (warn)."""
        if key not in self._rows:
            return
        icon_var, msg_var, frame = self._rows[key]
        if status is True:
            icon_var.set("✅")
            msg_var.set(message)
            frame.configure(bg="#0d2b0d")
            for w in frame.winfo_children():
                w.configure(bg="#0d2b0d")
        elif status is False:
            icon_var.set("❌")
            msg_var.set(message)
            frame.configure(bg="#2b0d0d")
            for w in frame.winfo_children():
                w.configure(bg="#2b0d0d")
            self._issues.append(key)
        else:  # None = warning — also fixable
            icon_var.set("⚠️")
            msg_var.set(message)
            frame.configure(bg="#2b2200")
            for w in frame.winfo_children():
                w.configure(bg="#2b2200")
            self._issues.append(key)  # warnings are also fixable

    def _run_all(self):
        self.btn_run.configure(state=tk.DISABLED)
        self.btn_fix.configure(state=tk.DISABLED)
        self._clear_results()

        checks = [
            ("xlink_running",    "Xlink Kai Running"),
            ("webui",            "Xlink Kai Web UI"),
            ("orbital",          "Orbital Server Ping"),
            ("vpn",              "VPN Interference"),
            ("ics",              "Connection Sharing"),
            ("adapters",         "Network Adapters"),
            ("xbox",             "Xbox on Network"),
            ("fw_ports",         "Firewall UDP 3074/30000"),
            ("fw_kaiengine",     "Firewall kaiEngine.exe"),
        ]
        for key, label in checks:
            self._add_row(key, label)

        threading.Thread(target=self._run_checks, daemon=True).start()

    def _run_checks(self):
        def upd(key, ok, msg):
            self.after(0, lambda: self._update_row(key, ok, msg))
        def prog(msg):
            self.after(0, lambda: self.progress_var.set(msg))

        # 1. Xlink Kai running
        prog("Checking if Xlink Kai is running...")
        ok, msg = check_xlink_running()
        upd("xlink_running", ok, msg)

        # 2. Web UI reachable
        prog("Checking Xlink Kai web UI...")
        ok, msg = check_xlink_webui()
        upd("webui", ok, msg)

        # 3. Orbital ping
        prog("Pinging Xlink Kai orbital server...")
        ok, msg = check_orbital_ping()
        upd("orbital", ok, msg)

        # 4. VPN check
        prog("Checking for active VPN...")
        ok, msg = check_vpn_active()
        upd("vpn", ok, msg)

        # 5. ICS check
        prog("Checking Internet Connection Sharing...")
        ok, msg = check_connection_sharing()
        upd("ics", ok, msg)

        # 6. Adapter check
        prog("Checking network adapters...")
        adapters = check_network_adapters()
        if not adapters:
            upd("adapters", None, "Could not enumerate adapters")
        else:
            wifi = [a for a, w in adapters if w]
            wired = [a for a, w in adapters if not w]
            if wifi and not wired:
                upd("adapters", False,
                    f"Only WiFi detected: {wifi[0]} — use Ethernet for best results")
            elif wifi and wired:
                upd("adapters", None,
                    f"Both WiFi & Ethernet active — ensure Xlink Kai uses: {wired[0]}")
            else:
                upd("adapters", True,
                    f"Wired adapter active: {wired[0] if wired else 'OK'}")

        # 7. Xbox on network
        prog("Scanning for Xbox on network...")
        ok, msg = check_xbox_on_network()
        upd("xbox", ok, msg)

        # 8 & 9 share a single netsh call
        prog("Checking Windows Firewall rules...")
        fw_rules_cache = get_all_firewall_rules()

        fw_results = check_firewall_ports(fw_rules_cache)
        all_ok = all(r[0] is True for r in fw_results)
        any_missing = any(r[0] is False for r in fw_results)
        summary = "  |  ".join(
            f"UDP {r[1]}: {'OK' if r[0] is True else 'MISSING'}" for r in fw_results)
        upd("fw_ports",
            True if all_ok else (False if any_missing else None),
            summary)

        # 9. kaiEngine firewall exception (reuses cached rules)
        prog("Checking kaiEngine.exe firewall exception...")
        ok, msg = check_kaiengine_firewall(fw_rules_cache)
        upd("fw_kaiengine", ok, msg)

        # Done
        issue_count = len(self._issues)
        if issue_count == 0:
            prog("✅ All checks passed! Your setup looks good.")
        else:
            # Count warnings vs errors
            err_keys = [k for k in self._issues if self._rows[k][0].get() == "❌"]
            warn_keys = [k for k in self._issues if self._rows[k][0].get() == "⚠️"]
            parts = []
            if err_keys:
                parts.append(f"{len(err_keys)} error(s)")
            if warn_keys:
                parts.append(f"{len(warn_keys)} warning(s)")
            prog(f"Found {', '.join(parts)} — click Auto-Fix to resolve")
            self.after(0, lambda: self.btn_fix.configure(state=tk.NORMAL))

        self.after(0, lambda: self.btn_run.configure(state=tk.NORMAL))

    def _auto_fix(self):
        self.btn_fix.configure(state=tk.DISABLED)
        self.btn_run.configure(state=tk.DISABLED)
        threading.Thread(target=self._do_fixes, daemon=True).start()

    def _do_fixes(self):
        fixed = 0

        if "fw_ports" in self._issues:
            self._flog("Adding Windows Firewall rules for UDP 3074 & 30000...", "#88aaff")
            results = add_firewall_rules()
            for ok, port, msg in results:
                color = "#00ff88" if ok else "#ff4466"
                self._flog(f"  UDP {port}: {msg}", color)
                if ok:
                    fixed += 1

        if "fw_kaiengine" in self._issues:
            self._flog("Adding firewall exception for kaiEngine.exe...", "#88aaff")
            ok, msg = add_kaiengine_exception()
            color = "#00ff88" if ok else ("#ff4466" if ok is False else "#ffaa44")
            self._flog(f"  {msg}", color)
            if ok:
                fixed += 1

        if "vpn" in self._issues:
            self._flog("VPN detected — please disable your VPN manually then re-run diagnostics.", "#ffaa44")

        if "xlink_running" in self._issues:
            self._flog("Xlink Kai is not running — please launch it then re-run diagnostics.", "#ffaa44")
            self._flog("Download: https://www.teamxlink.co.uk/", "#88aaff")

        if "adapters" in self._issues:
            self._flog("WiFi-only detected — connect your PC to router via Ethernet cable for best results.", "#ffaa44")

        if "xbox" in self._issues:
            self._flog("Xbox not detected — make sure your Xbox is powered on and connected to the same network.", "#ffaa44")

        if fixed > 0:
            self._flog(f"\nAuto-fixed {fixed} issue(s). Re-run diagnostics to verify.", "#00ff88")
        else:
            self._flog("\nManual action required for remaining issues (see messages above).", "#ffaa44")

        self.after(0, lambda: self.btn_run.configure(state=tk.NORMAL))
        self.after(0, lambda: self.progress_var.set("Fix complete — click Run Diagnostics to re-check"))



class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Xlink Kai Port Opener  v2")
        self.resizable(False, False)
        self.configure(bg=BG)
        self.ctrl = self.stype = self.lip = self.gwip = None
        self._log_tag = 0
        self._build()

    def _build(self):
        # ── Watermark header banner ───────────────────────────────────────────
        wm = draw_watermark(self, bg=ACC)
        wm.pack(fill=tk.X, padx=0, pady=0)

        gb = tk.Frame(self, bg="#0f2040", padx=16, pady=8)
        gb.pack(fill=tk.X)
        tk.Label(gb, text="First time setup?  Connection problems?",
                 font=("Segoe UI", 9), bg="#0f2040", fg="#aaccff").pack(side=tk.LEFT)
        tk.Button(gb, text="🔍  Diagnostics",
                  font=("Segoe UI", 9, "bold"), bg="#e94560", fg="white",
                  relief=tk.FLAT, padx=10, pady=3, cursor="hand2",
                  command=lambda: DiagnosticsWindow(self)).pack(side=tk.RIGHT, padx=(4,0))
        tk.Button(gb, text="📖  Router Setup Guide",
                  font=("Segoe UI", 9, "bold"), bg=ACC, fg=FG,
                  relief=tk.FLAT, padx=10, pady=3, cursor="hand2",
                  command=lambda: RouterGuideWindow(self)).pack(side=tk.RIGHT)

        card = tk.Frame(self, bg=CARD, padx=20, pady=14)
        card.pack(fill=tk.X, padx=16, pady=(10, 4))

        def row(lbl, var, color=FG):
            f = tk.Frame(card, bg=CARD); f.pack(fill=tk.X, pady=2)
            tk.Label(f, text=lbl, font=("Segoe UI", 9), bg=CARD,
                     fg=DIM, width=18, anchor="w").pack(side=tk.LEFT)
            tk.Label(f, textvariable=var, font=("Segoe UI", 9, "bold"),
                     bg=CARD, fg=color).pack(side=tk.LEFT)

        self.vlan    = tk.StringVar(value="—")
        self.vgw     = tk.StringVar(value="—")
        self.vext    = tk.StringVar(value="—")
        self.vstatus = tk.StringVar(value="Not started")
        row("Your LAN IP:",  self.vlan)
        row("Router IP:",    self.vgw)
        row("External IP:",  self.vext)
        row("Ports Status:", self.vstatus, GOLD)

        lf = tk.Frame(self, bg=BG, padx=16)
        lf.pack(fill=tk.BOTH, expand=True, pady=(8, 4))
        self.log = scrolledtext.ScrolledText(lf, height=12, width=62,
                                             bg="#0d0d1a", fg="#00ff88",
                                             font=("Consolas", 9),
                                             relief=tk.FLAT, borderwidth=0,
                                             state=tk.DISABLED)
        self.log.pack(fill=tk.BOTH, expand=True)

        bf = tk.Frame(self, bg=BG, padx=16, pady=12)
        bf.pack(fill=tk.X)
        s = {"font": ("Segoe UI", 10, "bold"), "relief": tk.FLAT,
             "padx": 18, "pady": 8, "cursor": "hand2"}
        self.bopen = tk.Button(bf, text="Open Ports 3074 & 30000",
                               bg=GOLD, fg="white", state=tk.DISABLED,
                               command=self._run_open, **s)
        self.bopen.pack(side=tk.LEFT, padx=(0, 8))
        self.bclose = tk.Button(bf, text="Remove Rules",
                                bg=ACC, fg=FG, state=tk.DISABLED,
                                command=self._run_close, **s)
        self.bclose.pack(side=tk.LEFT, padx=(0, 8))
        tk.Button(bf, text="Re-detect Router", bg="#333355", fg=FG,
                  command=self._run_detect, **s).pack(side=tk.RIGHT)

        foot = tk.Frame(self, bg=BG)
        foot.pack(fill=tk.X, padx=16, pady=(0, 8))
        tk.Label(foot, text="UDP 3074 & 30000  |  Rainbow Six 3 / Black Arrow  |  Xlink Kai",
                 font=("Segoe UI", 8), bg=BG, fg=DIM).pack(side=tk.LEFT)
        tk.Label(foot, text="Created by Juv3nile",
                 font=("Segoe UI", 8, "bold"), bg=BG, fg=GOLD).pack(side=tk.RIGHT)

        self.after(300, self._run_detect)

    def _log(self, msg, color=None):
        self.log.configure(state=tk.NORMAL)
        self._log_tag += 1
        tag = f"t{self._log_tag}"
        self.log.insert(tk.END, msg + "\n", tag)
        if color:
            self.log.tag_config(tag, foreground=color)
        self.log.see(tk.END)
        self.log.configure(state=tk.DISABLED)

    def _ok(self, m):  self._log(f"OK  {m}", "#00ff88")
    def _err(self, m): self._log(f"ERR {m}", "#ff4466")
    def _inf(self, m): self._log(f"... {m}", "#88aaff")

    def _run_detect(self):
        self.bopen.configure(state=tk.DISABLED)
        self.bclose.configure(state=tk.DISABLED)
        threading.Thread(target=self._detect, daemon=True).start()

    def _detect(self):
        self._inf("Scanning for router via UPnP (trying multiple service types)...")
        self._inf("This may take up to 8 seconds on first attempt...")
        self.vstatus.set("Scanning...")
        lip = get_local_ip()
        self.vlan.set(lip)
        loc, gwip = discover_gateway(timeout=8)
        if not loc:
            self._err("No UPnP gateway found.")
            self._inf("Click 'Router Setup Guide' for help enabling UPnP.")
            self.vstatus.set("Router not found")
            return
        self._ok(f"Router found at {gwip}")
        self.vgw.set(gwip)
        self.gwip = gwip
        self.lip  = lip
        try:
            ctrl, stype = get_service_url(loc)
        except Exception as e:
            self._err(f"Could not parse router: {e}")
            self.vstatus.set("Parse error")
            return
        self.ctrl  = ctrl
        self.stype = stype
        ext = get_ext_ip(ctrl, stype)
        self.vext.set(ext)
        self._ok(f"External IP: {ext}")
        self.vstatus.set("Ready")
        self.bopen.configure(state=tk.NORMAL)

    def _run_open(self):
        self.bopen.configure(state=tk.DISABLED)
        threading.Thread(target=self._open, daemon=True).start()

    def _open(self):
        ok = 0
        try:
            for port, proto, desc in PORTS:
                self._inf(f"Sending request to router for {proto} {port}...")
                resp, status = add_port(self.ctrl, self.stype, self.lip, port, proto, desc)
                self._inf(f"Router responded: HTTP {status}")
                if status in (200, 204):
                    self._ok(f"Opened {proto} {port} -> {self.lip}:{port}")
                    ok += 1
                elif "ConflictInMappingEntry" in resp or "718" in resp or status == 718:
                    self._inf(f"{proto} {port} - rule already exists on router (OK)")
                    ok += 1
                elif status == 0:
                    self._err(f"No response from router for {proto} {port}: {resp}")
                else:
                    self._err(f"Failed {proto} {port} (HTTP {status}): {str(resp)[:80]}")
        except Exception as e:
            self._err(f"Unexpected error: {e}")
        finally:
            if ok == len(PORTS):
                self.vstatus.set("OPEN")
                self._ok("Both ports open. You can close this window.")
                self.bclose.configure(state=tk.NORMAL)
            else:
                self.vstatus.set("Failed - see log")
                self._err("Some ports failed. Check log above for details.")
                self._inf("Tips: Run as Administrator. Check UPnP is enabled on router.")
                self.bopen.configure(state=tk.NORMAL)

    def _run_close(self):
        self.bclose.configure(state=tk.DISABLED)
        threading.Thread(target=self._close, daemon=True).start()

    def _close(self):
        for port, proto, _ in PORTS:
            _, status = del_port(self.ctrl, self.stype, port, proto)
            if status in (200, 204):
                self._ok(f"UDP {port} removed.")
            else:
                self._err(f"UDP {port} remove failed (HTTP {status})")
        self.vstatus.set("Closed")
        self.bopen.configure(state=tk.NORMAL)


if __name__ == "__main__":
    App().mainloop()
