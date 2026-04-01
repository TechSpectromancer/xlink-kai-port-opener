"""
Xlink Kai Port Opener v2.0 - Automatic UPnP port forwarder
Opens UDP 3074 & 30000 on your router for better Xlink Kai connectivity
Includes Router Setup Guide for first-time users
No external dependencies - pure Python 3
"""

import socket
import urllib.request
import urllib.parse
import ipaddress
import datetime
import platform
import xml.etree.ElementTree as ET
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import threading
import time
import webbrowser
import re
import subprocess
import os
import sys
import ctypes
import logging
import pathlib

# ── Subprocess flag ────────────────────────────────────────────────────────────
NO_WIN = getattr(subprocess, "CREATE_NO_WINDOW", 0)

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

# ── Process / executable constants ─────────────────────────────────────────────
KAI_ENGINE_EXE   = "kaiEngine.exe"
XLINK_KAI_EXE    = "XLinkKai.exe"
KAI_WEBUI_PORT   = 34522
KAI_INSTALL_PATHS = [
    r"C:\Program Files (x86)\XLink Kai\kaiEngine.exe",
    r"C:\Program Files\XLink Kai\kaiEngine.exe",
    r"C:\XLink Kai\kaiEngine.exe",
]

def _ssdp_request(st):
    return (
        "M-SEARCH * HTTP/1.1\r\n"
        f"HOST: {SSDP_ADDR}:{SSDP_PORT}\r\n"
        "MAN: \"ssdp:discover\"\r\n"
        "MX: 3\r\n"
        f"ST: {st}\r\n\r\n"
    ).encode()


# ── Logging setup ─────────────────────────────────────────────────────────────
def _setup_logging(debug: bool = False) -> logging.Logger:
    log_dir = pathlib.Path(os.environ.get("APPDATA", ".")) / "XlinkKaiPortOpener"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "debug.log"
    level = logging.DEBUG if debug else logging.INFO
    handler = logging.FileHandler(log_file, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    log = logging.getLogger("xlink_kai")
    log.setLevel(level)
    if not log.handlers:
        log.addHandler(handler)
    return log

logger = _setup_logging()

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
    except (subprocess.CalledProcessError, OSError):
        pass
    return None


def _is_lan_url(location: str) -> bool:
    """Return True only if location is http:// pointing to a private/LAN address.

    Prevents SSRF by rejecting locations that point outside the local network.
    """
    try:
        parsed = urllib.parse.urlparse(location)
        if parsed.scheme != "http":
            return False
        host = parsed.hostname
        if not host:
            return False
        addr = ipaddress.ip_address(host)
        return addr.is_private or addr.is_loopback
    except (ValueError, Exception):
        return False


def discover_gateway(timeout=8):
    """Send M-SEARCH probes for multiple service types, retrying each twice.

    Strategy:
    - Bind to the local IP so the correct network interface is used
    - Send multicast AND unicast (to default gateway) for each service type —
      many routers ignore multicast but respond to unicast on port 1900
    - Each probe is sent twice to handle routers that drop the first packet
    - Responses are collected for the full timeout window
    """
    gateway_ip = _get_default_gateway()
    local_ip = get_local_ip(gateway_ip)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 4)
    # Bind to the local IP so multicast/responses use the correct interface
    try:
        sock.bind((local_ip, 0))
    except OSError:
        try:
            sock.bind(('', 0))
        except OSError:
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
                    except OSError:
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
                        if loc not in seen and _is_lan_url(loc):
                            seen.add(loc)
                            logger.info("Discovered gateway at %s (from %s)", loc, addr[0])
                            return loc, addr[0]
            except socket.timeout:
                break
    finally:
        sock.close()
    return None, None


def get_service_url(location):
    with urllib.request.urlopen(location, timeout=5) as r:
        xml_str = r.read().decode("utf-8", errors="ignore")
    root = ET.fromstring(xml_str)

    # Determine base URL: prefer URLBase from device description if present
    parsed_loc = urllib.parse.urlparse(location)
    base_url = f"{parsed_loc.scheme}://{parsed_loc.netloc}"
    for elem in root.iter():
        local = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        if local == "URLBase" and elem.text and elem.text.strip():
            base_url = elem.text.strip().rstrip("/")
            break

    # Walk all elements; strip namespace prefix to match serviceType/controlURL
    for elem in root.iter():
        if (elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag) != "service":
            continue
        st = ctrl = ""
        for child in elem:
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if tag == "serviceType":
                st = child.text or ""
            elif tag == "controlURL":
                ctrl = child.text or ""
        for target in ("WANIPConnection:1", "WANIPConnection:2", "WANPPPConnection:1"):
            if target in st:
                if not ctrl.startswith("http"):
                    ctrl = base_url + ("" if ctrl.startswith("/") else "/") + ctrl
                logger.info("Using UPnP service %s at %s", st, ctrl)
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
    except OSError as e:
        return f"Error: {e}", 0


def get_local_ip(gateway: str = None) -> str:
    """Return the local IP used to reach `gateway` (or 8.8.8.8 as fallback).

    Passing the discovered gateway ensures we bind the same interface that
    UPnP responses came in on, which matters on multi-NIC hosts.
    """
    target = gateway if gateway else "8.8.8.8"
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect((target, 80))
        return s.getsockname()[0]
    except OSError:
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
        self.resizable(True, True)
        self.minsize(480, 460)
        self.configure(bg=BG)
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
    for exe in (KAI_ENGINE_EXE, XLINK_KAI_EXE):
        try:
            out = subprocess.check_output(
                ["tasklist", "/FI", f"IMAGENAME eq {exe}", "/NH", "/FO", "CSV"],
                stderr=subprocess.DEVNULL, creationflags=NO_WIN).decode(errors="ignore")
            for line in out.splitlines():
                parts = line.strip().strip('"').split('","')
                if parts and parts[0].lower() == exe.lower():
                    return True, f"{exe} is running"
        except (subprocess.CalledProcessError, OSError) as e:
            return None, f"Could not check processes: {e}"
    return False, f"Xlink Kai is NOT running ({KAI_ENGINE_EXE} not found)"


