# -*- coding: utf-8 -*-
"""
지오테스 나머지 페이지 생성기 (솔루션 외)
  python _tools/gen_pages.py

  활용사례 허브 + 7  /  업종별 허브 + 11  /  요금 · 구축사례 · 회사소개 · 상담문의

머리말·꼬리말·상대경로 처리는 gen_solution.py 것을 그대로 가져다 씀.
내용 수정은 아래 데이터 목록만 고치면 됨.
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_solution import (head, header, FOOTER, write, e, SITE, TEL, TEL_RAW)

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DIST = os.path.join(ROOT, "dist")

# ---------------------------------------------------------------- 활용사례

USE_CASES = [
 dict(slug="support", nav="고객 응대",
  h1="반복 문의를<br>첫 통화에서 끝냅니다",
  sub="같은 질문에 같은 답을 하루에 수십 번 하고 있다면, 그 시간은 다른 곳에 써야 합니다.",
  aq="고객 응대를 자동화하면 서비스가 나빠지지 않나요?",
  a="나빠지는 쪽은 <b>대기</b>입니다. 답이 정해진 문의까지 사람이 받으면 정작 설명이 필요한 고객이 기다립니다. "
    "<span class='hl'>정해진 답이 있는 문의는 즉시 처리하고, 판단이 필요한 통화는 사람에게 넘기는</span> 구조가 양쪽 다 낫습니다.",
  points=[("첫 통화 종결","묻고 답하고 끝냅니다. 다시 걸 일이 줄어듭니다."),
          ("대기 이탈 감소","기다리다 끊는 고객이 사라집니다."),
          ("야간·휴일 유지","시간대와 상관없이 같은 안내가 나갑니다.")],
  flows=[("발화로 의도 파악","무엇 때문에 걸었는지 첫 마디에서 잡습니다."),
         ("자료 기반 응답","등록된 안내와 정책에서 근거를 찾아 답합니다."),
         ("처리·접수","단순 변경과 접수는 통화 안에서 끝냅니다."),
         ("상담원 인계","넘길 때 대화 요약을 함께 전달합니다.")],
  faq=[("어떤 문의부터 넣나요?","가장 자주 오면서 답이 고정된 것부터 넣습니다."),
       ("답을 못 하면요?","상담원에게 넘어갑니다. 고객이 설명을 반복하지 않게 요약이 같이 갑니다."),
       ("안내 내용을 바꾸려면요?","등록된 자료를 수정하면 그다음 통화부터 반영됩니다.")]),

 dict(slug="booking", nav="예약·접수",
  h1="예약 변경 전화를<br>사람이 받지 않아도 됩니다",
  sub="예약 확인, 변경, 취소는 통화 내용이 거의 정해져 있습니다.",
  aq="예약 전화는 어떤 점이 자동화하기 좋은가요?",
  a="예약 통화는 <span class='hl'>물어볼 것과 확인할 것이 정해져 있습니다</span>. 누구인지 확인하고, 언제로 옮길지 듣고, 가능한 시간을 알려주면 끝납니다. "
    "여기에 방문 전 확인 전화까지 붙이면 빈자리가 줄어듭니다.",
  points=[("빈자리 감소","오기로 한 사람이 안 오는 일이 줄어듭니다."),
          ("접수 누락 방지","업무 외 시간 예약도 받아 둡니다."),
          ("변경 처리 자동화","일정 조정을 통화 안에서 끝냅니다.")],
  flows=[("본인 확인","이름과 연락처로 예약 건을 찾습니다."),
         ("가능 시간 안내","비어 있는 시간을 알려주고 고릅니다."),
         ("확정 안내 발송","정해진 일정을 문자로 보냅니다."),
         ("방문 전 확인","하루 이틀 전에 다시 걸어 확인합니다.")],
  faq=[("기존 예약 시스템과 연결되나요?","연동 방식은 쓰시는 시스템을 보고 정합니다."),
       ("취소도 받을 수 있나요?","취소와 변경 모두 통화 안에서 처리합니다."),
       ("확정 문자는 자동인가요?","통화가 끝나면 바로 나갑니다.")]),

 dict(slug="routing", nav="대표번호 안내",
  h1="번호를 누르지 않고도<br>맞는 곳으로 갑니다",
  sub="1번 누르고 다시 2번 누르는 안내를 끝까지 듣는 고객은 많지 않습니다.",
  aq="기존 ARS와 무엇이 다른가요?",
  a="기존 ARS는 <b>메뉴를 순서대로 눌러야</b> 원하는 곳에 도착합니다. 단계가 깊어질수록 중간에 끊는 사람이 늘어납니다. "
    "<span class='hl'>말한 내용으로 바로 분기하면</span> 메뉴 트리를 지나갈 필요가 없습니다.",
  points=[("대기 없는 첫 응답","울리자마자 받습니다."),
          ("정확한 이관","부서·지점·긴급도를 판단해 넘깁니다."),
          ("단순 문의 종결","위치와 영업시간은 그 자리에서 끝냅니다.")],
  flows=[("첫 마디로 분류","무엇 때문에 걸었는지 듣고 나눕니다."),
         ("지점·부서 분기","조건과 일정에 따라 갈라집니다."),
         ("자료 기반 안내","반복 문의는 연결 없이 답합니다."),
         ("요약과 함께 이관","넘길 때 지금까지의 내용을 붙입니다.")],
  faq=[("쓰던 대표번호를 그대로 쓰나요?","번호를 바꾸지 않고 적용합니다."),
       ("기존 ARS와 같이 쓸 수 있나요?","일부 구간만 바꾸는 방식도 가능합니다."),
       ("긴급 전화는 어떻게 하나요?","조건을 정해 바로 담당자로 넘깁니다.")]),

 dict(slug="outbound", nav="아웃바운드 영업",
  h1="사람이 못 거는 양까지<br>걸어 봅니다",
  sub="명단은 있는데 걸 사람이 없어서 못 돌리는 경우가 많습니다.",
  aq="자동 발신이 영업에 실제로 도움이 되나요?",
  a="도움이 되는 지점은 <span class='hl'>거르는 단계</span>입니다. 수백 통을 돌려 관심 있는 곳만 남기면, 영업 담당자는 그 명단부터 시작합니다. "
    "관심 없는 통화에 쓰던 시간이 빠집니다.",
  points=[("도달량 확보","같은 톤으로 정해진 양을 채웁니다."),
          ("관심 고객 선별","반응이 있는 곳만 남깁니다."),
          ("기록 자동화","통화 결과가 CRM에 바로 쌓입니다.")],
  flows=[("명단 업로드","보유한 목록을 올립니다."),
         ("대량 발신","예약 발송과 자동 재발신을 씁니다."),
         ("관심 확인","조건을 물어 자격을 나눕니다."),
         ("담당자 연결","가능성 있는 건만 사람에게 넘깁니다.")],
  faq=[("발신 시간 규정은 지켜지나요?","발신 가능 시간대와 수신 거부 처리를 설정에 넣습니다."),
       ("스크립트는 누가 만드나요?","기존에 쓰시던 내용을 바탕으로 함께 정리합니다."),
       ("결과를 어디서 보나요?","통화별 결과와 녹취를 관리자 화면에서 봅니다.")]),

 dict(slug="reminder", nav="리마인드·해피콜",
  h1="잊지 않게,<br>빠뜨리지 않게",
  sub="방문 전 확인과 사후 만족도 조사는 미루면 안 하게 됩니다.",
  aq="리마인드 전화를 꼭 사람이 해야 하나요?",
  a="확인 전화는 <span class='hl'>내용이 거의 같고 양이 많습니다</span>. 사람이 하면 바쁠 때 가장 먼저 밀립니다. "
    "자동으로 돌리면 밀리지 않고, 응답 결과만 정리해서 봅니다.",
  points=[("노쇼 감소","오기 전에 한 번 더 확인합니다."),
          ("사후 관리 유지","바빠도 빠뜨리지 않습니다."),
          ("응답 자동 정리","결과가 이력에 바로 남습니다.")],
  flows=[("대상 추출","날짜와 조건으로 명단을 뽑습니다."),
         ("자동 발신","정해진 시간에 겁니다."),
         ("응답 수집","확인·변경·취소를 통화에서 받습니다."),
         ("결과 반영","일정과 이력에 반영합니다.")],
  faq=[("몇 번까지 다시 거나요?","재발신 횟수와 간격을 정해둡니다."),
       ("문자로도 보낼 수 있나요?","통화와 문자를 함께 씁니다."),
       ("불만이 나오면요?","상담원에게 바로 넘깁니다.")]),

 dict(slug="overdue", nav="미납 안내",
  h1="정해진 기준 안에서<br>차분하게 안내합니다",
  sub="미납 안내는 무엇을 말하고 무엇을 말하지 않을지가 중요합니다.",
  aq="미납 안내를 자동으로 해도 되나요?",
  a="규정을 지키는 것이 전제입니다. <span class='hl'>발신 가능 시간, 금지 표현, 수신 거부 처리</span>를 설정에 넣어두면 통화마다 같은 기준이 적용됩니다. "
    "사람마다 말이 달라지는 문제가 줄어듭니다.",
  points=[("일관된 안내","누가 받아도 같은 내용이 전달됩니다."),
          ("약속 기록","납부 예정일과 금액을 남깁니다."),
          ("규정 준수","시간과 표현을 기준 안에서 관리합니다.")],
  flows=[("본인 확인","정해진 절차로 확인합니다."),
         ("금액·기한 안내","미납 내용과 납부 방법을 전달합니다."),
         ("납부 약속 접수","예정일과 방식을 받습니다."),
         ("이의 제기 이관","항의나 분쟁은 사람에게 넘깁니다.")],
  faq=[("이미 납부한 분에게 또 걸지 않나요?","납부 확인 결과를 반영해 대상에서 뺍니다."),
       ("녹취는 남나요?","전 통화를 남기고 조건으로 찾습니다."),
       ("수신 거부는요?","거부 의사를 받으면 다음 발신에서 제외합니다.")]),

 dict(slug="survey", nav="설문조사",
  h1="문자로는 답하지 않는 분들께<br>전화로 묻습니다",
  sub="응답률이 낮으면 결과를 믿기 어렵습니다.",
  aq="전화 설문이 문자 설문보다 나은가요?",
  a="대상에 따라 다릅니다. <span class='hl'>문자에 응답하지 않는 층</span>, 특히 연령대가 높은 표본은 통화 응답률이 훨씬 높습니다. "
    "점수와 자유응답을 함께 받아 바로 정리된 형태로 쌓습니다.",
  points=[("응답률 확보","닿기 어려운 표본까지 접근합니다."),
          ("건당 비용 절감","동시에 여러 건을 돌립니다."),
          ("즉시 집계","응답이 들어오는 대로 쌓입니다.")],
  flows=[("문항 구성","질문 순서와 조건 분기를 정합니다."),
         ("자동 발신","대상 명단으로 동시에 겁니다."),
         ("응답 수집","점수와 자유응답을 함께 받습니다."),
         ("결과 정리","항목별로 집계해 내려받습니다.")],
  faq=[("자유응답도 되나요?","말한 내용을 글로 정리해 남깁니다."),
       ("개인정보 동의는요?","안내와 동의 절차를 문항에 넣습니다."),
       ("결과를 외부로 보낼 수 있나요?","파일로 내려받거나 시스템으로 넘깁니다.")]),
]

# ---------------------------------------------------------------- 업종별

def ind(slug, nav, h1, sub, why, pains, calls, setup, ucs, faq):
    return dict(slug=slug, nav=nav, h1=h1, sub=sub, why=why,
                pains=pains, calls=calls, setup=setup, ucs=ucs, faq=faq)

INDUSTRIES = [
 ind("hospital", "병원·의원", "예약 전화가<br>진료를 방해하지 않게",
  "접수 직원이 전화를 받느라 창구 앞에 선 환자를 기다리게 하는 상황이 매일 반복됩니다.",
  "병원 전화는 <span class='hl'>진료 시간과 정확히 겹칩니다</span>. 가장 바쁜 시간에 가장 많이 울립니다. "
  "그런데 걸려오는 내용은 예약·변경·취소·위치·진료시간으로 거의 정해져 있습니다. "
  "정해진 문의를 자동으로 처리하면 접수 직원은 눈앞의 환자에게 집중할 수 있습니다.",
  [("접수와 전화를 한 사람이 함", "창구 응대 중에 전화가 오면 둘 중 하나는 기다려야 합니다."),
   ("점심시간과 진료 마감 후 문의", "받을 사람이 없는 시간에 걸려온 전화는 그대로 사라집니다."),
   ("예약 부도로 비는 진료 시간", "확인 전화를 돌릴 여력이 없어 빈자리를 그대로 둡니다.")],
  ["오늘 진료 되나요", "예약을 다음 주로 옮기고 싶어요", "몇 시까지 하나요",
   "주차는 어디에 하나요", "검사 결과 나왔나요", "예약 취소할게요"],
  [("예약·변경·취소 자동 접수", "통화 안에서 일정을 확인하고 바꿉니다. 확정 내용은 문자로 나갑니다."),
   ("진료시간·위치 자동 안내", "가장 많이 오는 문의를 사람 연결 없이 끝냅니다."),
   ("방문 전 확인 전화", "하루 이틀 전에 자동으로 걸어 확인합니다. 빈자리가 줄어듭니다."),
   ("진료과별 연결", "문의 내용에 따라 해당 과나 담당자에게 넘깁니다.")],
  ["booking", "routing", "reminder"],
  [("환자 개인정보는 어떻게 관리되나요?", "통화 이력과 녹취의 열람 권한을 직급·담당별로 나눕니다. 보관 위치도 클라우드와 원내 서버 중에 고를 수 있습니다."),
   ("증상 문의도 AI가 답하나요?", "진료 판단이 필요한 내용은 답하지 않고 담당자에게 넘깁니다. 예약과 안내만 처리합니다."),
   ("기존 예약 프로그램과 연결되나요?", "쓰시는 프로그램을 보고 연동 범위를 정합니다. 연동이 어려우면 별도 화면으로 운영합니다.")]),

 ind("public", "공공·기관", "민원이 몰려도<br>대기가 생기지 않게",
  "특정 기간에 민원이 폭증하고, 담당자 개인번호가 노출되는 문제가 함께 옵니다.",
  "공공기관 전화는 <span class='hl'>기간에 따라 통화량이 몇 배로 뜁니다</span>. 신청 마감이나 정책 발표 직후가 그렇습니다. "
  "그때 인원을 늘릴 수는 없으니 대기가 길어지고 민원이 다시 민원을 부릅니다. "
  "안내로 끝나는 문의를 먼저 걸러내면 사람이 받아야 할 통화만 남습니다.",
  [("기간별 민원 폭증", "평소 인원으로는 감당이 안 되는 시기가 정해져 있습니다."),
   ("담당자 개인번호 노출", "한 번 알려준 번호로 퇴근 후에도 연락이 옵니다."),
   ("같은 안내의 반복", "공고에 있는 내용을 전화로 다시 설명하는 일이 대부분입니다.")],
  ["신청 자격이 되나요", "서류는 뭘 내야 하나요", "접수 기간이 언제까지인가요",
   "담당 부서 연결해 주세요", "처리 어디까지 됐나요", "방문 시간 알려주세요"],
  [("민원 유형 자동 분류", "무엇 때문에 걸었는지 듣고 담당 부서로 나눕니다."),
   ("안내 자동 응답", "공고 내용과 제출 서류는 연결 없이 답합니다."),
   ("개인번호 비노출", "대표번호와 안심번호로 통화해 직원 번호가 남지 않습니다."),
   ("전 통화 녹취·보관", "민원 응대 기록을 규정에 맞는 기간만큼 남깁니다.")],
  ["routing", "support", "survey"],
  [("녹취를 기관 서버에 둘 수 있나요?", "가능합니다. 기본은 클라우드지만 외부 보관이 어려운 곳은 기관 서버에 직접 둡니다."),
   ("조달 절차로 도입할 수 있나요?", "계약 방식은 기관 규정에 맞춰 협의합니다."),
   ("야간·휴일 민원은 어떻게 되나요?", "안내와 접수를 받아두고 다음 근무일에 담당자가 이어서 처리합니다.")]),

 ind("finance", "금융·보험", "녹취와 본인확인을<br>규정대로",
  "누가 언제 무엇을 안내했는지 확인할 수 있어야 하고, 그 기록이 규정 기간만큼 남아야 합니다.",
  "금융·보험 상담은 <span class='hl'>기록이 곧 근거</span>입니다. 말로 한 안내가 나중에 분쟁이 되면 녹취가 있느냐 없느냐로 갈립니다. "
  "본인확인 절차도 사람마다 다르면 안 됩니다. 정해진 순서와 표현을 시스템에 넣어두면 누가 받아도 같은 절차가 지켜집니다.",
  [("상담원별 안내 편차", "같은 상품인데 설명이 사람마다 달라집니다."),
   ("녹취 보관 규정 대응", "얼마나 오래, 어디에 남길지가 규정으로 정해져 있습니다."),
   ("본인확인 누락", "바쁠 때 절차가 생략되면 그대로 사고가 됩니다.")],
  ["계약 내용 확인하고 싶어요", "보험금 청구는 어떻게 하나요", "납입일을 바꿀 수 있나요",
   "해지하면 얼마 나오나요", "담당 설계사 연결해 주세요", "서류 접수됐나요"],
  [("전 통화 녹취·조건 검색", "기간·상담원·고객번호·통화상태로 찾습니다."),
   ("본인확인 절차 표준화", "정해진 질문 순서를 통화 흐름에 넣습니다."),
   ("보관 위치·기간 선택", "AWS 클라우드 기본, 요청 시 고객사 서버에 직접 보관합니다."),
   ("열람 권한 분리", "누가 어떤 녹취를 들을 수 있는지 나눕니다.")],
  ["support", "overdue", "reminder"],
  [("녹취를 몇 년까지 보관할 수 있나요?", "규정에 맞춰 기간을 설정합니다. 용량은 통화량과 기간으로 산정해 드립니다."),
   ("상담 품질 점검이 되나요?", "실시간 감청과 녹취 재생으로 점검하고, AI 통화요약으로 내용을 빠르게 확인합니다."),
   ("개인정보 마스킹이 되나요?", "열람 권한에 따라 민감 정보 노출 범위를 조정합니다.")]),

 ind("education", "교육·학원", "상담 전화를<br>놓치지 않게",
  "상담 문의는 저녁과 주말에 몰리는데, 정작 그 시간에 받을 사람이 없습니다.",
  "학원 상담 전화는 <span class='hl'>학부모가 시간이 나는 때</span> 걸려옵니다. 퇴근 후, 주말, 방학 직전입니다. "
  "그때 못 받은 전화는 다시 걸려오지 않고 다른 학원으로 갑니다. 한 통이 곧 등록 한 건이라 놓치는 비용이 큽니다.",
  [("저녁·주말 문의 누락", "가장 문의가 많은 시간에 받을 사람이 없습니다."),
   ("교사 개인번호 노출", "한 번 알려주면 시도 때도 없이 연락이 옵니다."),
   ("상담 이력이 안 남음", "누가 무엇을 물었는지 기억에만 있어 후속 연락이 끊깁니다.")],
  ["수업료가 얼마인가요", "레벨테스트 받을 수 있나요", "시간표 알려주세요",
   "상담 예약하고 싶어요", "결석하면 보강되나요", "셔틀 노선이 어떻게 되나요"],
  [("업무 외 시간 상담 접수", "저녁과 주말 문의를 받아 두고 다음 날 이어갑니다."),
   ("안심번호 통화", "교사 개인번호를 노출하지 않고 연락합니다."),
   ("상담 이력 관리", "문의부터 등록까지의 과정을 한 화면에 쌓습니다."),
   ("등록 안내 문자 발송", "상담 뒤 안내와 결제 정보를 바로 보냅니다.")],
  ["support", "booking", "reminder"],
  [("문의만 하고 등록 안 한 분도 관리되나요?", "상담 이력에 남아 재연락 시점을 걸어둘 수 있습니다."),
   ("여러 지점을 함께 관리할 수 있나요?", "지점별로 번호와 담당을 나누고 본원에서 전체를 봅니다."),
   ("작은 규모도 되나요?", "한두 석 규모부터 구성합니다.")]),

 ind("shop", "쇼핑몰", "전화도 채팅도<br>한 화면에서",
  "주문, 배송, 교환 문의가 전화와 메신저로 동시에 들어옵니다.",
  "쇼핑몰 문의는 <span class='hl'>채널이 흩어져 있는 것이 가장 큰 문제</span>입니다. "
  "전화로 물었다가 카카오톡으로 다시 묻는 고객을 다른 사람으로 응대하면 답이 엇갈립니다. "
  "게다가 내용의 대부분은 주문 조회와 배송 상태라 자동으로 처리할 수 있는 영역입니다.",
  [("채널마다 창이 따로", "네 개를 띄워놓고 번갈아 보다 보면 놓칩니다."),
   ("같은 조회 문의 반복", "배송 어디까지 갔는지 묻는 전화가 하루 종일 옵니다."),
   ("행사 기간 문의 폭증", "세일 때만 몰리는데 그때만 사람을 늘릴 수는 없습니다.")],
  ["주문한 거 언제 오나요", "교환하고 싶어요", "환불은 언제 되나요",
   "사이즈 바꿀 수 있나요", "주문 취소해 주세요", "재입고 되나요"],
  [("채널 통합 상담", "문자·카카오·톡톡을 한 목록에서 받습니다."),
   ("주문 조회 자동 응답", "주문번호나 연락처로 상태를 바로 안내합니다."),
   ("교환·반품 접수 분류", "요청 유형을 나눠 담당자에게 넘깁니다."),
   ("전화 상담 이력 연결", "채팅과 통화 기록을 같은 고객 이력에 쌓습니다.")],
  ["support", "routing", "reminder"],
  [("쇼핑몰 솔루션과 연동되나요?", "쓰시는 플랫폼을 보고 연동 범위를 정합니다."),
   ("행사 때만 늘릴 수 있나요?", "회선과 상담석을 기간에 맞춰 조정하는 방식으로 협의합니다."),
   ("반품 요청도 자동으로 받나요?", "접수와 분류는 자동으로, 판단이 필요한 건은 상담원에게 넘깁니다.")]),

 ind("manufacturing", "제조업", "거래처 통화를<br>회사 자산으로",
  "담당자 개인 휴대폰에만 이력이 남아, 그 사람이 자리를 비우면 아무도 답을 못 합니다.",
  "제조업 전화는 <span class='hl'>사람에게 붙어 있습니다</span>. 거래처는 담당자 휴대폰으로 직접 걸고, 통화 내용은 그 사람 머릿속에만 남습니다. "
  "담당자가 휴가를 가거나 퇴사하면 거래 이력이 통째로 사라집니다. 통화를 회사 기록으로 옮기면 이 위험이 없어집니다.",
  [("개인 휴대폰 의존", "담당자가 없으면 거래처 문의에 아무도 답을 못 합니다."),
   ("이력 인수인계 불가", "퇴사할 때 통화 기록이 함께 나갑니다."),
   ("견적·발주 구두 진행", "말로 정한 수량과 단가가 나중에 달라집니다.")],
  ["견적 요청드립니다", "발주 넣은 거 확인해 주세요", "납기가 언제인가요",
   "단가 조정 가능한가요", "불량 건으로 연락드립니다", "담당자 바뀌었나요"],
  [("거래처별 통화 이력", "어느 거래처와 언제 무슨 이야기를 했는지 쌓입니다."),
   ("회사번호로 수발신", "개인 휴대폰에서도 회사 번호로 걸고 받습니다."),
   ("전 통화 녹취", "구두로 정한 수량과 단가를 확인할 수 있습니다."),
   ("담당 부재 시 인계", "다른 직원이 이력을 보고 바로 이어받습니다.")],
  ["support", "outbound", "reminder"],
  [("외근이 많은데 사무실 밖에서도 되나요?", "앱으로 회사 번호를 그대로 씁니다. 개인 번호는 노출되지 않습니다."),
   ("기존 ERP와 연결되나요?", "저희가 직접 개발하는 시스템이라 연동 개발이 가능합니다."),
   ("작은 규모도 되나요?", "몇 석 규모부터 구성합니다.")]),

 ind("distribution", "유통·물류", "배송 문의를<br>자동으로 걸러",
  "같은 배송 조회 문의가 하루 종일 반복되고, 클레임은 그 사이에 묻힙니다.",
  "물류 관련 문의는 <span class='hl'>대부분 조회</span>입니다. 지금 어디쯤 왔는지 묻는 전화가 압도적으로 많습니다. "
  "이걸 사람이 받으면 정작 처리가 필요한 파손·오배송 클레임이 대기에 밀립니다. "
  "조회를 자동으로 돌리면 사람은 클레임만 봅니다.",
  [("조회 문의가 대부분", "처리할 것도 없는 통화가 상담 시간을 다 씁니다."),
   ("클레임이 뒤로 밀림", "급한 건이 단순 문의 뒤에서 기다립니다."),
   ("기사·고객 번호 노출", "개인 번호가 오가면 이후 연락이 통제되지 않습니다.")],
  ["지금 어디쯤 왔나요", "오늘 배송 되나요", "물건이 파손됐어요",
   "다른 주소로 바꿔주세요", "반품 수거 요청합니다", "송장번호 알려주세요"],
  [("배송 조회 자동 안내", "송장번호나 연락처로 상태를 바로 알려줍니다."),
   ("클레임 접수 분류", "파손·오배송·지연을 나눠 담당자에게 넘깁니다."),
   ("안심번호 통화", "기사와 고객이 서로 번호를 남기지 않고 통화합니다."),
   ("대량 안내 발송", "지연이나 일정 변경을 한 번에 알립니다.")],
  ["support", "routing", "reminder"],
  [("배송 시스템과 연결되나요?", "쓰시는 시스템을 보고 조회 연동 범위를 정합니다."),
   ("기사 번호를 숨길 수 있나요?", "안심번호로 연결해 양쪽 다 실제 번호가 남지 않습니다."),
   ("성수기에 늘릴 수 있나요?", "회선과 상담석을 기간에 맞춰 조정합니다.")]),

 ind("law", "법무·세무", "놓친 전화가<br>곧 놓친 사건",
  "상담 중에는 전화를 받을 수 없고, 부재중 전화는 대개 다시 걸려오지 않습니다.",
  "법무·세무 상담 문의는 <span class='hl'>한 통의 값이 큽니다</span>. 상담을 받으러 거는 사람은 여러 곳에 전화하고, 먼저 받는 곳과 진행합니다. "
  "그런데 정작 그 시간에 담당자는 다른 상담 중입니다. 받아두고 나중에 잇는 구조가 필요합니다.",
  [("상담 중 전화 못 받음", "가장 중요한 시간에 가장 많은 전화가 옵니다."),
   ("부재중은 회신이 없음", "다시 걸어오지 않고 다른 곳으로 갑니다."),
   ("문의 내용이 안 남음", "무슨 사건으로 걸었는지 모른 채 다시 걸어야 합니다.")],
  ["상담 받을 수 있나요", "비용이 얼마나 드나요", "이런 경우도 되나요",
   "서류는 뭘 준비하나요", "진행 상황 알려주세요", "예약 변경하고 싶어요"],
  [("부재중 콜백 접수", "용건과 연락처를 받아 목록으로 띄웁니다."),
   ("상담 예약 자동 안내", "가능한 시간을 알려주고 예약까지 받습니다."),
   ("문의 내용 요약", "어떤 건으로 걸었는지 정리해 남깁니다."),
   ("전 통화 녹취", "상담 내용을 확인할 수 있게 남깁니다.")],
  ["booking", "support", "reminder"],
  [("상담 내용을 AI가 답해도 되나요?", "법률 판단은 하지 않습니다. 접수와 예약, 안내만 처리하고 나머지는 넘깁니다."),
   ("의뢰인 정보가 안전한가요?", "열람 권한을 나누고 녹취 보관 위치를 선택할 수 있습니다."),
   ("혼자 운영해도 되나요?", "1인 사무소 규모부터 구성합니다.")]),

 ind("counseling", "심리상담", "상담사 번호를<br>지키면서",
  "개인 번호로 연락이 이어지면 상담사가 먼저 소진됩니다.",
  "심리상담은 <span class='hl'>경계를 지키는 것이 곧 상담의 조건</span>입니다. 개인 번호가 알려지면 상담 시간 밖에도 연락이 오고, "
  "그 부담이 그대로 상담 품질로 이어집니다. 번호를 분리하고 시간을 정해두면 상담사와 내담자 모두를 보호할 수 있습니다.",
  [("개인번호 노출", "한 번 알려진 번호는 회수할 수 없습니다."),
   ("상담 시간 밖 연락", "밤과 주말에도 연락이 이어집니다."),
   ("기록 접근 관리", "민감한 내용이라 누가 볼 수 있는지가 중요합니다.")],
  ["상담 예약하고 싶어요", "비용이 어떻게 되나요", "어떤 상담을 받아야 하나요",
   "시간 변경 가능한가요", "온라인으로도 되나요", "상담사를 바꿀 수 있나요"],
  [("안심번호 통화", "실제 번호를 노출하지 않고 연결합니다."),
   ("상담 시간 외 자동 안내", "정해진 시간 밖에는 안내와 접수만 받습니다."),
   ("열람 권한 관리", "상담 기록을 볼 수 있는 범위를 나눕니다."),
   ("예약·변경 접수", "일정 조정을 통화 안에서 처리합니다.")],
  ["booking", "support", "reminder"],
  [("녹취를 꼭 남겨야 하나요?", "남길지 여부와 범위를 선택할 수 있습니다. 남기지 않는 설정도 가능합니다."),
   ("내담자 정보는 어떻게 보호되나요?", "열람 권한 분리와 보관 위치 선택으로 관리합니다."),
   ("위급 상황 연락은요?", "정해진 조건에서 담당자에게 바로 연결되도록 구성합니다.")]),

 ind("sales", "분양·영업", "걸어야 할 곳이<br>많을 때",
  "명단은 수천 건인데 상담 인력은 한정돼 있습니다.",
  "분양과 영업 전화는 <span class='hl'>양이 성과를 만듭니다</span>. 다만 사람이 거는 양에는 한계가 있고, 대부분은 관심 없는 통화입니다. "
  "자동으로 돌려 관심 있는 곳만 남기면, 상담원은 그 명단부터 시작합니다. 버리는 시간이 크게 줄어듭니다.",
  [("발신량 한계", "하루에 걸 수 있는 통화 수가 정해져 있습니다."),
   ("관심 없는 통화에 소모", "대부분의 시간이 거절에 쓰입니다."),
   ("실적 파악이 늦음", "누가 몇 건을 걸어 몇 건이 됐는지 집계가 늦습니다.")],
  ["분양가가 얼마인가요", "위치가 어디인가요", "방문 상담 예약할게요",
   "잔여 세대 있나요", "대출 조건이 어떻게 되나요", "연락하지 마세요"],
  [("대량 발신·자동 재발신", "명단을 올리면 예약 시간에 자동으로 겁니다."),
   ("관심 고객 선별", "조건을 물어 가능성 있는 건만 남깁니다."),
   ("상담원별 실적 통계", "발신·연결·성사 건수를 사람별로 봅니다."),
   ("수신 거부 관리", "거부 의사를 받으면 다음 발신에서 제외합니다.")],
  ["outbound", "reminder", "survey"],
  [("발신 규정은 지켜지나요?", "발신 가능 시간대와 수신 거부 처리를 설정에 넣습니다."),
   ("녹취가 남나요?", "전 통화를 남기고 조건으로 찾습니다."),
   ("상담원이 늘어도 되나요?", "인원에 맞춰 회선과 상담석을 늘립니다.")]),

 ind("rental", "렌탈·구독", "정기 안내를<br>빠뜨리지 않게",
  "만기, 점검, 수납 안내가 매달 반복되는데 사람이 하면 바쁠 때 가장 먼저 밀립니다.",
  "렌탈과 구독 사업은 <span class='hl'>정기 연락이 곧 매출 유지</span>입니다. 만기 안내를 못 하면 그대로 해지가 되고, "
  "수납 안내가 늦으면 연체가 쌓입니다. 내용이 매번 거의 같기 때문에 자동으로 돌리기에 가장 적합한 영역입니다.",
  [("정기 안내 누락", "바쁜 달에는 안내가 통째로 밀립니다."),
   ("만기 시점 놓침", "연락이 없으면 고객은 그냥 해지합니다."),
   ("연체 안내 부담", "말을 꺼내기 어려워 미루게 됩니다.")],
  ["만기가 언제인가요", "점검 예약하고 싶어요", "요금이 왜 올랐나요",
   "해지하려면 어떻게 하나요", "납부일을 바꿀 수 있나요", "필터 교체 신청합니다"],
  [("정기 안내 자동 발신", "만기와 점검 시점에 자동으로 겁니다."),
   ("납부 안내 표준화", "정해진 표현과 시간대 안에서 안내합니다."),
   ("점검 예약 접수", "가능한 날짜를 안내하고 예약을 받습니다."),
   ("해지 방어 연결", "해지 의사가 확인되면 담당 상담원에게 넘깁니다.")],
  ["reminder", "overdue", "outbound"],
  [("연체 안내에 규정 문제는 없나요?", "발신 시간, 금지 표현, 수신 거부 처리를 설정에 넣어 기준 안에서 운영합니다."),
   ("이미 납부한 분에게 또 걸지 않나요?", "납부 결과를 반영해 대상에서 뺍니다."),
   ("고객 수가 많아도 되나요?", "규모에 맞춰 시스템 사양을 잡습니다.")]),
]

# ---------------------------------------------------------------- 템플릿 조각

def hero(eyebrow, h1, sub, crumb):
    return f'''
<div class="hero-top">
  <div class="wrap">
    <p style="font-size:13px;color:var(--slate-400);text-align:center">{crumb}</p>
    <div class="hero-center compact">
      <span class="eyebrow">{eyebrow}</span>
      <h1 style="margin-top:16px">{h1}</h1>
      <p class="sub">{sub}</p>
      <div class="actions">
        <a href="/#lead" class="btn btn-brand">무료 상담 신청</a>
        <a href="tel:{TEL_RAW}" class="btn btn-outline">{TEL}</a>
      </div>
    </div>
  </div>
</div>'''


def answer_box(q, a):
    return f'''
<section style="padding:56px 0 0">
  <div class="wrap"><div class="answer"><span class="lab">{e(q)}</span><p>{a}</p></div></div>
</section>'''


def sec(eyebrow, title, inner, bg=False, narrow=False):
    style = ' style="background:var(--slate-50)"' if bg else ""
    w = "wrap-narrow" if narrow else "wrap"
    return f'''
<section{style}>
  <div class="{w}">
    <div class="sec-head"><span class="eyebrow">{eyebrow}</span><h2 class="h">{title}</h2></div>
    {inner}
  </div>
</section>'''


def faq_block(items):
    ds = "".join(f'<details><summary>{e(q)}</summary><div class="a">{e(a)}</div></details>'
                 for q, a in items)
    return sec("FAQ", "자주 묻는 것",
               f'<div class="faq" style="max-width:720px;margin:0 auto">{ds}</div>', narrow=True)


# ---------------------------------------------------------------- 렌더

def render_usecase(u, others):
    pts = "".join(f'<div class="card"><h3>{e(t)}</h3><p class="cd">{e(d)}</p></div>' for t, d in u["points"])
    fls = "".join(f'<div class="step"><span class="sn wn c{i}">{i+1}</span><div><h4>{e(t)}</h4><p>{e(d)}</p></div></div>'
                  for i, (t, d) in enumerate(u["flows"]))
    rel = "".join(f'<a href="/use-cases/{o["slug"]}/" class="ind"><h4>{o["nav"]}</h4></a>' for o in others)
    return (head(f'{u["nav"]} AI 자동화 | 지오테스', u["sub"], f'{SITE}/use-cases/{u["slug"]}/', u["faq"])
      + header()
      + hero("Use case", u["h1"], u["sub"],
             '<a href="/">홈</a> · <a href="/use-cases/">활용사례</a> · ' + e(u["nav"]))
      + answer_box(u["aq"], u["a"])
      + sec("Outcomes", "무엇이 달라지나요", f'<div class="cards3">{pts}</div>')
      + sec("Workflow", "통화는 이렇게 흘러갑니다", f'<div class="steps">{fls}</div>', bg=True)
      + faq_block(u["faq"])
      + sec("More", "다른 활용사례", f'<div class="ind-grid">{rel}</div>', bg=True)
      + FOOTER)


UC_NAV = {}   # main()에서 채움. 활용사례 slug -> 이름


def render_industry(i, others):
    pains = "".join(f'<div class="card"><h3>{e(t)}</h3><p class="cd">{e(d)}</p></div>'
                    for t, d in i["pains"])

    calls = "".join(f'<li>{e(c)}</li>' for c in i["calls"])
    calls_html = (f'<ul class="svc-list" style="grid-template-columns:1fr 1fr;display:grid;'
                  f'gap:11px 28px;max-width:760px;margin:0 auto">{calls}</ul>')

    setup = "".join(f'<div class="step"><span class="sn wn c{n}">{n+1}</span>'
                    f'<div><h4>{e(t)}</h4><p>{e(d)}</p></div></div>'
                    for n, (t, d) in enumerate(i["setup"]))

    ucs = "".join(f'<a href="/use-cases/{s}/" class="ind"><h4>{UC_NAV.get(s, s)}</h4></a>'
                  for s in i["ucs"])
    rel = "".join(f'<a href="/industries/{o["slug"]}/" class="ind"><h4>{o["nav"]}</h4></a>'
                  for o in others)

    return (head(f'{i["nav"]} 콜센터·고객관리 구축 | 지오테스', i["sub"],
                 f'{SITE}/industries/{i["slug"]}/', i["faq"])
      + header()
      + hero("Industry", i["h1"], i["sub"],
             '<a href="/">홈</a> · <a href="/industries/">업종별</a> · ' + e(i["nav"]))
      + answer_box(f'{i["nav"]}은 전화 업무가 어떻게 다른가요?', i["why"])
      + sec("Pain", "이런 상황이 반복됩니다", f'<div class="cards3">{pains}</div>')
      + sec("Calls", "이런 문의가 들어옵니다", calls_html, bg=True)
      + sec("Setup", "그래서 이렇게 구성합니다", f'<div class="steps">{setup}</div>')
      + sec("Use cases", "함께 많이 쓰는 활용사례", f'<div class="ind-grid">{ucs}</div>', bg=True)
      + faq_block(i["faq"])
      + sec("More", "다른 업종", f'<div class="ind-grid">{rel}</div>', bg=True)
      + FOOTER)


def hub(eyebrow, h1, sub, cards, canonical, title, desc):
    return (head(title, desc, canonical) + header()
      + hero(eyebrow, h1, sub, '<a href="/">홈</a> · ' + e(h1.replace("<br>", " ")))
      + f'<section style="padding:56px 0 76px"><div class="wrap"><div class="cards2">{cards}</div></div></section>'
      + FOOTER)


# ---------------------------------------------------------------- 단독 페이지

def page_pricing():
    body = '''
<div class="table-scroll">
  <table class="t">
    <thead><tr><th>항목</th><th>내용</th><th>과금</th></tr></thead>
    <tbody>
      <tr><th>시스템 구축</th><td class="typ">IP 교환기 · 상담 프로그램 · 설치 · 교육</td><td class="price">1회</td></tr>
      <tr><th>회선 이용료</th><td class="typ">인터넷전화 회선, 대표번호, 통화료</td><td class="price">월</td></tr>
      <tr><th>유지보수</th><td class="typ">장애 대응, 기능 수정, 정기 점검</td><td class="price">별도 계약</td></tr>
      <tr><th>부가서비스</th><td class="typ">문자, 팩스, 영상상담 등 선택 항목</td><td class="price">선택</td></tr>
    </tbody>
  </table>
</div>
<p class="note">※ 쓰지 않는 기능은 빼고 산정합니다.</p>

<h3 style="font-size:18px;font-weight:800;margin:34px 0 12px">금액이 어느 정도인지 감을 잡으시려면</h3>
<div class="table-scroll">
  <table class="t">
    <thead><tr><th>구분</th><th>임대형 2좌석 기준</th></tr></thead>
    <tbody>
      <tr><th>처음 한 번</th><td class="price">300,000원</td></tr>
      <tr><th>매달</th><td class="price">100,000원</td></tr>
      <tr><th>좌석을 더 늘리면</th><td class="typ">좌석당 비용만 추가</td></tr>
    </tbody>
  </table>
</div>
<p class="note">
  설치비가 포함된 금액이며 부가세는 별도입니다. <b>실제 진행된 견적을 예시로 옮긴 것</b>이라
  구성과 규모에 따라 달라집니다. 회선 이용료와 통화료는 별도이며, 쓰시는 회선 조건에 따라 산정합니다.
  <br>기존에 쓰시던 고객관리 프로그램이 있으면 그대로 두고 전화 기능만 붙일 수 있습니다.
</p>'''
    split = '''
<p class="lead-txt" style="text-align:center;max-width:640px;margin:0 auto 32px">
  같은 콜센터를 놓아도 3년 뒤 총액이 갈립니다.<br>
  갈리는 지점은 <b>인원이 늘 때 무엇이 따라 오르느냐</b>입니다.
</p>
<div class="table-scroll">
  <table class="t">
    <thead><tr><th>항목</th><th>흔한 방식</th><th>지오테스</th></tr></thead>
    <tbody>
      <tr><th>좌석이 늘 때</th><td class="typ">좌석 비용 + 기능별 사용료</td><td class="typ">좌석 비용만</td></tr>
      <tr><th>오토콜·클릭투콜</th><td class="typ">기능별 추가</td><td class="price">무료</td></tr>
      <tr><th>블랙리스트·부재중 알림</th><td class="typ">기능별 추가</td><td class="price">무료</td></tr>
      <tr><th>통화 후 문자·알림톡</th><td class="typ">기능별 추가</td><td class="price">무료</td></tr>
      <tr><th>부분 녹취·통화 종료 추적</th><td class="typ">기능별 추가</td><td class="price">무료</td></tr>
    </tbody>
  </table>
</div>
<p class="note">
  좌석이 늘면 좌석 비용은 어디서든 늘어납니다. 갈리는 것은 <b>그 위에 붙는 기능 값</b>입니다.
  기능을 하나씩 옵션으로 파는 방식이라면 쓰면 쓸수록 매달 나가는 금액이 올라갑니다.
  지오테스는 아래 12가지 기능을 <b>추가 비용 없이</b> 드립니다.
</p>

<div class="answer" style="margin-top:40px">
  <span class="lab">몇 퍼센트 절감된다고 말하지 않는 이유</span>
  <p>
    절감률은 지금 무엇을 쓰고 계신지에 따라 완전히 달라집니다.
    같은 시스템을 놓아도 어떤 곳은 30%가 줄고 어떤 곳은 거의 그대로입니다.
    <span class="hl">그래서 저희는 몇 퍼센트라고 먼저 말하지 않습니다.</span>
    지금 내고 계신 항목을 함께 보고, 어느 항목이 없어지고 어느 항목이 남는지 계산해서 알려드립니다.
    계산이 맞지 않으면 도입하지 않으시는 편이 낫습니다.
  </p>
</div>'''

    free12 = '''
<p class="lead-txt" style="text-align:center;max-width:660px;margin:0 auto 32px">
  다른 곳에서는 기능마다 값을 매기는 항목들입니다.<br>
  지오테스는 <b>추가 비용 없이</b> 함께 드립니다.
</p>
<div class="cards2">
  <div class="card">
    <span class="svc-tag">영업 자동화</span>
    <h3>발신하는 일을 시스템이 대신합니다</h3>
    <ul class="svc-list">
      <li><b>오토콜</b> — 명단에 대량으로 자동 발신</li>
      <li><b>클릭투콜</b> — 화면의 번호를 눌러 즉시 발신 (API·엑셀 연동)</li>
      <li><b>스케줄 발신</b> — 정해둔 시간에 자동으로 거는 API 연동</li>
    </ul>
  </div>
  <div class="card">
    <span class="svc-tag">브랜드 구분</span>
    <h3>어느 광고에서 온 전화인지 구분합니다</h3>
    <ul class="svc-list">
      <li><b>착신번호별 구분</b> — 번호마다 다른 안내 음성이 나갑니다</li>
      <li><b>브랜드별 발신번호</b> — 걸 때 표시되는 번호를 나눕니다</li>
    </ul>
    <p class="cd" style="margin-top:12px">브랜드나 광고를 여러 개 돌리는 곳에서 성과를 나눠 볼 수 있습니다.</p>
  </div>
  <div class="card">
    <span class="svc-tag">상담 품질</span>
    <h3>상담원을 보호하고 기록을 남깁니다</h3>
    <ul class="svc-list">
      <li><b>필수 안내 자동 재생</b> — 약관처럼 꼭 읽어야 하는 내용을 통화 중 자동으로</li>
      <li><b>욕설 방지 안내</b> — 상담원이 혼자 감당하지 않게</li>
      <li><b>통화 종료 추적</b> — 누가 먼저 끊었는지 남습니다</li>
    </ul>
  </div>
  <div class="card">
    <span class="svc-tag">고객 관리</span>
    <h3>놓치는 것과 하지 말아야 할 것을 관리합니다</h3>
    <ul class="svc-list">
      <li><b>블랙리스트</b> — 수신 거부 고객을 자동으로 걸러냅니다</li>
      <li><b>통화 후 자동 문자·알림톡</b> — 안내를 빠뜨리지 않습니다</li>
      <li><b>부재중 자동 알림</b> — 못 받은 전화를 그냥 넘기지 않습니다</li>
      <li><b>부분 녹취</b> — 필요한 구간만 골라 남깁니다</li>
    </ul>
  </div>
</div>

<div class="table-scroll" style="margin-top:34px">
  <table class="t">
    <thead><tr><th>필요하실 때 추가하는 것</th><th>내용</th></tr></thead>
    <tbody>
      <tr><th>AI 통화요약</th><td class="typ">녹취를 글로 풀고 요점을 정리, 상담 자동 평가</td></tr>
      <tr><th>콜백 API 연동</th><td class="typ">부재중 회신 요청을 외부 시스템과 주고받기</td></tr>
      <tr><th>DB API 연동</th><td class="typ">사내 데이터베이스와 실시간 조회·기록</td></tr>
      <tr><th>실시간 API 연동</th><td class="typ">통화 중 발생하는 정보를 즉시 다른 시스템으로</td></tr>
    </tbody>
  </table>
</div>
<p class="note">위 네 가지는 선택 항목입니다. 필요하신 것만 넣습니다.</p>'''

    faq = [("절감률을 몇 퍼센트라고 말해주실 수 있나요?", "지금 쓰시는 구성과 요금을 봐야 계산이 됩니다. 항목별로 무엇이 없어지고 무엇이 남는지 정리해서 알려드립니다. 근거 없이 몇 퍼센트라고 말씀드리지 않습니다."),
           ("상담사가 늘면 비용이 얼마나 오르나요?", "회선과 관련된 항목은 늘어납니다. 상담 프로그램은 구축에 포함되어 있어 인원에 따라 따로 오르지 않습니다."),
           ("금액이 왜 공개되어 있지 않나요?", "상담 인원, 회선 수, 필요한 기능에 따라 차이가 커서 일률적인 표로는 오히려 잘못된 기대를 만듭니다."),
           ("상담 프로그램은 따로 사야 하나요?", "고객관리(CRM)·녹취·통계는 시스템에 함께 들어갑니다. 쓰시던 CRM이 있으면 그것을 그대로 두고 전화 기능만 붙이는 방식도 가능합니다."),
           ("나중에 기능을 추가하면 다시 구축해야 하나요?", "같은 시스템 안에서 기능을 켜는 방식이라 재구축은 없습니다.")]
    return (head("요금 구조 | 콜센터 구축 비용 | 지오테스",
                 "콜센터 구축 비용이 어떤 항목으로 구성되는지 정리했습니다. 시스템 구축, 회선 이용료, 유지보수, 부가서비스.",
                 f"{SITE}/pricing/", faq)
      + header()
      + hero("Pricing", "비용은 이렇게<br>구성됩니다",
             "규모와 구성에 따라 달라지지만, 항목 자체는 단순합니다.", '<a href="/">홈</a> · 요금')
      + sec("Structure", "네 가지 항목", body, narrow=True)
      + sec("Compare", "3년 뒤 총액이 갈리는 지점", split, bg=True, narrow=True)
      + sec("Included", "12가지 기능이 무상으로 제공됩니다", free12)
      + faq_block(faq) + FOOTER)


# 고객사 로고 — 현 사이트 customers.php 이미지를 그대로 가져옴
# alt 텍스트를 넣는 이유: 이미지 안의 글자는 검색엔진과 AI가 읽지 못합니다.
LOGOS = [
 ("icon1",  "KT olleh"),          ("icon2",  "LG U+"),
 ("icon3",  "SK네트웍스"),          ("icon4",  "울산광역시 교육연구정보원"),
 ("icon5",  "문깡 잉글리시스쿨"),     ("icon6",  "YBM시사닷컴"),
 ("icon7",  "아발론교육"),           ("icon8",  "정철"),
 ("icon9",  "넥스트네트워크"),        ("icon10", "kt cs"),
 ("icon11", "스피크케어"),
 ("icon13", "바이오인프라"),         ("icon14", "카누다"),
 ("icon15", "웰컴론"),              ("icon17", "축산물안전관리인증원"),
 ("icon18", "엠피온"),              ("icon19", "홍국F&B"),
 ("icon21", "도움과나눔"),
]


# 업종별 고객사 — 로고가 있는 곳과 제안서에만 있던 곳을 합친 목록
CLIENTS = [
 ("통신·IT", ["KT olleh", "LG U+", "SK네트웍스", "kt cs", "넥스트네트워크",
             "LG상사", "엠피온"]),
 ("교육", ["YBM시사닷컴", "정철", "아발론교육", "문깡 잉글리시스쿨", "스피크케어",
          "멀티캠퍼스", "스터디맥스", "틴타임즈", "아이보린", "고려대학교"]),
 ("공공·기관", ["울산광역시 교육연구정보원", "축산물안전관리인증원", "의왕도시공사",
              "한국기계산업진흥회", "행복커넥트", "공직메일"]),
 ("제조·유통·서비스", ["삼성SDI 서비스센터", "홍국F&B", "카누다",
                   "바이오인프라", "씨에스렌탈", "다온홈시스", "웰컴론", "도움과나눔"]),
]


def logo_grid():
    figs = "".join(
        f'<figure><img src="/assets/logos/{f}.png" alt="{e(n)}" loading="lazy" decoding="async">'
        f'<figcaption>{e(n)}</figcaption></figure>' for f, n in LOGOS)

    groups = ""
    total = 0
    for cat, names in CLIENTS:
        total += len(names)
        chips = "".join(f'<span>{e(n)}</span>' for n in names)
        groups += (f'<div class="client-row"><h4>{e(cat)}</h4>'
                   f'<div class="chips-ink">{chips}</div></div>')

    return (f'<div class="logos">{figs}</div>'
            f'<div class="client-list">{groups}</div>'
            f'<p class="note">지면에 옮긴 {total}곳 외에도 구축한 곳이 더 있습니다. '
            f'업종이 같은 곳의 사례가 궁금하시면 상담 시 말씀해 주세요.</p>')


def page_cases():
    body = '''
<div class="table-scroll">
  <table class="t">
    <thead><tr><th>업종</th><th>규모</th><th>도입 구성</th><th>해결한 문제</th></tr></thead>
    <tbody>
      <tr><th>제조</th><td>상담 <span class="gb">20</span>석</td><td class="typ">IP교환기 · CRM · 녹취</td><td class="typ">거래처 통화 이력이 담당자 개인 휴대폰에만 남던 문제</td></tr>
      <tr><th>공공</th><td>상담 <span class="gb">35</span>석</td><td class="typ">IPCC · IVR · 전수녹취</td><td class="typ">민원 폭주 시간대 대기 이탈과 담당자 개인번호 노출</td></tr>
      <tr><th>쇼핑몰</th><td>상담 <span class="gb">12</span>석</td><td class="typ">CRM · 채팅상담 · 문자</td><td class="typ">전화·카카오·문자 문의가 서로 다른 창에 흩어지던 문제</td></tr>
      <tr><th>금융</th><td>상담 <span class="gb">60</span>석</td><td class="typ">IPCC · 스킬 호분배 · 통계</td><td class="typ">상담원별 편차와 녹취 보관 규정 대응</td></tr>
    </tbody>
  </table>
</div>
<p class="note">※ 위 구성 내역은 예시입니다. 실제 사례로 교체 예정입니다.</p>'''
    return (head("구축 사례 | 120여 곳의 컨택센터 | 지오테스",
                 "2006년부터 120여 곳의 컨택센터를 구축했습니다. 업종과 규모, 도입 구성으로 정리했습니다.",
                 f"{SITE}/cases/")
      + header()
      + hero("Cases", "120여 곳이<br>이렇게 쓰고 있습니다",
             "통신사부터 교육, 유통, 공공기관까지.<br>전화가 멈추면 안 되는 곳들과 일해 왔습니다.",
             '<a href="/">홈</a> · 구축사례')
      + sec("Clients", "이런 곳들과 일했습니다", logo_grid())
      + sec("Records", "업종별 구축 내역", body, bg=True) + FOOTER)


# 연혁 — (연도, 제목, 설명, 강조여부)
# TODO 확인: 연도와 항목을 사장님께 받아 채울 것. 아래는 확인된 것만 넣은 상태.
HISTORY = [
 ("2006", "법인 설립, KT와 인터넷전화 계약",
  "법인을 세우고 KT와 VoIP 계약을 맺으며 시작했습니다. 같은 해 CTI와 녹취 시스템을 도입했습니다.", True),
 ("2007", "녹취 시스템 필리핀 독점 계약",
  "해외 녹취 솔루션의 필리핀 독점 계약을 맺고, 국내 교육기업 등 10여 곳에 녹취를 공급했습니다.", False),
 ("2008", "자체 녹취 시스템 개발",
  "남의 제품을 파는 데서 <b>직접 만드는 쪽</b>으로 넘어온 해입니다. "
  "이때부터 고객사 요구를 그 자리에서 반영할 수 있게 됐습니다.", True),
 ("2009", "한국 법인 설립, 자체 학습관리 시스템 개발",
  "국내 법인을 세우고 교육기업용 시스템까지 범위를 넓혔습니다.", False),
 ("2011", "통신사 제휴, 전화영어 ARS 시스템 개발",
  "통신사와 전략적 제휴를 맺고, 정해진 시간에 통화가 몰리는 전화영어 서비스용 ARS를 개발했습니다.", False),
 ("2013", "필리핀 클락 콜센터 설립 (1,200㎡)",
  "직접 콜센터를 세워 운영했습니다. <b>파는 쪽이 아니라 쓰는 쪽에서</b> 무엇이 불편한지 겪어 본 경험입니다. "
  "같은 해 자체 CTI 솔루션을 개발했습니다.", True),
 ("2015", "판매법인 설립, 대기업 서비스센터 구축",
  "개발과 판매를 나눴습니다. 대기업 서비스센터와 공공기관 인증원의 컨택센터를 구축했습니다.", False),
 ("2016~2018", "대학·공공기관·통신 자회사로 확대",
  "고려대학교, 의왕도시공사, KT계열사 등으로 넓혔습니다. 2018년 두 법인을 합병했습니다.", False),
 ("2019~2022", "교육·렌탈·공공 분야 구축 이어감",
  "멀티캠퍼스, 한국기계산업진흥회, 행복커넥트, 스터디맥스 등의 컨택센터를 구축했습니다.", False),
 ("2026", "AI 컨택센터 제공 시작",
  "AI 통화요약과 AI 응대, 보이는 ARS를 서비스에 더했습니다. "
  "쓰시던 시스템을 걷어내지 않고 기능만 얹는 방식으로 적용합니다.", True),
]


def page_about():
    body = '''
<div class="table-scroll">
  <table class="t">
    <thead><tr><th>구분</th><th>내용</th></tr></thead>
    <tbody>
      <tr><th>법인명</th><td class="typ">㈜지오테스솔루션 (2008년 9월 10일)</td></tr>
      <tr><th>사업 시작</th><td class="typ">2006년</td></tr>
      <tr><th>대표이사</th><td class="typ">신명남</td></tr>
      <tr><th>사업자등록번호</th><td class="typ">144-81-03835</td></tr>
      <tr><th>주소</th><td class="typ">경기 고양시 덕양구 삼막3길 5 고양삼송듀클래스 904호</td></tr>
    </tbody>
  </table>
</div>'''
    biz = '''<div class="cards3">
      <div class="card"><h3>인터넷전화(VoIP)</h3><p class="cd">기업 대상 인터넷전화 서비스와 VPN.</p></div>
      <div class="card"><h3>IP-PBX · IP-IVR</h3><p class="cd">대형 서버형과 중소형 임베디드 교환기 개발.</p></div>
      <div class="card"><h3>통합 IPCC</h3><p class="cd">콜센터 솔루션 구축과 호스팅·임대 서비스.</p></div>
      <div class="card"><h3>콜센터 애플리케이션</h3><p class="cd">CRM, 녹취, 통계 등 상담 프로그램 개발.</p></div>
      <div class="card"><h3>Centrex Switch</h3><p class="cd">통신사업자용 VoIP 및 SIP Proxy 시스템.</p></div>
      <div class="card"><h3>온라인 마케팅</h3><p class="cd">마케팅 프로그램 개발과 대행.</p></div>

    </div>'''
    terms = '''<div class="cards3">
      <div class="card">
        <span class="svc-tag">회선</span>
        <h3>통신 3사와 모두 제휴</h3>
        <p class="cd">KT, LG U+, SK브로드밴드. 한 곳에 묶지 않고 조건이 맞는 쪽을 골라 드립니다.
          중복으로 열어 두면 한쪽에 문제가 생겨도 통화가 끊기지 않습니다.</p>
      </div>
      <div class="card">
        <span class="svc-tag">계약</span>
        <h3>약정 기간이 없습니다</h3>
        <p class="cd">몇 년을 묶어두고 중간에 그만두면 위약금을 물리는 방식으로 팔지 않습니다.
          쓰다가 맞지 않으면 그만두실 수 있어야 저희도 계속 잘해야 합니다.</p>
      </div>
      <div class="card">
        <span class="svc-tag">장애 대비</span>
        <h3>365일 24시간,<br>전화가 멈추지 않게</h3>
        <p class="cd">시스템을 이중으로 둡니다. 문제가 생기면 백업 서버로 자동으로 넘어갑니다.
          회선도 통신사 두 곳 이상에 열어 두면 한쪽에 장애가 나도 통화는 이어집니다.
          <b>전화가 멈추면 매출이 멈추는 곳</b>을 기준으로 구성합니다.</p>
      </div>
    </div>'''

    return (head("회사소개 | ㈜지오테스솔루션 · 지오테스",
                 "2006년부터 인터넷전화와 컨택센터 솔루션을 직접 개발해 온 ㈜지오테스솔루션의 회사 정보입니다.",
                 f"{SITE}/about/")
      + header()
      + hero("About", "2006년부터<br>이 일만 했습니다",
             "회선을 공급하면서 교환기와 상담 프로그램까지 직접 만드는 곳은 많지 않습니다.",
             '<a href="/">홈</a> · 회사소개')
      + sec("Business", "하는 일", biz)
      + sec("Terms", "이렇게 거래합니다", terms, bg=True)
      + sec("History", "걸어온 길", hist_html())
      + sec("Company", "회사 정보", body, narrow=True) + FOOTER)


def hist_html():
    # 설명에는 <b> 같은 강조를 직접 씁니다. 연도·제목만 escape 합니다.
    rows = "".join(
      f'<div class="hist-item{" on" if on else ""}">'
      f'<div class="hist-yr">{e(y)}</div>'
      f'<div class="hist-body"><h4>{e(t)}</h4><p>{d}</p></div></div>'
      for y, t, d, on in HISTORY)
    return (f'<div class="hist">{rows}</div>'
            f'<p class="note">2006년 창업 이후 지금까지 이어온 기록입니다. '
            f'회사 이름과 법인 형태는 바뀌었지만 하는 일은 한 가지였습니다.</p>')


def page_demo():
    import mocks
    order = ["consult", "recording", "dashboard", "ai_summary", "ivr_tree", "stats", "stt"]
    blocks = ""
    for n, key in enumerate(order):
        title, lead, fn = mocks.ALL[key]
        bg = ' style="background:var(--slate-50)"' if n % 2 else ""
        blocks += f'''
<section{bg}>
  <div class="wrap">
    <div class="sec-head">
      <span class="eyebrow">Screen {n + 1:02d}</span>
      <h2 class="h">{title}</h2>
      <p class="lead-txt">{lead}</p>
    </div>
    <div style="max-width:820px;margin:0 auto">{fn()}</div>
  </div>
</section>'''

    faq = [("실제 화면과 같은가요?",
            "구성과 흐름은 같습니다. 표시 항목과 명칭은 업무에 맞게 바꾸기 때문에 도입하시면 회사에 맞는 형태로 나옵니다."),
           ("직접 써 볼 수 있나요?",
            "상담 시 실제 화면으로 시연해 드립니다. 쓰시는 업무를 알려주시면 그 상황으로 보여드립니다."),
           ("화면을 우리 업무에 맞게 바꿀 수 있나요?",
            "저희가 직접 개발한 시스템이라 항목과 배치, 업무 흐름을 요청대로 수정합니다."),
           ("모바일에서도 같은 화면인가요?",
            "웹 기반이라 사무실 밖에서도 같은 기능을 씁니다. 화면은 기기 크기에 맞춰 배치가 달라집니다.")]

    demo_box = '''
<div class="answer" style="max-width:820px;margin:0 auto">
  <span class="lab">직접 눌러보고 싶으시면</span>
  <p>
    아래 화면 중 일부는 실제 화면이고, 일부는 구성을 재현한 것입니다. <b>진짜 시스템을 눌러보고 싶으시면</b>
    체험용 계정을 열어 두었습니다. 신청이나 결제 없이 바로 들어가실 수 있습니다.
  </p>
  <div class="table-scroll" style="margin-top:16px">
    <table class="t">
      <tbody>
        <tr><th>주소</th><td class="typ"><a class="inlink" href="http://v1.070crm.com/login?demo" target="_blank" rel="noopener">v1.070crm.com/login?demo</a></td></tr>
        <tr><th>아이디</th><td class="typ">user</td></tr>
        <tr><th>비밀번호</th><td class="typ">0000</td></tr>
      </tbody>
    </table>
  </div>
  <p class="note" style="text-align:left">체험용 계정이라 여러 분이 함께 씁니다. 실제 고객 정보는 들어 있지 않습니다.</p>
</div>'''

    return (head("화면 예시 | 상담화면·녹취·현황판·AI요약 | 지오테스",
                 "지오테스 관리자 화면이 실제로 어떻게 생겼는지 보여드립니다. 상담 화면, 통화 녹취, 실시간 현황판, AI 통화요약, ARS 시나리오, 통계. 체험 계정으로 직접 눌러볼 수도 있습니다.",
                 f"{SITE}/demo/", faq)
      + header()
      + hero("Screens", "말로 설명하는 것보다<br>보시는 편이 빠릅니다",
             "관리자 화면이 실제로 어떻게 생겼는지 정리했습니다.<br>계정 없이 이 페이지에서 바로 보실 수 있습니다.",
             '<a href="/">홈</a> · 화면 예시')
      + '<section style="padding:52px 0 0"><div class="wrap">' + demo_box + '</div></section>'
      + blocks
      + faq_block(faq) + FOOTER)


def page_contact():
    form = '''
<div class="lead-wrap">
  <form class="lead">
    <h3>무료 상담 신청</h3>
    <p class="ls">평일 09:00 – 18:00 · ''' + TEL + '''</p>
    <label for="c-company">회사명</label><input type="text" id="c-company" name="company" required>
    <label for="c-name">담당자</label><input type="text" id="c-name" name="name" required>
    <label for="c-tel">연락처</label><input type="tel" id="c-tel" name="tel" required>
    <label for="c-size">상담 인원</label>
    <select id="c-size" name="size"><option>5석 이하</option><option>6 – 20석</option><option>21 – 50석</option><option>51석 이상</option><option>아직 모르겠습니다</option></select>
    <label for="c-memo">문의 내용</label><textarea id="c-memo" name="memo"></textarea>
    <div class="agree"><input type="checkbox" id="c-agree" name="agree" value="1" required>
      <label for="c-agree" style="margin:0;font-weight:500">상담을 위한 개인정보 수집·이용에 동의합니다</label></div>
    <button type="submit" class="btn btn-brand">상담 신청하기</button>
  </form>
</div>
<p class="note" style="text-align:center">보내주신 내용은 상담 목적으로만 쓰이며, 처리 후 보관 기간이 지나면 지웁니다.</p>'''
    info = '''<div class="contact-one">
      <span class="contact-lab">고객센터</span>
      <a class="contact-tel" href="tel:''' + TEL_RAW + '''">''' + TEL + '''</a>
      <p class="contact-meta"><a href="mailto:help@ziotes.com">help@ziotes.com</a><span class="dot-sep">·</span>평일 09:00 – 18:00</p>
      <p class="contact-note">문의도, 장애가 나도 연락할 곳은 여기 하나입니다.</p>
    </div>'''
    return (head("상담 문의 | 지오테스",
                 "콜센터 구축 상담은 무료입니다. 현황을 보고 필요한 구성만 담아 제안해 드립니다.",
                 f"{SITE}/contact/")
      + header()
      + hero("Contact", "무엇이 불편하신지만<br>알려주세요",
             "현황을 먼저 보고 필요한 구성만 담아 제안해 드립니다. 상담은 무료입니다.",
             '<a href="/">홈</a> · 상담문의')
      + sec("Channels", "연락처", info)
      + sec("Form", "상담 신청", form, bg=True, narrow=True) + FOOTER)


# ---------------------------------------------------------------- 실행

def main():
    print("나머지 페이지 생성")

    uc_cards = "".join(
      f'<a href="/use-cases/{u["slug"]}/" class="card" style="display:block">'
      f'<span class="svc-tag">Use case</span><h3>{u["nav"]}</h3>'
      f'<p class="cd">{e(u["sub"])}</p></a>' for u in USE_CASES)
    write(os.path.join(DIST, "use-cases", "index.html"),
          hub("Use cases", "어떤 전화 업무를<br>맡기시겠습니까",
              "걸려오는 전화부터 걸어야 하는 전화까지.", uc_cards,
              f"{SITE}/use-cases/", "활용사례 | 전화 업무 자동화 | 지오테스",
              "고객 응대, 예약·접수, 대표번호 안내, 아웃바운드 영업, 리마인드, 미납 안내, 설문조사."), 1)
    for u in USE_CASES:
        others = [o for o in USE_CASES if o["slug"] != u["slug"]][:4]
        write(os.path.join(DIST, "use-cases", u["slug"], "index.html"), render_usecase(u, others), 2)

    UC_NAV.update({u["slug"]: u["nav"] for u in USE_CASES})

    ind_cards = "".join(
      f'<a href="/industries/{i["slug"]}/" class="card" style="display:block">'
      f'<span class="svc-tag">Industry</span><h3>{i["nav"]}</h3>'
      f'<p class="cd">{e(i["sub"])}</p>'
      f'<ul class="svc-list">'
      + "".join(f'<li>{e(t)}</li>' for t, _ in i["setup"][:3])
      + f'</ul></a>' for i in INDUSTRIES)
    write(os.path.join(DIST, "industries", "index.html"),
          hub("Industries", "업종마다<br>필요한 것이 다릅니다",
              "120여 곳을 구축하며 쌓인 업종별 기본 구성이 있습니다.", ind_cards,
              f"{SITE}/industries/", "업종별 콜센터 구축 | 지오테스",
              "병원, 공공, 금융, 교육, 쇼핑몰, 제조, 유통, 법무, 심리상담, 분양, 렌탈."), 1)
    for i in INDUSTRIES:
        others = [o for o in INDUSTRIES if o["slug"] != i["slug"]][:4]
        write(os.path.join(DIST, "industries", i["slug"], "index.html"), render_industry(i, others), 2)

    write(os.path.join(DIST, "demo", "index.html"), page_demo(), 1)
    write(os.path.join(DIST, "pricing", "index.html"), page_pricing(), 1)
    write(os.path.join(DIST, "cases", "index.html"), page_cases(), 1)
    write(os.path.join(DIST, "about", "index.html"), page_about(), 1)
    write(os.path.join(DIST, "contact", "index.html"), page_contact(), 1)

    total = 2 + len(USE_CASES) + len(INDUSTRIES) + 5
    print(f"\n총 {total}개 생성 완료")


if __name__ == "__main__":
    main()
