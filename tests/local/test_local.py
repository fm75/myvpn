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
    
    rtl.save_peer_to_csv(peer1, str(csv_file))
    rtl.save_peer_to_csv(peer2, str(csv_file))
    
    # Load them back
    loaded = rtl.load_peers(str(csv_file))
    
    assert len(loaded) == 2
    assert loaded[0].name == "Alice"
    assert loaded[1].name == "Bob"
    
    # Test find_next_vpn_ip
    next_ip = rtl.find_next_vpn_ip(loaded)
    assert next_ip == "10.0.0.3"  # Should find the gap


def test_delete_peer(tmp_path):
    """Test deleting a peer from CSV."""
    csv_file = tmp_path / "test_peers.csv"
    
    # Add some peers
    peer1 = rtl.PeerRecord(name="Alice", public_key="key1", device="iPhone", 
                           email="alice@test.com", vpn_ip="10.0.0.2", created_utc="2024-12-03T00:00:00Z")
    peer2 = rtl.PeerRecord(name="Bob", public_key="key2", device="Laptop", 
                           email="bob@test.com", vpn_ip="10.0.0.3", created_utc="2024-12-03T00:01:00Z")
    rtl.save_peer_to_csv(peer1, str(csv_file))
    rtl.save_peer_to_csv(peer2, str(csv_file))
    
    # Delete Alice
    result = rtl.remove_peer_from_csv("Alice", "iPhone", str(csv_file))
    assert result is True
    
    # Verify only Bob remains
    peers = rtl.load_peers(str(csv_file))
    assert len(peers) == 1
    assert peers[0].name == "Bob"
    
    # Try deleting non-existent peer
    result = rtl.remove_peer_from_csv("Charlie", "iPad", str(csv_file))
    assert result is False

def test_find_next_vpn_ip_empty_csv(tmp_path):
    """Test that first IP is 10.0.0.2 when no peers exist."""
    csv_file = tmp_path / "empty_peers.csv"
    
    peers = rtl.load_peers(str(csv_file))
    next_ip = rtl.find_next_vpn_ip(peers)
    
    assert next_ip == "10.0.0.2"


def test_find_next_vpn_ip_full_range(tmp_path):
    """Test that None is returned when all IPs are used."""
    csv_file = tmp_path / "full_peers.csv"
    
    # Create 253 peers (10.0.0.2 through 10.0.0.254)
    for i in range(2, 255):
        peer = rtl.PeerRecord(
            name=f"User{i}",
            public_key=f"pubkey{i}",
            device="Device",
            email=f"user{i}@example.com",
            vpn_ip=f"10.0.0.{i}",
            created_utc="2024-12-03T00:00:00Z"
        )
        rtl.save_peer_to_csv(peer, str(csv_file))
    
    peers = rtl.load_peers(str(csv_file))
    next_ip = rtl.find_next_vpn_ip(peers)
    
    assert next_ip is None


def test_load_peers_nonexistent_file():
    """Test that loading from non-existent file returns empty list."""
    peers = rtl.load_peers("this_file_does_not_exist.csv")
    
    assert peers == []


def test_remove_peer_from_csv(tmp_path):
    """Test deleting a peer from CSV."""
    csv_file = tmp_path / "test_peers.csv"
    
    # Add some peers
    peer1 = rtl.PeerRecord(name="Alice", public_key="key1", device="iPhone", 
                           email="alice@test.com", vpn_ip="10.0.0.2", created_utc="2024-12-03T00:00:00Z")
    peer2 = rtl.PeerRecord(name="Bob", public_key="key2", device="Laptop", 
                           email="bob@test.com", vpn_ip="10.0.0.3", created_utc="2024-12-03T00:01:00Z")
    rtl.save_peer_to_csv(peer1, str(csv_file))
    rtl.save_peer_to_csv(peer2, str(csv_file))
    
    # Delete Alice
    result = rtl.remove_peer_from_csv("Alice", "iPhone", str(csv_file))
    assert result is True
    
    # Verify only Bob remains
    peers = rtl.load_peers(str(csv_file))
    assert len(peers) == 1
    assert peers[0].name == "Bob"
    
    # Try deleting non-existent peer
    result = rtl.remove_peer_from_csv("Charlie", "iPad", str(csv_file))
    assert result is False


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
