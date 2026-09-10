/* 사이트 공통 동작 — 모든 페이지에 들어갑니다.
 *
 * PC에서 전화 버튼을 누르면 윈도우가 "앱 선택" 창을 띄우고 정작 번호는 안 보입니다.
 * 휴대폰에서는 눌러서 바로 걸리는 게 맞으므로, 기기를 구분해서
 *   - 휴대폰: 그대로 전화 걸기
 *   - PC: 번호를 크게 보여주고 복사할 수 있게
 * 처리합니다.
 */
(function () {
  "use strict";

  /* 전화를 걸 수 있는 기기인지. 터치가 되고 화면이 좁으면 휴대폰으로 봅니다. */
  function 전화되는기기() {
    try {
      return window.matchMedia("(hover: none) and (pointer: coarse)").matches;
    } catch (e) {
      return /Android|iPhone|iPad|iPod|Mobile/i.test(navigator.userAgent);
    }
  }

  function 보기좋게(번호) {
    var d = ("" + 번호).replace(/\D/g, "");
    if (d.length === 8) return d.slice(0, 4) + "-" + d.slice(4);       // 1555-5528
    if (d.length === 10) return d.replace(/(\d{3})(\d{3})(\d{4})/, "$1-$2-$3");
    if (d.length === 11) return d.replace(/(\d{3})(\d{4})(\d{4})/, "$1-$2-$3");
    return 번호;
  }

  var 팝업;
  function 번호보이기(번호) {
    var 표시 = 보기좋게(번호);

    if (!팝업) {
      팝업 = document.createElement("div");
      팝업.className = "pop";
      팝업.innerHTML = '<div class="pop-box" role="dialog" aria-modal="true"></div>';
      document.body.appendChild(팝업);
    }

    팝업.querySelector(".pop-box").innerHTML =
      '<div class="pop-ico ok">' +
      '<svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2A19.79 19.79 0 0 1 2.08 4.18 2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.13.96.36 1.9.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.9.34 1.85.57 2.81.7A2 2 0 0 1 22 16.92z"/></svg>' +
      "</div>" +
      "<h3>전화 상담</h3>" +
      '<p class="pop-num">' + 표시 + "</p>" +
      '<p class="pop-sub">평일 09:00 – 18:00</p>' +
      '<button type="button" class="btn btn-brand">번호 복사</button>';

    팝업.classList.add("on");

    var 닫기 = function () { 팝업.classList.remove("on"); };
    var 버튼 = 팝업.querySelector("button");
    버튼.onclick = function () {
      var 원문 = 표시;
      var 끝내기 = function () {
        버튼.textContent = "복사했습니다";
        setTimeout(닫기, 700);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(원문).then(끝내기, 끝내기);
      } else {
        try {
          var t = document.createElement("textarea");
          t.value = 원문;
          document.body.appendChild(t);
          t.select();
          document.execCommand("copy");
          document.body.removeChild(t);
        } catch (e) {}
        끝내기();
      }
    };
    팝업.onclick = function (e) { if (e.target === 팝업) 닫기(); };
    document.addEventListener("keydown", function esc(e) {
      if (e.key === "Escape") { 닫기(); document.removeEventListener("keydown", esc); }
    });
    try { 버튼.focus(); } catch (e) {}
  }

  /* 고객사 로고판이 화면에 들어오면 한 칸씩 차례로 떠오르게 한다.
     들어오기 전에는 CSS 가 숨겨 두고, 여기서 .in 을 붙여 살린다. */
  function 로고판살리기() {
    var 판 = document.querySelectorAll(".logos");
    if (!판.length) return;

    var 켜기 = function (el) {
      var 칸 = el.querySelectorAll("figure");
      for (var i = 0; i < 칸.length; i++) 칸[i].style.animationDelay = (i * 45) + "ms";
      el.classList.add("in");
    };

    // 관찰 기능이 없거나 창 크기를 못 읽는 환경에서는 그냥 바로 켠다
    if (!("IntersectionObserver" in window) || !window.innerHeight) {
      for (var i = 0; i < 판.length; i++) 켜기(판[i]);
      return;
    }
    var 관찰 = new IntersectionObserver(function (목록) {
      목록.forEach(function (e) {
        if (e.isIntersecting) { 켜기(e.target); 관찰.unobserve(e.target); }
      });
    }, { threshold: 0.15 });
    for (var j = 0; j < 판.length; j++) 관찰.observe(판[j]);

    // 혹시 관찰이 한 번도 안 걸리면 3초 뒤에는 그냥 보여 준다
    setTimeout(function () {
      for (var k = 0; k < 판.length; k++) {
        if (!판[k].classList.contains("in")) { 켜기(판[k]); 관찰.unobserve(판[k]); }
      }
    }, 3000);
  }

  function init() {
    로고판살리기();
    신청버튼();

    if (전화되는기기()) return;   // 휴대폰 전화 버튼은 손대지 않습니다

    document.addEventListener("click", function (ev) {
      var a = ev.target.closest ? ev.target.closest('a[href^="tel:"]') : null;
      if (!a) return;
      ev.preventDefault();
      번호보이기(a.getAttribute("href").replace(/^tel:/, ""));
    });
  }

  /* '무료 상담신청' 버튼 — 상담 페이지로 보내지 않고 그 자리에서 팝업으로 받는다.
     글을 읽다 마음이 생긴 사람을 다른 페이지로 보내면 거기서 그만두는 일이 많다.
     팝업은 처음 누를 때 한 번만 만들고 그다음부터는 다시 쓴다. */
  var 신청팝업;

  function 신청팝업만들기() {
    if (신청팝업) return 신청팝업;

    신청팝업 = document.createElement("div");
    신청팝업.className = "pop";
    신청팝업.innerHTML =
      '<div class="pop-box wide" role="dialog" aria-modal="true" aria-label="무료 상담 신청">' +
      '<button type="button" class="pop-x" aria-label="닫기">&times;</button>' +
      '<form class="lead">' +
      "<h3>무료 상담 신청</h3>" +
      '<p class="ls">평일 09:00 – 18:00 · 1555-5528</p>' +
      '<label for="m-company">회사명</label><input type="text" id="m-company" name="company" required>' +
      '<label for="m-name">담당자</label><input type="text" id="m-name" name="name" required>' +
      '<label for="m-tel">연락처</label><input type="tel" id="m-tel" name="tel" required>' +
      '<label for="m-size">상담 인원</label>' +
      '<select id="m-size" name="size"><option>5석 이하</option><option>6 – 20석</option>' +
      "<option>21 – 50석</option><option>51석 이상</option><option>아직 모르겠습니다</option></select>" +
      '<label for="m-memo">문의 내용</label>' +
      '<textarea id="m-memo" name="memo" placeholder="지금 쓰시는 시스템이나 불편한 점을 적어주세요."></textarea>' +
      '<div class="agree"><input type="checkbox" id="m-agree" name="agree" value="1" required>' +
      '<label for="m-agree" style="margin:0;font-weight:500">상담을 위한 개인정보 수집·이용에 동의합니다</label></div>' +
      '<button type="submit" class="btn btn-brand">상담 신청하기</button>' +
      "</form></div>";
    document.body.appendChild(신청팝업);

    var 닫기 = function () { 신청팝업.classList.remove("on"); };
    신청팝업.querySelector(".pop-x").onclick = 닫기;
    신청팝업.onclick = function (e) { if (e.target === 신청팝업) 닫기(); };
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && 신청팝업.classList.contains("on")) 닫기();
    });

    // 폼을 붙인다. lead.js 가 없는 페이지면 팝업을 만들지 않는다(아래에서 걸러냄).
    window.상담폼붙이기(신청팝업.querySelector("form.lead"));
    return 신청팝업;
  }

  function 신청받기() {
    var p = 신청팝업만들기();
    p.classList.add("on");
    try { p.querySelector("#m-company").focus(); } catch (e) {}
  }

  function 신청버튼() {
    document.addEventListener("click", function (ev) {
      var a = ev.target.closest ? ev.target.closest('a.btn[href$="/contact/"]') : null;
      if (!a) return;
      // lead.js 가 안 붙은 페이지에서는 그냥 상담 페이지로 보낸다.
      // 팝업만 열리고 보내기가 안 되는 것이 제일 나쁘다.
      if (typeof window.상담폼붙이기 !== "function") return;
      ev.preventDefault();
      신청받기();
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();

/* ------------------------------------------------------------------
   블로그 홍보 유입 집계 (파워잉글리쉬 CRM)
   블로그 글에서 링크를 타고 들어온 방문만 셉니다. 사람을 알아보는 정보는
   보내지 않습니다. 상담 접수까지 이어졌는지는 lead.js 에서 알려줍니다.
   이 한 줄이 페이지마다 따로 붙지 않게 site.js 에 모아 둡니다.
------------------------------------------------------------------ */
(function () {
  try {
    var s = document.createElement("script");
    s.src = "https://keyword-crm.marketwave99.workers.dev/t.js";
    s.defer = true;
    document.head.appendChild(s);
  } catch (e) {}
})();
