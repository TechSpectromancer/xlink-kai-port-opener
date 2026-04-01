╔══════════════════════════════════════════════════════════════╗
║         XLINK KAI PORT OPENER v2.1 - README                 ║
║         Rainbow Six 3 / Black Arrow - Original Xbox         ║
║                                        Created by Juv3nile  ║
╚══════════════════════════════════════════════════════════════╝

WHAT THIS DOES
──────────────
This tool automatically opens UDP ports 3074 and 30000 on your
home router using UPnP. These are the ports Xlink Kai uses for
Xbox System Link tunneling over the internet.

Opening them allows other players to connect directly to you
instead of being routed through a relay server — reducing lag
from ~1000ms down to ~30ms in ideal conditions.

It also includes a full diagnostics tool that checks 17 common
setup issues and auto-fixes the ones it can.


══════════════════════════════════════════════════════════════
  STEP 1 — DO THIS BEFORE RUNNING (IMPORTANT)
══════════════════════════════════════════════════════════════

Windows may block the .bat file because it was downloaded from
the internet. Before double-clicking it you MUST unblock it:

  1. Right-click  Run_XlinkPortOpener.bat
  2. Click        Properties
  3. At the bottom check the box next to "Unblock"
  4. Click        Apply  then  OK

You only need to do this once. After unblocking, the file will
run normally every time.


══════════════════════════════════════════════════════════════
  STEP 2 — REQUIREMENTS
══════════════════════════════════════════════════════════════

  - Windows 10 or Windows 11
  - Internet connection (first run only, to install Python)
  - UPnP enabled on your router (see Step 3 if unsure)

Python 3 is required but installs AUTOMATICALLY on first run
if you don't already have it. Nothing to do manually.

TIP: Right-click Run_XlinkPortOpener.bat and choose
     "Run as Administrator" so Auto-Fix has full permissions.


══════════════════════════════════════════════════════════════
  STEP 3 — ENABLE UPnP ON YOUR ROUTER (if needed)
══════════════════════════════════════════════════════════════

If the tool cannot find your router, UPnP may be disabled.
The tool includes a built-in Router Setup Guide to help you.

To access it:
  1. Run the tool (double-click Run_XlinkPortOpener.bat)
  2. Click the "Router Setup Guide" button at the top
  3. Select your router brand from the dropdown list
  4. The guide shows your router's default login address,
     username, password, and step-by-step UPnP enable
     instructions specific to your router model
  5. Click "Open Router Login Page in Browser" to go
     directly to your router's admin page
  6. Follow the steps shown, then click Re-detect Router

SUPPORTED ROUTER BRANDS IN THE GUIDE:
  ASUS, ASUS BE9700, Netgear, Netgear Orbi, Linksys,
  Linksys Velop, TP-Link Archer, TP-Link older, D-Link,
  Belkin, Motorola/Arris, Xfinity/Comcast xFi, AT&T BGW/NVG,
  Verizon Fios, Spectrum, Cox Panoramic, Eero, Google Nest,
  and "I don't know my brand" with auto-detection steps.

NOTE: Some ISP-provided gateways (Xfinity, AT&T, Google Nest)
lock or disable UPnP entirely. The guide explains workarounds
for each of these cases.


══════════════════════════════════════════════════════════════
  STEP 4 — HOW TO USE THE TOOL
══════════════════════════════════════════════════════════════

  1. Double-click  Run_XlinkPortOpener.bat
     (Python installs automatically on first run if needed)

  2. The tool detects your router automatically on launch.
     You will see your LAN IP, Router IP, and External IP
     appear in the status panel when detection succeeds.

  3. Click  "Open Ports 3074 & 30000"

  4. The log will confirm both ports are open.

  5. Launch Xlink Kai and your game as normal.

The port rules stay active until you reboot your router or
click "Remove Rules". You can close the tool after opening.


══════════════════════════════════════════════════════════════
  DIAGNOSTICS TOOL
══════════════════════════════════════════════════════════════