def check_xlink_webui():
    """Try to reach Xlink Kai web UI at localhost:34522."""
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{KAI_WEBUI_PORT}/", timeout=2)
        return True, f"Xlink Kai web UI reachable at http://localhost:{KAI_WEBUI_PORT}"
    except urllib.error.URLError:
        return False, f"Xlink Kai web UI not reachable (port {KAI_WEBUI_PORT} not responding)"
    except OSError as e:
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
    except (subprocess.CalledProcessError, OSError):
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
    except (subprocess.CalledProcessError, OSError):
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
    except (subprocess.CalledProcessError, OSError) as e:
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
    except (subprocess.CalledProcessError, OSError) as e:
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
    except (subprocess.CalledProcessError, OSError) as e:
        return None, f"ICS check failed: {e}"


def check_admin():
    """Check if the process is running with Administrator privileges."""
    try:
        is_admin = bool(ctypes.windll.shell32.IsUserAnAdmin())
        if is_admin:
            return True, "Running as Administrator — Auto-Fix has full permissions"
        return False, "Not running as Administrator — Auto-Fix (firewall rules) may fail"
    except OSError as e:
        return None, f"Could not check admin status: {e}"


def check_double_nat(ctrl, stype):
    """Check if the user is behind double NAT.

    Double NAT means the router's own WAN IP is a private address, indicating
    an upstream modem/router.  UPnP only opens ports on the first device — the
    outer NAT layer still blocks traffic and Xlink Kai will not connect.
    """
    if not ctrl or not stype:
        return None, "Router not detected — run Re-detect Router first"
    try:
        ext_ip = get_ext_ip(ctrl, stype)
        if ext_ip == "Unknown":
            return None, "Could not retrieve external IP from router"
        parts = ext_ip.split(".")
        if len(parts) != 4:
            return None, f"Unexpected IP format: {ext_ip}"
        first, second = int(parts[0]), int(parts[1])
        is_private = (
            first == 10 or
            (first == 172 and 16 <= second <= 31) or
            (first == 192 and second == 168) or
            (first == 100 and 64 <= second <= 127)   # CGNAT RFC 6598
        )
        if is_private:
            return False, (f"Double NAT detected — router WAN IP {ext_ip} is a private address. "
                           f"Enable bridge/passthrough mode on your ISP modem to fix this.")
        return True, f"No double NAT — external IP {ext_ip} is a public address"
    except (OSError, ValueError) as e:
        return None, f"Double NAT check failed: {e}"


def check_network_profile():
    """Check if Windows network profile is set to Public.

    Public profile applies stricter firewall rules and can block Xlink Kai
    traffic even when port rules exist.  Private or Domain is required.
    """
    try:
        out = subprocess.check_output(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command",
             "Get-NetConnectionProfile | Select-Object -ExpandProperty NetworkCategory"],
            stderr=subprocess.DEVNULL, creationflags=NO_WIN
        ).decode(errors="ignore").strip()
        profiles = [p.strip() for p in out.splitlines() if p.strip()]
        if not profiles:
            return None, "Could not determine network profile"
        if "Public" in profiles:
            return False, ("Network set to Public profile — change to Private so Windows "
                           "allows Xlink Kai traffic through the firewall")
        return True, f"Network profile: {', '.join(profiles)} — OK"
    except (subprocess.CalledProcessError, OSError) as e:
        return None, f"Network profile check failed: {e}"


def fix_network_profile():
    """Attempt to set all Public network profiles to Private via PowerShell."""
    try:
        subprocess.check_call(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command",
             "Get-NetConnectionProfile | Where-Object {$_.NetworkCategory -eq 'Public'} "
             "| Set-NetConnectionProfile -NetworkCategory Private"],
            stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            creationflags=NO_WIN
        )
        return True, "Network profile changed to Private"
    except subprocess.CalledProcessError:
        return False, "Failed to change profile — re-run as Administrator"
    except OSError as e:
        return False, f"Could not change network profile: {e}"


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
    except (subprocess.CalledProcessError, OSError) as e:
        return None, f"VPN check failed: {e}"


def check_port_conflict():
    """Check if UDP 3074 or 30000 are bound by a process other than Xlink Kai."""
    try:
        # Get PIDs belonging to Xlink Kai so we can exclude them
        kai_pids = set()
        for exe in (KAI_ENGINE_EXE, XLINK_KAI_EXE):
            try:
                tl = subprocess.check_output(
                    ["tasklist", "/FI", f"IMAGENAME eq {exe}", "/NH", "/FO", "CSV"],
                    stderr=subprocess.DEVNULL, creationflags=NO_WIN
                ).decode(errors="ignore")
                for line in tl.splitlines():
                    parts = line.strip().strip('"').split('","')
                    if len(parts) >= 2:
                        try:
                            kai_pids.add(int(parts[1]))
                        except ValueError:
                            pass
            except (subprocess.CalledProcessError, OSError):
                pass

        # netstat -ano shows UDP lines with PIDs: "UDP  0.0.0.0:3074  *:*  12345"
        out = subprocess.check_output(
            ["netstat", "-ano"],
            stderr=subprocess.DEVNULL, creationflags=NO_WIN
        ).decode(errors="ignore")

        conflicts = []
        for port, _, _ in PORTS:
            for line in out.splitlines():
                m = re.match(r'\s*UDP\s+\S+:' + str(port) + r'\s+\S+\s+(\d+)', line)
                if m:
                    pid = int(m.group(1))
                    if pid not in kai_pids:
                        conflicts.append(f"UDP {port} (PID {pid})")

        if conflicts:
            return None, (f"Port(s) in use by another app: {', '.join(conflicts)} — "
                          f"see Auto-Fix log for how to identify and close it")
        return True, "UDP 3074 & 30000 are free — no port conflicts detected"
    except (subprocess.CalledProcessError, OSError) as e:
        return None, f"Port conflict check failed: {e}"


def check_upnp_conflicts(ctrl, stype):
    """Check if router already has 3074/30000 mapped to a different device."""
    if not ctrl or not stype:
        return None, "Router not detected — run Re-detect Router first"
    local_ip = get_local_ip()
    conflicts = []
    try:
        for port, proto, _ in PORTS:
            args = (f"<NewRemoteHost></NewRemoteHost>"
                    f"<NewExternalPort>{port}</NewExternalPort>"
                    f"<NewProtocol>{proto}</NewProtocol>")
            resp, status = soap_action(ctrl, stype, "GetSpecificPortMappingEntry", args)
            if status == 200:
                m = re.search(r"<NewInternalClient>(.*?)</NewInternalClient>", resp)
                if m:
                    mapped_ip = m.group(1).strip()
                    if mapped_ip and mapped_ip != local_ip:
                        conflicts.append(f"UDP {port} → {mapped_ip}")
        if conflicts:
            return False, (f"Router ports mapped to another device: {'; '.join(conflicts)} — "
                           f"remove those mappings or open ports from that device instead")
        return True, "No conflicting UPnP mappings on router"
    except OSError as e:
        return None, f"UPnP conflict check failed: {e}"


