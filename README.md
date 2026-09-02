# 지오테스 홈페이지

㈜지오테스솔루션 / 지오테스 컨택센터 솔루션 사이트.

정적 HTML + CSS만 씁니다. 빌드 도구도, 프레임워크도, 의존성 설치도 없습니다.
페이지는 Python 스크립트로 생성합니다.

---

## 폴더

```
dist/                    배포되는 것 전부
  index.html             홈
  assets/nova.css        랜딩형 스타일 (홈·솔루션·업종)
  assets/nova-post.css   문서형 스타일 (정보글·지역 페이지)
  solution/              솔루션 상세 8 + 허브 (자동 생성)
_tools/
  gen_solution.py        솔루션 페이지 생성기
_notes/                  기획 문서 (배포 대상 아님)
```

## 페이지 다시 만들기

```bash
python _tools/gen_solution.py
```

내용을 고칠 때는 `_tools/gen_solution.py` 안의 `PAGES` 목록만 수정하면 됩니다.
HTML을 직접 손대지 마세요. 다시 생성하면 덮어써집니다.

## 로컬에서 보기

```bash
python -m http.server 8791 --directory dist
```

http://localhost:8791

---

## 지역 페이지 5만 장 (PHP)

`dist/_router.php` 파일 하나가 **53,238개 지역 페이지**를 만들어 냅니다.
HTML을 미리 뽑아 두지 않기 때문에 문구를 한 줄 고치면 5만 장에 바로 반영됩니다.

```
/local/                                   전국 허브             1
/local/{시도}/                             시도 허브            17
/local/{시도}/{시군구}/                     시군구 허브         229
/local/{시도}/{시군구}/{업종}/               시군구 × 업종     7,557
/local/{시도}/{시군구}/{읍면동}/             읍면동 허브       3,495
/local/{시도}/{시군구}/{읍면동}/{서비스}/     읍면동 × 서비스  41,940
/local/sitemap.xml                        사이트맵 목록
/local/sitemap-{시도}.xml                  시도별 사이트맵
```

**필요 환경** — PHP 7.4 이상, Apache mod_rewrite (`dist/.htaccess` 참고)
nginx면 `location /local/ { try_files $uri /_router.php; }` 한 줄이면 됩니다.

**로컬에서 확인**

```bash
php -S 127.0.0.1:8792 -t dist dist/_router.php
```

http://127.0.0.1:8792/local/seoul/gangnam/hospital/

**데이터**

| 파일 | 내용 |
|---|---|
| `_data/regions-index.json` | 시도·시군구 목록 (9KB, 매 요청 로드) |
| `_data/regions/{시도}.json` | 읍면동 포함 상세 (필요할 때만 로드) |
| `_data/topics.json` | 업종 33 · 서비스 12 |

지역 데이터는 `node _tools/extract_regions.mjs`, 주제는 `python _tools/gen_topics.py`로 다시 만듭니다.

> ⚠️ **GitHub Pages에서는 `/local/` 페이지가 뜨지 않습니다.** PHP를 실행하지 못하기 때문입니다.
> 미리보기에서는 정적 페이지 42장만 보입니다. 지역 페이지는 PHP가 되는 서버에 올려야 동작합니다.

---

## 상담 신청 폼

홈(`#lead`)과 상담문의 페이지의 폼이 `dist/_lead.php` 로 들어갑니다.
받으면 **파일로 남기고, 텔레그램·이메일로 알립니다.**

**설정 (한 번만)**

```bash
cp dist/_config.example.php dist/_config.php
```

`_config.php` 를 열어 값을 채웁니다. 비워 두면 그 기능만 꺼지고 접수는 계속 됩니다.

| 항목 | 설명 |
|---|---|
| `telegram_token` · `telegram_chat_id` | 텔레그램 즉시 알림 (선택) |
| `mail_to` | 이메일 알림 (선택, 서버에 메일 발송 설정 필요) |
| `admin_key` | `/_leads.php?key=값` 으로 목록을 볼 때 쓰는 열쇠. **길게 정하세요** |
| `store_dir` | 비워 두면 웹 폴더 바깥에 자동 생성 |

