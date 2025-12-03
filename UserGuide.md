# WireGuard VPN Setup and Management Guide

## What is a VPN?

### General Overview
A VPN (Virtual Private Network) creates an encrypted tunnel between your device and a server, routing your internet traffic through that server. WireGuard is a modern, fast, and secure VPN protocol that's simpler to configure than older alternatives like OpenVPN.

### Why Would I Want One?
- **Privacy on public WiFi**: Protect your data on hotel, coffee shop, or airport networks
- **Encrypt your traffic**: Prevent ISPs and network administrators from seeing your browsing
- **Secure remote access**: Safely access resources on your server's network
- **Control your exit point**: Your traffic appears to come from your server's location

### What Does It Do?
When connected to your WireGuard VPN:
- All internet traffic flows through an encrypted tunnel to your server
- Your server forwards that traffic to its destination
- Responses come back through the same encrypted tunnel
- To outside observers, you appear to be browsing from your server's IP address

### How Does It Work?
WireGuard uses UDP packets to create an encrypted tunnel:
1. Your device wraps regular traffic (IP packets) in encrypted WireGuard packets
2. These packets are sent via UDP to your server (default port 51820)
3. The server unwraps (decrypts) them and forwards to the internet
4. Responses return through the same encrypted tunnel
5. Uses modern cryptography with public/private key pairs (like SSH)

## Prerequisites

### Server Requirements
- A VPS or cloud server (tested with Hetzner)
- Ubuntu 24.04 (or similar recent version)
- Root or sudo access
- Public IP address
- At least 1GB RAM (minimal requirements)

### Required Knowledge
- Basic SSH usage
- Basic Linux command line (cd, ls, cat, nano/vi)
- Understanding of IP addresses and ports

### Tools Needed
- SSH client on your local machine
- Text editor (nano, vi, or similar)
- WireGuard client apps for your devices

## Roadmap of What Needs to Be Done

### Server Side
1. Install WireGuard package
2. Generate server key pair
3. Create server configuration
4. Configure IP forwarding and firewall
5. Start and enable WireGuard service

### Client Side
1. Generate key pair for each client
2. Create configuration file for each client
3. Add client to server configuration
4. Transfer config to client device
5. Install WireGuard app and import config

### Process Overview
The setup follows this pattern: server setup once, then repeat client setup for each device you want to connect.

## Server Setup

### Installation

SSH into your server and install WireGuard:
sudo apt update sudo apt install wireguard


### Key Generation

Generate the server's private and public keys:
Generate private key
```
wg genkey | sudo tee /etc/wireguard/private.key
```
Generate public key from private key
```
sudo cat /etc/wireguard/private.key | wg pubkey | sudo tee /etc/wireguard/public.key
```

Keep these keys secure. You'll need them in the next step.

### Configuration

First, identify your server's network interface:
```
ip route | grep default
```

Look for the interface name after "dev" (usually `eth0` or `ens3`).

Create the server configuration file:
```
sudo nano /etc/wireguard/wg0.conf
```

Add this configuration (replace `<server-private-key>` with the content of `/etc/wireguard/private.key` and adjust `eth0` if your interface is different):
```
[Interface]
Address = 10.0.0.1/24 
ListenPort = 51820 
PrivateKey = <private-key>
PostUp = iptables -A FORWARD -i %i -j ACCEPT; iptables -A FORWARD -o %i -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE 
PostDown = iptables -D FORWARD -i %i -j ACCEPT; iptables -D FORWARD -o %i -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE
```

**Configuration explained:**
- `Address`: Server's VPN IP (10.0.0.1) and subnet (10.0.0.0/24 gives 254 possible client IPs)
- `ListenPort`: UDP port for VPN connections (51820 is default, or use 443 if behind restrictive firewalls)
- `PrivateKey`: Server's private key
- `PostUp/PostDown`: iptables rules to enable NAT and forwarding when VPN starts/stops
- `%i`: Automatically replaced with interface name (wg0)

### Firewall Configuration