Click the "Diagnostics" button to run 17 automated checks:

  - Admin Privileges       Are you running as Administrator
  - Network Profile        Public profile blocks traffic
  - Xlink Kai Installed    Version from Windows registry
  - Xlink Kai Running      Is kaiEngine.exe launched
  - Xlink Kai Web UI       Can reach localhost:34522
  - Orbital Server Ping    Connection to Xlink Kai servers
  - VPN Interference       Active VPN breaks Xlink Kai
  - Tunnel Adapters        Teredo/6to4/ISATAP conflicts
  - Connection Sharing     ICS can interfere with Xlink Kai
  - Network Adapters       WiFi vs Ethernet
  - MTU Size               Above 1500 causes fragmentation
  - Xbox on Network        Scans ARP table for Xbox MAC
  - Double NAT             Two NAT layers — UPnP not enough
  - UPnP Port Conflicts    Ports mapped to another device
  - Local Port Conflicts   Another app using 3074/30000
  - Firewall UDP 3074/30000  Windows Firewall inbound rules
  - Firewall kaiEngine.exe   App firewall exception

Each check shows green (OK), red (problem), or yellow (warning).
Click "Auto-Fix Issues" to automatically resolve what it can.


══════════════════════════════════════════════════════════════
  VERIFY IT WORKED
══════════════════════════════════════════════════════════════

In Xlink Kai's web UI (open browser: http://localhost:34522):
  - Go to the Metrics tab
  - NAT Type should show "Open" or "Moderate"
  - Other players' ping bars should appear green, not red

On your Xbox dashboard:
  - Settings -> Network Settings -> Connection Test
  - Press Y then A for detailed view
  - NT: 1 = Open NAT (best)
  - NT: 2 = Moderate NAT
  - NT: 3 = Strict NAT (port forwarding may not have worked)


══════════════════════════════════════════════════════════════
  PORTS OPENED
══════════════════════════════════════════════════════════════

  UDP 3074   —  Xbox System Link / Xlink Kai game traffic
  UDP 30000  —  Xlink Kai tunnel (peer-to-peer routing)


══════════════════════════════════════════════════════════════
  TROUBLESHOOTING
══════════════════════════════════════════════════════════════

"Router not found" in log:
  → UPnP is disabled. Use the Router Setup Guide button.

"Rule already exists":
  → Ports are already open from a previous run. You're good.

"Some ports failed":
  → Right-click the .bat and choose "Run as Administrator".

"Python installed but PATH not updated":
  → Close the window and double-click the .bat again.
    This happens once after first install.

Auto-Fix didn't change anything:
  → Close the tool, right-click Run_XlinkPortOpener.bat,
    and choose "Run as Administrator". Firewall rules,
    network profile, and MTU fixes require admin rights.

Double NAT detected:
  → Your ISP modem and router are both doing NAT. Log into
    your ISP modem and enable Bridge Mode or IP Passthrough.
    Contact your ISP if you cannot find the setting.

Ports open but still lagging in Xlink Kai:
  → The lag may be on other players' end. Share this tool
    with them. Common causes: strict NAT, no firewall rules,
    VPN active, or WiFi instead of Ethernet.


══════════════════════════════════════════════════════════════
  VERSION HISTORY
══════════════════════════════════════════════════════════════

  v2.1  Export Log button in Diagnostics — saves a full .txt
        report with step-by-step fix instructions for every
        failing check, an AI prompt template, and a screen
        share checklist for remote support sessions

  v2.0  Major reliability and security overhaul — thread-safe
        UI (eliminates intermittent crashes), SSRF protection
        on SSDP location URLs, namespace-aware XML parsing,
        CGNAT double-NAT detection, correct NIC selection on
        multi-adapter systems, named constants throughout,
        consistent CSV process detection, specific exception
        handling, and structured debug log to %APPDATA%

  v1.1  8 new diagnostic checks (MTU, double NAT, tunnel
        adapters, port conflicts, UPnP conflicts, admin
        check, network profile, Kai version); resizable
        windows; bug fixes for false positives

  v1.0  Initial release — UPnP port opener, router guide,
        diagnostics with auto-fix


══════════════════════════════════════════════════════════════

  Created by Juv3nile
  For the Rainbow Six 3 / Black Arrow Xlink Kai community

══════════════════════════════════════════════════════════════
