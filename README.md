# Dynamic WAF IP Manager

A centralized, safety-first service to dynamically manage IP allowlists and blocklists for WAF enforcement. This solution acts as a "Source of Truth" to prevent unintended blocking of legitimate traffic.

## Overview

This project implements a RESTful API designed to decouple human intent (e.g., "block this attacker for 1 hour") from specific WAF configurations. It handles validation, expiration (TTL), and safety checks before rules are consumed by enforcement layers.

### Key Features
* **Dynamic TTL**: Supports temporary blocks (e.g., 60 seconds) that expire automatically.
* **Context Awareness**: Manages rules per environment or merchant (e.g., `prod`, `staging`, `merchant-xyz`).
* **Safety Net**: Hardcoded checks to prevent blocking critical infrastructure.
* **WAF Integration**: Exposes a `GET /waf/config/{context}` endpoint optimized for WAF polling mechanisms.

## Preventing Legitimate Traffic Blocking

The core objective of this challenge is operational safety. This solution implements three layers of protection:

1.  **Critical Infrastructure Allowlist (The Safety Net):**
    The `IPManager` core logic contains an immutable list of safe CIDRs (e.g., Private Networks, Corporate VPNs). Any attempt to add a `BLOCK` rule against these IPs is rejected immediately with a `400 Bad Error`.
    
2.  **Input Validation:**
    Uses strict typing (`IPvAnyAddress` via Pydantic) to reject malformed IP strings (e.g., `192.168.1.999`) before they reach the logic layer.

3.  **Lazy Expiration:**
    Rules are evaluated at read-time. If a temporary block has expired, it is automatically removed from the list returned to the WAF, ensuring that blocks do not persist longer than intended.

## Setup & Running

### Option A: Running Locally (Python)

**Prerequisites:** Python 3.9+

1.  **Clone the repository:**
    
    git clone [https://github.com/YOUR_USER/dynamic-ip-waf-manager.git](https://github.com/franca2000/dynamic-ip-waf-manager.git)
    cd dynamic-ip-waf-manager
    

2.  **Setup Environment:**
    
    python -m venv venv
    # Windows:
    .\venv\Scripts\Activate
    # Mac/Linux:
    source venv/bin/activate
    

3.  **Install Dependencies:**
    pip install -r requirements.txt
    

4.  **Run the Server:**
    
    uvicorn app.main:app --reload
    
    The API will be available at `http://127.0.0.1:8000`.
    Interactive documentation: `http://127.0.0.1:8000/docs`.

### Option B: Running with Docker

1.  **Build the image:**
    
    docker build -t waf-manager .
    

2.  **Run the container:**
    
    docker run -p 8000:8000 waf-manager

## Infrastructure as Code (Terraform)

A `terraform/` directory is included to demonstrate how this application would be deployed to **AWS** using modern serverless container practices.

**Resources defined:**
1.  **AWS ECR**: To securely store the Docker image.
2.  **AWS App Runner**: To run the API as a scalable, managed service (eliminating the need to manage EC2/ECS servers manually).

**Usage:**
```bash
cd terraform
terraform init
terraform plan
# terraform apply  <-- Deploys infrastructure to AWS
    

## API Usage Examples

### 1. Block an Attacker (Temporary)
Blocks an IP for 60 seconds.

curl -X POST "[http://127.0.0.1:8000/ips/](http://127.0.0.1:8000/ips/)" \
     -H "Content-Type: application/json" \
     -d '{"ip": "203.0.113.5", "action": "BLOCK", "context": "prod", "ttl_seconds": 60}'
