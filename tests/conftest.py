from pathlib import Path

import pytest

from cloak_manager.models import Inventory


@pytest.fixture
def inventory_data():
    return {
        "ROUTER_HOST": "root@router.local",
        "ROUTER_AUTH_METHOD": "password",
        "ROUTER_PASSWORD": "secret",
        "SERVICE_NAME": "cloak-home",
        "CLOAK_VERSION": "v2.12.0",
        "VPS_IP": "1.2.3.4",
        "REMOTE_PORT": "443",
        "LOCAL_PORT": "1984",
        "TRANSPORT": "tcp",
        "UID_VALUE": "uid-123",
        "PUBLIC_KEY": "pub-456",
        "SERVER_NAME": "example.com",
    }


@pytest.fixture
def inventory(inventory_data):
    return Inventory(
        router_host=inventory_data["ROUTER_HOST"],
        router_auth_method=inventory_data["ROUTER_AUTH_METHOD"],
        router_password=inventory_data["ROUTER_PASSWORD"],
        service_name=inventory_data["SERVICE_NAME"],
        cloak_version=inventory_data["CLOAK_VERSION"],
        vps_ip=inventory_data["VPS_IP"],
        remote_port=int(inventory_data["REMOTE_PORT"]),
        local_port=int(inventory_data["LOCAL_PORT"]),
        transport=inventory_data["TRANSPORT"],
        uid_value=inventory_data["UID_VALUE"],
        public_key=inventory_data["PUBLIC_KEY"],
        server_name=inventory_data["SERVER_NAME"],
    )


@pytest.fixture
def inventory_file(tmp_path, inventory_data):
    path = tmp_path / "test.env"
    path.write_text(
        "\n".join(f"{key}={value}" for key, value in inventory_data.items()) + "\n"
    )
    return path


@pytest.fixture
def repo_root():
    return Path(__file__).resolve().parent.parent
