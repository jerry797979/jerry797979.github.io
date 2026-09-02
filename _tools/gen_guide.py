# -*- coding: utf-8 -*-
"""
지오테스 가이드(정보성 원고) 생성기
  python _tools/gen_guide.py
  → dist/guide/index.html + dist/guide/{slug}/index.html

문서형 스타일(nova-post.css)을 씁니다. 랜딩형과 다릅니다.
새 글은 GUIDES 목록에 항목만 추가하면 됩니다.

원칙
- 어려운 말을 먼저 쓰지 않습니다. 쉬운 말로 쓰고 괄호에 용어를 답니다.
- 각 글 맨 위에 답변 박스를 둡니다. AI 검색이 그 문단을 인용해 갑니다.
- 남의 글을 옮기지 않습니다. 구조만 참고하고 문장은 새로 씁니다.
"""
import os, sys, html

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_solution import relativize, SITE, OG_BASE, TEL, TEL_RAW, header

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
OUT = os.path.join(ROOT, "dist", "guide")

e = lambda s: html.escape(str(s), quote=True)
jstr = lambda s: '"%s"' % str(s).replace("\\", "\\\\").replace('"', '\\"')

# ---------------------------------------------------------------- 원고

GUIDES = [
{
 "slug": "ipcc",
 "cat": "콜센터 기초",
 "title": "IPCC가 뭔가요? 콜센터 구축을 처음 알아보는 분들을 위한 설명",
 "desc": "IP-PBX, CTI, IVR, 녹취, 상담화면. 콜센터 견적서에 나오는 말들을 쉬운 말로 풀었습니다. 전화 한 통이 상담이 되기까지의 과정과 구축 절차, 업체 고르는 기준까지.",
 "h1": "IPCC가 뭔가요?",
 "sub": "콜센터 견적서를 처음 받아보면 모르는 말이 절반입니다.<br>그 말들이 실제로 무슨 일을 하는지부터 정리했습니다.",
 "answer_q": "IPCC가 무엇인가요?",
 "answer": "IPCC는 <b>인터넷 전화로 돌아가는 콜센터 시스템</b>입니다. "
   "전화를 받아 나눠주는 장치, 자동 안내, 상담사에게 배분하는 기능, 상담 화면, 녹취를 "
   "<span class='hl'>하나로 묶어 놓은 것</span>을 말합니다. "
   "예전에는 이 다섯 가지를 각각 다른 장비로 샀지만, 지금은 인터넷 회선 위에서 한 시스템으로 묶습니다. "
   "그래서 회선을 늘리는 데 공사가 필요 없고, 사무실을 옮겨도 번호가 그대로입니다.",
 "body": [
  ("전화 한 통이 상담이 되기까지", [
    ("p", "고객이 전화를 겁니다. 그 한 통이 상담사에게 닿기까지 다섯 단계를 지납니다. "
          "견적서에 적힌 낯선 말들은 대부분 이 다섯 단계 중 하나를 가리킵니다."),
    ("table", [
      ["단계", "견적서에 쓰이는 말", "실제로 하는 일"],
      ["1", "IP-PBX (교환기)", "걸려온 전화를 받아서 어디로 보낼지 나눠주는 장치입니다. 회사 전화의 중심입니다."],
      ["2", "IVR / ARS (자동안내)", "\"상담원 연결은 1번\" 하는 안내입니다. 사람이 받지 않아도 되는 문의를 여기서 거릅니다."],
      ["3", "CTI (지능형 분배)", "이 전화를 누구에게 넘길지 정합니다. 놀고 있는 사람, 그 업무를 잘하는 사람, 지난번에 응대했던 사람을 골라 연결합니다."],
      ["4", "CRM (상담화면)", "전화가 연결되는 순간 상담사 화면에 고객 정보가 뜹니다. 누구인지 물어보지 않아도 됩니다."],
      ["5", "녹취", "통화 내용을 저장합니다. 나중에 확인이 필요할 때 찾아 듣습니다."],
    ]),
    ("p", "이 다섯이 따로 놀면 콜센터가 아닙니다. 전화는 오는데 누구 화면에도 안 뜨거나, "
          "화면은 뜨는데 녹취가 안 되는 상태가 됩니다. <strong>다섯 개가 서로 연결돼야 비로소 콜센터입니다.</strong>"),
    ("callout", "이 중에서 가장 자주 문제가 되는 것은 3번 CTI입니다. "
                "전화가 몰릴 때 누구에게 넘길지 정하는 기준이 여기서 나오기 때문입니다. "
                "대기 시간이 길어지는 것도, 특정 상담사에게만 전화가 몰리는 것도 대부분 이 부분의 문제입니다."),
  ]),
  ("구축은 어떻게 진행되나요", [
    ("p", "보통 여섯 단계로 진행합니다. 규모에 따라 다르지만 한 달에서 세 달 정도 걸립니다."),
    ("list", [
      "<strong>요구 정리</strong> — 지금 전화를 몇 명이 받는지, 무엇이 불편한지 확인합니다.",
      "<strong>설계와 견적</strong> — 필요한 구성만 골라 제안합니다. 안 쓰는 기능은 빼야 합니다.",
      "<strong>설치</strong> — 회선을 열고 시스템을 올립니다.",
      "<strong>연동</strong> — 쓰시던 사내 시스템과 상담 화면을 연결합니다.",
      "<strong>시험 운영</strong> — 일부 인원으로 먼저 써 봅니다.",
      "<strong>오픈과 운영</strong> — 전체로 넓히고 계속 손봅니다.",
    ]),
    ("p", "기간을 좌우하는 것은 장비 설치가 아니라 <strong>4번 연동</strong>입니다. "
          "기존에 쓰던 주문 시스템이나 고객 관리 프로그램과 상담 화면을 어디까지 연결할지, "
          "이 범위를 처음에 정하지 않으면 일정이 계속 밀립니다. "
          "견적 단계에서 <strong>연동 범위를 문서로 못 박아 두는 것</strong>이 안전합니다."),
  ]),
  ("업체를 고를 때 확인할 네 가지", [
    ("p", "콜센터는 한 번 깔면 몇 년을 씁니다. 가격표만 보고 정하면 나중에 바꾸기가 어렵습니다. "
          "다음 네 가지는 계약 전에 확인하시는 편이 좋습니다."),
    ("h3", "1. 직접 만든 것인가, 사 와서 파는 것인가"),
    ("p", "교환기와 상담 프로그램을 <strong>직접 개발한 회사</strong>는 화면 항목 하나를 바꿔달라고 하면 그 자리에서 고칩니다. "
          "외국 제품을 사 와서 파는 회사는 본사에 확인을 요청해야 하고, 대개 몇 주가 걸립니다. "
          "업무가 조금이라도 특수하다면 이 차이가 크게 벌어집니다."),
    ("h3", "2. 회선도 그 회사 것인가"),
    ("p", "이건 잘 안 물어보시는데 <strong>장애가 났을 때 가장 크게 갈리는 부분</strong>입니다. "
          "시스템은 직접 만들었어도 회선은 통신사에서 받아 쓰는 회사가 많습니다. "
          "그러면 전화가 안 될 때 시스템 문제인지 회선 문제인지를 두 회사가 서로 미룹니다. "
          "그동안 전화는 계속 안 됩니다. "
          "<strong>회선까지 직접 공급하는 회사</strong>는 연락할 곳이 한 곳입니다."),
    ("h3", "3. 우리 업종을 해 봤는가"),
    ("p", "업종마다 걸리는 지점이 다릅니다. "
          "병원은 진료 시스템과의 연결, 공공기관은 망 분리, 금융은 녹취 보관 규정이 핵심입니다. "
          "해당 업종 경험이 없으면 그 시행착오를 고객이 떠안게 됩니다."),
    ("h3", "4. 깔고 나서 누가 봐주는가"),
    ("p", "구축보다 그 뒤가 깁니다. 장애가 났을 때 몇 시간 안에 오는지, 담당자가 정해져 있는지, "
          "기능 수정 요청은 어떻게 처리되는지를 <strong>계약 전에 문서로</strong> 받아 두시는 편이 좋습니다."),
  ]),
  ("녹취는 개인정보입니다", [
    ("p", "녹취 파일에는 고객의 목소리와 연락처, 상담 내용이 그대로 들어 있습니다. "
          "그래서 녹음이 되느냐보다 <strong>어디에 저장하고 누가 들을 수 있느냐</strong>가 더 중요합니다."),
    ("list", [
      "<strong>어디에 저장할지</strong> — 클라우드에 둘지, 회사 서버에 직접 둘지 고를 수 있어야 합니다. 규정상 외부 보관이 안 되는 곳이 있습니다.",
      "<strong>얼마나 보관할지</strong> — 업종에 따라 보관 기간이 정해져 있는 경우가 있습니다.",
      "<strong>누가 들을 수 있는지</strong> — 상담사 본인 것만 볼지, 팀장이 전체를 볼지 나눌 수 있어야 합니다.",
    ]),
    ("p", "지오테스는 기본으로 AWS 클라우드에 보관하고, 요청하시면 고객사 서버에 직접 둡니다. "
          "보관 기간과 열람 권한도 구축할 때 함께 정합니다."),
  ]),
  ("비용은 어떻게 구성되나요", [
    ("p", "견적서가 복잡해 보여도 항목은 네 가지입니다."),
    ("table", [
      ["항목", "내용", "언제 내는지"],
      ["시스템 구축", "교환기, 상담 프로그램, 설치, 교육", "처음 한 번"],
      ["회선 이용료", "인터넷전화 회선, 대표번호, 통화료", "매달"],
      ["유지보수", "장애 대응, 기능 수정, 점검", "별도 계약"],
      ["부가서비스", "문자, 팩스, 영상상담 등 고른 것만", "고른 것만"],
    ]),
    ("p", "여기서 자주 새는 부분이 <strong>상담 프로그램 값</strong>입니다. "
          "회사에 따라 상담사 한 명이 늘 때마다 프로그램 사용료를 매달 더 받습니다. "
          "인원이 늘수록 비용이 계속 올라가는 구조입니다. "
          "지오테스는 고객관리(CRM)와 녹취, 통계 프로그램을 시스템 구축에 포함해 드립니다. "
          "프로그램만 따로 구매하는 항목이 없습니다."),
  ]),
 ],
 "faq": [
  ("몇 명부터 콜센터를 만들 수 있나요?",
   "정해진 최소 인원은 없습니다. 전화를 두세 명이 나눠 받는 곳도 구축합니다. 인원보다는 통화가 몰리는 정도와 기록을 남겨야 하는지가 기준이 됩니다."),
  ("쓰던 전화번호를 그대로 쓸 수 있나요?",
   "번호 이전으로 유지할 수 있습니다. 안내문과 명함을 다시 만들지 않아도 됩니다. 절차는 저희가 진행합니다."),
  ("인터넷이 끊기면 전화도 안 되나요?",
   "회선을 이중으로 두거나 휴대폰으로 넘기는 방식으로 대비합니다. 구축할 때 함께 구성합니다."),
  ("기존에 쓰던 프로그램이 있는데 버려야 하나요?",
   "그대로 두고 전화 기능만 붙이는 방식도 가능합니다. 어디까지 연결할지는 현황을 보고 정합니다."),
  ("AI를 꼭 넣어야 하나요?",
   "필요한 곳만 넣으면 됩니다. 반복 문의가 많은 곳은 효과가 크고, 통화량이 적은 곳은 녹취와 상담 이력만으로도 충분합니다."),
 ],
},
{
 "slug": "cost",
 "cat": "비용",
 "title": "콜센터 구축 비용, 견적서에서 확인해야 할 것",
 "desc": "콜센터 구축 비용이 어떤 항목으로 나뉘는지, 견적서에서 무엇을 확인해야 나중에 비용이 불어나지 않는지 정리했습니다.",
 "h1": "콜센터 구축 비용,<br>견적서에서 볼 것",
 "sub": "총액만 보면 나중에 달라집니다.<br>어떤 항목이 매달 나가는지가 더 중요합니다.",
 "answer_q": "콜센터 구축에 비용이 얼마나 드나요?",
 "answer": "규모와 구성에 따라 차이가 커서 하나의 금액으로 말하기 어렵습니다. "
   "다만 <span class='hl'>항목은 네 가지로 정해져 있습니다.</span> "
   "처음 한 번 내는 <b>시스템 구축비</b>, 매달 나가는 <b>회선 이용료</b>, 별도 계약인 <b>유지보수비</b>, "
   "그리고 고른 것만 붙는 <b>부가서비스</b>입니다. "
   "견적을 비교할 때는 총액보다 <b>매달 나가는 금액이 무엇인지</b>를 먼저 보셔야 합니다.",
 "body": [
  ("항목은 네 가지입니다", [
    ("table", [
      ["항목", "무엇인지", "언제 내는지"],
      ["시스템 구축", "교환기, 상담 프로그램, 설치, 교육", "처음 한 번"],
      ["회선 이용료", "인터넷전화 회선, 대표번호, 통화료", "매달"],
      ["유지보수", "장애 대응, 기능 수정, 정기 점검", "별도 계약"],
      ["부가서비스", "문자, 팩스, 영상상담 등", "고른 것만"],
    ]),
    ("p", "견적서가 복잡해 보여도 결국 이 네 칸 안에 들어갑니다. "
          "항목 이름이 회사마다 달라서 복잡해 보일 뿐입니다."),
  ]),
  ("총액보다 매달 나가는 돈을 보세요", [
    ("p", "구축비가 싸 보이는 견적이 3년을 두고 보면 더 비싼 경우가 자주 있습니다. "
          "<strong>매달 나가는 항목이 몇 개인지</strong>가 총액을 갈라놓기 때문입니다."),
    ("h3", "특히 확인할 것 — 상담 프로그램 사용료"),
    ("p", "회사에 따라 상담사 한 명이 늘 때마다 프로그램 사용료를 매달 더 받습니다. "
          "10석으로 시작해 30석이 되면 그 항목만 세 배가 됩니다. "
          "<strong>사람이 늘수록 비용이 따라 올라가는 구조인지</strong>를 계약 전에 확인하셔야 합니다."),
    ("callout", "지오테스는 고객관리(CRM)와 녹취, 통계 프로그램을 시스템 구축에 포함해 드립니다. "
                "프로그램만 따로 구매하는 항목이 없습니다. 유지보수는 별도 계약입니다."),
  ]),
  ("견적서에서 물어볼 다섯 가지", [
    ("list", [
      "<strong>이 금액에 상담 프로그램이 포함입니까, 별도입니까</strong> — 가장 많이 갈리는 부분입니다.",
      "<strong>상담사가 늘면 무엇이 추가됩니까</strong> — 회선만인지, 프로그램 사용료까지인지 확인하세요.",
      "<strong>유지보수는 어떻게 계산됩니까</strong> — 구축비의 몇 퍼센트인지, 무엇까지 포함인지 문서로 받으세요.",
      "<strong>기능을 하나 바꾸면 비용이 듭니까</strong> — 직접 개발한 회사인지 아닌지에 따라 답이 다릅니다.",
      "<strong>3년 쓰면 총 얼마입니까</strong> — 이 질문에 바로 답하지 못하는 견적은 다시 받으세요.",
    ]),
  ]),
  ("규모에 따라 무엇이 달라지나요", [
    ("table", [
      ["규모", "주로 필요한 것", "고려할 점"],
      ["5석 이하", "회선, 상담 화면, 녹취", "장비보다 번호 구성이 중요합니다"],
      ["6~20석", "여기에 자동안내와 분배", "전화를 누가 받을지 규칙이 필요해집니다"],
      ["21~50석", "스킬 분배, 통계, 전광판", "상담원별 편차 관리가 과제가 됩니다"],
      ["51석 이상", "이중화, 권한 분리, 연동", "장애 대비와 사내 시스템 연동이 핵심입니다"],
    ]),
    ("p", "석수가 늘어난다고 같은 시스템을 더 사는 것이 아닙니다. "
          "<strong>필요한 기능 자체가 달라집니다.</strong> 지금 규모가 아니라 2~3년 뒤 규모로 설계하는 편이 낫습니다."),
  ]),
 ],
 "faq": [
  ("가장 저렴하게 시작하려면 어떻게 하나요?",
   "쓰지 않을 기능을 빼는 것이 가장 확실합니다. 필요한 것만 넣고, 나중에 필요해지면 그때 켜는 방식으로 구성합니다."),
  ("구축형과 임대형 중 무엇이 낫나요?",
   "쓰는 기간에 따라 갈립니다. 오래 쓰실 계획이면 구축형이 총액에서 유리하고, 단기간이거나 규모가 자주 바뀌면 임대형이 낫습니다."),
  ("견적을 받으려면 무엇을 알려드려야 하나요?",
   "전화를 받는 인원, 하루 통화량, 지금 쓰시는 회선과 장비, 그리고 불편한 점을 알려주시면 됩니다."),
  ("설치 후에 비용이 더 드는 경우가 있나요?",
   "회선을 늘리거나 부가서비스를 추가할 때 듭니다. 기능 수정은 유지보수 계약 범위 안에서 처리합니다."),
 ],
},
{
 "slug": "cti",
 "cat": "콜센터 기초",
 "title": "CTI가 무엇인가요? 전화와 컴퓨터를 연결한다는 말의 뜻",
 "desc": "CTI는 전화와 상담 화면을 연결하는 기능입니다. 스크린 팝업, 클릭 투 콜, 지능형 분배가 모두 여기서 나옵니다.",
 "h1": "CTI가 무엇인가요?",
 "sub": "견적서에 꼭 나오는데 설명은 어렵게 돼 있는 말입니다.<br>실제로 무슨 일을 하는지 정리했습니다.",
 "answer_q": "CTI가 무엇인가요?",
 "answer": "CTI는 <b>전화와 컴퓨터 화면을 연결하는 기능</b>입니다. "
   "전화가 걸려오면 그 번호로 고객을 찾아 <span class='hl'>상담사 화면에 자동으로 띄우고</span>, "
   "화면의 번호를 누르면 <span class='hl'>바로 전화가 걸리게</span> 합니다. "
   "누구에게 전화를 넘길지 정하는 것도 CTI가 합니다. "
   "쉽게 말해 <b>전화기와 컴퓨터가 따로 놀지 않게 만드는 부분</b>입니다.",
 "body": [
  ("CTI가 실제로 하는 일 네 가지", [
    ("h3", "1. 스크린 팝업"),
    ("p", "전화가 울리는 순간 그 번호의 고객 정보가 화면에 뜹니다. "
          "\"성함이 어떻게 되세요\"부터 시작하지 않아도 되고, 지난번에 무슨 이야기를 했는지 보면서 통화합니다."),
    ("h3", "2. 클릭 투 콜"),
    ("p", "화면에 있는 전화번호를 누르면 바로 걸립니다. 번호를 옮겨 적다가 잘못 누르는 일이 없어집니다. "
          "발신이 많은 업무일수록 차이가 큽니다."),
    ("h3", "3. 지능형 분배"),
    ("p", "걸려온 전화를 누구에게 넘길지 정합니다. "
          "지금 통화 중이 아닌 사람, 그 업무를 담당하는 사람, 지난번에 응대했던 사람 중에서 규칙에 따라 고릅니다. "
          "<strong>대기 시간이 길어지는 문제는 대부분 이 규칙에서 나옵니다.</strong>"),
    ("h3", "4. 통화 기록 연결"),
    ("p", "통화가 끝나면 그 내용이 해당 고객 이력에 자동으로 붙습니다. "
          "따로 옮겨 적지 않아도 누가 언제 무슨 통화를 했는지 남습니다."),
  ]),
  ("CTI가 없으면 어떻게 되나요", [
    ("table", [
      ["상황", "CTI 없을 때", "CTI 있을 때"],
      ["전화가 옴", "누구인지 물어보고 검색", "화면에 고객이 먼저 뜸"],
      ["전화를 걺", "번호를 보고 손으로 누름", "화면에서 클릭"],
      ["분배", "먼저 받는 사람이 받음", "규칙대로 배분"],
      ["기록", "통화 후 따로 입력", "자동으로 이력에 남음"],
    ]),
    ("p", "전화기와 컴퓨터를 둘 다 쓰지만 서로 모르는 상태가 CTI가 없는 상태입니다. "
          "통화 한 건마다 몇십 초씩 더 걸리고, 그게 하루 수백 통이면 사람 한 명 몫이 됩니다."),
  ]),
  ("도입할 때 확인할 것", [
    ("list", [
      "<strong>쓰던 프로그램에 붙일 수 있는지</strong> — 사내 시스템이 이미 있다면 그것을 그대로 두고 전화 기능만 붙이는 방식이 가능합니다.",
      "<strong>분배 규칙을 우리가 바꿀 수 있는지</strong> — 조직이 바뀔 때마다 업체에 요청해야 하면 번거롭습니다.",
      "<strong>화면 항목을 수정할 수 있는지</strong> — 직접 개발한 회사는 그 자리에서 고치고, 외산 제품 총판은 본사 확인이 필요합니다.",
    ]),
    ("callout", "지오테스는 교환기와 상담 프로그램을 같은 회사에서 만듭니다. "
                "그래서 전화와 화면이 따로 놀지 않고, 항목이나 흐름을 요청대로 수정합니다."),
  ]),
 ],
 "faq": [
  ("CTI만 따로 도입할 수 있나요?",
   "가능합니다. 쓰시던 교환기나 사내 시스템에 전화 기능만 붙이는 방식으로 검토합니다."),
  ("스크린 팝업은 어떤 프로그램에 뜨나요?",
   "저희 상담 화면에 띄우거나, 쓰시던 사내 시스템에 띄우는 방식 모두 가능합니다."),
  ("모르는 번호로 걸려오면 어떻게 되나요?",
   "등록되지 않은 번호는 신규 고객으로 화면이 뜨고, 통화하면서 바로 등록합니다."),
  ("재택 근무에도 되나요?",
   "웹 기반이라 사무실 밖에서도 같은 화면과 같은 내선을 씁니다."),
 ],
},
{
 "slug": "aicc",
 "cat": "AI",
 "title": "AI 콜센터(AICC) 도입 전에 확인할 것",
 "desc": "AI 상담을 넣기 전에 무엇부터 자동화할지, 어디까지 맡길지, 무엇을 확인해야 하는지 정리했습니다.",
 "h1": "AI 콜센터,<br>도입 전에 볼 것",
 "sub": "전부 자동화하려고 하면 실패합니다.<br>어디부터 넘길지 정하는 것이 먼저입니다.",
 "answer_q": "AI 콜센터(AICC)가 무엇인가요?",
 "answer": "AI 콜센터는 <b>전화 상담에 음성인식과 AI를 붙인 것</b>입니다. "
   "자주 오는 문의를 사람 연결 없이 처리하고, 통화 내용을 자동으로 정리해 줍니다. "
   "중요한 것은 <span class='hl'>전부를 대신하는 것이 아니라는 점</span>입니다. "
   "답이 정해진 문의를 걸러내고, 판단이 필요한 통화는 사람에게 넘기는 구조로 만들어야 실제로 굴러갑니다.",
 "body": [
  ("무엇부터 넘겨야 하나요", [
    ("p", "자주 오면서 답이 정해진 문의부터입니다. 아래 세 조건을 다 만족하는 문의가 1순위입니다."),
    ("list", [
      "<strong>자주 온다</strong> — 하루에 여러 번 같은 질문이 옵니다.",
      "<strong>답이 고정돼 있다</strong> — 누가 받아도 같은 답을 합니다.",
      "<strong>판단이 필요 없다</strong> — 사정을 봐가며 다르게 답할 일이 없습니다.",
    ]),
    ("p", "영업시간, 위치, 주차, 진행 상황 조회가 대표적입니다. "
          "반대로 <strong>가격 협상이나 불만 응대처럼 사람이 판단해야 하는 통화는 처음부터 넘기지 않는 편이 낫습니다.</strong>"),
  ]),
  ("AI가 실제로 하는 일", [
    ("table", [
      ["기능", "하는 일", "효과"],
      ["AI 통화요약", "녹취를 글로 풀고 요점을 정리", "통화를 다시 듣지 않아도 됨"],
      ["AI 응대", "자주 오는 문의를 통화에서 처리", "상담원 연결 자체가 줄어듦"],
      ["보이는 ARS", "음성 대신 화면에서 고르게 함", "안내를 끝까지 듣지 않아도 됨"],
      ["상담원 인계", "요약과 함께 사람에게 넘김", "같은 설명을 반복하지 않음"],
    ]),
  ]),
  ("도입 전에 확인할 다섯 가지", [
    ("list", [
      "<strong>쓰던 시스템을 바꿔야 하는지</strong> — 기존 콜센터 위에 얹을 수 있으면 비용과 기간이 크게 줄어듭니다.",
      "<strong>못 알아들었을 때 어떻게 되는지</strong> — 몇 번 시도하고 사람에게 넘어가는지, 넘길 때 내용이 전달되는지 확인하세요.",
      "<strong>안내 내용을 우리가 고칠 수 있는지</strong> — 문구 하나 바꾸는 데 업체 요청이 필요하면 운영이 안 됩니다.",
      "<strong>통화 데이터가 어디에 저장되는지</strong> — 녹취와 대화 기록의 보관 위치와 열람 권한을 확인하세요.",
      "<strong>무엇으로 성과를 볼 것인지</strong> — 자동 처리된 비율, 사람에게 넘어간 비율, 통화 시간 변화를 미리 정해두세요.",
    ]),
    ("callout", "지오테스는 기존 시스템을 걷어내지 않고 기능만 추가하는 방식으로 적용합니다. "
                "이미 저희 시스템을 쓰고 계시면 새로 구축하지 않습니다."),
  ]),
  ("사람을 줄이는 것이 목적이 아닙니다", [
    ("p", "AI를 넣으면 상담원을 줄일 수 있다고 생각하기 쉽지만, 실제로 달라지는 것은 "
          "<strong>상담원이 하는 일의 종류</strong>입니다."),
    ("p", "반복 문의가 빠지면 남는 통화는 설명이 필요하거나 판단이 필요한 것들입니다. "
          "그 통화에 시간을 더 쓸 수 있게 되는 것이 실제 효과입니다. "
          "인원을 그대로 두고 응대 품질을 올리는 쪽이, 인원을 줄이고 품질을 유지하는 것보다 대개 결과가 낫습니다."),
  ]),
 ],
 "faq": [
  ("우리 회사 자료를 학습시켜야 하나요?",
   "안내 문서와 FAQ를 등록하면 그 자료를 근거로 답합니다. 자료를 고치면 그다음 통화부터 반영됩니다."),
  ("AI가 잘못 안내하면 어떻게 하나요?",
   "등록된 자료 밖의 내용은 답하지 않고 사람에게 넘기도록 구성합니다. 통화 기록으로 확인하고 자료를 보완합니다."),
  ("통화 품질이 어색하지 않나요?",
   "직접 통화해 보시는 것이 가장 정확합니다. 상담 시 시연해 드립니다."),
  ("작은 규모도 도입할 수 있나요?",
   "통화량이 적으면 AI보다 녹취와 상담 이력만으로 충분한 경우가 많습니다. 현황을 보고 필요 여부부터 말씀드립니다."),
 ],
},
]

