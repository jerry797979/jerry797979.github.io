# -*- coding: utf-8 -*-
"""
지오테스 자동 원고 생성 — CRM 키워드 → Gemini → 검증 → 대기열(generated/*.json)

  python _tools/gen_ziotes.py "콜센터 구축 비용"     한 건 생성해서 대기열에 저장
  python _tools/gen_ziotes.py --dry "키워드"          생성만 하고 저장 안 함(검사만)
  python _tools/gen_ziotes.py --fill 2                CRM에서 2건 뽑아 생성

daily_post.py 는 대기열이 하루 발행량보다 적으면 autofill() 을 부릅니다.

이 파일의 핵심은 생성이 아니라 **검증**입니다.
지오테스는 "절감률을 몇 퍼센트라고 말하지 않는다"를 요금 페이지에 직접 써 둔 회사입니다.
그런데 AI 는 그럴듯한 숫자를 잘 지어냅니다. 그래서 본문에 나온 모든 숫자를
확정 목록과 대조해 하나라도 벗어나면 저장하지 않고 다시 생성합니다.
"""
import os
import re
import io
import sys
import json
import time

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DIST = os.path.join(ROOT, "dist")
OUT = os.path.join(HERE, "generated")
sys.path.insert(0, HERE)
# 제미나이 호출·검증기는 공용 모듈을 씁니다(콜비즈에서 뽑아 공용화한 것).
sys.path.insert(0, r"C:\Users\marke\Desktop\projects-hub\shared")
import gemini_call
import content_validator as cv

_cfg = {}
try:
    _cfg = json.load(open(os.path.join(HERE, "gen_config.json"), encoding="utf-8"))
except Exception:
    pass

GEMINI_KEY = gemini_call.load_key(_cfg.get("gemini_key") or None)
MODEL = _cfg.get("model", "gemini-flash-latest")
AUTOPICK_LIKE = _cfg.get("autopick_like", "")
TRIES = int(_cfg.get("tries", 4))

TEL = "1555-5528"
SALES_TEL = "070-4509-0770"
TECH_TEL = "070-4509-0766"

# ── 확정 사실 ────────────────────────────────────────
# 여기 없는 숫자는 본문에 나오면 안 됩니다. 프롬프트와 검증이 이 값을 같이 씁니다.
# 출처는 사이트의 회사소개·요금 페이지입니다. 사이트를 고치면 여기도 같이 고쳐야 합니다.
FACTS = """[회사]
- 지오테스, ㈜지오테스솔루션 운영, 대표이사 신명남
- 2006년부터 컨택센터 구축과 인터넷전화 한 분야만 해 왔음
- 지금까지 120여 곳 구축 (제조·유통·금융·공공·병원·쇼핑몰·교육)
- 고객센터 1555-5528 (상담 무료) · 영업 070-4509-0770 · 기술 070-4509-0766
- 평일 09:00~18:00

[직접 만드는 것 — 이게 이 회사의 성격이다]
- IP 교환기(IP-PBX)와 상담 애플리케이션을 직접 개발한다
- 인터넷전화 회선까지 직접 공급한다
- 회선을 공급하면서 교환기와 상담 프로그램까지 직접 만드는 곳은 많지 않다
- KT·LG유플러스·SK브로드밴드 3사와 모두 제휴 (한 곳에 묶지 않고 조건이 맞는 쪽을 고름)

[거래 조건]
- 약정 기간이 없다. 위약금이 없다.
- 365일 24시간 이중화. 장애가 나면 백업 서버로 자동 전환.
- 회선도 통신사 두 곳 이상에 열어 두면 한쪽에 장애가 나도 통화가 이어진다.

[구축에 포함되는 것 — 따로 사지 않는다]
- 상담 CRM, 통화 녹취, 통계, 실시간 현황판, 스크린 팝업
- 쓰던 CRM이 있으면 그대로 두고 전화 기능만 붙이는 방식도 된다

[추가 비용 없이 함께 주는 12가지]
- 영업 자동화: 오토콜, 클릭투콜, 스케줄 발신
- 브랜드 구분: 착신번호별 구분, 브랜드별 발신번호
- 상담 품질: 필수 안내 자동 재생, 욕설 방지 안내, 통화 종료 추적
- 고객 관리: 블랙리스트, 통화 후 자동 문자·알림톡, 부재중 자동 알림, 부분 녹취

[선택 항목 — 필요할 때 추가]
- AI 통화요약, 콜백 API 연동, DB API 연동, 실시간 API 연동
- AI 응대, 보이는 ARS

[요금 — ★금액은 절대 쓰지 않는다]
- 비용은 네 항목: 시스템 구축(1회), 회선 이용료(월), 유지보수(별도 계약), 부가서비스(선택)
- 좌석을 늘리면 좌석당 비용만 추가된다
- 회선 이용료와 통화료는 별도
- ★원·만원 같은 금액을 한 글자도 쓰지 않는다. 표에도, FAQ 에도 쓰지 않는다.
  비용을 물으면 "상담 인원·회선 수·필요한 기능에 따라 달라서, 지금 쓰시는 구성을 보고
  산정해 드린다"고 쓴다. 금액이 궁금하면 1555-5528 로 상담하라고 안내한다.
- ★절감률을 몇 퍼센트라고 말하지 않는다. 지금 무엇을 쓰는지에 따라 완전히 달라지기 때문.
  퍼센트를 쓰지 말고, "항목별로 무엇이 없어지고 무엇이 남는지 계산해 알려준다"고 쓴다.

[연혁]
- 2006 법인 설립, KT와 인터넷전화 계약
- 2008 자체 녹취 시스템 개발 (남의 제품을 파는 데서 직접 만드는 쪽으로)
- 2013 필리핀 클락에 콜센터 직접 설립 (쓰는 쪽에서 겪어 본 경험)
- 2026 AI 컨택센터 제공 시작
"""

