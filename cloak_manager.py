import argparse
import sys
from getpass import getpass

from rich.console import Console
from rich.table import Table

from cloak_manager.config import ConfigError, load_inventory
from cloak_manager.installer import Installer
from cloak_manager.router import Router, RouterError
from cloak_manager.ssh import SSHClient, SSHError


console = Console()


def build_ssh_client(inventory):
    password = inventory.router_password

    if inventory.router_auth_method == "password" and not password:
        password = getpass(
            f"Enter SSH password for {inventory.router_host}: "
        )

    return SSHClient(
        inventory.router_host,
        auth_method=inventory.router_auth_method,
        password=password,
    )


def cmd_install(args):
    inventory = load_inventory(args.inventory)

    ssh = build_ssh_client(inventory)
    ssh.connect()

    installer = Installer(ssh, inventory)

    installer.install()

    ssh.close()

    console.print("[green]Installation complete[/green]")


def cmd_list(args):
    inventory = load_inventory(args.inventory)

    ssh = build_ssh_client(inventory)
    ssh.connect()

    router = Router(ssh)

    services = router.check_existing_services()

    table = Table(title="Cloak services")

    table.add_column("Service")

    for service in services:
        table.add_row(service)

    console.print(table)

    ssh.close()


def cmd_status(args):
    inventory = load_inventory(args.inventory)

    ssh = build_ssh_client(inventory)
    ssh.connect()

    router = Router(ssh)
    status = router.get_service_status(inventory.service_name)

    ssh.close()

    console.print(
        f"[green]{inventory.service_name}[/green]: {status}"
    )


def cmd_remove(args):
    inventory = load_inventory(args.inventory)

    ssh = build_ssh_client(inventory)
    ssh.connect()

    router = Router(ssh)
    router.remove_service(inventory.service_name)

    ssh.close()

    console.print("[green]Service removed[/green]")


def cmd_update(args):
    inventory = load_inventory(args.inventory)

    ssh = build_ssh_client(inventory)
    ssh.connect()

    installer = Installer(ssh, inventory)
    installer.update()

    ssh.close()

    console.print("[green]Update complete[/green]")


def main():
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(dest="command")

    install_parser = subparsers.add_parser("install")
    install_parser.add_argument("inventory")

    list_parser = subparsers.add_parser("list")
    list_parser.add_argument("inventory")

    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("inventory")

    remove_parser = subparsers.add_parser("remove")
    remove_parser.add_argument("inventory")

    update_parser = subparsers.add_parser("update")
    update_parser.add_argument("inventory")

    args = parser.parse_args()

    try:
        if args.command == "install":
            cmd_install(args)
        elif args.command == "list":
            cmd_list(args)
        elif args.command == "status":
            cmd_status(args)
        elif args.command == "remove":
            cmd_remove(args)
        elif args.command == "update":
            cmd_update(args)
        else:
            parser.print_help()
            return 1
    except (ConfigError, RouterError, SSHError, Exception) as exc:
        console.print(f"[red]Error:[/red] {exc}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
