# -*- coding: utf-8 -*-
"""
지오테스 솔루션 상세 페이지 생성기
  python _tools/gen_solution.py
  → dist/solution/index.html (허브) + dist/solution/{slug}/index.html × 8

내용 수정은 아래 PAGES 데이터만 고치면 됨. 템플릿은 건드릴 일 없음.
TODO 표시는 사장님 확인 후 확정할 항목.
"""
import os, sys, html

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mocks

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "dist", "solution")

SITE = "https://ziotes.com"
# 카카오톡·문자로 링크를 보낼 때 쓰이는 이미지 주소.
# 실제로 열리는 주소여야 썸네일이 뜹니다. 거래처 서버로 옮긴 뒤에는 SITE 로 바꾸세요.
OG_BASE = "https://jerry797979.github.io/bitwave"
TEL = "1555-5528"
TEL_RAW = "15555528"

# ---------------------------------------------------------------- 데이터

PAGES = [
{
 "mock": "ai_summary",
 "slug": "aicc", "nav": "AI 컨택센터", "eyebrow": "AICC",
 "title": "AI 컨택센터(AICC) 구축 | 통화요약·AI 응대·보이는 ARS | 지오테스",
 "desc": "쓰던 콜센터를 걷어내지 않고 AI만 얹습니다. AI 통화요약(STT), AI 응대, 보이는 ARS. 교환기를 직접 만드는 회사가 구축합니다.",
 "h1": "반복되는 통화부터<br>AI가 받습니다",
 "sub": "사람을 줄이는 것이 아니라, 사람이 할 일을 남기는 방향입니다.<br>쓰시던 시스템 위에 기능만 얹습니다.",
 "answer_q": "AI 컨택센터(AICC)가 무엇인가요?",
 "answer": "AI 컨택센터는 전화 상담에 <span class='hl'>음성인식과 AI를 붙여</span> 반복되는 문의를 자동으로 처리하고, 통화 내용을 자동으로 정리하는 방식입니다. "
           "지오테스는 교환기와 상담 프로그램을 직접 개발하기 때문에, <span class='hl'>기존 시스템을 걷어내지 않고 AI 기능만 추가</span>하는 방식으로 적용합니다.",
 "features": [
   ("AI 통화요약", "통화가 끝나면 녹취를 글로 풀어 요점을 정리합니다. 처음부터 다시 듣지 않아도 무슨 통화였는지 확인됩니다."),
   ("AI 응대", "자주 오는 문의는 사람 연결 없이 그 자리에서 끝냅니다. 판단이 필요한 통화만 상담원에게 넘어갑니다."),
   ("보이는 ARS", "안내 음성을 끝까지 듣고 번호를 누를 필요가 없습니다. 화면에서 골라 바로 원하는 곳으로 갑니다."),
   ("상담원 인계", "AI가 처리하지 못한 통화는 대화 요약과 함께 넘깁니다. 고객이 같은 설명을 두 번 하지 않습니다."),
   ("문의 유형 분석", "어떤 문의가 몰리는지, 어디에서 상담이 길어지는지 자동으로 분류해 보여줍니다."),
   ("쓰던 시스템 위에", "이미 지오테스를 쓰고 계시면 새로 구축하지 않고 기능만 추가합니다."),
 ],
 "targets": [
   ("문의가 특정 시간대에 몰리는 곳", "점심시간과 퇴근 직전에 대기가 길어지고, 기다리다 끊는 고객이 생깁니다."),
   ("야간·휴일 문의를 놓치는 곳", "업무 외 시간에 걸려온 전화가 그대로 사라집니다."),
   ("상담 기록 입력에 시간을 쓰는 곳", "통화보다 정리에 더 오래 걸려 다음 전화를 못 받습니다."),
 ],
 "faq": [
   ("지금 쓰는 시스템을 바꿔야 하나요?", "지오테스 시스템을 쓰고 계시면 교체 없이 기능만 추가하는 방식으로 검토합니다. 타사 시스템은 현황을 본 뒤 연동 가능 범위를 알려드립니다."),
   ("AI가 못 알아들으면 어떻게 되나요?", "정해진 횟수 안에 처리가 안 되면 상담원에게 넘어갑니다. 넘길 때 지금까지의 대화 요약을 함께 전달합니다."),
   ("어떤 문의부터 자동화하는 것이 좋을까요?", "가장 자주 오면서 답이 정해져 있는 문의부터 시작합니다. 영업시간, 위치, 진행 상황 조회 같은 것들입니다."),
   ("녹취와 통화 요약은 어디에 저장되나요?", "기본은 클라우드에 보관하고, 고객사 서버에 직접 두는 방식도 선택할 수 있습니다. 보관 기간도 함께 정합니다."),
 ],
},
{
 "mock": "dashboard",
 "slug": "ipcc", "nav": "콜센터 솔루션", "eyebrow": "IPCC · CTI",
 "title": "콜센터 솔루션 구축 | IP 교환기·호분배·CTI | 지오테스",
 "desc": "IP 교환기, 호분배(ACD), 상담원 화면, 통계를 하나의 시스템으로 제공합니다. 자체 개발이라 화면과 흐름을 요청대로 수정합니다.",
 "h1": "교환기부터 상담 화면까지<br>하나로",
 "sub": "교환기는 장비사에서, 상담 프로그램은 소프트웨어 회사에서 따로 사실 필요가 없습니다.<br>처음부터 한 시스템으로 만들었습니다.",
 "answer_q": "콜센터 솔루션은 무엇으로 구성되나요?",
 "answer": "콜센터를 돌리려면 전화를 받고 나누는 <b>IP 교환기</b>, 상담원에게 전화를 배분하는 <b>호분배(ACD)</b>, 고객 정보를 띄우는 <b>상담원 화면(CTI)</b>, 그리고 <b>녹취와 통계</b>가 필요합니다. "
           "보통은 이것들을 각각 사서 연동합니다. 지오테스는 <span class='hl'>이 전부를 직접 개발해 한 시스템으로 제공</span>하기 때문에 연동 비용과 기간이 들지 않습니다.",
 "features": [
   ("IP 교환기 (IP-PBX)", "착·발신, 내선, 착신전환, 돌려주기, 당겨받기, 3자통화 등 교환기 기능 전부를 제공합니다."),
   ("호분배 (ACD)", "균등 분배, 스킬별 분배, 대기시간 기준 등 상담 조직에 맞는 방식으로 전화를 나눕니다."),
   ("상담원 화면 (CTI)", "전화가 울리면 고객 정보가 함께 뜹니다. 상담 이력을 보면서 통화합니다."),
   ("실시간 현황판(전광판)", "대기·통화중·후처리·휴식 상태를 한 화면에서 봅니다. 지금 몇 명이 대기 중인지 보입니다."),
   ("통계·보고서", "수신·발신, 일·주·월별, 요일별, 내선별 통계를 뽑습니다."),
   ("감청·속삭임", "관리자가 통화를 들으며 상담원에게만 들리는 안내를 넣을 수 있습니다. 신입 교육에 씁니다."),
 ],
 "targets": [
   ("상담 인원이 늘고 있는 곳", "전화를 누가 받을지 사람이 정하고 있다면 분배 규칙이 필요한 시점입니다."),
   ("지점이 여러 곳인 곳", "본사와 지점 전화를 하나의 번호 체계로 묶습니다."),
   ("재택·외부 상담이 있는 곳", "사무실 밖에서도 같은 내선과 같은 화면을 씁니다."),
 ],
 "faq": [
   ("몇 석부터 구축할 수 있나요?", "소규모부터 대형 콜센터까지 구성합니다. 인원과 동시 통화량에 따라 시스템 사양이 달라집니다."),
   ("기존 전화번호를 그대로 쓸 수 있나요?", "쓰시던 대표번호와 국번을 유지한 채 이전할 수 있습니다. 번호 이전 절차도 함께 진행합니다."),
   ("사내 시스템과 연동되나요?", "저희가 직접 개발한 시스템이라 고객사 ERP·주문 시스템과 연동 개발이 가능합니다."),
   ("화면 항목을 저희 업무에 맞게 바꿀 수 있나요?", "소스를 직접 수정하기 때문에 항목과 업무 흐름을 요청대로 반영합니다."),
 ],
},
{
 "mock": "consult",
 "slug": "crm", "nav": "고객관리 CRM", "eyebrow": "CRM",
 "title": "상담 CRM 고객관리 프로그램 | 스크린 팝업·상담이력 | 지오테스",
 "desc": "전화가 울리면 고객 정보가 뜨는 상담 전용 CRM. 항목을 업무에 맞게 수정하고, 클릭 한 번으로 발신합니다.",
 "h1": "전화가 울리면<br>고객이 먼저 뜹니다",
 "sub": "누가 걸었는지 물어보고, 이력을 찾고, 다시 설명하게 하는 시간을 없앱니다.",
 "answer_q": "일반 CRM과 상담용 CRM은 무엇이 다른가요?",
 "answer": "일반 CRM은 사람이 검색해서 고객을 찾습니다. 상담용 CRM은 <span class='hl'>전화가 걸려오는 순간 발신번호로 고객을 자동으로 찾아 화면에 띄웁니다</span>. "
           "통화가 끝나면 상담 내용이 그 고객 이력에 바로 쌓입니다. 지오테스 CRM은 교환기와 같은 회사가 만들었기 때문에 전화와 화면이 따로 놀지 않습니다.",
 "features": [
   ("스크린 팝업", "전화가 울리는 순간 고객 정보와 지난 상담 이력이 함께 뜹니다."),
   ("상담 이력", "누가 언제 무슨 이야기를 했는지 한 줄로 쌓입니다. 담당자가 바뀌어도 이어집니다."),
   ("항목 맞춤 수정", "관리할 항목을 업무에 맞게 추가하고 뺍니다. 쓰지 않는 칸을 억지로 채울 필요가 없습니다."),
   ("클릭 투 콜", "화면의 전화번호를 누르면 바로 발신됩니다. 번호를 옮겨 적을 일이 없습니다."),
   ("문자·알림톡 발송", "통화 뒤 안내 문자를 화면에서 바로 보냅니다. 예약 문자도 지정할 수 있습니다."),
   ("상담 예약", "다시 연락할 시간을 걸어두면 그때 알려줍니다. 놓치는 콜백이 줄어듭니다."),
 ],
 "targets": [
   ("엑셀로 고객을 관리하는 곳", "파일이 여러 벌로 갈라지고, 누구 버전이 최신인지 모르게 됩니다."),
   ("담당자 휴대폰에만 이력이 남는 곳", "그 사람이 자리를 비우면 아무도 답을 못 합니다."),
   ("고객이 같은 설명을 반복하는 곳", "전화할 때마다 처음부터 다시 이야기하게 만들면 불만이 쌓입니다."),
 ],
 "faq": [
   ("쓰던 고객 데이터를 옮길 수 있나요?", "엑셀 등으로 보유하신 자료를 정리해 이전합니다. 구축 과정에 포함됩니다."),
   ("외근 중에도 볼 수 있나요?", "웹 기반이라 사무실 밖에서도 같은 화면을 씁니다."),
   ("고객 수가 많아도 괜찮나요?", "규모에 맞춰 시스템 사양을 잡습니다. 상담 건수와 보관 기간을 알려주시면 산정해 드립니다."),
   ("기존에 쓰던 사내 시스템이 있는데요?", "그 시스템을 그대로 두고 전화 기능만 붙이는 방식도 가능합니다."),
 ],
},
{
 "mock": "ivr_tree",
 "extra": '''
<section>
  <div class="wrap">
    <div class="sec-head">
      <span class="eyebrow">Scenario</span>
      <h2 class="h">실제로 쓰이는 시나리오 네 가지</h2>
      <p class="lead-txt">구축해 드린 안내 흐름을 그대로 옮겼습니다. 멘트도 실제로 나가는 문장입니다.</p>
    </div>

    <div style="max-width:760px;margin:0 auto 20px">
      <h3 style="font-size:19px;font-weight:800;text-align:center">
        기본형 — 시간대별 안내와 회원 구분
        <span class="mk done" style="margin-left:8px;vertical-align:middle">제작 무료</span>
      </h3>
      <p class="lead-txt" style="text-align:center;font-size:15px;margin-top:8px">
        전화가 걸려온 뒤 상담원에게 닿기까지 실제로 이렇게 흘러갑니다.
      </p>
    </div>

    <div class="flow">
      <div class="flow-node start"><b>대표번호로 전화가 옵니다</b></div>
      <div class="flow-link"></div>
      <span class="flow-cond">지금이 근무시간인지 확인</span>
      <div class="flow-link"></div>
      <div class="flow-branch">
        <div class="fb end"><b>점심시간</b><p>"오후 12시부터 1시까지 점심시간이오니, 1시 이후에 다시 전화 주시길 바랍니다."</p></div>
        <div class="fb end"><b>업무 시간 외</b><p>"운영시간은 평일 오전 9시부터 오후 6시까지입니다."</p></div>
        <div class="fb end"><b>휴일</b><p>"금일은 당사 휴일입니다."</p></div>
        <div class="fb on"><b>근무시간</b><p>다음 단계로 넘어갑니다</p></div>
      </div>
      <div class="flow-link"></div>
      <div class="flow-node say"><b>"회원은 1번, 비회원은 2번을 눌러주세요"</b></div>
      <div class="flow-link"></div>
      <div class="flow-branch">
        <div class="fb on"><b>1번 · 회원</b><p>담당 상담원에게 연결합니다</p></div>
        <div class="fb on"><b>2번 · 비회원</b><p>해당 부서로 연결합니다</p></div>
      </div>
      <div class="flow-link"></div>
      <span class="flow-cond">받을 사람이 있는지 확인</span>
      <div class="flow-link"></div>
      <div class="flow-branch">
        <div class="fb on"><b>연결 가능</b><p>녹취 고지 후 상담원에게 넘깁니다</p></div>
        <div class="fb end"><b>모두 통화 중</b><p>"모든 상담원이 통화 중입니다. 잠시 후에 다시 연락 주십시오."</p></div>
      </div>
    </div>

    <p class="note" style="text-align:center;max-width:760px;margin:16px auto 0">
      점심시간·휴일 같은 조건은 관리자 화면에서 날짜와 시간을 직접 지정합니다.
      명절이나 임시 휴무도 그날만 다른 안내가 나가도록 걸어둘 수 있습니다.
    </p>

    <div class="answer" style="margin-top:34px">
      <span class="lab">시나리오 짜는 것부터 무료로 도와드립니다</span>
      <p>
        단계가 깊어질수록 중간에 끊는 고객이 늘어납니다. 그래서 <span class="hl">단계를 줄이는 작업을 값 없이 함께 합니다.</span>
        지금 쓰시는 안내 내용을 보내주시면 어디를 합치고 어디를 뺄 수 있는지 정리해 드립니다.
        <b>기본 시나리오 제작도 무료입니다.</b> 쓰시던 음원이 있으면 그대로 가져다 씁니다.
      </p>
    </div>

    <div class="steps" style="margin-top:44px">
      <div class="step">
        <span class="sn wn c1">2</span>
        <div>
          <h4>지점 분기 + 콜백 접수</h4>
          <p>지점이 여러 곳일 때 씁니다. 서울·부산·제주처럼 눌러서 고르게 하고,
            <b>통화량이 많아 연결이 어려우면 기다릴지 번호를 남길지 고르게</b> 합니다.
            남긴 번호는 다시 읽어 주고 확인까지 받습니다.</p>
          <p class="cd" style="margin-top:9px;font-size:13.5px;color:var(--slate-500)">
            실제 멘트 — "계속 기다리시려면 1번, 연락 받으실 번호를 남기시려면 2번을 눌러주십시오."</p>
        </div>
      </div>

      <div class="step">
        <span class="sn wn c2">3</span>
        <div>
          <h4>회원번호로 찾아 나누기</h4>
          <p>회원번호를 누르면 <b>등록된 자료에서 찾아</b> 기존 회원과 비회원을 갈라
            서로 다른 상담 그룹으로 넘깁니다. 담당자가 정해져 있는 업무에 씁니다.</p>
          <p class="cd" style="margin-top:9px;font-size:13.5px;color:var(--slate-500)">
            실제 멘트 — "회원번호를 입력 후 우물 정자를 눌러주세요."</p>
        </div>
      </div>

      <div class="step">
        <span class="sn wn c3">4</span>
        <div>
          <h4>대기 인원 안내 + 문자 발송</h4>
          <p><b>지금 몇 명이 앞에 기다리는지</b> 숫자로 알려 줍니다.
            기다릴지 번호를 남길지 고객이 판단할 수 있습니다.
            전 지점 연락처를 문자로 받아 가는 번호도 함께 둡니다.</p>
          <p class="cd" style="margin-top:9px;font-size:13.5px;color:var(--slate-500)">
            실제 멘트 — "현재 대기인원은 XX명입니다. 계속 기다리시려면 1번을…"</p>
        </div>
      </div>
    </div>

    <p class="note" style="max-width:760px;margin:18px auto 0">
      기본 시나리오 제작은 값을 받지 않습니다. 위 2·3번처럼 콜백 접수나 회원번호 검색을 붙이려면
      선택 기능으로 추가하고, 4번의 대기 인원 안내는 서버를 직접 두는 방식에서 지원합니다.
      필요한 것만 넣으시면 됩니다.
    </p>

    <div class="answer" style="margin-top:34px">
      <span class="lab">녹취 고지는 꼭 넣습니다</span>
      <p>
        상담원에게 넘기기 직전에 <span class="hl">"통화품질 향상과 고객 권익을 위해 통화 내용은 자동으로 녹음됩니다"</span>
        안내가 나갑니다. 나중에 통화 내용을 확인해야 할 때 <b>고지했다는 기록이 함께 남아야</b>
        분쟁에서 근거가 됩니다. 시나리오를 짤 때 빠뜨리기 쉬운 부분이라 기본으로 넣어 드립니다.
      </p>
    </div>
  </div>
</section>''',
 "slug": "ivr", "nav": "ARS·IVR", "eyebrow": "ARS · IVR",
 "title": "ARS·IVR 자동응답 시스템 구축 | 다단계 시나리오·콜백 | 지오테스",
 "desc": "사람이 받지 않아도 되는 전화를 걸러냅니다. 다단계 시나리오, 시간·요일별 분기, 콜백, TTS 음원 편집.",
 "h1": "사람이 받지 않아도 되는<br>전화를 걸러냅니다",
 "sub": "위치, 영업시간, 진행 상황처럼 답이 정해진 문의는 상담원까지 갈 필요가 없습니다.",
 "answer_q": "ARS와 IVR은 무엇이 다른가요?",
 "answer": "둘은 거의 같은 뜻으로 쓰입니다. 정확히는 <b>ARS</b>가 녹음된 안내를 들려주는 자동응답이고, <b>IVR</b>은 고객이 누른 번호나 말한 내용에 따라 <span class='hl'>다른 안내로 갈라지는 것</span>까지 포함합니다. "
           "지오테스는 단계 수 제한 없이 시나리오를 구성하고, 시간·요일·상황에 따라 다른 안내가 나가도록 설정합니다.",
 "features": [
   ("다단계 시나리오", "단계 수에 제한 없이 안내를 구성합니다. 누른 번호에 따라 다음 안내가 갈라집니다."),
   ("시간·요일별 분기", "업무시간, 점심시간, 야간, 주말, 공휴일에 각각 다른 안내가 나갑니다."),
   ("콜백", "통화 중이거나 부재중일 때 회신 번호를 남기게 하고, 그 목록을 상담 화면에 띄웁니다."),
   ("TTS 음원 편집", "글로 입력하면 음성으로 만들어 줍니다. 안내 문구를 바꿀 때 성우 녹음을 다시 하지 않아도 됩니다."),
   ("컬러링", "연결음 자리에 회사 안내나 이벤트를 넣습니다."),
   ("오토콜", "정해진 명단에 자동으로 전화를 걸어 안내하거나 설문을 받습니다."),
 ],
 "targets": [
   ("같은 질문을 하루에 수십 번 받는 곳", "위치, 주차, 영업시간 문의가 상담원 시간을 잠식합니다."),
   ("부서가 여러 개인 곳", "전화를 받아서 다시 돌려주는 일이 반복됩니다."),
   ("업무 외 시간 문의가 많은 곳", "안내와 콜백 접수만 해도 다음 날 아침에 이어서 처리할 수 있습니다."),
 ],
 "faq": [
   ("안내 문구를 저희가 직접 바꿀 수 있나요?", "관리자 화면에서 문구를 수정하면 음성으로 만들어 적용합니다."),
   ("단계가 너무 많으면 고객이 답답해하지 않나요?", "맞습니다. 단계가 깊어질수록 중간에 끊는 사람이 늘어납니다. 그래서 단계를 줄이는 작업을 무료로 도와드립니다. 지금 쓰시는 안내 내용을 보내주시면 어디를 합치고 어디를 뺄 수 있는지 정리해 드립니다. 음성을 끝까지 듣지 않고 화면에서 고르는 보이는 ARS를 함께 쓰면 단계가 더 줄어듭니다."),
   ("명절이나 임시 휴무 안내도 되나요?", "날짜를 지정해 그날만 다른 안내가 나가도록 걸어둘 수 있습니다."),
   ("시나리오 예시를 볼 수 있나요?", "업종별 구성 예시를 상담 시 함께 보여드립니다."),
 ],
},
{
 "mock": "recording",
 "slug": "recording", "nav": "통화 녹취", "eyebrow": "Recording",
 "title": "통화 녹취 시스템 | 전수 녹취·조건 검색·권한 관리 | 지오테스",
 "desc": "모든 통화를 남기고 필요한 것만 찾습니다. 기간·상담원·고객번호·통화상태별 검색, 웹에서 바로 재생.",
 "h1": "통화는 남기고,<br>필요한 것만 찾습니다",
 "sub": "녹음은 어디나 됩니다. 문제는 그중에서 그 통화를 찾을 수 있느냐입니다.",
 "answer_q": "녹취는 왜 필요한가요?",
 "answer": "말로 한 약속을 확인할 방법이 필요하기 때문입니다. 주문 내용이 달라졌다거나 안내를 못 받았다는 이야기가 나올 때, <span class='hl'>녹취가 있으면 확인하면 끝나고 없으면 분쟁이 됩니다</span>. "
           "금융·보험처럼 녹취 보관이 의무인 업종도 있습니다. 지오테스는 전 통화 자동 녹취와 조건 검색을 기본으로 제공합니다.",
 "features": [
   ("전수 / 선택 녹취", "모든 통화를 남기거나, 정해둔 조건의 통화만 남깁니다."),
   ("조건 검색", "기간, 상담원, 고객 번호, 통화 상태로 찾습니다. 파일 이름을 뒤질 필요가 없습니다."),
   ("웹에서 바로 재생", "프로그램을 설치하지 않고 브라우저에서 듣고 내려받습니다."),
   ("보관 위치·기간 선택", "기본은 AWS 클라우드에 보관하고, 규정상 외부 보관이 어려운 곳은 고객사 서버에 직접 둡니다. 얼마나 오래 남길지도 업종 규정에 맞춰 정합니다."),
   ("권한 관리", "누가 어떤 녹취를 들을 수 있는지 나눕니다. 관리자만 열 수 있는 범위를 정합니다."),
   ("실시간 감청", "진행 중인 통화를 관리자가 들을 수 있습니다. 교육과 품질 점검에 씁니다."),
 ],
 "targets": [
   ("말로 주문·계약을 받는 곳", "전화로 정한 내용이 나중에 달라졌다는 이야기가 나옵니다."),
   ("녹취 보관이 의무인 업종", "금융·보험·의료처럼 규정으로 정해진 경우입니다."),
   ("상담 품질을 관리하려는 곳", "잘 된 통화와 안 된 통화를 실제 녹취로 놓고 교육합니다."),
 ],
 "faq": [
   ("녹취 파일은 어디에 저장되나요?", "기본은 AWS 클라우드에 보관합니다. 고객사 서버에 직접 두는 방식도 가능하며, 규정상 외부 보관이 어려운 곳은 사내에 두고 운영합니다."),
   ("고객에게 녹취 사실을 알려야 하나요?", "통화 시작 안내에 녹취 고지를 넣는 것이 일반적입니다. 시나리오에 함께 구성합니다."),
   ("용량이 얼마나 필요한가요?", "통화량과 보관 기간으로 계산합니다. 상담 인원과 하루 통화 건수를 알려주시면 산정해 드립니다."),
   ("녹취를 글로 바꿀 수 있나요?", "AI 통화요약을 함께 쓰면 녹취를 글로 풀고 요점을 정리합니다."),
 ],
},
{
 "slug": "chat", "nav": "통합 채팅상담", "eyebrow": "Chat",
 "title": "통합 채팅상담 | 문자·카카오·네이버톡톡 한 화면 | 지오테스",
 "desc": "문자, 카카오톡, 네이버 톡톡, SNS로 흩어진 문의를 한 화면에서 받습니다. 전화 상담 이력과 함께 봅니다.",
 "h1": "흩어진 문의를<br>한 화면에서 받습니다",
 "sub": "창을 네 개 띄워놓고 번갈아 보는 방식으로는 놓치는 문의가 생깁니다.",
 "answer_q": "채팅상담을 왜 통합해야 하나요?",
 "answer": "고객은 편한 채널로 연락합니다. 전화로 물었다가 카카오톡으로 다시 묻기도 합니다. 채널별로 창이 따로면 <span class='hl'>같은 고객인지 알 수 없고, 답변이 엇갈립니다</span>. "
           "한 화면에서 받으면 이 고객이 아까 전화로 뭘 물었는지 보면서 답할 수 있습니다.",
 "features": [
   ("채널 통합", "문자, 카카오톡, 네이버 톡톡 등으로 들어온 문의를 한 목록에서 봅니다."),
   ("상담원 분배", "채널별로 담당자를 정하거나 순서대로 나눕니다."),
   ("자주 쓰는 문구", "반복해서 보내는 안내를 저장해두고 클릭으로 넣습니다."),
   ("이력 확인", "이 고객이 전에 무엇을 물었는지 전화 상담 이력과 함께 봅니다."),
   ("전화로 전환", "글로 설명이 길어지면 화면에서 바로 전화를 겁니다."),
   ("모바일 사용", "외부에서도 휴대폰으로 이어서 응대합니다."),
 ],
 "targets": [
   ("쇼핑몰·서비스업", "주문, 배송, 교환 문의가 여러 채널로 동시에 들어옵니다."),
   ("전화받기 어려운 고객이 많은 곳", "통화가 부담스러워 글로 묻는 고객이 늘고 있습니다."),
   ("상담 인원이 적은 곳", "한 사람이 여러 채널을 봐야 한다면 통합이 필수입니다."),
 ],
 "faq": [
   ("어떤 채널을 연결할 수 있나요?", "문자와 주요 메신저 채널을 연결합니다. 쓰시는 채널을 알려주시면 가능 여부를 확인해 드립니다."),
   ("기존 카카오 채널을 그대로 쓸 수 있나요?", "운영 중인 채널을 연결하는 방식입니다. 새로 만들지 않아도 됩니다."),
   ("상담 내용이 CRM에 남나요?", "같은 고객 이력에 전화 상담과 함께 쌓입니다."),
   ("업무시간 외에는 어떻게 되나요?", "자동 응답을 걸어두고, 다음 영업일에 이어서 처리합니다."),
 ],
},
{
 "slug": "voip", "nav": "기업 인터넷전화", "eyebrow": "VoIP",
 "title": "기업 인터넷전화·대표번호 | 070·내선·번호이동 | 지오테스",
 "desc": "인터넷전화 사업자가 직접 공급하는 기업 회선. 070, 대표번호, 내선, 착신전환, 모바일 앱까지 한 계약으로.",
 "h1": "회선도<br>저희 것입니다",
 "sub": "통신사에서 회선을 사 와서 얹는 방식이 아닙니다.<br>회선과 시스템을 한 곳에서 계약합니다.",
 "answer_q": "기업 인터넷전화는 일반 전화와 무엇이 다른가요?",
 "answer": "인터넷 회선으로 통화하기 때문에 <span class='hl'>회선을 늘리는 데 공사가 필요 없고, 사무실을 옮겨도 번호가 그대로</span>입니다. "
           "내선끼리는 통화료가 들지 않고, 지점이 여러 곳이어도 하나의 내선 체계로 묶입니다. 지오테스는 인터넷전화 사업자라 회선을 직접 공급합니다.",
 "features": [
   ("070 · 대표번호", "새 번호를 받거나 쓰시던 번호를 옮겨옵니다."),
   ("내선", "지점이 달라도 짧은 번호로 서로 연결됩니다. 내선 통화료가 없습니다."),
   ("착신전환", "받지 못한 전화를 휴대폰이나 다른 번호로 넘깁니다."),
   ("모바일 앱", "회사 번호로 휴대폰에서 걸고 받습니다. 개인 번호가 노출되지 않습니다."),
   ("번호 이동", "쓰시던 번호를 그대로 가져옵니다. 안내문을 다시 만들 필요가 없습니다."),
   ("증설", "자리가 늘어도 공사 없이 회선을 추가합니다."),
 ],
 "targets": [
   ("사무실 이전 계획이 있는 곳", "번호를 바꾸면 명함부터 간판까지 전부 다시 만들어야 합니다."),
   ("지점이 여러 곳인 곳", "지점 간 통화가 잦다면 내선으로 묶는 편이 낫습니다."),
   ("외부 근무가 많은 곳", "회사 번호를 휴대폰에서 쓰면 개인 번호를 알려주지 않아도 됩니다."),
 ],
 "faq": [
   ("쓰던 번호를 그대로 가져올 수 있나요?", "번호 이동으로 유지할 수 있습니다. 절차는 저희가 진행합니다."),
   ("인터넷이 끊기면 전화도 안 되나요?", "회선 이중화와 휴대폰 착신전환으로 대비합니다. 구성 방법을 함께 잡아드립니다."),
   ("통화 품질은 괜찮나요?", "2006년부터 인터넷전화 서비스를 운영해 왔습니다. 통화 품질은 구축 전 테스트로 확인하실 수 있습니다."),
   ("통화료는 어떻게 되나요?", "요금은 상담 시 안내해 드립니다."),  # TODO 확인
 ],
},
{
 "slug": "extra", "nav": "부가서비스", "eyebrow": "Add-ons",
 "title": "콜센터 부가서비스 | 문자·팩스·전광판·080·안심번호 | 지오테스",
 "desc": "필요한 것만 골라 붙이는 부가 기능. 문자 발송, 웹팩스, 실시간 현황판(전광판), 080 수신거부, 안심번호, 영상상담 등.",
 "h1": "필요한 것만<br>골라 붙이세요",
 "sub": "전부 쓰는 곳은 없습니다. 안 쓰는 기능은 빼고 견적을 드립니다.",
 "answer_q": "부가서비스는 나중에 추가해도 되나요?",
 "answer": "됩니다. 처음부터 전부 넣을 필요가 없습니다. <span class='hl'>운영해 보시고 필요한 시점에 추가</span>하는 편이 낫습니다. "
           "같은 시스템 안에서 기능을 켜는 방식이라, 새로 구축하거나 다른 회사와 계약할 일이 없습니다.",
 "features": [
   ("문자·알림톡", "상담 화면에서 바로 보냅니다. 예약 발송과 대량 발송도 됩니다."),
   ("웹팩스", "팩스 기기 없이 보내고 받습니다."),
   ("실시간 현황판(전광판)", "대기·통화중·후처리 상태를 한 화면에 띄웁니다."),
   ("080 수신거부", "광고 문자를 보낼 때 필요한 무료 수신거부 번호입니다."),
   ("안심번호", "실제 번호를 노출하지 않고 통화합니다. 상담사와 고객 모두 보호됩니다."),
   ("영상상담", "화면을 보면서 확인해야 하는 상담에 씁니다."),
   ("대표번호 그룹", "여러 대표번호를 한 그룹으로 묶어 받습니다."),
   ("패턴 발신", "상황에 따라 다른 번호로 발신합니다."),
 ],
 "targets": [
   ("광고 문자를 보내는 곳", "080 수신거부 번호가 있어야 합니다."),
   ("개인정보 노출이 부담인 곳", "학교, 심리상담, 배달처럼 개인 번호를 알리기 어려운 업무입니다."),
   ("현장 확인이 필요한 곳", "말로 설명이 안 되는 상담은 화면을 보는 편이 빠릅니다."),
 ],
 "faq": [
   ("나중에 추가하면 비용이 더 드나요?", "기능을 켜는 방식이라 재구축은 없습니다. 비용은 항목별로 안내해 드립니다."),
   ("안 쓰는 기능도 값을 내야 하나요?", "쓰시는 것만 넣어 견적을 드립니다."),
   ("어떤 것부터 넣는 것이 좋을까요?", "업무를 보고 권해드립니다. 대부분 문자와 전광판부터 시작합니다."),
   ("여기 없는 기능이 필요합니다.", "저희가 직접 개발하는 시스템이라 맞춤 개발이 가능합니다. 상담 시 말씀해 주세요."),
 ],
},
{
 # TODO 확인: 마케팅 대행의 실제 서비스 범위·계약 방식·성과 지표를 받아서 아래 내용 교체
 "slug": "marketing", "nav": "온라인 마케팅", "eyebrow": "Marketing",
 "title": "온라인 마케팅 대행 | 문의를 만들고 상담까지 잇습니다 | 지오테스",
 "desc": "콜센터를 잘 만들어도 전화가 오지 않으면 소용이 없습니다. 검색 노출부터 문의 접수, 상담 시스템 연결까지 한 곳에서 진행합니다.",
 "h1": "전화가 울리게 만드는 일까지",
 "sub": "상담 시스템을 아무리 잘 갖춰도 문의가 없으면 놀립니다.<br>고객을 데려오는 단계부터 함께합니다.",
 "answer_q": "콜센터 회사가 왜 마케팅까지 하나요?",
 "answer": "20년 동안 상담 시스템을 구축하면서 반복해서 본 장면이 있습니다. <span class='hl'>시스템은 갖췄는데 걸려오는 전화가 없어서 그대로 놀리는 경우</span>입니다. "
           "지오테스는 설립 때부터 온라인 마케팅 프로그램 개발과 대행을 함께 해왔습니다. "
           "광고로 들어온 문의가 <span class='hl'>그대로 상담 시스템에 쌓이기 때문에</span>, 어느 광고에서 온 전화가 실제 계약까지 갔는지 끊기지 않고 확인할 수 있습니다.",
 "features": [
   ("검색 노출", "고객이 실제로 검색하는 말에 맞춰 페이지와 글을 만듭니다. 광고를 끄면 사라지는 노출과 다릅니다."),
   ("콘텐츠 발행", "한 번 만들고 두는 것이 아니라 꾸준히 쌓습니다. 순위는 멈추면 내려갑니다."),
   ("문의 접수", "상담 신청을 받는 페이지와 폼을 만듭니다. 들어온 신청은 담당자에게 바로 알립니다."),
   ("광고별 번호 분리", "광고마다 다른 번호를 두면 어느 경로에서 걸려온 전화인지 구분됩니다."),
   ("상담 시스템 연결", "문의가 CRM에 자동으로 쌓입니다. 명단을 따로 옮겨 적지 않습니다."),
   ("계약까지 추적", "문의 건수가 아니라 그중 몇 건이 계약이 됐는지까지 봅니다."),
 ],
 "targets": [
   ("시스템은 있는데 문의가 없는 곳", "상담원이 전화를 기다리는 시간이 길다면 시스템 문제가 아닙니다."),
   ("광고비를 쓰는데 효과를 모르는 곳", "어느 광고에서 전화가 왔는지 구분이 안 되면 어디를 줄일지 정할 수 없습니다."),
   ("신청은 들어오는데 놓치는 곳", "메일함이나 문자에 흩어져 있으면 연락이 늦어지고, 늦으면 이미 다른 곳과 계약합니다."),
 ],
 "faq": [
   ("광고 대행사와 무엇이 다른가요?", "문의를 만드는 데서 끝나지 않고 그 문의가 상담 시스템에 들어가 계약까지 이어지는 흐름을 같이 봅니다."),
   ("어느 정도 기간이 걸리나요?", "검색 노출은 쌓이는 데 시간이 걸립니다. 진행 방식과 일정은 상담 시 안내해 드립니다."),
   ("지오테스 시스템을 안 쓰는데도 되나요?", "마케팅만 따로 진행할 수 있습니다. 다만 상담 시스템까지 함께 쓰시면 성과 확인이 훨씬 정확해집니다."),
   ("비용은 어떻게 되나요?", "진행 범위에 따라 달라집니다. 상담 시 안내해 드립니다."),
 ],
},
]



