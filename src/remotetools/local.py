
import csv
from pathlib import Path
from dataclasses import dataclass, asdict

# Move these somewhere else. Maybe useful for ssh key stuff
# import os
# from cryptography.hazmat.primitives.asymmetric import ed25519
# from cryptography.hazmat.primitives import serialization

# def generate_ssh_keypair():
#     private_key = ed25519.Ed25519PrivateKey.generate()
#     private_bytes = private_key.private_bytes(
#         encoding=serialization.Encoding.PEM,
#         format=serialization.PrivateFormat.OpenSSH,
#         encryption_algorithm=serialization.NoEncryption()
#     )
#     public_key = private_key.public_key()
#     public_bytes = public_key.public_bytes(
#         encoding=serialization.Encoding.OpenSSH,
#         format=serialization.PublicFormat.OpenSSH
#     )
#     return private_bytes, public_bytes

# def generate_public_bytes(private_bytes):
#     loaded_key = serialization.load_ssh_private_key(private_bytes, password=None)
#     public_key = loaded_key.public_key()
#     return public_key.public_bytes(
#         encoding=serialization.Encoding.OpenSSH,
#         format=serialization.PublicFormat.OpenSSH
#     )


# def save_private_key(key_bytes, filepath):
#     filepath = Path(filepath).expanduser()
#     filepath.parent.mkdir(parents=True, exist_ok=True)
    
#     # Write the key
#     filepath.write_bytes(key_bytes)
    
#     # Set permissions to 0o600 (owner read/write only)
#     os.chmod(filepath, 0o600)


# def retrieve_private_key(filepath):
#     filepath = Path(filepath).expanduser()
#     content = filepath.read_bytes()
#     return content


@dataclass
class PeerInfo:
    name: str
    private_key: str
    public_key: str
    device: str
    email: str
    vpn_ip: str
    created_utc: str


@dataclass
class PeerRecord:
    name: str
    public_key: str
    device: str
    email: str
    vpn_ip: str
    created_utc: str
    
    @classmethod
    def from_peer_info(cls, peer_info: PeerInfo) -> 'PeerRecord':
        return cls(
            name=peer_info.name,
            public_key=peer_info.public_key,
            device=peer_info.device,
            email=peer_info.email,
            vpn_ip=peer_info.vpn_ip,
            created_utc=peer_info.created_utc
        )


def save_peer(peer_record: PeerRecord, csv_path: str = "peers.csv"):
    """Append a single peer to the CSV file."""
    file_exists = Path(csv_path).exists()
    
    with open(csv_path, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['name', 'public_key', 'device', 'email', 'vpn_ip', 'created_utc'])
        if not file_exists:
            writer.writeheader()
        writer.writerow(asdict(peer_record))


def load_peers(csv_path: str = "peers.csv") -> list[PeerRecord]:
    """Load all peers from the CSV file."""
    if not Path(csv_path).exists():
        return []
    
    with open(csv_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        return [PeerRecord(**row) for row in reader]


def find_next_vpn_ip(peer_records: list[PeerRecord]) -> str | None:
    all_possible = set(f"10.0.0.{i}" for i in range(2, 255))
    used_ips = {record.vpn_ip for record in peer_records}
    available = all_possible - used_ips
    return min(available, key=lambda ip: int(ip.split('.')[-1])) if available else None


def generate_client_config(peer_info: PeerInfo, server_public_key: str, server_endpoint: str = "46.62.216.199:51820") -> str:
    """Generate WireGuard client config file text."""
    return f"""[Interface]
PrivateKey = {peer_info.private_key}
Address = {peer_info.vpn_ip}/32
DNS = 8.8.8.8

[Peer]
PublicKey = {server_public_key}
Endpoint = {server_endpoint}
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
"""


def save_client_config(client_config: str, name: str, device: str, output_dir: str = ".") -> str:
    """Save client config to a file and return the filename."""
    filename = f"{name}_{device}.conf"
    filepath = Path(output_dir) / filename
    filepath.write_text(client_config)
    return str(filepath)
