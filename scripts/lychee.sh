#!/usr/bin/env bash
# Run the pinned lychee link checker with the org rules.
#
# CI (reusable-links.yml) and the `lychee` pre-commit hook both call this
# script, so a commit and a pull request apply the same rules. Arguments pass
# through to lychee. The script adds:
#
#   - the org rules in lychee/org.toml in the portolan-ops checkout
#   - the repo's own lychee.toml, when the working directory has one
#   - --root-dir, so an absolute link like /img/a.png resolves. The root is
#     public/ when that directory exists (Vite and Next.js serve it at /).
#     Otherwise it is the working directory. LYCHEE_ROOT_DIR overrides it.
#
# The binary comes from the lychee GitHub release. The script checks it
# against the SHA-256 below before it runs it, and caches it per version.
# LYCHEE_BIN skips the download and uses the binary it names.
set -euo pipefail

LYCHEE_VERSION=0.24.2

ops_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

target() {
  case "$(uname -s)-$(uname -m)" in
    Linux-x86_64) echo x86_64-unknown-linux-gnu ;;
    Linux-aarch64 | Linux-arm64) echo aarch64-unknown-linux-gnu ;;
    Darwin-x86_64) echo x86_64-apple-darwin ;;
    Darwin-arm64) echo aarch64-apple-darwin ;;
    *) return 1 ;;
  esac
}

# The sums come from the .sha256 assets of release lychee-v0.24.2.
checksum() {
  case "$1" in
    x86_64-unknown-linux-gnu)
      echo 1f4e0ef7f6554a6ed33dd7ac144fb2e1bbed98598e7af973042fc5cd43951c9a ;;
    aarch64-unknown-linux-gnu)
      echo 91a7bd65685da41b90ccb9bc867a3d649a7818042dae04ff405e55a25bddee4c ;;
    x86_64-apple-darwin)
      echo 887503a9cff667d322b8d0892b40bf49976eb9507af8483220a3706cdad55978 ;;
    aarch64-apple-darwin)
      echo c9d3740ea2d891854d37116c9fba840f37b6e7c89d330e7db84ac333631c4977 ;;
  esac
}

sha256() {
  if command -v sha256sum > /dev/null; then
    sha256sum "$1" | cut -d' ' -f1
  else
    shasum -a 256 "$1" | cut -d' ' -f1
  fi
}

install_lychee() {
  local triple="$1" dest="$2"
  local name="lychee-$triple"
  local url="https://github.com/lycheeverse/lychee/releases/download/lychee-v$LYCHEE_VERSION/$name.tar.gz"
  work=$(mktemp -d)
  trap 'rm -rf "$work"' EXIT

  echo "Installing lychee $LYCHEE_VERSION ($triple)." >&2
  curl --fail --silent --show-error --location \
    --retry 3 --retry-all-errors --output "$work/$name.tar.gz" "$url"

  local want got
  want=$(checksum "$triple")
  got=$(sha256 "$work/$name.tar.gz")
  if [ "$got" != "$want" ]; then
    echo "lychee $LYCHEE_VERSION checksum mismatch for $triple." >&2
    echo "  want $want" >&2
    echo "  got  $got" >&2
    return 1
  fi

  tar -xzf "$work/$name.tar.gz" -C "$work" "$name/lychee"
  mkdir -p "$(dirname "$dest")"
  install -m 0755 "$work/$name/lychee" "$dest"
  rm -rf "$work"
  trap - EXIT
}

if [ -n "${LYCHEE_BIN:-}" ]; then
  lychee=$LYCHEE_BIN
else
  if ! triple=$(target); then
    echo "No pinned lychee build for $(uname -s) $(uname -m)." >&2
    echo "Set LYCHEE_BIN to a lychee $LYCHEE_VERSION binary." >&2
    exit 1
  fi
  cache=${LYCHEE_CACHE_DIR:-${XDG_CACHE_HOME:-$HOME/.cache}/portolan-lychee}
  lychee="$cache/$LYCHEE_VERSION/$triple/lychee"
  if [ ! -x "$lychee" ]; then
    install_lychee "$triple" "$lychee"
  fi
fi

configs=(--config "$ops_dir/lychee/org.toml")
if [ -f lychee.toml ]; then
  configs+=(--config lychee.toml)
fi

if [ -n "${LYCHEE_ROOT_DIR:-}" ]; then
  root=$(cd "$LYCHEE_ROOT_DIR" && pwd)
elif [ -d public ]; then
  root="$PWD/public"
else
  root=$PWD
fi

exec "$lychee" "${configs[@]}" --root-dir "$root" "$@"
