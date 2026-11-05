import sys, os, json, html
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
M = json.load(open(os.path.join(OUT, "surge_model.json"))); Q = json.load(open(os.path.join(OUT, "quality.json")))
W = json.load(open(os.path.join(OUT, "whatif.json")))["scenario"]
GP = json.load(open(os.path.join(OUT, "gap.json")))
S25 = json.load(open(os.path.join(OUT, "surge2025.json"))); D25 = S25["days"]; T25 = S25["t_clear"]; L = json.load(open(os.path.join(OUT, "lots.json")))
e = html.escape
S = M["surge_days"]; T = M["t_clear"]
srows = "".join(f"<tr><td>{r['date']}</td><td>{'토일'[r['dow']-5]}</td><td>{r['peak5']}</td><td>{r['cap_per_min']}</td><td>{r['excess']:,}</td><td>{r['dur']}</td></tr>" for r in S)
wt = M["wait_table"]; ax = M["wait_axis_min"]
sel = [0, 10, 20, 30, 40]
wrows = "".join(f"<tr><td>{s}분 후 합류</td><td>{wt['lo'][s//5]}</td><td><b>{wt['med'][s//5]}</b></td><td>{wt['hi'][s//5]}</td></tr>" for s in sel)
qrows = "".join(f"<tr><td>{e(q['id'])}</td><td>{e(q['dataset'])}</td><td>{e(q['finding'])}</td><td>{e(q['suggestion'])}</td></tr>" for q in Q)
datasets = [
 ("15138735","올림픽공원 입출차 정보(2024-07)","중소 규모 출차 서지·대기 추정","사용"),
 ("15164822","올림픽공원 2025 차량입출차·공연·날씨 연계 데이터","시간별 주차대수·공연명·관람객수(2025)","사용(파일 사본)"),
 ("15159093","올림픽공원 입출차정보 전체구역(2025)","게이트·차선별 출차, 대규모 서지 분석","사용(파일 사본)"),
 ("15168686","실시간 주차현황","입차 전 탭에 현재 주차 대수 표시","사용(실시간)"),
 ("15131671","월별주차현황","계절성, 입출차 파일 집계 검증","사용"),
 ("15164156","주차장 혼잡도 정보","주차구역별 혼잡 기록 참고","사용"),
 ("15143220","잔디시설정보","산책 코스 개방기간(계절) 반영","사용"),
 ("15149169","영문 공연정보","공연일 대조, 누락 확인","사용"),
 ("3037877","올림픽공원 공연정보(API, 인증키)","과거 공연의 공연장·시작 시각·공연 시간으로 종료 시각 추정","사용(API)"),
 ("15056986, 15024888","장미광장, 수목정보(API)","산책 코스 볼거리","연동 예정"),
]
drows = "".join(f"<tr><td>{a}</td><td>{b}</td><td>{c}</td><td>{d}</td></tr>" for a,b,c,d in datasets)
def _v(n): return int(os.path.getmtime(os.path.join(ROOT, "submission", "img", n)))
img = lambda n, cap: f'<figure><img src="img/{n}?v={_v(n)}"><figcaption>{cap}</figcaption></figure>'
def _w25(f):
    v = [d['whatif'][f] for d in D25 if not d['partial']]
    return sum(v)/len(v), min(v), max(v)
