# -*- coding: utf-8 -*-
"""지오테스 매일 자동발행을 '클로드 코드'로 돌린다 — daily_post.py 는 손대지 않는다. (2026-09-19)
  python daily_post_claude.py 2      제미나이 대신 클로드로 2건 발행
  python daily_post.py 2             지금까지처럼 제미나이로 발행

발행 절차(대기열 → 검증 → HTML → 커밋 → 거래처 서버 전송 → CRM 보고 → 텔레그램)는
daily_post.py 것을 그대로 쓴다. 원고를 만드는 한 걸음만 클로드가 맡는다.
runpy 로 daily_post.py 를 __main__ 으로 실행해야 파일 맨 아래의 예외 처리
(치명적 오류도 텔레그램으로 알리고 죽는다)까지 그대로 탄다. 콜비즈와 같은 방식.
"""
import os, sys, runpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import gen_claude
gen_claude.use()        # 공용 gemini_call.generate_text 자리에 클로드를 끼운다.

runpy.run_path(os.path.join(HERE, "daily_post.py"), run_name="__main__")
