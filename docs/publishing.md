# Publishing `alloc-context` to PyPI

Use this checklist for the first public release and version bumps. PyPI makes the
stdio MCP installable as `pip install alloc-context` and backs the `packages`
entry in [`server.json`](../server.json) for the MCP Registry.

## Prerequisites

- PyPI account with a trusted publishing API token (or OIDC via GitHub Actions)
- Clean `main` with passing CI (`pytest -q`)
- Version bumped in **`pyproject.toml`** and **`server.json`** (keep in sync)

## Version bump

Edit both files, for example `0.1.0` → `0.1.1`:

- `pyproject.toml` → `[project].version`
- `server.json` → top-level `version` and `packages[0].version`

Tag after merge (optional but recommended):

```bash
git tag -s v0.1.0 -m "Release 0.1.0"
git push origin v0.1.0
```

## Build and upload (manual)

```bash
cd alloc-context
python3.11 -m venv .venv && source .venv/bin/activate
pip install -U build twine
rm -rf dist/
python -m build
twine check dist/*
twine upload dist/*
```

`twine upload` prompts for username `__token__` and password = API token.

## Verify

```bash
pip install alloc-context==0.1.0
alloc-context --help
pip install "alloc-context[mcp]"
alloc-context mcp --help
```

Confirm the [PyPI project page](https://pypi.org/project/alloc-context/) shows:

- Description from `README.md` (hosted MCP block at top)
- Keywords and classifiers from `pyproject.toml`
- **MCP Server** URL → `https://mcp.alloc-context.com/mcp`

## After PyPI publish

1. Publish or refresh the MCP Registry entry (`mcp-publisher publish`) — see
   [distribution.md](distribution.md).
2. Wait for directory mirrors (PulseMCP, Smithery) or submit manually if needed.

## CI publishing (optional)

A future GitHub Actions workflow can upload on signed tags using
`PYPI_API_TOKEN` as a repository secret. Until that exists, use manual `twine`
upload as above.
