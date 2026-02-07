# Network Monitor - Complete Implementation Plan

## Executive Summary

A **stealth desktop application** that monitors ALL network traffic from devices on your WiFi network. Features dual-layer monitoring:

1. **DNS Monitoring** - No installation required, works immediately
2. **Full HTTPS Decryption** - Via remote certificate installation link

Includes MAC spoofing for anonymity, website blocking, keyword alerts, and complete traffic logging.

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Feature List](#feature-list)
3. [Stealth System](#1-stealth-system)
4. [DNS Monitoring](#2-dns-monitoring)
5. [HTTPS Monitoring](#3-https-monitoring)
6. [Certificate Remote Installation](#4-certificate-remote-installation)
7. [Blocking Engine](#5-blocking-engine)
8. [Alert System](#6-alert-system)
9. [Traffic Logging](#7-traffic-logging--history)
10. [Dashboard UI](#8-dashboard-ui)
11. [Project Structure](#project-structure)
12. [Configuration Files](#configuration-files)
13. [Implementation Phases](#implementation-phases)
14. [Prerequisites](#prerequisites)
15. [Security & Legal](#security--legal-notes)

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           NETWORK MONITOR SYSTEM                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│                                 INTERNET                                         │
│                                     │                                            │
│                                     ▼                                            │
│                              ┌──────────┐                                        │
│                              │  ROUTER  │                                        │
│                              └────┬─────┘                                        │
│                                   │                                              │
│      ┌────────────────────────────┼────────────────────────────┐                │
│      │                            │                            │                │
│      ▼                            ▼                            ▼                │
│  ┌────────┐                ┌─────────────┐              ┌────────┐              │
│  │Child's │                │  YOUR PC    │              │ Other  │              │
│  │Device  │                │ (DISGUISED) │              │Devices │              │
│  └───┬────┘                │             │              └────────┘              │
│      │                     │ Appears as: │                                      │
│      │                     │ "HP Printer"│                                      │
│      │    ARP Spoof        │ or "Smart TV"│                                     │
│      │◄────────────────────│             │                                      │
│      │  "I am the router"  └──────┬──────┘                                      │
│      │                            │                                              │
│      │     ALL TRAFFIC            │                                              │
│      └───────────────────────────►│                                              │
│                                   │                                              │
│                    ┌──────────────┴──────────────┐                              │
│                    │                             │                              │
│                    ▼                             ▼                              │
│          ┌─────────────────┐          ┌─────────────────┐                       │
│          │  DNS MONITOR    │          │  HTTPS MONITOR  │                       │
│          │  ────────────   │          │  ────────────── │                       │
│          │  NO CERT NEEDED │          │  CERT REQUIRED  │                       │
│          │                 │          │                 │                       │
│          │ • Domain names  │          │ • Full URLs     │                       │
│          │ • All devices   │          │ • Messages      │                       │
│          │ • Blocking      │          │ • Searches      │                       │
│          │ • Alerts        │          │ • Form data     │                       │
│          └────────┬────────┘          └────────┬────────┘                       │
│                   │                            │                                │
│                   └─────────────┬──────────────┘                                │
│                                 ▼                                               │
│                   ┌─────────────────────────┐                                   │
│                   │    UNIFIED DASHBOARD    │                                   │
│                   │    ─────────────────    │                                   │
│                   │  • Real-time traffic   │                                   │
│                   │  • Device management   │                                   │
│                   │  • Block manager       │                                   │
│                   │  • Keyword alerts      │                                   │
│                   │  • History search      │                                   │
│                   │  • Stealth controls    │                                   │
│                   └─────────────────────────┘                                   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              DATA FLOW                                           │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  Child's Device                                                                  │
│       │                                                                          │
│       │ 1. DNS Query: "instagram.com"                                           │
│       ▼                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │  YOUR PC (Acting as Router via ARP Spoofing)                            │    │
│  │  ─────────────────────────────────────────────                          │    │
│  │                                                                          │    │
│  │  2. DNS CAPTURE ──► Log domain ──► Check blocklist ──► Allow/Block      │    │
│  │          │                                                               │    │
│  │          ▼                                                               │    │
│  │  3. If allowed, forward to real DNS                                     │    │
│  │          │                                                               │    │
│  │          ▼                                                               │    │
│  │  4. Child connects to instagram.com                                     │    │
│  │          │                                                               │    │
│  │          ▼                                                               │    │
│  │  5. HTTPS PROXY (if cert installed)                                     │    │
│  │     ├── Decrypt traffic                                                 │    │
│  │     ├── Parse content (messages, searches, etc.)                        │    │
│  │     ├── Check for alert keywords                                        │    │
│  │     ├── Log to database                                                 │    │
│  │     └── Re-encrypt and forward                                          │    │
│  │          │                                                               │    │
│  │          ▼                                                               │    │
│  │  6. Traffic reaches destination                                         │    │
│  │                                                                          │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│       │                                                                          │
│       ▼                                                                          │
│  Real Instagram Server                                                           │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Feature List

### 1. Stealth System

Disguise your PC to avoid detection on the network.

| Feature | Description | Configurable |
|---------|-------------|--------------|
| **MAC Randomization** | Disguise PC as printer, TV, smart home device | Yes - choose device type |
| **Hostname Spoofing** | Match hostname to fake device (HP-LaserJet, Samsung-TV) | Yes - custom names |
| **Device Profiles** | Pre-configured profiles for common devices | Yes - add custom |
| **Auto-Rotation** | Automatically change MAC periodically | Yes - interval |
| **Quiet ARP Mode** | Reduce ARP packet frequency to avoid detection | Yes - timing |
| **Hidden Process** | Hide from taskbar, use generic process name | Yes - enable/disable |
| **Panic Button** | Instantly hide application with hotkey | Yes - custom hotkey |
| **Boss Screen** | Show fake application on panic | Yes - customize |
| **Startup Options** | Start hidden, start with Windows | Yes - configure |

#### Device Profiles Available

| Profile | MAC Prefix | Hostname | Description |
|---------|------------|----------|-------------|
| HP Printer | 00:1A:2B | HP-LaserJet-Pro | Common office printer |
| Samsung TV | 00:1E:A6 | Samsung-TV | Smart television |
| Google Nest | F4:F5:D8 | Google-Home | Smart speaker |
| Amazon Echo | FC:A1:83 | Echo-Dot | Alexa device |
| Apple TV | 40:CB:C0 | Apple-TV | Streaming device |
| Philips Hue | 00:17:88 | Philips-Hue | Smart light bridge |
| Ring Doorbell | 34:3E:A4 | Ring-Doorbell | Security camera |
| Roku | 84:EA:ED | Roku-Ultra | Streaming device |
| Custom | User-defined | User-defined | Create your own |

---

### 2. DNS Monitoring

Monitor all domain lookups without any installation on target devices.

| Feature | Description | Configurable |
|---------|-------------|--------------|
| **Domain Capture** | See all domains visited by all devices | Automatic |
| **Real-time Stream** | Live view of DNS queries | Automatic |
| **Device Identification** | Track by IP and MAC address | Automatic |
| **Hostname Resolution** | Resolve device names when possible | Automatic |
| **Query Types** | Capture A, AAAA, CNAME, MX, etc. | Filter options |
| **Response Logging** | Log DNS responses too | Yes - enable |
| **Domain Statistics** | Most visited domains per device | Automatic |
| **Export DNS Logs** | Export to CSV/JSON | Automatic |

#### DNS Blocking

| Feature | Description | Configurable |
|---------|-------------|--------------|
| **Domain Blocklist** | Block specific domains | Yes - add/remove |
| **Wildcard Blocking** | Block *.tiktok.com | Yes - patterns |
| **Category Blocking** | Block entire categories | Yes - toggles |
| **Silent Block** | Return NXDOMAIN (site doesn't exist) | Yes - or redirect |
| **Block Page** | Redirect to block page instead | Yes - custom page |
| **Per-Device Rules** | Different rules per device | Yes |
| **Bypass Whitelist** | Allow specific domains always | Yes |

#### Built-in Block Categories

| Category | Examples | Default |
|----------|----------|---------|
| Adult | pornhub.com, xvideos.com, etc. | Off |
| Gambling | bet365.com, pokerstars.com | Off |
| Social Media | tiktok.com, instagram.com | Off |
| Gaming | roblox.com, fortnite.com | Off |
| Streaming | netflix.com, twitch.tv | Off |
| Dating | tinder.com, bumble.com | Off |
| Drugs | Drug-related sites | Off |
| Weapons | Weapon-related sites | Off |
| Malware | Known malicious domains | On |
| Ads | Ad networks | Off |

---

### 3. HTTPS Monitoring

Full visibility into encrypted traffic after certificate installation.

| Feature | Description | Configurable |
|---------|-------------|--------------|
| **Full URL Capture** | Complete URLs with paths and parameters | Automatic |
| **Request Headers** | All HTTP headers | Automatic |
| **Response Headers** | All response headers | Automatic |
| **Request Bodies** | Form submissions, JSON payloads, file uploads | Automatic |
| **Response Bodies** | API responses, page content, downloads | Automatic |
| **Cookies** | All cookies sent and received | Automatic |
| **WebSocket Traffic** | Real-time WebSocket messages | Automatic |
| **HTTP/2 Support** | Modern protocol support | Automatic |

#### Content Parsing

| Content Type | Parsing | Example |
|--------------|---------|---------|
| JSON | Pretty-printed, searchable | API responses |
| Form Data | Key-value pairs | Login forms |
| HTML | Rendered preview | Web pages |
| XML | Formatted | RSS feeds |
| Images | Thumbnail preview | Photos |
| Video | URL extraction | Streaming |
| Binary | Hex view | Downloads |

#### Special Detections

| Detection | What You See |
|-----------|--------------|
| **Messages** | Social media DMs, chat messages |
| **Searches** | Google, YouTube, TikTok searches |
| **Logins** | Login attempts (username visible) |
| **Posts** | Social media posts and comments |
| **Profile Views** | Profiles they view |
| **Video Watches** | Video titles and URLs |
| **File Downloads** | Downloaded file URLs |
| **Location Shares** | Shared locations |

---

### 4. Certificate Remote Installation

Install monitoring certificate without physical device access.

| Feature | Description | Configurable |
|---------|-------------|--------------|
| **Landing Page** | Professional security update page | Yes - full customization |
| **Device Detection** | Auto-detect Android/iOS/Windows | Automatic |
| **Certificate Download** | Auto-download appropriate cert format | Automatic |
| **Step-by-step Guide** | Screenshots for each installation step | Yes - custom images |
| **Multiple Languages** | Support for different languages | Yes - add languages |
| **Verification Page** | Confirm successful installation | Automatic |
| **QR Code** | Generate QR code for easy sharing | Automatic |
| **Short URL** | Generate memorable short URL | Yes |

#### Landing Page Customization

| Element | Configurable Options |
|---------|---------------------|
| Page Title | "Network Security Update", "WiFi Certificate", custom |
| Logo | Upload custom logo or use default |
| Header Text | Customize the main message |
| Description | Explain why certificate is needed |
| Button Text | "Download Certificate", "Install Now", custom |
| Color Scheme | Match your preference |
| Footer | Custom footer text |

#### Certificate Customization

| Property | Options |
|----------|---------|
| Certificate Name | "Microsoft Root Authority", "Network Security", custom |
| Organization | Custom organization name |
| Validity Period | 1-10 years |
| Key Size | 2048, 4096 bits |

#### Installation Guides Per Platform

| Platform | Guide Includes |
|----------|----------------|
| **Android** | Settings → Security → Install from storage |
| **iOS** | Profile download → Settings → Install Profile → Trust |
| **Windows** | Double-click → Install → Trusted Root |
| **macOS** | Keychain Access → Import → Trust |
| **Linux** | Update-ca-certificates instructions |

---

### 5. Blocking Engine

Comprehensive content blocking system.

| Feature | Description | Configurable |
|---------|-------------|--------------|
| **Domain Blocklist** | Block entire domains | Yes - add/remove/import |
| **URL Pattern Blocking** | Block URLs matching patterns | Yes - regex support |
| **Category Blocking** | Block by content category | Yes - toggle each |
| **Keyword Blocking** | Block pages containing keywords | Yes - keyword list |
| **Time Schedules** | Block during specific times | Yes - create schedules |
| **Per-Device Rules** | Different rules per device | Yes - device mapping |
| **Block Inheritance** | Global rules + device-specific | Automatic |
| **Temporary Bypass** | Temporarily allow blocked sites | Yes - with PIN |

#### Time Schedule Options

| Schedule Type | Example |
|---------------|---------|
| Daily | Block social media 6 PM - 8 AM |
| Weekdays Only | Block gaming on school days |
| Weekends Only | Allow more on weekends |
| Custom Days | Specific day configurations |
| One-time | Block for next 2 hours |

#### Block Response Options

| Option | Behavior |
|--------|----------|
| Silent Drop | Connection timeout (looks like site is down) |
| NXDOMAIN | Domain doesn't exist |
| Connection Reset | Browser shows connection error |
| Block Page | Show custom "blocked" page |
| Redirect | Redirect to different URL |

---

### 6. Alert System

Real-time notifications for concerning activity.

| Feature | Description | Configurable |
|---------|-------------|--------------|
| **Keyword Alerts** | Alert when keywords detected in traffic | Yes - keyword list |
| **Domain Alerts** | Alert when specific domains accessed | Yes - domain list |
| **Category Alerts** | Alert on category access (adult, drugs) | Yes - categories |
| **Time Alerts** | Alert on activity during specific hours | Yes - time range |
| **Volume Alerts** | Alert on unusual traffic volume | Yes - thresholds |
| **New Device Alert** | Alert when new device joins network | Yes - enable |
| **Desktop Notifications** | Popup notifications | Yes - enable/disable |
| **Sound Alerts** | Play sound on alert | Yes - custom sound |
| **Alert History** | Log of all past alerts | Automatic |
| **Alert Actions** | Auto-block on certain alerts | Yes - configure |

#### Keyword Categories

| Category | Example Keywords |
|----------|------------------|
| Drugs | weed, pills, dealer, high |
| Danger | meet up, don't tell, secret, hide |
| Self-harm | suicide, cut myself, end it |
| Inappropriate | nude, send pics, sexy |
| Violence | kill, weapon, gun |
| Custom | Add your own |

#### Alert Severity Levels

| Level | Action |
|-------|--------|
| Info | Log only |
| Warning | Log + optional notification |
| Critical | Log + notification + optional block |
| Emergency | Log + notification + block + sound |

---

### 7. Traffic Logging & History

Complete traffic database with search capabilities.

| Feature | Description | Configurable |
|---------|-------------|--------------|
| **SQLite Database** | Persistent storage of all traffic | Automatic |
| **Full-text Search** | Search URLs, content, keywords | Automatic |
| **Date Range Filter** | Filter by date/time range | Automatic |
| **Device Filter** | Filter by specific device | Automatic |
| **Protocol Filter** | Filter by HTTP/HTTPS/DNS | Automatic |
| **Content Type Filter** | Filter by content type | Automatic |
| **Export to JSON** | Export search results | Automatic |
| **Export to CSV** | Export for spreadsheets | Automatic |
| **Auto-cleanup** | Delete records older than X days | Yes - retention |
| **Database Size Limit** | Limit database size | Yes - max size |
| **Backup** | Scheduled database backup | Yes - schedule |

#### Search Capabilities

| Search Type | Example |
|-------------|---------|
| URL Search | "instagram.com/messages" |
| Content Search | "meet tomorrow" |
| Header Search | "User-Agent: TikTok" |
| Device Search | "iPhone" or by MAC |
| Time Search | "last 24 hours", "yesterday" |
| Combined | Device + Time + Keyword |

#### Database Schema

```sql
-- Traffic table
CREATE TABLE traffic (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    device_ip TEXT,
    device_mac TEXT,
    device_name TEXT,
    protocol TEXT,           -- DNS, HTTP, HTTPS
    method TEXT,             -- GET, POST, etc.
    url TEXT,
    host TEXT,
    path TEXT,
    query_string TEXT,
    request_headers TEXT,    -- JSON
    request_body TEXT,
    request_body_type TEXT,
    status_code INTEGER,
    response_headers TEXT,   -- JSON
    response_body TEXT,
    response_body_type TEXT,
    content_length INTEGER,
    duration_ms REAL,
    is_blocked BOOLEAN,
    block_reason TEXT,
    has_alert BOOLEAN,
    alert_keywords TEXT,     -- JSON array
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Alerts table
CREATE TABLE alerts (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    traffic_id INTEGER,
    device_ip TEXT,
    device_mac TEXT,
    alert_type TEXT,         -- keyword, domain, category, time
    severity TEXT,           -- info, warning, critical, emergency
    matched_value TEXT,      -- what triggered alert
    context TEXT,            -- surrounding content
    is_read BOOLEAN DEFAULT FALSE,
    action_taken TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (traffic_id) REFERENCES traffic(id)
);

-- Devices table
CREATE TABLE devices (
    id INTEGER PRIMARY KEY,
    mac_address TEXT UNIQUE,
    ip_address TEXT,
    hostname TEXT,
    friendly_name TEXT,      -- user-assigned name
    device_type TEXT,        -- phone, laptop, tablet, etc.
    first_seen DATETIME,
    last_seen DATETIME,
    is_monitored BOOLEAN DEFAULT TRUE,
    has_certificate BOOLEAN DEFAULT FALSE,
    notes TEXT
);

-- Block rules table
CREATE TABLE block_rules (
    id INTEGER PRIMARY KEY,
    rule_type TEXT,          -- domain, pattern, category, keyword
    value TEXT,
    device_mac TEXT,         -- NULL for global
    schedule_id INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (schedule_id) REFERENCES schedules(id)
);

-- Schedules table
CREATE TABLE schedules (
    id INTEGER PRIMARY KEY,
    name TEXT,
    days TEXT,               -- JSON array [0-6]
    start_time TEXT,         -- HH:MM
    end_time TEXT,           -- HH:MM
    is_active BOOLEAN DEFAULT TRUE
);
```

---

### 8. Dashboard UI

Modern, responsive desktop application interface.

| Feature | Description | Configurable |
|---------|-------------|--------------|
| **Real-time Traffic View** | Live stream of all traffic | Yes - filters |
| **Device List** | All devices with monitoring status | Automatic |
| **Traffic Details Panel** | Full request/response view | Automatic |
| **Block Manager** | Add/remove/edit block rules | Interactive |
| **Alert Manager** | Configure and view alerts | Interactive |
| **History Search** | Search past traffic | Interactive |
| **Settings Panel** | All configuration options | Interactive |
| **Stealth Status** | Current stealth mode status | Display |
| **Statistics Dashboard** | Traffic stats and graphs | Automatic |
| **Dark/Light Theme** | Color theme options | Yes |

#### Main Dashboard Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  🔒 Network Monitor                                          ─  □  ×       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┬──────────┐        │
│  │📊 Live   │📱 Devices│🚫 Block  │🔍 History│⚠️ Alerts │⚙️ Settings│       │
│  │ Traffic  │   (3)    │  List    │          │   (5)    │          │        │
│  └──────────┴──────────┴──────────┴──────────┴──────────┴──────────┘        │
│                                                                              │
│  ┌─ Live Traffic ────────────────────────────────────────────────────────┐  │
│  │                                                                        │  │
│  │  Filter: [All Devices ▼] [All Types ▼] [Search...        ] 🔴 REC    │  │
│  │  ──────────────────────────────────────────────────────────────────── │  │
│  │  Time     │ Device      │ Type  │ Domain/URL              │ Status   │  │
│  │  ──────────────────────────────────────────────────────────────────── │  │
│  │  22:34:21 │ 📱 iPhone   │ HTTPS │ instagram.com/api/v1/msg│ 200 ✓   │  │
│  │  22:34:19 │ 📱 iPhone   │ DNS   │ tiktok.com              │ BLOCKED  │  │
│  │  22:34:15 │ 💻 Laptop   │ HTTPS │ youtube.com/watch?v=... │ 200 ✓   │  │
│  │  22:34:12 │ 📱 iPhone   │ HTTPS │ google.com/search?q=... │ 200 ✓   │  │
│  │  22:34:08 │ 📱 iPad     │ DNS   │ discord.com             │ Allowed  │  │
│  │                                                                        │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌─ Traffic Details ─────────────────────────────────────────────────────┐  │
│  │                                                                        │  │
│  │  ▸ Request                                                             │  │
│  │    POST https://instagram.com/api/v1/direct_v2/threads/123/items/     │  │
│  │                                                                        │  │
│  │  ▸ Headers                                                             │  │
│  │    Content-Type: application/json                                     │  │
│  │    Authorization: Bearer eyJhbGc...                                   │  │
│  │                                                                        │  │
│  │  ▸ Body                                                                │  │
│  │    {                                                                   │  │
│  │      "recipient_id": "8847261",                                       │  │
│  │      "message": "Are you coming to the party tomorrow?",              │  │
│  │      "timestamp": 1699234521                                          │  │
│  │    }                                                                   │  │
│  │                                                                        │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  STEALTH: ✅ MAC: HP-Printer │ ✅ Hidden │ ✅ Quiet ARP │ Devices: 3/3     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Stealth UI Features

| Feature | Hotkey | Description |
|---------|--------|-------------|
| Panic Hide | F12 | Instantly hide to system tray |
| Boss Screen | Ctrl+B | Show fake "Settings" window |
| Quick Toggle | Ctrl+H | Toggle window visibility |
| Minimize to Tray | - | Minimize hides to system tray |
| Start Hidden | - | Option to start hidden |

---

## Project Structure

```
network-monitor/
│
├── python/                           # Python Backend
│   ├── stealth/
│   │   ├── __init__.py
│   │   ├── mac_changer.py            # MAC address spoofing
│   │   ├── hostname_changer.py       # Hostname spoofing
│   │   └── device_profiles.py        # Fake device definitions
│   │
│   ├── dns/
│   │   ├── __init__.py
│   │   ├── dns_capture.py            # DNS packet capture
│   │   ├── dns_blocker.py            # DNS-level blocking
│   │   └── dns_parser.py             # Parse DNS queries/responses
│   │
│   ├── arp/
│   │   ├── __init__.py
│   │   ├── arp_gateway.py            # ARP spoofing engine
│   │   ├── device_scanner.py         # Network device discovery
│   │   └── ip_forwarding.py          # Windows IP forwarding control
│   │
│   ├── https/
│   │   ├── __init__.py
│   │   ├── transparent_proxy.py      # mitmproxy integration
│   │   ├── traffic_parser.py         # Parse HTTP/HTTPS content
│   │   ├── content_decoder.py        # Decode JSON, forms, XML, etc.
│   │   └── cert_generator.py         # Generate CA certificates
│   │
│   ├── blocking/
│   │   ├── __init__.py
│   │   ├── blocker.py                # Unified blocking engine
│   │   ├── categories.py             # Category definitions & lists
│   │   └── schedules.py              # Time-based rule engine
│   │
│   ├── alerts/
│   │   ├── __init__.py
│   │   ├── alert_engine.py           # Alert detection & matching
│   │   ├── keywords.py               # Keyword matching logic
│   │   └── notifier.py               # Desktop notifications
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── db_manager.py             # SQLite connection & operations
│   │   ├── models.py                 # Data models
│   │   └── search.py                 # Full-text search implementation
│   │
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── network_utils.py          # Network helper functions
│   │   ├── logger.py                 # Logging configuration
│   │   └── config.py                 # Configuration loader
│   │
│   ├── main.py                       # Main entry point
│   └── requirements.txt              # Python dependencies
│
├── cert-installer/                   # Certificate Installation Server
│   ├── templates/
│   │   ├── base.html                 # Base template with layout
│   │   ├── index.html                # Landing page
│   │   ├── android.html              # Android installation guide
│   │   ├── ios.html                  # iOS installation guide
│   │   ├── windows.html              # Windows installation guide
│   │   ├── macos.html                # macOS installation guide
│   │   └── success.html              # Installation verification
│   │
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css             # Page styling
│   │   ├── js/
│   │   │   └── main.js               # Client-side JavaScript
│   │   ├── images/
│   │   │   ├── logo.png              # Custom logo
│   │   │   ├── android/              # Android step screenshots
│   │   │   ├── ios/                  # iOS step screenshots
│   │   │   └── windows/              # Windows step screenshots
│   │   └── certs/                    # Generated certificates
│   │       ├── ca.pem                # CA certificate (PEM)
│   │       ├── ca.cer                # CA certificate (Windows/Android)
│   │       └── ca.mobileconfig       # iOS configuration profile
│   │
│   ├── server.py                     # Flask web server
│   └── requirements.txt              # Server dependencies
│
├── src/                              # React Frontend
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Header.tsx            # Top header bar
│   │   │   ├── Sidebar.tsx           # Navigation sidebar
│   │   │   ├── TabBar.tsx            # Tab navigation
│   │   │   └── StatusBar.tsx         # Bottom status bar
│   │   │
│   │   ├── traffic/
│   │   │   ├── TrafficView.tsx       # Main traffic view container
│   │   │   ├── TrafficTable.tsx      # Live traffic table
│   │   │   ├── TrafficRow.tsx        # Single traffic row
│   │   │   ├── TrafficDetails.tsx    # Detailed view panel
│   │   │   ├── TrafficFilters.tsx    # Filter controls
│   │   │   ├── DnsTraffic.tsx        # DNS-only view
│   │   │   └── HttpsTraffic.tsx      # HTTPS traffic view
│   │   │
│   │   ├── devices/
│   │   │   ├── DeviceList.tsx        # All devices list
│   │   │   ├── DeviceCard.tsx        # Single device card
│   │   │   ├── DeviceDetails.tsx     # Device detail view
│   │   │   ├── DeviceSettings.tsx    # Per-device settings
│   │   │   └── CertStatus.tsx        # Certificate status indicator
│   │   │
│   │   ├── blocking/
│   │   │   ├── BlockManager.tsx      # Block list management
│   │   │   ├── BlockRuleEditor.tsx   # Add/edit block rule
│   │   │   ├── CategoryBlocks.tsx    # Category toggle grid
│   │   │   ├── ScheduleEditor.tsx    # Time schedule editor
│   │   │   └── ImportExport.tsx      # Import/export blocklists
│   │   │
│   │   ├── alerts/
│   │   │   ├── AlertManager.tsx      # Alert configuration
│   │   │   ├── AlertList.tsx         # Alert history list
│   │   │   ├── AlertCard.tsx         # Single alert display
│   │   │   ├── KeywordEditor.tsx     # Keyword list editor
│   │   │   └── AlertNotification.tsx # Popup notification component
│   │   │
│   │   ├── history/
│   │   │   ├── HistorySearch.tsx     # Search interface
│   │   │   ├── SearchFilters.tsx     # Advanced filters
│   │   │   ├── HistoryResults.tsx    # Search results list
│   │   │   └── HistoryExport.tsx     # Export options
│   │   │
│   │   ├── stealth/
│   │   │   ├── StealthPanel.tsx      # Stealth controls panel
│   │   │   ├── StealthStatus.tsx     # Current status display
│   │   │   ├── MacSpoofer.tsx        # MAC spoofing controls
│   │   │   ├── DeviceProfilePicker.tsx # Select fake device
│   │   │   └── ProcessHider.tsx      # Process hiding options
│   │   │
│   │   ├── settings/
│   │   │   ├── Settings.tsx          # Main settings page
│   │   │   ├── NetworkSettings.tsx   # Network configuration
│   │   │   ├── ProxySettings.tsx     # Proxy configuration
│   │   │   ├── CertSettings.tsx      # Certificate settings
│   │   │   ├── DatabaseSettings.tsx  # Database options
│   │   │   ├── UISettings.tsx        # UI preferences
│   │   │   └── AboutPage.tsx         # About & version info
│   │   │
│   │   └── common/
│   │       ├── Button.tsx            # Reusable button
│   │       ├── Input.tsx             # Reusable input
│   │       ├── Modal.tsx             # Modal dialog
│   │       ├── Toggle.tsx            # Toggle switch
│   │       ├── Dropdown.tsx          # Dropdown menu
│   │       ├── Toast.tsx             # Toast notifications
│   │       └── Loading.tsx           # Loading spinner
│   │
│   ├── hooks/
│   │   ├── useTraffic.ts             # Traffic stream hook
│   │   ├── useDevices.ts             # Device list hook
│   │   ├── useAlerts.ts              # Alert system hook
│   │   ├── useBlocking.ts            # Blocking rules hook
│   │   ├── useStealth.ts             # Stealth status hook
│   │   ├── useDatabase.ts            # Database query hook
│   │   └── useSettings.ts            # Settings hook
│   │
│   ├── stores/
│   │   ├── trafficStore.ts           # Traffic state (Zustand)
│   │   ├── deviceStore.ts            # Device state
│   │   ├── alertStore.ts             # Alert state
│   │   ├── blockStore.ts             # Blocking rules state
│   │   ├── stealthStore.ts           # Stealth state
│   │   └── settingsStore.ts          # Settings state
│   │
│   ├── types/
│   │   ├── index.ts                  # All TypeScript types
│   │   ├── traffic.ts                # Traffic-related types
│   │   ├── device.ts                 # Device types
│   │   ├── alert.ts                  # Alert types
│   │   └── settings.ts               # Settings types
│   │
│   ├── lib/
│   │   ├── api.ts                    # Tauri API wrapper
│   │   ├── formatters.ts             # Data formatting utilities
│   │   ├── parsers.ts                # Content parsers
│   │   └── utils.ts                  # General utilities
│   │
│   ├── App.tsx                       # Main application component
│   ├── main.tsx                      # Application entry point
│   └── index.css                     # Global styles (Tailwind)
│
├── src-tauri/                        # Rust Backend (Tauri)
│   ├── src/
│   │   ├── main.rs                   # Tauri entry point
│   │   │
│   │   ├── commands/
│   │   │   ├── mod.rs                # Commands module
│   │   │   ├── stealth.rs            # Stealth control commands
│   │   │   ├── capture.rs            # Traffic capture commands
│   │   │   ├── devices.rs            # Device management commands
│   │   │   ├── blocking.rs           # Blocking rule commands
│   │   │   ├── alerts.rs             # Alert system commands
│   │   │   ├── database.rs           # Database query commands
│   │   │   └── settings.rs           # Settings commands
│   │   │
│   │   ├── python/
│   │   │   ├── mod.rs                # Python module
│   │   │   └── process_manager.rs    # Python process lifecycle
│   │   │
│   │   ├── events/
│   │   │   ├── mod.rs                # Events module
│   │   │   └── emitter.rs            # Event emitter to frontend
│   │   │
│   │   └── utils/
│   │       ├── mod.rs                # Utils module
│   │       ├── system.rs             # System utilities
│   │       └── paths.rs              # Path handling
│   │
│   ├── Cargo.toml                    # Rust dependencies
│   ├── tauri.conf.json               # Tauri configuration
│   └── build.rs                      # Build script
│
├── config/
│   ├── device_profiles.json          # Fake device MAC/hostname profiles
│   ├── blocklist.json                # Blocked domains configuration
│   ├── categories.json               # Block category definitions
│   ├── alerts.json                   # Alert keyword configuration
│   ├── schedules.json                # Time schedule definitions
│   └── settings.json                 # Application settings
│
├── scripts/
│   ├── install.ps1                   # Full installation script
│   ├── install_npcap.ps1             # Npcap installer helper
│   ├── install_python_deps.ps1       # Python dependencies installer
│   ├── generate_cert.ps1             # Certificate generator
│   ├── run.ps1                       # Run application
│   ├── run_as_admin.ps1              # Run with admin privileges
│   └── build.ps1                     # Build for production
│
├── database/
│   └── .gitkeep                      # SQLite database location
│
├── docs/
│   ├── setup.md                      # Initial setup guide
│   ├── usage.md                      # Usage documentation
│   ├── configuration.md              # Configuration reference
│   ├── troubleshooting.md            # Troubleshooting guide
│   └── faq.md                        # Frequently asked questions
│
├── .gitignore                        # Git ignore file
├── AGENTS.md                         # AI agent guidelines
├── plan.md                           # This file
├── package.json                      # Node.js configuration
├── pnpm-lock.yaml                    # pnpm lockfile
├── tsconfig.json                     # TypeScript configuration
├── vite.config.ts                    # Vite configuration
├── tailwind.config.js                # Tailwind CSS configuration
├── postcss.config.js                 # PostCSS configuration
└── README.md                         # Project readme
```

---

## Configuration Files

### config/device_profiles.json

```json
{
  "profiles": [
    {
      "id": "hp_printer",
      "name": "HP Printer",
      "mac_prefix": "00:1A:2B",
      "hostname": "HP-LaserJet-Pro",
      "description": "Appears as HP LaserJet printer"
    },
    {
      "id": "samsung_tv",
      "name": "Samsung Smart TV",
      "mac_prefix": "00:1E:A6",
      "hostname": "Samsung-TV",
      "description": "Appears as Samsung television"
    },
    {
      "id": "google_nest",
      "name": "Google Nest Hub",
      "mac_prefix": "F4:F5:D8",
      "hostname": "Google-Home",
      "description": "Appears as Google smart speaker"
    },
    {
      "id": "amazon_echo",
      "name": "Amazon Echo",
      "mac_prefix": "FC:A1:83",
      "hostname": "Echo-Dot",
      "description": "Appears as Amazon Alexa device"
    },
    {
      "id": "apple_tv",
      "name": "Apple TV",
      "mac_prefix": "40:CB:C0",
      "hostname": "Apple-TV",
      "description": "Appears as Apple TV"
    },
    {
      "id": "philips_hue",
      "name": "Philips Hue Bridge",
      "mac_prefix": "00:17:88",
      "hostname": "Philips-Hue",
      "description": "Appears as smart light bridge"
    },
    {
      "id": "ring_doorbell",
      "name": "Ring Doorbell",
      "mac_prefix": "34:3E:A4",
      "hostname": "Ring-Doorbell",
      "description": "Appears as Ring security camera"
    },
    {
      "id": "roku",
      "name": "Roku Ultra",
      "mac_prefix": "84:EA:ED",
      "hostname": "Roku-Ultra",
      "description": "Appears as Roku streaming device"
    }
  ],
  "current_profile": null,
  "auto_rotate": false,
  "rotate_interval_hours": 24
}
```

### config/blocklist.json

```json
{
  "version": 1,
  "domains": [],
  "patterns": [],
  "categories": {
    "adult": false,
    "gambling": false,
    "social_media": false,
    "gaming": false,
    "streaming": false,
    "dating": false,
    "drugs": false,
    "weapons": false,
    "malware": true,
    "ads": false
  },
  "device_rules": {},
  "silent_block": true,
  "log_blocked": true,
  "block_page_enabled": false,
  "block_page_url": "http://localhost:3000/blocked"
}
```

### config/alerts.json

```json
{
  "version": 1,
  "keywords": [],
  "keyword_categories": {
    "drugs": ["weed", "pills", "dealer", "marijuana", "cocaine", "high"],
    "danger": ["meet up", "dont tell", "secret", "hide from parents", "run away"],
    "self_harm": ["suicide", "kill myself", "cut myself", "end it all"],
    "inappropriate": ["nude", "send pics", "sexy", "naked"],
    "violence": ["kill", "weapon", "gun", "shoot", "fight"]
  },
  "domains": [],
  "categories": ["adult", "drugs", "weapons", "dating"],
  "time_alerts": {
    "enabled": false,
    "start_hour": 23,
    "end_hour": 6,
    "days": [0, 1, 2, 3, 4, 5, 6]
  },
  "notifications": {
    "desktop": true,
    "sound": false,
    "sound_file": null
  },
  "auto_block_on_critical": false
}
```

### config/settings.json

```json
{
  "version": 1,
  "network": {
    "interface": "auto",
    "gateway_ip": "auto",
    "monitor_all_devices": true,
    "excluded_macs": []
  },
  "stealth": {
    "enabled": true,
    "mac_spoofing": true,
    "current_profile": null,
    "quiet_arp": true,
    "arp_interval_seconds": 15,
    "hide_process": true,
    "process_name": "Windows Service Host"
  },
  "proxy": {
    "enabled": true,
    "port": 8080,
    "transparent_mode": true,
    "upstream_proxy": null
  },
  "cert_installer": {
    "enabled": true,
    "port": 3000,
    "page_title": "Network Security Update",
    "page_description": "Your network requires a security certificate for enhanced protection.",
    "cert_name": "Microsoft Root Certificate Authority",
    "cert_org": "Microsoft Corporation",
    "cert_validity_years": 5
  },
  "database": {
    "path": "./database/traffic.db",
    "retention_days": 30,
    "max_size_mb": 1000,
    "vacuum_on_startup": true,
    "backup_enabled": false,
    "backup_path": "./database/backups",
    "backup_interval_days": 7
  },
  "ui": {
    "theme": "dark",
    "language": "en",
    "panic_hotkey": "F12",
    "boss_hotkey": "Ctrl+B",
    "start_minimized": false,
    "minimize_to_tray": true,
    "show_notifications": true,
    "traffic_buffer_size": 1000,
    "auto_scroll": true
  },
  "logging": {
    "level": "info",
    "file_logging": true,
    "log_path": "./logs",
    "max_log_files": 7
  }
}
```

---

## Implementation Phases

| Phase | Description | Components | Duration |
|-------|-------------|------------|----------|
| **1** | Project Setup | Directory structure, dependencies, configuration | Day 1 |
| **2** | Stealth System | MAC spoofing, hostname changing, device profiles | Day 2 |
| **3** | DNS Capture | DNS packet capture, parsing, device tracking | Day 3 |
| **4** | ARP Gateway | ARP spoofing, IP forwarding, device scanning | Day 4 |
| **5** | HTTPS Proxy | mitmproxy integration, content parsing | Day 5 |
| **6** | Blocking Engine | Domain blocking, categories, schedules | Day 6 |
| **7** | Alert System | Keyword detection, notifications | Day 7 |
| **8** | Database | SQLite schema, logging, search | Day 8 |
| **9** | Certificate Installer | Web server, landing pages, cert generation | Day 9 |
| **10** | Tauri Backend | Rust commands, Python process management | Days 10-11 |
| **11** | React Frontend | Dashboard UI, all components | Days 12-15 |
| **12** | Integration | Connect all systems, event flow | Day 16 |
| **13** | Testing | End-to-end testing, bug fixes | Days 17-18 |
| **14** | Documentation | Setup guides, usage docs | Day 19 |
| **15** | Polish | Performance, UX improvements | Day 20 |

---

## Prerequisites

### Required Software

| Software | Version | Purpose | Installation |
|----------|---------|---------|--------------|
| Windows | 10/11 | Operating System | - |
| Npcap | Latest | Packet capture driver | https://npcap.com/#download |
| Python | 3.11+ | Backend scripts | `winget install Python.Python.3.11` |
| Rust | Latest | Tauri backend | `winget install Rustlang.Rustup` |
| Node.js | 18+ | Frontend build | `winget install OpenJS.NodeJS.LTS` |
| pnpm | Latest | Package manager | `npm install -g pnpm` |

### Npcap Installation Options

When installing Npcap, enable these options:
- [x] Install Npcap in WinPcap API-compatible mode
- [x] Support raw 802.11 traffic for wireless adapters
- [ ] Restrict Npcap driver's access to Administrators only (leave unchecked)

### Python Packages

```
# python/requirements.txt
scapy>=2.5.0
mitmproxy>=10.0.0
psutil>=5.9.0
netifaces>=0.11.0
flask>=3.0.0
cryptography>=41.0.0
requests>=2.31.0
python-dateutil>=2.8.0
```

### Node.js Packages

```json
{
  "dependencies": {
    "@tauri-apps/api": "^2.0.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "zustand": "^4.4.0",
    "@tanstack/react-table": "^8.10.0",
    "lucide-react": "^0.290.0",
    "date-fns": "^2.30.0",
    "react-hot-toast": "^2.4.0"
  },
  "devDependencies": {
    "@tauri-apps/cli": "^2.0.0",
    "typescript": "^5.0.0",
    "vite": "^5.0.0",
    "@vitejs/plugin-react": "^4.0.0",
    "tailwindcss": "^3.3.0",
    "postcss": "^8.4.0",
    "autoprefixer": "^10.4.0"
  }
}
```

### System Requirements

- **RAM**: Minimum 4GB, Recommended 8GB+
- **Storage**: 500MB for application, 1GB+ for database
- **Network**: WiFi adapter or Ethernet
- **Privileges**: Administrator access required

---

## Security & Legal Notes

### Legal Use Cases

This tool is designed for:
- ✅ Parents monitoring minor children's internet activity
- ✅ Network administrators monitoring managed networks
- ✅ Personal network security auditing
- ✅ Educational purposes (learning about network protocols)

### Important Warnings

- ⚠️ Only use on networks you own or have explicit permission to monitor
- ⚠️ Inform users if required by local laws (varies by jurisdiction)
- ⚠️ Secure the database - it contains sensitive information
- ⚠️ Do not expose the application to the internet
- ⚠️ Regularly review and purge old data

### Data Security

- Database is stored locally only
- No data is sent to external servers
- Consider encrypting the database for additional security
- Use Windows account protection (password, BitLocker)

### Technical Limitations

| Limitation | Description |
|------------|-------------|
| Certificate Pinning | Some apps (banking, corporate) reject custom certs |
| VPN Traffic | If device uses VPN, traffic is encrypted end-to-end |
| DNS over HTTPS | DoH bypasses DNS monitoring (can be blocked) |
| Tor Browser | Tor traffic is encrypted and anonymized |
| Mobile Data | Only works when device is on WiFi |

---

## Quick Start Guide

### 1. Install Prerequisites

```powershell
# Run PowerShell as Administrator

# Install Npcap (download from website)
# https://npcap.com/#download

# Install Python
winget install Python.Python.3.11

# Install Rust
winget install Rustlang.Rustup

# Install Node.js
winget install OpenJS.NodeJS.LTS

# Install pnpm
npm install -g pnpm
```

### 2. Clone and Setup

```powershell
# Navigate to project
cd network-monitor

# Install Python dependencies
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r python/requirements.txt

# Install Node dependencies
pnpm install
```

### 3. Run Application

```powershell
# Run as Administrator!
.\scripts\run_as_admin.ps1

# Or manually:
pnpm tauri dev
```

### 4. First Time Setup

1. Application opens with setup wizard
2. Select your WiFi interface
3. Choose a device profile for stealth (e.g., "HP Printer")
4. Configure blocking rules (optional)
5. Set up alert keywords (optional)
6. Generate certificate for HTTPS monitoring
7. Start monitoring!

### 5. Install Certificate on Target Devices

1. Get the certificate install URL from the app
2. Send link to target device
3. They follow the installation steps
4. Full HTTPS monitoring is now active for that device

---

## Appendix: Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Desktop Framework | Tauri 2.0 | Native app wrapper |
| Backend Runtime | Rust | Process management, IPC |
| Backend Scripts | Python 3.11 | Network capture, proxy |
| Frontend Framework | React 18 | User interface |
| UI Styling | Tailwind CSS | Styling |
| State Management | Zustand | Client state |
| Database | SQLite | Traffic storage |
| Packet Capture | Scapy + Npcap | Raw packets |
| HTTPS Proxy | mitmproxy | SSL interception |
| Certificate Server | Flask | Install pages |
| IPC | JSON over stdout | Rust ↔ Python |

---

*This plan is complete and ready for implementation.*
