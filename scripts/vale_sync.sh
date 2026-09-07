#!/usr/bin/env bash
# Fetch the pinned Vale style packages, and retry a transient failure.
#
# `vale sync` downloads every package in `Packages` from a GitHub release. It
# stops at the first failure and exits non-zero. GitHub answers a release
# download with 504 often enough to fail a correct pull request. See issue #92.
#
# A retry absorbs a short outage. A package that stays unreachable still fails
# the run, and the vale output names the package and the status code.
set -euo pipefail

attempts=${VALE_SYNC_ATTEMPTS:-3}
wait_seconds=${VALE_SYNC_WAIT:-5}

for attempt in $(seq 1 "$attempts"); do
  if vale sync; then
    exit 0
  fi
  if [ "$attempt" -eq "$attempts" ]; then
    echo "vale sync failed after $attempts attempts." >&2
    exit 1
  fi
  echo "vale sync failed on attempt $attempt. Retrying in ${wait_seconds}s." >&2
  sleep "$wait_seconds"
  wait_seconds=$((wait_seconds * 2))
done
