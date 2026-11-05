"""출차 서지(공연 종료 후 몰림) 검출 + 대기시간 큐 모델 + 홀드아웃 검증. 모든 대기시간은 추정치."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
from common import *

df = load_inout()
ex = exits_5min(df)
tab = ex.to_frame("n")
tab["d"] = tab.index.normalize(); tab["hm"] = tab.index.hour*60 + tab.index.minute
tab["wknd"] = tab.index.dayofweek >= 5
pv = tab.pivot(index="hm", columns="d", values="n").fillna(0)

EV0, EV1 = 19*60+30, 23*60       # 저녁 탐색 구간
days = list(pv.columns)
ev_excess = {}
# 1차 기준선: 요일유형별 중앙값(전체 일자 사용 -> 서지일이 소수이므로 중앙값은 안정적)
def base_for(d, pool):
    same = [x for x in pool if (x.dayofweek >= 5) == (d.dayofweek >= 5) and x != d]
    return pv[same].median(axis=1).rolling(3, center=True, min_periods=1).mean()
for d in days:
    b = base_for(d, days)
    ex_ = (pv[d] - b).clip(lower=0)
    ev_excess[d] = ex_.loc[EV0:EV1].sum()
surge_days = [d for d in days if ev_excess[d] >= 350 and pv[d].loc[EV0:EV1].max() >= 85]
pool = [d for d in days if d not in surge_days]
rows = []
for d in surge_days:
    b = base_for(d, pool)
    n = pv[d]; e = (n - b)
    # 서지 코어: 저녁 구간(18:00~)에서 5분 출차대수 n 이 (피크의 60% 이상)인 연속 구간(1빈 공백 허용), 양쪽 1빈 확장
    ev = n.loc[18*60:23*60+55]
    pk = ev.loc[EV0-90:EV1].max(); pk_t = ev.loc[EV0-90:EV1].idxmax()
    thr = 0.6 * pk
    lo = pk_t
    while (lo - 5 in ev.index) and (ev[lo - 5] >= thr or (lo - 10 in ev.index and ev[lo - 10] >= thr)): lo -= 5
    hi = pk_t
    while (hi + 5 in ev.index) and (ev[hi + 5] >= thr or (hi + 10 in ev.index and ev[hi + 10] >= thr)): hi += 5
    lo -= 5; hi += 5
    seg = [x for x in range(lo, hi + 1, 5)]
    t0, t1 = seg[0], seg[-1] + 5
    excess = float(e[seg].clip(lower=0).sum())
    peak = float(pk)
    top3 = n[seg].sort_values(ascending=False).head(3).mean()
    cap = float(top3 / 5)
    tot_excess_evening = float(e.loc[EV0-90:EV1+60].clip(lower=0).sum())
    rows.append(dict(date=str(d.date()), dow=int(d.dayofweek), t0=int(t0), t1=int(t1), dur=int(t1 - t0),
                     excess=round(excess), excess_evening=round(tot_excess_evening), peak5=int(peak), cap_per_min=round(cap, 1)))
S = pd.DataFrame(rows).sort_values("date")
print(S.to_string())

# --- 큐 모델: 차량이 t0부터 w분 동안 균등하게 출차 준비(펄스), 처리율 C(대/분), FIFO ---
def simulate(E, C, w, step=1.0, horizon=240):
    """반환: 준비시각 r(분, t0 기준)별 대기시간(분). 균등 도착률 E/w, 서비스 C."""
    # 분 단위 이산 시뮬레이션
    arr = np.zeros(horizon); arr[:int(w)] = E / w
    q = 0.0; waits = {}
    cumA = np.cumsum(arr); cumS = np.zeros(horizon)
    served = 0.0
    for m in range(horizon):
        q += arr[m]
        s = min(q, C); q -= s; served += s; cumS[m] = served
    # 준비시각 r에서 준비한 차량의 대기 = 누적서비스가 cumA[r]에 도달하는 시각 - r
    out = []
    for r in range(horizon):
        target = cumA[r]
        if target <= 1e-9: out.append(0.0); continue
        k = int(np.searchsorted(cumS, target - 1e-9))
        out.append(max(0.0, (k + 1) - r - 1))
    return np.array(out), cumS

# 홀드아웃(leave-one-day-out): 다른 날들의 평균 용량 C 와 해당일 초과 출차량 E 만으로 코어 창 안에서
# '초과 출차 90% 도달 시점(코어 시작 기준 분)'을 예측하고 실측과 비교. (표본 5일: 정합성 점검이지 강한 검증이 아님)
def t90_obs(r):
    d = pd.Timestamp(r.date); n = pv[d]; b = base_for(d, pool)
    ee = (n - b).clip(lower=0).loc[r.t0:r.t1 - 5]
    c = ee.cumsum() / ee.sum()
    return int((c >= 0.9).idxmax() - r.t0 + 5)
res = []
for i, r in S.iterrows():
    others = S[S.date != r.date]
    C = others.cap_per_min.mean()
    base_rate = float(np.mean([ (pv[pd.Timestamp(r.date)].loc[:r.t0-5].tail(6).mean())/5 ]))  # 직전 30분 일반 출차율(대/분)
    Ceff = max(C - base_rate, 1.0)
    _, cumS = simulate(r.excess, Ceff, 10)
    pred = int(np.searchsorted(cumS, 0.9 * r.excess)) + 1
    obs = t90_obs(r)
    res.append(dict(date=r.date, obs_t90=obs, pred_t90=pred, err=pred - obs))
H = pd.DataFrame(res); print(H.to_string())
mae = float(H.err.abs().mean()); print("MAE(분)", round(mae, 1))

# 일반화 용량(중앙값) 및 범위
cap_med = float(S.cap_per_min.median()); cap_lo = float(S.cap_per_min.min()); cap_hi = float(S.cap_per_min.max())
size_q = {"소": float(S.excess.quantile(0.1)), "중": float(S.excess.median()), "대": float(S.excess.quantile(0.9))}
print("size", size_q, "cap", cap_lo, cap_med, cap_hi)

# 경험적 예측기(홀드아웃): 다른 날들의 t90 평균
H["emp_pred"] = [round(H.obs_t90[H.index != i].mean()) for i in H.index]
emp_mae = float((H.emp_pred - H.obs_t90).abs().mean()); print("경험적 평균 예측기 MAE(분)", round(emp_mae, 1))
t90 = [int(x) for x in H.obs_t90]
T = dict(lo=min(t90), med=float(np.median(t90)), hi=max(t90))
# 앱용 대기표: 서지 시작 후 s분에 줄에 합류 -> 대기 = 큐가 비는 시각(T) - s  (FIFO 펄스 가정, 경계값 3개)
wait_axis = list(range(0, 66, 5))
wait_tab = {k: [max(0, int(round(v - s))) for s in wait_axis] for k, v in T.items()}
# 서지 프로파일(서지 시작 정렬, 5분 단위 출차대수) + 누적비율
prof = {}; cumf = {}
for _, r in S.iterrows():
    d = pd.Timestamp(r.date); n = pv[d]; b = base_for(d, pool)
    prof[r.date] = [int(n.get(r.t0 + 5*k, 0)) for k in range(-6, 25)]
    ee = (n - b).clip(lower=0).loc[r.t0:r.t1 - 5]
    cumf[r.date] = [round(float(x), 3) for x in (ee.cumsum() / ee.sum()).values]
base_prof = {}
for lab, w_ in (("주말", True), ("평일", False)):
    pool_ = [d for d in pool if (d.dayofweek >= 5) == w_]
    base_prof[lab] = {int(k): round(float(v), 1) for k, v in pv[pool_].median(axis=1).items()}
json.dump(dict(
    surge_days=S.to_dict("records"),
    holdout_queue=H.to_dict("records"), holdout_queue_mae_min=round(mae, 1), holdout_empirical_mae_min=round(emp_mae, 1),
    t_clear=T, wait_axis_min=wait_axis, wait_table=wait_tab,
    cap=dict(lo=cap_lo, med=cap_med, hi=cap_hi), size_excess=size_q,
    profiles=prof, profile_axis_min=[5*k for k in range(-6, 25)], cum_fraction=cumf, baseline=base_prof,
    n_days_total=len(days), n_surge_days=len(S),
    method=dict(
        surge_def="저녁(19:30~23:00) 요일유형 기준선(비서지일 중앙값) 대비 초과 출차 합 350대 이상이고 5분 최대 85대 이상인 날",
        core_def="저녁 5분 출차 피크의 60% 이상인 연속 구간(양쪽 1빈 확장) = 서지 코어",
        capacity_def="코어 상위 3개 5분 출차대수 평균/5 (대/분). 포화 가정의 하한",
        t_clear_def="코어 시작 후 초과 출차의 90%가 빠져나가는 시점(분). 5일 실측의 최소/중앙/최대",
        wait_def="서지 시작 후 s분에 줄에 합류하면 큐가 비는 시점(T)까지 남은 시간(FIFO 펄스 가정). 추정치"),
), open(os.path.join(OUT, "surge_model.json"), "w"), ensure_ascii=False)
print(T, wait_tab)
