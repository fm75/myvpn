import remotetools.local as rtl
import fabric
from invoke.exceptions import UnexpectedExit

def generate_client_keypair(c: fabric.connection.Connection) -> tuple[str, str]:
    """Generate WireGuard keypair for a client and return both keys."""
    try:
        result = c.run("wg genkey", hide=True, in_stream=False)
        private_key = result.stdout.strip()
        public_key = c.run(f"echo -n '{private_key}' | wg pubkey", hide=True, in_stream=False).stdout.strip()
        return private_key, public_key
    except UnexpectedExit as e:
        raise RuntimeError(f"Failed to generate client keypair: {e}")


def retrieve_server_public_key(c: fabric.connection.Connection) -> str:
    """Read and return the server's public key from /etc/wireguard/public.key"""
    try:
        result = c.run("cat /etc/wireguard/public.key", hide=True, in_stream=False)
        return result.stdout.strip()
    except UnexpectedExit as e:
        raise FileNotFoundError(f"Server public key not found at /etc/wireguard/public.key: {e}")



def generate_peer_section(peer_record: rtl.PeerRecord) -> str:
    """Generate a [Peer] section for the server config."""
    return f"""
[Peer]
PublicKey = {peer_record.public_key}
AllowedIPs = {peer_record.vpn_ip}/32
"""


def generate_server_config(peer_records: list[rtl.PeerRecord], server_private_key: str) -> str:
    """Generate complete WireGuard server config."""
    interface = f"""[Interface]
Address = 10.0.0.1/24
ListenPort = 51820
PrivateKey = {server_private_key}
PostUp = iptables -A FORWARD -i %i -j ACCEPT; iptables -A FORWARD -o %i -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -D FORWARD -i %i -j ACCEPT; iptables -D FORWARD -o %i -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE
"""
    
    peers = "".join(generate_peer_section(pr) for pr in peer_records)
    return interface + peers


def get_public_interfaces(output: str) -> tuple[int, list[str]]:
    """Parse ip a output and return count and list of public-facing interfaces."""
    lines = output.splitlines()
    interface_blocks = []
    interface_block = []

    # Split into interface blocks
    for line in lines:
        if len(line) == 0:
            continue
        if line[0].isdigit():
            if len(interface_block) > 0:
                interface_blocks.append(interface_block)
                interface_block = []
        interface_block.append(line)
    
    if len(interface_block) > 0:
        interface_blocks.append(interface_block)
    
    # Filter candidates
    candidates = []
    for block in interface_blocks:
        line = block[0].split()
        interf = line[1].replace(":", "")
        
        # Skip loopback and wireguard
        if interf == 'lo' or interf.startswith('wg'):
            continue
        
        # Check for BROADCAST and UP state
        if "BROADCAST" not in block[0] or "state UP" not in block[0]:
            continue
        
        # Check for public IP (not 127.x, 10.x, 192.168.x, 172.16-31.x)
        has_public = False
        for line in block[1:]:
            if 'inet ' in line and 'inet6' not in line:
                ip = line.split()[1].split('/')[0]
                if not (ip.startswith('127.') or 
                       ip.startswith('10.') or 
                       ip.startswith('192.168.') or
                       (ip.startswith('172.') and 16 <= int(ip.split('.')[1]) <= 31)):
                    has_public = True
                    break
        
        if has_public:
            candidates.append(interf)
    
    return len(candidates), candidates

    
def detect_network_interface(c: Connection) -> tuple[int, list[str]]:
    """Detect public-facing network interface on the server."""
    result = c.run("ip a", hide=True, in_stream=False)
    return get_public_interfaces(result.stdout)