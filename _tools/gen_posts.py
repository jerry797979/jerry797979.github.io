# -*- coding: utf-8 -*-
"""
지오테스 정보 포스트 생성기 — 전국콜비즈 /posts/ 와 같은 서식·디자인
  python _tools/gen_posts.py
  → dist/posts/index.html + dist/posts/{slug}/index.html

콜비즈(callbiz.kr/posts/)에 매일 글을 올리듯, 지오테스도 여기에 쌓습니다.
글 서식과 화면은 가이드(gen_guide.py)와 똑같은 것을 씁니다. 그래서 그 render 를 그대로 빌려 씁니다.

새 글 올리는 법
  아래 POSTS 목록에 항목 하나를 추가하고 이 파일을 실행하면 끝입니다.
  slug 는 주소가 됩니다(영문 소문자·하이픈). cat 은 카드에 붙는 꼬리표입니다.

원칙 (가이드와 동일)
- 어려운 말을 먼저 쓰지 않습니다. 쉬운 말로 쓰고 괄호에 용어를 답니다.
- 각 글 맨 위에 답변 박스를 둡니다. AI 검색이 그 문단을 인용해 갑니다.
- 남의 글을 옮기지 않습니다. 구조만 참고하고 문장은 새로 씁니다.
"""
import os, sys, html

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_solution import SITE, OG_BASE, TEL, TEL_RAW
from gen_guide import render, write, e

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
OUT = os.path.join(ROOT, "dist", "posts")

BASE = "posts"        # 주소: /posts/
BASE_NAME = "정보"     # 빵부스러기·메뉴에 쓰는 이름

# ---------------------------------------------------------------- 원고

