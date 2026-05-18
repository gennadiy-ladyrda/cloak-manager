from pathlib import Path
from urllib.request import urlretrieve

from rich.console import Console

from cloak_manager.constants import CLOAK_RELEASE_BASE_URL
from cloak_manager.renderer import render_template
from cloak_manager.router import Router


console = Console()


class Installer:
    def __init__(self, ssh_client, inventory):
        self.ssh = ssh_client
        self.inventory = inventory
        self.router = Router(ssh_client)

    def install(self):
        console.print("[green]Checking router[/green]")

        self.router.check_disk_space()

        if self.router.service_exists(self.inventory.service_name):
            raise Exception(
                f"Service {self.inventory.service_name} already exists"
            )

        arch = self.router.detect_architecture()

        console.print(f"[green]Detected architecture:[/green] {arch}")

        binary_path = self.download_cloak_binary(arch)

        self.upload_binary(binary_path)

        self.install_config()

        self.install_service()

        self.enable_service()

    def download_cloak_binary(self, arch: str):
        cache_dir = Path("cache")
        cache_dir.mkdir(exist_ok=True)

        filename = (
            f"ck-client-linux-{arch}-{self.inventory.cloak_version}"
        )

        local_path = cache_dir / filename

        if local_path.exists():
            console.print("[yellow]Using cached binary[/yellow]")
            return str(local_path)

        url = (
            f"{CLOAK_RELEASE_BASE_URL}/"
            f"{self.inventory.cloak_version}/"
            f"{filename}"
        )

        console.print(f"Downloading {url}")

        urlretrieve(url, local_path)

        return str(local_path)

    def upload_binary(self, binary_path: str):
        console.print("[green]Uploading binary[/green]")

        self.ssh.upload_file(binary_path, "/tmp/ck-client")

        self.ssh.exec("chmod +x /tmp/ck-client")

        self.ssh.exec("mv /tmp/ck-client /usr/sbin/ck-client")

    def install_config(self):
        console.print("[green]Installing config[/green]")

        self.ssh.exec("mkdir -p /etc/cloak")

        config = render_template(
            "ckclient.json.j2",
            vars(self.inventory),
        )

        self.ssh.upload_text(
            f"/etc/cloak/{self.inventory.service_name}.json",
            config,
        )

    def install_service(self):
        console.print("[green]Installing service[/green]")

        init_script = render_template(
            "init.d.j2",
            vars(self.inventory),
        )

        service_path = f"/etc/init.d/{self.inventory.service_name}"

        self.ssh.upload_text(service_path, init_script)

        self.ssh.exec(f"chmod +x {service_path}")

    def enable_service(self):
        console.print("[green]Enabling service[/green]")

        service_name = self.inventory.service_name

        self.ssh.exec(f"/etc/init.d/{service_name} enable")
        self.ssh.exec(f"/etc/init.d/{service_name} restart")