# ---------------------------------------------------------------- 렌더

def block(kind, val):
    if kind == "p":
        return f"<p>{val}</p>"
    if kind == "h3":
        return f"<h3>{e(val)}</h3>"
    if kind == "callout":
        return f'<div class="callout"><p>{val}</p></div>'
    if kind == "list":
        return "<ul>" + "".join(f"<li>{v}</li>" for v in val) + "</ul>"
    if kind == "table":
        head = "".join(f"<th>{e(c)}</th>" for c in val[0])
        rows = "".join("<tr>" + "".join(
            (f"<th>{e(c)}</th>" if n == 0 else f"<td>{c}</td>")
            for n, c in enumerate(r)) + "</tr>" for r in val[1:])
        return f'<div class="table-scroll"><table><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table></div>'
    return ""


def render(g, base="guide", base_name="가이드"):
    """base 를 바꾸면 같은 서식으로 다른 섹션(예: 정보 /posts/)도 찍어낼 수 있습니다."""
    faq_ld = ",".join(
        '{"@type":"Question","name":%s,"acceptedAnswer":{"@type":"Answer","text":%s}}'
        % (jstr(q), jstr(a)) for q, a in g["faq"])

    secs = ""
    for h2, blocks in g["body"]:
        secs += f"<h2>{e(h2)}</h2>" + "".join(block(k, v) for k, v in blocks)

    faqs = "".join(
        f'<details><summary>{e(q)}</summary><div class="a">{e(a)}</div></details>'
        for q, a in g["faq"])

    return f'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{e(g["title"])} | 지오테스</title>