# '이런 곳에 필요합니다'에 붙는 업종. 추상적인 설명보다 업종 이름이 먼저 걸립니다.
# 순서는 각 페이지 targets 순서와 같습니다.
TARGET_INDS = {
    "aicc":      [["병원·의원", "쇼핑몰", "공공기관"],
                  ["학원", "A/S센터", "렌탈"],
                  ["금융", "보험", "카드"]],
    "ipcc":      [["쇼핑몰", "콜센터 아웃소싱", "금융"],
                  ["프랜차이즈", "병원", "학원"],
                  ["심리상담", "아웃소싱", "보험"]],
    "crm":       [["제조", "도소매", "인테리어"],
                  ["제조", "부동산", "법무법인"],
                  ["쇼핑몰", "A/S센터", "병원"]],
    "ivr":       [["병원·의원", "학원", "공공기관"],
                  ["공공기관", "대학", "제조"],
                  ["학원", "병원", "쇼핑몰"]],
    "recording": [["도소매", "제조", "유통"],
                  ["금융", "보험", "의료"],
                  ["콜센터 아웃소싱", "쇼핑몰", "카드"]],
    "chat":      [["쇼핑몰", "이커머스", "서비스업"],
                  ["학원", "병원", "미용·뷰티"],
                  ["1인기업", "소규모 쇼핑몰", "스타트업"]],
    "voip":      [["스타트업", "분양사무소", "신규 사무실"],
                  ["프랜차이즈", "학원", "병원"],
                  ["부동산", "인테리어", "영업 조직"]],
    "extra":     [["쇼핑몰", "학원", "분양"],
                  ["학교·교원", "심리상담", "배달·물류"],
                  ["A/S센터", "보험", "렌탈"]],
    "marketing": [["병원·의원", "학원", "인테리어"],
                  ["분양", "렌탈", "쇼핑몰"],
                  ["법무법인", "세무·회계", "심리상담"]],
}

