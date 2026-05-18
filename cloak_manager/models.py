from dataclasses import dataclass


@dataclass
class Inventory:
    router_host: str
    service_name: str
    cloak_version: str

    vps_ip: str
    remote_port: int
    local_port: int

    transport: str

    uid_value: str
    public_key: str

    server_name: str
