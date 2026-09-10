# -*- coding: utf-8 -*-
"""
정보 글을 ziotes.com 에 올립니다 —  python _tools/push_post.py {slug}

  python _tools/push_post.py call-center-outsourcing-vs-inhouse
  python _tools/push_post.py --all          이미 만들어진 글 전부
  python _tools/push_post.py --assets       스타일·스크립트만 보내기
  python _tools/push_post.py --list         서버에 올라와 있는 글 확인

무엇을 하는가
  gen_posts.py 가 만들어 둔 dist/posts/{slug}/index.html 과 목록·사이트맵을
  ziotes.com/_post.php 로 보냅니다. 거래처 서버라 우리가 git pull 을 눌러 줄 수
  없어서, 만든 페이지를 그대로 실어 보내는 것입니다.

열쇠
  환경변수 ZIOTES_POST_KEY 에 넣거나, _tools/.post_key 파일에 한 줄로 적어 둡니다.
  .post_key 는 저장소에 올라가지 않습니다(.gitignore).

순서
  1) python _tools/gen_posts.py     페이지를 만들고
  2) python _tools/push_post.py …   서버에 보냅니다
  3) git commit && git push         저장소에도 남깁니다 (같은 내용이라 충돌하지 않습니다)
"""
import io
import json
import os
import sys
import urllib.error
import urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
DIST = os.path.join(ROOT, "dist")
API = os.environ.get("ZIOTES_POST_API", "https://ziotes.com/_post.php")


def 열쇠() -> str:
    v = os.environ.get("ZIOTES_POST_KEY", "").strip()
    if v:
        return v
    p = os.path.join(ROOT, "_tools", ".post_key")
    if os.path.isfile(p):
        return io.open(p, encoding="utf-8").read().strip()
    sys.exit("열쇠가 없습니다. ZIOTES_POST_KEY 환경변수를 넣거나 _tools/.post_key 에 적어 주세요.")


def 읽기(*parts) -> str:
    """
    파일을 읽어 온다.

    newline 을 지정하지 않는 것이 중요합니다. 이렇게 읽으면 윈도우의 CRLF 가
    LF 로 바뀌어 들어오고, 그 상태로 보내면 서버에는 LF 로 쓰입니다.
    리눅스 서버의 git 체크아웃도 LF 라서, 우리가 보낸 파일과 저장소 내용이
    바이트까지 같아집니다. 그래서 나중에 git pull 을 해도 충돌이 나지 않습니다.

    여기에 newline="" 을 넣으면 CRLF 가 그대로 나가고, 서버에서 git 이
    "누가 파일을 고쳤다"고 보게 되어 pull 이 막힙니다.
    """
    p = os.path.join(DIST, *parts)
    if not os.path.isfile(p):
        sys.exit("파일이 없습니다: " + p + "\n먼저 python _tools/gen_posts.py 를 실행하세요.")
    return io.open(p, encoding="utf-8").read()


def 부르기(method: str, body=None):
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
    req = urllib.request.Request(API, data=data, method=method, headers={
        "X-Post-Key": 열쇠(),
        "Content-Type": "application/json; charset=utf-8",
        # 기본 파이썬 UA 는 막는 서버가 있어 이름을 붙여 둡니다
        "User-Agent": "ziotes-push-post/1.0",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        본문 = e.read().decode("utf-8", "replace")
        try:
            return json.loads(본문)
        except ValueError:
            return {"ok": False, "message": "HTTP %d — %s" % (e.code, 본문[:300])}
    except urllib.error.URLError as e:
        return {"ok": False, "message": "서버에 닿지 못했습니다 — %s" % e.reason}


# 글 모양이 바뀌면 스타일·스크립트가 같이 가야 합니다.
# 서버는 '이미 있는 파일을 같은 이름으로 바꾸는 것'만 받습니다.
ASSETS = ["assets/nova.css", "assets/nova-post.css",
          "assets/site.js", "assets/lead.js"]


def 스타일보내기() -> bool:
    몸통 = {"assets": {p: 읽기(*p.split("/")) for p in ASSETS}}
    답 = 부르기("POST", 몸통)
    if 답.get("ok"):
        print("올림  스타일·스크립트 %d개" % len(답.get("written", [])))
        for p in 답.get("written", []):
            print("      " + p)
        if 답.get("failed"):
            print("      못 쓴 것:", ", ".join(답["failed"]))
        return True
    print("실패  " + 답.get("message", "알 수 없는 오류"))
    return False


def 보내기(slug: str) -> bool:
    몸통 = {
        "slug": slug,
        "html": 읽기("posts", slug, "index.html"),
        "index": 읽기("posts", "index.html"),
    }
    사이트맵 = os.path.join(DIST, "sitemap.xml")
    if os.path.isfile(사이트맵):
        몸통["sitemap"] = io.open(사이트맵, encoding="utf-8").read()

    답 = 부르기("POST", 몸통)
    if 답.get("ok"):
        print("올림  %-45s https://ziotes.com/posts/%s/" % (slug, slug))
        if 답.get("failed"):
            print("      다만 못 쓴 파일:", ", ".join(답["failed"]))
        return True
    print("실패  %-45s %s" % (slug, 답.get("message", "알 수 없는 오류")))
    return False


def 목록():
    답 = 부르기("GET")
    if not 답.get("ok"):
        sys.exit("실패 — " + 답.get("message", ""))
    print("서버에 올라와 있는 글 %d개" % 답.get("count", 0))
    for it in 답.get("posts", []):
        print("  %-45s %7d바이트  %s" % (it["slug"], it["bytes"], it["at"]))


def main():
    인자 = sys.argv[1:]
    if not 인자:
        sys.exit(__doc__.strip())

    if 인자[0] == "--list":
        return 목록()

    if 인자[0] == "--assets":
        sys.exit(0 if 스타일보내기() else 1)

    if 인자[0] == "--all":
        d = os.path.join(DIST, "posts")
        slugs = sorted(n for n in os.listdir(d)
                       if os.path.isfile(os.path.join(d, n, "index.html")))
    else:
        slugs = 인자

    실패 = [s for s in slugs if not 보내기(s)]
    print("\n%d개 중 %d개 올렸습니다." % (len(slugs), len(slugs) - len(실패)))
    if 실패:
        sys.exit(1)


if __name__ == "__main__":
    main()