# ── 숫자 화이트리스트 ────────────────────────────────
# 본문에서 "숫자+단위"를 전부 뽑아 이 표와 대조합니다. 벗어나면 재생성합니다.
# 빈 집합은 "그 단위로는 확정된 숫자가 하나도 없다" = 그 단위를 쓰면 무조건 반려.
ALLOWED = {
    # ★금액은 아예 금지. CRM 지오테스 규칙: "요금·할인율은 쓰지 말 것".
    # 2026-09-11: 요금 페이지 금액(300,000원/100,000원)을 허용했다가 7편에 금액이 나갔다.
    "원":     set(),
    "만원":   set(),
    "%":      set(),                  # ★퍼센트는 아예 금지 — 회사 방침
    "년":     {"2006", "2007", "2008", "2009", "2011", "2013", "2015",
               "2016", "2018", "2019", "2022", "2026", "3", "20"},
    "시간":   {"24"},                 # 365일 24시간
    "개월":   set(),
    "영업일": set(),
    "분":     set(),
    "명":     set(),                  # 인원 주장은 확정된 게 없다
    "건":     set(),
}

# 검사할 단위를 좁힌 정규식.
# 공용 UNIT_RE 에는 개·주·단계·점·위·배까지 들어 있는데, 그건 "항목 2개", "3단계로"
# 같은 평범한 셈까지 반려시킨다. 사실 주장을 담는 단위만 본다.
UNIT_RE = re.compile(r"(\d[\d,]*(?:\.\d+)?)\s*(만원|원|%|개월|영업일|년|시간|명|건)")

# 발행을 막는 표현
FORBIDDEN = ["업계 최저가", "무조건 승인", "100% 보장", "국내 유일", "절대 해지 안",
             "최저가", "무조건", "100%", "업계 1위", "국내 최대"]

# 형제 사이트 — 전국콜비즈(callbiz.kr)는 대표번호 개통 쪽이라 여기서 언급하면 안 됩니다.
SIBLING = ["전국콜비즈", "callbiz"]

# 경쟁사 이름 — 본문에 나오면 반려합니다.
# ※ 비어 있습니다. 이 시장의 경쟁사 이름을 지어내면 안 되므로 채우지 않았습니다.
#    막아야 할 상호가 있으면 여기에 적어 주세요. 적는 즉시 검증에 반영됩니다.
COMPETITORS = []

# 지오테스가 쓰는 꼬리표(cat) — 카드에 붙습니다. 여기 없는 값이 나오면 반려합니다.
CATS = ["콜센터 구축", "콜센터 운영", "고객관리 CRM", "통화 녹취",
        "ARS·IVR", "AI 컨택센터", "기업 인터넷전화", "비용"]


def _text(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s or "")).strip()


