"""시나리오(가정): 서지 차량의 일부(f)가 산책으로 출발을 늦춰 몰림 이후로 분산될 때 5분 피크 감소율.
실측 곡선만 사용: 서지 코어의 초과 출차 중 f 비율을 코어 종료 후 20~50분 구간에 균등 재배치."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
from common import *
M = json.load(open(os.path.join(OUT, "surge_model.json")))
df = load_inout(); ex = exits_5min(df)
tab = ex.to_frame("n"); tab["d"] = tab.index.normalize(); tab["hm"] = tab.index.hour*60 + tab.index.minute
pv = tab.pivot(index="hm", columns="d", values="n").fillna(0)
pool = [d for d in pv.columns if str(d.date()) not in {r["date"] for r in M["surge_days"]}]
out = {}
for f in (0.1, 0.2, 0.3):
    reds = []
    for r in M["surge_days"]:
        d = pd.Timestamp(r["date"]); n = pv[d].copy()
        same = [x for x in pool if (x.dayofweek >= 5) == (d.dayofweek >= 5)]
        b = pv[same].median(axis=1)
        core = [h for h in range(r["t0"], r["t1"], 5)]
        exc = (n - b).clip(lower=0)
        moved = sum(exc[h] * f for h in core)
        new = n.copy()
        for h in core: new[h] -= exc[h] * f
        tgt = [h for h in range(r["t1"] + 20, r["t1"] + 55, 5)]
        for h in tgt: new[h] += moved / len(tgt)
        pk0 = n.loc[core].max(); pk1 = new.loc[core + tgt].max()
        reds.append(1 - pk1 / pk0)
    out[str(f)] = dict(mean=round(float(np.mean(reds)) * 100, 1), lo=round(float(min(reds)) * 100, 1), hi=round(float(max(reds)) * 100, 1))
print(out)
json.dump(dict(scenario=out, note="가정 시나리오: 초과 출차의 f 비율이 코어 종료 20~55분 뒤로 이동. 피크(5분 최대) 감소율(%)"), open(os.path.join(OUT, "whatif.json"), "w"), ensure_ascii=False)
