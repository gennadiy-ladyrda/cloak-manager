import pytest

from cloak_manager.config import ConfigError, load_inventory


def test_load_inventory_success_defaults_to_key_auth(tmp_path, inventory_data):
    inventory_data.pop("ROUTER_AUTH_METHOD")
    inventory_data.pop("ROUTER_PASSWORD")
    inventory_data["TRANSPORT"] = "UDP"

    path = tmp_path / "inventory.env"
    path.write_text(
        "\n".join(f"{key}={value}" for key, value in inventory_data.items()) + "\n"
    )

    inventory = load_inventory(str(path))

    assert inventory.router_auth_method == "key"
    assert inventory.router_password is None
    assert inventory.transport == "udp"
    assert inventory.remote_port == 443
    assert inventory.local_port == 1984


def test_load_inventory_rejects_missing_required_values(tmp_path, inventory_data):
    inventory_data.pop("VPS_IP")

    path = tmp_path / "inventory.env"
    path.write_text(
        "\n".join(f"{key}={value}" for key, value in inventory_data.items()) + "\n"
    )

    with pytest.raises(ConfigError, match="Missing required variables: VPS_IP"):
        load_inventory(str(path))


def test_load_inventory_rejects_invalid_auth_method(tmp_path, inventory_data):
    inventory_data["ROUTER_AUTH_METHOD"] = "token"

    path = tmp_path / "inventory.env"
    path.write_text(
        "\n".join(f"{key}={value}" for key, value in inventory_data.items()) + "\n"
    )

    with pytest.raises(
        ConfigError, match="ROUTER_AUTH_METHOD must be either 'key' or 'password'"
    ):
        load_inventory(str(path))


def test_load_inventory_rejects_invalid_transport(tmp_path, inventory_data):
    inventory_data["TRANSPORT"] = "quic"

    path = tmp_path / "inventory.env"
    path.write_text(
        "\n".join(f"{key}={value}" for key, value in inventory_data.items()) + "\n"
    )

    with pytest.raises(ConfigError, match="TRANSPORT must be either 'tcp' or 'udp'"):
        load_inventory(str(path))


def test_load_inventory_rejects_non_integer_ports(tmp_path, inventory_data):
    inventory_data["REMOTE_PORT"] = "four-four-three"

    path = tmp_path / "inventory.env"
    path.write_text(
        "\n".join(f"{key}={value}" for key, value in inventory_data.items()) + "\n"
    )

    with pytest.raises(
        ConfigError, match="REMOTE_PORT and LOCAL_PORT must be integers"
    ):
        load_inventory(str(path))
