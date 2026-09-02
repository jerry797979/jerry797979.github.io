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

    if (전화되는기기()) return;   // 휴대폰 전화 버튼은 손대지 않습니다

    document.addEventListener("click", function (ev) {
      var a = ev.target.closest ? ev.target.closest('a[href^="tel:"]') : null;
      if (!a) return;
      ev.preventDefault();
      번호보이기(a.getAttribute("href").replace(/^tel:/, ""));
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
