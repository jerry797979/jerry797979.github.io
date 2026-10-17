"""웨이브뷰 경제지표 일정.

GitHub Actions(.github/workflows/waveview-calendar.yml)가 하루 몇 번 실행한다.
ForexFactory 주간 일정에서 미국(USD) 중요·보통 지표만 골라 dist/waveview/calendar.json 에 합쳐 둔다.
지난 일정도 지우지 않고 쌓아서(최근 400일) 차트의 과거 급변동 봉에 어떤 지표였는지 붙일 수 있게 한다.
"""
import json
import os
import sys
import time
import urllib.request
from datetime import datetime

OUT = os.environ.get("WAVEVIEW_CALENDAR", "dist/waveview/calendar.json")
FEEDS = ["https://nfs.faireconomy.media/ff_calendar_thisweek.json",
         "https://nfs.faireconomy.media/ff_calendar_nextweek.json"]
KEEP_DAYS = 400


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 waveview-calendar"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def main():
    try:
        with open(OUT) as f:
            old = json.load(f)
    except (OSError, ValueError):
        old = []
    events = {(e["date"], e["title"]): e for e in old}
    got = 0
    for url in FEEDS:
        try:
            rows = fetch(url)
        except Exception as e:  # noqa: BLE001  다음 주 일정은 주 후반에만 올라온다
            print(f"{url}: 받지 못함 - {e}")
            continue
        for r in rows:
            if r.get("country") != "USD" or r.get("impact") not in ("High", "Medium"):
                continue
            e = {k: r.get(k, "") for k in ("title", "date", "impact", "forecast", "previous", "actual")}
            events[(e["date"], e["title"])] = e
            got += 1
    if not got and not old:
        print("일정을 받지 못했습니다")
        return 1
    cut = time.time() - KEEP_DAYS * 86400
    keep = sorted((e for e in events.values() if datetime.fromisoformat(e["date"]).timestamp() >= cut),
                  key=lambda e: e["date"])
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(keep, f, ensure_ascii=False, separators=(",", ":"))
    print(f"{got}개 받음, 총 {len(keep)}개 저장")
    return 0


if __name__ == "__main__":
    sys.exit(main())
