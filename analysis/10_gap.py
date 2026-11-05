"""공연 종료 -> 출차 몰림 시작 간격 추정. 공연 시작시각/공연 시간은 공연정보 API(3037877) 과거 god 콘서트 기록의 요일 패턴,
몰림 시작은 게이트 파일(API_CPM_008)의 초과 출차. 결과: web/data/gap.json"""
import sys, os, re, glob, html, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
from common import ROOT, OUT
# 1) API 과거 god KSPO DOME 콘서트 기록
its = []
for f in sorted(glob.glob(os.path.join(ROOT, "data/raw_api/perf_*.xml"))):
    its += re.findall(r"<item>(.*?)</item>", open(f, encoding="utf-8").read(), re.S)
def g(it, k):
    m = re.search(rf"<{k}>(.*?)</{k}>", it, re.S); return html.unescape(m.group(1)).strip() if m else ""
god = []
for i in its:
    t = g(i, "title")
    if re.search(r"\bgod\b", t, re.I) and re.search(r"KSPO|체조", g(i, "spatial")) and g(i, "extent"):
        god.append(dict(title=t, venue=g(i, "spatial"), schedule=g(i, "temporalCoverage"), extent=g(i, "extent")))
print(len(god)); [print(x) for x in god]
# 2) 게이트 파일
b = pd.read_csv(os.path.join(ROOT, "data/raw_kcisa/API_CPM_008.csv"), encoding="utf-8-sig")
d = b.DESCRIPTION.str.extract(r"입구:(?P<gin>[^,]*), 입차시간:(?P<tin>[^,]*), 출구:(?P<gout>[^,]*), 출차시간:(?P<tout>.*)")
d["tout"] = pd.to_datetime(d.tout); d["tin"] = pd.to_datetime(d.tin); d["n"] = 1
w = d[(d.tout >= "2025-12-01") & (d.tout < "2025-12-08") & d.gout.str.contains("출구")].set_index("tout")
m5 = w.n.resample("5min").sum()
bd = m5[m5.index.normalize().isin([pd.Timestamp(x) for x in ("2025-12-01", "2025-12-02", "2025-12-03", "2025-12-04")])]
base = bd.groupby(bd.index.hour * 60 + bd.index.minute).median()
res = []
for day, start_hm, dur in (("2025-12-05", (20, 0), 150), ("2025-12-06", (18, 0), 150)):
    t = pd.Timestamp(day); st = t + pd.Timedelta(hours=start_hm[0], minutes=start_hm[1]); end = st + pd.Timedelta(minutes=dur)
    s = m5[(m5.index >= end - pd.Timedelta(minutes=20)) & (m5.index < end + pd.Timedelta(minutes=120))]
    exc = {i: v - base.get(i.hour * 60 + i.minute, 0) for i, v in s.items()}
    idx = list(exc.keys()); on = None
    for k in range(len(idx) - 1):
        if exc[idx[k]] >= 25 and exc[idx[k + 1]] >= 25: on = idx[k]; break
    ent = d[(d.tin >= t + pd.Timedelta(hours=9)) & (d.tin < t + pd.Timedelta(hours=24))].set_index("tin").n.resample("15min").sum()
    peak = ent.idxmax()
    res.append(dict(date=day, start=st.strftime("%H:%M"), end=end.strftime("%H:%M"), onset=on.strftime("%H:%M"),
                    gap_min=int((on - end).total_seconds() / 60), arrival_peak=peak.strftime("%H:%M"),
                    arrival_to_start_min=int((st - peak).total_seconds() / 60)))
for r in res: print(r)
gaps = [r["gap_min"] for r in res]
json.dump(dict(days=res, gap_min=dict(lo=min(gaps), hi=max(gaps), n=len(gaps)), god_records=god,
    method="공연 시작은 API의 같은 아티스트(god) KSPO DOME 과거 요일 패턴(2023·2024 시즌 금 20:00, 토 18:00)과 입차 피크(시작 약 75분 전)로 보강, 공연 시간 150분(API 기록). 몰림 시작은 비공연일 기준선 대비 +25대/5분 이상이 2구간 연속인 첫 구간",
    caveat="2025-12 공연은 API에 없어 시작 시각은 추정. 표본 2회"), open(os.path.join(OUT, "gap.json"), "w"), ensure_ascii=False)
