<?php
/**
 * 상담 신청 접수
 *
 * 폼에서 POST로 받아서
 *   1) 검사하고  2) 파일로 남기고  3) 텔레그램·이메일로 알립니다.
 *
 * 설정은 _config.php 에 있습니다. (_config.example.php 를 복사해서 만드세요)
 * 저장 위치는 _leads/ 이며 웹에서 직접 열리지 않도록 막아 두었습니다.
 */

/* PHP 7.4 호환 — str_starts_with 는 PHP 8.0부터 있습니다.
   낮은 버전에서 이 함수를 부르면 화면이 통째로 죽어(500) 버리므로 직접 채워 둡니다. */
if (!function_exists('str_starts_with')) {
    function str_starts_with($haystack, $needle) {
        return strncmp($haystack, $needle, strlen($needle)) === 0;
    }
}

header('Content-Type: application/json; charset=utf-8');
header('X-Content-Type-Options: nosniff');

function done(bool $ok, string $msg, int $code = 200) {
    http_response_code($code);
    echo json_encode(['ok' => $ok, 'message' => $msg], JSON_UNESCAPED_UNICODE);
    exit;
}

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    done(false, '잘못된 접근입니다.', 405);
}

$cfgFile = __DIR__ . '/_config.php';
$cfg = is_file($cfgFile) ? require $cfgFile : [];
$cfg += [
    'telegram_token' => '', 'telegram_chat_id' => '',
    'mail_to' => '', 'mail_from' => 'no-reply@ziotes.com',
    'admin_key' => '', 'store_dir' => null,
    'min_seconds' => 3, 'per_ip_limit' => 5,
];

/**
 * 신청 내용을 저장할 폴더.
 *
 * 개인정보가 담기므로 웹에서 열리면 안 됩니다.
 * .htaccess 로 막아 두었지만 nginx 처럼 .htaccess 를 읽지 않는 서버도 있어서,
 * 기본값을 웹 폴더 '바깥'으로 잡습니다. 바깥에 못 만들면 안쪽으로 물러섭니다.
 */
function store_dir(array $cfg): string {
    if (!empty($cfg['store_dir'])) return $cfg['store_dir'];
    $outside = dirname(__DIR__) . '/_ziotes_leads';
    if (is_dir($outside) || @mkdir($outside, 0700, true)) {
        if (is_writable($outside)) return $outside;
    }
    return __DIR__ . '/_leads';   // 물러선 경우 — .htaccess 가 막아 줍니다
}

// ---------------------------------------------------------------- 입력

$in = $_POST;
if (empty($in)) {                       // fetch 로 JSON을 보낸 경우
    $raw = file_get_contents('php://input');
    $j = json_decode($raw, true);
    if (is_array($j)) $in = $j;
}

/** 글자 수로 자릅니다. mbstring 확장이 없는 서버에서도 한글이 깨지지 않게 처리합니다. */
function cut(string $s, int $max): string {
    if (function_exists('mb_substr')) return mb_substr($s, 0, $max, 'UTF-8');
    if (preg_match('/^.{0,' . $max . '}/us', $s, $m)) return $m[0];
    return substr($s, 0, $max);
}

$get = function (string $k, int $max = 200) use ($in) {
    $v = trim((string)($in[$k] ?? ''));
    $v = preg_replace('/[\x00-\x08\x0B\x0C\x0E-\x1F]/u', '', $v);   // 제어문자 제거
    return cut((string)$v, $max);
};

// 사람이 아니면 걸러낸다 ─ 봇은 숨은 칸을 채우고, 너무 빨리 보낸다
if ($get('website') !== '') done(true, '접수되었습니다.');          // 벌집(honeypot)
// 폼을 연 시각과의 차이. 방문자 기기 시계가 서버보다 앞서면 음수가 나올 수 있는데,
// 그때는 막지 않습니다. 시계가 틀렸다고 정상 문의를 놓치면 안 됩니다.
$openedAt = (int)$get('t', 20);
$age = time() - $openedAt;
if ($openedAt > 0 && $age >= 0 && $age < (int)$cfg['min_seconds']) {
    done(false, '잠시 후 다시 눌러 주세요.', 429);
}