wrows5 = "".join(f"<tr><td>서지 차량의 {int(float(f)*100)}%가 20~55분 늦게 출발</td><td>{W[f]['mean']}% ({W[f]['lo']}~{W[f]['hi']}%)</td><td>{_w25(f)[0]:.1f}% ({_w25(f)[1]:.1f}~{_w25(f)[2]:.1f}%)</td></tr>" for f in ('0.1','0.2','0.3'))
rows25 = "".join(f"<tr><td>{d['date']}{' (일부)' if d['partial'] else ''}</td><td>{d['audience']:,}</td><td>{d['peak5']}</td><td>{d['peak_per_min']}</td><td>{d['excess']:,}</td><td>{d['dur']}</td><td>{d['t90']}</td></tr>" for d in D25)
_full = [d for d in D25 if not d['partial']]
G = {k: sum(d['gate_share'].get(k, 0) for d in _full)/len(_full) for k in ('남2문','동2문','북2문')}
G['기타'] = 100 - sum(G.values())
doc = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>올팍 30분 활용사례 설명서</title>
<meta name="description" content="공연 후 올림픽공원 출차 대기를 공공데이터로 추정하고 산책 코스로 바꾸는 서비스의 활용사례 설명서">
<style>
/* Hallmark · shape: app screen · genre: editorial · theme: custom · job: try · idea: "공연 후 출차 대기를 산책으로 바꾸는 서비스의 활용사례 설명서" · vibe: "차분한 공공 보고서, 숫자와 표 중심"
 * paper: oklch(98.5% 0.006 150) · accent: oklch(46% 0.1 155) · display: 시스템 고딕 · body: 시스템 고딕 · hero: none · nav: none · footer: none · imagery: 앱 화면 캡처 · signature: 실측 서지 표와 대기시간 표
 * axes: 연녹회색/시스템고딕/녹색 · posture: restrained · contrast: pass · fold: pass · v2.0.0 */
/* Hallmark · pre-emit critique: P4 H4 E4 S4 R4 V3 · weakest: V, 인쇄 문서라 구조 변주 여지가 적어 표와 숫자로 승부 */
:root {{
  --font-ui: "Apple SD Gothic Neo", "Noto Sans KR", "Malgun Gothic", sans-serif;
  --color-paper: oklch(99.2% 0.003 150);
  --color-ink: oklch(24% 0.02 155);
  --color-muted: oklch(44% 0.02 155);
  --color-line: oklch(84% 0.012 150);
  --color-accent: oklch(42% 0.1 155);
  --color-heading: oklch(30% 0.07 155);
  --color-accent-ink: oklch(97% 0.01 150);
  --color-accent-soft: oklch(93% 0.04 155);
  --color-warn-soft: oklch(94% 0.05 80);
  --color-warn: oklch(46% 0.1 70);
}}
@page {{ size: A4; margin: 16mm 15mm; }}
html {{ overflow-x: clip; caret-color: var(--color-accent); scrollbar-color: var(--color-line) var(--color-paper); }}
::selection {{ background: var(--color-accent-soft); color: var(--color-ink); }}
body {{ overflow-x: clip; margin: 0; background: var(--color-paper); font-family: var(--font-ui); color: var(--color-ink); font-size: 10pt; line-height: 1.5; }}
h1 {{ font-size: 24pt; margin: 0 0 2pt; color: var(--color-accent); text-wrap: balance; }}
h2 {{ font-size: 14pt; border-bottom: 2px solid var(--color-accent); padding-bottom: 4pt; margin: 16pt 0 8pt; color: var(--color-heading); break-after: avoid; text-wrap: balance; }}
h3 {{ font-size: 11pt; margin: 10pt 0 4pt; break-after: avoid; }}
.sub {{ color: var(--color-muted); margin-bottom: 8pt; }}
table {{ border-collapse: collapse; width: 100%; font-size: 8.8pt; margin: 6pt 0; break-inside: avoid; }}
table.long {{ break-inside: auto; }}
.keep {{ break-inside: avoid; }}
td, th {{ border: 1px solid var(--color-line); padding: 3pt 7pt; text-align: left; vertical-align: top; }}
th {{ background: var(--color-accent-soft); font-weight: 600; }}
tr {{ break-inside: avoid; }}
.box {{ background: var(--color-warn-soft); border: 1px solid var(--color-line); border-radius: 8px; padding: 8pt 12pt; margin: 8pt 0; font-size: 9.5pt; break-inside: avoid; }}
.shots {{ display: flex; gap: 8pt; justify-content: space-between; }}
figure {{ margin: 0; width: 24%; break-inside: avoid; }}
figure img {{ width: 100%; border: 1px solid var(--color-line); border-radius: 8px; }}
figcaption {{ font-size: 9pt; color: var(--color-muted); text-align: center; margin-top: 4pt; }}
.meta {{ font-size: 9.5pt; color: var(--color-muted); }}
.kpi {{ display: flex; gap: 8pt; }}
.kpi div {{ flex: 1; border: 1px solid var(--color-line); border-radius: 8px; padding: 8pt; text-align: center; font-size: 9.5pt; }}
.kpi b {{ display: block; font-size: 17pt; color: var(--color-accent); }}
ul {{ margin: 4pt 0 4pt 16pt; padding: 0; }}
</style></head><body>
<h1>올팍 30분</h1>
<div class="sub">공연이 끝난 뒤 출차 대기 시간을 공원 산책으로 바꾸는 서비스, 공공데이터 활용사례 설명서</div>
<div class="meta">한국체육산업개발(주) 공공데이터 활용 경진대회. 작성자 백승현(개인). 개방 데이터 9종을 사용하고(파일 7종, 실시간 API 1종, 공연정보 API 1종) 2종은 연계 예정입니다.</div>

