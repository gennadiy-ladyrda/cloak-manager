from pathlib import Path

import pytest

from cloak_manager.installer import Installer


class RecordingSSH:
    def __init__(self):
        self.exec_calls = []
        self.upload_file_calls = []
        self.upload_text_calls = []

    def exec(self, command):
        self.exec_calls.append(command)
        return {"stdout": "", "stderr": "", "exit_code": 0}

    def upload_file(self, local_path, remote_path):
        self.upload_file_calls.append((local_path, remote_path))

    def upload_text(self, remote_path, content):
        self.upload_text_calls.append((remote_path, content))


def test_download_cloak_binary_uses_cache(tmp_path, monkeypatch, inventory):
    monkeypatch.chdir(tmp_path)
    ssh = RecordingSSH()
    installer = Installer(ssh, inventory)
    cached_path = tmp_path / "cache" / "ck-client-linux-amd64-v2.12.0"
    cached_path.parent.mkdir()
    cached_path.write_text("cached")

    calls = []
    monkeypatch.setattr("cloak_manager.installer.urlretrieve", lambda *args: calls.append(args))

    result = installer.download_cloak_binary("amd64")

    assert Path(result) == Path("cache/ck-client-linux-amd64-v2.12.0")
    assert calls == []


def test_download_cloak_binary_downloads_when_cache_is_missing(tmp_path, monkeypatch, inventory):
    monkeypatch.chdir(tmp_path)
    ssh = RecordingSSH()
    installer = Installer(ssh, inventory)
    captured = {}

    def fake_urlretrieve(url, local_path):
        captured["url"] = url
        captured["local_path"] = str(local_path)
        Path(local_path).write_text("downloaded")

    monkeypatch.setattr("cloak_manager.installer.urlretrieve", fake_urlretrieve)

    result = installer.download_cloak_binary("amd64")

    assert result.endswith("cache/ck-client-linux-amd64-v2.12.0")
    assert captured["url"].endswith("/v2.12.0/ck-client-linux-amd64-v2.12.0")
    assert Path(result).read_text() == "downloaded"


def test_upload_binary_moves_binary_into_place(inventory):
    ssh = RecordingSSH()
    installer = Installer(ssh, inventory)

    installer.upload_binary("cache/ck-client")

    assert ssh.upload_file_calls == [("cache/ck-client", "/tmp/ck-client")]
    assert ssh.exec_calls == [
        "chmod +x /tmp/ck-client",
        "mv /tmp/ck-client /usr/sbin/ck-client",
    ]


def test_install_config_renders_and_uploads_json(monkeypatch, inventory):
    ssh = RecordingSSH()
    installer = Installer(ssh, inventory)
    monkeypatch.setattr("cloak_manager.installer.render_template", lambda name, context: f"{name}:{context['service_name']}")

    installer.install_config()

    assert ssh.exec_calls == ["mkdir -p /etc/cloak"]
    assert ssh.upload_text_calls == [
        ("/etc/cloak/cloak-home.json", "ckclient.json.j2:cloak-home")
    ]


def test_install_service_renders_and_uploads_init_script(monkeypatch, inventory):
    ssh = RecordingSSH()
    installer = Installer(ssh, inventory)
    monkeypatch.setattr("cloak_manager.installer.render_template", lambda name, context: f"{name}:{context['transport']}")

    installer.install_service()

    assert ssh.upload_text_calls == [
        ("/etc/init.d/cloak-home", "init.d.j2:tcp")
    ]
    assert ssh.exec_calls == ["chmod +x /etc/init.d/cloak-home"]


def test_enable_service_runs_enable_and_restart(inventory):
    ssh = RecordingSSH()
    installer = Installer(ssh, inventory)

    installer.enable_service()

    assert ssh.exec_calls == [
        "/etc/init.d/cloak-home enable",
        "/etc/init.d/cloak-home restart",
    ]


def test_install_runs_expected_sequence(monkeypatch, inventory):
    ssh = RecordingSSH()
    installer = Installer(ssh, inventory)
    events = []

    class RouterStub:
        def check_disk_space(self):
            events.append("check_disk_space")

        def service_exists(self, service_name):
            events.append(("service_exists", service_name))
            return False

        def detect_architecture(self):
            events.append("detect_architecture")
            return "amd64"

    installer.router = RouterStub()
    monkeypatch.setattr(installer, "download_cloak_binary", lambda arch: events.append(("download", arch)) or "cache/bin")
    monkeypatch.setattr(installer, "upload_binary", lambda path: events.append(("upload_binary", path)))
    monkeypatch.setattr(installer, "install_config", lambda: events.append("install_config"))
    monkeypatch.setattr(installer, "install_service", lambda: events.append("install_service"))
    monkeypatch.setattr(installer, "enable_service", lambda: events.append("enable_service"))

    installer.install()

    assert events == [
        "check_disk_space",
        ("service_exists", "cloak-home"),
        "detect_architecture",
        ("download", "amd64"),
        ("upload_binary", "cache/bin"),
        "install_config",
        "install_service",
        "enable_service",
    ]


def test_install_rejects_existing_service(monkeypatch, inventory):
    ssh = RecordingSSH()
    installer = Installer(ssh, inventory)

    class RouterStub:
        def check_disk_space(self):
            return 64

        def service_exists(self, service_name):
            return True

    installer.router = RouterStub()

    with pytest.raises(Exception, match="Service cloak-home already exists"):
        installer.install()


def test_update_runs_expected_sequence(monkeypatch, inventory):
    ssh = RecordingSSH()
    installer = Installer(ssh, inventory)
    events = []

    class RouterStub:
        def check_disk_space(self):
            events.append("check_disk_space")

        def service_exists(self, service_name):
            events.append(("service_exists", service_name))
            return True

        def detect_architecture(self):
            events.append("detect_architecture")
            return "amd64"

    installer.router = RouterStub()
    monkeypatch.setattr(installer, "download_cloak_binary", lambda arch: events.append(("download", arch)) or "cache/bin")
    monkeypatch.setattr(installer, "upload_binary", lambda path: events.append(("upload_binary", path)))
    monkeypatch.setattr(installer, "install_config", lambda: events.append("install_config"))
    monkeypatch.setattr(installer, "install_service", lambda: events.append("install_service"))
    monkeypatch.setattr(installer, "enable_service", lambda: events.append("enable_service"))

    installer.update()

    assert events == [
        "check_disk_space",
        ("service_exists", "cloak-home"),
        "detect_architecture",
        ("download", "amd64"),
        ("upload_binary", "cache/bin"),
        "install_config",
        "install_service",
        "enable_service",
    ]


def test_update_rejects_missing_service(inventory):
    ssh = RecordingSSH()
    installer = Installer(ssh, inventory)

    class RouterStub:
        def check_disk_space(self):
            return 64

        def service_exists(self, service_name):
            return False

    installer.router = RouterStub()

    with pytest.raises(Exception, match="Service cloak-home is not installed"):
        installer.update()
