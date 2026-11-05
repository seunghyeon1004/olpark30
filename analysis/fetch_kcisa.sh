#!/bin/bash
# 문화공공데이터광장 API_CPM_009(올림픽공원 2025 연계 데이터) 시험 호출 반복. 키는 .secrets.env 에서 읽음(출력 금지).
set -a; . /Users/m4pro-1/hackathons-2026/.secrets.env; set +a
OUT=/Users/m4pro-1/hackathons-2026/korea/kspo/olpark30/data/raw_api
for i in $(seq 1 12); do
  code=$(curl -sL -m 60 "https://api.kcisa.kr/openapi/API_CPM_009/request?serviceKey=${KCISA_KEY_API_CPM_009}&numOfRows=5&pageNo=1" -o $OUT/probe.txt -w "%{http_code}")
  echo "$(date +%T) try $i http=$code size=$(stat -f%z $OUT/probe.txt)"
  [ "$code" = "200" ] && [ -s $OUT/probe.txt ] && exit 0
  sleep 120
done
exit 1
