# Network Monitor - Complete System Walkthrough

## Table of Contents

1. [Overview](#1-overview)
2. [System Architecture](#2-system-architecture)
3. [Prerequisites](#3-prerequisites)
4. [Installation Guide](#4-installation-guide)
5. [Configuration](#5-configuration)
6. [Component Details](#6-component-details)
7. [Usage Guide](#7-usage-guide)
8. [API Reference](#8-api-reference)
9. [Database Schema](#9-database-schema)
10. [Security Considerations](#10-security-considerations)
11. [Troubleshooting](#11-troubleshooting)
12. [Development Guide](#12-development-guide)

---

## 1. Overview

### 1.1 What is Network Monitor?

Network Monitor is a **stealth parental control application** designed to monitor all network traffic from devices on your WiFi network. Unlike traditional monitoring solutions that only track the monitoring PC, this application uses **ARP spoofing** to intercept traffic from ALL devices on your network.

### 1.2 Key Features

| Feature | Description |
|---------|-------------|
| **Network-Wide Monitoring** | Captures traffic from all devices on WiFi, not just the host PC |
| **HTTPS Decryption** | Decrypts HTTPS traffic using mitmproxy for full content visibility |
| **Stealth Mode** | Disguises the monitoring PC as a printer/TV/smart device |
| **Website Blocking** | Block domains, categories, or keywords with time-based schedules |
| **Keyword Alerts** | Real-time alerts for concerning content (self-harm, predators, drugs) |
| **Remote Certificate Install** | Disguised landing page for installing CA certificates on target devices |
| **Full-Text Search** | Search through all captured traffic content |
| **Modern Desktop UI** | Clean, responsive interface built with React and Tailwind CSS |

### 1.3 How It Works

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              YOUR WIFI NETWORK                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐         │
│   │  Phone   │     │  Laptop  │     │  Tablet  │     │Smart TV  │         │
│   └────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘         │
│        │                │                │                │               │
│        └────────────────┴────────────────┴────────────────┘               │
│                                    │                                       │
│                         ┌──────────▼──────────┐                           │
│                         │  MONITORING PC      │                           │
│                         │  (Appears as HP     │                           │
│                         │   Printer on network)│                          │
│                         │                     │                           │
│                         │  ┌───────────────┐  │                           │
│                         │  │ ARP Spoofing  │  │  Intercepts all traffic   │
│                         │  │ HTTPS Proxy   │  │  before forwarding to     │
│                         │  │ DNS Capture   │  │  the real router          │
│                         │  └───────────────┘  │                           │
│                         └──────────┬──────────┘                           │
│                                    │                                       │
│                         ┌──────────▼──────────┐                           │
│                         │      ROUTER         │                           │
│                         │   192.168.1.1       │                           │
│                         └──────────┬──────────┘                           │
│                                    │                                       │
└────────────────────────────────────┼───────────────────────────────────────┘
                                     │
                              ┌──────▼──────┐
                              │  INTERNET   │
                              └─────────────┘
```

---

## 2. System Architecture

### 2.1 Technology Stack

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (UI)                             │
│  React 18 + TypeScript + Vite + Tailwind CSS + Zustand          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Tauri IPC (invoke commands)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     TAURI BACKEND (Rust)                         │
│  Commands, State Management, Process Control, Settings          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Subprocess + JSON stdout
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PYTHON BACKEND                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ ARP Spoofer │  │ HTTPS Proxy │  │ DNS Capture │             │
│  │  (Scapy)    │  │ (mitmproxy) │  │  (Scapy)    │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  Blocking   │  │   Alerts    │  │   Stealth   │             │
│  │   Engine    │  │   Engine    │  │    Mode     │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DATABASE (SQLite)                           │
│  Devices, Traffic, DNS Queries, Sessions, Full-Text Search      │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Directory Structure

```
network-monitor/
│
├── src/                          # React Frontend
│   ├── components/               # UI Components
│   │   ├── common/              # Button, Input, Modal, etc.
│   │   ├── layout/              # Sidebar, Header, Layout
│   │   ├── traffic/             # Traffic table, details, filters
│   │   ├── devices/             # Device cards, list
│   │   ├── blocking/            # Block rules, categories
│   │   ├── alerts/              # Alert cards, list
│   │   └── stealth/             # Profile selector, status
│   ├── pages/                   # Page components
│   │   ├── Dashboard.tsx        # Main dashboard
│   │   ├── Devices.tsx          # Device management
│   │   ├── Traffic.tsx          # Traffic viewer
│   │   ├── Blocking.tsx         # Blocking rules
│   │   ├── Alerts.tsx           # Alert management
│   │   └── Settings.tsx         # App settings
│   ├── hooks/                   # Custom React hooks
│   ├── stores/                  # Zustand state stores
│   ├── lib/                     # Utilities and API wrapper
│   │   ├── api.ts              # Tauri command wrapper
│   │   └── utils.ts            # Helper functions
│   ├── types/                   # TypeScript type definitions
│   ├── App.tsx                  # Main app component
│   └── main.tsx                 # Entry point
│
├── src-tauri/                    # Rust Backend (Tauri)
│   ├── src/
│   │   ├── main.rs              # App entry point
│   │   ├── commands.rs          # Tauri command handlers
│   │   ├── python.rs            # Python process management
│   │   └── state.rs             # App state management
│   ├── icons/                   # App icons
│   ├── Cargo.toml               # Rust dependencies
│   └── tauri.conf.json          # Tauri configuration
│
├── python/                       # Python Backend
│   ├── main.py                  # Main entry point
│   ├── requirements.txt         # Python dependencies
│   │
│   ├── arp/                     # ARP Spoofing module
│   │   ├── arp_gateway.py       # Gateway spoofing
│   │   ├── device_scanner.py    # Network device discovery
│   │   └── ip_forwarding.py     # IP forwarding control
│   │
│   ├── https/                   # HTTPS Interception
│   │   ├── transparent_proxy.py # mitmproxy integration
│   │   ├── cert_generator.py    # CA certificate generation
│   │   ├── content_decoder.py   # Response body decoding
│   │   └── traffic_parser.py    # HTTP traffic parsing
│   │
│   ├── dns/                     # DNS Monitoring
│   │   ├── dns_capture.py       # DNS packet capture
│   │   ├── dns_blocker.py       # DNS-level blocking
│   │   └── dns_parser.py        # DNS packet parsing
│   │
│   ├── blocking/                # Content Blocking
│   │   ├── blocker.py           # Main blocking engine
│   │   ├── categories.py        # Category definitions
│   │   └── schedules.py         # Time-based schedules
│   │
│   ├── alerts/                  # Alert System
│   │   ├── alert_engine.py      # Alert processing
│   │   ├── keywords.py          # Keyword matching
│   │   └── notifier.py          # Notification sending
│   │
│   ├── stealth/                 # Stealth Mode
│   │   ├── device_profiles.py   # Fake device profiles
│   │   ├── mac_changer.py       # MAC address spoofing
│   │   └── hostname_changer.py  # Hostname changing
│   │
│   ├── database/                # Data Storage
│   │   ├── db_manager.py        # SQLite manager
│   │   ├── models.py            # Data models
│   │   └── search.py            # Full-text search
│   │
│   └── utils/                   # Utilities
│       ├── logger.py            # Logging
│       ├── config.py            # Configuration
│       └── network_utils.py     # Network helpers
│
├── cert-installer/               # Certificate Installation Server
│   ├── server.py                # Flask web server
│   ├── static/                  # CSS, JS assets
│   └── templates/               # HTML templates for each OS
│       ├── index.html           # Landing page (disguised)
│       ├── ios.html             # iOS instructions
│       ├── android.html         # Android instructions
│       ├── windows.html         # Windows instructions
│       ├── macos.html           # macOS instructions
│       └── complete.html        # Success page
│
├── config/                       # Configuration Files
│   ├── settings.json            # App settings
│   ├── device_profiles.json     # Stealth profiles
│   ├── blocklist.json           # Blocked domains/categories
│   ├── keywords.json            # Alert keywords
│   ├── schedules.json           # Time schedules
│   ├── alerts.json              # Alert rules
│   └── notifications.json       # Notification settings
│
├── database/                     # SQLite Database
│   └── network_monitor.db       # Main database (auto-created)
│
├── certs/                        # Certificates (auto-created)
│   ├── ca.crt                   # CA certificate (public)
│   ├── ca.key                   # CA private key
│   └── ca.pem                   # Combined PEM file
│
├── scripts/                      # Helper Scripts
│   ├── install.ps1              # Windows installer
│   ├── run.ps1                  # Run script
│   ├── setup_npcap.ps1          # Npcap installer
│   ├── generate_cert.ps1        # Certificate generator
│   └── build.ps1                # Build script
│
├── package.json                  # Node.js dependencies
├── pnpm-lock.yaml               # Lock file
├── vite.config.ts               # Vite configuration
├── tailwind.config.js           # Tailwind configuration
├── tsconfig.json                # TypeScript configuration
├── plan.md                      # Implementation plan
├── AGENTS.md                    # AI agent guidelines
└── WALKTHROUGH.md               # This document
```

---

## 3. Prerequisites

### 3.1 System Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| **OS** | Windows 10 | Windows 11 |
| **RAM** | 4 GB | 8 GB+ |
| **Storage** | 500 MB | 2 GB+ |
| **Network** | WiFi adapter | WiFi adapter with monitor mode |
| **Privileges** | Administrator | Administrator |

### 3.2 Software Requirements

#### Required Software

| Software | Version | Purpose | Download |
|----------|---------|---------|----------|
| **Node.js** | 18+ | Frontend build | https://nodejs.org |
| **pnpm** | 8+ | Package manager | `npm install -g pnpm` |
| **Rust** | 1.70+ | Tauri backend | https://rustup.rs |
| **Python** | 3.10+ | Network tools | https://python.org |
| **Npcap** | 1.70+ | Packet capture | https://npcap.com |

#### Python Packages (installed via requirements.txt)

```
scapy>=2.5.0          # Packet manipulation
mitmproxy>=10.0.0     # HTTPS interception
flask>=3.0.0          # Certificate server
psutil>=5.9.0         # System utilities
cryptography>=41.0.0  # Certificate generation
requests>=2.31.0      # HTTP client
netifaces>=0.11.0     # Network interfaces
```

### 3.3 Network Requirements

- **WiFi Connection**: Must be connected to the target WiFi network
- **Same Subnet**: Monitoring PC must be on the same subnet as target devices
- **No AP Isolation**: Router must not have AP/client isolation enabled
- **Administrator Access**: Required for ARP spoofing and packet capture

---

## 4. Installation Guide

### 4.1 Quick Install (Windows PowerShell - Admin)

```powershell
# 1. Clone or navigate to project directory
cd C:\Users\Techsmew\Pictures\Camera Roll\network-monitor

# 2. Run the installer script
.\scripts\install.ps1
```

### 4.2 Manual Installation

#### Step 1: Install Node.js Dependencies

```powershell
# Install pnpm if not installed
npm install -g pnpm

# Install project dependencies
pnpm install
```

#### Step 2: Install Rust (if not installed)

```powershell
# Download and run rustup
winget install Rustlang.Rustup

# Or download from https://rustup.rs
```

#### Step 3: Install Python Dependencies

```powershell
# Create virtual environment
python -m venv network_monitor_env

# Activate virtual environment
.\network_monitor_env\Scripts\Activate.ps1

# Install dependencies
pip install -r python/requirements.txt
```

#### Step 4: Install Npcap

```powershell
# Run the Npcap installer script
.\scripts\setup_npcap.ps1

# Or download manually from https://npcap.com
# IMPORTANT: Enable "WinPcap API-compatible Mode" during installation
```

#### Step 5: Generate CA Certificate

```powershell
# Generate certificate for HTTPS interception
.\scripts\generate_cert.ps1

# Or using Python directly
python python/https/cert_generator.py --action generate --profile "Network Optimizer"
```

#### Step 6: Verify Installation

```powershell
# Check all components
pnpm run check

# Or manually:
node --version          # Should be 18+
pnpm --version          # Should be 8+
rustc --version         # Should be 1.70+
python --version        # Should be 3.10+
pip show scapy          # Should show scapy package
```

### 4.3 First Run

```powershell
# Start in development mode (run as Administrator!)
pnpm tauri dev
```

---

## 5. Configuration

### 5.1 Main Settings (`config/settings.json`)

```json
{
  "theme": "dark",
  "stealth_enabled": true,
  "device_profile": "hp_printer",
  "blocking_enabled": true,
  "notifications_enabled": true,
  "network_interface": "Wi-Fi"
}
```

| Setting | Type | Description |
|---------|------|-------------|
| `theme` | string | UI theme: "dark" or "light" |
| `stealth_enabled` | boolean | Enable stealth mode (MAC/hostname spoofing) |
| `device_profile` | string | Current stealth profile ID |
| `blocking_enabled` | boolean | Enable website blocking |
| `notifications_enabled` | boolean | Enable desktop notifications |
| `network_interface` | string | Network adapter to use |

### 5.2 Device Profiles (`config/device_profiles.json`)

```json
{
  "profiles": [
    {
      "id": "hp_printer",
      "name": "HP LaserJet Pro",
      "type": "printer",
      "vendor": "HP",
      "mac_prefix": "00:1E:0B",
      "hostname": "HP-LaserJet-Pro",
      "mdns_services": ["_ipp._tcp", "_printer._tcp"]
    },
    {
      "id": "samsung_tv",
      "name": "Samsung Smart TV",
      "type": "smart_tv",
      "vendor": "Samsung",
      "mac_prefix": "00:07:AB",
      "hostname": "Samsung-TV",
      "mdns_services": ["_samsungtv._tcp"]
    }
  ]
}
```

### 5.3 Blocklist (`config/blocklist.json`)

```json
{
  "domains": [
    "example-blocked-site.com",
    "*.adult-content.com"
  ],
  "categories": {
    "adult": { "enabled": true, "severity": "high" },
    "gambling": { "enabled": true, "severity": "high" },
    "social_media": { "enabled": false, "severity": "medium" },
    "gaming": { "enabled": false, "severity": "low" }
  },
  "keywords": [
    "explicit-keyword",
    "blocked-term"
  ]
}
```

### 5.4 Alert Keywords (`config/keywords.json`)

```json
{
  "categories": {
    "self_harm": {
      "severity": "critical",
      "keywords": ["suicide", "self-harm", "cutting", "end it all"],
      "notify_immediately": true
    },
    "predators": {
      "severity": "critical", 
      "keywords": ["meet in person", "don't tell your parents", "secret"],
      "notify_immediately": true
    },
    "drugs": {
      "severity": "high",
      "keywords": ["buy drugs", "dealer", "pills for sale"],
      "notify_immediately": true
    },
    "bullying": {
      "severity": "high",
      "keywords": ["kill yourself", "nobody likes you", "loser"],
      "notify_immediately": false
    }
  }
}
```

### 5.5 Schedules (`config/schedules.json`)

```json
{
  "schedules": [
    {
      "id": "school_hours",
      "name": "School Hours",
      "enabled": true,
      "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
      "start_time": "08:00",
      "end_time": "15:00",
      "action": "block_social_media"
    },
    {
      "id": "bedtime",
      "name": "Bedtime",
      "enabled": true,
      "days": ["sunday", "monday", "tuesday", "wednesday", "thursday"],
      "start_time": "21:00",
      "end_time": "07:00",
      "action": "block_all"
    }
  ]
}
```

---

## 6. Component Details

### 6.1 ARP Spoofing Module (`python/arp/`)

#### Purpose
Tricks devices on the network into sending their traffic through the monitoring PC by pretending to be the router.

#### How It Works

```
NORMAL NETWORK:
Device → Router → Internet

WITH ARP SPOOFING:
Device → Monitoring PC → Router → Internet
         (intercepts)
```

#### Files

| File | Description |
|------|-------------|
| `arp_gateway.py` | Main ARP spoofing loop |
| `device_scanner.py` | Discovers devices on network |
| `ip_forwarding.py` | Enables Windows IP forwarding |

#### Usage

```python
# Scan for devices
python python/arp/device_scanner.py --scan

# Start ARP spoofing
python python/arp/arp_gateway.py --interface "Wi-Fi"
```

#### Important Notes

- Requires **Administrator privileges**
- Requires **Npcap** installed
- Automatically restores ARP tables on exit
- Only spoofs devices marked as "monitored"

---

### 6.2 HTTPS Proxy Module (`python/https/`)

#### Purpose
Intercepts and decrypts HTTPS traffic using a man-in-the-middle proxy.

#### How It Works

```
1. Generate CA certificate (one-time)
2. Install CA on target devices
3. Proxy intercepts HTTPS connections
4. Decrypts, inspects, re-encrypts traffic
5. Logs to database
```

#### Files

| File | Description |
|------|-------------|
| `transparent_proxy.py` | mitmproxy integration |
| `cert_generator.py` | CA certificate generation |
| `content_decoder.py` | Decodes response bodies (gzip, etc.) |
| `traffic_parser.py` | Parses HTTP requests/responses |

#### Usage

```python
# Generate certificate
python python/https/cert_generator.py --action generate --profile "Network Optimizer"

# Start proxy
python python/https/transparent_proxy.py --action start
```

#### Certificate Profiles

The CA certificate can be disguised with different names:

| Profile | Common Name | Organization |
|---------|-------------|--------------|
| `network_optimizer` | Network Optimizer CA | Network Services |
| `security_scanner` | Security Scanner CA | IT Security |
| `parental_control` | Parental Control CA | Family Safety |

---

### 6.3 DNS Capture Module (`python/dns/`)

#### Purpose
Captures and logs all DNS queries, enabling domain-level blocking without HTTPS decryption.

#### Files

| File | Description |
|------|-------------|
| `dns_capture.py` | Sniffs DNS packets |
| `dns_blocker.py` | DNS-level blocking |
| `dns_parser.py` | Parses DNS packets |

#### Usage

```python
# Start DNS capture
python python/dns/dns_capture.py --interface "Wi-Fi"
```

---

### 6.4 Blocking Engine (`python/blocking/`)

#### Purpose
Blocks websites based on domains, categories, keywords, or schedules.

#### Blocking Methods

| Method | Level | Requires Cert? |
|--------|-------|----------------|
| DNS Block | Domain | No |
| HTTP Block | URL/Content | Yes |
| Category Block | Domain lists | No |
| Keyword Block | Content | Yes |
| Schedule Block | Time-based | No |

#### Files

| File | Description |
|------|-------------|
| `blocker.py` | Main blocking engine |
| `categories.py` | Category definitions and domain lists |
| `schedules.py` | Time-based schedule logic |

#### Usage

```python
# Block a domain
python python/blocking/blocker.py --action block --domain "facebook.com"

# Check if domain is blocked
python python/blocking/blocker.py --action check --domain "facebook.com"

# Get blocking config
python python/blocking/blocker.py --action config
```

---

### 6.5 Alert Engine (`python/alerts/`)

#### Purpose
Monitors traffic for concerning content and generates real-time alerts.

#### Alert Severities

| Severity | Color | Examples |
|----------|-------|----------|
| `critical` | Red | Suicide mentions, predator behavior |
| `high` | Orange | Drug references, severe bullying |
| `medium` | Yellow | Inappropriate content |
| `low` | Blue | Policy violations |

#### Files

| File | Description |
|------|-------------|
| `alert_engine.py` | Main alert processing |
| `keywords.py` | Keyword matching with context |
| `notifier.py` | Desktop/email notifications |

#### Usage

```python
# List alerts
python python/alerts/alert_engine.py --action list

# Process content for alerts
python python/alerts/alert_engine.py --action process --content "test content" --url "http://example.com"

# Acknowledge an alert
python python/alerts/alert_engine.py --action acknowledge --id "alert_123"

# Delete an alert
python python/alerts/alert_engine.py --action delete --id "alert_123"
```

---

### 6.6 Stealth Mode (`python/stealth/`)

#### Purpose
Disguises the monitoring PC as a harmless device (printer, TV, etc.) to avoid detection.

#### What It Changes

| Property | Before | After (HP Printer) |
|----------|--------|-------------------|
| MAC Address | AA:BB:CC:DD:EE:FF | 00:1E:0B:XX:XX:XX |
| Hostname | DESKTOP-ABC123 | HP-LaserJet-Pro |
| mDNS Services | None | _ipp._tcp, _printer._tcp |

#### Files

| File | Description |
|------|-------------|
| `device_profiles.py` | Profile definitions |
| `mac_changer.py` | MAC address spoofing |
| `hostname_changer.py` | Hostname changing |

#### Usage

```python
# List available profiles
python python/stealth/mac_changer.py --list-profiles

# Apply a profile
python python/stealth/mac_changer.py --profile hp_printer --interface "Wi-Fi"

# Restore original settings
python python/stealth/mac_changer.py --restore --interface "Wi-Fi"
```

---

### 6.7 Certificate Installer (`cert-installer/`)

#### Purpose
Provides a user-friendly web interface for installing the CA certificate on target devices.

#### How It Works

```
1. Start Flask server on port 8888
2. User visits http://[monitoring-pc-ip]:8888
3. Landing page disguised as "Network Optimizer"
4. Detects user's device OS
5. Shows OS-specific installation instructions
6. Provides certificate download
```

#### Files

| File | Description |
|------|-------------|
| `server.py` | Flask web server |
| `templates/index.html` | Disguised landing page |
| `templates/ios.html` | iOS installation guide |
| `templates/android.html` | Android installation guide |
| `templates/windows.html` | Windows installation guide |
| `templates/macos.html` | macOS installation guide |

#### Usage

```python
# Start certificate server
python cert-installer/server.py

# Server runs on http://0.0.0.0:8888
```

---

### 6.8 Database (`python/database/`)

#### Purpose
Stores all captured traffic, devices, alerts, and statistics in SQLite.

#### Files

| File | Description |
|------|-------------|
| `db_manager.py` | SQLite operations |
| `models.py` | Data models (Device, Traffic, etc.) |
| `search.py` | Full-text search helpers |

#### Usage

```python
# Get statistics
python python/database/db_manager.py --action stats

# Search traffic
python python/database/db_manager.py --action search --query "facebook"

# List devices
python python/database/db_manager.py --action devices

# Get traffic entries
python python/database/db_manager.py --action traffic --limit 50

# Export data
python python/database/db_manager.py --action export --format json --output backup.json

# Cleanup old data
python python/database/db_manager.py --action cleanup --days 30
```

---

### 6.9 Tauri Backend (`src-tauri/`)

#### Purpose
Bridges the React frontend with Python backend, manages app state, and handles system integration.

#### Files

| File | Description |
|------|-------------|
| `main.rs` | App entry point, command registration |
| `commands.rs` | All Tauri command handlers |
| `python.rs` | Python process spawning and IPC |
| `state.rs` | App state (monitoring status, etc.) |

#### Command Categories

| Category | Commands |
|----------|----------|
| **Monitoring** | start_monitoring, stop_monitoring, get_status |
| **Devices** | get_devices, scan_devices, set_device_monitoring |
| **Traffic** | get_traffic, search_traffic, get_traffic_details |
| **Alerts** | get_alerts, mark_alert_read, resolve_alert, delete_alert |
| **Blocking** | add_block_rule, remove_block_rule, toggle_category |
| **Settings** | get_settings, update_settings |
| **Stealth** | change_stealth_profile, get_stealth_profiles |
| **Certificates** | generate_certificate, start_cert_server, get_cert_url |
| **System** | check_admin, get_network_interfaces, cleanup_database |

---

### 6.10 React Frontend (`src/`)

#### Purpose
Provides a modern, responsive user interface for monitoring and control.

#### Pages

| Page | Route | Description |
|------|-------|-------------|
| Dashboard | `/` | Overview with stats and charts |
| Devices | `/devices` | Device list and management |
| Traffic | `/traffic` | Real-time traffic viewer |
| Blocking | `/blocking` | Block rules and categories |
| Alerts | `/alerts` | Alert list and management |
| Settings | `/settings` | App configuration |

#### State Management (Zustand Stores)

| Store | Purpose |
|-------|---------|
| `useMonitoringStore` | Monitoring status |
| `useDeviceStore` | Device list and selection |
| `useTrafficStore` | Traffic entries |
| `useAlertStore` | Alerts and counts |
| `useSettingsStore` | App settings |

---

## 7. Usage Guide

### 7.1 Starting the Application

```powershell
# MUST run as Administrator!
# Right-click PowerShell → Run as Administrator

cd C:\Users\Techsmew\Pictures\Camera Roll\network-monitor

# Development mode
pnpm tauri dev

# Or production build
pnpm tauri build
.\src-tauri\target\release\network-monitor.exe
```

### 7.2 Initial Setup Wizard

1. **Select Network Interface**
   - Go to Settings → Network Interface
   - Select your WiFi adapter

2. **Configure Stealth Mode**
   - Go to Settings → Stealth Mode
   - Choose a device profile (HP Printer recommended)
   - Click "Apply Stealth Profile"

3. **Generate Certificate**
   - Go to Settings → Certificates
   - Click "Generate New Certificate"
   - Choose a profile name (e.g., "Network Optimizer")

4. **Start Certificate Server**
   - Click "Start Certificate Server"
   - Note the URL shown (e.g., http://192.168.1.100:8888)

### 7.3 Installing Certificates on Devices

#### On Target Device:

1. Connect to the same WiFi network
2. Open browser and go to: `http://[monitoring-pc-ip]:8888`
3. Follow the OS-specific instructions
4. Trust the installed certificate

#### iOS

```
1. Download profile (tap the link)
2. Settings → General → VPN & Device Management
3. Tap the downloaded profile
4. Install → Enter passcode
5. Settings → General → About → Certificate Trust Settings
6. Enable full trust for the certificate
```

#### Android

```
1. Download certificate file
2. Settings → Security → Install from storage
3. Select the downloaded .crt file
4. Name it (e.g., "Network Optimizer")
5. Set usage to "VPN and apps"
```

#### Windows

```
1. Download certificate file
2. Double-click the .crt file
3. Click "Install Certificate"
4. Select "Local Machine"
5. Select "Place in specific store"
6. Choose "Trusted Root Certification Authorities"
7. Click Finish
```

### 7.4 Starting Monitoring

1. **Ensure all prerequisites are met:**
   - Running as Administrator
   - Npcap installed
   - Stealth mode configured (optional)
   - Target devices have certificate installed

2. **Start Monitoring:**
   - Click the "Start Monitoring" button on Dashboard
   - Wait for all services to start (ARP, HTTPS Proxy, DNS)

3. **Verify Status:**
   - Check the status indicators turn green
   - Look for devices appearing in the Devices page

### 7.5 Viewing Traffic

1. Go to the **Traffic** page
2. Traffic entries appear in real-time
3. Use filters:
   - By device
   - By domain
   - By status (blocked/allowed)
   - By alert status

4. Click an entry to see details:
   - Request headers
   - Request body
   - Response headers
   - Response body (decoded)

5. Use the search bar for full-text search across all captured content

### 7.6 Managing Devices

1. Go to the **Devices** page
2. View all discovered devices with:
   - Hostname
   - IP Address
   - MAC Address
   - Device Type
   - Online Status
   - Certificate Status

3. Click a device to:
   - Enable/disable monitoring
   - View device-specific traffic
   - See bandwidth usage

4. Click "Scan Network" to discover new devices

### 7.7 Configuring Blocking

1. Go to the **Blocking** page

2. **Block a Domain:**
   - Enter domain in the "Add Domain" field
   - Click "Block"
   - Supports wildcards: `*.facebook.com`

3. **Block by Category:**
   - Toggle categories on/off:
     - Adult Content
     - Gambling
     - Social Media
     - Gaming
     - Violence
     - etc.

4. **Block by Keyword:**
   - Add keywords that will block pages containing them
   - Requires certificate installed on device

5. **Create Schedule:**
   - Click "Add Schedule"
   - Set name, days, start/end time
   - Choose action (block categories, block all, etc.)

### 7.8 Reviewing Alerts

1. Go to the **Alerts** page
2. Alerts are color-coded by severity:
   - 🔴 Critical - Immediate attention needed
   - 🟠 High - Review soon
   - 🟡 Medium - Review when possible
   - 🔵 Low - Informational

3. Click an alert to see:
   - Full context
   - Matched keywords
   - Source device
   - URL/domain
   - Timestamp

4. Actions:
   - Mark as Read
   - Resolve (dismiss)
   - Delete

### 7.9 Changing Settings

Go to **Settings** to configure:

| Setting | Description |
|---------|-------------|
| Theme | Dark or Light mode |
| Network Interface | Select WiFi adapter |
| Stealth Mode | Enable/disable, choose profile |
| Notifications | Desktop notification settings |
| Data Retention | How long to keep traffic data |
| Export Data | Export to JSON/CSV |

---

## 8. API Reference

### 8.1 Frontend API (`src/lib/api.ts`)

All API calls use the `invoke` function from Tauri:

```typescript
import api from '@/lib/api';

// Monitoring
await api.monitoring.start();
await api.monitoring.stop();
const status = await api.monitoring.getStatus();

// Devices
const devices = await api.devices.getAll();
await api.devices.setMonitoring(deviceId, true);
const scanned = await api.devices.scan();

// Traffic
const traffic = await api.traffic.get({ limit: 100, device_id: 'xxx' });
const results = await api.traffic.search('facebook');
const details = await api.traffic.getDetails(entryId);

// Alerts
const alerts = await api.alerts.getAll(false);  // false = all, true = unread only
await api.alerts.markAsRead(alertId);
await api.alerts.resolve(alertId);
await api.alerts.delete(alertId);
await api.alerts.markAllAsRead();

// Stats
const stats = await api.stats.get();

// Blocking
const config = await api.blocking.getConfig();
await api.blocking.addRule('domain', 'facebook.com');
await api.blocking.removeRule('domain', 'facebook.com');
await api.blocking.toggleCategory('adult', true);
const check = await api.blocking.checkDomain('example.com');

// Stealth
const profiles = await api.stealth.getProfiles();
await api.stealth.changeProfile('hp_printer');

// Certificates
await api.certificates.generate('Network Optimizer');
await api.certificates.startServer();
const url = await api.certificates.getServerUrl();

// Settings
const settings = await api.settings.get();
await api.settings.update({ theme: 'dark' });

// Export
await api.exportData.toFile('json', '/path/to/export.json');

// System
const isAdmin = await api.system.isAdmin();
const interfaces = await api.system.getInterfaces();
await api.system.cleanupDatabase(30);
```

### 8.2 Python CLI Reference

#### Database Manager

```bash
python python/database/db_manager.py --action <action> [options]

Actions:
  stats              Get database statistics
  search             Full-text search (requires --query)
  devices            List all devices
  traffic            List traffic entries
  dns                List DNS queries
  get-traffic        Get single traffic entry (requires --id)
  update-device      Update device (requires --device, --monitored)
  export             Export data (requires --output, --format)
  cleanup            Delete old data (uses --days)

Options:
  --query TEXT       Search query
  --device TEXT      Device ID
  --id TEXT          Entry ID
  --monitored 0|1    Set monitored status
  --host TEXT        Filter by host
  --limit INT        Max results (default: 100)
  --days INT         Days to keep (default: 30)
  --format TEXT      Export format: json, csv
  --output TEXT      Export file path
```

#### Alert Engine

```bash
python python/alerts/alert_engine.py --action <action> [options]

Actions:
  stats              Get alert statistics
  list               List alerts
  process            Process content for alerts
  acknowledge        Mark alert as read
  acknowledge-all    Mark all alerts as read
  delete             Delete an alert
  unacknowledged     Get unacknowledged counts

Options:
  --id TEXT          Alert ID
  --content TEXT     Content to scan
  --url TEXT         URL context
  --domain TEXT      Domain context
  --severity TEXT    Filter by severity
  --category TEXT    Filter by category
  --limit INT        Max results
```

#### Blocking Engine

```bash
python python/blocking/blocker.py --action <action> [options]

Actions:
  block              Block a domain
  unblock            Unblock a domain
  block-category     Enable category blocking
  unblock-category   Disable category blocking
  add-keyword        Add blocking keyword
  remove-keyword     Remove blocking keyword
  check              Check if domain is blocked
  config             Get blocking configuration

Options:
  --domain TEXT      Domain to block/unblock
  --category TEXT    Category name
  --keyword TEXT     Keyword to add/remove
```

#### Network Utilities

```bash
python python/utils/network_utils.py --action <action> [options]

Actions:
  get-ip             Get local IP address
  list-interfaces    List network interfaces
  get-gateway        Get gateway IP and MAC
  get-mac            Get MAC address
  get-range          Get network range (CIDR)
  is-admin           Check admin privileges

Options:
  --interface TEXT   Network interface name
```

#### Stealth Mode

```bash
python python/stealth/mac_changer.py [options]

Options:
  --list-profiles    List available profiles
  --profile TEXT     Profile ID to apply
  --interface TEXT   Network interface
  --restore          Restore original settings
  --show             Show current MAC address
```

---

## 9. Database Schema

### 9.1 Tables

#### devices

```sql
CREATE TABLE devices (
    id TEXT PRIMARY KEY,
    mac_address TEXT UNIQUE NOT NULL,
    ip_address TEXT NOT NULL,
    hostname TEXT,
    device_type TEXT DEFAULT 'unknown',
    manufacturer TEXT,
    nickname TEXT,
    is_monitored INTEGER DEFAULT 1,
    has_certificate INTEGER DEFAULT 0,
    first_seen TEXT,
    last_seen TEXT,
    total_requests INTEGER DEFAULT 0,
    total_bytes INTEGER DEFAULT 0,
    metadata TEXT DEFAULT '{}'
);
```

#### traffic

```sql
CREATE TABLE traffic (
    id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    device_id TEXT,
    device_ip TEXT NOT NULL,
    method TEXT NOT NULL,
    url TEXT NOT NULL,
    host TEXT NOT NULL,
    path TEXT,
    protocol TEXT DEFAULT 'https',
    request_headers TEXT DEFAULT '{}',
    request_body TEXT,
    request_body_type TEXT,
    request_size INTEGER DEFAULT 0,
    status_code INTEGER,
    status_message TEXT,
    response_headers TEXT DEFAULT '{}',
    response_body TEXT,
    response_body_type TEXT,
    response_size INTEGER DEFAULT 0,
    duration_ms INTEGER DEFAULT 0,
    category TEXT,
    sensitivity TEXT,
    blocked INTEGER DEFAULT 0,
    block_reason TEXT,
    intercepted INTEGER DEFAULT 1,
    alerts TEXT DEFAULT '[]',
    FOREIGN KEY (device_id) REFERENCES devices(id)
);
```

#### dns_queries

```sql
CREATE TABLE dns_queries (
    id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    device_id TEXT,
    device_ip TEXT NOT NULL,
    query_name TEXT NOT NULL,
    query_type TEXT DEFAULT 'A',
    response_ip TEXT,
    response_ttl INTEGER,
    blocked INTEGER DEFAULT 0,
    block_reason TEXT,
    category TEXT,
    FOREIGN KEY (device_id) REFERENCES devices(id)
);
```

#### sessions

```sql
CREATE TABLE sessions (
    session_id TEXT PRIMARY KEY,
    start_time TEXT NOT NULL,
    end_time TEXT,
    total_requests INTEGER DEFAULT 0,
    total_bytes_in INTEGER DEFAULT 0,
    total_bytes_out INTEGER DEFAULT 0,
    blocked_count INTEGER DEFAULT 0,
    alert_count INTEGER DEFAULT 0,
    devices_seen INTEGER DEFAULT 0,
    top_domains TEXT DEFAULT '{}',
    top_categories TEXT DEFAULT '{}'
);
```

#### traffic_fts (Full-Text Search)

```sql
CREATE VIRTUAL TABLE traffic_fts USING fts5(
    id UNINDEXED,
    url,
    host,
    request_body,
    response_body,
    content='traffic',
    content_rowid='rowid'
);
```

### 9.2 Indexes

```sql
CREATE INDEX idx_dns_timestamp ON dns_queries(timestamp);
CREATE INDEX idx_dns_device ON dns_queries(device_id);
CREATE INDEX idx_dns_domain ON dns_queries(query_name);
CREATE INDEX idx_traffic_timestamp ON traffic(timestamp);
CREATE INDEX idx_traffic_device ON traffic(device_id);
CREATE INDEX idx_traffic_host ON traffic(host);
CREATE INDEX idx_traffic_category ON traffic(category);
```

---

## 10. Security Considerations

### 10.1 Legal Considerations

> **WARNING**: Using this software may be illegal in your jurisdiction without proper consent.

- Only use on networks you own or have explicit permission to monitor
- Inform all network users that monitoring is in place
- May violate wiretapping laws if used without consent
- Not intended for use on corporate or public networks

### 10.2 Data Security

| Risk | Mitigation |
|------|------------|
| Database contains sensitive data | Database is local-only, not cloud-synced |
| Captured passwords | Passwords in traffic are logged - secure the database |
| CA private key | Store securely, don't share |
| Admin credentials | Required to run - don't share access |

### 10.3 Network Security

| Risk | Mitigation |
|------|------------|
| ARP spoofing detectable | Use stealth mode to appear as innocent device |
| Certificate warnings | Properly install CA on target devices |
| Network disruption | Automatic ARP table restoration on exit |

### 10.4 Recommendations

1. **Password-protect the application** (not yet implemented)
2. **Encrypt the database** (not yet implemented)
3. **Use disk encryption** (BitLocker on Windows)
4. **Regular data cleanup** to minimize exposure
5. **Secure physical access** to the monitoring PC

---

## 11. Troubleshooting

### 11.1 Common Issues

#### "Npcap not found" Error

```
Solution:
1. Download Npcap from https://npcap.com
2. Run installer as Administrator
3. Enable "WinPcap API-compatible Mode"
4. Restart the application
```

#### "Access Denied" or "Requires Admin"

```
Solution:
1. Right-click PowerShell → Run as Administrator
2. Right-click the .exe → Run as Administrator
3. Disable UAC temporarily if needed
```

#### Devices Not Appearing

```
Solution:
1. Ensure you're on the same WiFi network
2. Check if AP isolation is disabled on router
3. Run a network scan: Devices → Scan Network
4. Check Windows Firewall isn't blocking
```

#### HTTPS Traffic Not Decrypted

```
Solution:
1. Verify certificate is installed on target device
2. Check certificate is trusted (not just installed)
3. Some apps use certificate pinning - these can't be decrypted
4. Restart the target device after certificate install
```

#### High CPU Usage

```
Solution:
1. Reduce traffic logging (disable body capture)
2. Increase cleanup frequency (Settings → Data Retention)
3. Close other monitoring windows
4. Reduce number of monitored devices
```

#### "Python script failed" Error

```
Solution:
1. Activate virtual environment
2. Verify all dependencies installed: pip install -r requirements.txt
3. Check Python version is 3.10+
4. Review error message for specific module issues
```

### 11.2 Log Files

| Log | Location | Content |
|-----|----------|---------|
| App log | `%APPDATA%/network-monitor/logs/` | General app logs |
| Python log | `python/logs/` | Python backend logs |
| Tauri log | Console (dev mode) | Rust backend logs |

### 11.3 Debug Mode

```powershell
# Run with verbose logging
$env:RUST_LOG="debug"
pnpm tauri dev

# Python debug mode
python python/main.py --debug
```

---

## 12. Development Guide

### 12.1 Development Setup

```powershell
# Clone repository
git clone <repository-url>
cd network-monitor

# Install dependencies
pnpm install
pip install -r python/requirements.txt

# Start development server
pnpm tauri dev
```

### 12.2 Project Scripts

```json
{
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "tauri": "tauri",
    "tauri:dev": "tauri dev",
    "tauri:build": "tauri build",
    "lint": "eslint src --ext ts,tsx",
    "lint:fix": "eslint src --ext ts,tsx --fix",
    "typecheck": "tsc --noEmit",
    "test": "vitest"
  }
}
```

### 12.3 Adding a New Feature

1. **Frontend Component:**
   ```
   src/components/feature/FeatureName.tsx
   ```

2. **Tauri Command:**
   ```rust
   // src-tauri/src/commands.rs
   #[tauri::command]
   pub async fn feature_command() -> Result<Data, String> { }
   
   // src-tauri/src/main.rs
   .invoke_handler(tauri::generate_handler![
       commands::feature_command,
   ])
   ```

3. **Python Backend:**
   ```python
   # python/feature/feature_module.py
   def main():
       # CLI entry point
   ```

4. **API Wrapper:**
   ```typescript
   // src/lib/api.ts
   export const feature = {
     action: () => invokeCommand('feature_command'),
   };
   ```

### 12.4 Code Style

#### TypeScript/React
- Functional components with explicit types
- Custom hooks prefixed with `use`
- Zustand for global state
- Tailwind for styling

#### Rust
- `#[tauri::command]` for all commands
- `Result<T, String>` return types
- Use `?` operator for error propagation

#### Python
- PEP 8 style (enforced by Ruff)
- Type hints required
- Google-style docstrings
- JSON output for CLI scripts

### 12.5 Testing

```powershell
# Frontend tests
pnpm test

# Rust tests
cd src-tauri && cargo test

# Python tests
pytest python/
```

### 12.6 Building for Production

```powershell
# Build Windows executable
pnpm tauri build

# Output location
.\src-tauri\target\release\network-monitor.exe

# Installer location
.\src-tauri\target\release\bundle\msi\network-monitor_x.x.x_x64.msi
```

---

## Quick Reference Card

### Start Monitoring

```powershell
# As Administrator
pnpm tauri dev
```

### Key URLs

| URL | Purpose |
|-----|---------|
| http://localhost:1420 | Frontend dev server |
| http://[local-ip]:8888 | Certificate installer |
| http://localhost:8080 | mitmproxy web interface |

### Key Files

| File | Purpose |
|------|---------|
| `config/settings.json` | Main settings |
| `config/blocklist.json` | Blocked sites |
| `config/keywords.json` | Alert keywords |
| `database/network_monitor.db` | All captured data |
| `certs/ca.crt` | CA certificate (install on devices) |

### Emergency Stop

```powershell
# Stop all Python processes
Get-Process python | Stop-Process -Force

# Restore ARP tables (automatic on clean exit)
python python/arp/arp_gateway.py --restore

# Restore MAC address
python python/stealth/mac_changer.py --restore --interface "Wi-Fi"
```

---

## Support

For issues and feature requests, please refer to:
- `AGENTS.md` - AI agent guidelines
- `plan.md` - Implementation plan
- GitHub Issues (if published)

---

*Document Version: 1.0*
*Last Updated: 2024*