# 링크에 붙는 한 줄 설명. 코드 같은 약어 대신 쉬운 말을 씁니다.
SHORT = {
    "aicc": "반복 문의를 사람 없이 처리",
    "ipcc": "전화를 받아 나눠주고 화면에 띄움",
    "crm": "전화가 울리면 고객이 먼저 뜸",
    "ivr": "사람 없이 안내하고 넘김",
    "recording": "모두 남기고 필요한 것만 찾음",
    "chat": "흩어진 문의를 한 화면에서",
    "voip": "공사 없이 회선을 늘림",
    "extra": "필요한 것만 골라 붙임",
    "marketing": "문의를 만들고 상담까지 연결",
}
# ---------------------------------------------------------------- 템플릿

def head(title, desc, canonical, faq=None):
    ld = ""
    if faq:
        items = ",".join(
            '{"@type":"Question","name":%s,"acceptedAnswer":{"@type":"Answer","text":%s}}'
            % (jstr(q), jstr(a)) for q, a in faq)
        ld = ('\n<script type="application/ld+json">{"@context":"https://schema.org",'
              '"@type":"FAQPage","mainEntity":[%s]}</script>' % items)
    return f'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="website">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
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
<link rel="stylesheet" href="/assets/nova.css">{ld}
</head>
<body>'''


def header(active=""):
    links = "".join(
        f'<a href="/solution/{p["slug"]}/">{p["nav"]}</a>' for p in PAGES)
    return f'''