POSTS = [
{
 "slug": "call-center-outsourcing-vs-inhouse",
 "cat": "콜센터 운영",
 "title": "콜센터, 직접 운영과 아웃소싱 중 무엇이 나은가",
 "desc": "전화 응대를 직접 할지 맡길지 고민하는 분들을 위해 두 방식의 비용 구조와 갈리는 지점을 정리했습니다. 통화량과 문의 내용에 따라 답이 달라집니다.",
 "h1": "직접 운영과 아웃소싱,<br>무엇이 나은가",
 "sub": "인원을 뽑을지 맡길지는 통화량만으로 정하지 않습니다.<br>무엇을 묻는 전화인지가 더 중요합니다.",
 "answer_q": "콜센터를 직접 운영하는 것과 맡기는 것 중 어느 쪽이 나은가요?",
 "answer": "정해진 답은 없고 <span class='hl'>문의 내용이 무엇인지에 따라 갈립니다.</span> "
   "답이 정해져 있고 반복되는 문의(영업시간, 배송 조회, 예약 변경)가 대부분이라면 "
   "<b>맡기거나 자동 응대로 넘기는 쪽</b>이 낫습니다. "
   "반대로 우리 제품을 알아야 답할 수 있고 그 통화가 매출로 이어진다면 "
   "<b>직접 받는 쪽</b>이 낫습니다. 사람을 쓰는 비용보다 "
   "<b>답을 아는 사람이 받았는지</b>가 결과를 더 크게 바꿉니다.",
 "body": [
  ("먼저 나눠야 할 것은 전화의 종류입니다", [
    ("p", "직접 할지 맡길지부터 정하려 하면 답이 잘 안 나옵니다. "
          "걸려오는 전화를 두 갈래로 나눠 보는 편이 빠릅니다."),
    ("table", [
      ["갈래", "어떤 전화인지", "적합한 방식"],
      ["답이 정해진 전화", "영업시간, 위치, 배송 조회, 예약 변경처럼 누가 받아도 답이 같은 것", "자동 응대(ARS·AI) 또는 아웃소싱"],
      ["판단이 필요한 전화", "제품 상담, 견적, 불만 처리처럼 우리 사정을 알아야 답할 수 있는 것", "직접 응대"],
    ]),
    ("p", "대부분의 회사는 이 둘이 섞여 있습니다. "
          "그래서 실제로는 <strong>전부 직접 하거나 전부 맡기는 것이 아니라, 갈라서 처리</strong>하게 됩니다."),
    ("callout", "한 달치 통화 기록을 뽑아 이 두 갈래로 나눠 보시면 방향이 거의 정해집니다. "
                "답이 정해진 전화가 7할을 넘으면 사람을 더 뽑는 것보다 앞단을 자동화하는 쪽이 먼저입니다."),
  ]),
  ("직접 운영할 때 실제로 드는 것", [
    ("p", "직접 운영은 인건비만 드는 것이 아닙니다. 자주 빠뜨리는 항목이 있습니다."),
    ("list", [
      "<strong>사람</strong> — 급여와 4대보험, 그리고 뽑고 가르치는 시간",
      "<strong>자리</strong> — 책상, 컴퓨터, 헤드셋, 사무공간",
      "<strong>시스템</strong> — 전화를 나눠주는 장비, 상담 화면, 녹취",
      "<strong>빈자리</strong> — 사람이 그만두면 그 자리를 채울 때까지 통화가 밀립니다",
    ]),
    ("p", "이 중에서 계산에서 자주 빠지는 것이 <strong>마지막 항목</strong>입니다. "
          "상담 인원이 서너 명인 곳은 한 사람이 그만두면 처리량이 눈에 띄게 떨어집니다. "
          "인원이 적을수록 이 위험이 큽니다."),
  ]),
  ("맡길 때 확인해야 할 것", [
    ("p", "아웃소싱은 사람을 뽑는 부담이 없고 통화량이 늘어도 바로 받쳐줍니다. "
          "다만 계약 전에 확인하지 않으면 나중에 곤란해지는 부분이 있습니다."),
    ("h3", "1. 통화 기록이 우리 것으로 남는가"),
    ("p", "맡긴 회사의 시스템에만 기록이 쌓이면, 계약을 끝낼 때 <strong>고객 응대 이력이 통째로 사라집니다.</strong> "
          "녹취와 상담 이력을 우리 쪽에도 남길 수 있는지를 먼저 확인하셔야 합니다."),
    ("h3", "2. 답변 기준을 누가 만드는가"),
    ("p", "상담사가 우리 제품을 우리만큼 알기는 어렵습니다. "
          "그래서 <strong>어디까지 답하고 어디서부터 넘길지</strong>를 문서로 정해 두어야 합니다. "
          "이 문서가 없으면 잘못된 안내가 나가고, 그 책임 소재도 애매해집니다."),
    ("h3", "3. 번호는 누구 것인가"),
    ("p", "대표번호를 맡긴 회사 명의로 열면 나중에 옮길 때 번호를 못 가져올 수 있습니다. "
          "<strong>번호는 우리 명의로 두는 편</strong>이 안전합니다."),
  ]),
  ("많이 쓰는 절충안", [
    ("p", "실제로 가장 많이 자리 잡는 형태는 셋 중 하나가 아니라 이 조합입니다."),
    ("list", [
      "답이 정해진 문의는 <strong>자동 응대에서 끝냅니다</strong> — 사람에게 오는 전화 자체를 줄입니다.",
      "그래도 사람이 필요한 전화는 <strong>내부 담당자에게 넘깁니다</strong> — 인원을 크게 늘리지 않아도 됩니다.",
      "통화가 몰리는 시간대나 야간·휴일만 <strong>외부에 맡깁니다</strong>.",
    ]),
    ("p", "이렇게 하면 사람은 그대로 두고 처리량만 올릴 수 있습니다. "
          "어느 문의부터 자동으로 넘길지는 통계를 봐야 정할 수 있어서, "
          "<strong>무엇이 몇 통 왔는지 세는 것</strong>이 사실상 첫 단계가 됩니다."),
  ]),
  ("무엇부터 하면 되나요", [
    ("p", "지금 통화가 몇 통이고 무엇을 묻는 전화인지 모르는 상태라면, 그것부터 보이게 만드는 것이 먼저입니다. "
          "시스템을 새로 깔지 않아도 대표번호와 통계만으로 한 달이면 그림이 나옵니다."),
    ("p", "지오테스는 회선부터 교환기, 상담 화면, 녹취, AI 응대까지 직접 만들어 공급합니다. "
          "지금 상태를 보고 <strong>필요한 것만 골라</strong> 구성해 드립니다. 상담은 무료입니다."),
  ]),
 ],
 "faq": [
  ("상담 인원이 두세 명인데 시스템이 필요할까요?",
   "인원보다 통화가 몰리는지, 기록을 남겨야 하는지가 기준입니다. 두세 명이어도 놓치는 전화가 있거나 통화 내용을 확인할 일이 생긴다면 필요합니다."),
  ("아웃소싱하면 우리 제품을 잘 모르지 않나요?",
   "그래서 답이 정해진 문의부터 맡기는 것이 일반적입니다. 판단이 필요한 통화는 내부 담당자에게 넘기도록 기준을 정해 둡니다."),
  ("자동 응대를 넣으면 고객이 불편해하지 않나요?",
   "기다리는 쪽이 더 불편합니다. 답이 정해진 문의를 앞에서 걸러내면 사람과 통화해야 하는 고객의 대기 시간이 줄어듭니다."),
  ("지금 쓰는 번호를 그대로 둘 수 있나요?",
   "번호 이전으로 유지할 수 있습니다. 명함과 안내문을 다시 만들지 않아도 됩니다. 절차는 저희가 진행합니다."),
 ],
},
]


