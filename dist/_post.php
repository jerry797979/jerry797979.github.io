<?php
/**
 * 정보 글 올리기 API — /posts/ 에 글을 원격으로 올립니다.
 *
 * 지오테스 사이트는 원래 우리 쪽 컴퓨터에서 페이지를 만들어 git 으로 올립니다.
 * 그런데 ziotes.com 은 거래처 서버라서 우리가 git pull 을 대신 눌러 줄 수 없습니다.
 * 그래서 만들어 둔 페이지를 HTTP 로 보내 바로 반영하는 통로가 이 파일입니다.
 *
 *   POST /_post.php
 *   헤더  X-Post-Key: (_config.php 의 post_key 값)
 *   본문  {"slug":"...", "title":"...", "html":"...", "index":"...", "sitemap":"..."}
 *
 * 하는 일은 파일 세 개를 쓰는 것뿐입니다.
 *   posts/{slug}/index.html   ← html    (새 글)
 *   posts/index.html          ← index   (글 목록)
 *   sitemap.xml               ← sitemap (선택)
 *
 * 페이지 모양을 여기서 만들지 않는 이유
 *   같은 서식을 파이썬(_tools/gen_posts.py)과 PHP 두 군데에 두면 반드시 어긋납니다.
 *   한쪽만 고치는 날이 오기 때문입니다. 그래서 모양은 파이썬 한 곳에서만 만들고
 *   이 파일은 받아 적기만 합니다.
 *
 *   보내는 쪽은 _tools/push_post.py 입니다.
 *
 * 여기서 쓴 글은 우리 저장소에도 똑같이 들어갑니다.
 * 그래서 나중에 git pull 을 하셔도 같은 내용이라 충돌하지 않습니다.
 */

/* PHP 7.4 호환 — str_starts_with 는 PHP 8.0부터 있습니다.
   낮은 버전에서 부르면 화면이 통째로 죽어(500) 버리므로 직접 채워 둡니다. */
if (!function_exists('str_starts_with')) {
    function str_starts_with($haystack, $needle) {
        return strncmp($haystack, $needle, strlen($needle)) === 0;
    }
}

header('Content-Type: application/json; charset=utf-8');
header('X-Content-Type-Options: nosniff');

const MAX_BYTES = 2097152;   // 한 요청 2MB — 글 한 편은 보통 40KB 안쪽입니다

function done(bool $ok, string $msg, int $code = 200, array $extra = []) {
    http_response_code($code);
    echo json_encode(['ok' => $ok, 'message' => $msg] + $extra, JSON_UNESCAPED_UNICODE);
    exit;
}

$cfgFile = __DIR__ . '/_config.php';
$cfg = is_file($cfgFile) ? require $cfgFile : [];
$cfg += ['post_key' => ''];

/* 열쇠를 안 정해 두셨으면 기능 자체를 꺼 둡니다.
   빈 값을 통과시키면 아무나 글을 올릴 수 있게 됩니다. */
if ($cfg['post_key'] === '' || strlen($cfg['post_key']) < 20) {
    done(false, '글 올리기가 꺼져 있습니다. _config.php 의 post_key 를 20자 이상으로 정해 주세요.', 503);
}

/** 기록을 남길 곳 — 웹 폴더 바깥입니다. */
function log_line(string $line) {
    $dir = dirname(__DIR__) . '/_ziotes_posts';
    if (!is_dir($dir)) @mkdir($dir, 0700, true);
    if (!is_writable($dir)) return;
    @file_put_contents($dir . '/post.log',
        date('Y-m-d H:i:s') . "\t" . ($_SERVER['REMOTE_ADDR'] ?? '-') . "\t" . $line . "\n",
        FILE_APPEND | LOCK_EX);
}

/** 보낸 열쇠 꺼내기 — 헤더가 우선이고, 안 되는 환경을 위해 ?key= 도 받습니다. */
function sent_key(): string {
    $h = $_SERVER['HTTP_X_POST_KEY'] ?? '';
    if ($h !== '') return trim($h);
    return trim($_GET['key'] ?? '');
}

/* 열쇠 대조 — 글자를 하나씩 비교하면 걸린 시간으로 열쇠를 추측당할 수 있어
   hash_equals 로 항상 같은 시간이 걸리게 비교합니다. */
if (!hash_equals((string) $cfg['post_key'], sent_key())) {
    log_line("거부\t열쇠 틀림");
    done(false, '열쇠가 맞지 않습니다.', 403);
}

// ---------------------------------------------------------------- 목록 보기

/* GET 은 올라와 있는 글을 확인하는 용도입니다.
   보낸 쪽에서 "제대로 들어갔나" 확인할 때 씁니다. */
if (($_SERVER['REQUEST_METHOD'] ?? '') === 'GET') {
    $items = [];
    foreach (glob(__DIR__ . '/posts/*/index.html') ?: [] as $f) {
        $items[] = [
            'slug'  => basename(dirname($f)),
            'bytes' => filesize($f),
            'at'    => date('c', filemtime($f)),
        ];
    }
    usort($items, function ($a, $b) { return strcmp($b['at'], $a['at']); });
    done(true, '목록입니다.', 200, ['count' => count($items), 'posts' => $items]);
}

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    done(false, 'POST 로 보내 주세요.', 405);
}

