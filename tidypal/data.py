from abc import ABC

from sqlalchemy.engine import Engine
from dataclasses import dataclass
from plum import type_of, parametric


# File classes ----------------------------------------------------------------

class File:
    _registry = {}
    suffix = None

    def __init__(self, name: str, parent: "str | None" = None):
        self.name = name
        self.parent = parent

    def __init_subclass__(cls, *args, **kwargs):
        super().__init_subclass__(*args, **kwargs)

        if cls.suffix in cls._registry:
            raise KeyError("Suffix {cls.suffix} already in registry")

        cls._registry[cls.suffix] = cls

    @classmethod
    def from_name(cls, name, parent=None):
        suffix = name.rsplit(".", 1)[-1]
        return cls._registry[suffix](name, parent)


class ParquetFile(File):
    suffix = "parquet"


class JsonlFile(File):
    suffix = "jsonl"

class NdjsonFile(JsonlFile):
    # TODO: change ndjson to jsonl in gh extractor
    suffix = "ndjson"


# SQLAlchemy engine abstract classes ------------------------------------------


@parametric(runtime_type_of=True)
class SqlEngine(Engine):
    name = None

    @classmethod
    def __subclasshook__(cls, C):
        if issubclass(C, Engine) and C.name == cls.engine_name:
            return True

        return NotImplemented


@parametric(runtime_type_of=True)
class SqlEngineDuckdb(SqlEngine):
    engine_name = "duckdb"


@parametric(runtime_type_of=True)
class SqlEngineBigquery(SqlEngine):
    engine_name = "bigquery"


# DuckdbWarehouse class, for writing to disk ----------------------------------

@dataclass
class DuckdbDiskhouse:
    engine: Engine
    dir_path: str
    result_type: File = ParquetFile


# type_of (essentially holy traits?) ==========================================

@type_of.dispatch
def type_of_ext(x: Engine):

    print("checking type")
    if x.name == "duckdb":
        return SqlEngineDuckdb
    elif x.name == "bigquery":
        return SqlEngineBigquery

    raise TypeError(f"Unsupported sqlalchemy engine name: {x.name}")

