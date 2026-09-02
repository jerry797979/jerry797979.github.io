/* 상담 신청 폼 처리
 *
 * class="lead" 인 폼을 찾아 자동으로 붙습니다. 폼마다 코드를 넣을 필요가 없습니다.
 * 보내는 곳은 이 파일 위치를 기준으로 계산하므로, 하위 폴더에 올려도 동작합니다.
 */
(function () {
  "use strict";

  // 이 스크립트가 /assets/lead.js 이므로 두 단계 위가 사이트 루트
  var me = document.currentScript || (function () {
    var s = document.getElementsByTagName("script");
    return s[s.length - 1];
  })();
  var BASE = me.src.replace(/assets\/lead\.js.*$/, "");
  var ENDPOINT = BASE + "_lead.php";

  /* 전화번호 자동 하이픈 — 02(서울)와 그 외를 나눠 끊는다. */
  function 하이픈(v) {
    var d = ("" + v).replace(/\D/g, "").slice(0, 11);
    if (d.indexOf("02") === 0) {
      if (d.length < 3) return d;
      if (d.length < 6) return d.replace(/(\d{2})(\d+)/, "$1-$2");
      if (d.length < 10) return d.replace(/(\d{2})(\d{3,4})(\d+)/, "$1-$2-$3");
      return d.replace(/(\d{2})(\d{4})(\d{4})/, "$1-$2-$3");
    }
    if (d.length < 4) return d;
    if (d.length < 8) return d.replace(/(\d{3})(\d+)/, "$1-$2");
    if (d.length < 11) return d.replace(/(\d{3})(\d{3})(\d+)/, "$1-$2-$3");
    return d.replace(/(\d{3})(\d{4})(\d{4})/, "$1-$2-$3");
  }

  /* 보내기 전에 검사한다. 문제가 있으면 {칸, 말}, 없으면 null.
     2026-09-02: 회사명에 "333", 연락처에 "234-32" 같은 값을 넣어도 그냥 서버로 갔고
     손님은 무엇이 잘못됐는지 알 수 없었다. 어느 칸이 왜 틀렸는지 짚어 준다. */
  function 검사(data) {
    var 회사 = (data.company || "").trim();
    if (!회사) return { 칸: "company", 말: "회사명을 입력해 주세요." };
    if (/^\d+$/.test(회사)) return { 칸: "company", 말: "회사명을 정확히 입력해 주세요. 숫자만으로는 안 됩니다." };

    var 이름 = (data.name || "").trim();
    if (!이름) return { 칸: "name", 말: "담당자 성함을 입력해 주세요." };
    if (/\d/.test(이름)) return { 칸: "name", 말: "담당자 이름에는 숫자를 넣을 수 없습니다. (예: 홍길동)" };
    if (!/^[가-힣a-zA-Z][가-힣a-zA-Z ().·]*$/.test(이름)) return { 칸: "name", 말: "담당자 이름은 한글 또는 영문으로 입력해 주세요. (예: 홍길동)" };
    if (이름.replace(/[^가-힣a-zA-Z]/g, "").length < 2) return { 칸: "name", 말: "이름이 너무 짧습니다. 두 글자 이상 입력해 주세요. (예: 홍길동)" };

    var 숫자 = (data.tel || "").replace(/\D/g, "");
    if (!숫자) return { 칸: "tel", 말: "연락처를 입력해 주세요." };
    if (숫자.charAt(0) !== "0") return { 칸: "tel", 말: "연락처는 0으로 시작해야 합니다. 지역번호나 010을 함께 입력해 주세요. (예: 010-1234-5678)" };
    if (숫자.length < 9) return { 칸: "tel", 말: "연락처 자릿수가 모자랍니다. 지역번호나 010을 포함해 9자리 이상 입력해 주세요. (예: 010-1234-5678)" };
    if (숫자.length > 11) return { 칸: "tel", 말: "연락처가 너무 깁니다. 하이픈을 빼고 11자리까지 입력해 주세요. (예: 010-1234-5678)" };
    if (/^(\d)+$/.test(숫자)) return { 칸: "tel", 말: "연락 가능한 번호를 입력해 주세요. (예: 010-1234-5678)" };

    if (!data.agree) return { 칸: "agree", 말: "개인정보 수집·이용에 동의해 주세요." };
    return null;
  }

  /* 문제가 난 칸을 빨갛게 짚고 커서를 옮긴다. 다시 쓰기 시작하면 표시를 지운다. */
  function 짚기(form, 칸) {
    var el = form.querySelector('[name="' + 칸 + '"]');
    if (!el) return;
    if (el.type !== "checkbox") {
      el.style.borderColor = "#d63a3a";
      el.addEventListener("input", function 지우기() {
        el.style.borderColor = "";
        el.removeEventListener("input", 지우기);
      });
    }
    try { el.focus(); } catch (e) {}
  }

  function hidden(form, name, value) {
    var el = form.querySelector('input[name="' + name + '"]');
    if (!el) {
      el = document.createElement("input");
      el.type = "hidden";
      el.name = name;
      form.appendChild(el);
    }
    el.value = value;
  }

  function setup(form) {
    // 봇 걸러내기 — 사람 눈에는 안 보이고, 자동 입력 도구는 채웁니다
    if (!form.querySelector('input[name="website"]')) {
      var trap = document.createElement("input");
      trap.type = "text";
      trap.name = "website";
      trap.tabIndex = -1;
      trap.autocomplete = "off";
      trap.setAttribute("aria-hidden", "true");
      trap.style.cssText =
        "position:absolute;left:-9999px;width:1px;height:1px;opacity:0;pointer-events:none";
      form.appendChild(trap);
    }
    hidden(form, "t", String(Math.floor(Date.now() / 1000)));
    hidden(form, "page", location.pathname + location.search);

    var 전화칸 = form.querySelector('input[type="tel"]');
    if (전화칸) {
      전화칸.addEventListener("input", function () { 전화칸.value = 하이픈(전화칸.value); });
    }

    var msg = form.querySelector(".msg");
    if (!msg) {
      msg = document.createElement("p");
      msg.className = "msg";
      form.appendChild(msg);
    }

    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      if (form.dataset.sending === "1") return;

      var btn = form.querySelector('button[type="submit"], .btn');
      var label = btn ? btn.textContent : "";

      var data = {};
      Array.prototype.forEach.call(form.elements, function (el) {
        if (!el.name) return;
        if (el.type === "checkbox") data[el.name] = el.checked ? "1" : "";
        else data[el.name] = el.value;
      });
      // 동의 체크박스는 name이 없을 수 있으므로 따로 확인
      var agreeBox = form.querySelector('input[type="checkbox"]');
      if (agreeBox) data.agree = agreeBox.checked ? "1" : "";

      var 문제 = 검사(data);
      if (문제) {
        show(msg, "err", 문제.말);
        짚기(form, 문제.칸);
        return;
      }

      form.dataset.sending = "1";
      if (btn) { btn.disabled = true; btn.textContent = "보내는 중…"; }
      show(msg, "", "");

      fetch(ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
      })
        .then(function (r) { return r.json().catch(function () { return { ok: false, message: "잠시 후 다시 시도해 주세요." }; }); })
        .then(function (res) {
          if (res.ok) {
            form.reset();
            hidden(form, "t", String(Math.floor(Date.now() / 1000)));
            show(msg, "", "");
            띄우기("ok", "접수되었습니다",
              (res.message || "확인 후 담당자가 연락드리겠습니다.") +
              "<br>급하시면 바로 전화 주셔도 됩니다." +
              '<a class="pop-tel" href="tel:15555528">1555-5528</a>');
          } else {
            show(msg, "err", res.message || "접수하지 못했습니다.");
            띄우기("err", "접수하지 못했습니다",
              (res.message || "잠시 후 다시 시도해 주세요.") +
              "<br>계속 안 되시면 전화로 알려주세요." +
              '<a class="pop-tel" href="tel:15555528">1555-5528</a>');
          }
        })
        .catch(function () {
          show(msg, "err", "접수하지 못했습니다.");
          띄우기("err", "접수하지 못했습니다",
            "인터넷 연결이 끊겼거나 서버에 닿지 못했습니다.<br>전화로 알려주시면 바로 도와드리겠습니다." +
            '<a class="pop-tel" href="tel:15555528">1555-5528</a>');
        })
        .then(function () {
          form.dataset.sending = "";
          if (btn) { btn.disabled = false; btn.textContent = label; }
        });
    });
  }

  function show(el, kind, text) {
    el.className = "msg" + (kind ? " " + kind : "");
    el.textContent = text;
  }

  /* 접수 결과를 화면 가운데 팝업으로 띄운다.
     버튼 아래 작은 글씨는 스크롤 위치에 따라 안 보여서 놓치는 분이 있었다. */
  var 팝업;
  function 팝업만들기() {
    if (팝업) return 팝업;
    팝업 = document.createElement("div");
    팝업.className = "pop";
    팝업.innerHTML = '<div class="pop-box" role="alertdialog" aria-modal="true"></div>';
    document.body.appendChild(팝업);
    return 팝업;
  }

  function 띄우기(kind, 제목, 내용) {
    var p = 팝업만들기();
    var ok = kind === "ok";
    var 아이콘 = ok
      ? '<svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"/></svg>'
      : '<svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><path d="M12 8v5M12 17h.01"/><circle cx="12" cy="12" r="9"/></svg>';
    p.querySelector(".pop-box").innerHTML =
      '<div class="pop-ico ' + (ok ? "ok" : "err") + '">' + 아이콘 + "</div>" +
      "<h3></h3><p></p>" +
      '<button type="button" class="btn btn-brand">확인</button>';
    p.querySelector("h3").textContent = 제목;
    p.querySelector("p").innerHTML = 내용;
    p.classList.add("on");

    var 닫기 = function () { p.classList.remove("on"); };
    p.querySelector("button").onclick = 닫기;
    p.onclick = function (e) { if (e.target === p) 닫기(); };
    document.addEventListener("keydown", function esc(e) {
      if (e.key === "Escape") { 닫기(); document.removeEventListener("keydown", esc); }
    });
    try { p.querySelector("button").focus(); } catch (e) {}
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  function init() {
    Array.prototype.forEach.call(document.querySelectorAll("form.lead"), setup);
  }
})();
