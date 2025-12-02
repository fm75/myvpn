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