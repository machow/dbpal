# Note that this config is copied from dbcooper-py:
# https://github.com/machow/dbcooper-py/blob/main/dbcooper/tests/conftest.py

import pytest
import tempfile

from siuba.tests.helpers import SqlBackend, BigqueryBackend, CloudBackend
from dbpal.tests.helpers import TempBucket

params_backend = [
    #pytest.param(lambda: SqlBackend("postgresql"), id = "postgresql", marks=pytest.mark.postgresql),
    #pytest.param(lambda: SqlBackend("mysql"), id = "mysql", marks=pytest.mark.mysql),
    #pytest.param(lambda: SqlBackend("sqlite"), id = "sqlite", marks=pytest.mark.sqlite),
    pytest.param(lambda: BigqueryBackend("bigquery"), id = "bigquery", marks=pytest.mark.bigquery),
    pytest.param(lambda: SqlBackend("duckdb"), id = "duckdb", marks=pytest.mark.duckdb),
    #pytest.param("diskhouse", id="diskhouse", marks=pytest.mark.diskhouse),
    #pytest.param(lambda: CloudBackend("snowflake"), id = "snowflake", marks=pytest.mark.snowflake),
    ]


@pytest.fixture(params=params_backend, scope = "session")
def backend(request):
    if isinstance(request.param, str):
        yield request.getfixturevalue(request.param)

    else:
        backend = request.param()

        yield backend


@pytest.fixture
def bucket():
    import fsspec
    import uuid

    # TODO: currently hard-coding gcs bucket
    bucket = TempBucket.from_protocol("gs", f"tidyverse-pipeline/tests/ci/{uuid.uuid4()}")

    yield bucket

    bucket.teardown()


@pytest.fixture(scope = "session")
def diskhouse():
    from dbpal.data import DuckdbDiskhouse
    from sqlalchemy import create_engine

    engine = create_engine("duckdb:///:memory:")

    with tempfile.TemporaryDirectory() as tmp_dir:
        yield DuckdbDiskhouse(engine, tmp_dir)
