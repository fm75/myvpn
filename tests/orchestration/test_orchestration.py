import remotetools.orchestration as rto
import remotetools.remote as rtr
import remotetools.local as rtl
from fabric.connection import Connection

def mock_deploy_config(c, csv_path):
    pass  # Don't actually deploy during test

def test_add_peer(tmp_path, monkeypatch):
    csv_file = tmp_path / "test_peers.csv"
    
    # Mock remote functions
    def mock_generate_client_keypair(c):
        return ("fake_private_key", "fake_public_key")
    
    def mock_retrieve_server_public_key(c):
        return "fake_server_public_key"
    
    def mock_deploy_config(c, config_text):
        pass  # Don't actually deploy during test
    
    monkeypatch.setattr(rtr, 'generate_client_keypair', mock_generate_client_keypair)
    monkeypatch.setattr(rtr, 'retrieve_server_public_key', mock_retrieve_server_public_key)
    monkeypatch.setattr(rto, 'deploy_config', mock_deploy_config)

    # Create a mock connection (won't actually connect)
    c = Connection(host='test.example.com', user='testuser')
    
    # Call add_peer
    result = rto.add_peer(c, name="Alice", device="iPhone", email="alice@example.com", csv_path=str(csv_file))

    # Verify peer was saved to CSV
    peers = rtl.load_peers(str(csv_file))
    assert len(peers) == 1
    assert peers[0].name == "Alice"
    assert peers[0].public_key == "fake_public_key"
    assert peers[0].vpn_ip == "10.0.0.2"
    
    # Verify result contains client config
    assert result is not None
    assert "fake_private_key" in result


def test_deploy_config(tmp_path, monkeypatch):
    csv_file = tmp_path / "test_peers.csv"
    
    # Create some test peers
    peer1 = rtl.PeerRecord(
        name="Alice",
        public_key="alice_pubkey",
        device="iPhone",
        email="alice@example.com",
        vpn_ip="10.0.0.2",
        created_utc="2024-12-02T23:30:00Z"
    )
    peer2 = rtl.PeerRecord(
        name="Bob",
        public_key="bob_pubkey",
        device="Laptop",
        email="bob@example.com",
        vpn_ip="10.0.0.3",
        created_utc="2024-12-02T23:31:00Z"
    )
    rtl.save_peer(peer1, str(csv_file))
    rtl.save_peer(peer2, str(csv_file))
    
    # Track what commands were run
    commands_run = []
    
    def mock_run(cmd, **kwargs):
        commands_run.append(cmd)
        # Mock response for reading private key
        class MockResult:
            stdout = "fake_server_private_key\n"
        return MockResult()
    
    def mock_sudo(cmd, **kwargs):
        commands_run.append(cmd)
        return None
    
    # Mock the connection methods
    c = Connection(host='test.example.com', user='testuser')
    monkeypatch.setattr(c, 'run', mock_run)
    monkeypatch.setattr(c, 'sudo', mock_sudo)
    
    # Call deploy_config
    rto.deploy_config(c, csv_path=str(csv_file))
    
    # Verify commands were called
    assert len(commands_run) >= 3
    assert "cat /etc/wireguard/private.key" in commands_run[0]
    assert "tee /etc/wireguard/wg0.conf" in commands_run[1]
    assert "wg syncconf" in commands_run[2] or "systemctl restart" in commands_run[2]



################################################### old stuff ###########################
# import pytest
# import os
# from pathlib import Path
# import remotetools.local


# # ################################### tests #####################################
# import stat

# def test_round_trip():
#     priv, pub = remotetools.local.generate_ssh_keypair()
#     pbyte = remotetools.local.generate_public_bytes(priv)
 
#     assert pbyte == pub


# def test_save_private_key():
#     p = "~/foo"
#     key = b'bar'

#     remotetools.local.save_private_key(key, p)
#     x = remotetools.local.retrieve_private_key(p)

#     filepath = Path(p).expanduser()

#     file_stat = os.stat(filepath)
#     file_permissions = stat.S_IMODE(file_stat.st_mode)
    
#     assert file_permissions == 0o600
#     assert x == key


# def test_add_peer(monkeypatch):
#     def mock_keygen():
#         return ('mock_private_key', 'mock_public_key')
    
#     monkeypatch.setattr('remotetools.local.generate_wireguard_keypair', mock_keygen)
    
#     peer = remotetools.local.add_peer('alice')
    
#     assert peer.name == 'alice'
#     assert peer.private_key == 'mock_private_key'
#     assert peer.public_key == 'mock_public_key'


# def test_generate_server_keys():
#     from fabric import Connection
    
#     c = Connection(host='46.62.216.199', user='root')
    
#     # Generate keys in /tmp
#     remotetools.local.deploy_server_keys(c, key_dir="/tmp")
    
#     # Read back the keys
#     priv_result = c.sudo("cat /tmp/private.key", hide=True, in_stream=False)
#     pub_result = c.sudo("cat /tmp/public.key", hide=True, in_stream=False)
    
#     private_key = priv_result.stdout.strip()
#     public_key = pub_result.stdout.strip()
    
#     # Verify the public key can be derived from the private key
#     derived_pub = c.sudo(f"cat /tmp/private.key | wg pubkey", hide=True, in_stream=False)
    
#     assert derived_pub.stdout.strip() == public_key  