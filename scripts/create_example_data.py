import json
import pandas as pd
import sys

from pathlib import Path


out_dir = Path(sys.argv[1])

out_dir.mkdir(exist_ok=True, parents=True)


def to_ndjson(d, out_file):
    json_data = json.loads(d.to_json(orient="records"))

    for entry in json_data:
        json.dump(entry, out_file)
        out_file.write("\n")


df = pd.DataFrame({"x": [1,2]})
df.to_parquet(out_dir / "data.parquet")
to_ndjson(df, open(out_dir / "data.jsonl", "w"))

