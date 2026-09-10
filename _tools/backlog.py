# -*- coding: utf-8 -*-
"""
정보 글 대기열 — daily_post.py 가 여기서 앞에서부터 꺼내 발행합니다.

두 종류가 섞여 있습니다.

  1. 손으로 쓴 원고 — 아래 BACKLOG 목록에 직접 적습니다. 항상 먼저 나갑니다.
  2. 자동 생성분 — gen_ziotes.py 가 generated/*.json 에 넣어 둔 것. 그 뒤를 채웁니다.

원고 한 편의 생김새는 gen_posts.py 의 POSTS 항목과 같습니다.
  slug cat title desc h1 sub answer_q answer body faq
"""
import os
import json

# ── 손으로 쓴 원고 ────────────────────────────────────
# 급하게 내보내야 할 글이 있으면 여기에 직접 적으면 자동 생성분보다 먼저 나갑니다.
BACKLOG = [
]


# ── 자동 생성분 ──────────────────────────────────────
def _load_generated():
    """generated/*.json 을 읽어 온다.

    깨진 파일이 하나 있어도 그것만 건너뛴다. 파일 하나 때문에
    그날 발행이 통째로 멈추는 일이 없게 한다.
    """
    d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "generated")
    out = []
    if not os.path.isdir(d):
        return out
    for fn in sorted(os.listdir(d)):
        if not fn.endswith(".json"):
            continue
        try:
            p = json.load(open(os.path.join(d, fn), encoding="utf-8"))
            if p.get("slug") and p.get("body") and p.get("faq"):
                out.append(p)
        except Exception:
            pass
    return out


_있는것 = {p["slug"] for p in BACKLOG}
BACKLOG += [p for p in _load_generated() if p["slug"] not in _있는것]
