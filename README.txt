╔══════════════════════════════════════════════════════════════╗
║         XLINK KAI PORT OPENER - README                      ║
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
  → Try right-clicking the .bat and choosing
    "Run as Administrator", then try again.

"Python installed but PATH not updated":
  → Close the window and double-click the .bat again.
    This happens once after first install.

Tool opens but nothing happens after clicking Open Ports:
  → Check the log box for error messages.
  → Make sure your router was detected (Router IP shows a
    real address, not a dash).


══════════════════════════════════════════════════════════════

  Created by Juv3nile
  For the Rainbow Six 3 / Black Arrow Xlink Kai community

══════════════════════════════════════════════════════════════
