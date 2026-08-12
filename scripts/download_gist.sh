#!/usr/bin/env bash
#
# Download GIST 1M dataset from the official INRIA Texmex FTP mirror.
# (The HTTP site corpus-texmex.irisa.fr returns 404 as of 2026-08; the FTP
#  server ftp.irisa.fr/local/texmex/corpus/ is the live official source.)
# Produces: raw/gist_base.fvecs, raw/gist_query.fvecs, raw/gist_learn.fvecs,
#            raw/gist_groundtruth.ivecs
#
# Usage: ./download_gist.sh [--force]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RAW_DIR="$SCRIPT_DIR/../gist/raw"
URL="ftp://ftp.irisa.fr/local/texmex/corpus/gist.tar.gz"
TARBALL="$RAW_DIR/gist.tar.gz"

# Idempotency check
if [[ "${1:-}" != "--force" ]] && [[ -f "$RAW_DIR/gist_base.fvecs" ]] && [[ -f "$RAW_DIR/gist_query.fvecs" ]]; then
    echo "[download_gist] Raw files already exist, skipping. Use --force to re-download."
    exit 0
fi

mkdir -p "$RAW_DIR"

# Download with retries
MAX_RETRIES=3
for i in $(seq 1 $MAX_RETRIES); do
    echo "[download_gist] Attempt $i/$MAX_RETRIES: downloading $URL"
    if curl -L --retry 3 --retry-delay 5 --max-time 3600 \
        -o "$TARBALL" "$URL" 2>&1; then
        break
    fi
    if [[ $i -eq $MAX_RETRIES ]]; then
        echo "[download_gist] ERROR: Failed to download after $MAX_RETRIES attempts"
        exit 1
    fi
    sleep $((2 ** i))
done

SIZE=$(stat -c%s "$TARBALL" 2>/dev/null || stat -f%z "$TARBALL" 2>/dev/null)
if [[ "$SIZE" -lt 100000000 ]]; then
    echo "[download_gist] ERROR: Tarball too small ($SIZE bytes). Download may be corrupt."
    exit 1
fi
echo "[download_gist] Downloaded tarball: $SIZE bytes"

echo "[download_gist] Extracting..."
tar -xzf "$TARBALL" -C "$RAW_DIR"

# The official texmex tarball extracts into a `gist/` subdirectory. Hoist the
# raw fvecs/ivecs up to RAW_DIR so downstream (Makefile/slice_dataset.py)
# finds them flat.
find "$RAW_DIR" -maxdepth 2 -type f \( -name 'gist_base.fvecs' -o -name 'gist_query.fvecs' \
    -o -name 'gist_learn.fvecs' -o -name 'gist_groundtruth.ivecs' \) \
    -exec mv -f {} "$RAW_DIR/" \;

EXPECTED=("gist_base.fvecs" "gist_query.fvecs" "gist_learn.fvecs" "gist_groundtruth.ivecs")
for f in "${EXPECTED[@]}"; do
    if [[ ! -f "$RAW_DIR/$f" ]]; then
        echo "[download_gist] ERROR: Expected file not found after extract: $f"
        exit 1
    fi
    esize=$(stat -c%s "$RAW_DIR/$f" 2>/dev/null || stat -f%z "$RAW_DIR/$f" 2>/dev/null)
    echo "[download_gist]   $f: $esize bytes"
done

echo "[download_gist] Done."