<meta name="description" content="{e(g["desc"])}">
<link rel="icon" href="/assets/favicon.ico" sizes="any">
<link rel="icon" type="image/png" href="/assets/favicon-32.png" sizes="32x32">
<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
<meta name="theme-color" content="#6d4aff">
<link rel="canonical" href="{SITE}/{base}/{g["slug"]}/">
<meta property="og:type" content="article">
<meta property="og:title" content="{e(g["title"])}">
<meta property="og:description" content="{e(g["desc"])}">
<meta property="og:locale" content="ko_KR">
<meta property="og:site_name" content="지오테스">
<meta property="og:image" content="{OG_BASE}/assets/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Poppins:wght@600;700;800&display=swap">
<link rel="stylesheet" href="/assets/nova-post.css">
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{faq_ld}]}}</script>
</head>
<body>

{header()}

<div class="post-hero">
  <div class="wrap">
    <p class="crumb"><a href="/">홈</a> · <a href="/{base}/">{base_name}</a> · {e(g["cat"])}</p>
    <span class="eyebrow">{e(g["cat"])}</span>
    <h1>{g["h1"]}</h1>
    <p class="meta">{g["sub"]}</p>
  </div>
</div>

<div class="wrap">
  <article>
    <div class="answer">
      <span class="lab">{e(g["answer_q"])}</span>
      <p>{g["answer"]}</p>
    </div>
    {secs}

    <h2>자주 묻는 것</h2>
    <div class="faq">{faqs}</div>

    <div class="cta">
      <div class="dot"></div>
      <h2>어디부터 손대야 할지 모르시겠다면</h2>
      <p>지금 쓰시는 전화 환경을 보고, 필요한 것만 골라 알려드립니다. 상담은 무료입니다.</p>
      <div class="btns">
        <a href="tel:{TEL_RAW}" class="btn btn-white">{TEL}</a>
        <a href="/contact/" class="btn btn-line">상담 신청</a>
      </div>
    </div>
  </article>
