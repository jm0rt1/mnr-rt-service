"""
Network Location Detection Module

Provides robust network geolocation capabilities with multiple fallback strategies.
Detects the physical location of WiFi/LAN networks and identifies devices on the network.

Features:
- Public IP geolocation with multiple API providers
- Network device discovery
- Arduino webserver detection
- Offline caching for resilience
- Secure, non-intrusive scanning
"""

import json
import logging
import socket
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import requests

logger = logging.getLogger(__name__)


class NetworkLocator:
    """
    Network location detection with intelligent fallback strategies.
    
    This class provides methods to:
    1. Detect network location via public IP geolocation
    2. Discover devices on the local network
    3. Identify Arduino webserver hosts
    4. Cache location data for offline resilience
    """
    
    # Geolocation API providers with fallback support
    GEOLOCATION_APIS = [
        {
            "name": "ip-api",
            "url": "http://ip-api.com/json/",
            "fields": ["lat", "lon", "city", "country", "isp", "query"],
            "rate_limit": 45,  # requests per minute
        },
        {
            "name": "ipapi",
            "url": "https://ipapi.co/json/",
            "fields": ["latitude", "longitude", "city", "country_name", "org", "ip"],
            "rate_limit": 30000,  # requests per month for free tier
        },
        {
            "name": "ipinfo",
            "url": "https://ipinfo.io/json",
            "fields": ["loc", "city", "country", "org", "ip"],
            "rate_limit": 50000,  # requests per month for free tier
        }
    ]
    
    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        cache_ttl_hours: int = 24,
        api_timeout: int = 10
    ):
        """
        Initialize the NetworkLocator.
        
        Args:
            cache_dir: Directory for caching location data (default: ./cache)
            cache_ttl_hours: Time-to-live for cached data in hours
            api_timeout: Timeout for API requests in seconds
        """
        self.cache_dir = cache_dir or Path(__file__).parent.parent.parent / "cache"
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_ttl = timedelta(hours=cache_ttl_hours)
        self.api_timeout = api_timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MNR-RT-Service-TravelAssist/1.0'
        })
        
    def get_network_location(self, use_cache: bool = True) -> Dict[str, any]:
        """
        Get the physical location of the current network.
        
        Uses multiple geolocation APIs with fallback support. Caches results
        for offline resilience.
        
        Args:
            use_cache: Whether to use cached data if available
            
        Returns:
            Dictionary containing:
                - latitude: float
                - longitude: float
                - city: str
                - country: str
                - isp: str
                - ip: str
                - timestamp: str (ISO 8601)
                - source: str (API provider name)
                
        Raises:
            RuntimeError: If all geolocation attempts fail
        """
        # Try to use cached data first
        if use_cache:
            cached_data = self._load_from_cache("network_location")
            if cached_data:
                logger.info("Using cached network location data")
                return cached_data
        
        # Try each geolocation API
        for api_config in self.GEOLOCATION_APIS:
            try:
                location = self._fetch_location_from_api(api_config)
                if location:
                    # Cache the successful result
                    self._save_to_cache("network_location", location)
                    return location
            except Exception as e:
                logger.warning(
                    f"Failed to get location from {api_config['name']}: {e}"
                )
                continue
        
        # All APIs failed, try to return cached data even if expired
        cached_data = self._load_from_cache("network_location", ignore_ttl=True)
        if cached_data:
            logger.warning("All APIs failed, using expired cache")
            cached_data['stale'] = True
            return cached_data
            
        raise RuntimeError("Failed to determine network location from all sources")
    
    def _fetch_location_from_api(
        self, 
        api_config: Dict[str, any]
    ) -> Optional[Dict[str, any]]:
        """
        Fetch location data from a specific geolocation API.
        
        Args:
            api_config: API configuration dictionary
            
        Returns:
            Normalized location dictionary or None if failed
        """
        try:
            response = self.session.get(
                api_config["url"],
                timeout=self.api_timeout
            )
            response.raise_for_status()
            data = response.json()
            
            # Normalize the response based on API provider
            location = self._normalize_location_data(data, api_config["name"])
            location['source'] = api_config['name']
            location['timestamp'] = datetime.now().isoformat()
            
            logger.info(
                f"Successfully fetched location from {api_config['name']}: "
                f"{location['city']}, {location['country']}"
            )
            return location
            
        except Exception as e:
            logger.debug(f"API {api_config['name']} failed: {e}")
            return None
    
    def _normalize_location_data(
        self,
        data: Dict[str, any],
        provider: str
    ) -> Dict[str, any]:
        """
        Normalize location data from different API providers to a consistent format.
        
        Args:
            data: Raw API response data
            provider: API provider name
            
        Returns:
            Normalized location dictionary
        """
        if provider == "ip-api":
            return {
                'latitude': data.get('lat', 0.0),
                'longitude': data.get('lon', 0.0),
                'city': data.get('city', 'Unknown'),
                'country': data.get('country', 'Unknown'),
                'isp': data.get('isp', 'Unknown'),
                'ip': data.get('query', 'Unknown'),
            }
        elif provider == "ipapi":
            return {
                'latitude': data.get('latitude', 0.0),
                'longitude': data.get('longitude', 0.0),
                'city': data.get('city', 'Unknown'),
                'country': data.get('country_name', 'Unknown'),
                'isp': data.get('org', 'Unknown'),
                'ip': data.get('ip', 'Unknown'),
            }
        elif provider == "ipinfo":
            loc = data.get('loc', '0.0,0.0').split(',')
            return {
                'latitude': float(loc[0]) if len(loc) > 0 else 0.0,
                'longitude': float(loc[1]) if len(loc) > 1 else 0.0,
                'city': data.get('city', 'Unknown'),
                'country': data.get('country', 'Unknown'),
                'isp': data.get('org', 'Unknown'),
                'ip': data.get('ip', 'Unknown'),
            }
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    def discover_lan_devices(
        self,
        network_range: Optional[str] = None,
        timeout: float = 0.5
    ) -> List[Dict[str, str]]:
        """
        Discover devices on the local network.
        
        Uses ARP table lookup for fast, non-intrusive device discovery.
        Cross-platform compatible.
        
        Args:
            network_range: CIDR network range (e.g., "192.168.1.0/24")
                          If None, uses current network
            timeout: Timeout for network operations in seconds
            
        Returns:
            List of dictionaries containing:
                - ip: str (IP address)
                - mac: str (MAC address)
                - hostname: str (hostname if resolvable)
        """
        devices = []
        
        try:
            # Use ARP table for device discovery (non-intrusive)
            if subprocess.run(['which', 'arp'], 
                            capture_output=True).returncode == 0:
                devices = self._discover_via_arp()
            else:
                logger.warning("ARP command not available")
                
        except Exception as e:
            logger.error(f"Failed to discover LAN devices: {e}")
        
        # Try to resolve hostnames
        for device in devices:
            try:
                hostname = socket.gethostbyaddr(device['ip'])[0]
                device['hostname'] = hostname
            except (socket.herror, socket.gaierror):
                device['hostname'] = 'Unknown'
        
        logger.info(f"Discovered {len(devices)} devices on LAN")
        return devices
    
    def _discover_via_arp(self) -> List[Dict[str, str]]:
        """
        Discover devices using ARP table.
        
        Returns:
            List of device dictionaries
        """
        devices = []
        
        try:
            # Run arp command
            result = subprocess.run(
                ['arp', '-a'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                # Parse ARP output
                for line in result.stdout.splitlines():
                    # Look for lines with IP and MAC addresses
                    parts = line.split()
                    if len(parts) >= 4:
                        # Extract IP (format may vary by OS)
                        ip = None
                        mac = None
                        
                        for i, part in enumerate(parts):
                            # Look for IP address pattern
                            if '.' in part and part.replace('.', '').isdigit():
                                ip = part.strip('()')
                            # Look for MAC address pattern
                            if ':' in part and len(part.split(':')) == 6:
                                mac = part
                        
                        if ip and mac:
                            devices.append({
                                'ip': ip,
                                'mac': mac,
                                'hostname': 'Unknown'
                            })
        
        except Exception as e:
            logger.error(f"Failed to parse ARP table: {e}")
        
        return devices
    
    def find_arduino_webserver(
        self,
        devices: Optional[List[Dict[str, str]]] = None,
        ports: List[int] = [80, 8080, 5000, 3000]
    ) -> Optional[Dict[str, any]]:
        """
        Find Arduino webserver on the local network.
        
        Checks common ports for HTTP services and attempts to identify
        Arduino-based webservers.
        
        Args:
            devices: List of devices to check (from discover_lan_devices)
                    If None, discovers devices automatically
            ports: List of ports to check
            
        Returns:
            Dictionary containing:
                - ip: str
                - port: int
                - hostname: str
                - mac: str
                - confidence: str ('high', 'medium', 'low')
            or None if not found
        """
        if devices is None:
            devices = self.discover_lan_devices()
        
        for device in devices:
            for port in ports:
                try:
                    # Try to connect to the port
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1.0)
                    result = sock.connect_ex((device['ip'], port))
                    sock.close()
                    
                    if result == 0:
                        # Port is open, try to identify if it's Arduino
                        confidence = self._check_arduino_webserver(
                            device['ip'], 
                            port
                        )
                        
                        if confidence:
                            logger.info(
                                f"Found potential Arduino webserver at "
                                f"{device['ip']}:{port} "
                                f"(confidence: {confidence})"
                            )
                            return {
                                'ip': device['ip'],
                                'port': port,
                                'hostname': device['hostname'],
                                'mac': device.get('mac', 'Unknown'),
                                'confidence': confidence
                            }
                            
                except Exception as e:
                    logger.debug(
                        f"Failed to check {device['ip']}:{port}: {e}"
                    )
                    continue
        
        logger.info("No Arduino webserver found on network")
        return None
    
    def _check_arduino_webserver(
        self,
        ip: str,
        port: int
    ) -> Optional[str]:
        """
        Check if a webserver is likely an Arduino device.
        
        Args:
            ip: IP address
            port: Port number
            
        Returns:
            Confidence level ('high', 'medium', 'low') or None
        """
        try:
            response = self.session.get(
                f"http://{ip}:{port}",
                timeout=2.0
            )
            
            # Check server header
            server = response.headers.get('Server', '').lower()
            content = response.text.lower()
            
            # High confidence indicators
            if 'arduino' in server or 'esp' in server:
                return 'high'
            
            # Medium confidence indicators
            if any(keyword in content for keyword in [
                'arduino', 'esp8266', 'esp32', 'train', 'clock'
            ]):
                return 'medium'
            
            # Low confidence - generic webserver
            if response.status_code == 200:
                return 'low'
            
        except Exception as e:
            logger.debug(f"Failed to check webserver at {ip}:{port}: {e}")
        
        return None
    
    def _save_to_cache(self, key: str, data: Dict[str, any]) -> None:
        """
        Save data to cache file.
        
        Args:
            key: Cache key/filename
            data: Data to cache
        """
        try:
            cache_file = self.cache_dir / f"{key}.json"
            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved data to cache: {cache_file}")
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")
    
    def _load_from_cache(
        self,
        key: str,
        ignore_ttl: bool = False
    ) -> Optional[Dict[str, any]]:
        """
        Load data from cache file.
        
        Args:
            key: Cache key/filename
            ignore_ttl: If True, return data even if expired
            
        Returns:
            Cached data or None if not found/expired
        """
        try:
            cache_file = self.cache_dir / f"{key}.json"
            
            if not cache_file.exists():
                return None
            
            # Check file age
            file_age = datetime.now() - datetime.fromtimestamp(
                cache_file.stat().st_mtime
            )
            
            if not ignore_ttl and file_age > self.cache_ttl:
                logger.debug(f"Cache expired: {cache_file}")
                return None
            
            with open(cache_file, 'r') as f:
                data = json.load(f)
            
            logger.debug(f"Loaded data from cache: {cache_file}")
            return data
            
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")
            return None
