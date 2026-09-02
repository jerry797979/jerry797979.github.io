<?php
/**
 * 상담 신청 목록 (관리자용)
 *
 *   /_leads.php?key=설정한열쇠값
 *
 * _config.php 의 admin_key 를 비워 두면 이 화면은 열리지 않습니다.
 * 열쇠값은 길고 추측하기 어려운 값으로 정하세요.
 */

/* PHP 7.4 호환 — str_starts_with 는 PHP 8.0부터 있습니다.
   낮은 버전에서 이 함수를 부르면 화면이 통째로 죽어(500) 버리므로 직접 채워 둡니다. */
if (!function_exists('str_starts_with')) {
    function str_starts_with($haystack, $needle) {
        return strncmp($haystack, $needle, strlen($needle)) === 0;
    }
}

$cfg = is_file(__DIR__ . '/_config.php') ? require __DIR__ . '/_config.php' : [];
$key = (string)($cfg['admin_key'] ?? '');
$dir = $cfg['store_dir'] ?? null;
if (!$dir) {
    $outside = dirname(__DIR__) . '/_ziotes_leads';
    $dir = is_dir($outside) ? $outside : (__DIR__ . '/_leads');
}

header('Content-Type: text/html; charset=utf-8');
header('X-Robots-Tag: noindex, nofollow');

$given = (string)($_GET['key'] ?? '');
if ($key === '' || !hash_equals($key, $given)) {
    http_response_code(404);
    echo '<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8"><title>404</title></head>'
       . '<body style="font-family:system-ui;display:grid;place-items:center;height:100vh;margin:0">'
       . '<p style="color:#64748b">페이지를 찾을 수 없습니다.</p></body></html>';
    exit;
}

// ---------------------------------------------------------------- 읽기

$rows = [];
foreach (glob($dir . '/*.jsonl') ?: [] as $f) {
    foreach (file($f, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) as $line) {
        $r = json_decode($line, true);
        if (is_array($r)) $rows[] = $r;
    }
}
usort($rows, fn($a, $b) => strcmp($b['at'] ?? '', $a['at'] ?? ''));

$today = date('Y-m-d');
$cntToday = count(array_filter($rows, fn($r) => str_starts_with($r['at'] ?? '', $today)));
$cntMonth = count(array_filter($rows, fn($r) => str_starts_with($r['at'] ?? '', date('Y-m'))));

$esc = fn($s) => htmlspecialchars((string)$s, ENT_QUOTES, 'UTF-8');

$tr = '';
foreach (array_slice($rows, 0, 300) as $r) {
    $memo = trim((string)($r['memo'] ?? ''));
    $tel  = preg_replace('/[^0-9]/', '', (string)($r['tel'] ?? ''));
    $tr .= '<tr>'
         . '<td class="dim">' . $esc($r['at'] ?? '') . '</td>'
         . '<td>' . $esc($r['company'] ?? '-') . '</td>'
         . '<td><b>' . $esc($r['name'] ?? '') . '</b></td>'
         . '<td><a href="tel:' . $esc($tel) . '">' . $esc($r['tel'] ?? '') . '</a></td>'
         . '<td>' . $esc($r['size'] ?? '-') . '</td>'
         . '<td class="memo">' . ($memo !== '' ? nl2br($esc($memo)) : '<span class="dim">-</span>') . '</td>'
         . '<td class="dim">' . $esc($r['page'] ?? '') . '</td>'
         . '</tr>';
}
if ($tr === '') $tr = '<tr><td colspan="7" class="dim" style="text-align:center;padding:40px">아직 들어온 신청이 없습니다.</td></tr>';

$total = count($rows);
?><!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex, nofollow">
<title>상담 신청 목록 · 지오테스</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:Pretendard,system-ui,sans-serif;background:#f8fafc;color:#16121f;padding:28px 20px;line-height:1.6}
.wrap{max-width:1200px;margin:0 auto}
h1{font-size:21px;font-weight:800}
.sum{display:flex;gap:10px;margin:16px 0 20px;flex-wrap:wrap}
.sum div{background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:12px 18px;min-width:110px}
.sum small{display:block;color:#94a3b8;font-size:12px}
.sum b{font-size:22px;font-weight:800}
.box{background:#fff;border:1px solid #e2e8f0;border-radius:14px;overflow:auto}
table{width:100%;border-collapse:collapse;font-size:14px;min-width:900px}
th,td{padding:12px 14px;text-align:left;border-bottom:1px solid #f1f5f9;vertical-align:top}
thead th{background:#16121f;color:#fff;font-size:12.5px;font-weight:700;white-space:nowrap;position:sticky;top:0}
tbody tr:hover{background:#f8fafc}
tr:last-child td{border-bottom:none}
td a{color:#6d4aff;font-weight:700;text-decoration:none}
.dim{color:#94a3b8;font-size:12.5px}
.memo{max-width:340px;font-size:13px;color:#475569}
.note{color:#94a3b8;font-size:12.5px;margin-top:14px}
</style>
</head>
<body>
<div class="wrap">
  <h1>상담 신청 목록</h1>
  <div class="sum">
    <div><small>오늘</small><b><?= $cntToday ?></b></div>
    <div><small>이번 달</small><b><?= $cntMonth ?></b></div>
    <div><small>전체</small><b><?= $total ?></b></div>
  </div>
  <div class="box">
    <table>
      <thead><tr><th>접수 시각</th><th>회사</th><th>담당자</th><th>연락처</th><th>규모</th><th>문의 내용</th><th>들어온 경로</th></tr></thead>
      <tbody><?= $tr ?></tbody>
    </table>
  </div>
  <p class="note">최근 300건까지 보여 줍니다. 원본은 <code><?= $esc(basename($dir)) ?>/</code> 폴더에 월별 파일로 쌓입니다.</p>
</div>
</body>
</html>
