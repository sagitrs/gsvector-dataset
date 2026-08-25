#!/usr/bin/env python3
"""Deterministic query sampling from a clean base — 仓内口径载体（#6/#11 约定）。

gist/100k（及未来同口径数据集）的 query.fvecs = base 确定性采样：
  rng = numpy.random.default_rng(2026); rng.choice(N, size=Q, replace=False); sel.sort()
GT 基于采样后 query 对 base 精算（float64 L2），query ⊂ base 时**排自命中**
（compute_groundtruth.py --exclude-self）。

可复现保证：同 base oid + 本脚本 → 逐位相同 query/GT。已提交 oid 的复核命令：
  python3 scripts/sample_query.py --base gist/100k/base.fvecs --out /tmp/q.fvecs \
      --num 1000 --seed 2026 && cmp /tmp/q.fvecs gist/100k/query.fvecs && echo IDENTICAL
"""
import argparse
import struct

import numpy as np


def read_fvecs(path):
    a = np.fromfile(path, dtype=np.int32)
    d = a[0]
    return a.reshape(-1, d + 1)[:, 1:].copy().view(np.float32)


def write_fvecs(path, m):
    n, d = m.shape
    with open(path, "wb") as f:
        for i in range(n):
            f.write(struct.pack("<i", d))
            f.write(m[i].astype(np.float32).tobytes())


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--base", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--num", type=int, default=1000)
    p.add_argument("--seed", type=int, default=2026)
    args = p.parse_args()

    base = read_fvecs(args.base)
    rng = np.random.default_rng(args.seed)
    sel = rng.choice(base.shape[0], size=args.num, replace=False)
    sel.sort()
    write_fvecs(args.out, base[sel])
    print(f"sampled {args.num}/{base.shape[0]} (seed={args.seed}) -> {args.out}")


if __name__ == "__main__":
    main()
