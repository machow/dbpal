# tidypal

| variable | description |
| -------- | ----------- |
| `PIPELINE_BUCKET` | Path to pipeline bucket. Used by fsspec. |
| `PIPELINE_WAREHOUSE_URI` | Warehouse URI (e.g. `duckdb:///:memory:`). Used by sqlalchemy. |
| `PIPELINE_USER` | Name of user. If not set to "pipeline", write operations will become no-ops. |
