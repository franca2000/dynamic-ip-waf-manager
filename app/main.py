from fastapi import FastAPI, HTTPException
from typing import Dict, List
from datetime import datetime
from .models import IPEntry, IPResponse
from .core import IPManager

# Initialize the application
app = FastAPI(
    title="Dynamic WAF IP Manager",
    description="Centralized API to manage IP allowlists and blocklists for WAF enforcement.",
    version="1.0.0"
)

# Instantiate the logic core (Singleton pattern for this challenge)
manager = IPManager()

@app.get("/")
def health_check():
    """
    Simple health check to verify the service is running.
    """
    return {"status": "ok", "timestamp": datetime.utcnow()}

@app.post("/ips/", status_code=201)
def add_ip_rule(entry: IPEntry):
    """
    Adds a new IP rule (ALLOW/BLOCK).
    - Validates IP syntax.
    - Checks against the safety allowlist (prevents blocking critical infra).
    - Calculates TTL expiration if provided.
    """
    try:
        result = manager.add_ip(entry)
        return {"status": "added", "data": result}
    
    except ValueError as e:
        # Catch safety violations (e.g., trying to block a corporate VPN IP)
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/waf/config/{context}")
def get_waf_configuration(context: str):
    """
    WAF CONSUMPTION ENDPOINT.
    
    This endpoint is designed to be polled by the WAF or a sync agent.
    It returns the consolidated lists of IPs to block and allow for a specific context.
    
    - It automatically filters out expired IPs (TTL check).
    - Returns data in a format ready for WAF ingestion.
    """
    active_rules = manager.get_active_ips(context)
    
    # Segregate rules into sets for easy WAF consumption
    allow_set = [r['ip'] for r in active_rules if r['action'] == 'ALLOW']
    block_set = [r['ip'] for r in active_rules if r['action'] == 'BLOCK']
    
    return {
        "meta": {
            "context": context,
            "generated_at": datetime.utcnow(),
            "rule_count": len(active_rules)
        },
        "policy": {
            "allow_list": allow_set,
            "block_list": block_set
        }
    }

@app.delete("/ips/{context}/{ip}")
def remove_ip_rule(context: str, ip: str):
    """
    Manually removes an IP rule before its TTL expires.
    """
    if manager.remove_ip(ip, context):
        return {"status": "removed", "ip": ip, "context": context}
    
    raise HTTPException(status_code=404, detail="IP rule not found in this context")