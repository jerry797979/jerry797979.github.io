# -*- coding: utf-8 -*-
"""
지오테스 매일 자동발행 —  python _tools/daily_post.py [개수]   (기본 2)

대기열에서 N편을 꺼내 페이지로 찍고, 검사한 뒤 ziotes.com 에 올립니다.

콜비즈와 다른 점은 올리는 방법 하나뿐입니다.
콜비즈는 우리 쪽에서 wrangler 로 바로 배포하지만, ziotes.com 은 거래처 서버라
그럴 수 없습니다. 그 자리를 _post.php / push_post.py 가 대신합니다.

순서
  대기열 확인 → 모자라면 AI 생성 → 페이지 찍기 → 목록·사이트맵 →
  발행 전 검사 → 저장소에 커밋 → 서버로 전송 → CRM 보고 → 접속 확인 → 텔레그램
"""
import os
import re
import io
import sys
import json
import datetime
import subprocess
import urllib.request

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import gen_posts
import gen_sitemap
import push_post
from backlog import BACKLOG

try:
    import crm_sync
except Exception:
    crm_sync = None

LIVE = "https://ziotes.com"
POSTS_DIR = os.path.join(ROOT, "dist", "posts")
PUB_FILE = os.path.join(HERE, "published_slugs.txt")
DATES_FILE = os.path.join(HERE, "publish_dates.json")
TG_FILE = os.path.join(HERE, "telegram.json")
LOG = os.path.join(HERE, "daily_post.log")

LAST_AUTOFILL_ERROR = ""


def log(msg, screen=True):
    line = msg if isinstance(msg, str) else str(msg)
    if screen:
        print(line)
    try:
        with io.open(LOG, "a", encoding="utf-8") as f:
            f.write("%s %s\n" % (datetime.datetime.now().strftime("%m-%d %H:%M"), line))
    except Exception:
        pass


def load_pub():
    if not os.path.exists(PUB_FILE):
        return []
    return [l.strip() for l in io.open(PUB_FILE, encoding="utf-8") if l.strip()]


def notify(text):
    """텔레그램으로 알린다. 실패해도 발행은 그대로 진행한다."""
    if not os.path.exists(TG_FILE):
        return
    cfg = json.load(io.open(TG_FILE, encoding="utf-8"))
    token = cfg.get("bot_token")
    for cid in cfg.get("chat_ids", []):
        try:
            data = json.dumps({
                "chat_id": cid, "text": text,
                "parse_mode": "HTML", "disable_web_page_preview": True,
            }).encode("utf-8")
            req = urllib.request.Request(
                "https://api.telegram.org/bot%s/sendMessage" % token,
                data=data, headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=15).read()
        except Exception as ex:
            log("텔레그램 전송 실패 %s: %s" % (cid, ex))


def autofill(need, pool):
    """대기열이 모자라면 CRM 키워드로 원고를 만들어 채운다.

    gen_ziotes 는 진행·반려 사유를 print 로만 뱉는다. 작업 스케줄러로 돌면
    그 화면이 아무 데도 안 남아, 실패한 날 로그에 '대기열 비었음' 한 줄만 남는다.
    화면에도 그대로 두면서 로그에도 같이 적는다.
    """
    global LAST_AUTOFILL_ERROR
    try:
        import importlib
        import gen_ziotes

        원래출력 = sys.stdout
        받아쓰기 = io.StringIO()

        class _둘다(object):
            def write(self, s):
                원래출력.write(s)
                받아쓰기.write(s)
                return len(s)

            def flush(self):
                원래출력.flush()

        try:
            sys.stdout = _둘다()
            made = gen_ziotes.autofill(need)
        finally:
            # 도중에 터져도 여기까지 뱉은 사유는 남긴다 (크레딧 소진·API 오류 등)
            sys.stdout = 원래출력
            for 줄 in 받아쓰기.getvalue().splitlines():
                if 줄.strip():
                    log("  " + 줄.rstrip(), screen=False)

        if not made:
            return pool, []
        import backlog as _bl
        importlib.reload(_bl)
        log("자동 생성 %d개 보충: %s" % (len(made), ", ".join(p["slug"] for p in made)))
        return list(_bl.BACKLOG), made
    except Exception as ex:
        # 왜 못 만들었는지 남겨 둔다 — 아래 '대기열 비었음' 알림에 그대로 실린다.
        LAST_AUTOFILL_ERROR = str(ex)
        log("자동 생성 건너뜀: %s" % ex)
        return pool, []


