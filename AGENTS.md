# AGENTS.md

## Purpose

`cloak-manager` is a small CLI utility for deploying the Cloak client to OpenWRT routers over SSH.

The main entrypoint is `cloak_manager.py`. The repository uses `.env` inventory files from `inventory/` and Jinja templates from `templates/`.

## Repository Map

- `cloak_manager.py`: CLI entrypoint and command dispatch
- `cloak_manager/config.py`: inventory loading and validation
- `cloak_manager/ssh.py`: SSH wrapper around Paramiko
- `cloak_manager/router.py`: router inspection and service management helpers
- `cloak_manager/installer.py`: install and update workflow
- `cloak_manager/renderer.py`: Jinja template rendering
- `templates/`: OpenWRT init script and Cloak config templates
- `inventory/`: local inventory files, may contain secrets

## Local Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Common Commands

```bash
.venv/bin/python cloak_manager.py --help
.venv/bin/python cloak_manager.py list inventory/home.env
.venv/bin/python cloak_manager.py status inventory/home.env
.venv/bin/python -m compileall cloak_manager.py cloak_manager
make check
```

## Working Rules For Agents

1. Read `README.md` and this file before making non-trivial changes.
2. Assume `inventory/*.env` can contain secrets and real infrastructure endpoints.
3. Do not modify `inventory/home.env` unless the user explicitly asks.
4. Treat `install`, `update`, and `remove` as state-changing commands against a real router.
5. Prefer validation that does not require network access: `compileall`, `--help`, template rendering, and focused module checks.
6. Keep changes small and local; this project is intentionally lightweight and does not use a large framework.
7. When changing CLI behavior, keep `README.md`, `Makefile`, and command help aligned.

## Validation Checklist

- Python files compile successfully.
- `cloak_manager.py --help` reflects available commands.
- Template changes render for both TCP and UDP cases when relevant.
- New docs reference real file paths and current commands.

## Notes

- SSH access may fail in sandboxed environments even when the code is correct.
- `cache/` stores downloaded Cloak binaries and should not be committed.
