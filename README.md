# cloak-manager — deployment tool for Cloak/OpenWRT

## Project structure

```text
cloak-manager/
├── README.md
├── requirements.txt
├── cloak_manager.py
├── inventory/
│   ├── home.env
│   └── office.env
├── templates/
│   ├── ckclient.json.j2
│   └── init.d.j2
├── cache/
└── cloak_manager/
    ├── __init__.py
    ├── config.py
    ├── ssh.py
    ├── router.py
    ├── installer.py
    ├── renderer.py
    ├── models.py
    └── constants.py
```



# README.md

````markdown
# cloak-manager

Tool for automated Cloak deployment on OpenWRT routers.

## Features

- automatic architecture detection
- multi-service support
- TCP/UDP support
- interactive mode
- .env inventory support
- update mode
- status/list/remove/install
- Cloak binary caching
- OpenWRT procd integration

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Example inventory

```bash
ROUTER_HOST=root@192.168.8.1

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

## Commands

```bash
python cloak_manager.py install inventory/home.env
python cloak_manager.py list inventory/home.env
python cloak_manager.py status inventory/home.env
python cloak_manager.py remove inventory/home.env
python cloak_manager.py update inventory/home.env
```


# Следующие шаги

После создания базовой версии я бы рекомендовал добавить:

1. interactive wizard
2. update command
3. remove command
4. status command
5. OpenVPN config patching
6. binary checksum validation
7. dry-run mode
8. rollback support
9. structured logging
10. router inventory management
11. YAML inventory support
12. automatic architecture fallback
13. parallel deployment to multiple routers
14. CI pipeline
15. packaging via poetry