def flat(d):
    """검사 대상 전체 텍스트(HTML 포함)"""
    parts = [d.get("title", ""), d.get("desc", ""), d.get("h1", ""),
             d.get("sub", ""), d.get("answer_q", ""), d.get("answer", "")]
    for sec in d.get("body", []):
        parts.append(sec.get("h", ""))
        for b in sec.get("blocks", []):
            v = b.get("v")
            if isinstance(v, str):
                parts.append(v)
            elif isinstance(v, list):
                for row in v:
                    parts += [str(c) for c in row] if isinstance(row, list) else [str(row)]
    for f in d.get("faq", []):
        parts += [f.get("q", ""), f.get("a", "")]
    return "\n".join(parts)


def known_links():
    """dist 안에 실제로 있는 내부 경로 — 없는 주소로 링크하면 404가 됩니다."""
    out = {"/", "/posts/", "/guide/", "/glossary/", "/pricing/", "/cases/",
           "/about/", "/contact/", "/demo/", "/use-cases/", "/industries/",
           "/solution/"}
    for sub in ("posts", "guide", "solution", "use-cases", "industries"):
        d = os.path.join(DIST, sub)
        if not os.path.isdir(d):
            continue
        for name in os.listdir(d):
            if os.path.isdir(os.path.join(d, name)):
                out.add("/%s/%s/" % (sub, name))
    return out


def taken_slugs():
    """이미 쓰였거나 대기 중인 슬러그"""
    used = set()
    try:
        from backlog import BACKLOG
        used |= {p["slug"] for p in BACKLOG}
    except Exception:
        pass
    try:
        import gen_posts
        used |= {p["slug"] for p in gen_posts.POSTS}
    except Exception:
        pass
    d = os.path.join(DIST, "posts")
    if os.path.isdir(d):
        used |= set(os.listdir(d))
    return used


# ── 검증 ─────────────────────────────────────────────
BLOCK_KINDS = {"p", "h3", "callout", "list", "table"}


def check(d, keyword, avoid_titles=(), keep_slug=None):
    """통과하면 [] 를, 문제가 있으면 사유 목록을 돌려줍니다."""
    bad = []
    body = flat(d)
    plain = _text(body)

    # 구조
    if not re.match(r"^[a-z0-9][a-z0-9-]{2,39}$", d.get("slug", "")):
        bad.append("slug 형식이 잘못됨(영소문자·숫자·하이픈 3~40자)")
    elif d["slug"] in taken_slugs() and d["slug"] != keep_slug:
        bad.append("slug '%s' 는 이미 쓰고 있음 — 다른 슬러그로" % d["slug"])

    if d.get("cat") not in CATS:
        bad.append("cat 은 다음 중 하나여야 함: %s" % " / ".join(CATS))

    bad += cv.check_field_len(d, "title", 15, 60)
    bad += cv.check_field_len(d, "desc", 80, 230)
    bad += cv.check_count_range(d.get("body", []), 5, 6, "body 소제목")
    bad += cv.check_count_range(d.get("faq", []), 5, 6, "faq")
    bad += cv.check_length(plain, 2000)

    for sec in d.get("body", []):
        blocks = sec.get("blocks", [])
        if not any(b.get("k") == "p" for b in blocks):
            bad.append("소제목 '%s' 에 p 문단이 없음" % (sec.get("h") or "")[:20])
        for b in blocks:
            k = b.get("k")
            if k not in BLOCK_KINDS:
                bad.append("쓸 수 없는 블록 종류 '%s' — %s 만 됨" % (k, "·".join(sorted(BLOCK_KINDS))))
            elif k == "list" and not isinstance(b.get("v"), list):
                bad.append("list 블록의 v 는 문자열 배열이어야 함")
            elif k == "table":
                v = b.get("v")
                if not isinstance(v, list) or len(v) < 2 or not all(isinstance(r, list) for r in v):
                    bad.append("table 블록의 v 는 [머리줄, 줄, 줄] 형태의 2차원 배열이어야 함")
                elif len({len(r) for r in v}) != 1:
                    bad.append("table 의 칸 수가 줄마다 다름")

    # h1·sub 는 화면에서 두 줄로 나옵니다. 태그는 <br> 만 허용합니다.
    for 칸 in ("h1", "sub"):
        v = d.get(칸, "")
        for tag in set(re.findall(r"</?([a-zA-Z]+)", v)):
            if tag.lower() != "br":
                bad.append("%s 에는 <br> 말고 다른 태그를 쓸 수 없음 (<%s> 발견)" % (칸, tag))

    # 제목 겹침 — 각도만 바꾸고 제목을 베끼면 같은 글이 두 번 나가는 셈입니다.
    if avoid_titles:
        같은것 = similar_title(d.get("title", ""), avoid_titles)
        if 같은것:
            bad.append("제목이 이미 있는 글과 너무 닮음 ('%s') — 각도를 살려 다르게" % 같은것[:30])

    # 키워드
    if keyword.replace(" ", "") not in d.get("title", "").replace(" ", ""):
        bad.append("title 에 키워드 '%s' 가 들어가야 함" % keyword)
    bad += cv.check_keyword_count(plain, keyword, 3)

    # 숫자 화이트리스트 — 지어낸 요금·절감률을 막는 장치
    bad += cv.check_number_whitelist(plain, ALLOWED, unit_re=UNIT_RE)

    # 금지 표현
    bad += cv.check_forbidden(body, FORBIDDEN)
    bad += cv.check_forbidden(body, SIBLING, label="형제 사이트 이름(대표번호 쪽)")
    if COMPETITORS:
        bad += cv.check_forbidden(body, COMPETITORS, label="경쟁사 이름")
    if "<script" in body.lower():
        bad.append("script 태그 금지")

    # 링크
    ok_links = known_links()
    for href in re.findall(r'href=[\'"]([^\'"]+)[\'"]', body):
        if href.startswith("tel:"):
            if re.sub(r"\D", "", href) != TEL.replace("-", ""):
                bad.append("tel 링크가 %s 가 아님" % TEL)
        elif not href.startswith("/"):
            bad.append("외부 링크 '%s' 금지 — 내부 경로만" % href[:40])
        elif href not in ok_links:
            bad.append("없는 주소로 링크함 '%s'" % href)

    # 전화번호 — 사이트에 있는 세 개 말고 다른 번호를 적으면 반려
    맞는번호 = {TEL, SALES_TEL, TECH_TEL}
    for 번호 in set(re.findall(r"\b(0\d{1,2}-\d{3,4}-\d{4}|1\d{3}-\d{4})\b", plain)) - 맞는번호:
        bad.append("사이트에 없는 전화번호 '%s' 를 씀 (쓸 수 있는 번호: %s)"
                   % (번호, ", ".join(sorted(맞는번호))))

    return bad