$company = $get('company', 100);
$name    = $get('name', 50);
$tel     = $get('tel', 30);
$size    = $get('size', 40);
$memo    = $get('memo', 2000);
$agree   = $get('agree', 10);
$page    = $get('page', 200);

if ($name === '' || $tel === '')       done(false, '담당자와 연락처를 적어 주세요.', 422);
if (!preg_match('/^[0-9+\-\s()]{8,30}$/', $tel)) done(false, '연락처를 다시 확인해 주세요.', 422);
if ($agree === '')                     done(false, '개인정보 수집·이용에 동의해 주세요.', 422);

// ---------------------------------------------------------------- 같은 IP 제한

$ip = $_SERVER['HTTP_X_FORWARDED_FOR'] ?? $_SERVER['REMOTE_ADDR'] ?? '-';
$ip = trim(explode(',', $ip)[0]);

$dir = store_dir($cfg);
if (!is_dir($dir)) @mkdir($dir, 0700, true);

$rateFile = $dir . '/.rate';
$now = time();
$rates = is_file($rateFile) ? (json_decode(file_get_contents($rateFile), true) ?: []) : [];
$rates = array_filter($rates, fn($t) => $t > $now - 3600);          // 한 시간 지난 기록은 버림
$mine = count(array_filter($rates, fn($t, $k) => str_starts_with($k, $ip . '|'), ARRAY_FILTER_USE_BOTH));
if ($mine >= (int)$cfg['per_ip_limit']) {
    done(false, '접수가 너무 많습니다. 잠시 후 다시 시도해 주세요.', 429);
}
$rates[$ip . '|' . $now . '|' . random_int(100, 999)] = $now;
@file_put_contents($rateFile, json_encode($rates), LOCK_EX);

// ---------------------------------------------------------------- 저장

$row = [
    'at'      => date('Y-m-d H:i:s'),
    'company' => $company,
    'name'    => $name,
    'tel'     => $tel,
    'size'    => $size,
    'memo'    => $memo,
    'page'    => $page,
    'ip'      => $ip,
];

$file = $dir . '/' . date('Y-m') . '.jsonl';
$saved = @file_put_contents($file, json_encode($row, JSON_UNESCAPED_UNICODE) . "\n", FILE_APPEND | LOCK_EX);
if ($saved === false) {
    error_log('[lead] 저장 실패: ' . $file);
}

// ---------------------------------------------------------------- 알림

$lines = [
    '상담 신청이 들어왔습니다',
    '',
    '회사   ' . ($company ?: '-'),
    '담당자 ' . $name,
    '연락처 ' . $tel,
    '규모   ' . ($size ?: '-'),
    '내용   ' . ($memo ?: '-'),
    '',
    '경로   ' . ($page ?: '-'),
    '시각   ' . $row['at'],
];
$text = implode("\n", $lines);

if ($cfg['telegram_token'] && $cfg['telegram_chat_id']) {
    $url = 'https://api.telegram.org/bot' . $cfg['telegram_token'] . '/sendMessage';
    $body = http_build_query([
        'chat_id' => $cfg['telegram_chat_id'],
        'text' => $text,
        'disable_web_page_preview' => 'true',
    ]);
    $ctx = stream_context_create(['http' => [
        'method' => 'POST',
        'header' => "Content-Type: application/x-www-form-urlencoded\r\n",
        'content' => $body,
        'timeout' => 5,
        'ignore_errors' => true,
    ]]);
    @file_get_contents($url, false, $ctx);
}

if ($cfg['mail_to'] && function_exists('mail')) {
    $subject = '=?UTF-8?B?' . base64_encode('[지오테스] 상담 신청 - ' . $name) . '?=';
    $headers = "From: " . $cfg['mail_from'] . "\r\n"
             . "Content-Type: text/plain; charset=UTF-8\r\n";
    @mail($cfg['mail_to'], $subject, $text, $headers);
}

done(true, '접수되었습니다. 확인 후 연락드리겠습니다.');
