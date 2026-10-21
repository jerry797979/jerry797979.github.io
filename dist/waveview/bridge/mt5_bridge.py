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
import random
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
VERSION = 16
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
                                "board": [{"name": x["name"], "ok": x["ok"], **{k: round(v, 2) for k, v in x["full"].items()}} for x in ai["board"]],
                                "top": (ai.get("lab") or {}).get("top", []), "gen": (ai.get("lab") or {}).get("gen", 0)}
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
ai = {"at": 0, "pick": None, "board": [], "note": "아직 판단 전", "bench": {}, "spread": 0.2, "dayStop": ""}


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


def p_log(title, msg, tg=True):
    print("[모의·웨이브뷰]", title, msg)
    if tg and paper["cfg"].get("tg", True):
        try:
            send_telegram(f"[모의 · 웨이브뷰 계좌] {title}\n{msg}")
        except Exception as e:  # noqa: BLE001
            print("텔레그램 실패:", e)


STRAT_KO = {"grid": "물타기 회복", "trail": "끌고 가기", "ai": "AI 판단"}


def k_now(ms=None):
    return datetime.fromtimestamp((ms or time.time() * 1000) / 1000, KST).strftime("%m/%d %H:%M")


def side_ko(d):
    return "🟢 매수 (BUY)" if d > 0 else "🔴 매도 (SELL)"


def usd(v):
    return f"{'+' if v >= 0 else '−'}${abs(v):,.2f}"


def p_open(q, d, lots, strat, group, sl=None, quiet=False):
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
    if not quiet:
        loss = (sl - price) * d * lots * c["cs"] if sl else None
        p_log(f"{side_ko(d)} 진입 · {lots}랏",
              f"종목: {q['sym']}\n진입가: {price:,.2f}\n"
              + (f"손절가: {sl:,.2f} (손절되면 {usd(loss)})\n" if sl else "")
              + f"전략: {STRAT_KO.get(strat, strat)}\n시각: {k_now()} (한국)")
    return p


def p_close(p, q, why, log=True):
    price = q["bid"] if p["dir"] > 0 else q["ask"]
    pnl = (price - p["open"]) * p["dir"] * p["lots"] * paper["cfg"]["cs"]
    if log and not p.get("silent"):
        mins = int((time.time() * 1000 - p["time"]) / 60000)
        p_log(f"{'✅' if pnl >= 0 else '❌'} 청산 · {usd(pnl)} ({why})",
              f"종목: {p['sym']} · {'매수' if p['dir'] > 0 else '매도'} {p['lots']}랏\n"
              f"진입가 {p['open']:,.2f} → 청산가 {price:,.2f} ({(price - p['open']) * p['dir']:+.2f})\n"
              f"보유 {mins // 60}시간 {mins % 60}분 · 전략: {STRAT_KO.get(p.get('strat'), '직접')}\n"
              f"잔액: ${paper['bal'] + pnl:,.2f} · 시각: {k_now()} (한국)")
    paper["bal"] += pnl
    paper["pos"] = [x for x in paper["pos"] if x is not p]
    paper["hist"].insert(0, {**p, "close": price, "ctime": int(time.time() * 1000), "pnl": pnl,
                             "why": why + (" · 지표 시간 진입" if p.get("news") else "")})
    paper["hist"] = paper["hist"][:5000]
    return pnl


