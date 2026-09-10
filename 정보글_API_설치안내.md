# 정보 글 자동 등록 기능 — 서버 설치 안내

ziotes.com 의 **정보**(`/posts/`) 에 글을 자동으로 올릴 수 있게 하는 작업입니다.

지금은 저희가 글을 만들어 저장소에 올리면, 서버에서 `git pull` 을 눌러 주셔야
화면에 나옵니다. 글을 매일 올리게 되면 그때마다 부탁드릴 수가 없습니다.
그래서 **저희 쪽에서 곧바로 보내면 바로 반영되는 통로**를 하나 만들었습니다.

**해 주실 일은 두 가지입니다.**

1. `git pull` 로 새 파일 받기
2. `_config.php` 에 열쇠 한 줄 넣기

nginx 설정은 **고치실 것이 없습니다.** 새로 여는 포트도 없습니다.

---

## 1. 새 파일 받기

```bash
cd /var/www/ziotes
git pull
sudo chown -R www-data:www-data dist
```

이번에 들어가는 파일은 하나입니다.

- `dist/_post.php` — 글을 받아 파일로 쓰는 부분

---

## 2. 열쇠 만들어 넣기

아무나 글을 올릴 수 있으면 안 되므로 열쇠로 막습니다.
열쇠는 **서버에서 만들어 주시고, 저희에게 알려 주십시오.**

### 2-1. 열쇠 만들기

```bash
openssl rand -hex 20
```

`a3f9c1...` 처럼 40글자가 나옵니다. 이 값을 복사해 두세요.

### 2-2. `_config.php` 에 넣기

```bash
sudo nano /var/www/ziotes/dist/_config.php
```

`return [` 안에 아래 한 줄을 넣습니다. (기존 항목은 그대로 두세요.)

```php
'post_key' => '방금 만든 40글자',
```

저장하고 나옵니다. (`nano` 는 `Ctrl+O` → `Enter` → `Ctrl+X`)

> ⚠️ `_config.php` 는 반드시 **UTF-8 (BOM 없음)** 으로 저장하세요.
> 앞에 보이지 않는 문자가 붙으면 `headers already sent` 오류로
> **상담 접수까지 통째로 실패합니다.** 리눅스에서 `nano` 로 편집하시면 문제없습니다.

> `post_key` 를 비워 두거나 20자 미만으로 두면 이 기능은 **꺼진 상태**로 동작합니다.
> 실수로 열어 두는 일이 없도록 일부러 그렇게 만들었습니다.

### 2-3. 확인

```bash
curl -s -H "X-Post-Key: 넣으신열쇠" https://ziotes.com/_post.php
```

이렇게 나오면 정상입니다.

```json
{"ok":true,"message":"목록입니다.","count":1,"posts":[...]}
```

열쇠를 틀리게 넣으면 이렇게 나와야 합니다.

```json
{"ok":false,"message":"열쇠가 맞지 않습니다."}
```

---

## 3. 쓰기 권한 확인

글이 `dist/posts/` 안에 파일로 쌓입니다. 웹 서버 계정이 그 폴더에 쓸 수 있어야 합니다.

```bash
sudo -u www-data test -w /var/www/ziotes/dist/posts && echo "쓸 수 있음" || echo "권한 없음"
```

"권한 없음" 이면 아래를 실행해 주세요.

```bash
sudo chown -R www-data:www-data /var/www/ziotes/dist
```

---

## 이 통로가 하는 일

`dist/_post.php` 가 하는 일은 **파일 세 개를 쓰는 것**이 전부입니다.

- `dist/posts/{주소이름}/index.html` — 새 글
- `dist/posts/index.html` — 글 목록
- `dist/sitemap.xml` — 검색엔진용 목록

페이지 모양은 저희 쪽에서 만들어 완성된 상태로 보냅니다.
서버에서는 만들지 않습니다. **같은 서식을 두 군데에 두면 반드시 한쪽만 고치는 날이 와서**
화면이 어긋나기 때문입니다.

### 막아 둔 것

- **열쇠** — 40글자 이상. 맞지 않으면 403. 열쇠 대조는 걸린 시간으로 값을 추측당하지 않도록
  `hash_equals` 로 합니다.
- **주소이름 검사** — 영문 소문자·숫자·하이픈 3~64자만 받습니다.
  `../` 같은 것이 섞이면 거부하므로 다른 폴더에는 쓸 수 없습니다.
- **온전한 페이지인지 검사** — `<!doctype html>` 로 시작하고 `</html>` 로 끝나야 받습니다.
  전송이 중간에 끊겨 반쪽짜리 페이지가 올라가는 것을 막습니다.
