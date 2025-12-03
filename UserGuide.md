# WireGuard VPN Setup and Management Guide

## What is a VPN?

### General Overview
A VPN (Virtual Private Network) creates a secure, encrypted connection between your device and a server. Think of it as a private tunnel through the internet that:
- Encrypts all your internet traffic
- Hides your real IP address
- Protects your data on public WiFi
- Allows access to resources as if you were on the same network as the server

### WireGuard Specifically
WireGuard is a modern VPN protocol that's:
- **Fast**: Uses state-of-the-art cryptography
- **Simple**: Minimal code base (about 4,000 lines vs 100,000+ for alternatives)
- **Secure**: Modern cryptographic principles
- **Cross-platform**: Works on Linux, Windows, macOS, iOS, Android

## Server Setup

### Prerequisites
- A Linux server (Ubuntu 20.04+ recommended)
- Root or sudo access
- Public IP address
- Port 51820 open in firewall

### Installation

Update system and install WireGuard:

`sudo apt update`  
`sudo apt install wireguard`

### Generate Server Keys

`cd /etc/wireguard`  
`umask 077`  
`wg genkey | sudo tee private.key`  
`sudo cat private.key | wg pubkey | sudo tee public.key`

### Create Server Configuration

Create `/etc/wireguard/wg0.conf`:
[Interface] Address = 10.0.0.1/24 ListenPort = 51820 PrivateKey = PostUp = iptables -A FORWARD -i %i -j ACCEPT; iptables -A FORWARD -o %i -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE PostDown = iptables -D FORWARD -i %i -j ACCEPT; iptables -D FORWARD -o %i -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE

Copied!
**Note**: Replace `eth0` with your server's network interface if different. Check with `ip a`.

### Enable IP Forwarding

`sudo sysctl -w net.ipv4.ip_forward=1`

Make it permanent:

`echo "net.ipv4.ip_forward=1" | sudo tee -a /etc/sysctl.conf`

### Start WireGuard

`sudo systemctl enable wg-quick@wg0`  
`sudo systemctl start wg-quick@wg0`

Verify it's running:

`sudo wg show`

## Client Setup (Manual Method)

### Generate Client Keys

On the server or client:

`wg genkey | tee client_private.key | wg pubkey > client_public.key`

### Add Client to Server

Add to `/etc/wireguard/wg0.conf`:
[Peer] PublicKey = <client_public.key contents> AllowedIPs = 10.0.0.2/32

Copied!
Reload server:

`sudo systemctl restart wg-quick@wg0`

### Create Client Configuration

Create a file (e.g., `client.conf`):
[Interface] PrivateKey = <client_private.key contents> Address = 10.0.0.2/32 DNS = 8.8.8.8

[Peer] PublicKey = Endpoint = <server_public_ip>:51820 AllowedIPs = 0.0.0.0/0 PersistentKeepalive = 25

Copied!
### Import on Client Device

**Mobile (iOS/Android)**:
1. Install WireGuard app
2. Scan QR code or import file
3. Activate tunnel

**Desktop**:
1. Install WireGuard
2. Import configuration file
3. Activate tunnel

## Automated Management with remotetools

The remotetools Python package automates WireGuard peer management, eliminating manual configuration errors and simplifying operations.

### Installation

Install the package in editable mode:

`pip install -e /path/to/myvpn`

### Adding a New Peer

Instead of manually generating keys and editing config files, use the add_peer function. First, create a connection to your server, then add the peer:

`from fabric import Connection`  
`import remotetools.orchestration as rto`

`c = Connection(host='your.server.ip', user='root')`  
`config = rto.add_peer(c, name="Alice", device="iPhone", email="alice@example.com")`

`print(config)  # Send this to the client`

This automatically:
- Generates client keypair
- Assigns next available IP
- Updates server configuration
- Reloads WireGuard service
- Returns client config file

### Removing a Peer

To remove a peer, simply call:

`rto.remove_peer(c, name="Alice", device="iPhone")`

This removes the peer from tracking and updates the server configuration.

