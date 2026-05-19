# Contributing

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Development Workflow

1. Keep inventory secrets out of commits.
2. Make focused changes and avoid mixing infrastructure edits with refactors.
3. Run the lightweight checks before finishing:

```bash
make check
```

4. If you change commands or inventory format, update `README.md` and `AGENTS.md`.

## Safety

- `install`, `update`, and `remove` affect a live router.
- Prefer `list` and `status` when you only need read-only verification.
- In sandboxed environments, SSH failures may be environmental rather than code defects.