# ---------------------------------------------------------------- 목록 페이지

def render_index():
    cards = "".join(
      f'<a href="/{BASE}/{p["slug"]}/" class="post-card">'
      f'<span class="tag">{e(p["cat"])}</span>'
      f'<h3>{e(p["title"])}</h3><p>{e(p["desc"])}</p></a>' for p in POSTS)
    desc = "콜센터 구축과 운영, 기업 전화에 필요한 정보를 정리합니다. 상담 1555-5528."
    return f'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>정보 · 콜센터와 기업통신 가이드 | 지오테스</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{SITE}/{BASE}/">
<meta property="og:type" content="website">
<meta property="og:title" content="정보 · 콜센터와 기업통신 가이드 | 지오테스">
<meta property="og:description" content="{desc}">
<meta property="og:locale" content="ko_KR">
<meta property="og:site_name" content="지오테스">
<meta property="og:image" content="{OG_BASE}/assets/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Poppins:wght@600;700;800&display=swap">
<link rel="stylesheet" href="/assets/nova-post.css">
</head>
<body>
<header class="site">
  <div class="wrap">
    <a href="/" class="logo logo-img"><img src="/assets/logo.png" alt="지오테스 Ziotes"></a>
    <a href="tel:{TEL_RAW}" class="nav-call">{TEL}</a>
  </div>
</header>
<section class="post-hero">
  <div class="wrap">
    <p class="crumb"><a href="/">홈</a> · {BASE_NAME}</p>
    <span class="eyebrow">Guide</span>
    <h1>콜센터와 기업통신 가이드</h1>
    <p class="meta">회선·교환기·상담화면·녹취·AI까지, 콜센터를 알아볼 때 필요한 것들을 쉬운 말로 정리합니다.</p>
  </div>
</section>
<main class="wrap">
  <div class="post-list">{cards}</div>
</main>
<footer>
  <div class="wrap">
    <div class="flogo">지오<b>테스</b></div>
    <p>㈜지오테스솔루션 · 대표이사 신명남 · 사업자등록번호 144-81-03835 · 고객센터 {TEL}<br>
    © 2006 ZioTEs Solution Inc. All Rights Reserved.</p>
  </div>
</footer>
</body>
</html>'''


def main():
    print("정보 포스트 생성")
    write(os.path.join(OUT, "index.html"), render_index(), 1)
    for p in POSTS:
        write(os.path.join(OUT, p["slug"], "index.html"),
              render(p, base=BASE, base_name=BASE_NAME), 2)
    print(f"\n총 {len(POSTS) + 1}개 생성 완료")


if __name__ == "__main__":
    main()
