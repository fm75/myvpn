import remotetools.remote as rtr
import remotetools.local as rtl
from fabric import Connection

def test_generate_client_keypair():
    c = Connection(host='46.62.216.199', user='root')
    
    private_key, public_key = rtr.generate_client_keypair(c)
    
    assert len(private_key) == 44
    assert len(public_key) == 44
    assert private_key != public_key


def test_retrieve_server_public_key():
    c = Connection(host='46.62.216.199', user='root')
    
    public_key = rtr.retrieve_server_public_key(c)
    
    assert len(public_key) == 44
    assert all(c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=' for c in public_key)


def test_generate_peer_section():
    peer = rtl.PeerRecord(
        name="Alice",
        public_key="test_pubkey_123",
        device="iPhone",
        email="alice@example.com",
        vpn_ip="10.0.0.2",
        created_utc="2024-12-02T23:30:00Z"
    )
    
    section = rtr.generate_peer_section(peer)
    
    assert "[Peer]" in section
    assert "test_pubkey_123" in section
    assert "10.0.0.2/32" in section