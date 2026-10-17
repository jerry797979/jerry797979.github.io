"""웨이브뷰 ↔ MT5(한텍) 브리지.

PC에 켜 둔 MT5 터미널에서 시세를 읽어 웨이브뷰 차트에 그대로 넘겨준다.
같은 가격으로 돌파 더블비 신호를 확인해 텔레그램 알림도 보낸다.

설치 (Windows, MT5 가 설치된 PC)
  1. python.org 에서 Python 3 설치 (설치 화면에서 "Add python.exe to PATH" 체크)
  2. 명령 프롬프트에서:  pip install MetaTrader5
  3. MT5 를 켜고 로그인한 상태에서:  python mt5_bridge.py
  4. 웨이브뷰 설정에서 "한텍 MT5 연결"을 켠다.

텔레그램 알림은 같은 폴더의 mt5_bridge.json 에 적는다 (처음 실행하면 예시 파일이 생긴다).
"""
import json
import math
import os
import threading
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import sys

# 창 없이(pythonw) 실행되면 출력이 없으므로 로그 파일로 보낸다
if sys.stdout is None:
    _log = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "bridge.log"), "a", encoding="utf-8", buffering=1)
    sys.stdout = sys.stderr = _log

import MetaTrader5 as mt5

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(HERE, "mt5_bridge.json")
DEFAULT_CONFIG = {
    "port": 8765,
    "telegram_token": "",
    "telegram_chat_id": "",
    "watch": [],
    "rules": [],
    "bb_len": 20,
    "bb_mult": 2.0,
    "bb2_len": 4,
    "bb2_mult": 4.0,
    "utc_offset_hours": None,
}
KST = timezone(timedelta(hours=9))
TF = {
    "1m": mt5.TIMEFRAME_M1, "2m": mt5.TIMEFRAME_M2, "3m": mt5.TIMEFRAME_M3, "5m": mt5.TIMEFRAME_M5,
    "10m": mt5.TIMEFRAME_M10, "15m": mt5.TIMEFRAME_M15, "30m": mt5.TIMEFRAME_M30,
    "1h": mt5.TIMEFRAME_H1, "2h": mt5.TIMEFRAME_H2, "3h": mt5.TIMEFRAME_H3, "4h": mt5.TIMEFRAME_H4,
    "8h": mt5.TIMEFRAME_H8, "1D": mt5.TIMEFRAME_D1, "1W": mt5.TIMEFRAME_W1, "1M": mt5.TIMEFRAME_MN1,
}
TF_SEC = {"1m": 60, "2m": 120, "3m": 180, "5m": 300, "10m": 600, "15m": 900, "30m": 1800,
          "1h": 3600, "2h": 7200, "3h": 10800, "4h": 14400, "8h": 28800, "1D": 86400}
TF_KO = {"1m": "1분", "2m": "2분", "3m": "3분", "5m": "5분", "10m": "10분", "15m": "15분", "30m": "30분",
         "1h": "1시간", "2h": "2시간", "3h": "3시간", "4h": "4시간", "8h": "8시간", "1D": "일봉"}

lock = threading.Lock()  # MetaTrader5 패키지는 한 번에 한 호출만 안전하다
cfg = {}
server_offset = 0  # MT5 서버시간 - UTC (초)


def load_config():
    global cfg
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, ensure_ascii=False, indent=2)
        print(f"설정 예시 파일을 만들었습니다: {CONFIG_FILE}")
    with open(CONFIG_FILE, encoding="utf-8") as f:
        cfg = {**DEFAULT_CONFIG, **json.load(f)}


def detect_offset():
    """MT5 서버시간과 UTC 차이. 주말에도 움직이는 종목(BTC 등)의 최신 틱으로 잰다."""
    global server_offset
    if cfg.get("utc_offset_hours") is not None:
        server_offset = int(float(cfg["utc_offset_hours"]) * 3600)
        return
    with lock:
        syms = mt5.symbols_get() or []
        latest = 0
        for s in syms:
            if s.visible:
                t = mt5.symbol_info_tick(s.name)
                if t and t.time > latest:
                    latest = t.time
    if latest and abs(latest - time.time()) < 15 * 3600:
        server_offset = round((latest - time.time()) / 1800) * 1800