Enable IP forwarding permanently:
```
echo "net.ipv4.ip_forward=1" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

If using UFW, allow WireGuard traffic:
```
sudo ufw allow 51820/udp
```

**Note**: If your provider has a separate cloud firewall (like Hetzner Cloud Firewall), ensure UDP port 51820 is allowed there as well.

### Starting the Service

Start WireGuard and enable it to start on boot:
```
sudo systemctl start wg-quick@wg0 sudo systemctl enable wg-quick@wg0
```

Verify it's running:
```
sudo wg show
```

You should see your interface with public key and listening port.

Verify the port is listening:
```
sudo ss -ulnp | grep 51820
```

## Client Setup

### Overview

For each device you want to connect, you'll need to:
1. Generate a unique key pair
2. Create a configuration file
3. Add the client to the server
4. Transfer the config to the device
5. Import it into the WireGuard app

### Generating Client Keys

On your server, create a directory for client configs:
```
mkdir -p ~/wireguard-clients cd ~/wireguard-clients
```

For each client, generate keys (replace `client1` with a descriptive name):
```
wg genkey | tee client1-private.key | wg pubkey > client1-public.key
```

This creates:
- `client1-private.key`: Client's private key (keep secret)
- `client1-public.key`: Client's public key (will be added to server)

### Creating Client Configuration

Create a config file for the client: Pick an editor, `nano`, `vi`, etc.
```
nano client1.conf
vi client1.conf
```


Use this template (replace placeholders):
```
[Interface] 
PrivateKey = <client-private-key>
Address = 10.0.0.2/32 
DNS = 1.1.1.1

