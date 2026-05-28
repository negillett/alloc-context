#!/usr/bin/env bash
# Run x402 production checks on the VPS via SSH (CI and local ops).
set -euo pipefail

VPS_HOST="${VPS_HOST:?VPS_HOST is required}"
VPS_USER="${VPS_USER:-root}"
SSH_KEY="${DEPLOY_SSH_KEY:-${HOME}/.ssh/deploy_key}"
CORE_REMOTE="${ALLOC_CONTEXT_REMOTE:-/opt/trading/alloc-context}"
ENV_FILE="${ALLOC_CONTEXT_ENV_FILE:-/opt/trading/shared/.env}"

remote_cmd="set -a && source \"${ENV_FILE}\" && set +a && \
if [[ \"\${X402_ENABLED:-}\" != \"true\" ]]; then \
  echo \"SKIP: X402_ENABLED is not true\"; exit 0; fi && \
cd \"${CORE_REMOTE}\" && .venv/bin/python scripts/x402-production-check.py"

ssh -i "${SSH_KEY}" -o IdentitiesOnly=yes \
  "${VPS_USER}@${VPS_HOST}" \
  "sudo -u trading bash -lc $(printf '%q' "${remote_cmd}")"
