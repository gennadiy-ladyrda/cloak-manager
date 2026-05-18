from rich.console import Console

from cloak_manager.constants import SUPPORTED_ARCHES


console = Console()


class RouterError(Exception):
    pass


class Router:
    def __init__(self, ssh_client):
        self.ssh = ssh_client

    def detect_architecture(self):
        result = self.ssh.exec("uname -m")

        arch = result["stdout"].strip()

        if arch not in SUPPORTED_ARCHES:
            raise RouterError(f"Unsupported architecture: {arch}")

        return SUPPORTED_ARCHES[arch]

    def check_disk_space(self):
        result = self.ssh.exec("df -m / | tail -1 | awk '{print $4}'")

        free_mb = int(result["stdout"].strip())

        if free_mb < 20:
            raise RouterError(
                f"Not enough disk space. Only {free_mb} MB available"
            )

        return free_mb

    def check_existing_services(self):
        result = self.ssh.exec(
            "find /etc/init.d -maxdepth 1 -name 'cloak-*' -type f"
        )

        services = []

        for line in result["stdout"].splitlines():
            services.append(line.split("/")[-1])

        return services

    def service_exists(self, service_name: str):
        services = self.check_existing_services()
        return service_name in services