<header>
  <div class="wrap nav">
    <a href="/" class="logo logo-img"><img src="/assets/logo.png" alt="지오테스 Ziotes"></a>
    <nav class="nav-links">
      <div class="has-sub">
        <a href="/solution/">솔루션</a>
        <div class="sub">{links}</div>
      </div>
      <a href="/use-cases/">활용사례</a>
      <a href="/industries/">업종별</a>
      <a href="/demo/">화면 예시</a>
      <a href="/pricing/">요금</a>
      <a href="/cases/">구축사례</a>
      <a href="/about/">회사소개</a>
    </nav>
    <div style="display:flex;align-items:center;gap:10px">
      <a href="tel:{TEL_RAW}" class="nav-call">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2A19.79 19.79 0 0 1 2.08 4.18 2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.13.96.36 1.9.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.9.34 1.85.57 2.81.7A2 2 0 0 1 22 16.92z"/></svg>
        <span>{TEL}</span></a>
      <button class="nav-burger" type="button" aria-label="메뉴 열기" onclick="document.getElementById('drawer').classList.add('open')">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M3 6h18M3 12h18M3 18h18"/></svg>
      </button>
    </div>
  </div>
</header>

<div class="drawer" id="drawer" onclick="if(event.target===this)this.classList.remove('open')">
  <div class="drawer-panel">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:22px">
      <span class="logo logo-img"><img src="/assets/logo.png" alt="지오테스 Ziotes"></span>
      <button class="pm-x" type="button" aria-label="메뉴 닫기" onclick="document.getElementById('drawer').classList.remove('open')">&times;</button>
    </div>
    <div class="dgroup"><b>솔루션</b>{links}</div>
    <div class="dgroup"><b>도입</b><a href="/use-cases/">활용사례</a><a href="/industries/">업종별</a><a href="/demo/">화면 예시</a><a href="/pricing/">요금</a><a href="/cases/">구축사례</a></div>
    <div class="dgroup"><b>회사</b><a href="/about/">회사소개</a><a href="/contact/">상담 문의</a></div>
  </div>