# ── 각도 ─────────────────────────────────────────────
# 키워드가 바닥나도 발행을 멈추지 않습니다. 이미 쓴 키워드를 다시 꺼내되
# 각도를 바꿔 완전히 다른 글을 쓰게 합니다.
ANGLES = [
    ("고르는법", "여러 선택지를 놓고 무엇을 기준으로 고를지 판단표를 주는 글. "
                 "비교 항목을 세워 놓고 어떤 경우에 어느 쪽이 맞는지 갈라 준다."),
    ("실수",     "이미 쓰는 곳들이 흔히 저지르는 실수와 그 대가를 짚는 글. "
                 "실패 장면을 먼저 보여 주고 피하는 방법으로 넘어간다."),
    ("비용",     "돈 이야기만으로 끌고 가는 글. 눈에 보이는 값과 숨은 값을 나눠 "
                 "3년 총액으로 따지는 법을 알려 준다. 금액과 퍼센트는 쓰지 않는다."),
    ("업종별",   "업종에 따라 답이 어떻게 갈리는지 보여 주는 글. "
                 "병원·학원·쇼핑몰·제조처럼 구체적인 현장을 놓고 설명한다."),
    ("절차",     "처음부터 끝까지 순서대로 밟아 주는 글. "
                 "각 단계에서 무엇을 준비하고 무엇을 확인해야 하는지 짚는다."),
    ("문제해결", "이미 쓰고 있는데 뭔가 안 될 때 원인을 찾아가는 글. "
                 "증상에서 출발해 원인과 조치로 내려간다."),
]


def _norm_title(t):
    return re.sub(r"[^0-9a-z가-힣]", "", (t or "").lower())


def similar_title(title, others, limit=0.65):
    import difflib
    a = _norm_title(title)
    if not a:
        return None
    for o in others:
        b = _norm_title(o)
        if b and difflib.SequenceMatcher(None, a, b).ratio() >= limit:
            return o
    return None


def existing_posts():
    out = []
    try:
        import gen_posts
        out += list(gen_posts.POSTS)
    except Exception:
        pass
    try:
        from backlog import BACKLOG
        out += list(BACKLOG)
    except Exception:
        pass
    seen, uniq = set(), []
    for x in out:
        if x.get("slug") and x["slug"] not in seen:
            seen.add(x["slug"])
            uniq.append(x)
    return uniq


