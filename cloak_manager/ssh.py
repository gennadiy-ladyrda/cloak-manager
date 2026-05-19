import paramiko


class SSHError(Exception):
    pass


class SSHClient:
    def __init__(
        self,
        host: str,
        auth_method: str = "key",
        password: str | None = None,
    ):
        self.host = host
        self.auth_method = auth_method
        self.password = password

        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def connect(self):
        username, hostname = self._parse_host()
        connect_kwargs = {
            "hostname": hostname,
            "username": username,
            "timeout": 10,
        }

        if self.auth_method == "password":
            if not self.password:
                raise SSHError(
                    "Password authentication selected, but no router password was provided"
                )

            connect_kwargs.update(
                {
                    "password": self.password,
                    "look_for_keys": False,
                    "allow_agent": False,
                }
            )

        try:
            self.client.connect(**connect_kwargs)
        except (ValueError, OSError, paramiko.SSHException) as exc:
            raise SSHError(
                f"Failed to connect to {self.host}: {exc}"
            ) from exc

    def exec(self, command: str):
        stdin, stdout, stderr = self.client.exec_command(command)

        return {
            "stdout": stdout.read().decode(),
            "stderr": stderr.read().decode(),
            "exit_code": stdout.channel.recv_exit_status(),
        }

    def upload_text(self, remote_path: str, content: str):
        sftp = self.client.open_sftp()

        with sftp.open(remote_path, "w") as f:
            f.write(content)

        sftp.close()

    def upload_file(self, local_path: str, remote_path: str):
        sftp = self.client.open_sftp()
        sftp.put(local_path, remote_path)
        sftp.close()

    def close(self):
        self.client.close()

    def _parse_host(self):
        if "@" not in self.host:
            raise SSHError(
                "ROUTER_HOST must be in the format username@hostname"
            )

        username, hostname = self.host.split("@", 1)

        if not username or not hostname:
            raise SSHError(
                "ROUTER_HOST must be in the format username@hostname"
            )

        return username, hostname
