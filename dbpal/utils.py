import fsspec
import os
import logging
import siuba as sb
import pandas as pd

from dataclasses import dataclass
from plum import dispatch, type_of
from pathlib import Path
from siuba.sql import LazyTbl
from sqlalchemy import create_engine
from typing import Union, Any

from dbpal.config import get_sql_engine, get_bucket, get_fs
from dbpal import data as dc


SQL_DUCKDB_TEMPLATE = """
COPY (

{sql}

)
TO '{name}.parquet' (FORMAT 'parquet')
"""

SQL_TEMPLATE = """CREATE OR REPLACE TABLE {name} AS {sql}"""


def compile_sql(tbl: LazyTbl):
    sel = tbl.last_select
    compiled = sel.compile(
        dialect = tbl.source.dialect,
        compile_kwargs = {"literal_binds": True}
    )

    return str(compiled)


@dispatch
def fully_qualified_name(name: str, engine: dc.SqlEngineBigquery, escape=True):
    # TODO: is there a way to just do all this via an engine method, etc..?
    max_parts = 3
    parts = name.split(".")

    if len(parts) > max_parts:
        raise ValueError(f"Table has too many parts: {len(parts)}")

    name, schema, database = list(reversed(parts)) + [None]*(max_parts - len(parts))

    defaults = extract_table_name_defaults(engine)

    if schema is None:
        if defaults["schema"] is None:
            raise ValueError("No database schema specified, and no schema set for the engine.")
        schema = defaults["schema"]
    if database is None:
        if defaults["database"] is None:
            raise ValueError("No database database name specified, and no schema set for the engine.")
        database = defaults["database"]

    # TODO: the ` character is bigquery specific
    if escape:
        return f"`{database}`.`{schema}`.`{name}`"

    return f"{database}.{schema}.{name}"


@dispatch
def fully_qualified_name(name: str, engine: dc.SqlEngineDuckdb, escape=True):
    return name


@dispatch
def extract_table_name_defaults(engine: dc.SqlEngine):
    return {"database": engine.url.host, "schema": engine.url.database}


# copy_to_warehouse ===========================================================

#@dispatch
#def copy_to_warehouse(tbl, name, engine):
#    raise TypeError(f"Cannot copy data of type `{type(tbl)}` to warehouse")


@dispatch
def copy_to_warehouse(tbl, name, engine: None = None, **kwargs):
    if engine is None:
        engine = get_sql_engine()

    return copy_to_warehouse(tbl, name, engine, **kwargs)


@dispatch
def copy_to_warehouse(tbl: LazyTbl, name: str, engine: dc.SqlEngineDuckdb):
    compiled = compile_sql(data)

    create_stmt = f"""CREATE OR REPLACE TABLE "{name}" AS {compiled}"""

    engine.execute(create_stmt)

    return name
    

@dispatch
def copy_to_warehouse(tbl: pd.DataFrame, name: str, engine: dc.SqlEngineDuckdb):

    sql_tbl = engine.connect().connection.c.from_df(tbl)

    # note that duckdbs create method can't replace :/
    engine.execute(f"""DROP TABLE IF EXISTS "{name}" """)
    sql_tbl.create(name)

    return name
    

@dispatch
def copy_to_warehouse(tbl: pd.DataFrame, name: str, engine: dc.SqlEngineBigquery, if_exists = "replace"):

    # Note that pandas gbq does not allow quoted name parts (with `)
    # e.g. `my-project`.`my-dataset`.`a-table`
    full_name = fully_qualified_name(name, engine, escape=False)
    tbl.to_gbq(full_name, if_exists=if_exists)

    return full_name


@dispatch
def copy_to_warehouse(tbl: str, name: str, engine: dc.SqlEngine):

    # TODO: use something like dbcooper-py generic dispatch use name for dispatch
    full_name = fully_qualified_name(name, engine)
    create_stmt = SQL_TEMPLATE.format(sql=tbl, name=full_name)

    logging.info(create_stmt)

    engine.execute(create_stmt)

    return full_name


