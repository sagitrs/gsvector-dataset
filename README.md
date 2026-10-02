# gsvector_dataset

Benchmark datasets for the [gsvector](https://github.com/sagitrs/gsvector) approximate nearest neighbor (ANN) index extension.

## Datasets

Four datasets are provided. The table gives each one's dimension, the size of its 1M base set, and what it contains.

| Dataset | Dimension | 1M Base Size | Description |
|---------|-----------|-------------|-------------|
| SIFT    | 128       | ~500MB      | SIFT descriptors, classic ANN benchmark |
| GIST    | 960       | ~3.6GB      | GIST descriptors, high-dimensional benchmark |
| BioASQ  | 1024      | ~4.1GB (1m) | Biomedical QA passage embeddings (Cohere beir-embed-english-v3) |
| Cohere  | 768       | ~3GB        | Wikipedia embeddings via Cohere multilingual model |

Each dataset is available at four scales: 1k, 10k, 100k, and 1m vectors.

## Directory Structure

```
sift/
├── 1k/{base,query,gt_top10,gt_top100}.{fvecs,ivecs}
├── 10k/...
├── 100k/...
└── 1m/...                    # SIFT 1M included in LFS
gist/
├── 1k/...   (LFS)
├── 10k/...  (LFS)
├── 100k/... (LFS)
└── 1m/...                    # On-demand only (file > 1GB)
bioasq/  (same as gist)
cohere/  (same as gist)
```

## 数据来源与口径注记

本节说明各数据集的构造方式。与文献对表之前应当先读本节。

GIST 数据集的 base 取自 texmex 官方 corpus 的前 N 条嵌套切片。它的 query 并非 texmex 官方集：gist/100k 的 query 由 base 确定性采样得到（见 `scripts/sample_query.py`，seed 取 2026），真值由精确计算得出并排除自命中（见 `compute_groundtruth.py --exclude-self`，口径载体随数据入仓）。1k 与 10k 的 query 用同一方法生成，见 `#6`。因此该数据集的 query split 与官方不同，它的 recall 数字不可直接与 texmex 榜单对表。

BioASQ 数据集由两部分拼成：Cohere/beir-embed-english-v3（取自 Hugging Face，下称 HF）的 bioasq-corpus 前 1M 条切片，以及 bioasq-queries 的 test split（500 条独立集）。它的真值由精确最近邻计算得到，使用 float64 精度与 L2 距离，与 qrels 相关性口径不同。

SIFT 数据集使用官方 query split，共 10000 条。1m 规模的 query 与真值需要重算，该工作挂在 `#6`。

## Formats

The same data is available in three formats. `fvecs` and `ivecs` are the source formats; the other two are derived from them.

| Format | Files | Consumer | `make` target |
|--------|-------|----------|:--:|
| `.fvecs` / `.ivecs` | `base.fvecs`, `query.fvecs`, `gt_top*.ivecs` | gsvector C++, Python | `make fvecs` |
| `.csv` | `base.csv`, `query.csv` | gsvector-pg (PG COPY) | `make csv` |
| Iceberg | `iceberg/data/*.parquet` + `metadata/` | gsiceberg (FDW) | `make iceberg` |

### CLI: `get.py`

`get.py` prints the path of an already generated dataset, so that callers do not have to remember the directory layout.

```bash
python3 scripts/get.py sift 1k              # list available formats
python3 scripts/get.py sift 1k csv          # → base.csv, query.csv paths
python3 scripts/get.py gist 10k fvecs --gt top10  # fvecs + ground truth
python3 scripts/get.py sift 1k iceberg --json     # JSON for scripts
```

## Quick Start

The fastest path is to let `make` build what you need.

```bash
make ci              # 1k fvecs for CI
make csv             # CSV for gsvector-pg
make iceberg         # Iceberg for gsiceberg
make all-formats     # everything
```

### fvecs (float vectors)

A `.fvecs` file stores each vector as a 4-byte dimension followed by that many 4-byte floats.

```
[int32: dimension] [float32 × dimension] [int32: dimension] [float32 × dimension] ...
```

The file is little-endian binary data, and each vector is preceded by its dimension.

### ivecs (integer vectors)

An `.ivecs` file uses the same layout, but stores 4-byte integers instead of floats.

```
[int32: k] [int32 × k] [int32: k] [int32 × k] ...
```

The file is little-endian binary data. Values are 0-based indices into `base.fvecs`.

## Setup

This section walks through creating a working environment, generating the datasets, and validating them.

### Prerequisites

The scripts need numpy. The commands below create a virtual environment that reuses the system numpy.

```bash
# Python venv with numpy (uses system numpy via --system-site-packages)
python3 -m venv --system-site-packages ~/venv
```

### Generate All LFS-Tracked Datasets

```bash
make all
```

This target generates every dataset that fits within the 1GB-per-file limit of large file storage (LFS). The affected sizes are:

- SIFT: all four sizes (1k, 10k, 100k, 1m)
- GIST: 1k, 10k, 100k
- BioASQ: 1k, 10k, 100k
- Cohere: 1k, 10k, 100k

### Generate 1M On-Demand

For GIST, BioASQ, and Cohere the 1M datasets are too large for LFS and must therefore be generated locally.

```bash
make gist-1m
make bioasq-1m
make cohere-1m
```

### Validate

```bash
make validate
```

### Individual Datasets

Each dataset can also be generated on its own.

```bash
make sift      # SIFT: all 4 sizes
make gist      # GIST: 1k/10k/100k
make bioasq    # BioASQ: 1k/10k/100k
make cohere    # Cohere: 1k/10k/100k
```

### Clean

```bash
make clean     # Remove all generated data
```

## Data Sources

The table lists where the raw data comes from and the format it arrives in.

| Dataset | Source | Format |
|---------|--------|--------|
| SIFT | <http://corpus-texmex.irisa.fr/> | tar.gz, converted to fvecs |
| GIST | <http://corpus-texmex.irisa.fr/> | tar.gz, converted to fvecs |
| BioASQ | ANN benchmarks community mirror | fvecs files |
| Cohere | Cohere Wikipedia embeddings via ANN benchmarks | fvecs files |

### Custom Mirror Configuration

For Cohere and BioASQ, environment variables override the download URL.

```bash
BIOASQ_BASE_URL="https://your-mirror.example.com/bioasq" make bioasq
COHERE_BASE_URL="https://your-mirror.example.com/cohere" make cohere
```

## Pipeline Scripts

The pipeline is driven by the scripts below. Each one is documented in more detail in [scripts/README.md](scripts/README.md).

| Script | Purpose |
|--------|---------|
| `scripts/download_<dataset>.sh` | Fetch raw data from public mirrors |
| `scripts/slice_dataset.py` | First-N extraction from full base set |
| `scripts/compute_groundtruth.py` | Brute-force k-NN ground truth (L2^2) |
| `scripts/validate.py` | Format and integrity checks |

## Test tooling

**测试工具根**：`scripts/`

本仓测试支撑与数据准备工具（下载 / 转换 / 切片 / 真值 / 校验）位于 [`scripts/`](scripts/)；
逐项用途、固定命令、期望读数与失效条件见 [`scripts/README.md`](scripts/README.md)。

## 术语表

| 缩写 | 全称 | 说明 |
|---|---|---|
| ANN | Approximate Nearest Neighbor | 近似最近邻检索 |
| LFS | Large File Storage | Git 大文件存储 |
| CSV | Comma-Separated Values | 逗号分隔值文本格式 |
| PG / PG COPY | PostgreSQL | 本仓用 PG 指代 PostgreSQL；PG COPY 是它的批量装载命令 |
| FDW | Foreign Data Wrapper | PostgreSQL 的外部数据包装器 |
| GT | Ground Truth | 精确计算出的最近邻真值 |
| CLI | Command-Line Interface | 命令行界面 |
| IO | Input/Output | 输入输出 |
| HF | Hugging Face | 模型与数据集托管站点 |
| dim | dimension | 向量维度 |
| fvecs / ivecs | float vectors / integer vectors | 本仓的两种向量二进制格式 |

## License

Datasets are provided under their original licenses. See source sites for details.
