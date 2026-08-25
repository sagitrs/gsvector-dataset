# gsvector_dataset

Benchmark datasets for the [gsvector](https://github.com/sagitrs/gsvector) ANN index extension.

## Datasets

| Dataset | Dimension | 1M Base Size | Description |
|---------|-----------|-------------|-------------|
| SIFT    | 128       | ~500MB      | SIFT descriptors, classic ANN benchmark |
| GIST    | 960       | ~3.6GB      | GIST descriptors, high-dimensional benchmark |
| BioASQ  | ~768      | ~3GB        | Biomedical QA passage embeddings |
| Cohere  | 768       | ~3GB        | Wikipedia embeddings via Cohere multilingual model |

Each dataset is available at four scales: **1k**, **10k**, **100k**, **1m** vectors.

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

## Data Sources & 口径注记

- **GIST**：base 为 texmex 官方 corpus 前 N 嵌套切片；**query 非 texmex 官方集**——
  gist/100k query 为 base 确定性采样（`scripts/sample_query.py`，seed=2026），GT 精算
  排自命中（`compute_groundtruth.py --exclude-self`，口径载体入仓）。1k/10k query 同法
  （#6）。与文献对表者须知：非官方 query split，recall 数字不可直接与 texmex 榜对表。
- **BioASQ**：Cohere/beir-embed-english-v3（HF）bioasq-corpus 前 1M 切片 + bioasq-queries
  test split（500 条独立集）；GT=精确 NN float64 L2（非 qrels 相关性口径）。
- **SIFT**：官方 query split（10000 条）；1m query/gt 重算挂账 #6。

## Formats

| Format | Files | Consumer | `make` target |
|--------|-------|----------|:--:|
| `.fvecs` / `.ivecs` | `base.fvecs`, `query.fvecs`, `gt_top*.ivecs` | gsvector C++, Python | `make fvecs` |
| `.csv` | `base.csv`, `query.csv` | gsvector-pg (PG COPY) | `make csv` |
| Iceberg | `iceberg/data/*.parquet` + `metadata/` | gsiceberg (FDW) | `make iceberg` |

### CLI: `get.py`

```bash
python3 scripts/get.py sift 1k              # list available formats
python3 scripts/get.py sift 1k csv          # → base.csv, query.csv paths
python3 scripts/get.py gist 10k fvecs --gt top10  # fvecs + ground truth
python3 scripts/get.py sift 1k iceberg --json     # JSON for scripts
```

## Quick Start

```bash
make ci              # 1k fvecs for CI
make csv             # CSV for gsvector-pg
make iceberg         # Iceberg for gsiceberg
make all-formats     # everything
```

### fvecs (float vectors)
```
[int32: dimension] [float32 × dimension] [int32: dimension] [float32 × dimension] ...
```
Little-endian binary format. Each vector is preceded by its dimension.

### ivecs (integer vectors)
```
[int32: k] [int32 × k] [int32: k] [int32 × k] ...
```
Little-endian binary format. Values are 0-based indices into `base.fvecs`.

## Quick Start

### Prerequisites

```bash
# Python venv with numpy (uses system numpy via --system-site-packages)
python3 -m venv --system-site-packages ~/venv
```

### Generate All LFS-Tracked Datasets

```bash
make all
```

This generates all datasets that fit within the 1GB-per-file LFS limit:

- SIFT: all four sizes (1k, 10k, 100k, 1m)
- GIST: 1k, 10k, 100k
- BioASQ: 1k, 10k, 100k
- Cohere: 1k, 10k, 100k

### Generate 1M On-Demand

For GIST, BioASQ, and Cohere, the 1M datasets must be generated locally
(too large for LFS):

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

| Dataset | Source | Format |
|---------|--------|--------|
| SIFT | <http://corpus-texmex.irisa.fr/> | tar.gz → fvecs |
| GIST | <http://corpus-texmex.irisa.fr/> | tar.gz → fvecs |
| BioASQ | ANN benchmarks community mirror | fvecs files |
| Cohere | Cohere Wikipedia embeddings via ANN benchmarks | fvecs files |

### Custom Mirror Configuration

For Cohere and BioASQ, use environment variables to override the download URL:

```bash
BIOASQ_BASE_URL="https://your-mirror.example.com/bioasq" make bioasq
COHERE_BASE_URL="https://your-mirror.example.com/cohere" make cohere
```

## Pipeline Scripts

| Script | Purpose |
|--------|---------|
| `scripts/download_<dataset>.sh` | Fetch raw data from public mirrors |
| `scripts/slice_dataset.py` | First-N extraction from full base set |
| `scripts/compute_groundtruth.py` | Brute-force k-NN ground truth (L2^2) |
| `scripts/validate.py` | Format and integrity checks |

## License

Datasets are provided under their original licenses. See source sites for details.