_MTU_SKIP = ("loopback", "pseudo", "isatap", "teredo", "6to4",
             "local area connection*", "virtual")

def _mtu_is_real_adapter(name):
    """Return True if this adapter name should be included in MTU checks."""
    n = name.lower()
    return not any(skip in n for skip in _MTU_SKIP)


def check_mtu():
    """Check if any physical/Wi-Fi adapter has an MTU above 1500."""
    try:
        out = subprocess.check_output(
            ["netsh", "interface", "ipv4", "show", "subinterfaces"],
            stderr=subprocess.DEVNULL, creationflags=NO_WIN
        ).decode(errors="ignore")
        high_mtu = []
        for line in out.splitlines():
            m = re.match(r'^\s*(\d+)\s+\d+\s+\d+\s+\d+\s+(.+)$', line)
            if m:
                mtu, name = int(m.group(1)), m.group(2).strip()
                if mtu > 1500 and _mtu_is_real_adapter(name):
                    high_mtu.append(f"{name} (MTU {mtu})")
        if high_mtu:
            return False, (f"High MTU on: {', '.join(high_mtu)} — "
                           f"values above 1500 cause fragmentation; Auto-Fix can correct this")
        return True, "MTU is 1500 or below on all adapters — OK"
    except (subprocess.CalledProcessError, OSError) as e:
        return None, f"MTU check failed: {e}"


def fix_mtu():
    """Set MTU to 1500 on any real adapter currently above 1500."""
    try:
        out = subprocess.check_output(
            ["netsh", "interface", "ipv4", "show", "subinterfaces"],
            stderr=subprocess.DEVNULL, creationflags=NO_WIN
        ).decode(errors="ignore")
        fixed = []
        failed = []
        for line in out.splitlines():
            m = re.match(r'^\s*(\d+)\s+\d+\s+\d+\s+\d+\s+(.+)$', line)
            if m:
                mtu, name = int(m.group(1)), m.group(2).strip()
                if mtu > 1500 and _mtu_is_real_adapter(name):
                    try:
                        subprocess.check_call(
                            ["netsh", "interface", "ipv4", "set", "subinterface",
                             name, "mtu=1500", "store=persistent"],
                            stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                            creationflags=NO_WIN
                        )
                        fixed.append(name)
                    except (subprocess.CalledProcessError, OSError):
                        failed.append(name)
        if fixed:
            return True, f"MTU set to 1500 on: {', '.join(fixed)}"
        if failed:
            return False, f"Could not set MTU on: {', '.join(failed)} — re-run as Administrator"
        return None, "No adapters needed MTU adjustment"
    except (subprocess.CalledProcessError, OSError) as e:
        return False, f"MTU fix failed: {e}"


def check_teredo_6to4():
    """Check for Teredo/6to4/ISATAP tunnel adapters that can interfere with routing."""
    try:
        out = subprocess.check_output(
            ["netsh", "interface", "teredo", "show", "state"],
            stderr=subprocess.DEVNULL, creationflags=NO_WIN
        ).decode(errors="ignore")
        teredo_active = bool(re.search(r'State\s*:\s*(qualified|active|dormant)', out, re.IGNORECASE))

        # Also check ipconfig for 6to4 / ISATAP adapters
        ipc = subprocess.check_output(
            ["ipconfig"], stderr=subprocess.DEVNULL, creationflags=NO_WIN
        ).decode(errors="ignore")
        tunnel_adapters = re.findall(
            r'adapter\s+((?:6TO4|isatap|Teredo)[^:]+):', ipc, re.IGNORECASE)

        issues = []
        if teredo_active:
            issues.append("Teredo tunneling is active")
        issues.extend(tunnel_adapters)

        if issues:
            return None, (f"Tunnel adapter(s) detected: {'; '.join(issues)} — "
                          f"can cause routing conflicts with Xlink Kai")
        return True, "No Teredo/6to4/ISATAP tunnel adapters active"
    except (subprocess.CalledProcessError, OSError) as e:
        return None, f"Tunnel adapter check failed: {e}"


