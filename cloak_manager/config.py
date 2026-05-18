from dotenv import dotenv_values
from cloak_manager.models import Inventory


VALID_AUTH_METHODS = {"key", "password"}

REQUIRED_KEYS = [
    "ROUTER_HOST",
    "SERVICE_NAME",
    "CLOAK_VERSION",
    "VPS_IP",
    "REMOTE_PORT",
    "LOCAL_PORT",
    "TRANSPORT",
    "UID_VALUE",
    "PUBLIC_KEY",
    "SERVER_NAME",
]


class ConfigError(Exception):
    pass


def load_inventory(path: str) -> Inventory:
    data = dotenv_values(path)

    missing = [key for key in REQUIRED_KEYS if not data.get(key)]

    if missing:
        raise ConfigError(f"Missing required variables: {', '.join(missing)}")

    router_auth_method = (data.get("ROUTER_AUTH_METHOD") or "key").strip().lower()

    if router_auth_method not in VALID_AUTH_METHODS:
        raise ConfigError(
            "ROUTER_AUTH_METHOD must be either 'key' or 'password'"
        )

    return Inventory(
        router_host=data["ROUTER_HOST"],
        router_auth_method=router_auth_method,
        router_password=data.get("ROUTER_PASSWORD"),
        service_name=data["SERVICE_NAME"],
        cloak_version=data["CLOAK_VERSION"],
        vps_ip=data["VPS_IP"],
        remote_port=int(data["REMOTE_PORT"]),
        local_port=int(data["LOCAL_PORT"]),
        transport=data["TRANSPORT"],
        uid_value=data["UID_VALUE"],
        public_key=data["PUBLIC_KEY"],
        server_name=data["SERVER_NAME"],
    )