def reuse_keywords(need):
    """CRM이 비었을 때 다시 쓸 키워드를 need 개 고른다.

    글이 적게 붙은 키워드부터 고른다. 각도는 돌려 가며 쓰고(n % 6),
    그 키워드로 이미 쓴 제목을 전부 넘겨 같은 글이 안 나오게 막는다."""
    by_kw = {}
    for x in existing_posts():
        kw = (x.get("kw") or "").strip()
        if not kw:
            continue
        d = by_kw.setdefault(kw, {"vol": 0, "titles": []})
        d["vol"] = max(d["vol"], int(x.get("vol") or 0))
        d["titles"].append(x.get("title") or "")
    cand = sorted((len(v["titles"]), -v["vol"], k) for k, v in by_kw.items())
    return [(k, ANGLES[n % len(ANGLES)], by_kw[k]["titles"], -negvol)
            for n, negvol, k in cand[:need]]


# ── 생성 ─────────────────────────────────────────────
def prompt_for(keyword, links, retry_notes=None, angle=None, avoid_titles=()):
    linklist = "\n".join("- %s" % l for l in sorted(links))
    ang = ""
    if angle:
        ang = ("[이번 글의 각도 — %s]\n%s\n"
               "이 키워드로 쓴 글이 이미 있다. 아래 제목·구성과 겹치지 않게 쓰고,\n"
               "위 각도 하나로만 끝까지 밀어붙여라. 소제목도 그 각도 안에서 짜라.\n%s\n\n"
               % (angle[0], angle[1], "\n".join("- " + t for t in avoid_titles)))
    fix = ""
    if retry_notes:
        fix = ("\n\n[직전 시도에서 아래를 어겼다. 반드시 고쳐서 다시 써라]\n"
               + "\n".join("- " + n for n in retry_notes))

    return f"""{ang}너는 지오테스(콜센터 구축·컨택센터 전문)의 정보 콘텐츠를 쓰는 사람이다.
검색 키워드 "{keyword}" 로 들어온 담당자가 읽고 바로 판단할 수 있는 글을 쓴다.

[반드시 지킬 것]
1. 금액(원·만원)은 어떤 경우에도 쓰지 마라. 본문·표·FAQ 모두. 비용 질문에는 "구성을 보고 산정한다"로 답한다.
   아래 확정 사실에 없는 숫자(기간·건수·인원)도 쓰지 마라.
2. ★퍼센트(%)를 아예 쓰지 마라. 지오테스는 "절감률을 몇 퍼센트라고 말하지 않는다"를
   요금 페이지에 명시한 회사다. "30% 절감" 같은 문장은 회사 방침에 정면으로 어긋난다.
3. "전국콜비즈"를 언급하지 마라. 그쪽은 대표번호 개통 사이트이고 여기는 콜센터 구축이다.
4. 이모지를 쓰지 마라. 느낌표를 남발하지 마라.
5. 경쟁 업체 이름과 외부 URL을 쓰지 마라. 링크는 아래 내부 경로 목록에 있는 것만 쓴다.
6. "최저가·무조건·100%·업계 1위" 같은 단정 표현을 쓰지 마라.
7. 기계적으로 대칭되는 문장, 공허한 형용사, 연결어 남발을 피하라. 구체적인 장면으로 쓴다.
8. 독자의 문제를 먼저 정확히 짚고, 그 해답의 자리에 지오테스의 방식을 넣어라.
   혜택만 나열한 문단을 만들지 마라.

{FACTS}

[쓸 수 있는 내부 링크 — 본문에 3~6개를 <a class='inlink' href='...'> 로 자연스럽게 넣어라]
{linklist}

[본문 블록 규칙]
body 의 각 소제목은 blocks 배열을 가진다. 블록 종류는 다섯 가지뿐이다.
- {{"k":"p","v":"문단 HTML"}}            문단. <strong>, <a class='inlink'>, <br> 만 쓸 수 있다.
- {{"k":"h3","v":"작은 소제목"}}          평문만.
- {{"k":"list","v":["항목","항목"]}}      항목마다 <strong> 정도만.
- {{"k":"callout","v":"강조 상자 HTML"}}  한 글에 1~2개.
- {{"k":"table","v":[["머리","머리"],["칸","칸"]]}}  첫 줄이 머리줄. 한 글에 최대 1개.
소제목마다 p 블록이 최소 하나는 있어야 한다.

[분량] 태그를 뺀 순수 글자수 2,400자 이상. 소제목 5~6개, 소제목마다 블록 3~5개.

아래 JSON 형식으로만 답하라(설명 문장 없이 JSON만).
{{
 "slug": "영소문자-하이픈-슬러그(키워드를 영문으로, 20자 내외)",
 "cat": "다음 중 하나: {' / '.join(CATS)}",
 "title": "키워드가 앞쪽에 들어간 제목 15~60자. 과장 없이 구체적으로.",
 "desc": "검색결과에 뜨는 요약 80~230자. 키워드 + 핵심 답 + 상담 1555-5528.",
 "h1": "페이지 큰 제목. 두 줄로 끊어 <br> 를 한 번 넣는다. 다른 태그는 쓰지 않는다.",
 "sub": "큰 제목 아래 두 줄 설명. <br> 를 한 번 넣는다. 다른 태그는 쓰지 않는다.",
 "answer_q": "이 글이 답하는 질문 한 문장. 실제로 검색하는 말투로.",
 "answer": "그 질문에 곧바로 답하는 3~5문장. <b> 와 <span class='hl'>핵심</span> 만 쓴다.",
 "body": [{{"h":"소제목(결론을 선언하는 문장형)","blocks":[...]}}, ... 5~6개],
 "faq": [{{"q":"실제로 검색하는 질문","a":"80~200자 답변. 확정 사실만."}}, ... 6개]
}}{fix}"""