def check_kai_version():
    """Read Xlink Kai installed version from the Windows registry."""
    import winreg
    reg_paths = [
        (winreg.HKEY_LOCAL_MACHINE,
         r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\XLink Kai"),
        (winreg.HKEY_LOCAL_MACHINE,
         r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\XLink Kai"),
        (winreg.HKEY_CURRENT_USER,
         r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\XLink Kai"),
    ]
    for hive, path in reg_paths:
        try:
            key = winreg.OpenKey(hive, path)
            version = winreg.QueryValueEx(key, "DisplayVersion")[0]
            winreg.CloseKey(key)
            return True, f"Xlink Kai {version} is installed"
        except OSError:
            continue
    # Fallback: look for the executable
    for exe in KAI_INSTALL_PATHS:
        if os.path.exists(exe):
            return None, "Xlink Kai found (version unknown) — reinstall to register version"
    return False, "Xlink Kai does not appear to be installed — download from teamxlink.co.uk"


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
        except OSError as e:
            results.append((False, port, f"Error adding rule for UDP {port}: {e}"))
    return results


def add_kaiengine_exception():
    """Add Windows Firewall exception for kaiEngine.exe."""
    kai_path = None
    for p in KAI_INSTALL_PATHS:
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
        return True, "Firewall exception added for kaiEngine.exe"
    except (subprocess.CalledProcessError, OSError) as e:
        return False, f"Failed to add exception: {e}"


# ── Diagnostics Window ────────────────────────────────────────────────────────
class DiagnosticsWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Xlink Kai Diagnostics")
        self.resizable(True, True)
        self.minsize(720, 540)
        self.geometry("800x700")
        self.configure(bg=BG)
        self.grab_set()

        self._app = parent          # reference to App for ctrl/stype access
        self._log_tag = 0
        self._msg_labels = []       # track message labels for wraplength updates
        self.bind("<Configure>", self._on_resize)

        # Header
        hdr = tk.Frame(self, bg=ACC, pady=10)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="🔍  Xlink Kai Setup Diagnostics",
                 font=("Segoe UI", 14, "bold"), bg=ACC, fg=FG).pack()
        tk.Label(hdr, text="Automatic checks for common Xlink Kai / Rainbow Six setup issues",
                 font=("Segoe UI", 9), bg=ACC, fg=DIM).pack()

        # Scrollable results list
        list_frame = tk.Frame(self, bg=BG, padx=16, pady=8)
        list_frame.pack(fill=tk.BOTH, expand=True)

        self.result_canvas = tk.Canvas(list_frame, bg=BG, highlightthickness=0, height=280)
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
        log_frame.pack(fill=tk.BOTH, expand=True)
        self.flog = scrolledtext.ScrolledText(
            log_frame, height=9, width=70,
            bg="#0d0d1a", fg="#00ff88",
            font=("Consolas", 8), relief=tk.FLAT, borderwidth=0,
            state=tk.DISABLED)
        self.flog.pack(fill=tk.BOTH, expand=True)

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

        self.btn_export = tk.Button(bf, text="💾  Export Log",
                                     bg="#1a4a1a", fg="#00ff88", state=tk.DISABLED,
                                     command=self._export_log, **s)
        self.btn_export.pack(side=tk.LEFT, padx=(0, 8))

        tk.Button(bf, text="✕  Close", bg="#333355", fg=FG,
                  command=self.destroy, **s).pack(side=tk.RIGHT)

        # State
        self._rows = {}
        self._issues = []
        self._results = {}   # key -> (status, label, message) — populated as checks run
        self._check_labels = {}  # key -> human label — set in _run_all

    def _flog(self, msg, color="#00ff88"):
        self.flog.configure(state=tk.NORMAL)
        self._log_tag += 1
        tag = f"t{self._log_tag}"
        self.flog.insert(tk.END, msg + "\n", tag)
        self.flog.tag_config(tag, foreground=color)
        self.flog.see(tk.END)
        self.flog.configure(state=tk.DISABLED)

    def _on_resize(self, event=None):
        """Update message label wraplengths when the window is resized."""
        # 260px reserved for icon + name label + padding
        wl = max(200, self.winfo_width() - 260)
        for lbl in self._msg_labels:
            try:
                lbl.configure(wraplength=wl)
            except tk.TclError:
                pass

    def _clear_results(self):
        for w in self.inner.winfo_children():
            w.destroy()
        self._rows = {}
        self._issues = []
        self._results = {}
        self._msg_labels = []

    def _add_row(self, key, label):
        """Add a check row with pending status."""
        frame = tk.Frame(self.inner, bg=CARD, pady=4, padx=12)
        frame.pack(fill=tk.X, pady=2, padx=4)

        icon_var = tk.StringVar(value="⏳")
        msg_var  = tk.StringVar(value="Checking...")

        tk.Label(frame, textvariable=icon_var, font=("Segoe UI", 11),
                 bg=CARD, width=2).pack(side=tk.LEFT, padx=(0, 8))
        tk.Label(frame, text=label, font=("Segoe UI", 9, "bold"),
                 bg=CARD, fg=FG, width=22, anchor="w").pack(side=tk.LEFT)
        msg_lbl = tk.Label(frame, textvariable=msg_var, font=("Segoe UI", 9),
                           bg=CARD, fg=DIM, anchor="w", wraplength=480)
        msg_lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self._msg_labels.append(msg_lbl)

        self._rows[key] = (icon_var, msg_var, frame)

    def _update_row(self, key, status, message):
        """Update a row: status = True/False/None (warn)."""
        if key not in self._rows:
            return
        self._results[key] = (status, self._check_labels.get(key, key), message)
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
            ("admin",            "Admin Privileges"),
            ("net_profile",      "Network Profile"),
            ("kai_version",      "Xlink Kai Installed"),
            ("xlink_running",    "Xlink Kai Running"),
            ("webui",            "Xlink Kai Web UI"),
            ("orbital",          "Orbital Server Ping"),
            ("vpn",              "VPN Interference"),
            ("teredo",           "Tunnel Adapters"),
            ("ics",              "Connection Sharing"),
            ("adapters",         "Network Adapters"),
            ("mtu",              "MTU Size"),
            ("xbox",             "Xbox on Network"),
            ("double_nat",       "Double NAT"),
            ("upnp_conflict",    "UPnP Port Conflicts"),
            ("port_conflict",    "Local Port Conflicts"),
            ("fw_ports",         "Firewall UDP 3074/30000"),
            ("fw_kaiengine",     "Firewall kaiEngine.exe"),
        ]
        self._check_labels = dict(checks)
        for key, label in checks:
            self._add_row(key, label)

        threading.Thread(target=self._run_checks, daemon=True).start()

    def _run_checks(self):
        def upd(key, ok, msg):
            self.after(0, lambda: self._update_row(key, ok, msg))
        def prog(msg):
            self.after(0, lambda: self.progress_var.set(msg))

        # 1. Admin privileges
        prog("Checking administrator privileges...")
        ok, msg = check_admin()
        upd("admin", ok, msg)

        # 2. Network profile (Public blocks traffic)
        prog("Checking Windows network profile...")
        ok, msg = check_network_profile()
        upd("net_profile", ok, msg)

        # 3. Xlink Kai version / installed check
        prog("Checking Xlink Kai installation...")
        ok, msg = check_kai_version()
        upd("kai_version", ok, msg)

        # 4. Xlink Kai running
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

        # 5. VPN check
        prog("Checking for active VPN...")
        ok, msg = check_vpn_active()
        upd("vpn", ok, msg)

        # 6. Teredo/6to4 tunnel adapters
        prog("Checking for tunnel adapters...")
        ok, msg = check_teredo_6to4()
        upd("teredo", ok, msg)

        # 7. ICS check
        prog("Checking Internet Connection Sharing...")
        ok, msg = check_connection_sharing()
        upd("ics", ok, msg)

        # 8. Adapter check
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

        # 9. MTU size
        prog("Checking MTU size on network adapters...")
        ok, msg = check_mtu()
        upd("mtu", ok, msg)

        # 10. Xbox on network
        prog("Scanning for Xbox on network...")
        ok, msg = check_xbox_on_network()
        upd("xbox", ok, msg)

        # 11. Double NAT (uses already-discovered ctrl/stype from main window)
        prog("Checking for double NAT...")
        ok, msg = check_double_nat(
            getattr(self._app, "ctrl", None),
            getattr(self._app, "stype", None)
        )
        upd("double_nat", ok, msg)

        # 12. UPnP conflict (ports mapped to different device on router)
        prog("Checking for conflicting UPnP mappings on router...")
        ok, msg = check_upnp_conflicts(
            getattr(self._app, "ctrl", None),
            getattr(self._app, "stype", None)
        )
        upd("upnp_conflict", ok, msg)

        # 13. Local port conflict (another process using 3074/30000)
        prog("Checking for local port conflicts...")
        ok, msg = check_port_conflict()
        upd("port_conflict", ok, msg)

        # 14 & 15 share a single netsh call
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
        self.after(0, lambda: self.btn_export.configure(state=tk.NORMAL))

    # ── Remediation steps shown in the export log ─────────────────────────────
    _REMEDIATION = {
        "admin": [
            "HOW TO RUN AS ADMINISTRATOR:",
            "  1. Close this tool completely.",
            "  2. Find Run_XlinkPortOpener.bat in the folder.",
            "  3. Right-click it and choose 'Run as administrator'.",
            "  4. Click Yes on the UAC prompt.",
            "  5. Re-run diagnostics.",
            "",
            "WHY THIS MATTERS:",
            "  Without admin rights, Auto-Fix cannot add firewall rules,",
            "  change network profiles, or adjust MTU settings.",
        ],
        "net_profile": [
            "HOW TO CHANGE NETWORK PROFILE TO PRIVATE:",
            "  Option A — Auto-Fix (click Auto-Fix Issues button).",
            "  Option B — Manual:",
            "    1. Click the Wi-Fi or Ethernet icon in the system tray.",
            "    2. Click the arrow next to your network name.",
            "    3. Click Properties.",
            "    4. Under Network profile type, select Private.",
            "  Option C — PowerShell (run as Administrator):",
            "    Get-NetConnectionProfile | Set-NetConnectionProfile -NetworkCategory Private",
            "",
            "WHY THIS MATTERS:",
            "  Windows Public profile blocks incoming UDP traffic even",
            "  when firewall rules exist — Xlink Kai will not receive",
            "  packets from other players.",
        ],
        "kai_version": [
            "HOW TO INSTALL XLINK KAI:",
            "  1. Visit: https://www.teamxlink.co.uk/",
            "  2. Download the latest installer for Windows.",
            "  3. Run the installer as Administrator.",
            "  4. After install, launch Xlink Kai before using this tool.",
        ],
        "xlink_running": [
            "HOW TO START XLINK KAI:",
            "  1. Find kaiEngine.exe in your Xlink Kai install folder.",
            "     Common location: C:\\Program Files (x86)\\XLink Kai\\",
            "  2. Double-click kaiEngine.exe to start it.",
            "  3. Open a browser and go to: http://localhost:34522",
            "     to confirm the UI loads.",
            "  4. Leave kaiEngine running while using this tool.",
        ],
        "webui": [
            "HOW TO DIAGNOSE XLINK KAI WEB UI NOT RESPONDING:",
            "  1. Check Task Manager — is kaiEngine.exe in the list?",
            "     If not, launch it from the install folder.",
            "  2. Open browser and try: http://localhost:34522",
            "     If it does not load, kaiEngine may have crashed.",
            "  3. Try restarting kaiEngine.exe.",
            "  4. Check Windows Firewall — kaiEngine.exe must have",
            "     an inbound exception (Auto-Fix can add this).",
            "  5. Check if another app is using port 34522:",
            "     Open CMD as Admin and run:",
            "     netstat -ano | findstr \":34522\"",
        ],
        "orbital": [
            "HOW TO DIAGNOSE ORBITAL SERVER NOT REACHABLE:",
            "  1. Check your internet connection — open a browser and",
            "     verify you can load a webpage.",
            "  2. Disable any VPN — VPNs block Xlink Kai traffic.",
            "  3. Check Windows Firewall — kaiEngine.exe must be allowed.",
            "  4. Temporarily disable antivirus and retest.",
            "  5. Check router firewall — ensure outbound UDP is not blocked.",
            "  6. Try from a different network (hotspot) to isolate the issue.",
        ],
        "vpn": [
            "HOW TO DISABLE YOUR VPN:",
            "  1. Find your VPN app in the system tray (bottom-right).",
            "  2. Right-click it and choose Disconnect or Disable.",
            "  3. For WireGuard / OpenVPN: open the app and click Disconnect.",
            "  4. Verify the VPN adapter is gone:",
            "     Open CMD and run: ipconfig",
            "     You should not see a TAP/TUN adapter.",
            "  5. Re-run diagnostics after disconnecting.",
            "",
            "WHY THIS MATTERS:",
            "  VPNs route all traffic through an encrypted tunnel.",
            "  Xlink Kai's System Link tunneling conflicts with this —",
            "  other players cannot reach your PC.",
        ],
        "teredo": [
            "HOW TO DISABLE TEREDO / 6TO4 TUNNEL ADAPTERS:",
            "  1. Open Command Prompt as Administrator.",
            "  2. Run these commands one at a time:",
            "     netsh interface teredo set state disabled",
            "     netsh interface 6to4 set state disabled",
            "     netsh interface isatap set state disabled",
            "  3. Restart your PC.",
            "  4. Re-run diagnostics to confirm they are gone.",
        ],
        "ics": [
            "HOW TO DISABLE INTERNET CONNECTION SHARING (ICS):",
            "  1. Press Windows Key + R, type: ncpa.cpl, press Enter.",
            "  2. Right-click your main internet adapter.",
            "  3. Click Properties -> Sharing tab.",
            "  4. Uncheck 'Allow other network users to connect...'",
            "  5. Click OK and restart the PC.",
        ],
        "adapters": [
            "HOW TO IMPROVE YOUR NETWORK CONNECTION:",
            "  STRONGLY RECOMMENDED: Use a wired Ethernet cable.",
            "  1. Connect an Ethernet cable from your PC to the router.",
            "  2. Disable Wi-Fi in Windows:",
            "     Settings -> Network & Internet -> Wi-Fi -> toggle Off.",
            "  3. Re-run diagnostics.",
            "",
            "If Ethernet is not possible:",
            "  - Move closer to the router.",
            "  - Use 5GHz Wi-Fi if available.",
            "  - Avoid using both Wi-Fi and Ethernet at the same time.",
        ],
        "mtu": [
            "HOW TO FIX HIGH MTU:",
            "  Option A — Auto-Fix (click Auto-Fix Issues button).",
            "  Option B — Manual (run CMD as Administrator):",
            "    1. Find your adapter name:",
            "       netsh interface ipv4 show subinterfaces",
            "    2. Set MTU to 1500 (replace NAME with your adapter name):",
            "       netsh interface ipv4 set subinterface \"NAME\" mtu=1500 store=persistent",
            "",
            "WHY THIS MATTERS:",
            "  MTU above 1500 causes large packets to fragment.",
            "  Fragmented UDP packets are often dropped by routers,",
            "  causing dropped connections in Xlink Kai.",
        ],
        "xbox": [
            "HOW TO GET YOUR XBOX DETECTED ON THE NETWORK:",
            "  1. Make sure your Xbox is powered ON (not in standby).",
            "  2. Make sure the Xbox is connected to the same router",
            "     as your PC — either by Ethernet or Wi-Fi.",
            "  3. On the Xbox: go to Settings -> Network Settings",
            "     and run a connection test to confirm it is online.",
            "  4. Check the router's connected devices list to confirm",
            "     the Xbox appears there.",
            "  5. If using a network switch, try connecting the Xbox",
            "     directly to the router instead.",
            "",
            "NOTE: Xbox must be on the same LAN segment as your PC.",
            "  If your router has separate 2.4GHz and 5GHz networks,",
            "  both devices must be on the same one.",
        ],
        "double_nat": [
            "HOW TO FIX DOUBLE NAT:",
            "  Double NAT means two devices are each doing NAT (address",
            "  translation). UPnP only opens ports on your router — the",
            "  outer modem/gateway still blocks traffic.",
            "",
            "  OPTION 1 — Enable Bridge Mode on ISP modem (recommended):",
            "    1. Log into your ISP modem admin page.",
            "       Common address: http://192.168.100.1 or http://10.0.0.1",
            "    2. Find Bridge Mode, IP Passthrough, or DMZ setting.",
            "    3. Enable it and point it to your router's IP.",
            "    4. Your router becomes the only NAT device.",
            "",
            "  OPTION 2 — Use ISP modem's DMZ:",
            "    1. Log into your ISP modem.",
            "    2. Find DMZ settings and enter your router's WAN IP.",
            "    3. This forwards all ports to your router.",
            "",
            "  OPTION 3 — Contact your ISP:",
            "    Ask them to put the modem in bridge mode for you.",
        ],
        "upnp_conflict": [
            "HOW TO FIX UPNP PORT CONFLICTS:",
            "  Another device on your network has already claimed UDP",
            "  3074 or 30000 on the router. Only one device can hold",
            "  each port mapping at a time.",
            "",
            "  1. Log into your router admin page.",
            "     (Use Router Setup Guide button to find your login details.)",
            "  2. Find the port forwarding or UPnP mappings section.",
            "  3. Delete any existing entries for UDP 3074 and UDP 30000.",
            "  4. Return to this tool and click 'Open Ports 3074 & 30000'.",
            "",
            "  ALTERNATIVELY: On the other device (e.g. another Xbox PC),",
            "  remove its port mappings, then re-open ports here.",
        ],
        "port_conflict": [
            "HOW TO FIX LOCAL PORT CONFLICTS:",
            "  Another program on this PC is already listening on UDP 3074",
            "  or UDP 30000. Xlink Kai cannot use them if another app is.",
            "",
            "  1. Open Command Prompt as Administrator.",
            "  2. Run: netstat -ano | findstr \":3074\"",
            "     and: netstat -ano | findstr \":30000\"",
            "  3. Note the PID number in the last column.",
            "  4. Open Task Manager -> Details tab.",
            "  5. Find the process with that PID and end it.",
            "  6. If it is a system process, a restart may be needed.",
        ],
        "fw_ports": [
            "HOW TO ADD WINDOWS FIREWALL RULES FOR UDP 3074 & 30000:",
            "  Option A — Auto-Fix (click Auto-Fix Issues button).",
            "  Option B — Manual (run CMD as Administrator):",
            "    netsh advfirewall firewall add rule name=\"Xlink Kai UDP 3074\"",
            "      dir=in action=allow protocol=UDP localport=3074",
            "      enable=yes profile=any",
            "    netsh advfirewall firewall add rule name=\"Xlink Kai UDP 30000\"",
            "      dir=in action=allow protocol=UDP localport=30000",
            "      enable=yes profile=any",
            "",
            "  TO VERIFY: Run diagnostics again after adding rules.",
            "",
            "WHY THIS MATTERS:",
            "  Windows Firewall blocks inbound UDP by default.",
            "  Without these rules, other players' game data is silently",
            "  dropped before it reaches Xlink Kai.",
        ],
        "fw_kaiengine": [
            "HOW TO ADD A FIREWALL EXCEPTION FOR kaiEngine.exe:",
            "  Option A — Auto-Fix (click Auto-Fix Issues button).",
            "  Option B — Manual:",
            "    1. Open Windows Security -> Firewall & network protection.",
            "    2. Click 'Allow an app through firewall'.",
            "    3. Click 'Change settings' -> 'Allow another app'.",
            "    4. Browse to: C:\\Program Files (x86)\\XLink Kai\\kaiEngine.exe",
            "    5. Check both Private and Public, click OK.",
            "  Option C — CMD as Administrator:",
            "    netsh advfirewall firewall add rule name=\"XLink Kai Engine\"",
            "      dir=in action=allow protocol=any",
            "      program=\"C:\\Program Files (x86)\\XLink Kai\\kaiEngine.exe\"",
            "      enable=yes profile=any",
        ],
    }

    def _export_log(self):
        """Save a diagnostic report the user can share for remote troubleshooting."""
        if not self._results:
            messagebox.showinfo("Export Log", "Run diagnostics first before exporting.")
            return

        default_name = f"XlinkKai_DiagReport_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=default_name,
            title="Save Diagnostic Report"
        )
        if not path:
            return

        try:
            self._write_report(path)
            messagebox.showinfo("Export Log",
                f"Report saved to:\n{path}\n\nShare this file for troubleshooting assistance.")
        except OSError as e:
            messagebox.showerror("Export Log", f"Could not save file:\n{e}")

    def _write_report(self, path: str):
        app = self._app
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        errors   = [(k, lbl, msg) for k, (s, lbl, msg) in self._results.items() if s is False]
        warnings = [(k, lbl, msg) for k, (s, lbl, msg) in self._results.items() if s is None]
        passed   = [(k, lbl, msg) for k, (s, lbl, msg) in self._results.items() if s is True]

        lines = []
        def w(text=""): lines.append(text)

        w("╔══════════════════════════════════════════════════════════════════════╗")
        w("║          XLINK KAI PORT OPENER — DIAGNOSTIC REPORT                 ║")
        w("║          Rainbow Six 3 / Black Arrow — Original Xbox               ║")
        w("╚══════════════════════════════════════════════════════════════════════╝")
        w()
        w(f"  Generated : {now}")
        w(f"  Tool      : Xlink Kai Port Opener v2.0  (by Juv3nile)")
        w(f"  OS        : {platform.version()}")
        w(f"  Python    : {platform.python_version()}")
        w(f"  Machine   : {platform.machine()}")
        w()

        # Network info from App
        w("══════════════════════════════════════════════════════════════════════")
        w("  NETWORK SNAPSHOT")
        w("══════════════════════════════════════════════════════════════════════")
        w(f"  LAN IP      : {app.vlan.get()}")
        w(f"  Router IP   : {app.vgw.get()}")
        w(f"  External IP : {app.vext.get()}")
        w(f"  UPnP Service: {getattr(app, 'stype', None) or 'Not detected'}")
        w()

        # Summary
        w("══════════════════════════════════════════════════════════════════════")
        w("  RESULTS SUMMARY")
        w("══════════════════════════════════════════════════════════════════════")
        w(f"  ❌ Errors   : {len(errors)}")
        w(f"  ⚠️  Warnings : {len(warnings)}")
        w(f"  ✅ Passed   : {len(passed)}")
        w()

        # AI prompt header
        w("══════════════════════════════════════════════════════════════════════")
        w("  HOW TO USE THIS REPORT WITH AI")
        w("══════════════════════════════════════════════════════════════════════")
        w("  Paste the entire contents of this file into an AI assistant")
        w("  (ChatGPT, Claude, etc.) and use this prompt:")
        w()
        w('  "I am trying to get Xlink Kai working for Rainbow Six 3 Black')
        w('   Arrow on original Xbox. Below is my diagnostic report from')
        w('   the Xlink Kai Port Opener tool. Please review the errors and')
        w('   warnings and give me step-by-step instructions to fix them.')
        w('   Start with the most critical issue first."')
        w()

        # Errors
        if errors:
            w("══════════════════════════════════════════════════════════════════════")
            w("  ❌ ERRORS — MUST FIX (start here)")
            w("══════════════════════════════════════════════════════════════════════")
            for i, (key, lbl, msg) in enumerate(errors, 1):
                w()
                w(f"  [{i}] {lbl.upper()}")
                w(f"      Diagnostic result: {msg}")
                w()
                steps = self._REMEDIATION.get(key)
                if steps:
                    for step in steps:
                        w(f"      {step}")
                else:
                    w("      Refer to the Xlink Kai Port Opener documentation.")
                w()

        # Warnings
        if warnings:
            w("══════════════════════════════════════════════════════════════════════")
            w("  ⚠️  WARNINGS — INVESTIGATE IF STILL HAVING ISSUES")
            w("══════════════════════════════════════════════════════════════════════")
            for i, (key, lbl, msg) in enumerate(warnings, 1):
                w()
                w(f"  [{i}] {lbl.upper()}")
                w(f"      Diagnostic result: {msg}")
                w()
                steps = self._REMEDIATION.get(key)
                if steps:
                    for step in steps:
                        w(f"      {step}")
                else:
                    w("      Refer to the Xlink Kai Port Opener documentation.")
                w()

        # Passed
        if passed:
            w("══════════════════════════════════════════════════════════════════════")
            w("  ✅ PASSED CHECKS")
            w("══════════════════════════════════════════════════════════════════════")
            for key, lbl, msg in passed:
                w(f"  ✅ {lbl:<28} {msg}")
            w()

        # Fix log
        fix_text = self.flog.get("1.0", tk.END).strip()
        if fix_text:
            w("══════════════════════════════════════════════════════════════════════")
            w("  AUTO-FIX LOG")
            w("══════════════════════════════════════════════════════════════════════")
            for line in fix_text.splitlines():
                w(f"  {line}")
            w()

        # Where to start on screen share
        w("══════════════════════════════════════════════════════════════════════")
        w("  SCREEN SHARE CHECKLIST — WHERE TO BEGIN")
        w("══════════════════════════════════════════════════════════════════════")
        w("  When sharing your screen for remote support, verify these in order:")
        w()
        w("  STEP 1 — Confirm Xlink Kai is running")
        w("    [ ] kaiEngine.exe visible in Task Manager (Details tab)")
        w("    [ ] http://localhost:34522 loads in browser")
        w("    [ ] Xlink Kai shows your username and orbital connection")
        w()
        w("  STEP 2 — Confirm network profile")
        w("    [ ] Settings -> Network & Internet -> your connection")
        w("         shows 'Private network' (not Public)")
        w()
        w("  STEP 3 — Confirm firewall rules exist")
        w("    [ ] Open CMD as Admin and run:")
        w("         netsh advfirewall firewall show rule name=\"Xlink Kai UDP 3074\"")
        w("         netsh advfirewall firewall show rule name=\"Xlink Kai UDP 30000\"")
        w("    [ ] Both should show Enabled: Yes")
        w()
        w("  STEP 4 — Confirm ports are open on router")
        w("    [ ] This tool shows 'OPEN' in the Ports Status field")
        w("    [ ] In Xlink Kai web UI, Metrics tab, NAT Type = Open or Moderate")
        w()
        w("  STEP 5 — Confirm Xbox is online and visible")
        w("    [ ] Xbox is powered on and connected to same router")
        w("    [ ] Xbox Settings -> Network -> Connection Test passes")
        w("    [ ] This tool detected Xbox in ARP scan (check above)")
        w()
        w("  STEP 6 — Confirm no VPN / tunnel interference")
        w("    [ ] VPN app is disconnected")
        w("    [ ] ipconfig shows no TAP, TUN, or WireGuard adapters")
        w()
        w("  STEP 7 — Test in Xlink Kai")
        w("    [ ] Join or host an arena in Xlink Kai")
        w("    [ ] Other players' latency bars should be green/yellow")
        w("    [ ] Launch game and test System Link")
        w()
        w("══════════════════════════════════════════════════════════════════════")
        w("  END OF REPORT")
        w("══════════════════════════════════════════════════════════════════════")

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def _auto_fix(self):
        self.btn_fix.configure(state=tk.DISABLED)
        self.btn_run.configure(state=tk.DISABLED)
        threading.Thread(target=self._do_fixes, daemon=True).start()

    def _do_fixes(self):
        fixed = 0

        if "admin" in self._issues:
            self._flog("Not running as Administrator:", "#ffaa44")
            self._flog("  Close this tool, right-click Run_XlinkPortOpener.bat", "#ffaa44")
            self._flog("  and select 'Run as administrator'.", "#ffaa44")

        if "net_profile" in self._issues:
            self._flog("Changing network profile from Public to Private...", "#88aaff")
            ok, msg = fix_network_profile()
            color = "#00ff88" if ok else "#ff4466"
            self._flog(f"  {msg}", color)
            if ok:
                fixed += 1

        if "double_nat" in self._issues:
            self._flog("Double NAT detected — this requires a manual fix:", "#ffaa44")
            self._flog("  1. Log into your ISP modem/gateway admin page", "#ffaa44")
            self._flog("  2. Enable Bridge Mode or IP Passthrough", "#ffaa44")
            self._flog("  3. This lets your router handle NAT directly", "#ffaa44")
            self._flog("  4. Contact your ISP if you cannot find this setting", "#ffaa44")

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

        if "mtu" in self._issues:
            self._flog("Setting MTU to 1500 on high-MTU adapters...", "#88aaff")
            ok, msg = fix_mtu()
            color = "#00ff88" if ok else ("#ffaa44" if ok is None else "#ff4466")
            self._flog(f"  {msg}", color)
            if ok:
                fixed += 1

        if "teredo" in self._issues:
            self._flog("Teredo/6to4 tunnel adapter detected — manual steps to disable:", "#ffaa44")
            self._flog("  1. Open Command Prompt as Administrator", "#ffaa44")
            self._flog("  2. Run: netsh interface teredo set state disabled", "#ffaa44")
            self._flog("  3. Run: netsh interface 6to4 set state disabled", "#ffaa44")
            self._flog("  4. Restart your PC and re-run diagnostics", "#ffaa44")

        if "port_conflict" in self._issues:
            self._flog("Local port conflict on 3074 or 30000:", "#ffaa44")
            self._flog("  Another app is using these ports. To identify it,", "#ffaa44")
            self._flog("  open CMD as Administrator and run:", "#ffaa44")
            self._flog("    netstat -ano | findstr \":3074\"", "#88aaff")
            self._flog("    netstat -ano | findstr \":30000\"", "#88aaff")
            self._flog("  Note the PID, then find it in Task Manager and close it.", "#ffaa44")

        if "upnp_conflict" in self._issues:
            self._flog("UPnP conflict — ports mapped to a different device on your router:", "#ffaa44")
            self._flog("  Open your router admin page and delete the existing", "#ffaa44")
            self._flog("  port mappings for UDP 3074 and 30000, then re-open ports.", "#ffaa44")

        if "kai_version" in self._issues:
            self._flog("Xlink Kai not installed — download from:", "#ffaa44")
            self._flog("  https://www.teamxlink.co.uk/", "#88aaff")

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
        self.title("Xlink Kai Port Opener  v2.0")
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
        def _do():
            self.log.configure(state=tk.NORMAL)
            self._log_tag += 1
            tag = f"t{self._log_tag}"
            self.log.insert(tk.END, msg + "\n", tag)
            if color:
                self.log.tag_config(tag, foreground=color)
            self.log.see(tk.END)
            self.log.configure(state=tk.DISABLED)
        if threading.current_thread() is threading.main_thread():
            _do()
        else:
            self.after(0, _do)

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
        self.after(0, lambda: self.vstatus.set("Scanning..."))
        gateway_ip = _get_default_gateway()
        lip = get_local_ip(gateway_ip)
        self.after(0, lambda: self.vlan.set(lip))
        loc, gwip = discover_gateway(timeout=8)
        if not loc:
            self._err("No UPnP gateway found.")
            self._inf("Click 'Router Setup Guide' for help enabling UPnP.")
            self.after(0, lambda: self.vstatus.set("Router not found"))
            return
        self._ok(f"Router found at {gwip}")
        self.after(0, lambda: self.vgw.set(gwip))
        self.gwip = gwip
        self.lip  = lip
        try:
            ctrl, stype = get_service_url(loc)
        except (urllib.error.URLError, OSError, ET.ParseError, RuntimeError) as e:
            self._err(f"Could not parse router: {e}")
            self.after(0, lambda: self.vstatus.set("Parse error"))
            return
        self.ctrl  = ctrl
        self.stype = stype
        ext = get_ext_ip(ctrl, stype)
        self.after(0, lambda: self.vext.set(ext))
        self._ok(f"External IP: {ext}")
        self.after(0, lambda: self.vstatus.set("Ready"))
        self.after(0, lambda: self.bopen.configure(state=tk.NORMAL))

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
        except OSError as e:
            self._err(f"Unexpected error: {e}")
        finally:
            if ok == len(PORTS):
                self.after(0, lambda: self.vstatus.set("OPEN"))
                self._ok("Both ports open. You can close this window.")
                self.after(0, lambda: self.bclose.configure(state=tk.NORMAL))
            else:
                self.after(0, lambda: self.vstatus.set("Failed - see log"))
                self._err("Some ports failed. Check log above for details.")
                self._inf("Tips: Run as Administrator. Check UPnP is enabled on router.")
                self.after(0, lambda: self.bopen.configure(state=tk.NORMAL))

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
        self.after(0, lambda: self.vstatus.set("Closed"))
        self.after(0, lambda: self.bopen.configure(state=tk.NORMAL))


if __name__ == "__main__":
    App().mainloop()
