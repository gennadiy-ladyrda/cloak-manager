from dataclasses import dataclass
from typing import Optional


@dataclass
class Inventory:
    router_host: str
    router_auth_method: str
    router_password: Optional[str]
    service_name: str
    cloak_version: str

    vps_ip: str
    remote_port: int
    local_port: int

    transport: str

    uid_value: str
    public_key: str

    server_name: str
