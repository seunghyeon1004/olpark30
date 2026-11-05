# 올팍 30분

공연이 끝난 뒤 올림픽공원 출차 대기 시간을 공공데이터로 추정하고, 그 시간을 공원 산책 코스로 바꿔 주는 모바일 우선 웹앱입니다.
한국체육산업개발(주) 공공데이터 활용 경진대회 출품작, 작성자 백승현(개인).

## 앱 열기
정적 파일만 있습니다. `web/` 폴더를 아무 정적 호스팅(GitHub Pages 포함, 하위 경로 가능)에 올리거나 `web/index.html`을 직접 여세요.
분석 결과는 `web/data.js`에 미리 계산되어 있고, 실시간 주차 대수만 기관 공개 엔드포인트(`web/config.js`)를 호출하며 실패하면 해당 카드를 숨깁니다.
키나 개인정보는 들어 있지 않습니다(`config.js`의 apiKey는 한국체육산업개발이 공개 페이지에 게시한 값입니다).

## 분석 재현 (Python 3.11, pandas)
원본은 저장소에 넣지 않았습니다. 아래에서 받아 `data/` 아래에 저장합니다(인코딩 CP949/UTF-8 BOM 혼재, 스크립트가 처리).
- `data/raw/`: 공공데이터포털 파일 15138735(입출차 2024-07, 파일명 `15138735.csv`), 15164156, 15131671, 15143220, 15149169
- `data/raw_kcisa/`: 문화공공데이터광장 파일데이터(문화홍보)의 `API_CPM_009.csv`(2025 연계 데이터), `API_CPM_008.csv`(2025 게이트별 입출차)
- `data/raw_api/perf_1.xml`~`perf_6.xml`: 공연정보 API(3037877, KSCperf) 응답(서비스키 필요, 선택)

```
python3.11 -I analysis/02_surge.py        # 2024-07 서지와 대기시간 모델
python3.11 -I analysis/03_quality_lots.py # 데이터 품질 점검
python3.11 -I analysis/05_whatif.py       # 분산 시나리오(가정)
python3.11 -I analysis/07_gate2025.py     # 게이트 파일 탐색
python3.11 -I analysis/08_surge2025.py    # 2025-12 대규모 서지
python3.11 -I analysis/09_validate.py     # 연계 CSV 검증, 게이트 교차검증
python3.11 -I analysis/10_gap.py          # 공연 종료와 몰림 시작 간격
python3.11 -I analysis/04_build_web.py    # web/data.js 생성
python3.11 -I analysis/06_report.py       # 제출용 설명서 HTML
```

## 한계
모든 대기시간은 통계 기반 추정치(상한)입니다. 대기열은 어느 데이터에도 직접 기록되어 있지 않고, 대규모 표본은 2회입니다. 자세한 방법과 데이터 품질 제안은 앱의 '근거' 탭과 `submission/`의 설명서를 보세요.

## 라이선스와 출처
코드는 MIT. 데이터는 한국체육산업개발(주) 개방 데이터(공공데이터포털, 문화공공데이터광장)이며 각 데이터의 이용허락범위를 따릅니다.