</div>

<footer>
  <div class="wrap">
    <div class="flogo">지오<b>테스</b></div>
    ㈜지오테스솔루션 · 대표이사 신명남 · 사업자등록번호 144-81-03835<br>
    경기 고양시 덕양구 삼막3길 5 고양삼송듀클래스 904호 · 고객센터 {TEL}<br>
    © 2006 ZioTEs Solution Inc.
  </div>
</footer>

<div class="fab">
  <a href="tel:15555528" class="call" aria-label="전화 상담">
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2A19.79 19.79 0 0 1 2.08 4.18 2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.13.96.36 1.9.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.9.34 1.85.57 2.81.7A2 2 0 0 1 22 16.92z"/></svg>
  </a>
  <a href="https://pf.kakao.com/_xaxgYMC" target="_blank" rel="noopener" class="kko" aria-label="카카오톡 상담">
    <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 3.4C6.9 3.4 2.8 6.6 2.8 10.6c0 2.6 1.7 4.9 4.3 6.2-.2.7-.7 2.4-.8 2.8-.1.4.2.4.4.3.2-.1 2.4-1.6 3.3-2.3.6.1 1.2.1 1.8.1 5.1 0 9.2-3.2 9.2-7.2S17.1 3.4 12 3.4z"/></svg>
  </a>
