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