def ask(prompt):
    if not GEMINI_KEY:
        raise RuntimeError("제미나이 열쇠가 없습니다 (projects-hub/shared/keys.json 확인)")
    txt = gemini_call.generate_text(prompt, model=MODEL, temperature=0.65,
                                    timeout=120, key=GEMINI_KEY)
    txt = re.sub(r"^```json|^```|```$", "", txt.strip(), flags=re.M).strip()
    return json.loads(txt)


def to_post(d, keyword, vol=0):
    """gen_posts.build_html 이 먹는 형식으로 바꾼다."""
    return {
        "slug": d["slug"], "kw": keyword, "vol": vol,
        "cat": d["cat"],
        "title": re.sub(r"<[^>]+>", "", d["title"]).strip(),
        "desc": re.sub(r"<[^>]+>", "", d["desc"]).strip(),
        "h1": d["h1"], "sub": d["sub"],
        "answer_q": re.sub(r"<[^>]+>", "", d["answer_q"]).strip(),
        "answer": d["answer"],
        "body": [[s["h"], [[b["k"], b["v"]] for b in s["blocks"]]] for s in d["body"]],
        "faq": [[f["q"], f["a"]] for f in d["faq"]],
        "auto": True,
    }


def renders(post):
    """실제 HTML 로 찍어 보고 JSON-LD 가 깨지지 않는지 확인한다."""
    import gen_posts
    h = gen_posts.build_html(post)
    for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>', h, re.S):
        json.loads(b)
    return h


def build(keyword, vol=0, tries=TRIES, quiet=False, angle=None, avoid_titles=(),
          keep_slug=None):
    """검증까지 통과한 원고를 돌려준다. 못 만들면 None."""
    links = known_links()
    notes = None
    for i in range(1, tries + 1):
        try:
            raw = ask(prompt_for(keyword, links, notes, angle, avoid_titles))
        except gemini_call.CreditsExhausted:
            # 크레딧이 없으면 몇 번을 물어도 같은 답이다 — 바로 위로 올려 사유를 알린다
            raise
        except Exception as ex:
            if not quiet:
                print("  %d회차 생성 실패: %s" % (i, ex))
            time.sleep(2)
            continue

        if keep_slug:
            raw["slug"] = keep_slug      # 다시 쓰기 — 주소는 그대로 둔다
        bad = check(raw, keyword, avoid_titles, keep_slug)
        if not bad:
            post = to_post(raw, keyword, vol)
            try:
                renders(post)
            except Exception as ex:
                bad = ["HTML 로 찍었더니 깨짐: %s" % ex]
            if not bad:
                if not quiet:
                    print("  %d회차 통과 — %s (%d자)" % (i, post["slug"], len(_text(flat(raw)))))
                return post
        notes = bad[:6]
        if not quiet:
            print("  %d회차 반려 %d건: %s" % (i, len(bad), " / ".join(bad[:3])))
    return None