> ⚠️ `_config.php` 는 반드시 **UTF-8 (BOM 없음)** 으로 저장하세요.
> 메모장으로 저장하면 앞에 보이지 않는 문자가 붙어 접수가 통째로 실패합니다.

**들어온 신청 보기** — `https://도메인/_leads.php?key=설정한값`

**저장 위치** — 개인정보가 담기므로 기본값이 **웹 폴더 바깥**(`../_ziotes_leads`)입니다.
주소로 접근할 수 없는 자리입니다. 바깥에 못 만드는 환경이면 `dist/_leads/` 로 물러서고
그 폴더의 `.htaccess` 가 막습니다. **nginx를 쓰신다면** `.htaccess` 를 읽지 않으므로
`location ~ ^/_(leads|data|config)` 를 막아 두시거나 `store_dir` 을 웹 밖 경로로 지정하세요.

**막아 둔 것** — 숨은 입력칸(봇 판별), 폼 연 뒤 최소 대기시간, 같은 IP 시간당 건수 제한,
글자 수 제한, 전화번호 형식 검사, 동의 여부 확인.

---

## 배포

`dist/` 폴더를 그대로 올리면 됩니다.

**Cloudflare Pages** — 빌드 명령 없음, 출력 디렉터리 `dist`
**GitHub Pages** — 저장소 설정에서 Pages 소스를 `GitHub Actions` 로 지정하면
`.github/workflows/pages.yml` 이 `dist/` 를 알아서 올립니다.

사이트 안의 링크는 페이지 깊이에 맞는 상대경로로 자동 변환되므로
(`gen_solution.py` 의 `relativize`), `아이디.github.io/저장소이름/` 같은
하위 주소로 올려도 화면은 깨지지 않습니다.

---

## 다른 계정에 그대로 올리려면

1. 이 저장소를 **Fork** 하거나 내려받아 본인 계정에 새 저장소로 올립니다.
2. 저장소 **Settings → Pages → Source** 를 `GitHub Actions` 로 바꿉니다.
3. `main` 브랜치에 푸시하면 자동으로 배포됩니다.

주소를 `아이디.github.io/` (하위 경로 없이)로 쓰려면 저장소 이름을
**`아이디.github.io`** 로 지어야 합니다. GitHub 규칙입니다.

옮긴 뒤 바꿔야 하는 값 두 가지 — 둘 다 `_tools/gen_solution.py` 맨 위에 있습니다.

| 값 | 무엇 | 바꾼 뒤 |
|---|---|---|
| `SITE` | 검색엔진에 알리는 정식 주소 | `python _tools/gen_solution.py` 등 생성기 재실행 |
| `OG_BASE` | 카톡·문자로 링크 보낼 때 뜨는 썸네일 주소 | 〃 |

> ⚠️ `dist/_lead.php`(상담 접수), `dist/_leads.php`(신청 목록), `dist/_router.php`
> (지역 페이지)는 **PHP가 도는 서버에서만 동작**합니다. GitHub Pages는 PHP를
> 실행하지 못해 상담 신청이 저장되지 않습니다. 상담폼을 쓰려면 PHP 호스팅이나
> Cloudflare Pages(Functions)로 옮겨야 합니다.

---

## 디자인

퍼플/그린 Nova. 색·간격·컴포넌트 규칙은 `_notes/디자인시스템.md`에 있습니다.

- 브랜드 `#6d4aff` / 포인트 `#35e0a1` `#ffd53e`
- 본문 Pretendard, 숫자·영문 Poppins
- UI에 이모지를 쓰지 않습니다. 아이콘은 인라인 SVG
- 새 콜아웃·인용박스를 만들지 않습니다. 있는 서식만 씁니다

## 아직 확정되지 않은 것

요금, 무상 지원 범위, AI 기능 판매 범위, 보유 인증, 고객사 표기 방식이
확정 전입니다. 해당 자리는 구조만 잡아두었고 `_notes/사장님_확인요청.md`에
질문을 정리해 두었습니다.