</div>'''


FOOTER = f'''
<section style="padding:0 0 76px">
  <div class="wrap">
    <div class="final">
      <div class="doodle-circle" style="width:130px;height:130px;left:-40px;top:-40px"></div>
      <div class="doodle-circle" style="width:80px;height:80px;right:-26px;bottom:-26px;background:rgba(53,224,161,.85)"></div>
      <h2>무엇이 불편하신지만 알려주세요</h2>
      <div class="fp">{TEL}</div>
      <p class="fn">평일 09:00 – 18:00 · 영업 070-7615-0119 · 기술 070-7615-0927</p>
      <div class="fbtn">
        <a href="tel:{TEL_RAW}" class="btn btn-white">전화 상담</a>
        <a href="/#lead" class="btn" style="background:rgba(255,255,255,.16);color:#fff">상담 신청</a>
      </div>
    </div>
  </div>
</section>

<footer>
  <div class="wrap">
    <div class="flogo">지오<b>테스</b></div>
    <div class="fnav">
      <a href="/solution/">솔루션</a><a href="/use-cases/">활용사례</a><a href="/industries/">업종별</a>
      <a href="/pricing/">요금</a><a href="/cases/">구축사례</a><a href="/about/">회사소개</a><a href="/guide/">가이드</a><a href="/glossary/">용어집</a><a href="/contact/">상담문의</a>
    </div>
    <div class="info">
      ㈜지오테스솔루션 · 대표이사 신명남 · 사업자등록번호 144-81-03835<br>
      통신판매신고 제2023-고양덕양구-0487호 · 개인정보책임자 정필락<br>
      경기 고양시 덕양구 삼막3길 5 고양삼송듀클래스 904호<br>
      고객센터 {TEL} · 영업 070-7615-0119 · 기술 070-7615-0927 · help@ziotes.com<br>
      © 2006 ZioTEs Solution Inc. All Rights Reserved.
    </div>
  </div>
