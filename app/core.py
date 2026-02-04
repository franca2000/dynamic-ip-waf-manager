import ipaddress
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from .models import IPEntry

class IPManager:
    def __init__(self):
        # DB SIMULATION: In production, this would be Redis or DynamoDB.
        # Structure: Key="context:ip" -> Value={data...}
        self._store: Dict[str, dict] = {}
        
        # SAFETY NET: Immutable allowlist for critical infrastructure.
        # If someone attempts to block these IPs, the system will reject it.
        self._safety_allowlist = [
            ipaddress.ip_network("127.0.0.1/32"),  # Localhost
            ipaddress.ip_network("192.168.0.0/16"), # Typical Private Network (Office/VPN)
            ipaddress.ip_network("10.0.0.0/8"),     # Cloud Private Network
            # Payment gateways (Stripe, PayPal) IPs could be added here
        ]

    def _is_safe_infrastructure(self, ip_obj) -> bool:
        """
        Checks if an IP belongs to the protected critical infrastructure.
        """
        # Convert to ip_address object if necessary
        if isinstance(ip_obj, str):
            ip_obj = ipaddress.ip_address(ip_obj)
            
        for safe_net in self._safety_allowlist:
            if ip_obj in safe_net:
                return True
        return False

    def add_ip(self, entry: IPEntry) -> dict:
        """
        Adds an IP rule. Validates safety rules and calculates TTL.
        """
        ip_obj = ipaddress.ip_address(str(entry.ip))

        # 1. SAFETY CHECK: Prevent blocking critical infrastructure
        if entry.action == 'BLOCK' and self._is_safe_infrastructure(ip_obj):
            raise ValueError(f"CRITICAL SAFETY: Blocking protected IP {entry.ip} is not allowed")

        # 2. Calculate expiration (if applicable)
        expires_at = None
        if entry.ttl_seconds:
            expires_at = datetime.utcnow() + timedelta(seconds=entry.ttl_seconds)

        # 3. Prepare record
        record = entry.model_dump() # Convert Pydantic model to dict
        record['ip'] = str(record['ip']) # Store IP as string to facilitate JSON serialization
        record['expires_at'] = expires_at
        
        # 4. Save (Upsert - updates if already exists)
        key = self._get_key(entry.context, str(entry.ip))
        self._store[key] = record
        
        return record

    def get_active_ips(self, context: str) -> List[dict]:
        """
        Retrieves active IPs for a context, cleaning up expired ones.
        Strategy: Lazy Expiration (deleted upon read attempt).
        """
        now = datetime.utcnow()
        active_list = []
        keys_to_delete = []

        # Iterate over all rules (in Redis we would use SCAN for efficiency)
        for key, record in self._store.items():
            # Filter by context
            if record['context'] != context:
                continue

            # Check TTL
            if record['expires_at'] and now > record['expires_at']:
                keys_to_delete.append(key) # Marked for deletion
                continue
            
            active_list.append(record)

        # Cleanup expired entries
        for key in keys_to_delete:
            del self._store[key]

        return active_list

    def remove_ip(self, ip: str, context: str) -> bool:
        """Manually removes a rule."""
        key = self._get_key(context, ip)
        if key in self._store:
            del self._store[key]
            return True
        return False

    def _get_key(self, context: str, ip: str) -> str:
        """Generates a unique composite key."""
        return f"{context}:{ip}"