[Peer] 
PublicKey = <server-public-key>
Endpoint = <server-public-ip>:51820 
AllowedIPs = 0.0.0.0/0 
PersistentKeepalive = 25
```

**Fill in:**
- `<client-private-key>`: Content of `client1-private.key`
- `<server-public-key>`: Content of `/etc/wireguard/public.key`
- `<server-public-ip>`: Your server's public IP address

**Configuration explained:**
- `PrivateKey`: Client's private key
- `Address`: Client's VPN IP (increment for each client: .2, .3, .4, etc.)
- `DNS`: DNS server to use (1.1.1.1 is Cloudflare, or use 8.8.8.8 for Google)
- `PublicKey`: Server's public key
- `Endpoint`: Server's public IP and port
- `AllowedIPs = 0.0.0.0/0`: Route ALL traffic through VPN
- `PersistentKeepalive`: Keep connection alive through NAT (25 seconds)

**Important**: Each client must have a unique VPN IP address (10.0.0.2, 10.0.0.3, etc.) and its own key pair.

### Adding Client to Server

Edit the server configuration:
```
sudo vi /etc/wireguard/wg0.conf
```

Add a `[Peer]` section for this client (replace `<client-public-key>` with content of `client1-public.key`):
```
[Peer] 
PublicKey = <client-public-key>
AllowedIPs = 10.0.0.2/32
```


**Note**: The `AllowedIPs` here specifies which VPN IP this client is allowed to use (must match the client's config).

Restart WireGuard to apply changes:
```
sudo systemctl restart wg-quick@wg0
```

Verify the peer is registered:
```
sudo wg show
```

You should now see a `peer:` section with the client's public key.

### Installing Client Apps

#### iOS/iPadOS
- Install "WireGuard" from the App Store (official app, free)

#### Android
- Install "WireGuard" from Google Play Store (official app, free)

#### macOS
- Install "WireGuard" from the Mac App Store (official app, free)

#### Windows
- Download from [wireguard.com/install](https://www.wireguard.com/install/)

#### Linux
- Install via package manager: `sudo apt install wireguard` (Ubuntu/Debian)
- Or use distribution-specific instructions

#### ChromeOS
- Not officially supported, but Android app may work on compatible devices

### Importing Configurations

#### Method 1: File Transfer (Most Reliable)

1. **Transfer the `.conf` file to your device:**
   - Email it to yourself as an attachment
   - Use a file sharing service
   - Use SCP/SFTP to copy directly to a computer

2. **Import into WireGuard app:**
   - **iOS/iPadOS**: Tap "+", choose "Create from file or archive", select the file
   - **macOS**: Click "+", choose "Import tunnel(s) from file", select the file
   - **Android**: Tap "+", choose "Create from file or archive"
   - **Windows**: Click "Import tunnel(s) from file"
   - **Linux**: Copy to `/etc/wireguard/` and use `wg-quick up client1`

**Important for iOS/macOS file transfer:**
- Use TextEdit in Plain Text mode (Format → Make Plain Text)
- Don't modify the file contents
- Preserve exact formatting and keys

#### Method 2: QR Code (Mobile Devices)

Generate a QR code on the server:
```
sudo apt install qrencode qrencode -t ansiutf8 < ~/wireguard-clients/client1.conf
```

Scan with WireGuard app:
- Tap "+" → "Create from QR code"
- Scan the displayed QR code

**Note**: This method sometimes hangs. If it does, use file transfer instead.

#### Method 3: Manual Entry

In the WireGuard app:
1. Choose "Create from scratch"
2. Name the tunnel
3. Manually enter each field from your config file
4. Paste keys carefully (one wrong character breaks it)

### Activating the VPN

In the WireGuard app:
1. Find your tunnel in the list
2. Toggle it ON
3. Approve the VPN configuration (first time only)
4. Status should show "Active" with data transfer

## Testing

### Verify Connection on Server

Check if the client connected:
sudo wg show


Look for:
- `latest handshake`: Should show recent timestamp (within last 2 minutes)
- `transfer`: Should show data sent/received after using the VPN

### Verify Your IP Address

On the client device with VPN active:

1. Open a web browser
2. Visit [whatismyip.com](https://www.whatismyip.com) or [ifconfig.me](https://ifconfig.me)
3. Should display your **server's** IP address, not your actual location

### Verify Traffic Routing

All traffic should go through the VPN:
- Web browsing
- Email (SMTP/POP/IMAP)
- Apps
- DNS queries

The `AllowedIPs = 0.0.0.0/0` setting routes everything through the tunnel.

### Test From Different Networks

Try connecting from:
- Home WiFi
- Mobile data
- Public WiFi (coffee shop, hotel)
- Different locations

This ensures the VPN works across various network conditions.

## Management

### Adding New Clients

Repeat the client setup process for each device:

1. Generate new key pair:
```cd ~/wireguard-clients wg genkey | tee client2-private.key | wg pubkey > client2-public.key```


3. Create config file with unique IP (e.g., 10.0.0.3):
nano client2.conf


4. Add peer to server config:
```sudo nano /etc/wireguard/wg0.conf```

Add [Peer] section with client2's public key and IP

4. Restart server:
```sudo systemctl restart wg-quick@wg0```


5. Transfer config to device and import

**Tip**: Keep a list of which IPs are assigned to which devices.

### Viewing Connected Clients

See all peers and their status:
```
sudo wg show
```


Shows for each peer:
- Public key
- Last handshake time (how recently they connected)
- Data transfer amounts
- Endpoint (their current IP and port)

### Revoking Client Access

To remove a client's access:

1. Edit server config:
```sudo vi /etc/wireguard/wg0.conf```


2. Delete (or comment out) that client's `[Peer]` section

3. Restart WireGuard:
```sudo systemctl restart wg-quick@wg0```


The client can no longer connect, even with their config file.

**Note**: The client's config file still exists, but won't work. Delete it from the device for security.

### Optional: Web Interfaces

For easier management without SSH, consider installing a web interface:

**wg-easy** (popular option):
- Provides web UI for managing clients
- Generate QR codes easily
- View connection status
- Add/remove clients through browser

Installation requires Docker. See [wg-easy documentation](https://github.com/wg-easy/wg-easy) for setup instructions.

## Troubleshooting

### Client Can't Connect (No Handshake)

**Check server is running:**
```
sudo systemctl status wg-quick@wg0 
sudo wg show
```


**Verify port is listening:**
```
sudo ss -ulnp | grep 51820
```


**Check firewall allows UDP 51820:**
```
sudo ufw status
```

**Verify client config:**
- Correct server IP and port in `Endpoint`
- Correct server public key in `PublicKey`
- Client private key matches a registered peer

**Check provider firewall:**
- Hetzner Cloud Firewall, AWS Security Groups, etc.
- Must allow UDP port 51820 inbound

### Connection Works But No Internet

**Verify IP forwarding is enabled:**
```
sysctl net.ipv4.ip_forward
```
Should show: net.ipv4.ip_forward = 1

**Check iptables rules are active:**
```
sudo iptables -t nat -L POSTROUTING -v
```

Should show MASQUERADE rule for your interface.

**Verify network interface name:**
- In server config, `PostUp/PostDown` rules reference correct interface (eth0, ens3, etc.)
- Check with: `ip route | grep default`

### Wrong Keys in Client Config

**Symptom**: Interface public key in app doesn't match expected

**Cause**: Wrong private key in config file

**Solution**: 
1. Verify which private key you're using
2. Check what public key it generates:
```
echo "PRIVATE_KEY_HERE" | wg pubkey
```

3. Ensure client config has client's private key, not server's

### Service Won't Start

**Check for config errors:**
```
sudo wg-quick up wg0
```

Shows specific error messages.

**Common issues:**
- Syntax errors in `/etc/wireguard/wg0.conf`
- Invalid keys (wrong length, invalid characters)
- Duplicate IP addresses
- Port already in use

**View detailed logs:**
```
sudo journalctl -u wg-quick@wg0 -n 50
```

### Performance Issues

**High latency:**
- Check server load and bandwidth
- Try different MTU settings (add `MTU = 1420` to Interface section)
- Consider server location relative to your actual location

**Slow speeds:**
- Check server's network bandwidth limits
- Monitor server CPU usage during transfers
- Consider upgrading server resources

### Connection Drops

**Add to client config:**
PersistentKeepalive = 25


Keeps connection alive through NAT and prevents timeouts.

**Check server uptime:**
```
uptime sudo systemctl status wg-quick@wg0
```

## Security Best Practices

### Key Storage and Protection

**On Server:**
- Protect private key file:
```
sudo chmod 600 /etc/wireguard/private.key 
sudo chmod 600 /etc/wireguard/wg0.conf
```

- Never share server private key
- Back up keys securely (encrypted backup)

**On Clients:**
- Keep config files secure
- Delete configs from revoked devices
- Don't email configs without encryption
- Use secure transfer methods

### Regular Maintenance

**Update WireGuard:**
```
sudo apt update sudo apt upgrade wireguard
```

**Review connected clients periodically:**
```
sudo wg show
```

Remove peers for devices you no longer use.

**Monitor logs for issues:**
```
sudo journalctl -u wg-quick@wg0 --since "1 week ago"
```

**Rotate keys if compromised:**
1. Generate new server keys
2. Update server config
3. Regenerate all client configs with a new server public key
4. Distribute new configs to all devices

### Additional Security

**Use strong DNS:**
- Cloudflare (1.1.1.1) or Quad9 (9.9.9.9) for privacy
- Prevents DNS leaks

**Limit AllowedIPs if needed:**
- Instead of `0.0.0.0/0`, specify only routes you need
- Example: `10.0.0.0/24` for only VPN subnet access

**Consider fail-safe:**
- Some WireGuard clients have "kill switch" options
- Blocks internet if VPN disconnects unexpectedly

**Regular audits:**
- Review `/etc/wireguard/wg0.conf` for unknown peers
- Check server access logs for unauthorized access
- Monitor server resource usage for anomalies

## Quick Reference

### Common Commands

**Server management:**
Start/stop/restart
```
sudo systemctl start wg-quick@wg0 
sudo systemctl stop wg-quick@wg0 
sudo systemctl restart wg-quick@wg0
```
Status and logs
```
sudo systemctl status wg-quick@wg0 
sudo wg show 
sudo journalctl -u wg-quick@wg0
```
Check connections
```
sudo ss -ulnp | grep 51820
```

**Client management:**
Generate keys
```
wg genkey | tee client-private.key | wg pubkey > client-public.key
```
Derive public from private
```
cat client-private.key | wg pubkey
```
View public key
```
cat /etc/wireguard/public.key
```

### File Locations

- Server config: `/etc/wireguard/wg0.conf`
- Server keys: `/etc/wireguard/private.key`, `/etc/wireguard/public.key`
- Client configs: `~/wireguard-clients/`
- Logs:
```
journalctl -u wg-quick@wg0`
```
### IP Address Allocation

- Server: `10.0.0.1`
- Client 1: `10.0.0.2`
- Client 2: `10.0.0.3`
- Continue incrementing for each client

Keep track of assignments to avoid conflicts.

---

*This guide is based on WireGuard setup on Ubuntu 24.04 with Hetzner VPS. Adjust commands and paths for other distributions or providers as needed.*
