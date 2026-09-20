# -*- coding: utf-8 -*-
r"""지오테스 원고 생성을 '클로드 코드'로 돌린다 — gen_ziotes.py 는 손대지 않는다. (2026-09-19)

  python gen_claude.py --dry "키워드"       만들어만 보고 저장은 안 함
  python gen_claude.py --fill 2             CRM 키워드로 2건 채움
  python daily_post_claude.py 2             발행까지 클로드로

제미나이로 되돌리려면 지금까지처럼 gen_ziotes.py / daily_post.py 를 쓰면 된다.
콜비즈(Desktop/callbiz/_tools/gen_claude.py)와 같은 방식이다. 실제 엔진은
projects-hub/shared/claude_call.py 이고, gemini_call.generate_text() 자리에 끼운다.

준비물: 클로드 코드 로그인. 만료됐으면 `claude setup-token` 으로 발급한다.
"""
import os, io, sys

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, r"C:\Users\marke\Desktop\projects-hub\shared")

import claude_call
import gen_ziotes


def use():
    """이 줄 이후 gen_ziotes 의 모든 생성이 클로드를 거친다."""
    claude_call.patch()
    # gen_ziotes 의 생성 함수는 제미나이 키가 비었는지부터 확인하고 멈춘다.
    # 클로드로 돌 때는 키가 필요 없으므로 자리만 채워 둔다.
    gen_ziotes.GEMINI_KEY = gen_ziotes.GEMINI_KEY or "claude"
    return gen_ziotes


def main():
    use()
    gen_ziotes.main()


if __name__ == "__main__":
    main()