</footer>

<div class="fab">
  <a href="tel:{TEL_RAW}" class="call" aria-label="전화 상담">
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2A19.79 19.79 0 0 1 2.08 4.18 2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.13.96.36 1.9.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.9.34 1.85.57 2.81.7A2 2 0 0 1 22 16.92z"/></svg>
  </a>
</div>

<script src="/assets/lead.js" defer></script>
</body>
</html>
'''

e = lambda s: html.escape(str(s), quote=True)
jstr = lambda s: '"%s"' % str(s).replace('\\', '\\\\').replace('"', '\\"')


def render(p):
    others = [x for x in PAGES if x["slug"] != p["slug"]][:4]

    extra_sec = p.get("extra", "")

    mock_sec = ""
    if p.get("mock"):
        mtitle, mlead, mfn = mocks.ALL[p["mock"]]
        mock_sec = f'''
<section style="background:var(--slate-50)">
  <div class="wrap">
    <div class="sec-head">
      <span class="eyebrow">Screen</span>
      <h2 class="h">{mtitle}</h2>
      <p class="lead-txt">{mlead}</p>
    </div>
    <div style="max-width:820px;margin:0 auto">{mfn()}</div>
  </div>
</section>'''

    feats = "".join(f'''
      <div class="card">
        <h3>{e(t)}</h3>
        <p class="cd">{e(d)}</p>
      </div>''' for t, d in p["features"])

    tinds = TARGET_INDS.get(p["slug"], [])
    targets = ""
    for i, (t, d) in enumerate(p["targets"]):
        inds = tinds[i] if i < len(tinds) else []
        chips = ("".join(f'<span>{e(x)}</span>' for x in inds))
        chips = f'<div class="step-inds">{chips}</div>' if chips else ""
        targets += (f'<div class="step"><span class="sn wn c{i}">{i+1}</span>'
                    f'<div><h4>{e(t)}</h4><p>{e(d)}</p>{chips}</div></div>')

    faqs = "".join(f'''
      <details><summary>{e(q)}</summary><div class="a">{e(a)}</div></details>'''
      for q, a in p["faq"])

    rel = "".join(f'''
      <a href="/solution/{o["slug"]}/" class="ind"><h4>{o["nav"]}</h4><p>{e(SHORT.get(o["slug"], ""))}</p></a>'''
      for o in others)

    return (head(p["title"], p["desc"], f'{SITE}/solution/{p["slug"]}/', p["faq"])
+ header() + f'''