</div>
<script src="/assets/site.js" defer></script>
</body>
</html>
'''


def render_index():
    cards = "".join(
      f'<a href="/guide/{g["slug"]}/" class="post-card">'
      f'<span class="tag">{e(g["cat"])}</span>'
      f'<h3>{e(g["title"])}</h3><p>{e(g["desc"])}</p></a>' for g in GUIDES)
    return f'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>콜센터 가이드 | 지오테스</title>
<meta name="description" content="콜센터 구축을 처음 알아보는 분들을 위한 설명. 견적서에 나오는 용어부터 업체 고르는 기준까지 쉬운 말로 정리했습니다.">
<link rel="icon" href="/assets/favicon.ico" sizes="any">
<link rel="icon" type="image/png" href="/assets/favicon-32.png" sizes="32x32">
<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
<meta name="theme-color" content="#6d4aff">
<link rel="canonical" href="{SITE}/guide/">
<meta property="og:type" content="website">
<meta property="og:title" content="콜센터 가이드 | 지오테스">
<meta property="og:description" content="콜센터 구축을 처음 알아보는 분들을 위한 설명. 견적서에 나오는 용어부터 업체 고르는 기준까지 쉬운 말로 정리했습니다.">
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
{header()}
<div class="post-hero">
  <div class="wrap">
    <p class="crumb"><a href="/">홈</a> · 가이드</p>
    <span class="eyebrow">Guide</span>
    <h1>콜센터, 어렵게 설명하지 않겠습니다</h1>
    <p class="meta">견적서에 나오는 말부터 업체 고르는 기준까지 쉬운 말로 정리했습니다.</p>
  </div>
</div>
<div class="wrap"><div class="post-list">{cards}</div>
<div class="callout" style="margin-bottom:44px"><p>견적서에 모르는 말이 있으신가요? <a class="inlink" href="/glossary/">콜센터 용어집</a>에 IPCC, CTI, IVR 같은 말을 쉬운 말로 정리해 두었습니다.</p></div></div>
<footer>
  <div class="wrap">
    <div class="flogo">지오<b>테스</b></div>
    ㈜지오테스솔루션 · 고객센터 {TEL} · © 2006 ZioTEs Solution Inc.
  </div>
</footer>
<div class="fab">
  <a href="tel:15555528" class="call" aria-label="전화 상담">
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2A19.79 19.79 0 0 1 2.08 4.18 2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.13.96.36 1.9.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.9.34 1.85.57 2.81.7A2 2 0 0 1 22 16.92z"/></svg>
  </a>
  <a href="https://pf.kakao.com/_xaxgYMC" target="_blank" rel="noopener" class="kko" aria-label="카카오톡 상담">
    <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 3.4C6.9 3.4 2.8 6.6 2.8 10.6c0 2.6 1.7 4.9 4.3 6.2-.2.7-.7 2.4-.8 2.8-.1.4.2.4.4.3.2-.1 2.4-1.6 3.3-2.3.6.1 1.2.1 1.8.1 5.1 0 9.2-3.2 9.2-7.2S17.1 3.4 12 3.4z"/></svg>
  </a>
</div>
<script src="/assets/site.js" defer></script>
</body>
</html>
'''


