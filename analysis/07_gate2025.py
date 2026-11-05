"""2025 게이트별 입출차(API_CPM_008 CSV, 2025-11-03~12-07, 10만건 상한) 탐색. 실행: python3.11 -I analysis/07_gate2025.py"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pandas as pd, numpy as np
from common import ROOT
b = pd.read_csv(os.path.join(ROOT, "data/raw_kcisa/API_CPM_008.csv"), encoding="utf-8-sig")
d = b.DESCRIPTION.str.extract(r"입구:(?P<gin>[^,]*), 입차시간:(?P<tin>[^,]*), 출구:(?P<gout>[^,]*), 출차시간:(?P<tout>.*)")
d["tin"] = pd.to_datetime(d.tin); d["tout"] = pd.to_datetime(d.tout)
d["stay"] = (d.tout - d.tin).dt.total_seconds() / 60
d["lane"] = d.gout
print(d.describe(include="all").T[["count","min","max"]])
print("exit range", d.tout.min(), d.tout.max(), "entry range", d.tin.min(), d.tin.max())
print("stay<=0:", (d.stay <= 0).sum(), "stay>24h:", (d.stay > 1440).sum())
ex = d.set_index("tout").assign(n=1)
pm = ex.groupby([pd.Grouper(freq="1min"), "lane"]).n.sum().unstack(fill_value=0)
print("per-lane per-minute exits: max", pm.max().to_dict())
print("p99", pm.quantile(.99).to_dict())
day = ex.groupby(ex.index.date).n.sum(); print(day.tail(40).to_string())

print("\n=== Dec 1-7 ===")
w = ex[(ex.index >= "2025-12-01") & (ex.index < "2025-12-08") & ex.lane.str.contains("출구")]
m5 = w.groupby([pd.Grouper(freq="5min")]).n.sum()
for dday, s in m5.groupby(m5.index.date):
    t = s.idxmax(); print(dday, pd.Timestamp(dday).day_name()[:3], "total", int(s.sum()), "peak5", int(s.max()), t.strftime("%H:%M"))
lm = w.groupby([pd.Grouper(freq="1min"), "lane"]).n.sum().unstack(fill_value=0)
print("per-lane 1-min max/p99.5", lm.max().to_dict(), lm.quantile(.995).to_dict())
# 009 hourly shows in Dec
a = pd.read_csv(os.path.join(ROOT, "data/raw_kcisa/API_CPM_009.csv"), encoding="utf-8-sig")
a["dt"] = pd.to_datetime(a.ISSUED_DATE)
dd = a[(a.dt >= "2025-11-01")]
print(dd[["ISSUED_DATE", "DESCRIPTION"]].head(12).to_string())
print(a[a.DESCRIPTION.str.contains("공연명:[^,]", regex=True)].assign(day=lambda x: x.dt.dt.date).groupby("day").DESCRIPTION.first().tail(15).to_string())
