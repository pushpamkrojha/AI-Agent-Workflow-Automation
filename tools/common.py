from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "data"

def read_csv(name: str) -> pd.DataFrame:
    return pd.read_csv(DATA / name)

def pct_difference(a, b):
    if b == 0:
        return None
    return round(abs(a-b) / b * 100, 2)