def save(post):
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, post["slug"] + ".json")
    json.dump(post, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return p


# ── CRM 연동 ─────────────────────────────────────────
def crm_keywords(need):
    """CRM 대기열에서 아직 글이 없는 키워드를 need 개 가져온다"""
    import crm_sync
    have, new = crm_sync.compare()
    if len(new) < need:
        try:
            body = {"need": need - len(new), "company_id": crm_sync.COMPANY}
            if getattr(crm_sync, "GROUP", None):
                body["group"] = crm_sync.GROUP
            if AUTOPICK_LIKE:
                body["like"] = AUTOPICK_LIKE
            crm_sync._call("/api/partner/geo-autopick", body)
            have, new = crm_sync.compare()
        except Exception as ex:
            print("자동 선별 실패(무시): %s" % ex)
    return new[:need]


def _만들어저장(일감, made, need, quiet):
    for kw, angle, titles, vol in 일감:
        if len(made) >= need:
            break
        print("[생성] %s%s" % (kw, (" · %s 각도" % angle[0]) if angle else ""))
        post = build(kw, vol=vol, quiet=quiet, angle=angle, avoid_titles=titles)
        if not post:
            print("  포기 — %d회 시도 모두 검증 실패(발행 안 함)" % TRIES)
            continue
        if angle:
            post["reuse"] = angle[0]
        save(post)
        made.append(post)
    return made


def autofill(need, quiet=False):
    """need 개를 생성해 대기열(generated/)에 저장한다. 만든 목록을 돌려준다.

    새 키워드를 먼저 쓰고, 모자라면 쓰던 키워드를 각도만 바꿔 다시 쓴다.
    키워드가 없다고 발행을 쉬지 않는다."""
    made = []
    if need <= 0:
        return made

    일감 = []
    try:
        for _id, kw in crm_keywords(need):
            일감.append((kw, None, (), 0))
    except Exception as ex:
        print("CRM 키워드 조회 실패(쓰던 키워드로 대신함): %s" % ex)

    if len(일감) < need:
        추가 = reuse_keywords(need - len(일감))
        if 추가:
            print("새 키워드가 %d개뿐이라 쓰던 키워드 %d개를 다른 각도로 씁니다"
                  % (len(일감), len(추가)))
            일감 += 추가
        elif not 일감:
            print("쓸 키워드가 없습니다 — CRM 창고와 기존 글이 모두 비었습니다")
            return made

    _만들어저장(일감, made, need, quiet)

    # 키워드는 있었는데 생성이 실패해 모자란 경우 — 쓰던 키워드로 한 번 더 메운다.
    # 키워드가 없어서 못 쓰는 것과 글이 안 나와서 못 쓰는 것은 다른 일이다.
    if len(made) < need:
        쓴것 = {kw for kw, _, _, _ in 일감}
        추가 = [x for x in reuse_keywords(need * 2) if x[0] not in 쓴것]
        if 추가:
            print("생성 실패분 %d개를 쓰던 키워드로 다시 메웁니다" % (need - len(made)))
            _만들어저장(추가, made, need, quiet)
    return made


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__.strip())
        return
    if args[0] == "--rewrite":
        # 이미 나간 글을 같은 주소·같은 키워드로 다시 쓴다 (규칙이 바뀌었을 때)
        실패 = []
        for slug in args[1:]:
            옛것 = json.load(io.open(os.path.join(OUT, slug + ".json"), encoding="utf-8"))
            print("[다시 쓰기] %s (%s)" % (slug, 옛것["kw"]))
            post = build(옛것["kw"], vol=옛것.get("vol", 0), keep_slug=slug)
            if not post:
                실패.append(slug)
                continue
            save(post)
        print("\n%d편 중 %d편 다시 씀%s" % (len(args) - 1, len(args) - 1 - len(실패),
              (" / 실패: " + ", ".join(실패)) if 실패 else ""))
        return
    if args[0] == "--fill":
        autofill(int(args[1]) if len(args) > 1 else 2)
        return
    dry = args[0] == "--dry"
    kw = args[1] if dry else args[0]
    post = build(kw)
    if not post:
        sys.exit("만들지 못했습니다.")
    if dry:
        print(json.dumps(post, ensure_ascii=False, indent=1)[:1500])
    else:
        print("저장: " + save(post))


if __name__ == "__main__":
    main()
