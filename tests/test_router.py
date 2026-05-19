import pytest

from cloak_manager.router import Router, RouterError


class FakeSSH:
    def __init__(self, responses):
        self.responses = responses
        self.commands = []

    def exec(self, command):
        self.commands.append(command)
        response = self.responses.get(command)
        if response is None:
            raise AssertionError(f"Unexpected command: {command}")
        return response


def test_detect_architecture_maps_supported_value():
    ssh = FakeSSH({"uname -m": {"stdout": "x86_64\n", "stderr": "", "exit_code": 0}})

    assert Router(ssh).detect_architecture() == "amd64"


def test_detect_architecture_rejects_unsupported_value():
    ssh = FakeSSH({"uname -m": {"stdout": "sparc\n", "stderr": "", "exit_code": 0}})

    with pytest.raises(RouterError, match="Unsupported architecture: sparc"):
        Router(ssh).detect_architecture()


def test_check_disk_space_returns_available_megabytes():
    ssh = FakeSSH(
        {"df -m / | tail -1 | awk '{print $4}'": {"stdout": "64\n", "stderr": "", "exit_code": 0}}
    )

    assert Router(ssh).check_disk_space() == 64


def test_check_disk_space_rejects_low_space():
    ssh = FakeSSH(
        {"df -m / | tail -1 | awk '{print $4}'": {"stdout": "19\n", "stderr": "", "exit_code": 0}}
    )

    with pytest.raises(RouterError, match="Not enough disk space. Only 19 MB available"):
        Router(ssh).check_disk_space()


def test_check_existing_services_parses_service_names():
    ssh = FakeSSH(
        {
            "find /etc/init.d -maxdepth 1 -name 'cloak-*' -type f": {
                "stdout": "/etc/init.d/cloak-home\n/etc/init.d/cloak-office\n",
                "stderr": "",
                "exit_code": 0,
            }
        }
    )

    assert Router(ssh).check_existing_services() == ["cloak-home", "cloak-office"]


def test_service_exists_checks_membership(monkeypatch):
    router = Router(FakeSSH({}))
    monkeypatch.setattr(router, "check_existing_services", lambda: ["cloak-home"])

    assert router.service_exists("cloak-home") is True
    assert router.service_exists("cloak-missing") is False


def test_get_service_status_returns_not_installed(monkeypatch):
    router = Router(FakeSSH({}))
    monkeypatch.setattr(router, "service_exists", lambda service_name: False)

    assert router.get_service_status("cloak-home") == "not installed"


def test_get_service_status_returns_running(monkeypatch):
    ssh = FakeSSH(
        {"/etc/init.d/cloak-home status >/dev/null 2>&1": {"stdout": "", "stderr": "", "exit_code": 0}}
    )
    router = Router(ssh)
    monkeypatch.setattr(router, "service_exists", lambda service_name: True)

    assert router.get_service_status("cloak-home") == "running"


def test_get_service_status_returns_stopped(monkeypatch):
    ssh = FakeSSH(
        {"/etc/init.d/cloak-home status >/dev/null 2>&1": {"stdout": "", "stderr": "", "exit_code": 1}}
    )
    router = Router(ssh)
    monkeypatch.setattr(router, "service_exists", lambda service_name: True)

    assert router.get_service_status("cloak-home") == "stopped"


def test_remove_service_runs_cleanup_commands(monkeypatch):
    ssh = FakeSSH(
        {
            "/etc/init.d/cloak-home stop >/dev/null 2>&1 || true": {"stdout": "", "stderr": "", "exit_code": 0},
            "/etc/init.d/cloak-home disable >/dev/null 2>&1 || true": {"stdout": "", "stderr": "", "exit_code": 0},
            "rm -f /etc/init.d/cloak-home": {"stdout": "", "stderr": "", "exit_code": 0},
            "rm -f /etc/cloak/cloak-home.json": {"stdout": "", "stderr": "", "exit_code": 0},
        }
    )
    router = Router(ssh)
    monkeypatch.setattr(router, "service_exists", lambda service_name: True)

    router.remove_service("cloak-home")

    assert ssh.commands == [
        "/etc/init.d/cloak-home stop >/dev/null 2>&1 || true",
        "/etc/init.d/cloak-home disable >/dev/null 2>&1 || true",
        "rm -f /etc/init.d/cloak-home",
        "rm -f /etc/cloak/cloak-home.json",
    ]


def test_remove_service_rejects_missing_service(monkeypatch):
    router = Router(FakeSSH({}))
    monkeypatch.setattr(router, "service_exists", lambda service_name: False)

    with pytest.raises(RouterError, match="Service cloak-home is not installed"):
        router.remove_service("cloak-home")
