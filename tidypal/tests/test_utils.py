import pytest
import pandas as pd
import tidypal.data as dc

from pathlib import Path

from tidypal.utils import copy_to_warehouse, file_to_warehouse
from importlib_resources import files

FILES = files("tidypal") / "tests/example_files"


@pytest.mark.parametrize("tbl", [
    pd.DataFrame({"x": [1]}),
    "SELECT 1 AS x",
])
def test_copy_to_warehouse(tbl, backend):
    final_name = copy_to_warehouse(tbl, "test_copy_to_warehouse", backend.engine)


def test_copy_to_warehouse_diskhouse(diskhouse):
    df = pd.DataFrame({"x": [1,2,3]})
    copy_to_warehouse(df, "df", diskhouse)

    p_data = Path(diskhouse.dir_path) / "df.parquet"
    assert p_data.exists()

    res = pd.read_parquet(p_data)

    assert df.equals(res)


@pytest.mark.parametrize("fname", [
    dc.ParquetFile("data.parquet", "gs://tidyverse-pipeline/tests/tidypal/tests/example_files"),
    dc.JsonlFile("data.jsonl", "gs://tidyverse-pipeline/tests/tidypal/tests/example_files"),
])
def test_file_to_warehouse_bigquery(fname, backend):
    if backend.name == "duckdb":
        pytest.xfail()

    file_to_warehouse(fname, "test_file_to_warehouse", backend.engine)


@pytest.mark.parametrize("fname", [
    dc.ParquetFile("data.parquet", str(FILES)),
    dc.JsonlFile("data.jsonl", str(FILES)),
])
def test_file_to_warehouse_duckdb(fname, backend):
    if backend.name == "bigquery":
        pytest.xfail()

    file_to_warehouse(fname, "test_file_to_warehouse", backend.engine)
