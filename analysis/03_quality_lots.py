"""데이터 품질 점검 + 주차장 혼잡 빈도. 결과: web/data/quality.json, lots.json"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
from common import *

q = []
df = load_inout()
n = len(df)
# 1) 입출차 파일
zero = int((df.stay_min == 0).sum()); neg = int((df.stay_min < 0).sum())
long_ = int((df.stay_min > 24*60).sum()); mx = float(df.stay_min.max())
dup = int(df.duplicated(["입차일시", "출차일시"]).sum())
beyond = int((df.out_dt >= "2024-08-01").sum())
mis = int((df["입차일"] != df.in_dt.dt.strftime("%Y-%m-%d")).sum())
monthly = pd.read_csv(raw("15131671*.csv"), encoding="cp949")
jul24 = int(monthly[(monthly.연도 == 2024) & (monthly.월 == "07월") & (monthly.주차장소 == "올림픽공원")].주차대수.iloc[0])
q.append(dict(id="Q1", dataset="15138735 입출차 정보(2024-07)", severity="높음",
  finding=f"파일 설명은 '동2문/남2문/북2문 주차구역'이라 하나 컬럼은 입차일·입차일시·출차일시 3개뿐이라 문·구역별 분석 불가.",
  suggestion="주차구역(문/주차장 ID) 컬럼 추가. 구역별 출차 대기 분석과 입차 전 구역 추천이 가능해짐."))
q.append(dict(id="Q2", dataset="15138735 vs 15131671 월별주차현황", severity="높음",
  finding=f"2024-07 입출차 {n:,}건 vs 월별주차현황(올림픽공원, 2024-07) {jul24:,}대 → {n/jul24:.1f}배 차이. '1건=1대 입출차'인지 집계 단위 정의가 서로 다른 것으로 보임.",
  suggestion="두 데이터의 집계 단위(입차 건수/실차량/정산 건수)와 대상 주차장 범위를 메타데이터에 명시."))
q.append(dict(id="Q3", dataset="15138735", severity="중간",
  finding=f"출차일시가 조회기간(7월) 밖인 행 {beyond:,}건(최대 {mx/60/24:.1f}일 체류), 입출차 시각 동일(체류 0분) {zero:,}건, 입차일 컬럼과 입차일시 날짜 불일치 {mis}건, 동일 분 입·출차쌍 중복 {dup:,}건(차량 식별자가 없어 오류와 정상 동시 입차를 구분할 수 없음).",
  suggestion="장기주차 표기 규칙(출차일시 공란/장기 플래그)과 0분 체류(회차·오입차) 처리 기준 공개."))
q.append(dict(id="Q4", dataset="15138735", severity="낮음",
  finding="분 단위 시각, 차량 식별자 없음(익명화 의도로 보임), 월 1개 파일만 제공(2024-07). 2025년분은 포털 파일로는 없고 문화공공데이터광장의 별도 경로(API 또는 파일 사본)로만 제공.",
  suggestion="연월별 파일 추가 개방 또는 일별 파일 병행. 출차 대기(대기열) 분석에는 게이트 통과 시각과 정산 시각 분리 필요."))
# 2) 혼잡도
c = pd.read_csv(raw("15164156*.csv"), encoding="cp949")
c["dt"] = pd.to_datetime(c["등록일"] + " " + c["등록시간"])
idmap = c.groupby("주차장아이디")["주차구역"].nunique()
multi = c.groupby("주차장아이디")["주차구역"].unique()
bad = {int(k): list(map(str, v)) for k, v in multi.items() if len(v) > 1}
ndays = c["등록일"].nunique()
q.append(dict(id="Q5", dataset="15164156 주차장 혼잡도", severity="높음",
  finding=f"{len(c)}건이 {ndays}개 일자에만 존재(2025-02-12~2026-08-12)하고, 상태가 바뀔 때만 기록되는 이벤트 로그 형태라 시계열 혼잡도로 쓰기 어려움. 주차장아이디↔주차구역 매핑 불일치: {bad}.",
  suggestion="고정 간격(예: 5분) 스냅샷 + 주차장 마스터(아이디·구역명·면수) 동봉. '혼잡' 판정 기준(점유율 임계값) 명시."))
t = c["등록시간"].value_counts().head(3)
q.append(dict(id="Q6", dataset="15164156", severity="낮음",
  finding=f"등록시간이 '00:06:06'처럼 일괄처리 시각으로 보이는 값이 있음(예: 2026-06-06 만차 7건 동시각). 실제 만차 발생시각인지 입력시각인지 불명.",
  suggestion="발생시각과 기록시각 컬럼 분리."))
# 3) 공연정보 파일
p = pd.read_csv(raw("15149169*.csv"), encoding="cp949")
p["d"] = pd.to_datetime(p["공연일자"], errors="coerce")
day1 = float((p.d.dt.day == 1).mean())
ents = int(p["공연제목"].str.contains("&lt;|&gt;|&amp;").sum())
jul = p[(p.d >= "2024-07-01") & (p.d <= "2024-07-31")]
q.append(dict(id="Q7", dataset="15149169 영문 공연정보", severity="높음",
  finding=f"파일 전체 {len(p)}행(2018~2026)이며 2024-07은 3개 일자(7/1·7/12·7/20)만 기재. 같은 달 실제 출차 서지가 관측된 7/13·7/14·7/21·7/28(분석 참고)은 공연 기록이 없어 누락 또는 일자 대표값 기재로 추정. 시작/종료 시각·공연장 컬럼 없음, 제목에 HTML 엔티티 {ents}건.",
  suggestion="공연일(YYYY-MM-DD)·공연장·개시/종료 예정시각·예상 관객수 컬럼 제공. 출차 예측의 핵심 입력이 됨."))
# 4) 잔디시설
g = pd.read_csv(raw("15143220*.csv"), encoding="cp949")
dup_g = int(g.duplicated(["장소", "개방시간", "개방내용"]).sum())
q.append(dict(id="Q8", dataset="15143220 잔디시설정보", severity="중간",
  finding=f"동일 장소·내용 중복 {dup_g}건(나홀로나무), '개방시간' 컬럼에 일자 범위(06-01 ~ 10-31)와 '연중 상시개방'이 혼재, 잔디통제시기(11-01~익년05-31)가 별도 행. 시각(예: 09:00~18:00)·야간 개방 여부 없음.",
  suggestion="장소·개방시작일·개방종료일·일일 개방/폐쇄 시각을 별도 컬럼으로 분리하면 시간대별 산책 코스 추천 가능."))
q.append(dict(id="Q9", dataset="공고문/포털 메타", severity="낮음",
  finding="공고문은 '57종'이라 하나 포털 조회(키워드 '한국체육산업개발주식회사')는 58건(파일 30+API 28). 15164156 등 일부는 수정일(2026-09-22) 이후 갱신 이력 불명.",
  suggestion="공고문·포털의 데이터 수 기준 일치와 변경이력 공개."))
# 10) 2025 연계 API 가용성 + CSV 사본 점검
logp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kcisa_retry.log")
lines = [l.strip() for l in open(logp, encoding="utf-8") if l.strip()] if os.path.exists(logp) else []
q.append(dict(id="Q10", dataset="15164822·15159093 연계/입출차 API(문화공공데이터광장 경유)", severity="높음",
  finding=("data.go.kr에서는 LINK 유형이라 인증키를 받을 수 없고, 문화공공데이터광장(culture.go.kr) 별도 활용신청으로 키를 받아야 함. 키 발급 후 호출 "
           + (f"{len(lines)}회({lines[0].split()[0]}~{lines[-1].split()[0]}, 2026-11-05, 2분 간격)" if lines else "여러 차례") +
           " 모두 HTTP 504·빈 응답(게이트웨이 10초 대기 후 종료, 잘못된 키는 즉시 403). 같은 데이터가 문화공공데이터광장 '파일데이터(CSV)'로도 공개되어 이를 사용했으나, "
           "이 경로는 포털 안내에 없어 찾기 어려움."),
  suggestion="API 가용성 모니터링, data.go.kr 상세 페이지에 '파일데이터(CSV) 사본 위치'와 키 발급 경로 명시, 출력 항목(DESCRIPTION 한 칸에 모든 값이 뭉쳐 있음)을 컬럼으로 분리."))
V = json.load(open(os.path.join(OUT, "validation.json")))
q.append(dict(id="Q11", dataset="API_CPM_009 연계 CSV(15164822), 시간별 7,803행", severity="높음",
  finding=(f"(추정, 확인 요청) 방문객은 주차대수의 정확히 3배(평일, {V['ratio3']:,}행, 주말 0%) 또는 5배({V['ratio5']:,}행, 주말 {V['ratio5_weekend_share']:.0%})로 전 행이 일치해, 관측값이 아니라 요일 규칙을 곱한 파생값으로 보임. "
           f"또 11~12월 시간별 행은 11월 {V['hourly_coverage']['11']}행·12월 {V['hourly_coverage']['12']}행(월 약 720시간 중 약 1/3)이고, 주차대수가 ±1씩 변하는 계단이 이 두 달 스텝의 {V['steps_pm1_share_by_month']['11']:.0%}·{V['steps_pm1_share_by_month']['12']:.0%}(1~10월은 2~8%), 최대 {V['steps_pm1_maxrun']}행 연속이며, 공식 미리보기 10행(ID 7794~7803)은 28, 27, …, 19로 시간을 거슬러 정확히 +1씩 늘어남. 보간 또는 자리표시 값일 가능성이 있어 확인을 요청드림. "
           f"반면 12-03~07의 {V['cross_hours']}시간은 게이트별 파일에서 재구성한 재차 대수와 상관 {V['cross_corr']}(평균 {V['cross_hourly_mean']:,.0f}대, 평균절대오차 약 {V['cross_mae']:.0f}대)로 실측으로 보여, 본 서비스는 이 구간(공연명, 관람객수, 최대 주차대수)만 사용함."),
  suggestion="방문객 산출식과 보간·결측 처리 방식 공개, 합성이나 보간 행에는 구분 플래그, 누락 시간대 보완."))
q.append(dict(id="Q12", dataset="API_CPM_008 게이트별 입출차 CSV(15159093)", severity="중간",
  finding=(f"CSV 사본이 {V['f008_rows']:,}행으로 끊김(상한으로 보임). 입차시각 2025-11-03~12-07만 담겨 있어 실제 출차가 충분히 관측되는 날은 12-01~07 7일뿐이고, 12-07은 16:08 이후 입차분이 없어 저녁 출차가 과소 집계됨. "
           f"게이트·차선 정보(예: 북2문출구#2)는 우수하고 점검 결과도 양호: ID·행 중복 {V['f008_dup_localid']}건, 체류 0분 이하 {V['f008_stay_min_le0']}건, 1분 미만 {V['f008_stay_lt1min']}건, 중앙 체류 {V['f008_stay_median']:.0f}분(상위 10% 경계 {V['f008_stay_p90']:.0f}분), 24시간 초과 {V['f008_stay_gt24h']:,}건(장기주차로 추정)."),
  suggestion="월별 분할 파일(행 상한 해제)로 2025년 전체 게이트 데이터 개방. 출차 대기 분석에는 게이트 통과와 정산 시각 분리 필요."))
P = json.load(open(os.path.join(OUT, "perf_api.json")))
q.append(dict(id="Q13", dataset="3037877 올림픽공원 공연정보 API(KSCperf)", severity="중간",
  finding=(f"{P['total']:,}건이 모두 2025-01-02에 일괄 등록되어 있고 제목에 연도가 있는 공연은 2010~2024년뿐으로, 2025-12 콘서트(관람객 2만 명대)가 들어 있지 않음. 날짜 구조 필드가 없고 시작 시각은 자유 텍스트(예: '(금) 20:00 / (토) 18:00 / (일) 17:00', 연월일 없음), "
           f"공연 시간(extent)은 {P['with_extent']:,}건만 기재, 본문(description)은 HTML 조각임. 반면 공연장·시작 시각·공연 시간이 있어 종료 시각 추정에 유용했음(KSPO DOME 공연 시간 기록 {P['by_venue']['KSPO DOME(체조경기장)']['n']}건, 중앙값 {P['by_venue']['KSPO DOME(체조경기장)']['median']:.0f}분)."),
  suggestion="공연일(YYYY-MM-DD), 공연장, 시작·종료 시각을 컬럼으로 분리하고 최신 공연까지 갱신. 요일 규칙(금·토·일)과 회차별 시각은 회차 행으로 분해."))
json.dump(q, open(os.path.join(OUT, "quality.json"), "w"), ensure_ascii=False, indent=1)
for x in q: print(x["id"], x["finding"][:110])

# 주차장 혼잡 빈도 (이벤트 로그 기준)
lab = {"원활": 0, "혼잡": 1, "만차": 2}
rows = []
for z, g_ in c.groupby("주차구역"):
    k = len(g_)
    rows.append(dict(zone=z, records=k, full=int((g_.혼잡도 == "만차").sum()), busy=int((g_.혼잡도 == "혼잡").sum()),
                     ok=int((g_.혼잡도 == "원활").sum())))
L = pd.DataFrame(rows)
L["bad_share"] = ((L.full + L.busy) / L.records).round(3)
L["full_share"] = (L.full / L.records).round(3)
L = L.sort_values("full_share", ascending=False)
print(L.to_string())
json.dump(dict(zones=L.to_dict("records"),
               caveat="이벤트 로그(상태 변경 시에만 기록) 기준 비율이므로 '시간 비중'이 아닌 '기록 중 비중'. 참고용."),
          open(os.path.join(OUT, "lots.json"), "w"), ensure_ascii=False)
# 월별 계절성
m = monthly.copy(); m["m"] = m.월.str[:2].astype(int)
op = m[m.주차장소 == "올림픽공원"].groupby("m").주차대수.mean().round().astype(int)
json.dump(dict(monthly_avg_op={int(k): int(v) for k, v in op.items()}, years="2023-2025", place="올림픽공원"),
          open(os.path.join(OUT, "monthly.json"), "w"), ensure_ascii=False)
