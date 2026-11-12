"""Profile the raw Olist files: rows, columns, nulls, duplicate keys."""
from pathlib import Path
import pandas as pd

RAW = Path(__file__).resolve().parents[1] / "data" / "raw" / "olist"

for f in sorted(RAW.glob("*.csv")):
    df = pd.read_csv(f)
    nulls = df.isna().sum()
    nulls = nulls[nulls > 0]
    print(f"\n=== {f.name}: {len(df):,} rows, {df.shape[1]} cols, "
          f"{df.duplicated().sum():,} fully duplicated rows")
    print("columns:", ", ".join(df.columns))
    if len(nulls):
        print("nulls:", ", ".join(f"{k}={v:,}" for k, v in nulls.items()))
