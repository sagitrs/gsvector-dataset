#!/usr/bin/env bash
#
# Download SIFT 1M dataset from the official INRIA Texmex FTP mirror.
# (The HTTP site corpus-texmex.irisa.fr returns 404 as of 2026-08; the FTP
#  server ftp.irisa.fr/local/texmex/corpus/ is the live official source.)
# Produces: raw/sift_base.fvecs, raw/sift_query.fvecs, raw/sift_learn.fvecs,
#            raw/sift_groundtruth.ivecs
#
# Usage: ./download_sift.sh [--force]
#   --force  Re-download even if raw files exist
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RAW_DIR="$SCRIPT_DIR/../sift/raw"
URL="ftp://ftp.irisa.fr/local/texmex/corpus/sift.tar.gz"
TARBALL="$RAW_DIR/sift.tar.gz"

# Idempotency check
if [[ "${1:-}" != "--force" ]] && [[ -f "$RAW_DIR/sift_base.fvecs" ]] && [[ -f "$RAW_DIR/sift_query.fvecs" ]]; then
    echo "[download_sift] Raw files already exist, skipping. Use --force to re-download."
    exit 0
fi

mkdir -p "$RAW_DIR"

# Download with retries (3 attempts, exponential backoff)
MAX_RETRIES=3
for i in $(seq 1 $MAX_RETRIES); do
    echo "[download_sift] Attempt $i/$MAX_RETRIES: downloading $URL"
    if curl -L --retry 3 --retry-delay 5 --max-time 1800 \
        -o "$TARBALL" "$URL" 2>&1; then
        break
    fi
    if [[ $i -eq $MAX_RETRIES ]]; then
        echo "[download_sift] ERROR: Failed to download after $MAX_RETRIES attempts"
        exit 1
    fi
    sleep $((2 ** i))
done

# Verify file size (> 100MB to be reasonable)
SIZE=$(stat -c%s "$TARBALL" 2>/dev/null || stat -f%z "$TARBALL" 2>/dev/null)
if [[ "$SIZE" -lt 100000000 ]]; then
    echo "[download_sift] ERROR: Tarball too small ($SIZE bytes). Download may be corrupt."
    exit 1
fi
echo "[download_sift] Downloaded tarball: $SIZE bytes"

# Extract
echo "[download_sift] Extracting..."
tar -xzf "$TARBALL" -C "$RAW_DIR"

# The official texmex tarball extracts into a `sift/` subdirectory. Hoist the
# raw fvecs/ivecs up to RAW_DIR so downstream (Makefile/slice_dataset.py)
# finds them flat.
find "$RAW_DIR" -maxdepth 2 -type f \( -name 'sift_base.fvecs' -o -name 'sift_query.fvecs' \
    -o -name 'sift_learn.fvecs' -o -name 'sift_groundtruth.ivecs' \) \
    -exec mv -f {} "$RAW_DIR/" \;

# Verify extracted files exist
EXPECTED=("sift_base.fvecs" "sift_query.fvecs" "sift_learn.fvecs" "sift_groundtruth.ivecs")
for f in "${EXPECTED[@]}"; do
    if [[ ! -f "$RAW_DIR/$f" ]]; then
        echo "[download_sift] ERROR: Expected file not found after extract: $f"
        exit 1
    fi
    esize=$(stat -c%s "$RAW_DIR/$f" 2>/dev/null || stat -f%z "$RAW_DIR/$f" 2>/dev/null)
    echo "[download_sift]   $f: $esize bytes"
done

echo "[download_sift] Done."
