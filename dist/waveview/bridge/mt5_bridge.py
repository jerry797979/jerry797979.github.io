"""웨이브뷰 ↔ MT5(한텍) 브리지.

PC에 켜 둔 MT5 터미널에서 시세를 읽어 웨이브뷰 차트에 그대로 넘겨준다.
같은 가격으로 돌파 더블비 신호를 확인해 텔레그램 알림도 보낸다.

설치 (Windows, MT5 가 설치된 PC)
  1. python.org 에서 Python 3 설치 (설치 화면에서 "Add python.exe to PATH" 체크)
  2. 명령 프롬프트에서:  pip install MetaTrader5
  3. MT5 를 켜고 로그인한 상태에서:  python mt5_bridge.py
  4. 웨이브뷰 설정에서 "한텍 MT5 연결"을 켠다.

텔레그램 알림은 같은 폴더의 mt5_bridge.json 에 적는다 (처음 실행하면 예시 파일이 생긴다).
웨이브뷰 모의 거래의 '웨이브뷰 계좌'(자동 전략)도 여기서 24시간 돌린다 (paper_bot.json 에 기록).
한 시간마다 웹사이트의 최신 버전을 확인해 바뀌었으면 스스로 바꾸고 다시 시작한다.
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
PAPER_FILE = os.path.join(HERE, "paper_bot.json")
SITE = "https://jerry797979.github.io/waveview"
VERSION = 7
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
            if u.path == "/paper":
                return self._send(200, paper_config(body))
            if u.path == "/paper/close":
                return self._send(200, paper_close_id(int(body.get("id", 0)), "수동 청산"))
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
            if u.path == "/mt5/trades":
                return self._send(200, mt5_trades(int(q.get("since", 0))))
            if u.path == "/paper":
                with plock:
                    st = dict(paper)
                    st["hist"] = [h for h in paper.get("hist", []) if h.get("ctime", 0) > int(q.get("since", 0))][:1000]
                    st["ai"] = {"note": ai["note"], "at": ai["at"], "pick": ai["pick"]["name"] if ai["pick"] else None,
                                "board": [{"name": x["name"], "ok": x["ok"], **{k: round(v, 2) for k, v in x["full"].items()}} for x in ai["board"]]}
                return self._send(200, {"ok": True, **st})
            return self._send(200, {"ok": True, "service": "waveview-mt5-bridge", "version": VERSION, "paper": True,
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


# ---------- 사장님 MT5 실제 거래 (읽기만 한다. 주문은 내지 않는다) ----------
def mt5_trades(since_ms):
    """since_ms 이후 청산된 거래와 지금 보유 중인 포지션. 시간은 UTC 밀리초."""
    frm = datetime.fromtimestamp(max(since_ms / 1000, time.time() - 120 * 86400) + server_offset - 86400, timezone.utc)
    to = datetime.fromtimestamp(time.time() + server_offset + 86400, timezone.utc)
    with lock:
        deals = mt5.history_deals_get(frm, to) or []
        pos = mt5.positions_get() or []
        acc = mt5.account_info()
    opens = {}
    for d in deals:
        if d.entry == 0:  # 진입
            opens[d.position_id] = d
    closed = []
    for d in deals:
        if d.entry not in (1, 2, 3) or d.symbol == "":  # 청산 거래만
            continue
        t = (d.time_msc - server_offset * 1000) if getattr(d, "time_msc", 0) else (d.time - server_offset) * 1000
        if t <= since_ms:
            continue
        o = opens.get(d.position_id)
        closed.append({"id": f"m{d.ticket}", "sym": d.symbol, "dir": -1 if d.type == 0 else 1, "lots": d.volume,
                       "open": o.price if o else None, "close": d.price,
                       "time": ((o.time_msc - server_offset * 1000) if o and getattr(o, "time_msc", 0) else t),
                       "ctime": t, "pnl": d.profit + d.commission + d.swap + (o.commission if o else 0),
                       "why": "MT5 청산", "strat": None, "mt5": True})
    openp = [{"id": f"m{p.ticket}", "sym": p.symbol, "dir": 1 if p.type == 0 else -1, "lots": p.volume, "open": p.price_open,
              "sl": p.sl or None, "tp": p.tp or None, "time": (p.time - server_offset) * 1000, "strat": None, "mt5": True,
              "profit": p.profit + p.swap} for p in pos]
    return {"ok": True, "closed": closed, "pos": openp,
            "account": {"balance": acc.balance, "equity": acc.equity, "currency": acc.currency} if acc else None}


# ---------- 웨이브뷰 계좌 (모의 거래 자동 전략) 24시간 ----------
# 웹(index.html)의 ptStep · ptSignals 와 같은 규칙. 사장님 계좌(직접 주문)는 웹에서만 다룬다.
plock = threading.RLock()
paper = {}
PAPER_DEF = {"bal": 1000.0, "pos": [], "hist": [], "seq": 500000, "lastSig": {}, "race": 0,
             "auto": {"grid": False, "trail": False},
             "cfg": {"sym": "", "lev": 500, "cs": 100, "ptv": 1, "tg": True,
                     "grid": {"tf": "5m", "dir": "rev", "lot1": 0.01, "adds": "30:0.02, 60:0.03", "tp": 5, "be": 1, "stop": 100},
                     "trail": {"tf": "5m", "dir": "trend", "lot": 0.01, "sl": 10, "act": 10, "mode": "half", "dist": 10}}}
news = {"at": 0, "ev": []}
ai = {"at": 0, "pick": None, "board": [], "note": "아직 판단 전"}


def paper_load():
    global paper
    try:
        with open(PAPER_FILE, encoding="utf-8") as f:
            paper = {**json.loads(json.dumps(PAPER_DEF)), **json.load(f)}
    except (OSError, ValueError):
        paper = json.loads(json.dumps(PAPER_DEF))


def paper_save():
    tmp = PAPER_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(paper, f, ensure_ascii=False)
    os.replace(tmp, PAPER_FILE)


def paper_config(body):
    """웹이 보내는 설정. race(대결 시작 시각)가 바뀌면 $1,000 으로 새로 시작, 처음이면 웹의 계좌를 넘겨받는다."""
    with plock:
        if "cfg" in body:
            paper["cfg"] = {**paper["cfg"], **body["cfg"]}
        if "auto" in body:
            paper["auto"] = body["auto"]
        race = body.get("race")
        if race and race != paper.get("race"):
            adopt = body.get("adopt") if not paper.get("race") else None
            paper["race"] = race
            paper["bal"] = float(adopt["bal"]) if adopt else 1000.0
            paper["pos"] = list(adopt.get("pos", [])) if adopt else []
            paper["lastSig"] = {}
        paper_save()
        return {"ok": True, "race": paper["race"]}


def p_quote():
    sym = paper["cfg"].get("sym") or next((s["name"] for s in symbols() if s["name"].upper().startswith("XAU")), "")
    if not sym:
        return None
    with lock:
        t = mt5.symbol_info_tick(sym)
    return {"sym": sym, "bid": t.bid, "ask": t.ask} if t and t.bid else None


def p_pnl(p, q):
    cur = q["bid"] if p["dir"] > 0 else q["ask"]
    return (cur - p["open"]) * p["dir"] * p["lots"] * paper["cfg"]["cs"]


def p_log(title, msg):
    print("[모의·웨이브뷰]", title, msg)
    if paper["cfg"].get("tg", True):
        try:
            send_telegram(f"[모의 · 웨이브뷰 계좌] {title}\n{msg}")
        except Exception as e:  # noqa: BLE001
            print("텔레그램 실패:", e)


def p_open(q, d, lots, strat, group, sl=None):
    c = paper["cfg"]
    price = q["ask"] if d > 0 else q["bid"]
    need = lots * c["cs"] * price / c["lev"]
    eq = paper["bal"] + sum(p_pnl(p, q) for p in paper["pos"])
    margin = sum(p["lots"] * c["cs"] * p["open"] / c["lev"] for p in paper["pos"])
    if eq - margin < need:
        p_log("증거금 부족", f"{lots}랏 주문을 하지 않았습니다.")
        return None
    paper["seq"] += 1
    p = {"id": paper["seq"], "sym": q["sym"], "dir": d, "lots": lots, "open": price, "time": int(time.time() * 1000),
         "sl": sl, "tp": None, "strat": strat, "group": group, "peak": 0}
    paper["pos"].append(p)
    p_log(f"{'BUY' if d > 0 else 'SELL'} {lots}랏 체결", f"{q['sym']} @ {price:,.2f} · {'물타기 회복' if strat == 'grid' else 'AI 판단' if strat == 'ai' else '끌고 가기'}"
          + (f" · S/L {sl:,.2f}" if sl else ""))
    return p


def p_close(p, q, why):
    price = q["bid"] if p["dir"] > 0 else q["ask"]
    pnl = (price - p["open"]) * p["dir"] * p["lots"] * paper["cfg"]["cs"]
    paper["bal"] += pnl
    paper["pos"] = [x for x in paper["pos"] if x is not p]
    paper["hist"].insert(0, {**p, "close": price, "ctime": int(time.time() * 1000), "pnl": pnl, "why": why})
    paper["hist"] = paper["hist"][:5000]
    return pnl


def paper_close_id(pid, why):
    with plock:
        q = p_quote()
        p = next((x for x in paper["pos"] if x["id"] == pid), None)
        if not q or not p:
            return {"ok": False}
        r = p_close(p, q, why)
        p_log(f"청산 #{pid}", f"{r:+.2f}$ · 잔액 ${paper['bal']:.2f}")
        paper_save()
        return {"ok": True, "pnl": r}


def parse_adds(t):
    out = []
    for part in str(t).split(","):
        try:
            d, l = (float(x) for x in part.split(":"))
            if d > 0 and l > 0:
                out.append((d, l))
        except ValueError:
            pass
    return out


def p_step(q):
    c, v = paper["cfg"], paper["cfg"].get("ptv", 1)
    for p in list(paper["pos"]):
        cur = q["bid"] if p["dir"] > 0 else q["ask"]
        if p.get("sl") is not None and (cur <= p["sl"] if p["dir"] > 0 else cur >= p["sl"]):
            r = p_close(p, q, "손절" if (p["sl"] - p["open"]) * p["dir"] < 0 else "트레일링 스탑")
            p_log(f"청산 · {p['lots']}랏", f"{r:+.2f}$ · 잔액 ${paper['bal']:.2f}")
            continue
        if p.get("strat") in ("trail", "ai"):
            t = c["trail"]
            fav = (cur - p["open"]) * p["dir"] / v
            p["peak"] = max(p.get("peak", 0), fav)
            act, mode = (p["act"], "half") if p.get("strat") == "ai" else (t["act"], t["mode"])
            if p["peak"] >= act:
                keep = p["peak"] / 2 if mode == "half" else p["peak"] - t["dist"]
                ns = round(p["open"] + p["dir"] * max(0, keep) * v, 2)
                if p.get("sl") is None or (ns > p["sl"] if p["dir"] > 0 else ns < p["sl"]):
                    p["sl"] = ns
    groups = []
    for p in paper["pos"]:
        if p.get("strat") == "grid" and p["group"] not in groups:
            groups.append(p["group"])
    for g in groups:
        ps = [p for p in paper["pos"] if p["group"] == g]
        first = min(ps, key=lambda p: p["time"])
        d, gc = first["dir"], c["grid"]
        against = ((first["open"] - q["bid"]) if d > 0 else (q["ask"] - first["open"])) / v
        done = len(ps) - 1
        for k, (dist, lot) in enumerate(parse_adds(gc["adds"])):
            if k >= done and against >= dist and not any(p["group"] == g and p.get("addIdx") == k for p in paper["pos"]):
                np = p_open(q, d, lot, "grid", g)
                if np:
                    np["addIdx"] = k
        ps = [p for p in paper["pos"] if p["group"] == g]
        total = sum(p_pnl(p, q) for p in ps)
        has_add = any(p.get("addIdx") is not None for p in ps)
        why = None
        if against >= gc["stop"]:
            why = f"물타기 전체 손절 ({gc['stop']}포인트)"
        elif total >= (gc["be"] if has_add else gc["tp"]):
            why = "물타기 탈출" if has_add else "물타기 익절"
        if why:
            s = sum(p_close(p, q, why) for p in ps)
            p_log(f"{why} · {len(ps)}건 청산", f"합계 {s:+.2f}$ · 잔액 ${paper['bal']:.2f}")
    margin = lambda: sum(p["lots"] * c["cs"] * p["open"] / c["lev"] for p in paper["pos"])
    while paper["pos"] and margin() > 0:
        eq = paper["bal"] + sum(p_pnl(p, q) for p in paper["pos"])
        if eq / margin() * 100 >= 50:
            break
        worst = min(paper["pos"], key=lambda p: p_pnl(p, q))
        r = p_close(worst, q, "스톱아웃")
        p_log("스톱아웃 (마진 레벨 50% 미만)", f"{worst['lots']}랏 강제 청산 {r:+.2f}$")


def news_block():
    """웹과 같은 경제지표 일정(calendar.json)으로 중요 지표 30분 전 ~ 60분 후에는 새로 진입하지 않는다."""
    now = time.time()
    if now - news["at"] > 3600:
        news["at"] = now
        try:
            with urllib.request.urlopen(SITE + "/calendar.json", timeout=15) as r:
                rows = json.loads(r.read().decode())
            news["ev"] = [datetime.fromisoformat(e["date"]).timestamp() for e in rows if e.get("impact") == "High"]
        except Exception as e:  # noqa: BLE001
            print("경제지표 일정 받기 실패:", e)
    return any(t - 1800 <= now <= t + 3600 for t in news["ev"])


def sig_to_dir(mode, up, dn, st):
    if mode == "rev":
        return 1 if dn else -1
    if mode == "trend":
        return 1 if up else -1
    if mode == "long":
        return 1 if (dn if st == "grid" else up) else 0
    return -1 if (up if st == "grid" else dn) else 0


# ---------- AI 판단: 후보 전략을 최근 차트로 매시간 겨뤄 보고 가장 잘 맞는 것으로 거래 ----------
def _sma(v, n):
    out, s = [None] * len(v), 0.0
    for i, x in enumerate(v):
        s += x
        if i >= n:
            s -= v[i - n]
        if i >= n - 1:
            out[i] = s / n
    return out


def _bands(v, n, k):
    m = _sma(v, n)
    up, lo = [None] * len(v), [None] * len(v)
    for i in range(n - 1, len(v)):
        w = v[i - n + 1:i + 1]
        sd = math.sqrt(sum((x - m[i]) ** 2 for x in w) / n)
        up[i], lo[i] = m[i] + k * sd, m[i] - k * sd
    return m, up, lo


def zones_from(bars, touch=3):
    """웹 차트의 '매물대 지지·저항 자동'과 같은 계산: 고점·저점이 여러 번 모인 가격대."""
    n, L = len(bars), 5
    if n < 50:
        return []
    rng = sorted(b["h"] - b["l"] for b in bars[-300:])
    tol = (rng[len(rng) // 2] * 0.8) or 1
    piv = []
    for i in range(L, n - L):
        h, l = bars[i]["h"], bars[i]["l"]
        if all(bars[i - k]["h"] <= h and bars[i + k]["h"] <= h for k in range(1, L + 1)):
            piv.append(h)
        if all(bars[i - k]["l"] >= l and bars[i + k]["l"] >= l for k in range(1, L + 1)):
            piv.append(l)
    piv.sort()
    cl = []
    for v in piv:
        if cl and v - cl[-1][0] <= tol:
            cl[-1][1] = v
            cl[-1][2] += 1
        else:
            cl.append([v, v, 1])
    zs = [(lo - tol * .25, hi + tol * .25, k) for lo, hi, k in cl if k >= touch]
    out = []
    for z in sorted(zs, key=lambda z: -z[2]):
        if not any(z[0] <= o[1] + tol * .5 and z[1] >= o[0] - tol * .5 for o in out):
            out.append(z)
    return out


def ai_features(bars):
    """봉마다 신호: 돌파 더블비(db), 골든·데드크로스 후 1B 터치(gcb), 지난 미장 고저 돌파(usl), 그리고 ATR."""
    n = len(bars)
    c = [b["c"] for b in bars]
    o = [b["o"] for b in bars]
    m1, u1, l1 = _bands(c, int(cfg["bb_len"]), float(cfg["bb_mult"]))
    _, u2, l2 = _bands(o, int(cfg.get("bb2_len", 4)), float(cfg.get("bb2_mult", 4.0)))
    a20, a120 = _sma(c, 20), _sma(c, 120)
    tr = [bars[0]["h"] - bars[0]["l"]] + [max(bars[i]["h"], c[i - 1]) - min(bars[i]["l"], c[i - 1]) for i in range(1, n)]
    atr = _sma(tr, 14)
    f = [dict(db=0, gcb=0, usl=0, zone=0, zdb=0, zsl=None, atr=atr[i], trend=0) for i in range(n)]
    zs = []
    tr_state, armed = 0, False
    sh = sl_ = None
    prev_in = False
    fin = None
    for i in range(n):
        b = bars[i]
        if u1[i] is not None and u2[i] is not None:
            if b["h"] >= u1[i] and b["h"] >= u2[i]:
                f[i]["db"] = 1
            elif b["l"] <= l1[i] and b["l"] <= l2[i]:
                f[i]["db"] = -1
        if a20[i] is not None and a120[i] is not None:
            f[i]["trend"] = 1 if a20[i] > a120[i] else -1
            if i and a20[i - 1] is not None and a120[i - 1] is not None:
                if a20[i] > a120[i] and a20[i - 1] <= a120[i - 1]:
                    tr_state, armed = 1, True
                elif a20[i] < a120[i] and a20[i - 1] >= a120[i - 1]:
                    tr_state, armed = -1, True
        if tr_state and u1[i] is not None:
            w = u1[i] - l1[i]
            if tr_state > 0:
                if armed and b["l"] <= l1[i] + w * 0.1:
                    f[i]["gcb"], armed = 1, False
                elif not armed and c[i] > m1[i]:
                    armed = True
            else:
                if armed and b["h"] >= u1[i] - w * 0.1:
                    f[i]["gcb"], armed = -1, False
                elif not armed and c[i] < m1[i]:
                    armed = True
        # 매물대: 그 봉 이전 봉들로만 계산한다 (앞날을 미리 보지 않게). 48봉마다 다시 계산
        if i >= 200 and (i % 48 == 0 or not zs):
            zs = zones_from(bars[max(0, i - 1500):i])
        if zs and i:
            # 위에서 내려와(앞 봉 종가가 매물대 아래로 안 빠짐) 매물대를 찍고 다시 위에서 마감한 봉 = 지지 / 반대 = 저항
            sup = any(b["l"] <= hi and c[i] >= lo and c[i - 1] >= lo for lo, hi, _k in zs)
            res = any(b["h"] >= lo and c[i] <= hi and c[i - 1] <= hi for lo, hi, _k in zs)
            pb = bars[i - 1]
            fresh_sup = any(pb["l"] > hi and b["l"] <= hi and c[i] > hi for lo, hi, _k in zs)  # 위에 떠 있다가 처음 찍고 다시 위로
            fresh_res = any(pb["h"] < lo and b["h"] >= lo and c[i] < lo for lo, hi, _k in zs)
            if fresh_sup and c[i] > b["o"]:
                f[i]["zone"] = 1    # 지지 매물대 찍고 양봉
            elif fresh_res and c[i] < b["o"]:
                f[i]["zone"] = -1   # 저항 매물대 찍고 음봉
            # 매물대에서 DB 반전: 최근 36봉 고점에서 ATR×3 이상 빠진 뒤(매도는 오른 뒤)일 때만, 손절은 매물대 바깥 끝 + ATR×0.3
            a = atr[i]
            if a and i >= 36:
                hh = max(x["h"] for x in bars[i - 36:i + 1])
                ll = min(x["l"] for x in bars[i - 36:i + 1])
                if f[i]["db"] == -1 and hh - b["l"] >= 3 * a:
                    z = next((z for z in zs if b["l"] <= z[1] and c[i] >= z[0]), None)
                    if z:
                        f[i]["zdb"], f[i]["zsl"] = 1, min(z[0], b["l"]) - 0.3 * a
                elif f[i]["db"] == 1 and b["h"] - ll >= 3 * a:
                    z = next((z for z in zs if b["h"] >= z[0] and c[i] <= z[1]), None)
                    if z:
                        f[i]["zdb"], f[i]["zsl"] = -1, max(z[1], b["h"]) + 0.3 * a
        # 미장(한국 22:00~06:00) 고저
        k = datetime.fromtimestamp(b["t"], KST)
        mm = k.hour * 60 + k.minute
        ins = mm >= 1320 or mm < 360
        if ins and (not prev_in or (i and b["t"] - bars[i - 1]["t"] > 8 * 3600)):
            if prev_in and sh is not None:
                fin = (sh, sl_)
            sh, sl_ = b["h"], b["l"]
        elif ins:
            sh, sl_ = max(sh, b["h"]), min(sl_, b["l"])
        elif prev_in and sh is not None:
            fin = (sh, sl_)
        prev_in = ins
        if fin and i and not ins:
            if c[i - 1] <= fin[0] < c[i]:
                f[i]["usl"] = 1
            elif c[i - 1] >= fin[1] > c[i]:
                f[i]["usl"] = -1
    return f


AI_SIGNALS = [
    ("db", -1, "돌파 더블비 역추세 (위로 뚫으면 매도·아래로 뚫으면 매수)"),
    ("db", 1, "돌파 더블비 추세 따라가기"),
    ("gcb", 1, "골든·데드크로스 후 1B 눌림·반등"),
    ("usl", 1, "지난 미장 고점·저점 돌파 따라가기"),
    ("usl", -1, "지난 미장 고점·저점 돌파 실패 노리기"),
    ("zdb", 1, "매물대에서 돌파 더블비 반전 (지지에서 ↓DB 매수 · 저항에서 ↑DB 매도)"),
    ("zone", 1, "매물대 찍고 반등 (지지 양봉 매수 · 저항 음봉 매도)"),
]
AI_EXITS = [(1.5, 1.0, "손절 ATR×1.5"), (2.5, 2.0, "손절 ATR×2.5")]


def ai_experts():
    out = []
    for sig, way, name in AI_SIGNALS:
        for slk, actk, en in AI_EXITS:
            for flt in (False, True):
                out.append({"sig": sig, "way": way, "slk": slk, "actk": actk, "flt": flt,
                            "name": f"{name} · {en}{' · 20·120이평 방향만' if flt else ''}"})
    return out


def ai_dir(e, f):
    s = f[e["sig"]] * e["way"]
    if not s:
        return 0
    if e["flt"] and f["trend"] != s:
        return 0
    return s


def ai_backtest(e, bars, f, start, spread=0.2):
    """한 번에 한 포지션. 진입은 신호 봉 종가, 청산은 손절(추적 손절 포함). 손익은 가격 차이(1랏 0.01 기준 ×1달러)."""
    trades, pos = [], None
    for i in range(start, len(bars)):
        b = bars[i]
        if pos:
            d = pos["d"]
            if (b["l"] <= pos["sl"]) if d > 0 else (b["h"] >= pos["sl"]):
                trades.append((pos["sl"] - pos["px"]) * d - spread)
                pos = None
            else:
                fav = (b["c"] - pos["px"]) * d  # 종가 기준으로 보수적으로
                pos["peak"] = max(pos["peak"], fav)
                if pos["peak"] >= pos["act"]:
                    ns = pos["px"] + d * pos["peak"] / 2
                    pos["sl"] = max(pos["sl"], ns) if d > 0 else min(pos["sl"], ns)
            continue
        if f[i]["atr"] is None:
            continue
        d = ai_dir(e, f[i])
        if d:
            a = f[i]["atr"]
            sl = f[i]["zsl"] if e["sig"] == "zdb" and f[i].get("zsl") else b["c"] - d * e["slk"] * a
            pos = {"d": d, "px": b["c"], "sl": sl, "act": e["actk"] * a, "peak": 0}
    return trades


def ai_score(tr):
    if not tr:
        return {"n": 0, "net": 0, "pf": 0, "win": 0, "mdd": 0}
    gw = sum(x for x in tr if x > 0)
    gl = -sum(x for x in tr if x <= 0)
    eq = peak = mdd = 0
    for x in tr:
        eq += x
        peak = max(peak, eq)
        mdd = max(mdd, peak - eq)
    return {"n": len(tr), "net": gw - gl, "pf": gw / gl if gl else (9.9 if gw else 0), "win": sum(1 for x in tr if x > 0) / len(tr) * 100, "mdd": mdd}


def ai_learn(sym, tf):
    """최근 약 10일 봉으로 후보 전략을 모두 시험. 전체 기간 손익비 1.15 이상, 최근 3일도 이익, 거래 8번 이상인 것 중 1등을 고른다."""
    bars = rates(sym, tf, 3000)[:-1]
    f = ai_features(bars)
    recent = max(130, len(bars) - 3 * 24 * 3600 // TF_SEC.get(tf, 300))
    board = []
    for e in ai_experts():
        full = ai_score(ai_backtest(e, bars, f, 130))
        rec = ai_score(ai_backtest(e, bars, f, recent))
        ok = full["n"] >= 8 and full["pf"] >= 1.15 and rec["net"] > 0 and full["mdd"] < max(1e-9, full["net"]) * 1.5
        board.append({**e, "full": full, "rec": rec, "ok": ok, "score": full["net"] - full["mdd"] * 0.5 + rec["net"] * 0.5})
    board.sort(key=lambda x: (x["ok"], x["score"]), reverse=True)
    pick = board[0] if board and board[0]["ok"] else None
    prev = ai["pick"]["name"] if ai["pick"] else None
    ai.update(at=time.time(), pick=pick, board=board[:5],
              note=(f"지금 쓰는 전략: {pick['name']} (최근 10일 {pick['full']['n']}번 · 승률 {pick['full']['win']:.0f}% · 손익비 {pick['full']['pf']:.2f})"
                    if pick else "요즘 장에 잘 맞는 전략이 없어 쉬는 중"))
    if (pick["name"] if pick else None) != prev:
        p_log("AI 판단 · 전략 바꿈", ai["note"])


def ai_signal(q, tf):
    if not ai["pick"] or any(p.get("strat") == "ai" for p in paper["pos"]):
        return
    bars = rates(q["sym"], tf, 400)[:-1]
    key = f"ai|{q['sym']}|{tf}"
    bt = bars[-1]["t"]
    if paper["lastSig"].get(key) == bt:
        return
    first = key not in paper["lastSig"]
    paper["lastSig"][key] = bt
    if first:
        return
    f = ai_features(bars)
    e = ai["pick"]
    d = ai_dir(e, f[-1])
    if not d or f[-1]["atr"] is None:
        return
    if news_block():
        p_log("진입 건너뜀", "중요 경제지표 발표 전후라 대기합니다.")
        return
    a = f[-1]["atr"]
    px = q["ask"] if d > 0 else q["bid"]
    sl = f[-1]["zsl"] if e["sig"] == "zdb" and f[-1].get("zsl") else px - d * e["slk"] * a
    if (px - sl) * d <= 0:  # 이미 손절가를 지나 있으면 들어가지 않는다
        return
    p = p_open(q, d, paper["cfg"].get("aiLot", 0.01), "ai", f"A{int(time.time() * 1000)}", round(sl, 2))
    if p:
        p["act"] = round(e["actk"] * a / paper["cfg"].get("ptv", 1), 2)
        p["why"] = e["name"]
        p_log("AI 판단 · 진입 이유", f"{e['name']}\n최근 10일 성적: {e['full']['n']}번 · 승률 {e['full']['win']:.0f}% · 손익비 {e['full']['pf']:.2f}\n"
              f"손절 {p['sl']:,.2f} (ATR {a:.2f}) · 수익 {e['actk']}ATR 넘으면 절반 지키며 따라감")


def p_signals(q):
    c = paper["cfg"]
    if paper["auto"].get("ai", True):
        tf = c.get("aiTf", "5m")
        if time.time() - ai["at"] > 3600:
            ai_learn(q["sym"], tf)
        ai_signal(q, tf)
        return
    for st in ("grid", "trail"):
        if not paper["auto"].get(st) or any(p.get("strat") == st for p in paper["pos"]):
            continue
        tf = c[st]["tf"]
        if tf not in TF:
            continue
        bars = rates(q["sym"], tf, 200)
        i = len(bars) - 2
        if i < 130:
            continue
        key = f"{st}|{q['sym']}|{tf}"
        bt = bars[i]["t"]
        if key not in paper["lastSig"]:
            paper["lastSig"][key] = bt
            continue
        if paper["lastSig"][key] == bt:
            continue
        paper["lastSig"][key] = bt
        s = db_signal(bars, i)
        if not s:
            continue
        d = sig_to_dir(c[st]["dir"], s == "up", s == "dn", st)
        if not d:
            continue
        if news_block():
            p_log("진입 건너뜀", "중요 경제지표 발표 전후라 대기합니다.")
            continue
        if st == "grid":
            p_open(q, d, c["grid"]["lot1"], "grid", f"G{int(time.time() * 1000)}")
        else:
            px = q["ask"] if d > 0 else q["bid"]
            p_open(q, d, c["trail"]["lot"], "trail", f"T{int(time.time() * 1000)}", round(px - d * c["trail"]["sl"] * c.get("ptv", 1), 2))


def paper_loop():
    last_sig = 0
    while True:
        try:
            with plock:
                if paper.get("race"):
                    q = p_quote()
                    if q:
                        p_step(q)
                        if time.time() - last_sig >= 10:
                            last_sig = time.time()
                            p_signals(q)
                        paper_save()
        except Exception as e:  # noqa: BLE001
            print("모의 거래 오류:", e)
        time.sleep(1)


def self_update():
    """한 시간마다 웹사이트의 최신 연결 프로그램과 비교해 바뀌었으면 바꾸고 다시 시작한다."""
    me = os.path.abspath(__file__)
    while True:
        time.sleep(3600)
        try:
            with urllib.request.urlopen(SITE + "/bridge/mt5_bridge.py?" + str(int(time.time())), timeout=30) as r:
                new = r.read()
            with open(me, "rb") as f:
                old = f.read()
            if new and new != old and b"waveview-mt5-bridge" in new:
                with open(me + ".new", "wb") as f:
                    f.write(new)
                os.replace(me + ".new", me)
                print("새 버전으로 바꾸고 다시 시작합니다")
                os.execv(sys.executable, [sys.executable, me, "--restart"])
        except Exception as e:  # noqa: BLE001
            print("업데이트 확인 실패:", e)


def keep_mt5():
    """MT5 가 꺼지거나 끊기면 30초마다 다시 연결한다 (MT5 가 꺼져 있으면 initialize 가 MT5 를 켠다)."""
    while True:
        time.sleep(30)
        try:
            with lock:
                ok = mt5.terminal_info() is not None and mt5.account_info() is not None
                if not ok:
                    mt5.shutdown()
                    ok = mt5.initialize()
            if ok and not server_offset:
                detect_offset()
        except Exception as e:  # noqa: BLE001
            print("MT5 다시 연결 실패:", e)


def already_running(port):
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=2) as r:
            return b"waveview-mt5-bridge" in r.read()
    except Exception:  # noqa: BLE001
        return False


def main():
    load_config()
    if "--restart" not in sys.argv and already_running(int(cfg["port"])):
        print("이미 켜져 있습니다")
        return
    paper_load()
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
    threading.Thread(target=paper_loop, daemon=True).start()
    threading.Thread(target=keep_mt5, daemon=True).start()
    threading.Thread(target=self_update, daemon=True).start()
    port = int(cfg["port"])
    print(f"웨이브뷰 연결 주소: http://127.0.0.1:{port}  (이 창을 닫으면 연결이 끊깁니다)")
    for _ in range(30):  # 다시 시작할 때 앞 프로그램이 포트를 놓을 때까지 기다린다
        try:
            srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
            break
        except OSError:
            time.sleep(2)
    srv.serve_forever()


if __name__ == "__main__":
    main()