def rates(symbol, tf, count):
    with lock:
        mt5.symbol_select(symbol, True)
        r = mt5.copy_rates_from_pos(symbol, TF[tf], 0, count)
    if r is None:
        raise RuntimeError(f"{symbol} {tf} 봉을 읽지 못했습니다: {mt5.last_error()}")
    return [{"t": int(x["time"]) - server_offset, "o": float(x["open"]), "h": float(x["high"]),
             "l": float(x["low"]), "c": float(x["close"])} for x in r]


def symbols():
    with lock:
        out = []
        for s in mt5.symbols_get() or []:
            if s.visible:
                out.append({"name": s.name, "desc": s.description, "digits": s.digits})
    return out


def quotes():
    out = {}
    for s in symbols():
        with lock:
            t = mt5.symbol_info_tick(s["name"])
            d = mt5.copy_rates_from_pos(s["name"], mt5.TIMEFRAME_D1, 1, 1)
        if not t:
            continue
        prev = float(d[0]["close"]) if d is not None and len(d) else None
        out[s["name"]] = {"bid": t.bid, "ask": t.ask,
                          "chg": (t.bid - prev) if prev else None,
                          "pct": ((t.bid - prev) / prev * 100) if prev else None}
    return out


# ---------- 웹 차트용 HTTP ----------
class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Private-Network", "true")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Private-Network", "true")
        self.end_headers()

    def do_POST(self):
        u = urllib.parse.urlparse(self.path)
        try:
            n = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(n).decode("utf-8") or "{}")
            if u.path == "/config":
                for k in ("telegram_token", "telegram_chat_id", "rules"):
                    if k in body:
                        cfg[k] = body[k]
                with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                    json.dump(cfg, f, ensure_ascii=False, indent=2)
                ensure_watcher()
                return self._send(200, {"ok": True, "rules": len(cfg.get("rules", []))})
            return self._send(404, {"error": "없는 주소"})
        except Exception as e:  # noqa: BLE001
            return self._send(500, {"error": str(e)})

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        q = {k: v[0] for k, v in urllib.parse.parse_qs(u.query).items()}
        try:
            if u.path == "/symbols":
                return self._send(200, {"symbols": symbols(), "offset": server_offset})
            if u.path == "/bars":
                tf = q.get("tf", "15m")
                if tf not in TF:
                    return self._send(400, {"error": f"지원하지 않는 주기: {tf}"})
                return self._send(200, {"bars": rates(q["symbol"], tf, min(int(q.get("count", 1500)), 200000))})
            if u.path == "/quotes":
                return self._send(200, {"quotes": quotes()})
            return self._send(200, {"ok": True, "service": "waveview-mt5-bridge", "version": 2,
                                    "telegram": bool(cfg.get("telegram_token") and cfg.get("telegram_chat_id")),
                                    "rules": len(cfg.get("rules", []))})
        except Exception as e:  # noqa: BLE001
            return self._send(500, {"error": str(e)})


# ---------- 텔레그램 신호 감시 ----------
def send_telegram(text):
    if not cfg["telegram_token"] or not cfg["telegram_chat_id"]:
        return
    data = urllib.parse.urlencode({"chat_id": cfg["telegram_chat_id"], "text": text}).encode()
    url = f"https://api.telegram.org/bot{cfg['telegram_token']}/sendMessage"
    with urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=15) as r:
        j = json.loads(r.read().decode())
    if not j.get("ok"):
        raise RuntimeError(j.get("description"))


def bands(vals, i, n, k):
    if i < n - 1:
        return None
    w = vals[i - n + 1:i + 1]
    m = sum(w) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in w) / n)
    return m - k * sd, m + k * sd


def db_signal(bars, i):
    """더블 볼린저밴드 원본: BB1(종가 20, 2) · BB2(시가 4, 4) 를 고가/저가가 동시에 터치하면 DB."""
    c = [b["c"] for b in bars]
    o = [b["o"] for b in bars]
    b1 = bands(c, i, int(cfg["bb_len"]), float(cfg["bb_mult"]))
    b2 = bands(o, i, int(cfg.get("bb2_len", 4)), float(cfg.get("bb2_mult", 4.0)))
    if not b1 or not b2:
        return None
    b = bars[i]
    if b["h"] >= b1[1] and b["h"] >= b2[1]:
        return "up"
    if b["l"] <= b1[0] and b["l"] <= b2[0]:
        return "dn"
    return None


