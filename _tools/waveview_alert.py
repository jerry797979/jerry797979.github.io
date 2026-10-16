"""웨이브뷰 24시간 텔레그램 알림.

GitHub Actions(.github/workflows/waveview-alert.yml)가 5분마다 실행한다.
Twelve Data에서 봉을 받아 더블 볼린저밴드(20, 2σ) 돌파를 확인하고,
캔들 몸통 전체가 밴드 밖에서 마감한 첫 봉이면 텔레그램으로 보낸다.
웹 차트(dist/waveview)의 DB 신호와 같은 규칙이다.

필요한 저장소 Secrets
  TWELVEDATA_API_KEY   twelvedata.com API 키
  TELEGRAM_BOT_TOKEN   @BotFather 봇 토큰
  TELEGRAM_CHAT_ID     받을 채팅 ID

감시 대상은 환경변수 WAVEVIEW_WATCH 로 정한다. 예) "XAU/USD:5min,XAU/USD:4h"
"""
import json
import math
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta

STATE_FILE = os.environ.get("WAVEVIEW_STATE", ".waveview-state.json")
BB_LEN = int(os.environ.get("WAVEVIEW_BB_LEN", "20"))
BB_MULT = float(os.environ.get("WAVEVIEW_BB_MULT", "2"))
KST = timezone(timedelta(hours=9))

INTERVAL_SEC = {"1min": 60, "5min": 300, "15min": 900, "30min": 1800,
                "1h": 3600, "2h": 7200, "4h": 14400, "1day": 86400}
INTERVAL_KO = {"1min": "1분", "5min": "5분", "15min": "15분", "30min": "30분",
               "1h": "1시간", "2h": "2시간", "4h": "4시간", "1day": "일봉"}


def http_json(url, data=None):
    body = urllib.parse.urlencode(data).encode() if data else None
    with urllib.request.urlopen(urllib.request.Request(url, data=body), timeout=20) as r:
        return json.loads(r.read().decode())


def fetch_bars(symbol, interval, key):
    q = urllib.parse.urlencode({"symbol": symbol, "interval": interval, "outputsize": 60,
                                "timezone": "UTC", "apikey": key})
    j = http_json("https://api.twelvedata.com/time_series?" + q)
    if j.get("status") == "error" or "values" not in j:
        raise RuntimeError(j.get("message", "no data"))
    bars = []
    for v in reversed(j["values"]):
        dt = v["datetime"]
        fmt = "%Y-%m-%d" if len(dt) == 10 else "%Y-%m-%d %H:%M:%S"
        t = int(datetime.strptime(dt, fmt).replace(tzinfo=timezone.utc).timestamp())
        bars.append({"t": t, "o": float(v["open"]), "h": float(v["high"]),
                     "l": float(v["low"]), "c": float(v["close"])})
    return bars


def bands(closes, i):
    """i번째 봉의 (하단, 상단). 데이터가 모자라면 None."""
    if i < BB_LEN - 1:
        return None
    w = closes[i - BB_LEN + 1:i + 1]
    m = sum(w) / BB_LEN
    sd = math.sqrt(sum((x - m) ** 2 for x in w) / BB_LEN)
    return m - BB_MULT * sd, m + BB_MULT * sd


def signal_at(bars, i):
    """i번째 봉의 신호: 'dn' / 'up' / None. 연속 돌파는 첫 봉만."""
    closes = [b["c"] for b in bars]

    def side(k):
        bb = bands(closes, k)
        if not bb:
            return None
        b = bars[k]
        if max(b["o"], b["c"]) < bb[0]:
            return "dn"
        if min(b["o"], b["c"]) > bb[1]:
            return "up"
        return None

    s = side(i)
    if s and i > 0 and side(i - 1) == s:
        return None
    return s


def fmt_price(x):
    return f"{x:,.2f}"


def send_telegram(token, chat, text):
    j = http_json(f"https://api.telegram.org/bot{token}/sendMessage", {"chat_id": chat, "text": text})
    if not j.get("ok"):
        raise RuntimeError(j.get("description", "telegram error"))


def main():
    key = os.environ.get("TWELVEDATA_API_KEY", "")
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat = os.environ.get("TELEGRAM_CHAT_ID", "")
    missing = [n for n, v in [("TWELVEDATA_API_KEY", key), ("TELEGRAM_BOT_TOKEN", token),
                              ("TELEGRAM_CHAT_ID", chat)] if not v]
    if missing:
        print("저장소 Secrets 가 비어 있어 건너뜁니다:", ", ".join(missing))
        return 0

    if os.environ.get("WAVEVIEW_TEST") == "true":
        send_telegram(token, chat, "웨이브뷰 서버 알림 테스트입니다. 이 메시지가 보이면 설정이 끝났습니다.")
        print("테스트 메시지 전송")
        return 0

    try:
        with open(STATE_FILE) as f:
            state = json.load(f)
    except (OSError, ValueError):
        state = {}

    now = int(time.time())
    watch = [w.strip() for w in os.environ.get("WAVEVIEW_WATCH", "XAU/USD:5min").split(",") if w.strip()]
    failed = False
    for item in watch:
        symbol, interval = item.rsplit(":", 1)
        iv = INTERVAL_SEC[interval]
        sk = f"{symbol}|{interval}"
        last_done = state.get(sk, 0)
        # 새로 마감됐을 봉이 아직 없으면 API를 아끼려고 건너뛴다.
        expected = (now // iv) * iv - iv
        if interval != "1day" and last_done >= expected:
            print(f"{sk}: 새 마감 봉 없음, 건너뜀")
            continue
        try:
            bars = fetch_bars(symbol, interval, key)
        except Exception as e:  # noqa: BLE001
            print(f"{sk}: 시세 조회 실패 - {e}")
            failed = True
            continue

        closed = [i for i, b in enumerate(bars) if b["t"] + iv <= now]
        if not closed:
            continue
        if not last_done:
            todo = closed[-1:]  # 첫 실행: 지난 신호를 한꺼번에 보내지 않는다
        else:
            todo = [i for i in closed if bars[i]["t"] > last_done]

        for i in todo:
            s = signal_at(bars, i)
            if not s:
                continue
            b = bars[i]
            lo, up = bands([x["c"] for x in bars], i)
            end = datetime.fromtimestamp(b["t"] + iv, KST).strftime("%m-%d %H:%M")
            name = symbol.replace("/", "")
            way = "하방" if s == "dn" else "상방"
            band = f"하단밴드 {fmt_price(lo)}" if s == "dn" else f"상단밴드 {fmt_price(up)}"
            text = (f"{name} {INTERVAL_KO.get(interval, interval)} 돌파 더블비 {way} 몸통 마감\n"
                    f"종가 {fmt_price(b['c'])} · {band}\n{end} KST 마감")
            try:
                send_telegram(token, chat, text)
                print("전송:", text.replace("\n", " / "))
            except Exception as e:  # noqa: BLE001
                print(f"{sk}: 텔레그램 전송 실패 - {e}")
                failed = True
        state[sk] = bars[closed[-1]]["t"]
        print(f"{sk}: {len(todo)}개 봉 확인, 마지막 {datetime.fromtimestamp(state[sk], KST):%m-%d %H:%M} KST")

    with open(STATE_FILE, "w") as f:
        json.dump(state, f)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
