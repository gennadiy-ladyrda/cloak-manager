import argparse

from rich.console import Console
from rich.table import Table

from cloak_manager.config import load_inventory
from cloak_manager.installer import Installer
from cloak_manager.router import Router
from cloak_manager.ssh import SSHClient


console = Console()


def cmd_install(args):
    inventory = load_inventory(args.inventory)

    ssh = SSHClient(inventory.router_host)
    ssh.connect()

    installer = Installer(ssh, inventory)

    installer.install()

    ssh.close()

    console.print("[green]Installation complete[/green]")


def cmd_list(args):
    inventory = load_inventory(args.inventory)

    ssh = SSHClient(inventory.router_host)
    ssh.connect()

    router = Router(ssh)

    services = router.check_existing_services()

    table = Table(title="Cloak services")

    table.add_column("Service")

    for service in services:
        table.add_row(service)

    console.print(table)

    ssh.close()


def main():
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(dest="command")

    install_parser = subparsers.add_parser("install")
    install_parser.add_argument("inventory")

    list_parser = subparsers.add_parser("list")
    list_parser.add_argument("inventory")

    args = parser.parse_args()

    if args.command == "install":
        cmd_install(args)
    elif args.command == "list":
        cmd_list(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
