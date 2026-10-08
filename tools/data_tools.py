import pandas as pd
from pathlib import Path
from .common import DATA

def read_table(path: str):
    p = Path(path)
    if p.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(p)
    return pd.read_csv(p)

def normalize_columns(df):
    out = df.copy()
    out.columns = [str(c).strip().lower().replace(" ", "_") for c in out.columns]
    return out

def load_json_data(name):
    import json
    with open(DATA / name, encoding="utf-8") as f:
        return json.load(f)