# ---------------------------------------------------------------- 용어집
# 전문용어는 검색해서 들어오는 입구입니다. 그래서 지우지 않고 그대로 둡니다.
# 대신 옆에 쉬운 말을 붙여서, 모르고 들어온 사람도 이해하고 나가게 만듭니다.

GLOSSARY = [
 ("전화 시스템", [
  ("IPCC", "인터넷 전화로 돌아가는 콜센터 시스템",
   "교환기, 자동안내, 상담 화면, 녹취를 하나로 묶어 놓은 것입니다. IP Contact Center의 줄임말입니다.", "/solution/ipcc/"),
  ("IP-PBX", "걸려온 전화를 받아 나눠주는 장치",
   "회사 전화의 중심입니다. 예전에는 사무실에 놓는 큰 장비였고, 지금은 인터넷 회선 위에서 돌아갑니다.", "/solution/ipcc/"),
  ("CTI", "전화와 컴퓨터 화면을 연결하는 기능",
   "전화가 오면 고객 정보를 화면에 띄우고, 화면의 번호를 누르면 전화가 걸리게 합니다.", "/guide/cti/"),
  ("ACD / 호분배", "걸려온 전화를 상담원에게 나눠주는 규칙",
   "놀고 있는 사람, 그 업무를 담당하는 사람, 지난번에 응대한 사람 중에서 정해진 기준으로 고릅니다.", "/solution/ipcc/"),
  ("VoIP", "인터넷으로 하는 전화",
   "전화선 대신 인터넷 회선으로 통화합니다. 회선을 늘리는 데 공사가 필요 없습니다.", "/solution/voip/"),
  ("SIP", "인터넷전화가 서로 통하게 하는 약속",
   "장비와 서비스가 다른 회사 것이어도 이 규격을 따르면 연결됩니다.", None),
  ("내선", "회사 안에서 쓰는 짧은 번호",
   "지점이 여러 곳이어도 하나로 묶으면 내선끼리는 통화료가 들지 않습니다.", "/solution/voip/"),
 ]),
 ("자동응답", [
  ("ARS", "사람 대신 안내 음성이 나가는 자동응답",
   "\"상담원 연결은 0번\" 같은 안내입니다. 사람이 받지 않아도 되는 문의를 여기서 거릅니다.", "/solution/ivr/"),
  ("IVR", "누른 번호나 말한 내용에 따라 갈라지는 자동안내",
   "ARS보다 넓은 말입니다. 조건에 따라 다른 안내로 넘어가는 것까지 포함합니다.", "/solution/ivr/"),
  ("보이는 ARS", "음성 대신 화면에서 고르는 자동안내",
   "안내를 끝까지 듣고 번호를 누를 필요가 없습니다. 스마트폰 화면에서 바로 고릅니다.", "/solution/aicc/"),
  ("TTS", "글을 음성으로 만들어 주는 기술",
   "안내 문구를 바꿀 때 성우 녹음을 다시 하지 않아도 됩니다.", "/solution/ivr/"),
  ("콜백", "부재중일 때 회신 번호를 남기는 기능",
   "통화 중이거나 못 받았을 때 번호를 받아두고, 그 목록을 상담 화면에 띄웁니다.", "/solution/ivr/"),
  ("오토콜", "정해진 명단에 자동으로 거는 기능",
   "안내나 설문을 대량으로 돌릴 때 씁니다.", "/solution/ivr/"),
 ]),
 ("상담 관리", [
  ("CRM", "고객관리 프로그램",
   "상담용 CRM은 전화가 오는 순간 발신번호로 고객을 찾아 화면에 띄운다는 점이 일반 CRM과 다릅니다.", "/solution/crm/"),
  ("스크린 팝업", "전화가 울릴 때 고객 정보가 뜨는 것",
   "누구인지 물어보지 않고 바로 통화를 시작할 수 있습니다.", "/solution/crm/"),
  ("클릭 투 콜", "화면의 번호를 눌러 바로 거는 기능",
   "번호를 옮겨 적다가 잘못 누르는 일이 없어집니다.", "/solution/crm/"),
  ("전광판", "상담원 상태를 한 화면에 띄운 현황판",
   "지금 몇 통이 대기 중이고 누가 통화 중인지 실시간으로 보입니다.", "/demo/"),
  ("감청 / 속삭임", "관리자가 통화를 듣고 안내를 넣는 기능",
   "속삭임은 고객에게 들리지 않고 상담원에게만 들립니다. 신입 교육에 씁니다.", "/solution/ipcc/"),
 ]),
 ("AI", [
  ("AICC", "AI를 붙인 콜센터",
   "자주 오는 문의를 사람 연결 없이 처리하고 통화 내용을 자동으로 정리합니다.", "/solution/aicc/"),
  ("STT", "말을 글로 바꾸는 기술",
   "녹취를 글로 풀어 검색하거나 요약할 수 있게 만듭니다.", "/solution/aicc/"),
  ("AI 통화요약", "통화 내용을 자동으로 정리해 주는 기능",
   "4분짜리 통화를 세 줄로 줄입니다. 다시 듣지 않아도 무슨 통화였는지 알 수 있습니다.", "/demo/"),
  ("상담원 인계", "AI가 처리 못한 통화를 사람에게 넘기는 것",
   "넘길 때 지금까지의 대화 요약을 함께 전달해 고객이 같은 설명을 반복하지 않게 합니다.", "/solution/aicc/"),
 ]),
 ("번호 · 회선", [
  ("대표번호", "1544처럼 회사를 대표하는 번호",
   "여러 회선과 지점을 하나의 번호로 묶습니다.", "/solution/voip/"),
  ("번호이동", "쓰던 번호를 그대로 옮기는 것",
   "안내문과 명함을 다시 만들지 않아도 됩니다.", "/solution/voip/"),
  ("안심번호", "실제 번호를 감추고 연결하는 번호",
   "상담사나 기사의 개인 번호가 고객에게 남지 않습니다.", "/solution/extra/"),
  ("착신전환", "받지 못한 전화를 다른 번호로 넘기는 기능",
   "사무실 전화를 휴대폰으로 넘길 때 씁니다.", "/solution/voip/"),
 ]),
]


