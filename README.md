# Network Monitor

A stealthy network monitoring desktop application for parental control purposes. Monitor all network traffic from devices on your WiFi network without requiring router access or device configuration.

## Features

- **Network-Wide Monitoring**: Capture traffic from ALL devices on your network (phones, tablets, laptops, smart TVs)
- **HTTPS Decryption**: View full HTTPS content using mitmproxy with certificate installation
- **Stealth Mode**: Disguise monitoring PC as a printer, TV, or other network device
- **Website Blocking**: Block categories (adult, social media, gaming) with time-based schedules
- **Keyword Alerts**: Get notified about concerning content (self-harm, predators, bullying, drugs)
- **Traffic Logging**: Full-text searchable database of all network activity
- **Modern UI**: Dark-themed desktop app built with Tauri + React

## How It Works

```
                    ┌─────────────────┐
                    │   Your Router   │
                    │   (Gateway)     │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
    ┌────┴────┐         ┌────┴────┐         ┌────┴────┐
    │ Phone   │         │ Laptop  │         │ Tablet  │
    │(Target) │         │(Target) │         │(Target) │
    └────┬────┘         └────┬────┘         └────┬────┘
         │                   │                   │
         └───────────────────┼───────────────────┘
                             │
                    ┌────────┴────────┐
                    │  Network Monitor │
                    │  (This PC)       │
                    │  - ARP Spoofing  │
                    │  - HTTPS Proxy   │
                    │  - DNS Capture   │
                    └─────────────────┘
```

The application uses **ARP spoofing** to position itself as the gateway, routing all network traffic through itself for inspection.

## Requirements

- **Windows 10/11** (Administrator privileges required)
- **Npcap** driver (for packet capture)
- **Python 3.9+** (for backend)
- **Node.js 18+** (for frontend)
- **Rust** (for Tauri)

## Installation

### Quick Install

Run PowerShell as Administrator:

```powershell
cd network-monitor
.\scripts\install.ps1
```

This will:
1. Install Npcap (if not present)
2. Create Python virtual environment
3. Install Python dependencies
4. Install Node.js dependencies
5. Build the application

### Manual Installation

1. **Install Npcap**
   - Download from https://npcap.com/
   - Install with WinPcap compatibility mode

2. **Setup Python**
   ```powershell
   python -m venv network_monitor_env
   .\network_monitor_env\Scripts\Activate.ps1
   pip install -r python/requirements.txt
   ```

3. **Setup Frontend**
   ```powershell
   pnpm install
   ```

4. **Build Application**
   ```powershell
   pnpm tauri build
   ```

## Usage

### Development Mode

```powershell
pnpm tauri dev
```

### Production Mode

```powershell
.\scripts\run.ps1
```

Or run the built executable in `src-tauri/target/release/`.

### Certificate Installation

For HTTPS decryption, target devices need to trust the CA certificate:

1. Start the certificate server from the app's Settings page
2. On target device, navigate to `http://[YOUR_IP]:8888`
3. Follow the platform-specific installation guide
4. For iOS: Also enable full trust in Settings > General > About > Certificate Trust Settings

## Project Structure

```
network-monitor/
├── src/                    # React Frontend (TypeScript)
│   ├── components/         # UI components
│   ├── pages/              # Page components
│   ├── hooks/              # React hooks
│   ├── stores/             # Zustand state management
│   ├── lib/                # Utilities and API
│   └── types/              # TypeScript definitions
├── src-tauri/              # Rust Backend (Tauri)
│   └── src/
├── python/                 # Python Backend
│   ├── arp/                # ARP spoofing
│   ├── dns/                # DNS capture
│   ├── https/              # HTTPS proxy
│   ├── stealth/            # Device disguise
│   ├── blocking/           # Content blocking
│   ├── alerts/             # Keyword alerts
│   └── database/           # SQLite storage
├── cert-installer/         # Certificate installation server
├── config/                 # Configuration files
└── scripts/                # PowerShell scripts
```

## Configuration

Configuration files are in the `config/` directory:

- `settings.json` - Main application settings
- `device_profiles.json` - Stealth device profiles
- `blocklist.json` - Blocking rules
- `keywords.json` - Alert keywords by category
- `schedules.json` - Time-based blocking schedules

## Security Considerations

- This application requires Administrator privileges
- Generated certificates should be protected
- Database contains sensitive browsing data
- Use responsibly and in accordance with applicable laws

## Tech Stack

| Component | Technology |
|-----------|------------|
| Desktop Framework | Tauri 2.0 (Rust + WebView) |
| Frontend | React 18 + TypeScript + Vite + Tailwind |
| Packet Capture | Scapy + Npcap |
| HTTPS Proxy | mitmproxy |
| Certificate Server | Flask |
| Database | SQLite |
| State Management | Zustand |
| Charts | Recharts |

## Development

### Commands

```powershell
# Frontend development
pnpm dev

# Tauri development (frontend + backend)
pnpm tauri dev

# Type checking
pnpm tsc --noEmit

# Linting
pnpm lint

# Python tests
pytest python/

# Rust tests
cd src-tauri && cargo test
```

### Building for Production

```powershell
pnpm tauri build
```

The installer will be created in `src-tauri/target/release/bundle/`.

## Troubleshooting

### "Npcap not found"
Install Npcap from https://npcap.com/ with WinPcap API compatibility mode.

### "Access Denied" errors
Run as Administrator. Network capture requires elevated privileges.

### Devices not appearing
- Ensure the monitoring PC is on the same subnet
- Check that Windows Firewall isn't blocking traffic
- Verify ARP spoofing is active in the app

### HTTPS traffic not visible
- Ensure the CA certificate is installed on the target device
- For iOS, enable full trust in Certificate Trust Settings
- Check that mitmproxy is running (visible in app status)

## Legal Disclaimer

This software is intended for legitimate parental control purposes on networks you own or have explicit permission to monitor. Unauthorized network interception may be illegal in your jurisdiction. Use responsibly.

## License

MIT License - See LICENSE file for details.
