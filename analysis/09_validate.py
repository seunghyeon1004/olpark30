"""API_CPM_009(시간별 연계) 합성 의심 검정 + API_CPM_008(게이트별) 타당성 점검 + 두 파일 교차검증. 결과: web/data/validation.json"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
from common import ROOT, OUT
a = pd.read_csv(os.path.join(ROOT, "data/raw_kcisa/API_CPM_009.csv"), encoding="utf-8-sig")
b = pd.read_csv(os.path.join(ROOT, "data/raw_kcisa/API_CPM_008.csv"), encoding="utf-8-sig")
a["dt"] = pd.to_datetime(a.ISSUED_DATE)
x = a.DESCRIPTION.str.extract(r"주차대수:(\d+(?:\.\d+)?),\s*방문객:(\d+(?:\.\d+)?)").astype(float)
a["park"], a["vis"] = x[0], x[1]
a["lid"] = a.LOCAL_ID.astype(int)
a = a.sort_values("lid")
out = {}
n = len(a)
out["rows"] = n
out["ratio3_or5_share"] = float(((a.vis / a.park).round(6).isin([3.0, 5.0])).mean())
out["ratio3"] = int(((a.vis / a.park).round(6) == 3).sum()); out["ratio5"] = int(((a.vis / a.park).round(6) == 5).sum())
# 5배 행의 특성: 주말/공연일?
a["wd"] = a.dt.dt.dayofweek; a["show"] = a.DESCRIPTION.str.contains("공연관람객수:[1-9]")
r5 = a[(a.vis / a.park).round(6) == 5]
out["ratio5_weekend_share"] = float((r5.wd >= 5).mean()); out["ratio5_show_share"] = float(r5.show.mean())
r3 = a[(a.vis / a.park).round(6) == 3]; out["ratio3_weekend_share"] = float((r3.wd >= 5).mean())
# LOCAL_ID 순서(최신이 큰 번호)로 주차대수의 +1/-1 수열 비율
d = a.park.diff()
# 같은 순서로 연속 3개 이상 +1/-1 계단
step = d.abs().eq(1)
runs = 0; cur = 0; maxrun = 0
for v in step.values:
    cur = cur + 1 if v else 0
    maxrun = max(maxrun, cur)
    if cur == 3: runs += 1
out["steps_pm1_share"] = float(step.mean()); out["steps_pm1_runs_ge3"] = runs; out["steps_pm1_maxrun"] = int(maxrun)
# +1 수열이 몰려 있는 구간(월별 분포)
a["m"] = a.dt.dt.month
out["steps_pm1_share_by_month"] = {int(k): round(float(v), 3) for k, v in step.groupby(a.m).mean().items()}
out["park_max_by_month"] = {int(k): int(v) for k, v in a.groupby("m").park.max().items()}
# 데이터 연속성: 시간 간격
a = a.sort_values("dt"); gaps = a.dt.diff().dt.total_seconds() / 3600
out["hourly_coverage"] = {int(k): int(v) for k, v in a.groupby("m").size().items()}
out["gap_gt1h_share"] = float((gaps > 1.01).mean())
# 008 점검
dd = b.DESCRIPTION.str.extract(r"입구:(?P<gin>[^,]*), 입차시간:(?P<tin>[^,]*), 출구:(?P<gout>[^,]*), 출차시간:(?P<tout>.*)")
dd["tin"] = pd.to_datetime(dd.tin); dd["tout"] = pd.to_datetime(dd.tout); dd["id"] = b.LOCAL_ID.values
dd["stay"] = (dd.tout - dd.tin).dt.total_seconds() / 60
out["f008_rows"] = len(dd); out["f008_dup_localid"] = int(b.LOCAL_ID.duplicated().sum())
out["f008_dup_full"] = int(dd.duplicated(["gin", "tin", "gout", "tout"]).sum())
out["f008_stay_min_le0"] = int((dd.stay <= 0).sum()); out["f008_stay_lt1min"] = int((dd.stay < 1).sum())
out["f008_stay_median"] = float(dd.stay.median()); out["f008_stay_p90"] = float(dd.stay.quantile(.9)); out["f008_stay_gt24h"] = int((dd.stay > 1440).sum())
out["f008_issued_eq_tin"] = float((pd.to_datetime(b.ISSUED_DATE) == dd.tin).mean())
# 교차검증: 008 로 재구성한 시간별 재차 대수(12-01~07, 입차 후 미출차) vs 009 주차대수 (12-02~12-07 정각)
ev = pd.concat([pd.Series(1, index=dd.tin), pd.Series(-1, index=dd.tout)]).sort_index()
ev = ev.groupby(level=0).sum().sort_index(); occ = ev.cumsum()
hours = pd.date_range("2025-12-03", "2025-12-07 15:00", freq="h")
rec = occ.reindex(occ.index.union(hours)).ffill().reindex(hours)
# 시작 시점 보정: 12-01 이전 입차분이 남아 있으므로 12-03부터만 비교하고 상수 오프셋 추정
nine = a.set_index("dt").park.reindex(hours)
cmp_ = pd.DataFrame({"gate": rec, "hourly": nine}).dropna()
off = (cmp_.hourly - cmp_.gate).median()
cmp_["gate_adj"] = cmp_.gate + off
corr = float(np.corrcoef(cmp_.gate_adj, cmp_.hourly)[0, 1]); mae = float((cmp_.gate_adj - cmp_.hourly).abs().mean())
out["cross_hours"] = len(cmp_); out["cross_corr"] = round(corr, 4); out["cross_mae"] = round(mae, 1); out["cross_offset"] = round(float(off), 1)
out["cross_hourly_mean"] = round(float(cmp_.hourly.mean()), 1)
print(json.dumps(out, ensure_ascii=False, indent=1))
json.dump(out, open(os.path.join(OUT, "validation.json"), "w"), ensure_ascii=False)
