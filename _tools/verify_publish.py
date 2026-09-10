# -*- coding: utf-8 -*-
"""
발행 직전 검사 —  python _tools/verify_publish.py

찍어 놓은 /posts/ 페이지들을 다시 훑어 문제가 있으면 목록으로 돌려줍니다.
daily_post.py 는 하나라도 걸리면 **올리지 않고 멈춥니다.**
깨진 글이 나가는 것보다 안 나가는 게 낫기 때문입니다.

gen_ziotes.py 의 check() 는 '만들 때' 원고를 봅니다.
이 파일은 '올리기 직전' 완성된 HTML 을 봅니다. 손으로 쓴 글도 여기서 걸립니다.
"""
import os
import re
import io
import sys
import json
import urllib.request

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DIST = os.path.join(ROOT, "dist")
POSTS = os.path.join(DIST, "posts")
LIVE = "https://ziotes.com"

TEL = "1555-5528"
FORBIDDEN = ["업계 최저가", "무조건 승인", "100% 보장", "국내 유일", "절대 해지 안",
             "업계 1위", "국내 최대"]
MIN_CHARS = 1500


def _text(h):
    h = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", h, flags=re.S)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h)).strip()


def page_files():
    if not os.path.isdir(POSTS):
        return []
    out = []
    for name in sorted(os.listdir(POSTS)):
        p = os.path.join(POSTS, name, "index.html")
        if os.path.isfile(p):
            out.append((name, p))
    return out


def validate(only=None):
    """문제 목록과 검사한 쪽수를 돌려준다. only 를 주면 그 slug 들만 본다."""
    probs = []
    본것 = 0
    제목들 = {}

    for slug, path in page_files():
        if only and slug not in only:
            continue
        본것 += 1
        h = io.open(path, encoding="utf-8").read()
        t = _text(h)

        if not h.lstrip().lower().startswith("<!doctype html"):
            probs.append("%s — <!doctype html> 로 시작하지 않음" % slug)
        if "</html>" not in h:
            probs.append("%s — </html> 이 없음(잘린 파일)" % slug)
        if len(t) < MIN_CHARS:
            probs.append("%s — 본문이 너무 짧음(%d자, %d자 이상이어야 함)" % (slug, len(t), MIN_CHARS))

        m = re.search(r"<title>(.*?)</title>", h, re.S)
        title = (m.group(1) if m else "").strip()
        if not title:
            probs.append("%s — title 이 비어 있음" % slug)
        elif title in 제목들:
            probs.append("%s — title 이 '%s' 와 똑같음" % (slug, 제목들[title]))
        else:
            제목들[title] = slug

        if not re.search(r'<meta name="description" content="[^"]{40,}"', h):
            probs.append("%s — description 이 없거나 너무 짧음" % slug)
        if "<footer" not in h:
            probs.append("%s — 푸터가 없음" % slug)

        # JSON-LD 가 깨지면 검색엔진이 통째로 무시한다
        for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>', h, re.S):
            try:
                json.loads(b)
            except Exception as ex:
                probs.append("%s — JSON-LD 문법 오류: %s" % (slug, ex))

        for w in FORBIDDEN:
            if w in t:
                probs.append("%s — 금지 표현 '%s'" % (slug, w))
        if "%" in t and "100%" not in t:
            # 지오테스는 절감률을 퍼센트로 말하지 않는다 (요금 페이지에 명시)
            for m2 in re.findall(r"\d+\s*%", t):
                probs.append("%s — 퍼센트 표기 '%s' (회사 방침상 쓰지 않음)" % (slug, m2))

        for 번호 in set(re.findall(r"\b1\d{3}-\d{4}\b", t)) - {TEL}:
            probs.append("%s — 상담번호를 '%s' 로 적음 (정답 %s)" % (slug, 번호, TEL))

        # 내부 링크가 실제로 있는 파일인지
        for href in set(re.findall(r'href="(/[^"#?]*)"', h)):
            대상 = os.path.join(DIST, href.strip("/").replace("/", os.sep))
            if os.path.isdir(대상) or os.path.isfile(대상) or href == "/":
                continue
            if os.path.isfile(대상 + ".html") or os.path.isfile(os.path.join(대상, "index.html")):
                continue
            probs.append("%s — 없는 주소로 링크 '%s'" % (slug, href))

    # 목록 페이지에 글이 다 올라와 있는지
    idx = os.path.join(POSTS, "index.html")
    if not os.path.isfile(idx):
        probs.append("목록 페이지(posts/index.html)가 없음")
    else:
        ih = io.open(idx, encoding="utf-8").read()
        for slug, _ in page_files():
            if '/posts/%s/' % slug not in ih:
                probs.append("목록에 '%s' 가 빠져 있음" % slug)

    return probs, 본것


def check_urls(paths):
    """실제로 열리는지 확인한다. 안 열리는 주소만 돌려준다."""
    dead = []
    for p in paths:
        url = LIVE + p
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "ziotes-verify/1.0"})
            code = urllib.request.urlopen(req, timeout=20).getcode()
            if code != 200:
                dead.append("%s (%s)" % (url, code))
        except Exception as ex:
            dead.append("%s (%s)" % (url, ex))
    return dead


def main():
    probs, 본것 = validate()
    print("검사한 글 %d쪽" % 본것)
    if not probs:
        print("문제 없음")
        return
    print("문제 %d건" % len(probs))
    for p in probs:
        print("  · " + p)
    sys.exit(1)


if __name__ == "__main__":
    main()
