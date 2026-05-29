# Publishing `alloc-context` to PyPI

Releases are automated on version tags (`v*`). Pushing a tag runs tests,
tests, publishes to PyPI, and deploys to the production VPS (replacing the old
`main`-branch deploy for this repository). The operator repo still deploys on
`main` push.

## Prerequisites

- Versions aligned in **`pyproject.toml`**, **`server.json`**, and
  **`alloccontext/__init__.py`** (via `scripts/bump_version.py`)
- Clean `main` with passing CI (`pytest -q`)
- **PyPI trusted publisher** configured for this repo (one-time):
  - PyPI → Your projects → *alloc-context* → Publishing → Add a new publisher
  - Owner: `negillett`, repository: `alloc-context`, workflow: `release.yml`,
    environment: *(leave blank)*
- Existing VPS secrets (`VPS_SSH_KEY`, `VPS_HOST`) — same as self-hosting

## Release flow (automated)

**Recommended:** GitHub Actions → **bump-release** → Run workflow.

1. Choose **patch**, **minor**, or **major** (or set **exact_version**).
2. The workflow bumps all version files, commits to `main`, pushes tag `vX.Y.Z`.
3. The **release** workflow runs on that tag (PyPI + VPS).

Files kept in sync by `scripts/bump_version.py`:

- `pyproject.toml`
- `server.json` (top-level and `packages[0].version`)
- `alloccontext/__init__.py` (`__version__`)

### Local bump and tag

```bash
cd alloc-context
python3 scripts/bump_version.py --bump patch --write
git add pyproject.toml server.json alloccontext/__init__.py
git commit -m "Bump version to 0.1.1."
git tag -s v0.1.1 -m "Release 0.1.1"
git push origin main && git push origin v0.1.1
```

Dry-run: `python3 scripts/bump_version.py --bump minor` (omit `--write`).

Exact version: `python3 scripts/bump_version.py 0.2.0 --write --print`

The **release** workflow then:

- runs `pytest`
- verifies tag `vX.Y.Z` matches package versions
- builds and uploads to PyPI (OIDC — no `PYPI_API_TOKEN` secret)
- rsyncs to VPS, runs `remote-install.sh`, smoke, and x402 check

Watch the run: Actions → **release** → your tag.

## Verify PyPI

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

## Manual upload (break-glass)

If CI publish fails:

```bash
cd alloc-context
python3.11 -m venv .venv && source .venv/bin/activate
pip install -U build twine
rm -rf dist/
python -m build
twine check dist/*
twine upload dist/*
```

Use username `__token__` and a PyPI API token as the password.

## VPS-only deploy (no PyPI)

For hotfixes without a version bump, use break-glass rsync — see
[self-hosting.md](self-hosting.md).
