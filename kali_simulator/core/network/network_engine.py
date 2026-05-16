"""
Network simulation engine for Kali Linux Simulator.
Provides realistic network simulation with devices, connections, and protocols.
Inspired by Grey Hack networking mechanics.
"""

import socket
import random
import time
import threading
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class ConnectionState(Enum):
    """TCP connection states."""
    CLOSED = "CLOSED"
    LISTEN = "LISTEN"
    SYN_SENT = "SYN_SENT"
    SYN_RECEIVED = "SYN_RECEIVED"
    ESTABLISHED = "ESTABLISHED"
    FIN_WAIT_1 = "FIN_WAIT_1"
    FIN_WAIT_2 = "FIN_WAIT_2"
    CLOSE_WAIT = "CLOSE_WAIT"
    CLOSING = "CLOSING"
    LAST_ACK = "LAST_ACK"
    TIME_WAIT = "TIME_WAIT"


class Protocol(Enum):
    """Network protocols."""
    TCP = "TCP"
    UDP = "UDP"
    ICMP = "ICMP"
    HTTP = "HTTP"
    HTTPS = "HTTPS"
    SSH = "SSH"
    FTP = "FTP"
    SMTP = "SMTP"
    DNS = "DNS"


@dataclass
class IPAddress:
    """Represents an IP address."""
    octets: Tuple[int, int, int, int]
    
    def __init__(self, ip_str: str):
        parts = ip_str.split('.')
        if len(parts) != 4:
            raise ValueError(f"Invalid IP address: {ip_str}")
        self.octets = tuple(int(p) for p in parts)
        if not all(0 <= o <= 255 for o in self.octets):
            raise ValueError(f"Invalid IP address: {ip_str}")
    
    def __str__(self) -> str:
        return '.'.join(str(o) for o in self.octets)
    
    def __hash__(self) -> int:
        return hash(self.octets)
    
    def __eq__(self, other) -> bool:
        if isinstance(other, IPAddress):
            return self.octets == other.octets
        return False
    
    def is_local(self) -> bool:
        """Check if IP is in local network range."""
        return self.octets[0] == 192 and self.octets[1] == 168
    
    def is_loopback(self) -> bool:
        """Check if IP is loopback."""
        return self.octets[0] == 127


@dataclass
class NetworkPort:
    """Represents a network port."""
    number: int
    protocol: Protocol = Protocol.TCP
    state: ConnectionState = ConnectionState.CLOSED
    service: str = ""
    
    def __post_init__(self):
        if not (0 <= self.number <= 65535):
            raise ValueError(f"Invalid port number: {self.number}")


@dataclass
class NetworkConnection:
    """Represents an active network connection."""
    id: str
    local_ip: IPAddress
    local_port: int
    remote_ip: IPAddress
    remote_port: int
    protocol: Protocol
    state: ConnectionState = ConnectionState.ESTABLISHED
    created_at: datetime = field(default_factory=datetime.now)
    bytes_sent: int = 0
    bytes_received: int = 0
    data_buffer: List[bytes] = field(default_factory=list)
    
    def send_data(self, data: bytes) -> int:
        """Send data through connection."""
        self.data_buffer.append(data)
        self.bytes_sent += len(data)
        return len(data)
    
    def receive_data(self) -> bytes:
        """Receive data from connection."""
        if self.data_buffer:
            data = self.data_buffer.pop(0)
            self.bytes_received += len(data)
            return data
        return b""


@dataclass
class NetworkDevice:
    """Represents a network interface device."""
    name: str
    mac_address: str
    ip_addresses: List[IPAddress] = field(default_factory=list)
    subnet_mask: str = "255.255.255.0"
    gateway: Optional[IPAddress] = None
    dns_servers: List[IPAddress] = field(default_factory=list)
    status: str = "UP"
    mtu: int = 1500
    rx_bytes: int = 0
    tx_bytes: int = 0
    rx_packets: int = 0
    tx_packets: int = 0
    
    def add_ip(self, ip: IPAddress):
        """Add IP address to interface."""
        if ip not in self.ip_addresses:
            self.ip_addresses.append(ip)
    
    def remove_ip(self, ip: IPAddress):
        """Remove IP address from interface."""
        if ip in self.ip_addresses:
            self.ip_addresses.remove(ip)