// ---------------------------------------------------------------- 입력

$raw = file_get_contents('php://input');
if ($raw === false || $raw === '') {
    done(false, '내용이 비어 있습니다.', 400);
}
if (strlen($raw) > MAX_BYTES) {
    done(false, '내용이 너무 큽니다. 2MB 까지 받습니다.', 413);
}

$in = json_decode($raw, true);
if (!is_array($in)) {
    done(false, 'JSON 형식이 아닙니다.', 400);
}

$slug = trim((string) ($in['slug'] ?? ''));
if (!preg_match('/^[a-z0-9][a-z0-9-]{2,63}$/', $slug)) {
    done(false, 'slug 는 영문 소문자·숫자·하이픈으로 3~64자여야 합니다.', 400);
}

/** 넘어온 HTML 이 온전한 페이지인지 본다. 잘려서 오면 페이지가 깨집니다. */
function check_page(string $what, $v): string {
    if (!is_string($v) || $v === '') done(false, $what . ' 이(가) 비어 있습니다.', 400);
    if (!preg_match('/^\s*<!doctype html/i', $v)) {
        done(false, $what . ' 이(가) 온전한 페이지가 아닙니다. <!doctype html> 로 시작해야 합니다.', 400);
    }
    if (stripos($v, '</html>') === false) {
        done(false, $what . ' 이(가) 중간에 잘린 것 같습니다. </html> 이 없습니다.', 400);
    }
    return $v;
}

$html  = check_page('html', $in['html'] ?? null);
$index = check_page('index', $in['index'] ?? null);

$sitemap = null;
if (isset($in['sitemap']) && $in['sitemap'] !== '') {
    if (!is_string($in['sitemap']) || stripos($in['sitemap'], '<urlset') === false) {
        done(false, 'sitemap 이 sitemap.xml 형식이 아닙니다.', 400);
    }
    $sitemap = $in['sitemap'];
}

// ---------------------------------------------------------------- 쓰기

/**
 * 파일 하나를 안전하게 바꿔 쓴다.
 *
 * 곧바로 덮어쓰면 쓰는 도중에 누가 그 주소를 열었을 때 반쪽짜리 페이지를 보게 됩니다.
 * 그래서 임시 파일에 다 쓴 뒤 이름만 바꿉니다. 이름 바꾸기는 순식간이라 중간이 없습니다.
 *
 * 바뀌기 전 내용은 한 벌 남기되 웹 폴더 '바깥'에 둡니다.
 * 안쪽에 .bak 으로 두면 그 주소로 옛 페이지가 그대로 열려 버립니다.
 */
function put(string $path, string $data): bool {
    $dir = dirname($path);
    if (!is_dir($dir) && !@mkdir($dir, 0755, true)) return false;

    $tmp = $path . '.tmp' . getmypid();
    if (@file_put_contents($tmp, $data, LOCK_EX) !== strlen($data)) {
        @unlink($tmp);
        return false;
    }
    @chmod($tmp, 0644);

    if (is_file($path)) {
        $bak = dirname(__DIR__) . '/_ziotes_posts/bak';
        if (is_dir($bak) || @mkdir($bak, 0700, true)) {
            @copy($path, $bak . '/' . str_replace('/', '_', ltrim(substr($path, strlen(__DIR__)), '/')));
        }
    }
    if (!@rename($tmp, $path)) {
        @unlink($tmp);
        return false;
    }
    return true;
}

$쓴것 = [];

if (!put(__DIR__ . '/posts/' . $slug . '/index.html', $html)) {
    log_line("실패\t{$slug}\t글 파일을 쓰지 못함");
    done(false, '글 파일을 쓰지 못했습니다. dist/posts 폴더의 쓰기 권한을 확인해 주세요.', 500);
}
$쓴것[] = "posts/{$slug}/index.html";

/* 목록과 사이트맵은 글이 이미 들어간 뒤라 실패해도 글은 살아 있습니다.
   그래서 통째로 실패로 돌리지 않고 무엇이 안 됐는지 알려 줍니다. */
$못쓴것 = [];
if (put(__DIR__ . '/posts/index.html', $index)) $쓴것[] = 'posts/index.html';
else $못쓴것[] = 'posts/index.html';

if ($sitemap !== null) {
    if (put(__DIR__ . '/sitemap.xml', $sitemap)) $쓴것[] = 'sitemap.xml';
    else $못쓴것[] = 'sitemap.xml';
}

log_line("성공\t{$slug}\t" . implode(',', $쓴것) . ($못쓴것 ? "\t실패:" . implode(',', $못쓴것) : ''));

done(true, $못쓴것 ? '글은 올라갔지만 일부 파일을 쓰지 못했습니다.' : '올렸습니다.', 200, [
    'slug'    => $slug,
    'url'     => '/posts/' . $slug . '/',
    'written' => $쓴것,
    'failed'  => $못쓴것,
]);
