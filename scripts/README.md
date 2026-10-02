# scripts/ —— 测试支撑与数据准备工具

> 本目录为仓根 `README.md` 声明的 **`测试工具根`** ✓

**工具根实收 = 16 个 `*.py` / `*.sh`** —— 下表逐项列全（✗ 不漏列；索引与本目录实收集的**双向差集为空**）。

| 工具 | 用途（一句话） | 固定命令 | 期望读数 | 设立理由 / 失效条件 |
|---|---|---|---|---|
| **`scripts/download_sift.sh`** | 从公共镜像取 SIFT 原始数据（fvecs/ivecs） | `make sift`（或 `bash scripts/download_sift.sh`） | 目标目录出现 `base.fvecs` / `query.fvecs` | 理由：多镜像来源须统一入口 · 失效：数据改为内部托管后冗余 |
| **`scripts/download_gist.sh`** | 从公共镜像取 GIST 原始数据 | `make gist` | 同上 | 同上 |
| **`scripts/download_bioasq.sh`** | 从公共镜像取 BioASQ 原始数据 | `make bioasq` | 同上 | 同上 |
| **`scripts/download_cohere.sh`** | 从公共镜像取 Cohere 原始数据 | `make cohere` | 同上 | 同上 |
| **`scripts/compute_groundtruth.py`** | 暴力 k-NN 真值（穷举 L2²，输出 top-K ivecs） | `make sift`（生成 `gt_top{10,100}.ivecs`） | 生成的 GT 与 `scripts/validate.py` 同过（rc=0） | 理由：GT 口径须仓内自算才可复现 · 失效：官方 GT 可直接采用后冗余 |
| **`scripts/slice_dataset.py`** | 从完整 base 取前 N（CI 用小集） | `make ci`（见 `Makefile` 的 `ci-*` 目标） | 各档 `1k/` 下三件齐（base/query/gt） | 理由：全量过大、CI 只跑 1k · 失效：CI 改跑全量或抽样策略变更后重审 |
| **`scripts/validate.py`** | fvecs/ivecs **格式与完整性校验**（存在性 / 维度 / 记录数 / ivecs 索引域 / 分量量级异常） | `make validate`（或 `python3 scripts/validate.py <path>`） | **rc=0** 且逐文件报 OK；异常逐条列出且 rc≠0 | 理由：曾发生单分量被放大到 ~1e16 致下游静默错算 · 失效：数据源改为自带校验的内联格式后冗余 |
| **`scripts/get.py`** | 数据集路径 CLI —— 不记路径即可取用 | `python3 scripts/get.py <dataset> <size>` | 打印绝对路径且文件存在 | 理由：调用方硬记目录结构易错 · 失效：统一以环境变量/配置下发路径后冗余 |
| **`scripts/sample_query.py`** | 由干净 base **确定性**采样 query（仓内口径载体） | `python3 scripts/sample_query.py` | 同 seed 两次输出逐位一致 | 理由：query 抽样口径须可复现（✗ 每次不同） · 失效：口径改由上游固定文件下发后冗余 |
| **`scripts/extract_hdf5.py`** | 从 ann-benchmarks HDF5 按数据块直读抽出 fvecs/ivecs | `python3 scripts/extract_hdf5.py <in.hdf5> <outdir>` | 抽出文件与 `validate.py` 同过 | 理由：ann-benchmarks 只发 HDF5，本仓需 fvecs 口径 · 失效：上游改发 fvecs 后冗余 |
| **`scripts/convert_fbin.py`** | fbin/ibin（RAFT ANN bench 格式）→ fvecs/ivecs | `python3 scripts/convert_fbin.py <in> <out>` | 转换后与源逐位一致 | 理由：RAFT 数据只发 fbin/ibin · 失效：上游改发 fvecs 后冗余 |
| **`scripts/test_convert.py`** | `convert_fbin.py` 的**往返自证**（合成数据 → 转 → 逐位校验） | `python3 scripts/test_convert.py` | **rc=0**（含「注入错误必红」类断言） | 理由：转换器自身须可失败，否则成「看着能用」的掩盖源 · 失效：往返测试并入 pytest 套件后冗余 |
| **`scripts/fvecs2csv.py`** | fvecs → CSV（PG COPY 兼容），供关系导入 | `make csv`（或 `python3 scripts/fvecs2csv.py <in> <out>`） | 输出 CSV 行数 == 源记录数 | 理由：PG 侧消费需 CSV 口径 · 失效：改为 `COPY ... FROM PROGRAM` 直读 fvecs 后冗余 |
| **`scripts/csv2iceberg.py`** | CSV → Iceberg 表（表格数据，非向量） | `python3 scripts/csv2iceberg.py <csv> <table>` | 表可查且行数一致 | 理由：湖仓侧对接入口 · 失效：Iceberg 写入由上游 ETL 承担后冗余 |
| **`scripts/fvecs2iceberg.py`** | fvecs → Iceberg 表（向量列） | `python3 scripts/fvecs2iceberg.py <fvecs> <table>` | 表可查且行数/维度一致 | 同上（向量侧） |
| **`scripts/generate_tpcds.py`** | 生成 TPC-DS 形态的**确定性**随机表格数据 | `python3 scripts/generate_tpcds.py <outdir>` | 同 seed 两次输出逐位一致 | 理由：关系面基准须可复现且不依赖外部下载 · 失效：改用官方 TPC-DS 工具链后冗余 |

**退役 / 移动** ⇒ **须同步仓根 `README.md` 的声明行**（✗ 否则死链 ✓）
