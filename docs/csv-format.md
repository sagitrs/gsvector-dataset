# CSV 格式生成器

**日期：** 2026-06-24
**类型：** 子设计文档
**依赖：** [主文档](../DESIGN.md)

## 目标

本档说明如何为 gsvector-pg 的 SQL regression 测试生成 CSV 格式的数据集。这里用的是逗号分隔值（Comma-Separated Values，下称 CSV）文本格式，它与 PostgreSQL 的 `COPY` 命令兼容。

## CSV 格式

CSV 文件的第一行是列名，其后的每一行是一条向量。第一列 `id` 是 0 起始的行号，类型为无符号 64 位整数。其余各列是向量的 float32 分量。

```csv
id,v1,v2,...,vd
0,0.0607,-0.0295,...,0.0535
1,0.0131,0.0154,...,0.0221
```

gsvector-pg 的测试用 `COPY ... FROM 'base.csv' WITH (FORMAT CSV, HEADER)` 加载该文件。

## 转换脚本：`scripts/fvecs2csv.py`

脚本的调用方式是 `fvecs2csv.py <input.fvecs> <output.csv>`：读入 `.fvecs` 文件，写出 CSV。

### 实现要点

读取时先取文件头的 4 个字节，得到向量的维度 `dim`。此后逐条读取向量：每条向量以自己的 4 字节 `dim` 开头，随后是 `dim × 4` 字节的 float32 分量。写出时按 `id, v0, v1, ..., v{dim-1}` 的列序生成 CSV。

### 处理规模

三个规模的实测耗时如下：SIFT 1k 数据（1000 行）不到 1 秒，SIFT 100k 数据（10 万行）约 5 秒，GIST 1m 数据（100 万行、960 维）约 30 秒。

转换与输入输出（Input/Output，下称 IO）紧密相关，属 IO 密集型过程，因此多个数据集可以用 `make -jN csv` 并行生成。并行度 `N` 建议不超过 CPU 核心数。

## Makefile 集成

```makefile
sift/1k/base.csv: sift/1k/base.fvecs scripts/fvecs2csv.py
        $(PYTHON) scripts/fvecs2csv.py $< $@
```

所有 CSV 文件都可以批量生成，并由大文件存储（Large File Storage，下称 LFS）追踪。