@dispatch
def copy_to_warehouse(tbl: Union[str, pd.DataFrame], name: str, engine: dc.DuckdbDiskhouse):
    # just create parquet files on disk
    sql = tbl if isinstance(tbl, str) else "SELECT * FROM tbl"

    sql_engine = engine.engine
    warehouse_path = engine.dir_path

    # Note that this is an elaborate way to create the correct filesystem
    # from a url (e.g. s3://my_bucket/sub_path)
    fs, _, _ = fsspec.get_fs_token_paths(warehouse_path)
    if not fs.exists(warehouse_path):
        fs.mkdir(warehouse_path)

    # TODO: support formats other than parquet
    final_name = warehouse_path + "/" + name
    create_stmt = SQL_DUCKDB_TEMPLATE.format(sql=sql, name = final_name)

    logging.info(create_stmt)

    sql_engine.execute(create_stmt)


# File to warehouse ===========================================================

# file_to_warehouse ----

_DuckDb = Union[dc.SqlEngineDuckdb, dc.DuckdbDiskhouse]


def _expand_path(file_obj: dc.File):
    parent = get_bucket() if file_obj.parent is None else file_obj.parent
    full_path = parent + f"/{file_obj.name}"
    return full_path


@dispatch
def file_to_warehouse(file_name, table_name):
    raise TypeError(f"Cannot handle type type `{type(tbl)}`")


@dispatch
def file_to_warehouse(file_name: str, table_name, engine = None, **kwargs):
    if engine is None:
        engine = get_sql_engine()

    obj = dc.File.from_name(file_name)
    if type(obj) is dc.File:
        raise NotImplementedError(f"Cannot identify file type for file name: {file_name}")

    return file_to_warehouse(obj, table_name, engine, **kwargs)


@dispatch
def file_to_warehouse(file_name: dc.ParquetFile, table_name, engine: _DuckDb):
    full_path = _expand_path(file_name)

    sql = f"""SELECT * FROM read_parquet("{full_path}")"""

    copy_to_warehouse(sql, table_name, engine)


@dispatch
def file_to_warehouse(file_name: dc.JsonlFile, table_name, engine: _DuckDb):
    full_path = _expand_path(file_name)

    sql = f"""SELECT * FROM read_json_objects("{full_path}")"""

    copy_to_warehouse(sql, table_name, engine)


@dispatch
def file_to_warehouse(file_name: dc.File, table_name, engine: dc.SqlEngineBigquery, if_exists="replace"):
    full_path = _expand_path(file_name)

    if if_exists == "replace":
        overwrite = "OVERWRITE"
    elif if_exists == "append":
        overwrite = "INTO"
    else:
        raise ValueError(f"Unsupported if_exists option: {if_exists}")


    if isinstance(file_name, dc.JsonlFile):
        format_ = "NEWLINE_DELIMITED_JSON"
    elif isinstance(file_name, dc.ParquetFile):
        format_ = "PARQUET"
    else:
        raise ValueError(f"Unsupported file type: {type(file_name)}")

    full_name = fully_qualified_name(table_name, engine)

    sql = f"""
    LOAD DATA {overwrite} {full_name}
      FROM FILES (
        format='{format_}',
        uris = ['{full_path}']
      )
    """

    engine.execute(sql)


# copy_to_bucket ==============================================================

@dispatch
def copy_to_bucket(src: Union[str, Path], dst, fs = None):
    
    src_obj = dc.File.from_name(str(src))

    if isinstance(dst, str):
        dst = dc.File.from_name(dst)

    if fs is None:
        fs = get_fs()

    return copy_to_bucket(src_obj, dst, fs)


@dispatch
def copy_to_bucket(src: dc.File, dst: dc.File, fs: fsspec.AbstractFileSystem, **kwargs):
    # TODO: assumes source is always local
    src_path = src.name
    dst_path = _expand_path(dst)

    fs.put(src_path, dst_path, **kwargs)

    return dst_path