- **크기 제한** — 한 번에 2MB 까지. 글 한 편은 보통 40KB 안쪽입니다.
- **덮어쓰기 방식** — 임시 파일에 다 쓴 뒤 이름만 바꿉니다.
  쓰는 도중에 누가 그 주소를 열어도 반쪽짜리 화면을 보지 않습니다.

### 남는 기록

- **작업 기록** — `/var/www/ziotes/_ziotes_posts/post.log`
  (언제, 어디서, 무엇이 올라갔는지 / 열쇠 틀린 시도도 남습니다)
- **바뀌기 전 파일** — `/var/www/ziotes/_ziotes_posts/bak/`

둘 다 **웹 폴더 바깥**입니다. 주소로 열리면 안 되는 것들이라 그렇게 두었습니다.

---

## git pull 과 부딪히지 않습니다

이 통로로 올린 글은 **저희 저장소에도 똑같이 들어갑니다.**
보낼 때 줄바꿈까지 리눅스 방식(LF)으로 맞춰 보내므로,
`git pull` 을 하셔도 git 이 "누가 파일을 고쳤다"고 보지 않습니다.

혹시라도 `git pull` 이 `dist/posts` 때문에 막히면 아래로 풀 수 있습니다.
서버에 있는 것과 저장소에 있는 것이 같은 내용이라 잃는 것이 없습니다.

```bash
cd /var/www/ziotes
git checkout -- dist/posts dist/sitemap.xml
git pull
```

---

## 문제가 생기면

**`{"ok":false,"message":"글 올리기가 꺼져 있습니다..."}`**
`_config.php` 에 `post_key` 가 없거나 20자보다 짧습니다. 2번을 다시 봐 주세요.

**`{"ok":false,"message":"열쇠가 맞지 않습니다."}`**
보낸 열쇠와 `_config.php` 값이 다릅니다. 앞뒤 공백이 붙지 않았는지 봐 주세요.

**`{"ok":false,"message":"글 파일을 쓰지 못했습니다..."}`**
`dist/posts` 쓰기 권한 문제입니다. 3번을 실행해 주세요.

**500 오류가 나거나 화면이 하얗게 나올 때**

```bash
sudo tail -30 /var/log/php*-fpm.log
sudo tail -30 /var/log/nginx/error.log
```

**동작 기록을 보고 싶을 때**

```bash
sudo tail -30 /var/www/ziotes/_ziotes_posts/post.log
```

---

## 저희에게 알려 주실 것

- **`post_key` 값** — 만드신 40글자

이 값을 받으면 저희 쪽에서 글을 보내 정상 등록되는지 확인한 뒤,
결과를 다시 알려 드리겠습니다.

열쇠는 **카카오톡·이메일 말고 다른 경로**로 주시면 더 좋습니다.
바꾸고 싶으실 때는 `_config.php` 값만 바꾸시면 그 즉시 옛 열쇠는 막힙니다.
저희에게 미리 알려 주실 필요도 없습니다.

---

## 붙임 — 통신 규격 (참고용, 설치에는 필요 없습니다)

```
POST https://ziotes.com/_post.php
헤더  X-Post-Key: {열쇠}
      Content-Type: application/json; charset=utf-8

{
  "slug":    "call-center-cost",          글 주소가 됩니다
  "html":    "<!doctype html>…</html>",   글 페이지 전체
  "index":   "<!doctype html>…</html>",   글 목록 페이지 전체
  "sitemap": "<?xml …</urlset>"           선택
}
```

**성공**

```json
{"ok":true,"message":"올렸습니다.","slug":"call-center-cost",
 "url":"/posts/call-center-cost/",
 "written":["posts/call-center-cost/index.html","posts/index.html","sitemap.xml"],
 "failed":[]}
```

**올라와 있는 글 확인**

```
GET https://ziotes.com/_post.php
헤더  X-Post-Key: {열쇠}
```

```json
{"ok":true,"count":2,"posts":[{"slug":"…","bytes":16135,"at":"2026-09-10T13:22:41+09:00"}]}
```

**응답 코드**

- `200` 성공
- `400` 보낸 내용이 규격에 안 맞음 (주소이름·페이지 형식)
- `403` 열쇠가 틀림
- `405` POST 나 GET 이 아님
- `413` 2MB 초과
- `500` 파일을 쓰지 못함 (권한)
- `503` `post_key` 가 설정되지 않아 기능이 꺼져 있음

---

문의사항 있으시면 연락 주시기 바랍니다.