<h2>1. 배경과 문제</h2>
<p>대형 공연이 끝나면 올림픽공원 주차장 출차가 한꺼번에 몰립니다. 주최 측이 예시로 든 '혼잡 예측·분산 안내'는 혼잡을 <b>피하게</b> 하는 접근입니다. 올팍 30분은 한 걸음 더 나아가 혼잡을 <b>쓸모 있게</b> 만듭니다. 출차 대기 시간을 정확히 추정해 알려 주고, 그 시간만큼 바로 옆 공원을 걷는 코스를 구성합니다. 이용자는 차 안에서 기다리는 대신 걷고, 기관은 출차 피크가 분산되며 공원 체류가 늘어납니다.</p>
<p>실측으로 확인한 규모: 2025-12 관람객 2만 명대 콘서트(12-05, 12-06)에는 주차장에 3,000대 이상이 찼고, 몰림 구간의 초과 출차는 약 {D25[0]['excess']:,}대와 {D25[1]['excess']:,}대, 90%가 빠지기까지 {T25['lo']}~{T25['hi']}분이 걸렸습니다.</p>
<div class="kpi"><div><b>{T['lo']}~{T['hi']}분</b>중소 규모 90% 해소(2024-07, 5회)</div><div><b>{T25['lo']}~{T25['hi']}분</b>대규모 90% 해소(2025-12, 2회)</div><div><b>{max(d['excess'] for d in D25):,}대</b>대규모 몰림 구간 초과 출차</div><div><b>{len(Q)}건</b>데이터 품질 개선 제안</div></div>

<h2>2. 활용 데이터</h2>
<table><tr><th>번호</th><th>데이터</th><th>활용</th><th>상태</th></tr>{drows}</table>
<div class="box">2025년 데이터(연계 15164822, 게이트별 15159093)는 공공데이터포털에서 LINK 유형이라 포털 키가 없고, 문화공공데이터광장(culture.go.kr)의 API는 서비스키를 받아도 HTTP 504로 응답하지 않았습니다(품질 제안 Q10). 같은 데이터가 그 사이트의 파일데이터(CSV)로도 공개되어 있어 이를 사용했습니다. 실시간 주차현황(15168686)은 기관이 공개 페이지에 게시한 엔드포인트로 연동되어 입차 전 탭에 표시됩니다. 공연정보(3037877)는 서비스키로 정상 응답하여 공연 시작 시각과 공연 시간 분석에 사용했습니다(2025-12 공연은 이 API에 없음, 품질 제안 Q13).</div>

<h2>3. 서비스 화면 (모바일 우선)</h2>
<div class="shots">{img('s1.png','지금 출차: 규모와 경과 분 → 대기 상한')}{img('s2.png','산책 코스: 남는 시간·날짜 반영')}{img('s3.png','입차 전: 서지 요약·구역 혼잡 기록')}{img('s4.png','근거: 방법·검증·품질 제안')}</div>
<h3>이용 흐름</h3>
<ul><li><b>입차 전</b>: 공연 서지 규모, 구역별 혼잡 기록, 실시간 주차 대수를 보고 일정을 계획합니다.</li>
<li><b>공연 후</b>: 공연 규모(중소, 대규모)와 출차 줄이 몰리기 시작한 뒤 경과 분을 고르면 "지금 줄에 서면 최대 40분(대규모는 최대 약 103분), 20분 뒤면 최대 20분"처럼 대기 상한을 보여 줍니다.</li>
<li><b>대기가 길면</b>: 날짜(계절)·남는 시간에 맞춘 산책 코스를 제안하고, 몰림이 풀린 뒤 돌아오도록 안내합니다.</li></ul>