### Benefits

- **No manual key generation**: Automated and error-free
- **Automatic IP assignment**: No conflicts or gaps
- **Persistent tracking**: All peers stored in CSV database
- **One-command deployment**: Server config automatically rebuilt and deployed

### Configuration Options

**Default CSV location**: peers.csv in your working directory

**Server endpoint**: Automatically uses the connection host IP with port 51820

**Network interface**: Currently hardcoded to eth0. Check your server's interface with `ip a` and update in code if different (e.g., ens3, ens5).

**VPN subnet**: 10.0.0.0/24 (supports up to 253 clients)

**DNS**: Client configs use 8.8.8.8 by default

### Troubleshooting Automated Management

**Problem: "NameError: name 'fabric' is not defined"**

Solution: Ensure fabric is installed: `pip install fabric`

**Problem: Connection timeout or authentication failure**

Solution: Verify SSH access works manually first: `ssh root@your.server.ip`

Check that your SSH keys are properly configured.

**Problem: "Peer not found" when removing**

Solution: Verify the exact name and device match what's in peers.csv. Names and devices are case-sensitive.

**Problem: VPN stops working after adding peer**

Solution: Check server logs: `sudo journalctl -u wg-quick@wg0 -n 50`

Verify the server config is valid: `sudo wg-quick strip /etc/wireguard/wg0.conf`

**Problem: IP assignment conflicts**

Solution: The system tracks IPs in peers.csv. If you've manually edited server config, sync by removing peers.csv and regenerating from server config.

## Troubleshooting (General)

### Connection Issues

Check server status:

`sudo systemctl status wg-quick@wg0`  
`sudo wg show`

Check logs:

`sudo journalctl -u wg-quick@wg0 -n 50`

### Firewall Issues

Ensure port 51820 is open:

`sudo ufw allow 51820/udp`

### IP Forwarding Not Working

Verify it's enabled:

`sysctl net.ipv4.ip_forward`

Should return 1.

### Client Can't Connect

1. Verify server is running
2. Check firewall rules
3. Verify client config has correct server IP and port
4. Check if client's public key is in server config

## Security Best Practices

1. **Keep private keys private**: Never share or transmit private keys insecurely
2. **Use strong keys**: WireGuard generates cryptographically strong keys automatically
3. **Limit AllowedIPs**: Only route necessary traffic through VPN
4. **Regular updates**: Keep WireGuard and system packages updated
5. **Monitor logs**: Regularly check for unusual activity
6. **Revoke access promptly**: Remove peers immediately when access should end

## Advanced Topics

### Split Tunneling

To only route specific traffic through VPN, change `AllowedIPs` in client config:

`AllowedIPs = 10.0.0.0/24`  (only VPN subnet)

Instead of:

`AllowedIPs = 0.0.0.0/0`  (all traffic)

### Multiple Servers

Clients can have multiple WireGuard configurations for different servers. Each needs unique keys.

### IPv6 Support

Add IPv6 addresses to both server and client configs:

Server: `Address = 10.0.0.1/24, fd00::1/64`  
Client: `Address = 10.0.0.2/32, fd00::2/128`

## Maintenance

### Adding New Clients

See "Client Setup" or "Automated Management" sections above.

### Revoking Client Access

**Manual method**: Remove the `[Peer]` section from `/etc/wireguard/wg0.conf` and restart.

**Automated method**: Use `rto.remove_peer()` as described in the Automated Management section.

### Backup Configuration

Regularly backup:
- `/etc/wireguard/wg0.conf`
- `/etc/wireguard/private.key`
- `peers.csv` (if using automated management)

### Monitoring

Check active connections:

`sudo wg show`

View bandwidth usage:

`sudo wg show wg0 transfer`

## Resources

- [WireGuard Official Site](https://www.wireguard.com/)
- [WireGuard Quick Start](https://www.wireguard.com/quickstart/)
- [WireGuard Protocol Whitepaper](https://www.wireguard.com/papers/wireguard.pdf)