def render_glossary():
    secs = ""
    for cat, items in GLOSSARY:
        rows = ""
        for term, short, long_, link in items:
            name = f'<strong>{e(term)}</strong>'
            more = f' <a class="inlink" href="{link}">자세히</a>' if link else ""
            rows += (f'<tr><th>{name}</th><td>{e(short)}<br>'
                     f'<span style="color:var(--slate-500)">{e(long_)}</span>{more}</td></tr>')
        secs += (f'<h2>{e(cat)}</h2><div class="table-scroll"><table>'
                 f'<thead><tr><th style="width:34%">용어</th><th>쉬운 말로</th></tr></thead>'
                 f'<tbody>{rows}</tbody></table></div>')

    count = sum(len(i) for _, i in GLOSSARY)
    return f'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>콜센터 용어집 | IPCC·CTI·IVR·ACD 쉽게 정리 | 지오테스</title>
<meta name="description" content="콜센터 견적서와 제안서에 나오는 용어 {count}개를 쉬운 말로 정리했습니다. IPCC, IP-PBX, CTI, ACD, IVR, ARS, STT, AICC.">
<link rel="icon" href="/assets/favicon.ico" sizes="any">
<link rel="icon" type="image/png" href="/assets/favicon-32.png" sizes="32x32">
<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
<meta name="theme-color" content="#6d4aff">
<link rel="canonical" href="{SITE}/glossary/">
<meta property="og:type" content="article">
<meta property="og:title" content="콜센터 용어집 | 지오테스">
<meta property="og:description" content="견적서에 나오는 콜센터 용어 {count}개를 쉬운 말로 정리했습니다.">
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
{header()}
<div class="post-hero">
  <div class="wrap">
    <p class="crumb"><a href="/">홈</a> · 용어집</p>
    <span class="eyebrow">Glossary</span>
    <h1>콜센터 용어집</h1>
    <p class="meta">견적서와 제안서에 나오는 말 {count}개를 쉬운 말로 옮겼습니다.</p>
  </div>
