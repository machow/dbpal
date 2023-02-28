import dbpal.data as dc
from sqlalchemy.engine import Engine
from plum import dispatch, type_of
from sqlalchemy import create_engine


@dispatch
def f(engine: dc.SqlEngineDuckdb):
    print("doing stuff")
    return 1


@dispatch
def g(x: str, engine: dc.SqlEngineDuckdb):
    return 2

def test_dispatch_abc():
    engine = create_engine("duckdb:///:memory:")
    res = f(engine)
    assert res == 1
