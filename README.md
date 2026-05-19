# cloak-manager

`cloak-manager` is a lightweight CLI for deploying the Cloak client to OpenWRT routers over SSH.

It reads router and service parameters from `.env` inventory files, renders the required Cloak and init script templates, uploads the artifacts to the router, and manages the resulting OpenWRT service.

## Features

- install Cloak on an OpenWRT router
- update an existing service
- remove a previously installed service
- inspect installed Cloak services
- check a service status
- support SSH key and password authentication
- render router-specific config from inventory files
- cache downloaded Cloak binaries locally

## Project layout

```text
cloak-manager/
├── cloak_manager.py
├── cloak_manager/
│   ├── config.py
│   ├── constants.py
│   ├── installer.py
│   ├── models.py
│   ├── renderer.py
│   ├── router.py
│   └── ssh.py
├── inventory/
│   └── home.env.example
├── templates/
│   ├── ckclient.json.j2
│   └── init.d.j2
├── tests/
├── Makefile
├── requirements.txt
└── requirements-dev.txt
```

## Installation

For regular CLI usage:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

For development and tests:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
```

## Inventory format

Copy [inventory/home.env.example](inventory/home.env.example) and fill in your real router and Cloak values.

Required variables:

- `ROUTER_HOST` in `username@hostname` format
- `SERVICE_NAME`
- `CLOAK_VERSION`
- `VPS_IP`
- `REMOTE_PORT`
- `LOCAL_PORT`
- `TRANSPORT` as `tcp` or `udp`
- `UID_VALUE`
- `PUBLIC_KEY`
- `SERVER_NAME`

Optional variables:

- `ROUTER_AUTH_METHOD` as `key` or `password` (defaults to `key`)
- `ROUTER_PASSWORD` for non-interactive password auth

Example:

```env
ROUTER_HOST=root@192.168.8.1
ROUTER_AUTH_METHOD=key
# ROUTER_PASSWORD=

SERVICE_NAME=cloak-office

CLOAK_VERSION=v2.12.0

VPS_IP=1.2.3.4
REMOTE_PORT=443
LOCAL_PORT=1984

TRANSPORT=tcp

UID_VALUE=xxxxxxxx
PUBLIC_KEY=yyyyyyyy

SERVER_NAME=dzen.ru
```

## Supported workflows

Typical usage scenarios:

1. Install a new Cloak service on a router:

```bash
.venv/bin/python cloak_manager.py install inventory/home.env
```

2. Check what Cloak services are already present:

```bash
.venv/bin/python cloak_manager.py list inventory/home.env
```

3. Verify whether a configured service is running:

```bash
.venv/bin/python cloak_manager.py status inventory/home.env
```

4. Update an existing Cloak service after changing version or config:

```bash
.venv/bin/python cloak_manager.py update inventory/home.env
```

5. Remove a service from the router:

```bash
.venv/bin/python cloak_manager.py remove inventory/home.env
```

## Authentication

Two SSH authentication modes are supported:

- `ROUTER_AUTH_METHOD=key`: use the local SSH key configuration
- `ROUTER_AUTH_METHOD=password`: use a router password

With password authentication you can either:

- store `ROUTER_PASSWORD` in the inventory file
- omit `ROUTER_PASSWORD` and enter it interactively when the command starts

## Validation and tests

Safe local validation commands:

```bash
.venv/bin/python -m compileall cloak_manager.py cloak_manager
.venv/bin/python cloak_manager.py --help
```

Run the pytest suite:

```bash
.venv/bin/python -m pytest
make test
```

Run tests with coverage and enforce the minimum threshold:

```bash
.venv/bin/python -m pytest --cov=. --cov-config=.coveragerc --cov-report=term-missing --cov-fail-under=80
make coverage
```

## Notes

- `install`, `update`, and `remove` change state on a real router.
- `cache/` stores downloaded Cloak binaries and should not be committed.
- SSH access can fail in sandboxed or offline environments even when the code is correct.
