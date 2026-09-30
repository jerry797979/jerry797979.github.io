# -*- coding: utf-8 -*-
"""지오테스 한 번에 여러 편 — daily_post_claude.py 를 10편씩 차례로 부른다(덩이 사이 2분).

  python _tools/bulk50.py 50

2026-09-30 사용자: "지오테스도 올려줘 50개". 끝나면 새 글 주소를 _tools/bulk50_주소_<날짜>.txt 와 텔레그램으로.
"""
import os, sys, time, datetime, subprocess, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import daily_post as dp

total = int(sys.argv[1]) if len(sys.argv) > 1 else 50
CHUNK = 10
before = set(dp.load_pub())
env = dict(os.environ, PYTHONIOENCODING="utf-8", PATH=r"C:\Program Files\Git\cmd;C:\Program Files\nodejs;" + os.environ["PATH"])
dp.log("==== bulk50 시작 %d편 ====" % total)
done = 0
while done < total:
    n = min(CHUNK, total - done)
    t0 = time.time()
    prev = len(set(dp.load_pub()) - before)
    r = subprocess.run([sys.executable, os.path.join(HERE, "daily_post_claude.py"), str(n)], cwd=ROOT, env=env)
    got = len(set(dp.load_pub()) - before) - prev
    dp.log("bulk50 덩이 %d편 요청 → %d편, rc=%s, %d초" % (n, got, r.returncode, time.time() - t0))
    done += n
    if got <= 0:
        dp.log("bulk50 이번 덩이에서 한 편도 안 나와 멈춤")
        break
    if done < total:
        time.sleep(120)

new = sorted(set(dp.load_pub()) - before)
urls = ["https://ziotes.com/posts/%s/" % s for s in new]
ok = []
for u in urls:
    try:
        if urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "ziotes-check"}), timeout=20).status == 200:
            ok.append(u)
    except Exception:
        pass
out = os.path.join(HERE, "bulk50_주소_%s.txt" % datetime.date.today().isoformat())
open(out, "w", encoding="utf-8").write("지오테스 새 글 %d편, 열림 %d편\n" % (len(urls), len(ok)) + "\n".join(urls) + "\n")
dp.notify("<b>[지오테스] 대량 발행 끝</b> 새 글 %d편 · 열림 %d편\n%s\n전체: %s" % (len(urls), len(ok), "\n".join(ok[:5]), out))
dp.log("==== bulk50 끝 %d편 ====" % len(urls))
