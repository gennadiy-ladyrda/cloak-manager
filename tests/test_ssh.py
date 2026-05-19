from io import BytesIO

import pytest

from cloak_manager.ssh import SSHClient, SSHError


class FakeAutoAddPolicy:
    pass


class FakeChannel:
    def __init__(self, exit_code):
        self.exit_code = exit_code

    def recv_exit_status(self):
        return self.exit_code


class FakeStream:
    def __init__(self, content, exit_code=0):
        self._buffer = BytesIO(content)
        self.channel = FakeChannel(exit_code)

    def read(self):
        return self._buffer.read()


class FakeRemoteFile:
    def __init__(self, sftp, path, mode):
        self.sftp = sftp
        self.path = path
        self.mode = mode
        self.content = ""

    def write(self, content):
        self.content += content

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.sftp.opened_files.append((self.path, self.mode, self.content))
        return False


class FakeSFTP:
    def __init__(self):
        self.opened_files = []
        self.put_calls = []
        self.closed = False

    def open(self, path, mode):
        return FakeRemoteFile(self, path, mode)

    def put(self, local_path, remote_path):
        self.put_calls.append((local_path, remote_path))

    def close(self):
        self.closed = True


class FakeParamikoClient:
    def __init__(self):
        self.policy = None
        self.connect_kwargs = None
        self.exec_calls = []
        self.closed = False
        self.sftp = FakeSFTP()
        self.connect_error = None

    def set_missing_host_key_policy(self, policy):
        self.policy = policy

    def connect(self, **kwargs):
        if self.connect_error is not None:
            raise self.connect_error
        self.connect_kwargs = kwargs

    def exec_command(self, command):
        self.exec_calls.append(command)
        return (
            None,
            FakeStream(b"stdout-data", exit_code=7),
            FakeStream(b"stderr-data"),
        )

    def open_sftp(self):
        return self.sftp

    def close(self):
        self.closed = True


@pytest.fixture
def fake_paramiko_client(monkeypatch):
    client = FakeParamikoClient()
    monkeypatch.setattr("cloak_manager.ssh.paramiko.SSHClient", lambda: client)
    monkeypatch.setattr("cloak_manager.ssh.paramiko.AutoAddPolicy", FakeAutoAddPolicy)
    return client


def test_parse_host_returns_username_and_hostname(fake_paramiko_client):
    client = SSHClient("root@router.local")

    assert client._parse_host() == ("root", "router.local")


@pytest.mark.parametrize("host", ["router.local", "@router.local", "root@"])
def test_parse_host_rejects_invalid_format(fake_paramiko_client, host):
    client = SSHClient(host)

    with pytest.raises(SSHError, match="ROUTER_HOST must be in the format username@hostname"):
        client._parse_host()


def test_connect_with_key_auth_uses_default_credentials(fake_paramiko_client):
    client = SSHClient("root@router.local")

    client.connect()

    assert isinstance(fake_paramiko_client.policy, FakeAutoAddPolicy)
    assert fake_paramiko_client.connect_kwargs == {
        "hostname": "router.local",
        "username": "root",
        "timeout": 10,
    }


def test_connect_with_password_auth_passes_password_options(fake_paramiko_client):
    client = SSHClient("root@router.local", auth_method="password", password="secret")

    client.connect()

    assert fake_paramiko_client.connect_kwargs == {
        "hostname": "router.local",
        "username": "root",
        "timeout": 10,
        "password": "secret",
        "look_for_keys": False,
        "allow_agent": False,
    }


def test_connect_rejects_missing_password(fake_paramiko_client):
    client = SSHClient("root@router.local", auth_method="password")

    with pytest.raises(
        SSHError,
        match="Password authentication selected, but no router password was provided",
    ):
        client.connect()


def test_connect_wraps_paramiko_errors(fake_paramiko_client):
    fake_paramiko_client.connect_error = OSError("network down")
    client = SSHClient("root@router.local")

    with pytest.raises(SSHError, match="Failed to connect to root@router.local: network down"):
        client.connect()


def test_exec_returns_stdout_stderr_and_exit_code(fake_paramiko_client):
    client = SSHClient("root@router.local")

    result = client.exec("uname -m")

    assert fake_paramiko_client.exec_calls == ["uname -m"]
    assert result == {
        "stdout": "stdout-data",
        "stderr": "stderr-data",
        "exit_code": 7,
    }


def test_upload_text_writes_remote_file(fake_paramiko_client):
    client = SSHClient("root@router.local")

    client.upload_text("/etc/cloak/test.json", "payload")

    assert fake_paramiko_client.sftp.opened_files == [
        ("/etc/cloak/test.json", "w", "payload")
    ]
    assert fake_paramiko_client.sftp.closed is True


def test_upload_file_uses_sftp_put(fake_paramiko_client):
    client = SSHClient("root@router.local")

    client.upload_file("local.bin", "/tmp/remote.bin")

    assert fake_paramiko_client.sftp.put_calls == [("local.bin", "/tmp/remote.bin")]
    assert fake_paramiko_client.sftp.closed is True


def test_close_closes_underlying_client(fake_paramiko_client):
    client = SSHClient("root@router.local")

    client.close()

    assert fake_paramiko_client.closed is True