def paper_close_id(pid, why):
    with plock:
        q = p_quote()
        p = next((x for x in paper["pos"] if x["id"] == pid), None)
        if not q or not p:
            return {"ok": False}
        r = p_close(p, q, why)
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
            p_close(p, q, "손절" if (p["sl"] - p["open"]) * p["dir"] < 0 else "트레일링 스탑 · 수익 지키기")
            continue
        if p.get("strat") == "ai" and p.get("tmax_s") and time.time() * 1000 - p["time"] >= p["tmax_s"] * 1000 and p.get("peak", 0) < p.get("act", 0):
            p_close(p, q, "시간 손절 · 정해진 시간 안에 수익 없음")
            continue
        if p.get("strat") in ("trail", "ai") and not p.get("basket") and not p.get("zone"):
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
            s = sum(p_close(p, q, why, log=False) for p in ps)
            p_log(f"{why} · {len(ps)}건 청산", f"합계 {s:+.2f}$ · 잔액 ${paper['bal']:.2f}")
    # AI 블로그 구간 매매
    for g in {p["group"] for p in paper["pos"] if p.get("zone")}:
        ps = [p for p in paper["pos"] if p["group"] == g]
        first = min(ps, key=lambda p: p["time"])
        z, d = first["zone"], first["dir"]
        cur = q["bid"] if d > 0 else q["ask"]
        against = (first["open"] - cur) * d / v
        n = len(ps) - 1
        while (n + 1) * z["step"] <= z["max"] and against >= (n + 1) * z["step"]:
            n += 1
            np = p_open(q, d, round(0.01 * (n + 1 if z.get("up") else 1), 2), "ai", g, quiet=True)
            if not np:
                break
            np.update(addIdx=n, zone=z, logic=first.get("logic"), rank=first.get("rank"), silent=first.get("silent"), news=first.get("news"))
            if not first.get("silent"):
                p_log(f"➕ 구간 {n}차 추가 · {np['lots']:.2f}랏 ({'매수' if d > 0 else '매도'})",
                      f"첫 진입가 {first['open']:,.2f}에서 {against:.0f}포인트 반대로 와서 {np['open']:,.2f}에 추가했습니다.\n"
                      f"일괄 청산: 첫 진입가 {first['open'] + d * z['be'] * v:,.2f}로 돌아오면 · 손절 {first['open'] - d * z['stop'] * v:,.2f}")
        ps = [p for p in paper["pos"] if p["group"] == g]
        has_add = len(ps) > 1
        why = None
        if z.get("flip") and not first.get("flipped"):
            try:
                cs = [b["c"] for b in rates(first["sym"], z.get("tf", "3m"), 130)[:-1]]
            except Exception:
                cs = []
            if len(cs) >= 120 and (sum(cs[-20:]) / 20 - sum(cs[-120:]) / 120) * d < 0:
                first["flipped"] = True
                if not first.get("silent"):
                    p_log("⚠ 이평 배열이 반대로 뒤집힘 · 본절 정리 대기", f"{'정배열→역배열' if d > 0 else '역배열→정배열'}. 평단에 오면 바로 정리합니다 (블로그: 들고 있으면 골로 간다).")
        avg = sum(p["open"] * p["lots"] for p in ps) / sum(p["lots"] for p in ps)
        if against >= z["stop"]:
            why = f"구간 매매 손절 ({z['stop']}포인트)"
        elif first.get("flipped") and (cur - avg) * d >= 0:
            why = "배열 뒤집힘 · 본절 정리"
        elif has_add and (cur - first["open"]) * d >= z["be"] * v:
            why = "첫 진입가 복귀 · 일괄 청산"
        elif not has_add and z.get("tp") is not None and (cur - z["tp"]) * d >= 0:
            why = "익절 (전고·전저)" if z.get("hl") else f"익절 (+{z.get('tpp')}P)"
        if why:
            tot = sum(p_close(p, q, why, log=False) for p in ps)
            if not first.get("silent"):
                p_log(f"{'✅' if tot >= 0 else '❌'} 구간 매매 청산 · {usd(tot)} ({why})",
                      f"{len(ps)}건 ({'매수' if d > 0 else '매도'}, 합계 {sum(p['lots'] for p in ps):.2f}랏) · 첫 진입가 {first['open']:,.2f}\n"
                      f"잔액: ${paper['bal']:,.2f} · 시각: {k_now()} (한국)")
    # AI 사장님식 분할 진입 바스켓
    for g in {p["group"] for p in paper["pos"] if p.get("basket")}:
        ps = [p for p in paper["pos"] if p["group"] == g]
        first = min(ps, key=lambda p: p["time"])
        bk, d = first["basket"], first["dir"]
        against = ((first["open"] - q["bid"]) if d > 0 else (q["ask"] - first["open"])) / v
        for k, dist, lot in ((1, bk["a1"], 0.01), (2, bk["a2"], bk["l2"])):
            if against >= dist and not any(p.get("addIdx") == k for p in ps):
                np = p_open(q, d, lot, "ai", g, quiet=True)
                if np:
                    np.update(addIdx=k, basket=bk, logic=first.get("logic"), rank=first.get("rank"), silent=first.get("silent"), news=first.get("news"))
                    if not first.get("silent"):
                        p_log(f"➕ {k}차 추가 진입 · {lot}랏 ({'매수' if d > 0 else '매도'})",
                              f"첫 진입가 {first['open']:,.2f}에서 {against:.0f}포인트 밀려 {np['open']:,.2f}에 추가했습니다.\n"
                              f"흐름 바뀜 손절: {first['open'] - d * bk['bstop'] * v:,.2f} ({bk['bstop']}포인트)")
                ps = [p for p in paper["pos"] if p["group"] == g]
        total = sum(p_pnl(p, q) for p in ps)
        has_add = any(p.get("addIdx") for p in ps)
        why = None
        if against >= bk["bstop"]:
            why = f"흐름 바뀜 손절 ({bk['bstop']}포인트 반대)"
        elif total >= (bk["bbe"] if has_add else bk["btp"]):
            why = "분할 진입 탈출 (본전 위)" if has_add else "목표 수익 달성"
        if why:
            tot = sum(p_close(p, q, why, log=False) for p in ps)
            if not first.get("silent"):
                p_log(f"{'✅' if tot >= 0 else '❌'} 바스켓 청산 · {usd(tot)} ({why})",
                      f"{len(ps)}건 ({'매수' if d > 0 else '매도'}, 합계 {sum(p['lots'] for p in ps):.2f}랏) · 첫 진입가 {first['open']:,.2f}\n"
                      f"잔액: ${paper['bal']:,.2f} · 시각: {k_now()} (한국)")
    margin = lambda: sum(p["lots"] * c["cs"] * p["open"] / c["lev"] for p in paper["pos"])
    while paper["pos"] and margin() > 0:
        eq = paper["bal"] + sum(p_pnl(p, q) for p in paper["pos"])
        if eq / margin() * 100 >= 50:
            break
        worst = min(paper["pos"], key=lambda p: p_pnl(p, q))
        p_close(worst, q, "스톱아웃 · 마진 레벨 50% 미만")


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
    f = [dict(db=0, gcb=0, usl=0, zone=0, zdb=0, zsl=None, atr=atr[i], trend=0, sess="", mvd=0, mvu=0, sup=False, res=False, reg="", pbk=0, psl=None, lmt=0, avoid=False, ph=None, pl=None, dr=None, cal=None, htr=0) for i in range(n)]
    # 하루 변동폭(한국 날짜 기준 고가-저가): 지난 20일 평균. 구간 매매 '영점 조절'에 쓴다
    days, dk, dh, dl = [], None, None, None
    for i in range(n):
        b = bars[i]
        k = (b["t"] + 9 * 3600) // 86400
        if k != dk:
            if dk is not None:
                days.append(dh - dl)
            dk, dh, dl = k, b["h"], b["l"]
        else:
            dh, dl = max(dh, b["h"]), min(dl, b["l"])
        if len(days) >= 5:
            f[i]["dr"] = sum(days[-20:]) / len(days[-20:])
    # 1시간봉으로 묶기 (지난 시간까지만 써서 앞날을 보지 않는다): 기본 BB1·120이평·최근 24시간 전고·전저
    v_ = paper["cfg"].get("ptv", 1) if paper else 1
    H, acc, hk = [], None, None
    for i in range(n):
        b = bars[i]
        k = b["t"] // 3600
        if k != hk:
            if acc:
                H.append(acc)
            acc, hk = [b["h"], b["l"], b["c"]], k
        else:
            acc = [max(acc[0], b["h"]), min(acc[1], b["l"]), b["c"]]
        lv = []
        if len(H) >= 24:
            f[i]["ph"], f[i]["pl"] = max(x[0] for x in H[-24:]), min(x[1] for x in H[-24:])
            lv += [f[i]["ph"], f[i]["pl"]]
        if len(H) >= 20:
            cs_ = [x[2] for x in H[-20:]]
            mm = sum(cs_) / 20
            sd = math.sqrt(sum((x - mm) ** 2 for x in cs_) / 20)
            lv += [mm, mm + 2 * sd, mm - 2 * sd]
        if len(H) >= 120:
            h120 = sum(x[2] for x in H[-120:]) / 120
            lv.append(h120)
            # 1시간봉 우위: 20이평 vs 120이평 (지난 시간까지)
            f[i]["htr"] = 1 if sum(x[2] for x in H[-20:]) / 20 > h120 else -1
        kt_ = datetime.fromtimestamp(b["t"], KST)
        # 블로그 매매법의 피할 때: 새벽 2~7시, 1시간봉 기본 BB·장기이평·전고저 5포인트 안
        f[i]["avoid"] = 2 <= kt_.hour < 7 or any(abs(c[i] - x) <= 5 * v_ for x in lv)
    pb_dir, pb_left = 0, 0  # 돌파 더블비 뒤 되돌림 기다리는 중 (방향, 남은 봉 수)
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
        # 돌파 더블비 뒤 되돌림: ↓DB 뒤 위쪽 BB1 근처(밴드 폭 15% 안)까지 반등하면 매도, ↑DB 뒤 아래쪽 BB1 근처까지 밀리면 매수
        if pb_dir and u1[i] is not None and f[i]["db"] == 0:
            w = u1[i] - l1[i]
            if pb_dir > 0 and b["l"] <= l1[i] + w * 0.15:
                f[i]["pbk"], f[i]["psl"], pb_dir = 1, l1[i] - (atr[i] or 0) * 0.5, 0
            elif pb_dir < 0 and b["h"] >= u1[i] - w * 0.15:
                f[i]["pbk"], f[i]["psl"], pb_dir = -1, u1[i] + (atr[i] or 0) * 0.5, 0
        if f[i]["db"]:
            pb_dir, pb_left = f[i]["db"], 36
        elif pb_left:
            pb_left -= 1
            if not pb_left:
                pb_dir = 0
        # 장기이평(120) 터치: 정배열에서 위에서 내려와 닿으면 매수, 역배열에서 아래에서 올라와 닿으면 매도
        if i and a20[i] is not None and a120[i] is not None and a120[i - 1] is not None:
            if a20[i] > a120[i] and b["l"] <= a120[i] and bars[i - 1]["l"] > a120[i - 1]:
                f[i]["lmt"] = 1
            elif a20[i] < a120[i] and b["h"] >= a120[i] and bars[i - 1]["h"] < a120[i - 1]:
                f[i]["lmt"] = -1
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
        # 시간대 (한국 시각, 서머타임 반영 — 웹 차트 세션박스와 같은 기준)
        kt = datetime.fromtimestamp(b["t"], KST)
        wd = kt.isoweekday() % 7 + 1  # Pine dayofweek: 일=1 … 토=7
        us_dst = 3 < kt.month < 11 or (kt.month == 3 and kt.day - wd >= 8) or (kt.month == 11 and kt.day - wd < 1)
        eu_dst = 3 < kt.month < 10
        a_s, e_s, u_s = (7 if us_dst else 8), (16 if eu_dst else 17), (22 if us_dst else 23)
        f[i]["sess"] = "asia" if a_s <= kt.hour < e_s else "eu" if e_s <= kt.hour < u_s else "us"
        # 장세: 최근 36봉 동안 순수하게 간 거리 ÷ 오르내린 거리 (1에 가까우면 한 방향 추세, 0에 가까우면 박스)
        if i >= 36:
            path = sum(abs(c[j] - c[j - 1]) for j in range(i - 35, i + 1)) or 1e-9
            er = abs(c[i] - c[i - 36]) / path
            f[i]["reg"] = "trend" if er >= 0.35 else "range" if er <= 0.2 else ""
        # 최근 36봉 고점에서 얼마나 빠졌나 / 저점에서 얼마나 올랐나 (ATR 몇 배)
        if atr[i] and i >= 36:
            f[i]["mvd"] = (max(x["h"] for x in bars[i - 36:i + 1]) - b["l"]) / atr[i]
            f[i]["mvu"] = (b["h"] - min(x["l"] for x in bars[i - 36:i + 1])) / atr[i]
        if zs and i:
            # 위에서 내려와(앞 봉 종가가 매물대 아래로 안 빠짐) 매물대를 찍고 다시 위에서 마감한 봉 = 지지 / 반대 = 저항
            sup = any(b["l"] <= hi and c[i] >= lo and c[i - 1] >= lo for lo, hi, _k in zs)
            res = any(b["h"] >= lo and c[i] <= hi and c[i - 1] <= hi for lo, hi, _k in zs)
            f[i]["sup"], f[i]["res"] = sup, res
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
    # 영점 조절용 복기: 장기이평 터치마다 (끝난 시점, 시각, 첫 반등 폭, 최대로 물린 폭 · 못 돌아왔으면 None)
    rv = []
    for j in range(n):
        d = f[j]["lmt"]
        if not d:
            continue
        c0, mae, fav, back, k = bars[j]["c"], 0.0, 0.0, False, j + 1
        while k < n and k <= j + 400:
            x = bars[k]
            if k <= j + 20:
                fav = max(fav, ((x["h"] - c0) if d > 0 else (c0 - x["l"])) / v_)
            mae = max(mae, ((c0 - x["l"]) if d > 0 else (x["h"] - c0)) / v_)
            if mae > 0 and ((x["h"] >= c0) if d > 0 else (x["l"] <= c0)) and k > j + 1:
                back = True
                break
            k += 1
        if back or k > j + 400:
            rv.append((max(k, j + 20), bars[j]["t"], fav, mae if back else None))
    rv.sort()
    ptr, pool = 0, []
    for i in range(n):
        while ptr < len(rv) and rv[ptr][0] < i:
            pool.append(rv[ptr])
            ptr += 1
        t0 = bars[i]["t"] - 7 * 86400
        pool = [x for x in pool if x[1] >= t0] if pool and pool[0][1] < t0 else pool
        if len(pool) >= 6:
            favs = sorted(x[2] for x in pool)
            st = min(20, max(5, round(favs[len(favs) // 2] / 5) * 5))  # 보통 반등 폭 (5P 단위, 5~20)
            mx = 80
            for w in range(30, 81, 10):  # 이 구간이었으면 85%는 살아나왔다
                if sum(1 for x in pool if x[3] is None or x[3] > w) <= 0.15 * len(pool):
                    mx = w
                    break
            f[i]["cal"] = (st, max(st, mx // st * st))
    return f


AI_SIGNALS = [
    ("db", -1, "돌파 더블비 역추세 (위로 뚫으면 매도·아래로 뚫으면 매수)"),
    ("db", 1, "돌파 더블비 추세 따라가기"),
    ("gcb", 1, "골든·데드크로스 후 1B 눌림·반등"),
    ("usl", 1, "지난 미장 고점·저점 돌파 따라가기"),
    ("usl", -1, "지난 미장 고점·저점 돌파 실패 노리기"),
    ("zdb", 1, "매물대에서 돌파 더블비 반전 (지지에서 ↓DB 매수 · 저항에서 ↑DB 매도)"),
    ("zone", 1, "매물대 찍고 반등 (지지 양봉 매수 · 저항 음봉 매도)"),
    ("pbk", 1, "돌파 더블비 뒤 되돌림 진입 (반대편 1B 근처에서 DB 방향으로)"),
    ("lmt", 1, "장기이평(120) 터치 (정배열 매수·역배열 매도)"),
]
AI_EXITS = [(1.5, 1.0, "손절 ATR×1.5"), (2.5, 2.0, "손절 ATR×2.5")]


SESS_KO = {"asia": "아시아장", "eu": "유로장", "us": "미장"}
LAB_FILE = os.path.join(HERE, "ai_lab.json")
TF_KO_S = {"3m": "3분봉", "5m": "5분봉", "15m": "15분봉", "1h": "1시간봉"}
GENES = {"tf": ["3m", "5m", "15m", "1h"], "slk": [1.0, 1.5, 2.0, 2.5, 3.0], "actk": [0.8, 1.0, 1.5, 2.0, 3.0], "flt": [False, True],
         "sess": ["", "asia", "eu", "us"], "mv": [0, 2, 3, 4], "zf": [False, True],
         "reg": ["", "trend", "range"], "tmax": [0, 12, 24, 48],
         # 사장님식 분할 진입 (mode=basket): a1 포인트 밀리면 0.01랏 추가, a2 포인트 밀리면 l2 랏 추가, 첫 진입가에서 bstop 포인트 반대면 흐름이 바뀐 것으로 보고 전부 손절
         "slm": ["atr", "band", "p10", "p20", "p30"], "tpm": ["trail", "rr1", "rr2"],
         # 블로그 구간 매매 (mode=zone): zstep 포인트마다 0.01랏, zmax 까지, 첫 진입가에서 zstop 포인트면 손절.
         # 추가 없으면 ztp 포인트(또는 전고·전저 'hl')에서 익절, 추가됐으면 첫 진입가 + zbe 로 돌아오면 일괄 청산. avd=새벽 2~7시·1시간 BB·이평·전고저 근처 피하기
         "zstep": [5, 10], "zmax": [30, 50], "zstop": [55], "ztp": [5, 10, 15, 20, "hl"], "zbe": [0, 2], "avd": [False, True],
         # zlot: eq=추가도 0.01랏씩 / up=1·2·3·4배로 늘려 타기(블로그 5·10·15·20랏). zflip: 들고 있는데 이평 배열이 뒤집히면 본절(평단)에 무조건 정리
         "zlot": ["eq", "up"], "zflip": [True, False],
         # zhtf: 1시간봉 배열(20/120)과 같은 방향만. 1시간이 역배열인데 3분 정배열 장기이평 터치로 매수하면 1시간 장기이평 맞고 떨어지기 쉽다
         "zhtf": [True, False],
         # zvol: 블로그 작성자처럼 '한 달에 한 번 영점 조절' — 지난 20일 하루 변동폭이 70포인트일 때를 기준으로 구간·손절·익절 폭을 늘리고 줄인다
         # zvol="cal": 작성자 방식 그대로 — 지난 7일 장기이평 터치들을 되돌아보고 '보통 반등 폭'을 추가 간격으로,
         # '몇 포인트 구간이었으면 살아나왔나'(되돌아온 경우의 85%를 덮는 폭)를 구간 끝으로 다시 잡는다
         "zvol": [False, True, "cal"],
         "mode": ["atr", "basket", "zone"], "a1": [20, 25, 30], "a2": [50, 60, 70], "l2": [0.02, 0.03], "btp": [3, 5, 8], "bbe": [0.5, 1, 2], "bstop": [100]}


def ai_name(e):
    base = f"[{TF_KO_S.get(e.get('tf', '5m'), e.get('tf'))}] " + next(n for s_, w, n in AI_SIGNALS if s_ == e["sig"] and w == e["way"])
    if e.get("mode") == "zone":
        tp_ = "전고·전저" if e["ztp"] == "hl" else f"+{e['ztp']}P"
        tags = [f"구간 매매: {e['zstep']}P마다 추가({'1·2·3배로 늘려서' if e.get('zlot') == 'up' else '0.01랏씩'}, {e['zmax']}P까지) · {e['zstop']}P 손절 · 추가 없으면 {tp_} 익절 · 추가되면 첫 진입가{'+' + str(e['zbe']) + 'P' if e['zbe'] else ''} 복귀 시 일괄 청산"
            + (" · 배열 뒤집히면 본절 정리" if e.get("zflip", True) else "")
            + (" · 1시간봉 배열과 같은 방향만" if e.get("zhtf", True) else "")
            + (" · 폭은 지난 7일 이평 터치 복기로 영점 조절" if e.get("zvol") == "cal" else " · 폭은 지난 20일 변동폭에 맞춰 조절" if e.get("zvol") else "")]
    elif e.get("mode") == "basket":
        tags = [f"사장님식 분할: {e['a1']}P 밀리면 +0.01랏 · {e['a2']}P 밀리면 +{e['l2']}랏 · {e['bstop']}P 반대면 전부 손절 · 목표 +${e['btp']} (추가 후 본전+${e['bbe']})"]
    else:
        slm = e.get("slm", "atr")
        sl_t = (f"손절 ATR×{e['slk']}" if slm == "atr" else "손절 반대편 1B 바깥" if slm == "band" else f"손절 {slm[1:]}포인트")
        tp_t = {"trail": f"수익 지키기 {e['actk']}ATR부터", "rr1": "손절 폭만큼 벌면 익절(1:1)", "rr2": "손절 폭 2배 벌면 익절(1:2)"}[e.get("tpm", "trail")]
        tags = [sl_t, tp_t]
    if e.get("flt"):
        tags.append("20·120이평 방향만")
    if e.get("sess"):
        tags.append(f"{SESS_KO[e['sess']]}만")
    if e.get("mv"):
        tags.append(f"{e['mv']}ATR 이상 빠진(오른) 뒤만")
    if e.get("zf"):
        tags.append("매물대 위에서만")
    if e.get("reg"):
        tags.append("추세장에서만" if e["reg"] == "trend" else "박스장에서만")
    if e.get("tmax"):
        tags.append(f"{e['tmax']}봉 안에 수익 못 내면 정리")
    if e.get("avd"):
        tags.append("새벽 2~7시·1시간 BB·이평·전고저 근처 피함")
    return base + " · " + " · ".join(tags)


def ai_key(e):
    return (e.get("tf", "5m"), e["sig"], e["way"], e["slk"], e["actk"], bool(e.get("flt")), e.get("sess", ""), e.get("mv", 0), bool(e.get("zf")),
            e.get("reg", ""), e.get("tmax", 0), e.get("mode", "atr"), e.get("slm", "atr"), e.get("tpm", "trail"),
            *((e["a1"], e["a2"], e["l2"], e["btp"], e["bbe"], e["bstop"]) if e.get("mode") == "basket" else ()),
            *((e["zstep"], e["zmax"], e["zstop"], str(e["ztp"]), e["zbe"], e.get("zlot", "eq"), e.get("zflip", True), str(e.get("zvol") or ""), e.get("zhtf", True)) if e.get("mode") == "zone" else ()), bool(e.get("avd")))


def ai_mk(**e):
    e = {"tf": "5m", "slk": 2.5, "actk": 2.0, "slm": "atr", "tpm": "trail", "flt": False, "sess": "", "mv": 0, "zf": False, "reg": "", "tmax": 0,
         "zstep": 10, "zmax": 50, "zstop": 55, "ztp": 10, "zbe": 0, "avd": False, "zlot": "eq", "zflip": True, "zvol": False, "zhtf": True,
         "mode": "atr", "a1": 25, "a2": 60, "l2": 0.02, "btp": 5, "bbe": 1, "bstop": 100, **e}
    e["name"] = ai_name(e)
    return e


BLOG_RULE = None  # ai_mk 정의 뒤에 채운다


def ai_experts():
    """기본 후보: 5분·15분봉 × 신호 7종 × 손절 2종 × 이평 방향 걸러내기 유무."""
    base = [ai_mk(tf=tf, sig=sg, way=w, slk=sl, actk=ac, flt=fl) for tf in ("5m", "15m") for sg, w, _n in AI_SIGNALS
            for sl, ac in ((1.5, 1.0), (2.5, 2.0)) for fl in (False, True)]
    # 돌파 더블비 뒤 되돌림 진입: 손절 방식 × 청산 방식
    base += [ai_mk(tf=tf, sig="pbk", way=1, slm=sm, tpm=tp) for tf in ("5m", "15m") for sm in ("band", "p20", "atr") for tp in ("trail", "rr1", "rr2")]
    # 블로그 3분봉 장기이평 구간 매매: 10P마다 +0.01랏(50P까지) · 55P 손절 · 익절 10P/전고저 · 피할 때 피함
    global BLOG_RULE
    BLOG_RULE = ai_mk(tf="3m", sig="lmt", way=1, mode="zone", zstep=10, zmax=50, zstop=55, ztp=10, zbe=0, zlot="eq", zflip=True, zvol=False, zhtf=True, avd=True)
    base += [BLOG_RULE]
    base += [ai_mk(tf=tf, sig="lmt", way=1, mode="zone", ztp=tp, avd=True) for tf in ("3m", "5m") for tp in (10, "hl")]
    base += [ai_mk(tf="3m", sig="lmt", way=1, mode="zone", ztp="hl", avd=True, zlot="up")]
    base += [ai_mk(tf="3m", sig="lmt", way=1, mode="zone", ztp=tp, avd=True, zvol=zv) for tp in (10, "hl") for zv in (True, "cal")]
    # 사장님식 분할 진입 기본형: 25P +0.01 · 60P +0.02 · 100P 손절 · 목표 $5 (추가 후 본전+$1)
    base += [ai_mk(tf=tf, sig=sg, way=w, mode="basket", flt=fl) for tf in ("5m", "15m") for sg, w, _n in AI_SIGNALS for fl in (False, True)]
    return base


def ai_mutants(hall, n_mut=30, n_rand=10):
    """성적 좋은 로직을 한두 군데 바꿔 보고(돌연변이), 아예 새로 섞은 로직도 만든다."""
    out = []
    for _ in range(n_mut if hall else 0):
        e = dict(random.choice(hall[:10]))
        for g in random.sample(list(GENES), random.choice((1, 2))):
            e[g] = random.choice(GENES[g])
        if random.random() < 0.15:
            e["sig"], e["way"], _n = random.choice(AI_SIGNALS)
        out.append(ai_mk(**{k: e[k] for k in ("sig", "way", *GENES)}))
    for _ in range(n_rand):
        sg, w, _n = random.choice(AI_SIGNALS)
        out.append(ai_mk(sig=sg, way=w, **{g: random.choice(v) for g, v in GENES.items()}))
    return out


def ai_dir(e, f):
    s = f[e["sig"]] * e["way"]
    if not s:
        return 0
    if e.get("flt") and f["trend"] != s:
        return 0
    if e.get("sess") and f["sess"] != e["sess"]:
        return 0
    if e.get("mv") and (f["mvd"] if s > 0 else f["mvu"]) < e["mv"]:
        return 0
    if e.get("zf") and not (f["sup"] if s > 0 else f["res"]):
        return 0
    if e.get("reg") and f["reg"] != e["reg"]:
        return 0
    if e.get("avd") and f.get("avoid"):
        return 0
    if e.get("mode") == "zone" and e.get("zhtf", True) and f.get("htr") != s:
        return 0
    return s


def ai_stops(e, f, px, d):
    """진입가 px, 방향 d 일 때 손절가와 익절가(없으면 None)."""
    v = paper["cfg"].get("ptv", 1) if paper else 1
    slm, a = e.get("slm", "atr"), f["atr"]
    if e["sig"] == "zdb" and f.get("zsl"):
        sl = f["zsl"]
    elif slm == "band" and f.get("psl") is not None:
        sl = f["psl"]
    elif slm.startswith("p") and slm[1:].isdigit():
        sl = px - d * int(slm[1:]) * v
    else:
        sl = px - d * e["slk"] * a
    risk = (px - sl) * d
    tpm = e.get("tpm", "trail")
    tp = px + d * risk * (1 if tpm == "rr1" else 2) if tpm in ("rr1", "rr2") and risk > 0 else None
    return sl, tp


def ai_bt_basket(e, bars, f, start, spread=0.2, end=None):
    """사장님식 분할 진입 시험. 손익은 달러(0.01랏 = 1포인트 1달러). 추가 진입가는 정확히 a1·a2 포인트 지점, 손절은 bstop 지점에서 체결된 것으로 본다."""
    v = paper["cfg"].get("ptv", 1) if paper else 1
    out, st = [], None
    for i in range(start, end or len(bars)):
        b = bars[i]
        if st:
            d, p0 = st["d"], st["p0"]
            worst = ((p0 - b["l"]) if d > 0 else (b["h"] - p0)) / v
            if worst >= e["a1"] and 1 not in st["adds"]:
                st["legs"].append((p0 - d * e["a1"] * v, 0.01)); st["adds"].add(1)
            if worst >= e["a2"] and 2 not in st["adds"]:
                st["legs"].append((p0 - d * e["a2"] * v, e["l2"])); st["adds"].add(2)
            cost = sum(l for _px, l in st["legs"]) * 100 * spread
            if worst >= e["bstop"]:
                sp = p0 - d * e["bstop"] * v
                out.append(sum((sp - px) * d * l * 100 for px, l in st["legs"]) - cost)
                st = None
                continue
            tot = sum((b["c"] - px) * d * l * 100 for px, l in st["legs"]) - cost
            if tot >= (e["bbe"] if st["adds"] else e["btp"]):
                out.append(tot)
                st = None
            continue
        if f[i]["atr"] is None:
            continue
        d = ai_dir(e, f[i])
        if d:
            st = {"d": d, "p0": b["c"], "legs": [(b["c"], 0.01)], "adds": set()}
    return out


def zone_sz(e, fi):
    """구간 폭(포인트): (추가 간격, 최대 추가, 손절, 익절). zvol 이면 지난 20일 하루 변동폭/70 배로 조절 (0.5~2배)"""
    k = 1.0
    if e.get("zvol") == "cal":
        if fi.get("cal"):
            st, mx = fi["cal"]
            tp = st if e["ztp"] == "hl" else max(1, min(e["ztp"], st))
            return st, mx, mx + 5, tp
    elif e.get("zvol") and fi.get("dr"):
        v = paper["cfg"].get("ptv", 1) if paper else 1
        k = min(2.0, max(0.5, fi["dr"] / v / 70))
    tp = 10 if e["ztp"] == "hl" else e["ztp"]
    st = max(1, round(e["zstep"] * k))
    return st, max(st, round(e["zmax"] * k / st) * st), round(e["zstop"] * k), max(1, round(tp * k))


def ai_bt_zone(e, bars, f, start, spread=0.2, end=None):
    """블로그 구간 매매 시험. 손익은 달러(0.01랏 = 1포인트 1달러). 같은 봉에서 손절과 익절이 겹치면 손절로 본다."""
    v = paper["cfg"].get("ptv", 1) if paper else 1
    out, st = [], None
    for i in range(start, end or len(bars)):
        b = bars[i]
        if st:
            d, p0 = st["d"], st["p0"]
            zs, zm, zx, _ = st["sz"]
            worst = ((p0 - b["l"]) if d > 0 else (b["h"] - p0)) / v
            while st["n"] * zs + zs <= zm and worst >= (st["n"] + 1) * zs:
                st["n"] += 1
                st["legs"].append((p0 - d * st["n"] * zs * v, st["n"] + 1 if e.get("zlot") == "up" else 1))
            cost = sum(m for _, m in st["legs"]) * spread
            if worst >= zx:
                sp = p0 - d * zx * v
                out.append(sum((sp - px) * d * m for px, m in st["legs"]) - cost)
                st = None
                continue
            if e.get("zflip", True) and f[i]["trend"] == -d:
                st["flip"] = True
            if st.get("flip"):
                # 배열이 반대로 뒤집힘: 욕심 버리고 평단(본절)에 바로 정리
                tgt = sum(px * m for px, m in st["legs"]) / sum(m for _, m in st["legs"])
                if (b["c"] - tgt) * d >= 0 or (b["h"] >= tgt if d > 0 else b["l"] <= tgt):
                    out.append(sum((tgt - px) * d * m for px, m in st["legs"]) - cost)
                    st = None
                continue
            tgt = (p0 + d * e["zbe"] * v) if st["n"] else st["tp"]
            if (b["h"] >= tgt) if d > 0 else (b["l"] <= tgt):
                out.append(sum((tgt - px) * d * m for px, m in st["legs"]) - cost)
                st = None
            continue
        if f[i]["atr"] is None:
            continue
        d = ai_dir(e, f[i])
        if d:
            tp = None
            if e["ztp"] == "hl":
                lvl = f[i]["ph"] if d > 0 else f[i]["pl"]
                if lvl is not None and (lvl - b["c"]) * d >= 3 * v:
                    tp = lvl
            sz = zone_sz(e, f[i])
            st = {"d": d, "p0": b["c"], "legs": [(b["c"], 1)], "n": 0, "sz": sz, "tp": tp if tp is not None else b["c"] + d * sz[3] * v}
    return out


def ai_backtest(e, bars, f, start, spread=0.2, end=None):
    if e.get("mode") == "zone":
        return ai_bt_zone(e, bars, f, start, spread, end)
    if e.get("mode") == "basket":
        return ai_bt_basket(e, bars, f, start, spread, end)
    """한 번에 한 포지션. 진입은 신호 봉 종가, 청산은 손절(추적 손절 포함). 손익은 가격 차이(0.01랏이면 1달러)."""
    trades, pos = [], None
    for i in range(start, end or len(bars)):
        b = bars[i]
        if pos:
            d = pos["d"]
            if (b["l"] <= pos["sl"]) if d > 0 else (b["h"] >= pos["sl"]):
                trades.append((pos["sl"] - pos["px"]) * d - spread)  # 같은 봉에서 손절·익절 둘 다 닿으면 손절로 본다 (보수적)
                pos = None
            elif pos["tp"] is not None and ((b["h"] >= pos["tp"]) if d > 0 else (b["l"] <= pos["tp"])):
                trades.append((pos["tp"] - pos["px"]) * d - spread)
                pos = None
            elif e.get("tmax") and i - pos["i"] >= e["tmax"] and pos["peak"] < pos["act"]:
                trades.append((b["c"] - pos["px"]) * d - spread)  # 시간 손절: 정해진 봉 수 안에 수익 지키기 단계에 못 가면 종가에 정리
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
            sl, tp = ai_stops(e, f[i], b["c"], d)
            if (b["c"] - sl) * d <= 0:
                continue
            pos = {"d": d, "px": b["c"], "sl": sl, "tp": tp, "act": e["actk"] * a if tp is None else 1e9, "peak": 0, "i": i}
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


def lab_load():
    try:
        with open(LAB_FILE, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {"gen": 0, "hall": []}


def ai_learn(sym):
    """AI 연구실 (매시간): 기본 후보 + 지난 상위 로직 + 새로 만든 로직을 분봉별로 시험한다.
    최근 3일 전까지 20일(5분봉은 받을 수 있는 만큼)로 만들고 최근 3일로 검증. 하루 평균 성적으로 비교해서 분봉끼리도 공정하게 겨룬다.
    둘 다 통과한 것 중 1등을 쓰되, 지금 쓰는 로직보다 점수가 10% 넘게 좋을 때만 바꾼다. 실전에서 4연패한 로직은 24시간 쉰다."""
    lab = lab_load()
    hall = [ai_mk(**{k: h[k] for k in ("sig", "way", *GENES) if k in h}) for h in lab.get("hall", []) if h.get("sig") in {x[0] for x in AI_SIGNALS}]
    old = ai_experts() + hall + ([ai["pick"]] if ai["pick"] else [])
    old_keys = {ai_key(x) for x in old}
    new = [x for x in ai_mutants(hall) if ai_key(x) not in old_keys]  # 처음 시험하는 로직만 '새 로직'
    seen, cands = set(), []
    for e in old + new:
        k = ai_key(e)
        if k not in seen:
            seen.add(k)
            cands.append(e)
    data, ph55s = {}, {}
    split_t = time.time() - 3 * 86400
    for tf in {e.get("tf", "5m") for e in cands}:
        bars = rates(sym, tf, {"3m": 15000, "5m": 9000, "15m": 3500, "1h": 1500}.get(tf, 3000))[:-1]  # 약 한 달 + 지표 준비 기간
        if len(bars) < 300:
            continue
        f = ai_features(bars)
        split = next((i for i, x in enumerate(bars) if x["t"] >= split_t), len(bars))
        start = max(130, next((i for i, x in enumerate(bars) if x["t"] >= split_t - 27 * 86400), 130))  # 학습 27일 + 검증 3일 = 약 한 달
        days = max(1.0, (bars[split - 1]["t"] - bars[start]["t"]) / 86400) if split > start else 1.0
        # 분할 진입의 꼬리 위험: 아무 봉에서나 들어갔을 때 하루 안에 100포인트가 반대로 터진 비율 (양방향 평균)
        v = paper["cfg"].get("ptv", 1)
        look = max(1, 86400 // TF_SEC.get(tf, 300))
        hit = tot = h55 = 0
        for i in range(0, len(bars) - look, max(1, look // 24)):
            hi = max(x["h"] for x in bars[i + 1:i + 1 + look])
            lo = min(x["l"] for x in bars[i + 1:i + 1 + look])
            hit += ((bars[i]["c"] - lo) / v >= 100) + ((hi - bars[i]["c"]) / v >= 100)
            h55 += ((bars[i]["c"] - lo) / v >= 55) + ((hi - bars[i]["c"]) / v >= 55)
            tot += 2
        ph55s[tf] = h55 / tot if tot else 0.1
        data[tf] = (bars, f, start, split, days, hit / tot if tot else 0.05)
    spread = max(0.2, ai.get("spread", 0.2))
    now = time.time()
    ai["bench"] = {k: v for k, v in ai.get("bench", {}).items() if v > now}
    board = []
    for e in cands:
        if e.get("tf", "5m") not in data:
            continue
        bars, f, start, split, days, p_hit = data[e.get("tf", "5m")]
        trl = ai_backtest(e, bars, f, start, spread=spread, end=split)
        tr = ai_score(trl)
        va = ai_score(ai_backtest(e, bars, f, split, spread=spread))
        mid = (start + split) // 2
        h1 = ai_score(ai_backtest(e, bars, f, start, spread=spread, end=mid))
        h2 = ai_score(ai_backtest(e, bars, f, mid, spread=spread, end=split))
        benched = str(ai_key(e)) in ai["bench"]
        if e.get("mode") == "zone":
            # 구간 매매도 드물게 큰 손실(55포인트 손절)이 나는 구조라, 하루 안에 그만큼 반대로 터진 실제 빈도로 예상 손실을 뺀다
            legs_ = e["zmax"] // e["zstep"]
            worst = sum((e["zstop"] - k * e["zstep"]) * (k + 1 if e.get("zlot") == "up" else 1) for k in range(legs_ + 1)) * paper["cfg"].get("ptv", 1)
            # 하루 안에 55포인트 반대로 간 비율의 절반 정도가 실제 손절까지 간다고 본다 (들어가는 자리가 이평 지지라 무작위보다 낫다고 가정)
            ph55 = ph55s.get(e.get("tf", "5m"), p_hit)
            for x in (tr, va, h1, h2):
                x["net"] -= x["n"] * max(ph55, 0.02) * worst * 0.5
            tr["tail"] = round(max(ph55, 0.02) * 100, 1)
        if e.get("mode") == "basket":
            # 시험 기간에 100포인트 손절이 한 번도 안 나와 완벽해 보이는 착시를 막는다: 실제 빈도만큼 예상 손실을 뺀다
            worst = (e["bstop"] + (e["bstop"] - e["a1"]) + (e["bstop"] - e["a2"]) * e["l2"] / 0.01) * paper["cfg"].get("ptv", 1)
            for x in (tr, va, h1, h2):
                x["net"] -= x["n"] * max(p_hit, 0.02) * worst
            tr["tail"] = round(max(p_hit, 0.02) * 100, 1)
        ok = (not benched and tr["n"] >= 8 and tr["pf"] >= 1.15 and tr["mdd"] < max(1e-9, tr["net"]) * 1.5
              and h1["net"] > 0 and h2["net"] > 0  # 학습 기간 앞·뒤 절반 모두 이익 (한 구간에서만 번 로직은 탈락)
              and va["n"] >= 2 and va["net"] > 0)
        board.append({**e, "full": tr, "rec": va, "ok": ok, "benched": benched,
                      "score": (tr["net"] - tr["mdd"] * 0.5) / days + va["net"] / 3,  # 하루 평균으로 비교
                      "mon": (tr["net"] + va["net"]) / (days + 3) * 30,  # 한 달(30일) 환산 손익
                      "new": ai_key(e) not in old_keys})
    bars = data.get("5m", next(iter(data.values()), ([],)))[0]
    board.sort(key=lambda x: (x["ok"], x["score"]), reverse=True)
    best = board[0] if board and board[0]["ok"] else None
    cur = next((x for x in board if ai["pick"] and ai_key(x) == ai_key(ai["pick"])), None)
    prev = ai["pick"]["name"] if ai["pick"] else None
    if cur and cur["ok"] and best and best["score"] <= cur["score"] * 1.1 + 1e-9:
        pick, changed = cur, False
    else:
        pick, changed = best, (best["name"] if best else None) != prev
    lab["gen"] = lab.get("gen", 0) + 1
    lab["hall"] = [{k: x[k] for k in ("sig", "way", *GENES)} for x in board if x["ok"]][:40]
    lab["top"] = [{"name": x["name"], "ok": x["ok"], "new": x["new"], "mon": round(x.get("mon", 0), 2), "n": x["full"]["n"], "win": round(x["full"]["win"], 1), "pf": round(x["full"]["pf"], 2),
                   "net": round(x["full"]["net"], 2), "vnet": round(x["rec"]["net"], 2), "vn": x["rec"]["n"]} for x in board[:10]]
    lab["at"] = time.time()
    try:
        with open(LAB_FILE, "w", encoding="utf-8") as fh:
            json.dump(lab, fh, ensure_ascii=False)
    except OSError:
        pass
    # 데이터 수집 모드(기본): 연습 계좌이니 검증을 통과한 게 없어도 점수 1등으로 거래하고, 2·3등도 같이 거래해 실전 기록을 모은다
    collect = paper["cfg"].get("collect", True)
    if collect and not pick:
        pick = next((x for x in board if not x["benched"]), None)
        changed = (pick["name"] if pick else None) != prev
    picks = [pick] if pick else []
    if collect:
        for x in board:
            if len(picks) >= 3:
                break
            if not x["benched"] and all(ai_key(x) != ai_key(y) for y in picks):
                picks.append(x)
        # 사장님 지시: 블로그 규칙 그대로(3분봉·1시간 같은 방향·10P마다 추가·50P까지·55P 손절·10P 익절·첫 진입가 복귀 일괄 청산·배열 뒤집히면 본절·피할 때 피함)를 1등(텔레그램 알림)으로 매매
        if paper["cfg"].get("blog", True):
            bk = ai_key(BLOG_RULE)
            bx = next((x for x in board if ai_key(x) == bk), None)
            if bx:
                changed = changed or (pick["name"] if pick else None) != bx["name"]
                pick = bx = {**bx, "boss": True}
                picks = [bx] + [y for y in picks if ai_key(y) != bk][:2]
        # 블로그 3분봉 장기이평 구간 매매는 성적과 상관없이 한 자리를 늘 줘서 실제 시세 기록을 모은다 (한 달 뒤 판단)
        zb = next((x for x in board if x.get("mode") == "zone" and x["sig"] == "lmt" and not x["benched"]), None)
        if zb and all(not (y.get("mode") == "zone" and y["sig"] == "lmt") for y in picks):
            picks = (picks[:2] + [zb]) if len(picks) >= 3 else picks + [zb]
    ai["picks"] = picks
    ai.update(at=time.time(), pick=pick, board=board[:5], lab=lab,
              note=(f"지금 쓰는 로직{' (사장님 지정 · 블로그 3분봉 장기이평 매매)' if pick.get('boss') else '' if pick['ok'] else ' (검증 미통과 · 데이터 수집용)'}: {pick['name']} (한 달 환산 {usd(pick.get('mon', 0))} · 학습 기간 {pick['full']['n']}번 · 승률 {pick['full']['win']:.0f}% · 손익비 {pick['full']['pf']:.2f} · 최근 3일 검증 {usd(pick['rec']['net'])})"
                    if pick else "요즘 장에 잘 맞는 로직이 없어 쉬는 중"))
    # 1시간 보고 (장이 열려 있을 때만: 마지막 봉이 30분 안)
    if bars and time.time() - bars[-1]["t"] < 3600:
        okn = sum(1 for x in board if x["ok"])
        newok = sum(1 for x in board if x["ok"] and x["new"])
        hour = [h for h in paper["hist"] if h.get("strat") and h.get("ctime", 0) > (time.time() - 3600) * 1000]
        q = p_quote()
        eqv = paper["bal"] + (sum(p_pnl(p, q) for p in paper["pos"]) if q else 0)
        top3 = "\n".join(f"{k + 1}. {'🆕 ' if x['new'] else ''}{x['name']}\n   한 달 환산 {usd(x['mon'])} · 학습 {x['full']['n']}번 · 승률 {x['full']['win']:.0f}% · 손익비 {x['full']['pf']:.2f} · 최근 3일 {usd(x['rec']['net'])}"
                          for k, x in enumerate([x for x in board if x["ok"]][:3]))
        p_log(f"AI 연구실 · 1시간 보고 ({k_now()})",
              f"{'🔄 로직을 바꿨습니다' if changed else '✔ 지금 로직을 계속 씁니다'}\n{ai['note']}\n"
              + ("함께 거래하는 로직(데이터 수집): " + " / ".join(x["name"] for x in ai.get("picks", [])[1:]) + "\n" if len(ai.get("picks", [])) > 1 else "")
              + "\n" f"이번 시험: {len(board)}개 (새로 만든 것 {len(new)}개, 3분·5분·15분·1시간봉) → 통과 {okn}개 (새 로직 {newok}개) · {lab['gen']}번째 연구\n"
              f"시험 스프레드 {spread:.2f} (한텍 실제 호가 기준){' · 쉬는 로직 ' + str(len(ai['bench'])) + '개 (실전 4연패)' if ai['bench'] else ''}\n"
              f"{top3 or '통과한 로직 없음'}\n\n"
              f"지난 1시간 거래 {len(hour)}번 {usd(sum(h['pnl'] for h in hour))} · 웨이브뷰 계좌 평가금 ${eqv:,.2f}",
              tg=False)  # hourly report is log-only; too frequent for Telegram (2026-10-21)
    elif changed:
        p_log("AI 판단 · 로직 바꿈", ai["note"])


def ai_guard(e, main):
    """실전 4연패한 로직은 24시간 쉬게 하고 다음 후보로 바꾼다. 하루 손실 한도는 데이터 수집 모드면 알리기만 하고 계속 들어간다."""
    by, order = {}, []  # 분할 진입은 여러 건이 한 번의 거래 → 묶음(group) 단위로 센다
    for h in paper["hist"]:
        if h.get("logic") == e["name"]:
            g = h.get("group") or h["id"]
            if g not in by:
                by[g] = {"pnl": 0.0}
                order.append(g)
            by[g]["pnl"] += h["pnl"]
    live = [by[g] for g in order[:4]]
    blog = paper["cfg"].get("blog", True) and BLOG_RULE and ai_key(e) == ai_key(BLOG_RULE)  # 사장님이 정한 규칙 매매는 쉬지 않는다 (본절 정리도 스프레드만큼 −라 연패로 잘못 셀 수 있음)
    if not blog and len(live) == 4 and all(h["pnl"] < 0 for h in live):
        ai["bench"][str(ai_key(e))] = time.time() + 86400
        p_log("AI 판단 · 로직 쉬게 함", f"{e['name']}\n실전에서 4번 연속 손실이라 24시간 쉬고 다음 후보로 바꿉니다 (합계 {usd(sum(h['pnl'] for h in live))}).")
        ai["picks"] = [x for x in ai.get("picks", []) if ai_key(x) != ai_key(e)]
        if main:
            ai["pick"], ai["at"] = None, 0  # 다음 순서에 바로 다시 연구
        return False
    k = datetime.now(KST)
    day0 = datetime(k.year, k.month, k.day, tzinfo=KST).timestamp() * 1000
    today = sum(h["pnl"] for h in paper["hist"] if h.get("strat") and h.get("ctime", 0) >= day0)
    lim = float(paper["cfg"].get("dayLoss", 30))
    if today <= -lim:
        tag = k.strftime("%Y-%m-%d")
        collect = paper["cfg"].get("collect", True)
        if ai.get("dayStop") != tag:
            ai["dayStop"] = tag
            p_log("AI 판단 · 오늘 손실 한도 넘음", f"오늘 손실 {usd(today)} (한도 ${lim:.0f})."
                  + (" 연습 계좌 데이터 수집 모드라 계속 들어갑니다." if collect else " 오늘은 새로 진입하지 않습니다."))
        if not collect:
            return False
    return True


def ai_signal(q):
    """상위 로직(최대 3개)이 각자 따로 진입한다. 텔레그램은 1등 로직 거래만 보낸다."""
    picks = ai.get("picks") or ([ai["pick"]] if ai["pick"] else [])
    feats = {}
    for r, e in enumerate(picks):
        if any(p.get("logic") == e["name"] for p in paper["pos"]):
            continue
        tf = e.get("tf", "5m")
        if tf not in feats:
            # 구간 매매는 1시간봉 BB·120이평(피할 때)을 보려고 더 길게 받는다
            bars = rates(q["sym"], tf, 3000 if tf == "3m" else 1800 if tf == "5m" else 400)[:-1]
            feats[tf] = (bars, ai_features(bars))
        bars, f = feats[tf]
        key = f"ai|{q['sym']}|{ai_key(e)}"
        bt = bars[-1]["t"]
        if paper["lastSig"].get(key) == bt:
            continue
        first = key not in paper["lastSig"]
        paper["lastSig"][key] = bt
        if first:
            continue
        d = ai_dir(e, f[-1])
        if not d or f[-1]["atr"] is None or not ai_guard(e, r == 0):
            continue
        nb = news_block()
        if nb and not paper["cfg"].get("collect", True):
            p_log("진입 건너뜀", "중요 경제지표 발표 전후라 대기합니다.")
            continue
        a = f[-1]["atr"]
        px = q["ask"] if d > 0 else q["bid"]
        if e.get("mode") == "zone":
            v = paper["cfg"].get("ptv", 1)
            hl = None
            if e["ztp"] == "hl":
                lvl = f[-1]["ph"] if d > 0 else f[-1]["pl"]
                if lvl is not None and (lvl - px) * d >= 3 * v:
                    hl = lvl
            zs, zm, zx, tpp = zone_sz(e, f[-1])
            z = {"step": zs, "max": zm, "stop": zx, "be": e["zbe"], "hl": hl is not None, "tpp": tpp,
                 "up": e.get("zlot") == "up", "flip": e.get("zflip", True), "tf": e.get("tf", "3m"),
                 "tp": round(hl if hl is not None else px + d * tpp * v, 2)}
            p = p_open(q, d, 0.01, "ai", f"Z{int(time.time() * 1000)}{r}", quiet=True)
            if not p:
                continue
            p.update(zone=z, logic=e["name"], rank=r + 1, news=bool(nb), silent=r > 0)
            if r == 0:
                legs = zm // zs
                worst = sum((zx - k * zs) * (k + 1 if e.get("zlot") == "up" else 1) for k in range(legs + 1)) * v
                p_log(f"{side_ko(d)} 진입 · 0.01랏 · 장기이평 구간 매매",
                      f"종목: {p['sym']}\n진입가: {p['open']:,.2f}\n"
                      f"익절: {z['tp']:,.2f} ({'전고·전저' if hl is not None else f'+{tpp}포인트'}, 추가가 없을 때)\n"
                      f"구간 추가: {zs}포인트마다 {'0.02·0.03·0.04랏으로 늘려서' if e.get('zlot') == 'up' else '0.01랏'} ({p['open'] - d * zs * v:,.2f}부터 {p['open'] - d * zm * v:,.2f}까지 최대 {legs}번)\n"
                      f"추가되면: 첫 진입가로 돌아올 때 일괄 청산{' · 배열 뒤집히면 본절 정리' if z['flip'] else ''}\n"
                      + (f"영점 조절: 지난 7일 장기이평 터치 복기 → 반등 폭 {zs}P · 살아나온 구간 {zm}P\n" if e.get("zvol") == "cal" and f[-1].get("cal")
                         else f"폭 조절: 지난 20일 하루 평균 변동폭 {f[-1]['dr'] / v:.0f}포인트 기준\n" if e.get("zvol") and f[-1].get("dr") else "")
                      + f""
                      f"손절: {p['open'] - d * zx * v:,.2f} ({zx}포인트 · 다 추가된 뒤 손절되면 약 −${worst:,.0f})\n"
                      f"시각: {k_now()} (한국){' · ⚠ 경제지표 발표 시간' if nb else ''}\n\n"
                      f"이유: {e['name']}\n학습 기간 성적: {e['full']['n']}번 · 승률 {e['full']['win']:.0f}% · 손익비 {e['full']['pf']:.2f}"
                      + ("\n(사장님 지정 규칙 · 블로그 3분봉 장기이평 매매)" if e.get("boss") else "" if e.get("ok", True) else "\n(검증 미통과 로직 · 연습 계좌 데이터 수집용)"))
            continue
        if e.get("mode") == "basket":
            bk = {k: e[k] for k in ("a1", "a2", "l2", "btp", "bbe", "bstop")}
            p = p_open(q, d, 0.01, "ai", f"B{int(time.time() * 1000)}{r}", quiet=True)
            if not p:
                continue
            p.update(basket=bk, logic=e["name"], rank=r + 1, news=bool(nb), silent=r > 0)
            if r == 0:
                v = paper["cfg"].get("ptv", 1)
                worst = 100 * (bk["bstop"] + (bk["bstop"] - bk["a1"]) + (bk["bstop"] - bk["a2"]) * bk["l2"] / 0.01) * 0.01 * v
                p_log(f"{side_ko(d)} 진입 · 0.01랏 · 사장님식 분할 진입",
                      f"종목: {p['sym']}\n진입가: {p['open']:,.2f}\n"
                      f"1차 추가: {p['open'] - d * bk['a1'] * v:,.2f} ({bk['a1']}포인트 밀리면 0.01랏)\n"
                      f"2차 추가: {p['open'] - d * bk['a2'] * v:,.2f} ({bk['a2']}포인트 밀리면 {bk['l2']}랏)\n"
                      f"흐름 바뀜 손절: {p['open'] - d * bk['bstop'] * v:,.2f} ({bk['bstop']}포인트 · 다 추가된 뒤 손절되면 약 −${worst:,.0f})\n"
                      f"목표: +${bk['btp']} (추가가 들어가면 본전+${bk['bbe']}에서 탈출)\n"
                      f"시각: {k_now()} (한국){' · ⚠ 경제지표 발표 시간' if nb else ''}\n\n"
                      f"이유: {e['name']}\n학습 기간 성적: {e['full']['n']}번 · 승률 {e['full']['win']:.0f}% · 손익비 {e['full']['pf']:.2f}"
                      + ("" if e.get("ok", True) else "\n(검증 미통과 로직 · 연습 계좌 데이터 수집용)"))
            continue
        sl, tp = ai_stops(e, f[-1], px, d)
        if (px - sl) * d <= 0:  # 이미 손절가를 지나 있으면 들어가지 않는다
            continue
        lots = paper["cfg"].get("aiLot", 0.01)
        p = p_open(q, d, lots, "ai", f"A{int(time.time() * 1000)}{r}", round(sl, 2), quiet=True)
        if not p:
            continue
        p["act"] = round(e["actk"] * a / paper["cfg"].get("ptv", 1), 2) if tp is None else 1e9
        p["tp"] = round(tp, 2) if tp is not None else None
        p["logic"] = e["name"]
        p["rank"] = r + 1
        p["news"] = bool(nb)
        p["silent"] = r > 0
        p["tmax_s"] = e.get("tmax", 0) * TF_SEC.get(tf, 300)
        if r == 0:
            cs = paper["cfg"]["cs"]
            start = p["open"] + d * e["actk"] * a
            p_log(f"{side_ko(d)} 진입 · {lots}랏 · AI 판단",
                  f"종목: {p['sym']}\n"
                  f"진입가: {p['open']:,.2f}\n"
                  f"손절가: {p['sl']:,.2f} ({(p['sl'] - p['open']):+.2f} · 손절되면 {usd((p['sl'] - p['open']) * d * lots * cs)})\n"
                  + (f"익절가: {p['tp']:,.2f} ({(p['tp'] - p['open']):+.2f} · 익절되면 {usd((p['tp'] - p['open']) * d * lots * cs)})\n" if p.get("tp")
                     else f"수익 지키기 시작: {start:,.2f} 넘으면 (그 뒤로 번 것의 절반을 지키며 손절선을 따라 올림)\n") +
                  f"시각: {k_now()} (한국){' · ⚠ 경제지표 발표 시간 (데이터 수집용으로 진입)' if nb else ''}\n\n"
                  f"이유: {e['name']}\n학습 기간 성적: {e['full']['n']}번 · 승률 {e['full']['win']:.0f}% · 손익비 {e['full']['pf']:.2f} · ATR {a:.2f}"
                  + ("" if e.get("ok", True) else "\n(검증 미통과 로직 · 연습 계좌 데이터 수집용)"))


def p_signals(q):
    c = paper["cfg"]
    if paper["auto"].get("ai", True):
        ai["spread"] = ai.get("spread", 0.2) * 0.98 + max(0.0, q["ask"] - q["bid"]) * 0.02  # 실제 호가 차이 평균
        if time.time() - ai["at"] > 3600:
            ai_learn(q["sym"])
        ai_signal(q)
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


def weekly_report():
    """토요일 아침 7시(한국) 한 주 성적 보고 — 한 번만."""
    k = datetime.now(KST)
    tag = k.strftime("%G-W%V")
    if k.isoweekday() != 6 or k.hour < 7 or paper.get("weekly") == tag:
        return
    paper["weekly"] = tag
    since = (time.time() - 7 * 86400) * 1000
    wk = [h for h in paper["hist"] if h.get("strat") and h.get("ctime", 0) >= since]
    by = {}
    for h in wk:
        by.setdefault(h.get("logic") or STRAT_KO.get(h.get("strat"), "?"), []).append(h["pnl"])
    rank = sorted(by.items(), key=lambda kv: sum(kv[1]), reverse=True)
    wins = sum(1 for h in wk if h["pnl"] > 0)
    lab = lab_load()
    p_log(f"📅 주간 보고 ({k.strftime('%m/%d')})",
          f"이번 주 거래 {len(wk)}번 · 손익 {usd(sum(h['pnl'] for h in wk))} · 승률 {wins / len(wk) * 100 if wk else 0:.0f}%\n"
          f"계좌 잔액 ${paper['bal']:,.2f} (대결 시작 $1,000)\n"
          + (f"가장 잘한 로직: {rank[0][0]} ({usd(sum(rank[0][1]))}, {len(rank[0][1])}번)\n" if rank else "")
          + (f"가장 못한 로직: {rank[-1][0]} ({usd(sum(rank[-1][1]))}, {len(rank[-1][1])}번)\n" if len(rank) > 1 else "")
          + f"AI 연구 누적 {lab.get('gen', 0)}번 · 지금 로직: {ai['pick']['name'] if ai['pick'] else '쉬는 중'}")


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
                            weekly_report()
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
    # 웨이브뷰와의 연결 문을 먼저 연다 (MT5 가 아직 안 켜져도 웹이 '연결 대기'를 알 수 있고, 5분마다 도는 자동 실행이 중복으로 켜지지 않는다)
    port = int(cfg["port"])
    srv = None
    for _ in range(30):  # 다시 시작할 때 앞 프로그램이 포트를 놓을 때까지 기다린다
        try:
            srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
            break
        except OSError:
            time.sleep(2)
    if srv is None:
        print("포트를 열지 못했습니다 (이미 켜져 있는 것 같습니다)")
        return
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    print(f"웨이브뷰 연결 주소: http://127.0.0.1:{port}")
    while True:
        try:
            if mt5.initialize(timeout=60000):
                break
            print("MT5 에 연결하지 못했습니다. MT5 를 켜고 로그인하면 자동으로 연결합니다. (10초 뒤 다시 시도)", mt5.last_error())
        except Exception as e:  # noqa: BLE001
            print("MT5 연결 오류:", e)
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
    while True:
        time.sleep(3600)


if __name__ == "__main__":
    main()
