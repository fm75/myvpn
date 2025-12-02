import remotetools.local as rtl
import remotetools.remote as rtr
from fabric.connection import Connection
from datetime import datetime, timezone


def add_peer(c: Connection, name: str, device: str, email: str, csv_path: str = "peers.csv") -> str:
    """Add a new peer to the VPN and return client config."""
    # 1. Load existing peers
    peers = rtl.load_peers(csv_path)

    # 2. Find next available IP
    ip = rtl.find_next_vpn_ip(peers)
    if ip is None:
        return ip

    # 3. Generate client keypair
    private_key, public_key = rtr.generate_client_keypair(c)

    # 4. Get server public key
    server_key = rtr.retrieve_server_public_key(c)

    # 5. Create PeerInfo with current UTC timestamp
    peer_info = rtl.PeerInfo(name, private_key, public_key, device, email, ip, datetime.now(timezone.utc).isoformat())

    # 6. Convert to PeerRecord and save to CSV
    peer_record = rtl.PeerRecord.from_peer_info(peer_info)
    rtl.save_peer(peer_record, csv_path)

    # 7. Generate client config text
    client_config = rtl.generate_client_config(peer_info, server_key, f"{c.host}:51820")

    # 8. Deploy updated server config
    deploy_config(c, csv_path)

    # 9. Return client config
    return client_config

def deploy_config(c: Connection, csv_path: str = "peers.csv"):
    """Rebuild and deploy server config from peer database."""
    # 1. Load all peers from CSV
    peers = rtl.load_peers(csv_path)
    
    # 2. Get server private key from /etc/wireguard/private.key
    result = c.run("cat /etc/wireguard/private.key", hide=True, in_stream=False)
    server_private_key = result.stdout.strip()
    
    # 3. Generate full server config
    config_text = rtr.generate_server_config(peers, server_private_key)
    
    # 4. Write to /etc/wireguard/wg0.conf
    c.run(f"echo '{config_text}' | sudo tee /etc/wireguard/wg0.conf > /dev/null", hide=True, in_stream=False)
    
    # 5. Reload WireGuard
    c.sudo("wg syncconf wg0 <(wg-quick strip wg0.conf)", hide=True, in_stream=False)

def remove_peer(c: Connection, name: str, device: str, csv_path: str = "peers.csv"):
    """Remove a peer from the VPN."""
    # 1. Delete peer from CSV (need to add delete_peer to local.py)
    # 2. Rebuild and deploy server config
    pass


###############################################################################
# import os
# from pathlib import Path
# from cryptography.hazmat.primitives.asymmetric import ed25519
# from cryptography.hazmat.primitives import serialization
# from dataclasses import dataclass


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


# @dataclass
# class PeerInfo:
#     name: str
#     private_key: str
#     public_key: str


# def generate_wireguard_keypair():
#     return "private", "public"



# def add_peer(name):
#     private_key, public_key = generate_wireguard_keypair()
#     return PeerInfo(name=name, private_key=private_key, public_key=public_key)


# def deploy_server_keys(c, key_dir="/etc/wireguard"):
#     cmd1 = f"wg genkey | tee {key_dir}/private.key"
#     cmd2 = f"cat {key_dir}/private.key | wg pubkey | tee {key_dir}/public.key"
#     c.sudo(cmd1, hide=True, in_stream=False)
#     c.sudo(cmd2, hide=True, in_stream=False)
