# -*- coding: utf-8 -*-
"""
키워드 CRM 연동 — 지오테스(company_id=4, 글그룹 3)

  python crm_sync.py            대기열 대조만 (아무것도 안 바꿈)
  python crm_sync.py --report   이미 글이 있는 키워드를 CRM에 '완료'로 보고
  python crm_sync.py --next 10  아직 글 없는 키워드 N개 뽑기

daily_post.py 가 발행할 때도 report_done() 을 불러 자동으로 보고한다.
"""
import sys, io, os, json, urllib.request

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

CRM = "https://keyword-crm.marketwave99.workers.dev"
KEY = "partner-436f9e16fb0dff6b01c0"
# 2026-09-03: 콜비즈가 지오테스(4) 밑에서 독립 업체(6)로 떨어져 나갔는데 여기가 4로
# 남아 있었다. geo-autopick 은 "company_id=4 AND group_id=2" 로 찾는데 그런 키워드는
# 한 건도 없어서(그룹2는 전부 회사6) 588개를 두고도 "키워드가 없다"며 발행이 멈췄다.
COMPANY = 4                       # 지오테스
# 글 그룹(중 카테고리) — 업체 하나에 사이트가 여럿일 수 있다.
# 지오테스 업체 아래에 전국콜비즈(callbiz.kr)와 지오테스(ziotes.com)가 따로 있어서,
# 이걸 안 주면 콜센터 솔루션 키워드로 번호 개통 글을 쓰게 된다.
#   2 = 전국콜비즈(callbiz.kr) · 3 = 지오테스(ziotes.com)
# 콜비즈는 대표번호 개통, 지오테스는 콜센터 구축이다. 그룹을 안 주면
# 번호 개통 키워드로 콜센터 글을 쓰게 된다.
GROUP = 3
LIVE = "https://ziotes.com"

# Cloudflare가 기본 파이썬 UA를 403으로 막는다 — 반드시 UA를 붙일 것
HEADERS = {
    "X-Partner-Key": KEY,
    "User-Agent": "ziotes-crm-sync/1.0",
    "Content-Type": "application/json",
}


def _call(path, data=None, timeout=30):
    req = urllib.request.Request(
        CRM + path,
        data=json.dumps(data).encode("utf-8") if data is not None else None,
        headers=HEADERS,
        method="POST" if data is not None else "GET",
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _geo_pending(limit=50):
    q = "/api/partner/geo-pending?company=%d&limit=%d" % (COMPANY, limit)
    if GROUP:
        q += "&group=%d" % GROUP
    return _call(q)


def pending(limit=50):
    """봇 큐에 집어 둔 키워드 — 아직 글이 안 나간 것"""
    return _geo_pending(limit).get("items", [])


def stock():
    """창고 재고 — 아직 큐에 집어가지도 않은 키워드 수. 못 읽으면 None.

    큐(pending)와 창고(stock)는 다른 숫자다. 큐가 비면 봇이 창고에서 더 집어 온다.
    2026-09-04: 이 둘을 같은 것으로 알려 보내서, 창고에 539개가 있는데도
    "CRM에 남은 키워드 3개"라고 떠 재고가 바닥난 줄 알았다.
    """
    try:
        return _geo_pending(1).get("stock")
    except Exception:
        return None


def local_map():
    """로컬에 있는 글: 공백 뗀 키워드 -> (slug, title)"""
    import gen_posts
    from backlog import BACKLOG
    m = {}
    for p in list(gen_posts.POSTS) + list(BACKLOG):
        # 손으로 쓴 글에는 kw 가 없을 수 있다. 그런 글은 CRM 키워드와 짝지을
        # 대상이 아니므로 건너뛴다. (없는 키로 죽으면 대조 자체가 안 된다)
        kw = (p.get("kw") or "").strip()
        if not kw:
            continue
        m[kw.replace(" ", "")] = (p["slug"], p.get("title", kw))
    return m


def report_done(kw_id, slug, title):
    """이 키워드로 글이 나갔다고 CRM에 알린다"""
    try:
        _call("/api/partner/geo-done", {
            "id": kw_id,
            "url": "%s/posts/%s/" % (LIVE, slug),
            "title": title,
        })
        return True
    except Exception as e:
        print("  ! CRM 보고 실패 (id=%s): %s" % (kw_id, e))
        return False


def report_done_by_slug(slug):
    """슬러그로 CRM 키워드를 찾아 완료 보고 (daily_post.py 가 사용)"""
    lm = local_map()
    kw_by_slug = {v[0]: (k, v[1]) for k, v in lm.items()}
    if slug not in kw_by_slug:
        return False
    kw_norm, title = kw_by_slug[slug]
    for it in pending(50):
        if it["keyword"].replace(" ", "") == kw_norm:
            return report_done(it["id"], slug, title)
    return False   # CRM 대기열에 없으면 조용히 넘어감(이미 보고됨)


def compare():
    lm = local_map()
    have, new = [], []
    for it in pending(50):
        k = it["keyword"].replace(" ", "")
        if k in lm:
            have.append((it["id"], it["keyword"], lm[k][0], lm[k][1]))
        else:
            new.append((it["id"], it["keyword"]))
    return have, new


def main():
    args = sys.argv[1:]
    have, new = compare()

    print("[이미 글이 있는데 CRM엔 대기중] %d개" % len(have))
    for i, k, s, _ in have:
        print("   %-6s %-16s -> /posts/%s/" % (i, k, s))
    print()
    print("[아직 글이 없는 키워드] %d개" % len(new))
    for i, k in new:
        print("   %-6s %s" % (i, k))
    print()

    if "--report" in args:
        print("CRM에 완료 보고 중...")
        n = sum(1 for i, k, s, t in have if report_done(i, s, t))
        print("완료 보고 %d/%d건" % (n, len(have)))
    elif "--next" in args:
        try:
            cnt = int(args[args.index("--next") + 1])
        except Exception:
            cnt = 10
        print("다음에 쓸 키워드 %d개:" % cnt)
        for i, k in new[:cnt]:
            print("   %s  %s" % (i, k))
    else:
        print("바꾼 것 없음. 반영하려면 --report 를 붙이세요.")


if __name__ == "__main__":
    main()