def 커밋(slugs):
    """저장소에도 남긴다.

    서버에는 API 로 직접 보내지만, 저장소가 원본이라는 원칙은 지킨다.
    안 하면 서버에만 있고 저장소에는 없는 글이 생겨 나중에 되짚을 수 없다.
    실패해도 발행은 계속한다 — 사이트에 글이 올라가는 게 먼저다.
    """
    msg = "정보 글 자동 발행: %s" % ", ".join(slugs)
    try:
        subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True,
                       capture_output=True, timeout=60)
        r = subprocess.run(["git", "commit", "-m", msg], cwd=ROOT,
                           capture_output=True, timeout=60, text=True,
                           encoding="utf-8", errors="replace")
        if r.returncode != 0 and "nothing to commit" not in (r.stdout or ""):
            log("커밋 실패(무시): %s" % (r.stdout or r.stderr or "")[:200])
            return False
        r = subprocess.run(["git", "push", "origin", "main"], cwd=ROOT,
                           capture_output=True, timeout=180, text=True,
                           encoding="utf-8", errors="replace")
        if r.returncode != 0:
            log("푸시 실패(무시): %s" % (r.stderr or "")[:200])
            return False
        log("저장소에 커밋·푸시 완료")
        return True
    except Exception as ex:
        log("커밋 단계 오류(무시): %s" % ex)
        return False