TF_NAME = {"1m": "1분", "2m": "2분", "3m": "3분", "5m": "5분", "10m": "10분", "15m": "15분", "30m": "30분",
           "1h": "1시간", "2h": "2시간", "3h": "3시간", "4h": "4시간", "8h": "8시간", "1D": "일봉"}
_watcher_started = False


def ensure_watcher():
    global _watcher_started
    if not _watcher_started:
        _watcher_started = True
        threading.Thread(target=watcher, daemon=True).start()


def current_rules():
    rules = list(cfg.get("rules") or [])
    for symbol, tf in cfg.get("watch") or []:  # 예전 설정 호환
        rules.append({"sym": symbol, "tf": tf, "dir": "both", "name": ""})
    return rules


def watcher():
    """돌파 더블비(BB1·BB2 동시 돌파)를 봉 마감 때 확인해 텔레그램으로 보낸다."""
    done = {}
    while True:
        if cfg.get("telegram_token") and cfg.get("telegram_chat_id"):
            for r in current_rules():
                symbol, tf, way = r.get("sym"), r.get("tf"), r.get("dir", "both")
                if tf not in TF:
                    continue
                key = f"{symbol}|{tf}|{way}"
                try:
                    bars = rates(symbol, tf, 60)[:-1]  # 마지막 봉은 아직 진행 중
                    if not bars:
                        continue
                    last_t = bars[-1]["t"]
                    if key not in done:
                        done[key] = last_t  # 처음에는 지난 신호를 보내지 않는다
                        continue
                    for i in range(len(bars)):
                        if bars[i]["t"] <= done[key]:
                            continue
                        s = db_signal(bars, i)
                        if s and (way == "both" or way == s):
                            b = bars[i]
                            title = r.get("name") or f"{TF_NAME.get(tf, tf)} 돌파 더블비 {'상방' if s == 'up' else '하방'}"
                            text = (f"{title}\n{'↑' if s == 'up' else '↓'} DB | {symbol} {TF_NAME.get(tf, tf)} | 종가 {b['c']:,.2f} | "
                                    f"BB1·BB2 {'상단' if s == 'up' else '하단'} 동시 돌파 (한텍 MT5)")
                            plan = r.get("plan")
                            if plan:
                                sig = plan.get("sig")
                                up = s == "up"
                                d = (-1 if up else 1) if sig == "rev" else (1 if up else -1) if sig == "trend" else (0 if up else 1) if sig == "long" else (-1 if up else 0)
                                if d:
                                    ref = b["c"]
                                    parts = [f"{'매수' if d > 0 else '매도'} 진입 ≈ {ref:,.2f} ({plan.get('lot1', 0.01)}랏)"]
                                    for k, lot in enumerate(plan.get("adds") or []):
                                        parts.append(f"추가 {ref - d * plan.get('gap', 0) * (k + 1):,.2f} ({lot}랏)")
                                    parts.append(f"익절 평균가 {'+' if d > 0 else '-'}{plan.get('tp')} / 손절 평균가 {'-' if d > 0 else '+'}{plan.get('sl')}")
                                    text += "\n[적용 설정] " + " / ".join(parts)
                            send_telegram(text)
                            print("알림:", text.replace("\n", " / "))
                    done[key] = last_t
                except Exception as e:  # noqa: BLE001
                    print(f"{key} 확인 실패: {e}")
        time.sleep(5)


def main():
    load_config()
    while not mt5.initialize():
        print("MT5 에 연결하지 못했습니다. MT5 를 켜고 로그인하면 자동으로 연결합니다. (10초 뒤 다시 시도)", mt5.last_error())
        time.sleep(10)
    acc = mt5.account_info()
    detect_offset()
    print(f"MT5 연결됨: {acc.server if acc else '?'} · 서버시간 UTC{server_offset / 3600:+g}")
    ensure_watcher()
    if cfg.get("telegram_token") and cfg.get("telegram_chat_id"):
        print("텔레그램 신호 감시 중:", ", ".join(f"{r['sym']} {r['tf']}" for r in current_rules()) or "(규칙 없음)")
    else:
        print("텔레그램 설정 전입니다. 웨이브뷰 ⚙ 설정에서 봇 토큰과 채팅 ID를 저장하면 자동으로 켜집니다.")
    port = int(cfg["port"])
    print(f"웨이브뷰 연결 주소: http://127.0.0.1:{port}  (이 창을 닫으면 연결이 끊깁니다)")
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
