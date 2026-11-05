"""web/data/*.json -> web/data.js (file:// 에서도 동작하도록 window.OLPARK 로 인라인)"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
d = {}
for k in ("surge_model", "surge2025", "gap", "perf_api", "quality", "lots", "monthly"):
    d[k] = json.load(open(os.path.join(OUT, k + ".json")))
open(os.path.join(ROOT, "web", "data.js"), "w").write("window.OLPARK=" + json.dumps(d, ensure_ascii=False) + ";")
print("ok", os.path.getsize(os.path.join(ROOT, "web", "data.js")))
