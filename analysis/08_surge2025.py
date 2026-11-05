"""2025-12-05~07 공연 서지(게이트·차선별 CSV) 분석. 결과: web/data/surge2025.json
입력: data/raw_kcisa/API_CPM_008.csv (게이트별 입출차, 2025-11-03~12-07 입차분 10만건), API_CPM_009.csv (시간별 연계)"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
from common import ROOT, OUT
b = pd.read_csv(os.path.join(ROOT, "data/raw_kcisa/API_CPM_008.csv"), encoding="utf-8-sig")
d = b.DESCRIPTION.str.extract(r"입구:(?P<gin>[^,]*), 입차시간:(?P<tin>[^,]*), 출구:(?P<gout>[^,]*), 출차시간:(?P<tout>.*)")
d["tout"] = pd.to_datetime(d.tout); d["tin"] = pd.to_datetime(d.tin); d["n"] = 1
w = d[(d.tout >= "2025-12-01") & (d.tout < "2025-12-08") & d.gout.str.contains("출구")].set_index("tout").sort_index()
w["gate"] = w.gout.str.extract(r"^(.*?문)")[0]
m5 = w.n.resample("5min").sum()
# 기준선: 비공연일(12-01~04) 같은 시각 중앙값
idx = m5.index
hm = idx.hour * 60 + idx.minute
base_days = [pd.Timestamp(x) for x in ("2025-12-01", "2025-12-02", "2025-12-03", "2025-12-04")]
bd = m5[m5.index.normalize().isin(base_days)]
base = bd.groupby(bd.index.hour * 60 + bd.index.minute).median()
# 공연 연계(009) 일별 공연명/관람객
a = pd.read_csv(os.path.join(ROOT, "data/raw_kcisa/API_CPM_009.csv"), encoding="utf-8-sig"); a["dt"] = pd.to_datetime(a.ISSUED_DATE)
res = []
events = {"2025-12-05": (22 * 60 + 30, 24 * 60 + 90), "2025-12-06": (20 * 60 + 30, 23 * 60 + 15), "2025-12-07": (20 * 60 + 15, 22 * 60 + 15)}
for day, (lo, hi) in events.items():
    t0d = pd.Timestamp(day)
    s = m5[(m5.index >= t0d + pd.Timedelta(minutes=lo)) & (m5.index < t0d + pd.Timedelta(minutes=hi))]
    bs = np.array([base.get((t.hour * 60 + t.minute), 0) for t in s.index])
    exc = np.clip(s.values - bs, 0, None)
    peak = s.max(); thr = 0.6 * peak
    ok = (s.values >= thr)
    ii = np.where(ok)[0]; i0, i1 = ii[0], ii[-1]
    core = slice(max(i0 - 1, 0), i1 + 2)
    e = exc[core]; cum = np.cumsum(e) / e.sum()
    t90 = int((np.argmax(cum >= 0.9) + 1) * 5)
    # 게이트별 서지 구간 출차 점유율
    wc = w[(w.index >= s.index[core][0]) & (w.index < s.index[core][-1] + pd.Timedelta(minutes=5))]
    gshare = (wc.gate.value_counts(normalize=True) * 100).round(1).to_dict()
    lane = wc.groupby([pd.Grouper(freq="1min"), "gout"]).n.sum().unstack(fill_value=0)
    lane_peak = {k: int(v) for k, v in lane.max().items()}
    shows = a[(a.dt.dt.strftime("%Y-%m-%d") == day) & a.DESCRIPTION.str.contains("공연관람객수:[1-9]")]
    aud = shows.DESCRIPTION.str.extract(r"공연관람객수:(\d+)")[0].astype(int).max() if len(shows) else 0
    occ = a[a.dt.dt.strftime("%Y-%m-%d") == day].set_index("dt").DESCRIPTION.str.extract(r"주차대수:(\d+)")[0].astype(float)
    # what-if: 초과 출차의 f 비율을 코어 종료 20~55분 뒤로 이동했을 때 5분 최대 감소율
    wi = {}
    ncore = list(range(*core.indices(len(s))))
    vals = s.values.astype(float)
    for f in (0.1, 0.2, 0.3):
        new = vals.copy(); moved = sum(exc[i] * f for i in ncore)
        for i in ncore: new[i] -= exc[i] * f
        tgt = [i for i in range(ncore[-1] + 1 + 4, ncore[-1] + 1 + 11) if i < len(new)]
        if len(tgt) < 7:
            ext = np.concatenate([new, np.zeros(7 - len(tgt) + 12)]); new = ext
            tgt = list(range(ncore[-1] + 1 + 4, ncore[-1] + 1 + 11))
        for i in tgt: new[i] += moved / len(tgt)
        pk0 = vals[ncore].max(); pk1 = new[ncore + tgt].max()
        wi[str(f)] = round(float(1 - pk1 / pk0) * 100, 1)
    onset = s.index[core][0]
    prof = [int(m5.get(onset + pd.Timedelta(minutes=5 * k), 0)) for k in range(-6, 31)]
    cumf = [round(float(x), 3) for x in cum]
    res.append(dict(date=day, partial=(day == "2025-12-07"), whatif=wi, profile=prof, cum_fraction=cumf, start=s.index[core][0].strftime("%H:%M"), dur=int(len(e) * 5), exits=int(wc.n.sum()), excess=int(e.sum()),
                    peak5=int(peak), peak_per_min=round(float(np.sort(s.values[core])[-3:].mean() / 5), 1), t90=t90,
                    gate_share=gshare, lane_peak_1min=lane_peak, audience=int(aud),
                    occupancy_max=int(occ.max()) if len(occ) else None))
for r in res: print(json.dumps(r, ensure_ascii=False))
t90s = [r["t90"] for r in res if not r["partial"]]
summary = dict(lo=min(t90s), med=float(np.median(t90s)), hi=max(t90s), n=len(t90s))
print("t90 summary (partial 제외)", summary)
json.dump(dict(days=res, t_clear=summary, profile_axis_min=[5 * k for k in range(-6, 31)], note="게이트·차선 CSV(2025-11-03~12-07 입차분 10만건) 중 12-01~07 출차분. 12-01~04 비공연일 기준선(같은 시각 중앙값)."),
          open(os.path.join(OUT, "surge2025.json"), "w"), ensure_ascii=False)