</div>
<div class="wrap">
  <article>
    <div class="answer">
      <span class="lab">왜 어려운 말을 그대로 쓰나요?</span>
      <p>
        업계에서 쓰는 말을 임의로 바꾸면 <span class="hl">정작 그 말로 검색하시는 분들이 못 찾습니다.</span>
        그래서 용어는 그대로 두고, 옆에 쉬운 말을 함께 적었습니다.
        견적서를 받으셨는데 모르는 말이 있다면 여기서 찾아보시면 됩니다.
      </p>
    </div>
    {secs}
    <div class="cta">
      <div class="dot"></div>
      <h2>용어보다 지금 상황이 궁금하시면</h2>
      <p>지금 쓰시는 전화 환경을 보고 무엇이 필요한지부터 알려드립니다. 상담은 무료입니다.</p>
      <div class="btns">
        <a href="tel:{TEL_RAW}" class="btn btn-white">{TEL}</a>
        <a href="/contact/" class="btn btn-line">상담 신청</a>
      </div>
    </div>
  </article>
</div>
<footer>
  <div class="wrap">
    <div class="flogo">지오<b>테스</b></div>
    ㈜지오테스솔루션 · 고객센터 {TEL} · © 2006 ZioTEs Solution Inc.
  </div>
</footer>
<div class="fab">
  <a href="tel:15555528" class="call" aria-label="전화 상담">
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2A19.79 19.79 0 0 1 2.08 4.18 2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.13.96.36 1.9.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.9.34 1.85.57 2.81.7A2 2 0 0 1 22 16.92z"/></svg>
  </a>
  <a href="https://pf.kakao.com/_xaxgYMC" target="_blank" rel="noopener" class="kko" aria-label="카카오톡 상담">
    <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 3.4C6.9 3.4 2.8 6.6 2.8 10.6c0 2.6 1.7 4.9 4.3 6.2-.2.7-.7 2.4-.8 2.8-.1.4.2.4.4.3.2-.1 2.4-1.6 3.3-2.3.6.1 1.2.1 1.8.1 5.1 0 9.2-3.2 9.2-7.2S17.1 3.4 12 3.4z"/></svg>
  </a>
</div>
<script src="/assets/site.js" defer></script>
</body>
</html>
'''


def write(path, content, depth):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(relativize(content, depth))
    print("  ok", os.path.relpath(path, ROOT).replace("\\", "/"))


def main():
    print("가이드 생성")
    write(os.path.join(OUT, "index.html"), render_index(), 1)
    write(os.path.join(ROOT, "dist", "glossary", "index.html"), render_glossary(), 1)
    for g in GUIDES:
        write(os.path.join(OUT, g["slug"], "index.html"), render(g), 2)
    print(f"\n총 {len(GUIDES) + 2}개 생성 완료 (용어집 포함)")


if __name__ == "__main__":
    main()