@dataclass
class RemoteHost:
    """Represents a remote host in the network."""
    ip: IPAddress
    hostname: str = ""
    mac_address: str = ""
    os_type: str = "Unknown"
    open_ports: List[int] = field(default_factory=list)
    services: Dict[int, str] = field(default_factory=dict)
    vulnerability_score: float = 0.0
    compromised: bool = False
    last_seen: datetime = field(default_factory=datetime.now)


class NetworkManager:
    """
    Manages network simulation including devices, connections, and traffic.
    Provides realistic network behavior for security tools.
    """
    
    # Common ports and services
    COMMON_PORTS = {
        21: "FTP",
        22: "SSH",
        23: "Telnet",
        25: "SMTP",
        53: "DNS",
        80: "HTTP",
        110: "POP3",
        143: "IMAP",
        443: "HTTPS",
        445: "SMB",
        993: "IMAPS",
        995: "POP3S",
        3306: "MySQL",
        3389: "RDP",
        5432: "PostgreSQL",
        5900: "VNC",
        6379: "Redis",
        8080: "HTTP-Proxy",
        27017: "MongoDB",
    }
    
    # Simulated remote hosts for scanning
    SIMULATED_HOSTS = [
        {"ip": "192.168.1.1", "hostname": "gateway.local", "os": "Linux", "ports": [22, 80, 443]},
        {"ip": "192.168.1.10", "hostname": "webserver.local", "os": "Ubuntu 20.04", "ports": [22, 80, 443, 3306]},
        {"ip": "192.168.1.15", "hostname": "fileserver.local", "os": "Windows Server", "ports": [22, 445, 3389]},
        {"ip": "192.168.1.20", "hostname": "database.local", "os": "CentOS", "ports": [22, 3306, 5432]},
        {"ip": "192.168.1.25", "hostname": "mailserver.local", "os": "Debian", "ports": [22, 25, 110, 143, 993, 995]},
        {"ip": "10.0.0.5", "hostname": "external-server.com", "os": "Unknown", "ports": [80, 443, 8080]},
        {"ip": "10.0.0.10", "hostname": "api.service.net", "os": "Linux", "ports": [443, 6379, 27017]},
        {"ip": "172.16.0.100", "hostname": "internal-app.corp", "os": "Windows 10", "ports": [80, 443, 5900]},
    ]
    
    def __init__(self):
        """Initialize network manager."""
        self.devices: Dict[str, NetworkDevice] = {}
        self.connections: Dict[str, NetworkConnection] = {}
        self.remote_hosts: Dict[IPAddress, RemoteHost] = {}
        self.dns_cache: Dict[str, IPAddress] = {}
        self.arp_table: Dict[IPAddress, str] = {}
        self.routing_table: List[Dict] = []
        self.firewall_rules: List[Dict] = []
        self._connection_counter = 0
        self._lock = threading.Lock()
        
        # Initialize default network configuration
        self._init_default_config()
    
    def _init_default_config(self):
        """Initialize default network configuration."""
        # Create loopback interface
        lo = NetworkDevice(
            name="lo",
            mac_address="00:00:00:00:00:00",
            ip_addresses=[IPAddress("127.0.0.1")],
            subnet_mask="255.0.0.0",
            status="UP"
        )
        self.devices["lo"] = lo
        
        # Create eth0 interface
        eth0 = NetworkDevice(
            name="eth0",
            mac_address=self._generate_mac(),
            ip_addresses=[IPAddress("192.168.1.100")],
            subnet_mask="255.255.255.0",
            gateway=IPAddress("192.168.1.1"),
            dns_servers=[IPAddress("8.8.8.8"), IPAddress("1.1.1.1")],
            status="UP"
        )
        self.devices["eth0"] = eth0
        
        # Setup default routing table
        self.routing_table = [
            {"destination": "127.0.0.0", "gateway": "0.0.0.0", "interface": "lo", "mask": "255.0.0.0"},
            {"destination": "192.168.1.0", "gateway": "0.0.0.0", "interface": "eth0", "mask": "255.255.255.0"},
            {"destination": "0.0.0.0", "gateway": "192.168.1.1", "interface": "eth0", "mask": "0.0.0.0"},
        ]
    
    def _generate_mac(self) -> str:
        """Generate a random MAC address."""
        octets = [random.randint(0x00, 0xFF) for _ in range(6)]
        octets[0] &= 0xFE  # Ensure unicast
        return ':'.join(f'{o:02X}' for o in octets)
    
    def get_interface(self, name: str) -> Optional[NetworkDevice]:
        """Get network interface by name."""
        return self.devices.get(name)
    
    def get_all_interfaces(self) -> List[NetworkDevice]:
        """Get all network interfaces."""
        return list(self.devices.values())
    
    def get_primary_ip(self) -> Optional[IPAddress]:
        """Get primary IP address."""
        for device in self.devices.values():
            if device.name != "lo" and device.ip_addresses:
                return device.ip_addresses[0]
        return None
    
    def add_interface(self, device: NetworkDevice):
        """Add a network interface."""
        self.devices[device.name] = device
    
    def remove_interface(self, name: str):
        """Remove a network interface."""
        if name in self.devices:
            del self.devices[name]
    
    def create_connection(self, local_ip: IPAddress, local_port: int, 
                         remote_ip: IPAddress, remote_port: int,
                         protocol: Protocol = Protocol.TCP) -> NetworkConnection:
        """Create a new network connection."""
        with self._lock:
            self._connection_counter += 1
            conn_id = f"conn_{self._connection_counter}_{int(time.time())}"
            
            connection = NetworkConnection(
                id=conn_id,
                local_ip=local_ip,
                local_port=local_port,
                remote_ip=remote_ip,
                remote_port=remote_port,
                protocol=protocol
            )
            
            self.connections[conn_id] = connection
            return connection
    
    def close_connection(self, conn_id: str) -> bool:
        """Close a network connection."""
        if conn_id in self.connections:
            self.connections[conn_id].state = ConnectionState.CLOSED
            del self.connections[conn_id]
            return True
        return False
    
    def get_active_connections(self) -> List[NetworkConnection]:
        """Get all active connections."""
        return [c for c in self.connections.values() 
                if c.state != ConnectionState.CLOSED]
    
    def scan_port(self, ip: IPAddress, port: int, timeout: float = 1.0) -> bool:
        """Simulate port scanning."""
        # Check if this is a simulated host
        for host_data in self.SIMULATED_HOSTS:
            if host_data["ip"] == str(ip):
                return port in host_data["ports"]
        
        # Random simulation for unknown hosts
        if ip.is_local():
            return random.random() < 0.3  # 30% chance port is open locally
        return random.random() < 0.1  # 10% chance for external hosts
    
    def discover_hosts(self, network_range: str) -> List[RemoteHost]:
        """Discover hosts in a network range."""
        discovered = []
        
        # Parse network range (e.g., "192.168.1.0/24")
        try:
            base_ip, prefix = network_range.split('/')
            prefix_len = int(prefix)
            host_bits = 32 - prefix_len
            num_hosts = min(2 ** host_bits - 2, 256)  # Limit for performance
            
            base_octets = [int(x) for x in base_ip.split('.')]
            
            for i in range(1, num_hosts + 1):
                ip_octets = base_octets.copy()
                ip_octets[3] = i
                ip_str = '.'.join(str(o) for o in ip_octets)
                ip = IPAddress(ip_str)
                
                # Simulate discovery
                if random.random() < 0.3:  # 30% chance host exists
                    host = self.get_or_create_host(ip)
                    discovered.append(host)
        except Exception:
            pass
        
        return discovered
    
    def get_or_create_host(self, ip: IPAddress) -> RemoteHost:
        """Get existing host or create new one."""
        if ip in self.remote_hosts:
            return self.remote_hosts[ip]
        
        # Check if it's a known simulated host
        for host_data in self.SIMULATED_HOSTS:
            if host_data["ip"] == str(ip):
                host = RemoteHost(
                    ip=ip,
                    hostname=host_data["hostname"],
                    os_type=host_data["os"],
                    open_ports=host_data["ports"].copy(),
                    services={p: self.COMMON_PORTS.get(p, "unknown") for p in host_data["ports"]}
                )
                self.remote_hosts[ip] = host
                return host
        
        # Create generic host
        host = RemoteHost(
            ip=ip,
            hostname=f"host-{ip}.local",
            os_type="Unknown",
            open_ports=[]
        )
        self.remote_hosts[ip] = host
        return host
    
    def resolve_hostname(self, hostname: str) -> Optional[IPAddress]:
        """Resolve hostname to IP address."""
        # Check DNS cache
        if hostname in self.dns_cache:
            return self.dns_cache[hostname]
        
        # Check /etc/hosts simulation
        for host_data in self.SIMULATED_HOSTS:
            if host_data["hostname"] == hostname:
                ip = IPAddress(host_data["ip"])
                self.dns_cache[hostname] = ip
                return ip
        
        # Simulate DNS lookup
        if hostname.endswith(".local"):
            # Local domain resolution
            ip = IPAddress(f"192.168.1.{random.randint(1, 254)}")
            self.dns_cache[hostname] = ip
            return ip
        
        # External domain simulation
        if random.random() < 0.8:  # 80% success rate
            ip = IPAddress(f"{random.randint(1,223)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}")
            self.dns_cache[hostname] = ip
            return ip
        
        return None
    
    def add_firewall_rule(self, rule: Dict):
        """Add a firewall rule."""
        self.firewall_rules.append(rule)
    
    def check_firewall(self, src_ip: IPAddress, dst_ip: IPAddress, 
                      port: int, protocol: Protocol) -> bool:
        """Check if traffic is allowed by firewall."""
        for rule in self.firewall_rules:
            if rule.get("action") == "DROP":
                if rule.get("src_ip") == str(src_ip) or rule.get("src_ip") == "any":
                    if rule.get("dst_ip") == str(dst_ip) or rule.get("dst_ip") == "any":
                        if rule.get("port") == port or rule.get("port") == "any":
                            if rule.get("protocol") == str(protocol.value) or rule.get("protocol") == "any":
                                return False
        return True
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get network statistics."""
        total_rx = sum(d.rx_bytes for d in self.devices.values())
        total_tx = sum(d.tx_bytes for d in self.devices.values())
        total_rx_pkt = sum(d.rx_packets for d in self.devices.values())
        total_tx_pkt = sum(d.tx_packets for d in self.devices.values())
        
        return {
            "interfaces": len(self.devices),
            "active_connections": len(self.get_active_connections()),
            "known_hosts": len(self.remote_hosts),
            "dns_cache_size": len(self.dns_cache),
            "firewall_rules": len(self.firewall_rules),
            "total_rx_bytes": total_rx,
            "total_tx_bytes": total_tx,
            "total_rx_packets": total_rx_pkt,
            "total_tx_packets": total_tx_pkt,
        }


# Singleton instance
_network_manager: Optional[NetworkManager] = None


def get_network_manager() -> NetworkManager:
    """Get the global network manager instance."""
    global _network_manager
    if _network_manager is None:
        _network_manager = NetworkManager()
    return _network_manager