<div class="hero-top">
  <div class="wrap">
    <p class="crumb" style="font-size:13px;color:var(--slate-400);text-align:center">
      <a href="/">홈</a> · <a href="/solution/">솔루션</a> · {e(p["nav"])}
    </p>
    <div class="hero-center compact">
      <span class="eyebrow">{e(p["eyebrow"])}</span>
      <h1 style="margin-top:16px">{p["h1"]}</h1>
      <p class="sub">{p["sub"]}</p>
      <div class="actions">
        <a href="/#lead" class="btn btn-brand">무료 상담 신청</a>
        <a href="tel:{TEL_RAW}" class="btn btn-outline">{TEL}</a>
      </div>
    </div>
  </div>
</div>

<section style="padding:56px 0 0">
  <div class="wrap">
    <div class="answer">
      <span class="lab">{e(p["answer_q"])}</span>
      <p>{p["answer"]}</p>
    </div>
  </div>
</section>

<section>
  <div class="wrap">
    <div class="sec-head">
      <span class="eyebrow">Features</span>
      <h2 class="h">이런 기능이 들어갑니다</h2>
    </div>
    <div class="cards3">{feats}
    </div>
  </div>
</section>
{mock_sec}
{extra_sec}
<section>
  <div class="wrap">
    <div class="sec-head">
      <span class="eyebrow">Fit</span>
      <h2 class="h">이런 곳에 필요합니다</h2>
    </div>
    <div class="steps">{targets}
    </div>
  </div>
