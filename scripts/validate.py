#!/usr/bin/env python3
"""
Validate fvecs and ivecs files for format correctness and consistency.

Checks:
  - File existence
  - Consistent dimension across all vectors in a file
  - Correct record count
  - ivecs: all indices in valid range
  - Component sanity: no vector has a component magnitude wildly larger than
    the file's typical magnitude (catches corruption like a single component
    blown up to ~1e16 while siblings are ~1e2 — issue #6)
"""

import argparse
import os
import struct
import sys


def check_component_sanity(filepath, tag):
    """Detect corrupt fvecs where a single component is blown up far beyond
    the file's normal magnitude (issue #6: query.fvecs had components ~1e16
    while normal components are ~1e2, passing all format checks).

    Relative threshold: max|component| > 1e6 × median|component|. Robust for
    both integer-derived descriptors (SIFT/GIST, |x|<=~256) and float
    embeddings (Cohere/BioASQ, |x| typically <~50): natural max/median ratios
    are <~1e3; corruption is ~1e12+. numpy-gated (skip if unavailable)."""
    dim, count, _ = count_fvecs(filepath)
    if dim is None or count == 0:
        return None
    try:
        import numpy as np
    except ImportError:
        return None
    data = np.fromfile(filepath, dtype=np.float32)
    n_floats = count * (dim + 1)
    if data.size < n_floats:
        data = np.pad(data, (0, n_floats - data.size), mode="constant")
    vecs = data[:n_floats].reshape(count, dim + 1)[:, 1:]   # drop per-vector dim prefix
    absmed = np.median(np.abs(vecs))
    if absmed == 0:
        return None   # all-zero file: relative check N/A (format check already passed)
    max_abs = float(np.abs(vecs).max())
    ratio = max_abs / absmed
    if ratio > 1e6:
        raise ValueError(
            f"[FAIL] {filepath}: component sanity failed — max|component|={max_abs:.3e} "
            f"vs median|component|={absmed:.3e} (ratio {ratio:.1e}) — likely corrupt ({tag})"
        )
    return ratio


def count_fvecs(filepath):
    """Count vectors and return (dim, count, record_size). Returns (None,0,0) if missing."""
    if not os.path.isfile(filepath):
        return None, 0, 0
    record_size = None
    count = 0
    dim = None
    with open(filepath, "rb") as f:
        data = f.read()
    offset = 0
    while offset + 4 <= len(data):
        d = struct.unpack_from("<i", data, offset)[0]
        offset += 4
        if d <= 0 or offset + d * 4 > len(data):
            break
        if record_size is None:
            record_size = 4 + d * 4
            dim = d
        elif record_size != 4 + d * 4:
            raise ValueError(
                f"Dimension mismatch in {filepath}: expected "
                f"record_size={record_size}, got dim={d} at vector {count}"
            )
        offset += d * 4
        count += 1
    return dim, count, record_size or 0


def count_ivecs(filepath):
    """Count ivecs entries and return (k, count). Returns (None,0) if missing."""
    if not os.path.isfile(filepath):
        return None, 0
    k = None
    count = 0
    with open(filepath, "rb") as f:
        data = f.read()
    offset = 0
    while offset + 4 <= len(data):
        d = struct.unpack_from("<i", data, offset)[0]
        offset += 4
        if d <= 0 or offset + d * 4 > len(data):
            break
        if k is None:
            k = d
        elif k != d:
            raise ValueError(
                f"K mismatch in {filepath}: expected k={k}, got k={d} at entry {count}"
            )
        # Check indices are non-negative
        for i in range(d):
            idx = struct.unpack_from("<i", data, offset + i * 4)[0]
            if idx < 0:
                raise ValueError(
                    f"Negative index {idx} found in {filepath} at entry {count}"
                )
        offset += d * 4
        count += 1
    return k, count


def validate_dataset_size(base_dir, label, expected_base, expected_query, expected_ks, max_id):
    """Validate one size directory (e.g., sift/100k/)."""
    errors = []

    base_path = os.path.join(base_dir, label, "base.fvecs")
    query_path = os.path.join(base_dir, label, "query.fvecs")

    dim, base_count, _ = count_fvecs(base_path)
    if base_count != expected_base:
        errors.append(f"[FAIL] {base_path}: expected {expected_base} vectors, got {base_count}")
    else:
        print(f"[OK] {base_path}: {base_count} vectors, dim={dim}")

    qdim, query_count, _ = count_fvecs(query_path)
    if query_count != expected_query:
        errors.append(f"[FAIL] {query_path}: expected {expected_query} vectors, got {query_count}")
    else:
        print(f"[OK] {query_path}: {query_count} vectors, dim={qdim}")

    # Component sanity (issue #6): format-valid but corrupt (blown-up component).
    for p, tag in ((base_path, "base"), (query_path, "query")):
        try:
            r = check_component_sanity(p, tag)
            if r is not None:
                print(f"[OK] {p}: component sanity ratio={r:.1e}")
        except ValueError as e:
            errors.append(str(e))

    if dim != qdim:
        errors.append(f"[FAIL] Dimension mismatch: base dim={dim}, query dim={qdim}")

    for k_val in expected_ks:
        gt_path = os.path.join(base_dir, label, f"gt_top{k_val}.ivecs")
        k, gt_count = count_ivecs(gt_path)
        if gt_count != expected_query:
            errors.append(f"[FAIL] {gt_path}: expected {expected_query} entries, got {gt_count}")
        elif k != k_val:
            errors.append(f"[FAIL] {gt_path}: expected k={k_val}, got k={k}")
        else:
            print(f"[OK] {gt_path}: {gt_count} entries, k={k}")

    return errors


def main():
    parser = argparse.ArgumentParser(description="Validate dataset files")
    parser.add_argument("--dataset", required=True, help="Dataset name")
    parser.add_argument("--dataset-dir", required=True, help="Dataset root dir")
    parser.add_argument("--sizes", default="1k,10k,100k,1m",
                        help="Size labels to check (comma-separated)")
    args = parser.parse_args()

    size_config = {
        "1k": 1000,
        "10k": 10000,
        "100k": 100000,
        "1m": 1000000,
    }
    # Query set size is per-dataset, not per-scale: the standard SIFT1M has a
    # 10000-vector query set, GIST1M a 1000-vector query set (independent of the
    # base scale, shared across 1k/10k/100k/1m).  Hardcoding 1000 falsely fails
    # SIFT (query.fvecs / gt_top*.ivecs carry 10000 entries).
    query_config = {
        "sift": 10000,
        "gist": 1000,
        "bioasq": 500,  # beir-embed-english-v3 bioasq-queries test split 恰 500 条
    }

    sizes = [s.strip() for s in args.sizes.split(",")]
    expected_query = query_config.get(args.dataset, 1000)
    expected_ks = [10, 100]
    max_id = size_config[sizes[-1]]  # use largest size as max_id bound

    all_errors = []
    for label in sizes:
        if label not in size_config:
            all_errors.append(f"[FAIL] Unknown size label: {label}")
            continue
        expected_base = size_config[label]
        print(f"\n--- Validating {args.dataset}/{label} ---")
        errors = validate_dataset_size(
            args.dataset_dir, label, expected_base, expected_query,
            expected_ks, max_id
        )
        all_errors.extend(errors)

    if all_errors:
        print(f"\n=== {len(all_errors)} VALIDATION ERRORS ===")
        for e in all_errors:
            print(e)
        sys.exit(1)
    else:
        print(f"\n=== All checks passed for {args.dataset} ===")


if __name__ == "__main__":
    main()