def main():
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    published = load_pub()
    pool = list(BACKLOG)
    pending = [p for p in pool if p["slug"] not in published]

    if len(pending) < count:
        pool, made = autofill(count - len(pending), pool)
        if made:
            pending = [p for p in pool if p["slug"] not in published]

    todo = pending[:count]
    if not todo:
        log("대기열 비었음")
        if LAST_AUTOFILL_ERROR:
            log("자동 생성 실패 사유: %s" % LAST_AUTOFILL_ERROR)
        # 큐(봇이 미리 집어 둔 것)와 창고(아직 안 집어간 재고)는 다른 숫자다. 갈라서 적는다.
        tail = ""
        if crm_sync:
            try:
                _, new = crm_sync.compare()
                if new:
                    tail = "\n\n봇 큐에 남은 키워드 %d개\n%s" % (
                        len(new), ", ".join(k for _, k in new[:10]))
                else:
                    tail = "\n\n봇 큐에 남은 키워드가 없습니다."
                재고 = crm_sync.stock()
                if 재고 is None:
                    tail += "\n\n창고 재고는 확인하지 못했습니다."
                elif 재고 > 0:
                    tail += ("\n\nCRM 창고에는 아직 안 쓴 키워드 %d개가 있습니다 — "
                             "큐가 비면 봇이 알아서 더 집어 옵니다. "
                             "키워드가 없어서 멈춘 게 아닙니다." % 재고)
                else:
                    tail += "\n\nCRM 창고도 비었습니다. 키워드부터 채워야 합니다."
            except Exception as ex:
                log("CRM 조회 실패(무시): %s" % ex)
        why = ("자동 생성 실패 사유: %s" % LAST_AUTOFILL_ERROR) if LAST_AUTOFILL_ERROR else (
            "자동 생성도 글을 못 만들었습니다. 시도한 키워드와 반려 사유가 "
            "로그에 줄줄이 남아 있습니다:\nbitwave\\_tools\\daily_post.log")
        notify("<b>[지오테스] 자동발행 대기열이 비었습니다.</b>\n" + why + tail)
        return

    # 발행일 기록 — 새 글만 오늘 날짜, 이미 있으면 그대로 둔다
    try:
        dates = json.load(io.open(DATES_FILE, encoding="utf-8"))
    except Exception:
        dates = {}
    today = datetime.date.today().isoformat()
    for p in todo:
        dates.setdefault(p["slug"], today)
    json.dump(dates, io.open(DATES_FILE, "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)

    # 페이지 찍기
    for p in todo:
        d = os.path.join(POSTS_DIR, p["slug"])
        os.makedirs(d, exist_ok=True)
        io.open(os.path.join(d, "index.html"), "w", encoding="utf-8", newline="").write(
            gen_posts.build_html(p))
        published.append(p["slug"])
        log("발행 파일 생성: %s (%s)" % (p["slug"], dates[p["slug"]]))

    io.open(PUB_FILE, "w", encoding="utf-8", newline="").write("\n".join(published) + "\n")

    # 목록 재생성 — 기존 글 + 지금까지 발행된 대기열
    gen_posts.POSTS = list(gen_posts.POSTS) + [
        p for p in pool if p["slug"] in published
        and p["slug"] not in {x["slug"] for x in gen_posts.POSTS}]
    io.open(os.path.join(POSTS_DIR, "index.html"), "w", encoding="utf-8", newline="").write(
        gen_posts.build_index())

    try:
        gen_sitemap.main()
        log("sitemap 재생성")
    except Exception as ex:
        log("sitemap 재생성 실패(무시): %s" % ex)

    # 발행 전 검사 — 문제가 있으면 올리지 않는다
    try:
        import verify_publish
        probs, 본것 = verify_publish.validate()
        if probs:
            log("검증 실패 %d건 — 전송 중단" % len(probs))
            notify("<b>[지오테스] 발행 중단 — 검증 실패 %d건</b>\n\n%s"
                   % (len(probs), "\n".join("· " + p for p in probs[:10])))
            return
        log("발행 전 검사 통과 (%d쪽)" % 본것)
    except Exception as ex:
        log("검증 단계 오류(무시하고 진행): %s" % ex)

    # 저장소에 먼저 남기고, 그다음 서버로 보낸다
    커밋([p["slug"] for p in todo])

    보냄, 실패 = [], []
    for p in todo:
        try:
            (보냄 if push_post.보내기(p["slug"]) else 실패).append(p["slug"])
        except Exception as ex:
            log("전송 오류 %s: %s" % (p["slug"], ex))
            실패.append(p["slug"])
    log("전송 완료 %d개 / 실패 %d개" % (len(보냄), len(실패)))

    # CRM 보고 — 안 하면 이미 쓴 키워드가 계속 대기로 남는다
    if crm_sync and 보냄:
        for slug in 보냄:
            try:
                if crm_sync.report_done_by_slug(slug):
                    log("CRM 완료 보고: %s" % slug)
            except Exception as ex:
                log("CRM 보고 실패(무시) %s: %s" % (slug, ex))

    # 실제로 열리는지 확인 — 404를 다음 날까지 모르는 일이 없게
    dead = []
    if 보냄:
        try:
            import verify_publish
            dead = verify_publish.check_urls(
                ["/posts/%s/" % s for s in 보냄] + ["/posts/"])
        except Exception as ex:
            log("접속 확인 오류(무시): %s" % ex)

    lines = "\n".join("· %s — %s/posts/%s/" % (p.get("kw") or p["title"], LIVE, p["slug"])
                      for p in todo if p["slug"] in 보냄)
    if 실패:
        lines += "\n\n전송 실패 %d개\n" % len(실패) + "\n".join("! " + s for s in 실패)
    if dead:
        lines += "\n\n안 열리는 주소 %d개\n" % len(dead) + "\n".join("! " + u for u in dead[:5])
    상태 = "발행 완료" if (보냄 and not 실패 and not dead) else "발행됨(확인 필요)"
    notify("<b>[지오테스] 오늘의 자동 포스팅 %d건 %s</b>\n\n%s" % (len(보냄), 상태, lines))
    log("완료: %s" % 보냄)


if __name__ == "__main__":
    # 예기치 못한 오류도 반드시 말하고 죽는다. 조용히 끝나면 그날 발행이 없었다는 걸
    # 아무도 모른다 — 알림이 안 온 것과 성공한 것이 구분되지 않는다.
    try:
        main()
    except Exception as e:
        import traceback
        log("치명적 오류: %s" % e)
        log(traceback.format_exc())
        try:
            notify("<b>[지오테스] 자동 포스팅 실패</b>\n\n%s: %s" % (type(e).__name__, e))
        except Exception:
            pass
        raise
