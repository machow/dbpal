import os

def get_bucket():
    return os.environ["PIPELINE_BUCKET"]


def get_fs():
    import fsspec

    p_bucket = get_bucket()

    # TODO: hard-coding this for now. I can't remember how extract the protocol.
    if p_bucket.startswith("gcs:"):
        return fsspec.filesystem("gcs")

    return fsspec.filesystem("file")


def get_sql_engine(read_only=False):
    from sqlalchemy import create_engine

    db_path = os.environ["PIPELINE_WAREHOUSE_URI"]

    return create_engine(
        db_path,
    )