<h2>4. 분석 방법과 결과</h2>
<h3>4-1. 서지 검출과 처리율</h3>
<p>입출차 215,528건(2024-07)에서 5분 단위 출차 대수를 만들고, 저녁(19:30~23:00)에 평소(요일유형 중앙값)보다 크게 늘어난 날을 서지일로 정의했습니다. 서지 코어는 저녁 5분 출차 피크의 60% 이상인 연속 구간입니다.</p>
<table><tr><th>날짜</th><th>요일</th><th>5분 최대(대)</th><th>처리율(대/분)</th><th>초과 출차(대)</th><th>코어 길이(분)</th></tr>{srows}</table>
<p>7/20·7/21은 5분 출차대수가 약 126~132대에서 30분 가까이 평평하게 이어져 출구 처리율이 포화된 것으로 보입니다(분당 약 26대). 이는 대기열이 있었다는 간접 증거이며, 직접 관측은 아닙니다.</p>
<h3>4-1b. 대규모 콘서트(2025-12, 게이트별 데이터)</h3>
<p>2025 게이트별 입출차 파일(차량별 출구·차선, 10만 건, 12-01~07 출차 관측)에서 비공연일(12-01~04) 같은 시각 중앙값을 기준선으로 뺀 초과 출차를 구했습니다. 12-07은 16:08 이후 입차분이 파일에 없어 일부만 반영되므로 90% 해소 시간 통계에서는 제외했습니다. 시간별 연계 데이터는 12-05~07(공연명, 관람객수, 최대 주차대수)만 사용했고, 게이트 파일에서 재구성한 재차 대수와 12-03~07 112시간 상관 0.94로 교차 확인했습니다. 연계 데이터의 다른 구간은 보간 가능성이 있어 쓰지 않았습니다(품질 제안 Q11).</p>
<table><tr><th>날짜</th><th>관람객(명)</th><th>5분 최대(대)</th><th>대/분</th><th>초과 출차(대)</th><th>몰림 길이(분)</th><th>90% 해소(분)</th></tr>{rows25}</table>
<p>출구별 비중(서지 구간, 12-05·06 평균): 남2문 {G['남2문']:.0f}%, 동2문 {G['동2문']:.0f}%, 북2문 {G['북2문']:.0f}%(각 2차선), 서2·남4·남3·서1문 합계 {G['기타']:.0f}%(각 1차선). 차선별 1분 최대는 8~12대로 물리적 한계에 가깝지만, 모든 차선이 계속 포화된 것은 아닙니다.</p>
<h3>4-1c. 공연 종료와 출차 몰림 시작의 간격</h3>
<p>공연정보 API(3037877)에는 2025-12 공연이 없습니다. 대신 같은 아티스트(god)의 과거 KSPO DOME 콘서트 기록 {len(GP['god_records'])}건이 모두 공연 시간 150분이고, 가장 최근 2023·2024 시즌은 둘 다 금 20:00, 토 18:00, 일 17:00이어서 12-05(금)와 12-06(토)의 시작을 20:00과 18:00으로 보았습니다. 게이트 파일의 입차 피크가 두 날 모두 시작 약 75분 전(18:45, 16:45)이라 이 가정과 맞습니다. 종료는 22:30과 20:30이고, 비공연일 기준선 대비 초과 출차가 처음 연속 상승한 시각은 22:55와 20:55로, <b>종료 후 {GP['gap_min']['lo']}분</b>이었습니다(표본 2회, 시작 시각은 추정). 앱은 사용자가 공연 시작 시각을 넣으면 종료와 몰림 시작 시각을 이 규칙으로 보여 줍니다.</p>
<h3>4-2. 대기시간 추정</h3>
<p>몰림 시작 후 s분에 줄에 서면 큐가 빌 때까지 남은 시간을 대기의 <b>상한</b>으로 봅니다(선입선출, 한꺼번에 도착 가정이므로 실제 도착이 분산되면 이보다 짧습니다). 큐가 비는 시점은 실측에서 초과 출차의 90%가 빠져나간 시간입니다. 중소 규모는 최소 {T['lo']}분, 중앙 {T['med']:.0f}분, 최대 {T['hi']}분(5회), 대규모는 {T25['lo']}~{T25['hi']}분(2회)입니다. <b>모든 값은 추정치</b>입니다. 아래 표는 중소 규모입니다.</p>
<table><tr><th>합류 시점</th><th>낙관(분)</th><th>중앙(분)</th><th>보수(분)</th></tr>{wrows}</table>
<h3>4-3. 검증 (하루 제외 교차검증)</h3>
<p>용량 기반 큐 모델은 90% 해소 시점을 평균 {M['holdout_queue_mae_min']}분 틀려 정확도가 낮았고, 단순 경험 평균 예측은 평균 오차 {M['holdout_empirical_mae_min']}분이라 후자를 채택했습니다. 표본이 중소 규모 5일이고 대규모는 2회뿐이라 <b>정합성 점검 수준이며 강한 검증이 아닙니다</b>. 중소 규모에서는 해소 시간이 30~45분으로 안정적이었지만, 2025-12 대규모(관람객 2만 명대)에서는 100~105분으로 크게 길었습니다.</p>
<h3>4-4. 한계</h3>
<ul><li>대기열 자체는 어느 파일에도 기록되어 있지 않아 정산 통과 시각 분포로 간접 추정합니다(상한).</li>
<li>공연 시작 시각은 사용자가 입력해야 하며(API에 2025-12 공연 없음), 종료 후 25분 간격은 2회 표본입니다.</li>
<li>대규모 표본은 2회(12-05, 12-06)이고, 게이트 파일은 10만 건 상한으로 12월 첫 주만 출차를 관측합니다.</li>
<li>산책 코스는 잔디시설 개방기간만 공공데이터 근거이며 체류 시간은 가정값입니다(좌표·거리 데이터 없음).</li></ul>

