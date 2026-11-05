"""공통 로더. 모든 원본은 data/raw (cp949 CSV). 실행: /opt/homebrew/bin/python3.11 -I analysis/XX.py"""
import pandas as pd, glob, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
OUT = os.path.join(ROOT, "web", "data")
os.makedirs(OUT, exist_ok=True)

def raw(pattern):
    p = os.path.normpath(os.path.join(RAW, pattern))
    return glob.glob(p)[0]

def load_inout():
    df = pd.read_csv(raw("15138735.csv"), encoding="cp949")
    df["in_dt"] = pd.to_datetime(df["입차일시"])
    df["out_dt"] = pd.to_datetime(df["출차일시"])
    df["stay_min"] = (df["out_dt"] - df["in_dt"]).dt.total_seconds() / 60
    return df

def exits_5min(df, end="2024-08-01"):
    s = df.set_index("out_dt").assign(n=1)["n"].resample("5min").sum()
    return s[s.index < end]
