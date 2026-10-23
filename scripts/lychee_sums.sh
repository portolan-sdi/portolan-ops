#!/usr/bin/env bash
# Rewrite the pinned SHA-256 sums in scripts/lychee.sh for its LYCHEE_VERSION.
#
# Renovate bumps LYCHEE_VERSION through the `# renovate:` comment and then
# runs this script as a post-upgrade task, so the version and the sums move
# in one commit. Each sum comes from the .sha256 asset that the lychee
# release publishes beside the archive. Pass a path to rewrite another copy
# of the wrapper. The default is the copy next to this script.
set -euo pipefail

file=${1:-"$(dirname "${BASH_SOURCE[0]}")/lychee.sh"}

version=$(sed -n 's/^LYCHEE_VERSION=//p' "$file")
if [ -z "$version" ]; then
  echo "No LYCHEE_VERSION line in $file." >&2
  exit 1
fi

triples="x86_64-unknown-linux-gnu aarch64-unknown-linux-gnu"
triples="$triples x86_64-apple-darwin aarch64-apple-darwin"

base="https://github.com/lycheeverse/lychee/releases/download/lychee-v$version"
for triple in $triples; do
  sum=$(curl --fail --silent --show-error --location --retry 3 \
    "$base/lychee-$triple.tar.gz.sha256" | cut -d' ' -f1)
  if ! printf '%s' "$sum" | grep -Eq '^[0-9a-f]{64}$'; then
    echo "No SHA-256 for lychee $version ($triple)." >&2
    exit 1
  fi
  # The sum sits on the line after the triple's case label.
  sed -i.bak "/^    $triple)\$/{n;s/[0-9a-f]\{64\}/$sum/;}" "$file"
  rm -f "$file.bak"
done

sed -i.bak "s/assets of release lychee-v[^ ]*\.\$/assets of release lychee-v$version./" "$file"
rm -f "$file.bak"
