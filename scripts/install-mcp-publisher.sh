#!/usr/bin/env bash
# Download the official mcp-publisher CLI (MCP Registry).
set -euo pipefail

DEST="${1:-./mcp-publisher}"
ARCH="$(uname -m | sed 's/x86_64/amd64/;s/aarch64/arm64/')"
OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
URL="https://github.com/modelcontextprotocol/registry/releases/latest/download/mcp-publisher_${OS}_${ARCH}.tar.gz"

tmpdir="$(mktemp -d)"
trap 'rm -rf "${tmpdir}"' EXIT

curl -fsSL "${URL}" -o "${tmpdir}/mcp-publisher.tgz"
tar xzf "${tmpdir}/mcp-publisher.tgz" -C "${tmpdir}" mcp-publisher
install -m 755 "${tmpdir}/mcp-publisher" "${DEST}"
echo "installed mcp-publisher -> ${DEST}"
