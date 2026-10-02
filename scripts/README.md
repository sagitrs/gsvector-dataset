# scripts/ —— 测试支撑与数据准备工具

> 本目录为仓根 `README.md` 声明的 **`测试工具根`** ✓

| 工具 | 用途（一句话）| 固定命令 | 期望读数 | 设立理由 / 失效条件 |
|---|---|---|---|---|
| **`validate.py`**（**测试支撑**）| fvecs/ivecs 的**格式与完整性校验**（存在性 / 维度一致 / 记录数 / ivecs 索引域 / 分量量级异常）| `make validate`（或 `python3 scripts/validate.py <path>`）| **rc=0** 且逐文件报 OK；异常则逐条列出且 rc≠0 | 理由：数据损坏（如单分量被放大到 ~1e16）曾致下游静默错算 · 失效：数据源改为自带校验的内联格式后即冗余 |
| `download_<dataset>.sh` | 从公共镜像取原始数据 | `make <dataset>` | 目标目录出现 `base.fvecs`/`query.fvecs`/`gt_*.ivecs` | 理由：多镜像一致性 · 失效：数据改为内部托管后冗余 |
| `compute_groundtruth.py` | 暴力 k-NN 真值（L2²）| `make <dataset>`（生成 `gt_top{10,100}.ivecs`）| 生成的 GT 文件与 `validate.py` 同过 | 理由：GT 口径须自算以保证可复现 · 失效：官方 GT 可直接采用后冗余 |
| `slice_dataset.py` | 从完整 base 取前 N（CI 用小集）| 见 `Makefile` 的 `ci-*` 目标 | `*/1k/` 下三件齐 | 理由：全量太大，CI 只跑 1k · 失效：CI 改跑全量或抽样策略变后重审 |

**退役 / 移动** ⇒ **须同步仓根 `README.md` 的声明行**（✗ 否则死链 ✓）
