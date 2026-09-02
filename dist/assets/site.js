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

  function init() {
    if (전화되는기기()) return;   // 휴대폰은 손대지 않습니다

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
