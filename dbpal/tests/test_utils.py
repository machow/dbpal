import pytest
import pandas as pd
import dbpal.data as dc

from pathlib import Path

from dbpal.utils import copy_to_warehouse, file_to_warehouse, copy_to_bucket
from dbpal.config import get_sql_engine
from dbpal.tests.helpers import set_env

from importlib_resources import files

FILES = files("dbpal") / "tests/example_files"

IN_BUCKET = "gs://tidyverse-pipeline/tests/dbpal/tests/example_files"


@pytest.mark.parametrize("tbl", [
    pd.DataFrame({"x": [1]}),
    "SELECT 1 AS x",
])
def test_copy_to_warehouse(tbl, backend):
    final_name = copy_to_warehouse(tbl, "test_copy_to_warehouse", backend.engine)


def test_copy_to_warehouse_default():
    engine_url = "duckdb:///:memory:"
    with set_env(PIPELINE_WAREHOUSE_URI=engine_url):
        engine = get_sql_engine()

        assert str(engine.url) == engine_url

        res = copy_to_warehouse("SELECT 1", "test_df")

        engine.execute("SELECT * FROM test_df")


def test_copy_to_warehouse_diskhouse(diskhouse):
    df = pd.DataFrame({"x": [1,2,3]})
    copy_to_warehouse(df, "df", diskhouse)

    p_data = Path(diskhouse.dir_path) / "df.parquet"
    assert p_data.exists()

    res = pd.read_parquet(p_data)

    assert df.equals(res)


@pytest.mark.parametrize("fname", [
    dc.ParquetFile("data.parquet", IN_BUCKET),
    dc.JsonlFile("data.jsonl", IN_BUCKET),
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


@pytest.mark.parametrize("src", [
    FILES / "data.parquet",
    str(FILES / "data.parquet"),
    dc.File(str(FILES / "data.parquet"))
])
def test_copy_to_bucket(src, bucket):
    dst = dc.File(f"test_copy_to_bucket__{type(src)}.parquet", bucket.dirname)
    copy_to_bucket(src, dst, bucket.fs)