</section>

<section>
  <div class="wrap-narrow">
    <div class="sec-head">
      <span class="eyebrow">FAQ</span>
      <h2 class="h">자주 묻는 것</h2>
    </div>
    <div class="faq" style="max-width:720px;margin:0 auto">{faqs}
    </div>
  </div>
</section>

<section style="background:var(--slate-50)">
  <div class="wrap">
    <div class="sec-head">
      <span class="eyebrow">More</span>
      <h2 class="h">함께 많이 쓰는 솔루션</h2>
    </div>
    <div class="ind-grid">{rel}
    </div>
  </div>
</section>
''' + FOOTER)


def render_hub():
    cards = "".join(f'''
      <a href="/solution/{p["slug"]}/" class="card" style="display:block">
        <span class="svc-tag">{e(p["eyebrow"])}</span>
        <h3>{p["nav"]}</h3>
        <p class="cd">{e(SHORT.get(p["slug"], p["desc"].split(".")[0]))}</p>
      </a>''' for p in PAGES)

    return (head("솔루션 전체 | 콜센터·CRM·ARS·녹취·AI | 지오테스",
                 "지오테스가 제공하는 컨택센터 솔루션 8종. 교환기부터 AI까지 한 회사가 직접 개발합니다.",
                 f"{SITE}/solution/")
+ header() + f'''

<div class="hero-top">
  <div class="wrap">
    <div class="hero-center compact">
      <span class="eyebrow">Solutions</span>
      <h1 style="margin-top:16px">콜센터에 필요한 전부를<br>한 곳에서 만듭니다</h1>
      <p class="sub">필요한 것만 골라 쓰셔도 되고, 통째로 맡기셔도 됩니다.</p>
    </div>
  </div>
</div>

<section style="padding:56px 0 76px">
  <div class="wrap">
    <div class="cards2">{cards}
    </div>
  </div>
</section>
''' + FOOTER)


# ---------------------------------------------------------------- 실행

def relativize(s, depth):
    """사이트 내부 링크를 절대경로에서 상대경로로 바꾼다.

    저장소를 포크해 GitHub Pages로 켜면 주소가 `아이디.github.io/저장소이름/`
    형태가 된다. 이때 `/assets/nova.css` 같은 절대경로는 저장소 폴더를 건너뛰고
    도메인 루트를 찾아가서 404가 난다. 상대경로로 두면 어디에 올려도 동작한다.
    canonical·og 주소는 `https://`로 시작하므로 여기서 건드리지 않는다.
    """
    pfx = "../" * depth if depth else "./"
    s = s.replace('href="/"', 'href="%s"' % pfx)
    s = s.replace('href="/', 'href="%s' % pfx)
    s = s.replace('src="/', 'src="%s' % pfx)
    return s


def write(path, content, depth):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(relativize(content, depth))
    print("  ok", os.path.relpath(path, ROOT).replace("\\", "/"))


def main():
    print("솔루션 페이지 생성")
    write(os.path.join(OUT, "index.html"), render_hub(), 1)
    for p in PAGES:
        write(os.path.join(OUT, p["slug"], "index.html"), render(p), 2)
    print(f"\n총 {len(PAGES) + 1}개 생성 완료")


if __name__ == "__main__":
    main()
