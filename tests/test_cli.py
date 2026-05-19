import argparse
import importlib.util
import sys
from pathlib import Path

import pytest

from cloak_manager.config import ConfigError
from cloak_manager.models import Inventory
from cloak_manager.router import RouterError
from cloak_manager.ssh import SSHError


def load_cli_module(repo_root: Path):
    spec = importlib.util.spec_from_file_location(
        "cloak_manager_cli", repo_root / "cloak_manager.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class FakeSSHClient:
    def __init__(self, *args, **kwargs):
        self.connected = False
        self.closed = False

    def connect(self):
        self.connected = True

    def close(self):
        self.closed = True


def make_inventory():
    return Inventory(
        router_host="root@router.local",
        router_auth_method="key",
        router_password=None,
        service_name="cloak-home",
        cloak_version="v2.12.0",
        vps_ip="1.2.3.4",
        remote_port=443,
        local_port=1984,
        transport="tcp",
        uid_value="uid",
        public_key="pub",
        server_name="example.com",
    )


def test_build_ssh_client_prompts_for_password(monkeypatch, repo_root):
    cli = load_cli_module(repo_root)
    inventory = make_inventory()
    inventory.router_auth_method = "password"
    inventory.router_password = None

    monkeypatch.setattr(cli, "getpass", lambda prompt: "typed-secret")
    created = {}

    class SSHStub:
        def __init__(self, host, auth_method, password):
            created["host"] = host
            created["auth_method"] = auth_method
            created["password"] = password

    monkeypatch.setattr(cli, "SSHClient", SSHStub)

    cli.build_ssh_client(inventory)

    assert created == {
        "host": "root@router.local",
        "auth_method": "password",
        "password": "typed-secret",
    }


def test_cmd_install_closes_ssh_on_failure(monkeypatch, repo_root):
    cli = load_cli_module(repo_root)
    inventory = make_inventory()
    ssh = FakeSSHClient()

    monkeypatch.setattr(cli, "load_inventory", lambda path: inventory)
    monkeypatch.setattr(cli, "build_ssh_client", lambda loaded_inventory: ssh)

    class InstallerStub:
        def __init__(self, ssh_client, loaded_inventory):
            assert ssh_client is ssh
            assert loaded_inventory is inventory

        def install(self):
            raise RuntimeError("boom")

    monkeypatch.setattr(cli, "Installer", InstallerStub)

    with pytest.raises(RuntimeError, match="boom"):
        cli.cmd_install(argparse.Namespace(inventory="inventory/home.env"))

    assert ssh.connected is True
    assert ssh.closed is True


def test_cmd_install_prints_success(monkeypatch, repo_root):
    cli = load_cli_module(repo_root)
    inventory = make_inventory()
    ssh = FakeSSHClient()
    printed = []

    monkeypatch.setattr(cli, "load_inventory", lambda path: inventory)
    monkeypatch.setattr(cli, "build_ssh_client", lambda loaded_inventory: ssh)

    class InstallerStub:
        def __init__(self, ssh_client, loaded_inventory):
            assert ssh_client is ssh
            assert loaded_inventory is inventory

        def install(self):
            return None

    monkeypatch.setattr(cli, "Installer", InstallerStub)
    monkeypatch.setattr(cli.console, "print", lambda value: printed.append(value))

    cli.cmd_install(argparse.Namespace(inventory="inventory/home.env"))

    assert ssh.connected is True
    assert ssh.closed is True
    assert printed == ["[green]Installation complete[/green]"]


def test_cmd_list_renders_all_services(monkeypatch, repo_root):
    cli = load_cli_module(repo_root)
    inventory = make_inventory()
    ssh = FakeSSHClient()

    monkeypatch.setattr(cli, "load_inventory", lambda path: inventory)
    monkeypatch.setattr(cli, "build_ssh_client", lambda loaded_inventory: ssh)

    class RouterStub:
        def __init__(self, ssh_client):
            assert ssh_client is ssh

        def check_existing_services(self):
            return ["cloak-home", "cloak-office"]

    printed = []
    monkeypatch.setattr(cli, "Router", RouterStub)
    monkeypatch.setattr(cli.console, "print", lambda value: printed.append(value))

    cli.cmd_list(argparse.Namespace(inventory="inventory/home.env"))

    assert ssh.connected is True
    assert ssh.closed is True
    assert printed[0].row_count == 2


def test_cmd_status_prints_service_state(monkeypatch, repo_root):
    cli = load_cli_module(repo_root)
    inventory = make_inventory()
    ssh = FakeSSHClient()

    monkeypatch.setattr(cli, "load_inventory", lambda path: inventory)
    monkeypatch.setattr(cli, "build_ssh_client", lambda loaded_inventory: ssh)

    class RouterStub:
        def __init__(self, ssh_client):
            assert ssh_client is ssh

        def get_service_status(self, service_name):
            assert service_name == "cloak-home"
            return "running"

    printed = []
    monkeypatch.setattr(cli, "Router", RouterStub)
    monkeypatch.setattr(cli.console, "print", lambda value: printed.append(value))

    cli.cmd_status(argparse.Namespace(inventory="inventory/home.env"))

    assert ssh.closed is True
    assert printed == ["[green]cloak-home[/green]: running"]


def test_cmd_remove_prints_success(monkeypatch, repo_root):
    cli = load_cli_module(repo_root)
    inventory = make_inventory()
    ssh = FakeSSHClient()
    calls = []

    monkeypatch.setattr(cli, "load_inventory", lambda path: inventory)
    monkeypatch.setattr(cli, "build_ssh_client", lambda loaded_inventory: ssh)

    class RouterStub:
        def __init__(self, ssh_client):
            assert ssh_client is ssh

        def remove_service(self, service_name):
            calls.append(service_name)

    printed = []
    monkeypatch.setattr(cli, "Router", RouterStub)
    monkeypatch.setattr(cli.console, "print", lambda value: printed.append(value))

    cli.cmd_remove(argparse.Namespace(inventory="inventory/home.env"))

    assert calls == ["cloak-home"]
    assert ssh.closed is True
    assert printed == ["[green]Service removed[/green]"]


def test_cmd_update_prints_success(monkeypatch, repo_root):
    cli = load_cli_module(repo_root)
    inventory = make_inventory()
    ssh = FakeSSHClient()
    calls = []

    monkeypatch.setattr(cli, "load_inventory", lambda path: inventory)
    monkeypatch.setattr(cli, "build_ssh_client", lambda loaded_inventory: ssh)

    class InstallerStub:
        def __init__(self, ssh_client, loaded_inventory):
            assert ssh_client is ssh
            assert loaded_inventory is inventory

        def update(self):
            calls.append("update")

    printed = []
    monkeypatch.setattr(cli, "Installer", InstallerStub)
    monkeypatch.setattr(cli.console, "print", lambda value: printed.append(value))

    cli.cmd_update(argparse.Namespace(inventory="inventory/home.env"))

    assert calls == ["update"]
    assert ssh.closed is True
    assert printed == ["[green]Update complete[/green]"]


def test_main_runs_install_command(monkeypatch, repo_root):
    cli = load_cli_module(repo_root)
    calls = []
    monkeypatch.setattr(cli, "cmd_install", lambda args: calls.append(args.inventory))
    monkeypatch.setattr(sys, "argv", ["cloak_manager.py", "install", "inventory/test.env"])

    assert cli.main() == 0
    assert calls == ["inventory/test.env"]


@pytest.mark.parametrize(
    ("command", "attribute"),
    [
        ("list", "cmd_list"),
        ("remove", "cmd_remove"),
        ("update", "cmd_update"),
    ],
)
def test_main_runs_other_commands(monkeypatch, repo_root, command, attribute):
    cli = load_cli_module(repo_root)
    calls = []
    monkeypatch.setattr(cli, attribute, lambda args: calls.append(args.inventory))
    monkeypatch.setattr(sys, "argv", ["cloak_manager.py", command, "inventory/test.env"])

    assert cli.main() == 0
    assert calls == ["inventory/test.env"]


@pytest.mark.parametrize("exc_type", [ConfigError, RouterError, SSHError, Exception])
def test_main_handles_known_errors(monkeypatch, repo_root, exc_type):
    cli = load_cli_module(repo_root)
    printed = []

    def raise_error(args):
        raise exc_type("failure")

    monkeypatch.setattr(cli, "cmd_status", raise_error)
    monkeypatch.setattr(cli.console, "print", lambda value: printed.append(value))
    monkeypatch.setattr(sys, "argv", ["cloak_manager.py", "status", "inventory/test.env"])

    assert cli.main() == 1
    assert printed == ["[red]Error:[/red] failure"]


def test_main_prints_help_without_command(monkeypatch, repo_root):
    cli = load_cli_module(repo_root)
    monkeypatch.setattr(sys, "argv", ["cloak_manager.py"])

    assert cli.main() == 1
