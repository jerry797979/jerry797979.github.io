# -*- coding: utf-8 -*-
"""정해 준 키워드 목록으로 지오테스 글을 한 편씩 발행한다 — CRM 대기열 대신 파일에서 키워드를 꺼낸다.

  python _tools/bulk_keywords.py _tools/키워드_콜센터구축_2026-10-02.txt

2026-10-02 사용자: 콜센터 구축 키워드 50개를 키워드마다 한 편씩. 원고는 클로드(gen_claude),
발행 절차는 daily_post.py 그대로. 10편씩 끊고 덩이 사이 2분 쉰다. 이미 쓴 키워드는 건너뛰어 다시 돌려도 된다.
"""
import os, sys, io, json, glob, time, runpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen_claude
gen_ziotes = gen_claude.use()

목록 = [l.strip() for l in io.open(sys.argv[1], encoding="utf-8") if l.strip()]
CHUNK = 10


def 쓴키워드():
    out = set()
    for f in glob.glob(os.path.join(HERE, "generated", "*.json")):
        try:
            out.add(json.load(io.open(f, encoding="utf-8")).get("kw"))
        except Exception:
            pass
    return out


def 파일키워드(need, exclude=()):
    쓴것 = 쓴키워드()
    return [(None, kw) for kw in 목록 if kw not in 쓴것 and kw not in exclude][:need]


gen_ziotes.crm_keywords = 파일키워드
gen_ziotes.reuse_keywords = lambda need: []     # 목록 밖 키워드로 메우지 않는다

while True:
    남은 = [kw for kw in 목록 if kw not in 쓴키워드()]
    print("==== 남은 키워드 %d개 ====" % len(남은), flush=True)
    if not 남은:
        break
    전 = len(남은)
    sys.argv = ["daily_post.py", str(min(CHUNK, 전))]
    try:
        runpy.run_path(os.path.join(HERE, "daily_post.py"), run_name="__main__")
    except SystemExit:
        pass
    if len([kw for kw in 목록 if kw not in 쓴키워드()]) >= 전:
        print("이번 덩이에서 한 편도 못 만들어 멈춤", flush=True)
        break
    time.sleep(120)
