# 🎮 Xlink Kai Port Opener
### Rainbow Six 3 / Black Arrow — Original Xbox

> Automatic UPnP port forwarding, router setup guide, and full Xlink Kai diagnostics tool.  
> No networking experience required. Created by **Juv3nile**

---

## 📥 Download

**[⬇ Download Latest Release](../../releases/latest)**

Unzip the folder — you will find three files:
| File | Purpose |
|------|---------|
| `Run_XlinkPortOpener.bat` | Double-click to launch — installs Python automatically |
| `xlink_upnp_opener.py` | Main program (requires Python 3) |
| `README.txt` | Offline reference guide |

---

## ⚠️ Before You Run — Unblock the File First

Windows will block `.bat` files downloaded from the internet. You **must** do this before double-clicking:

1. **Right-click** `Run_XlinkPortOpener.bat`
2. Click **Properties**
3. At the bottom, check the box next to **Unblock**
4. Click **Apply** → **OK**

You only need to do this once.

---

## 🚀 What It Does

This tool solves the three most common reasons Xlink Kai games lag, drop, or fail to connect:

- **Opens UDP 3074 & 30000** on your router automatically via UPnP — no manual port forwarding needed
- **Guides you through enabling UPnP** on your router if it's turned off, with step-by-step instructions for 19 router brands
- **Runs full diagnostics** on your Xlink Kai setup and automatically fixes common issues

---

## 📋 Requirements

- Windows 10 or Windows 11
- Internet connection *(first run only — to auto-install Python)*
- UPnP enabled on your router *(the tool guides you if it's off)*

**Python installs automatically on first run.** Nothing to install manually.

---

## 🛠️ How To Use

### Step 1 — Unblock the .bat file
Follow the unblock instructions above before doing anything else.

### Step 2 — Launch the tool
Double-click `Run_XlinkPortOpener.bat`

On first run, Python downloads and installs silently in the background. This takes 1–2 minutes and only happens once.

### Step 3 — Enable UPnP (if needed)
If the tool says **"Router not found"**, UPnP is disabled on your router.

Click the **📖 Router Setup Guide** button and select your router brand. The guide shows:
- Your router's default admin page address
- Default username and password
- Step-by-step instructions to enable UPnP

Click **Open Router Login Page in Browser** to go there directly.

### Step 4 — Open the ports
Once your router is detected, click **▶ Open Ports 3074 & 30000**

The log will confirm both ports opened successfully.

### Step 5 — Run Diagnostics
Click **🔍 Diagnostics** to run a full health check of your Xlink Kai setup.

---

## 🔍 Diagnostics — What Gets Checked

The diagnostics tool automatically checks 9 common setup issues:

| Check | What It Looks For |
|-------|------------------|
| ✅ Xlink Kai Running | Is kaiEngine.exe actually launched |
| ✅ Xlink Kai Web UI | Can reach localhost:34522 |
| ✅ Orbital Server Ping | Connection to Xlink Kai's servers |
| ✅ VPN Interference | Active VPN adapters that break Xlink Kai |
| ✅ Connection Sharing | ICS conflicts |
| ✅ Network Adapters | WiFi vs Ethernet detection |
| ✅ Xbox on Network | Scans for Xbox on your local network |
| ✅ Firewall UDP 3074/30000 | Windows Firewall inbound rules |
| ✅ Firewall kaiEngine.exe | App exception for Xlink Kai engine |

Each check shows **✅ green** (OK), **❌ red** (problem), or **⚠️ yellow** (warning).

Click **🔧 Auto-Fix Issues** to automatically resolve any problems found.

---

## 📡 Router Support

The built-in Router Setup Guide covers 19 router brands:

| Brand | Brand | Brand |
|-------|-------|-------|
| ASUS (standard) | ASUS BE9700 | Netgear |
| Netgear Orbi | Linksys | Linksys Velop |
| TP-Link Archer | TP-Link (older) | D-Link |
| Belkin | Motorola / Arris | Xfinity / Comcast xFi |
| AT&T BGW / NVG | Verizon Fios | Spectrum |
| Cox Panoramic | Eero (Amazon) | Google Nest WiFi |
| *I don't know my brand* | | |

> **Note:** Google Nest WiFi and some ISP gateways (Xfinity, AT&T) do not support UPnP. The guide explains workarounds for each of these.

---

## 🔧 Troubleshooting

**"Router not found" in the log**
> UPnP is disabled. Click Router Setup Guide and follow the steps for your brand.

**"Rule already exists"**
> Ports are already open from a previous run. You are good to go.

**"Some ports failed"**
> Right-click the `.bat` file and choose **Run as Administrator**, then try again.

**"Python installed but PATH not updated"**
> Close the window and double-click the `.bat` again. This happens once after first install.

**Ports open but still lagging in Xlink Kai**
> The lag is likely on the other players' end, not yours. Share this tool with them and have them run it too. The four most common causes on their side are: strict NAT, missing firewall rules, VPN active, or WiFi instead of Ethernet.

---

## 📦 Ports Opened

| Port | Protocol | Purpose |
|------|----------|---------|
| 3074 | UDP | Xbox System Link / Xlink Kai game traffic |
| 30000 | UDP | Xlink Kai tunnel (peer-to-peer routing) |

---

## ❓ How It Works

The tool uses **UPnP (Universal Plug and Play)** — a standard protocol built into most home routers that allows programs to request port forwards automatically. It sends a SOAP request to your router asking it to open the specified UDP ports and forward them to your PC's local IP address.

No router login required. No manual configuration. The rules persist until you reboot your router or click **Remove Rules**.

---

## 📜 Version History

| Version | Notes |
|---------|-------|
| v1.0 | Initial release — UPnP port opener, router guide, full diagnostics, auto-fix |

---

## 👤 Credits

**Created by Juv3nile**  
For the Rainbow Six 3 / Black Arrow Xlink Kai community  

---

*Xbox, Rainbow Six 3, and Black Arrow are trademarks of their respective owners. This tool is an independent community project and is not affiliated with Microsoft, Ubisoft, or Team Xlink.*