<div class="keep"><h2>5. 기대효과</h2>
<p><b>이용자</b>: 차 안 공회전 대신 산책, 대기 예측으로 일정 계획. <b>기관</b>: 출차 피크 완화, 공원 체류·재방문, 민원 감소. 정량 효과는 아래 <u>가정 시나리오</u>로만 제시합니다(실제 도입 효과 아님).</p>
<table><tr><th>시나리오(가정)</th><th>중소 규모 평균(범위), 2024-07 5회</th><th>대규모 평균(범위), 2025-12 2회</th></tr>
{wrows5}</table>
<p class="meta">산식: 실측 서지 곡선에서 초과 출차의 f 비율을 코어 종료 20~55분 뒤로 균등 이동하여 5분 최대 출차 대수 변화를 계산. 효과의 크기는 산책으로 출발을 미루는 비율에 달려 있으며, 이 비율은 측정하지 않은 가정입니다.</p></div>

<h2>6. 데이터 품질 개선 제안</h2>
<p>분석 중 확인한 결측·불일치입니다. 개선되면 출차 대기 예측과 구역별 안내가 가능해집니다.</p>
<table class="long"><tr><th>ID</th><th>데이터</th><th>발견 사항</th><th>제안</th></tr>{qrows}</table>

<h2>7. 향후 계획</h2>
<ul><li>월별 파일이 추가로 개방되면(10만 건 상한 해제) 2025년 전체 게이트 데이터로 대규모 서지 표본을 늘리고 검증을 강화(공연 규모·날씨 효과 포함).</li>
<li>공연정보 API가 최신 공연(공연일, 시작·종료 시각)까지 갱신되면 사용자 입력 없이 오늘 공연의 몰림 시작 시각을 자동으로 안내하고, 주차장 수용 대수가 개방되면 실시간 주차 대수를 혼잡도 판정으로 확장.</li>
<li>장미광장·수목정보로 계절별 볼거리 코스 고도화, 유실물 많은 장소 안내(선택).</li></ul>

</body></html>"""
open(os.path.join(ROOT, "submission", "report.html"), "w").write(doc)
print(len(doc))
