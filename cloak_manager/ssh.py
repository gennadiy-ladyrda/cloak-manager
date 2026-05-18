import paramiko


class SSHClient:
    def __init__(self, host: str):
        self.host = host

        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def connect(self):
        username, hostname = self.host.split("@")

        self.client.connect(
            hostname=hostname,
            username=username,
        )

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
