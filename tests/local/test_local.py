import remotetools.local as rtl
# from dataclasses import asdict
# from dataclasses import dataclass, asdict

def test_peer_record_from_peer_info():
    peer_info = rtl.PeerInfo(
        name="Alice",
        private_key="private123",
        public_key="public456",
        device="iPhone",
        email="alice@example.com",
        vpn_ip="10.0.0.2",
        created_utc="2024-12-02T23:30:00Z"
    )
    
    peer_record = rtl.PeerRecord.from_peer_info(peer_info)
    
    assert peer_record.name == "Alice"
    assert peer_record.public_key == "public456"
    assert peer_record.device == "iPhone"
    assert peer_record.email == "alice@example.com"
    assert peer_record.vpn_ip == "10.0.0.2"
    assert peer_record.created_utc == "2024-12-02T23:30:00Z"
    assert not hasattr(peer_record, 'private_key')


def test_save_and_load_peers(tmp_path):
    csv_file = tmp_path / "test_peers.csv"
    
    # Create and save some peers
    peer1 = rtl.PeerRecord(
        name="Alice",
        public_key="pubkey1",
        device="iPhone",
        email="alice@example.com",
        vpn_ip="10.0.0.2",
        created_utc="2024-12-02T23:30:00Z"
    )
    peer2 = rtl.PeerRecord(
        name="Bob",
        public_key="pubkey2",
        device="Laptop",
        email="bob@example.com",
        vpn_ip="10.0.0.4",
        created_utc="2024-12-02T23:31:00Z"
    )
    
    rtl.save_peer(peer1, str(csv_file))
    rtl.save_peer(peer2, str(csv_file))
    
    # Load them back
    loaded = rtl.load_peers(str(csv_file))
    
    assert len(loaded) == 2
    assert loaded[0].name == "Alice"
    assert loaded[1].name == "Bob"
    
    # Test find_next_vpn_ip
    next_ip = rtl.find_next_vpn_ip(loaded)
    assert next_ip == "10.0.0.3"  # Should find the gap



############################# move to tests/ssh_stuff/test_ssh_stuff.py
# import os
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
