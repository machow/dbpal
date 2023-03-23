import os

from dbcooper import DbCooper, AccessorHierarchyBuilder
from functools import partial
from dbpal.config import get_sql_engine, get_fs
from pathlib import Path

__ALL__ = ["get_dbc", "tbls"]


def get_dbc(read_only=True):
    engine = get_sql_engine(read_only)
    dbc = DbCooper(
        engine,
        accessor_builder = AccessorHierarchyBuilder()
    )

    # if we're using duckdb, then the warehouse is a bunch of parquet files,
    # so we add accessors that just .query("... read_parquet...")
    if engine.name == "duckdb":
        fs = get_fs()
        warehouse_path = os.environ["PIPELINE_WAREHOUSE_URI"]

        parquet_files = fs.ls(warehouse_path)
        for fname in parquet_files:
            short_name = fname.rsplit(".")[0].split("/")[-1]
            sql = f"""SELECT * FROM read_parquet("{fname}")"""
            dbc._accessors[short_name] = partial(dbc.query, sql)

    return dbc


def __getattr__(k):
    if k == "tbls":
        return get_dbc()

    raise AttributeError(k)
