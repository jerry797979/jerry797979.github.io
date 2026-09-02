<?php
/**
 * 지오테스 지역 페이지 라우터
 *
 * 파일 하나로 5만 페이지를 만들어 냅니다. HTML을 미리 뽑아 두지 않기 때문에
 * 문구를 한 줄 고치면 전체 페이지에 바로 반영됩니다.
 *
 * 주소 구조
 *   /local/                                   전국 허브
 *   /local/{시도}/                             시도 허브
 *   /local/{시도}/{시군구}/                     시군구 허브
 *   /local/{시도}/{시군구}/{업종}/               시군구 x 업종      7,557
 *   /local/{시도}/{시군구}/{읍면동}/             읍면동 허브        3,495
 *   /local/{시도}/{시군구}/{읍면동}/{서비스}/     읍면동 x 서비스   41,940
 *   /local/sitemap.xml                        사이트맵 목록
 *   /local/sitemap-{시도}.xml                  시도별 사이트맵
 *
 * 데이터
 *   _data/regions.json  시도 17 / 시군구 229 / 읍면동 3,495
 *   _data/topics.json   업종 33 / 서비스 12
 *
 * 필요 환경: PHP 7.4 이상, mod_rewrite (.htaccess 참고)
 */

// ---------------------------------------------------------------- 설정

const SITE  = 'https://ziotes.com';
const BRAND = '지오테스';
const TEL   = '1555-5528';
const TEL_R = '15555528';

// ---------------------------------------------------------------- 데이터

// 통짜 파일(150KB)을 매 요청마다 읽지 않습니다.
// 목록은 얇은 색인에서, 읍면동까지 필요한 경우에만 해당 시도 파일을 읽습니다.
$IDX = json_decode(file_get_contents(__DIR__ . '/_data/regions-index.json'), true);
$TOP = json_decode(file_get_contents(__DIR__ . '/_data/topics.json'), true);

$PROV = [];      // 시도슬러그 => 시도(시군구 이름까지만)
foreach ($IDX['provinces'] as $p) $PROV[$p['slug']] = $p;

$IND = [];  foreach ($TOP['industries'] as $t) $IND[$t['slug']] = $t;
$SVC = [];  foreach ($TOP['services']   as $t) $SVC[$t['slug']] = $t;

/** 해당 시도의 전체 데이터(읍면동 포함)를 읽는다. 한 번 읽으면 재사용한다. */
function prov_full(string $slug) {
    static $cache = [];
    if (isset($cache[$slug])) return $cache[$slug];
    $f = __DIR__ . '/_data/regions/' . $slug . '.json';
    if (!is_file($f)) return null;
    return $cache[$slug] = json_decode(file_get_contents($f), true);
}

/** 시군구 하나를 읍면동까지 포함해 가져온다. */
function city_full(string $pslug, string $cslug) {
    $p = prov_full($pslug);
    if (!$p) return null;
    foreach ($p['cities'] as $c) if ($c['slug'] === $cslug) return $c;
    return null;
}

// ---------------------------------------------------------------- 도구

function esc($s) { return htmlspecialchars((string)$s, ENT_QUOTES, 'UTF-8'); }

/** 슬러그를 씨앗 삼아 목록에서 하나를 고른다. 페이지마다 문장이 달라지게 하는 용도. */
function pick(array $arr, string $seed) {
    return $arr[crc32($seed) % count($arr)];
}

/** 목록에서 n개를 씨앗 기준으로 골라 온다. (인접 지역 링크용) */
function around(array $arr, string $seed, int $n, $skip = null) {
    $out = [];
    $len = count($arr);
    if ($len === 0) return $out;
    $start = crc32($seed) % $len;
    for ($i = 0; $i < $len && count($out) < $n; $i++) {
        $it = $arr[($start + $i) % $len];
        if ($skip !== null && $it['slug'] === $skip) continue;
        $out[] = $it;
    }
    return $out;
}

function dong_of($city, $slug) {
    foreach ($city['dongs'] as $d) if ($d['slug'] === $slug) return $d;
    return null;
}

// ---------------------------------------------------------------- 문장 변형
// 같은 템플릿이 5만 번 반복되면 검색엔진이 얇은 페이지로 봅니다.
// 지역·주제 슬러그를 씨앗으로 문장을 갈라 놓습니다.

const OPEN_IND = [
    '%s에서 %s을 운영하신다면 전화가 곧 매출로 이어지는 지점이 분명합니다.',
    '%s의 %s은 전화 응대 방식에 따라 결과가 크게 갈립니다.',
    '%s에서 %s을 하시면서 전화 때문에 곤란했던 적이 있으실 겁니다.',
    '%s 지역 %s의 전화 업무를 정리하는 방법을 안내해 드립니다.',
];

const OPEN_SVC = [
    '%s에서 %s을 검토하고 계시다면 확인하실 내용을 정리했습니다.',
    '%s 지역에서 %s을 알아보실 때 필요한 내용입니다.',
    '%s에 계신 분들이 %s을 문의하실 때 자주 묻는 것들입니다.',
];

const CLOSE = [
    '전화가 몇 통인지, 그중 몇 통을 놓쳤는지부터 확인해 보시는 편이 좋습니다.',
    '지금 쓰시는 환경을 먼저 보고 필요한 것만 골라 제안해 드립니다.',
    '무엇이 불편한지만 알려주시면 나머지는 저희가 정리해 드립니다.',
];

// ---------------------------------------------------------------- 틀

function page(array $d) {
    $pfx  = $d['pfx'];
    $faq  = '';
    $ld   = '';
    if (!empty($d['faq'])) {
        $items = [];
        foreach ($d['faq'] as $qa) {
            $faq .= '<details><summary>' . esc($qa[0]) . '</summary><div class="a">' . esc($qa[1]) . '</div></details>';
            $items[] = json_encode([
                '@type' => 'Question', 'name' => $qa[0],
                'acceptedAnswer' => ['@type' => 'Answer', 'text' => $qa[1]],
            ], JSON_UNESCAPED_UNICODE);
        }
        $ld = '<script type="application/ld+json">{"@context":"https://schema.org","@type":"FAQPage","mainEntity":['
            . implode(',', $items) . ']}</script>';
        $faq = '<h2>자주 묻는 것</h2><div class="faq">' . $faq . '</div>';
    }

    $title = esc($d['title']);
    $desc  = esc($d['desc']);
    $canon = esc($d['canonical']);

    return <<<HTML
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{$title}</title>
<meta name="description" content="{$desc}">
<link rel="canonical" href="{$canon}">
<meta property="og:type" content="article">
<meta property="og:title" content="{$title}">
<meta property="og:description" content="{$desc}">
<meta property="og:locale" content="ko_KR">
<meta property="og:site_name" content="지오테스">
<meta property="og:image" content="https://jerry797979.github.io/assets/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Poppins:wght@600;700;800&display=swap">
<link rel="stylesheet" href="{$pfx}assets/nova-post.css">
{$ld}
</head>
<body>

<header class="site">
  <div class="wrap">
    <a href="{$pfx}" class="logo logo-img"><img src="{$pfx}assets/logo.png" alt="지오테스 Ziotes"></a>
    <a href="tel:{$d['telr']}" class="nav-call">{$d['tel']}</a>
  </div>
</header>

<div class="post-hero">
  <div class="wrap">
    <p class="crumb">{$d['crumb']}</p>
    <span class="eyebrow">{$d['eyebrow']}</span>
    <h1>{$d['h1']}</h1>
    <p class="meta">{$d['sub']}</p>
  </div>
</div>

<div class="wrap">
  <article>
    <div class="answer">
      <span class="lab">{$d['aq']}</span>
      <p>{$d['answer']}</p>
    </div>
    {$d['body']}
    {$faq}

    <div class="cta">
      <div class="dot"></div>
      <h2>상담은 무료입니다</h2>
      <p>지금 쓰시는 전화 환경을 보고 필요한 것만 골라 알려드립니다.</p>
      <div class="btns">
        <a href="tel:{$d['telr']}" class="btn btn-white">{$d['tel']}</a>
        <a href="{$pfx}contact/" class="btn btn-line">상담 신청</a>
      </div>
    </div>
  </article>
</div>

<footer>
  <div class="wrap">
    <div class="flogo">지오<b>테스</b></div>
    ㈜지오테스솔루션 · 대표이사 신명남 · 사업자등록번호 144-81-03835<br>
    경기 고양시 덕양구 삼막3길 5 고양삼송듀클래스 904호 · 고객센터 {$d['tel']}<br>
    © 2006 ZioTEs Solution Inc.
  </div>
</footer>

</body>
</html>
HTML;
}

/** page() 에 공통값을 채워 준다. */
function render(array $d) {
    $d['tel']  = TEL;
    $d['telr'] = TEL_R;
    return page($d);
}

function link_grid(array $links) {
    $s = '';
    foreach ($links as $l) $s .= '<li><a class="inlink" href="' . esc($l[0]) . '">' . esc($l[1]) . '</a></li>';
    return '<ul>' . $s . '</ul>';
}

// ---------------------------------------------------------------- 페이지

/** 시군구 x 업종 */
function page_city_industry($prov, $city, $ind, $pfx) {
    $seed = $city['slug'] . $ind['slug'];
    $where = $prov['ko'] . ' ' . $city['ko'];
    $open = sprintf(pick(OPEN_IND, $seed), $city['ko'], $ind['ko']);

    $pains = '';
    foreach ($ind['pains'] as $p) $pains .= '<li>' . esc($p) . '</li>';
    $setup = '';
    foreach ($ind['setup'] as $s) $setup .= '<li><strong>' . esc($s[0]) . '</strong> — ' . esc($s[1]) . '</li>';

    $dongs = around($city['dongs'], $seed, 8);
    $dlinks = [];
    foreach ($dongs as $d) $dlinks[] = [$pfx . 'local/' . $prov['slug'] . '/' . $city['slug'] . '/' . $d['slug'] . '/', $d['ko']];

    $cities = around($prov['cities'], $seed, 6, $city['slug']);
    $clinks = [];
    foreach ($cities as $c) $clinks[] = [$pfx . 'local/' . $prov['slug'] . '/' . $c['slug'] . '/' . $ind['slug'] . '/', $c['ko'] . ' ' . $ind['ko']];

    $body = '<h2>' . esc($city['ko'] . ' ' . $ind['ko']) . '에서 자주 나오는 문제</h2>'
          . '<p>' . esc($open) . ' ' . esc($ind['angle']) . '</p>'
          . '<ul>' . $pains . '</ul>'
          . '<h2>그래서 이렇게 구성합니다</h2>'
          . '<ul>' . $setup . '</ul>'
          . '<div class="callout"><p>' . esc($ind['lead']) . '. '
          . '지오테스는 인터넷전화 회선과 교환기, 상담 프로그램을 직접 개발해 공급합니다. '
          . '회선과 시스템을 한 곳에서 계약하기 때문에 장애가 나도 연락할 곳이 한 곳입니다.</p></div>'
          . '<h2>' . esc($where) . ' 지역 안내</h2>'
          . '<p>' . esc($city['ko']) . ' 안에서도 아래 지역에서 문의가 들어옵니다. '
          . '방문 상담이 필요하시면 일정을 맞춰 찾아뵙습니다.</p>'
          . link_grid($dlinks)
          . '<h2>' . esc($prov['ko']) . '의 다른 지역</h2>'
          . link_grid($clinks)
          . '<p>' . esc(pick(CLOSE, $seed)) . '</p>';

    $faq = [
        [$city['ko'] . '에도 방문해 주시나요?', '방문 상담이 필요하시면 일정을 맞춰 찾아뵙습니다. 원격으로 진행할 수 있는 부분은 방문 없이 처리합니다.'],
        ['쓰던 전화번호를 그대로 쓸 수 있나요?', '번호 이전으로 유지할 수 있습니다. 안내문과 명함을 다시 만들지 않아도 됩니다.'],
        [$ind['ko'] . '은 몇 석부터 구축하나요?', '정해진 최소 인원은 없습니다. 두세 명이 전화를 나눠 받는 곳도 구축합니다.'],
        ['비용이 얼마나 드나요?', '규모와 구성에 따라 다릅니다. 현황을 보고 필요한 것만 담아 견적을 드립니다.'],
    ];

    return render([
        'pfx' => $pfx,
        'title' => $city['ko'] . ' ' . $ind['ko'] . ' 콜센터 구축·고객관리 | ' . BRAND,
        'desc' => $where . ' ' . $ind['ko'] . '을 위한 콜센터 구축과 고객관리. ' . $ind['lead'] . '. 회선부터 상담 프로그램까지 한 곳에서 공급합니다.',
        'canonical' => SITE . '/local/' . $prov['slug'] . '/' . $city['slug'] . '/' . $ind['slug'] . '/',
        'crumb' => '<a href="' . $pfx . '">홈</a> · <a href="' . $pfx . 'local/">지역</a> · <a href="' . $pfx . 'local/' . $prov['slug'] . '/">' . esc($prov['ko']) . '</a> · <a href="' . $pfx . 'local/' . $prov['slug'] . '/' . $city['slug'] . '/">' . esc($city['ko']) . '</a>',
        'eyebrow' => esc($ind['ko']),
        'h1' => esc($city['ko'] . ' ' . $ind['ko']) . ',<br>' . esc($ind['lead']),
        'sub' => esc($where . '에서 ' . $ind['ko'] . '을 운영하시는 분들을 위한 안내입니다.'),
        'aq' => $city['ko'] . ' ' . $ind['ko'] . '은 전화 업무가 어떻게 다른가요?',
        'answer' => esc($ind['angle']),
        'faq' => $faq,
        'body' => $body,
    ]);
}

/** 읍면동 x 서비스 */
function page_dong_service($prov, $city, $dong, $svc, $pfx) {
    $seed = $dong['slug'] . $svc['slug'];
    $where = $city['ko'] . ' ' . $dong['ko'];
    $open = sprintf(pick(OPEN_SVC, $seed), $where, $svc['ko']);

    $steps = '';
    foreach ($svc['steps'] as $i => $s) $steps .= '<li><strong>' . ($i + 1) . '단계</strong> — ' . esc($s) . '</li>';

    $dongs = around($city['dongs'], $seed, 8, $dong['slug']);
    $dlinks = [];
    foreach ($dongs as $d) $dlinks[] = [$pfx . 'local/' . $prov['slug'] . '/' . $city['slug'] . '/' . $d['slug'] . '/' . $svc['slug'] . '/', $d['ko'] . ' ' . $svc['ko']];

    global $SVC;
    $others = array_values($SVC);
    $olinks = [];
    foreach (around($others, $seed, 5, $svc['slug']) as $o)
        $olinks[] = [$pfx . 'local/' . $prov['slug'] . '/' . $city['slug'] . '/' . $dong['slug'] . '/' . $o['slug'] . '/', $dong['ko'] . ' ' . $o['ko']];

    $body = '<h2>' . esc($where) . '에서 ' . esc($svc['ko']) . '을 알아보신다면</h2>'
          . '<p>' . esc($open) . ' ' . esc($svc['angle']) . '</p>'
          . '<h2>진행 순서</h2>'
          . '<ul>' . $steps . '</ul>'
          . '<div class="callout"><p>' . esc($svc['why']) . '</p></div>'
          . '<h2>' . esc($city['ko']) . '의 다른 지역</h2>'
          . '<p>' . esc($city['ko']) . ' 안에서 같은 문의가 들어오는 지역입니다.</p>'
          . link_grid($dlinks)
          . '<h2>' . esc($dong['ko']) . '에서 함께 문의하시는 것</h2>'
          . link_grid($olinks)
          . '<p>' . esc(pick(CLOSE, $seed)) . '</p>';

    $faq = [
        [$dong['ko'] . '에서도 되나요?', '전국 어디서나 진행합니다. 인터넷 회선이 있으면 지역과 관계없이 구축할 수 있습니다.'],
        ['공사가 필요한가요?', '인터넷전화라 별도 회선 공사가 필요 없습니다. 자리를 늘릴 때도 마찬가지입니다.'],
        ['얼마나 걸리나요?', '규모와 구성에 따라 다릅니다. 현황을 본 뒤 일정을 알려드립니다.'],
        ['상담하면 바로 계약해야 하나요?', '아닙니다. 현황을 보고 필요한 구성과 예상 비용만 정리해 드립니다. 계산이 맞지 않으면 도입하지 않으시는 편이 낫습니다.'],
    ];

    return render([
        'pfx' => $pfx,
        'title' => $dong['ko'] . ' ' . $svc['ko'] . ' | ' . BRAND,
        'desc' => $where . ' ' . $svc['ko'] . ' 안내. ' . $svc['lead'] . '. 회선부터 상담 프로그램까지 직접 개발해 공급합니다.',
        'canonical' => SITE . '/local/' . $prov['slug'] . '/' . $city['slug'] . '/' . $dong['slug'] . '/' . $svc['slug'] . '/',
        'crumb' => '<a href="' . $pfx . '">홈</a> · <a href="' . $pfx . 'local/' . $prov['slug'] . '/' . $city['slug'] . '/">' . esc($city['ko']) . '</a> · <a href="' . $pfx . 'local/' . $prov['slug'] . '/' . $city['slug'] . '/' . $dong['slug'] . '/">' . esc($dong['ko']) . '</a>',
        'eyebrow' => esc($svc['ko']),
        'h1' => esc($dong['ko'] . ' ' . $svc['ko']),
        'sub' => esc($svc['lead']),
        'aq' => $svc['ko'] . '이 무엇인가요?',
        'answer' => esc($svc['angle']),
        'faq' => $faq,
        'body' => $body,
    ]);
}

/** 읍면동 허브 */
function page_dong_hub($prov, $city, $dong, $pfx) {
    global $SVC, $IND;
    $seed = $dong['slug'];
    $base = $pfx . 'local/' . $prov['slug'] . '/' . $city['slug'] . '/';

    $links = [];
    foreach ($SVC as $s) $links[] = [$base . $dong['slug'] . '/' . $s['slug'] . '/', $dong['ko'] . ' ' . $s['ko']];

    $ilinks = [];
    foreach (around(array_values($IND), $seed, 8) as $t) $ilinks[] = [$base . $t['slug'] . '/', $city['ko'] . ' ' . $t['ko']];

    $nlinks = [];
    foreach (around($city['dongs'], $seed, 8, $dong['slug']) as $d) $nlinks[] = [$base . $d['slug'] . '/', $d['ko']];

    $body = '<h2>' . esc($dong['ko']) . '에서 문의하실 수 있는 항목</h2>'
          . '<p>' . esc($city['ko'] . ' ' . $dong['ko']) . ' 지역에서 전화 시스템을 알아보신다면 아래 항목 중에서 고르시면 됩니다. '
          . '무엇이 필요한지 모르시겠다면 지금 쓰시는 환경만 알려주셔도 됩니다. '
          . '전화를 몇 분이 받고 계신지, 무엇이 불편하신지만 들으면 나머지는 저희가 정리해 드립니다.</p>'
          . link_grid($links)

          . '<h2>공사 없이 시작합니다</h2>'
          . '<p>인터넷전화 방식이라 <strong>회선을 늘리는 데 공사가 필요 없습니다.</strong> '
          . '자리가 하나 늘어도, 사무실을 옮겨도 번호는 그대로 씁니다. '
          . '지점이 여러 곳이면 하나의 내선 체계로 묶어 지점 사이 통화료를 없앨 수 있습니다. '
          . '설치는 원격으로 진행하는 부분이 많아 ' . esc($dong['ko']) . '까지 여러 번 방문하지 않아도 됩니다.</p>'
          . '<div class="callout"><p>지오테스는 인터넷전화 회선과 교환기, 상담 프로그램을 직접 개발해 공급합니다. '
          . '회선과 시스템을 한 곳에서 계약하기 때문에 전화가 안 될 때 연락할 곳이 한 곳입니다. '
          . '통신사와 장비사가 서로 미루는 일이 생기지 않습니다.</p></div>'

          . '<h2>' . esc($city['ko']) . '에서 많이 찾는 업종</h2>'
          . '<p>업종마다 전화로 들어오는 내용이 다릅니다. '
          . '그 업종에서 반복해서 나온 요구를 기본 구성으로 잡아두고 시작합니다.</p>'
          . link_grid($ilinks)

          . '<h2>' . esc($city['ko']) . '의 다른 지역</h2>'
          . link_grid($nlinks)
          . '<p>' . esc(pick(CLOSE, $seed)) . '</p>';

    return render([
        'pfx' => $pfx,
        'title' => $dong['ko'] . ' 콜센터·기업전화 | ' . BRAND,
        'desc' => $city['ko'] . ' ' . $dong['ko'] . ' 지역 콜센터 구축, 고객관리 프로그램, 기업 인터넷전화 안내.',
        'canonical' => SITE . '/local/' . $prov['slug'] . '/' . $city['slug'] . '/' . $dong['slug'] . '/',
        'crumb' => '<a href="' . $pfx . '">홈</a> · <a href="' . $pfx . 'local/' . $prov['slug'] . '/' . $city['slug'] . '/">' . esc($city['ko']) . '</a> · ' . esc($dong['ko']),
        'eyebrow' => esc($city['ko']),
        'h1' => esc($dong['ko']) . ' 전화 시스템',
        'sub' => esc($dong['ko'] . '에서 콜센터와 기업 전화를 알아보신다면'),
        'aq' => $dong['ko'] . '에서도 구축이 되나요?',
        'answer' => '됩니다. 인터넷전화 기반이라 <span class="hl">인터넷 회선만 있으면 지역과 관계없이 구축</span>할 수 있습니다. '
                  . '회선 공사가 필요 없고, 자리를 늘릴 때도 공사 없이 추가합니다.',
        'faq' => [
            [$dong['ko'] . '까지 방문해 주시나요?', '필요하시면 방문합니다. 다만 설치와 설정은 원격으로 되는 부분이 많아 여러 번 오가지 않아도 됩니다.'],
            ['몇 명부터 쓸 수 있나요?', '정해진 최소 인원은 없습니다. 두세 명이 전화를 나눠 받는 곳도 구축합니다.'],
            ['쓰던 번호를 그대로 쓸 수 있나요?', '번호 이전으로 유지할 수 있습니다. 안내문과 명함을 다시 만들지 않아도 됩니다.'],
            ['얼마나 걸리나요?', '규모와 구성에 따라 다릅니다. 현황을 본 뒤 일정을 알려드립니다.'],
        ],
        'body' => $body,
    ]);
}

/** 시군구 허브 */
function page_city_hub($prov, $city, $pfx) {
    global $IND;
    $ilinks = [];
    foreach ($IND as $t) $ilinks[] = [$pfx . 'local/' . $prov['slug'] . '/' . $city['slug'] . '/' . $t['slug'] . '/', $city['ko'] . ' ' . $t['ko']];
    $dlinks = [];
    foreach ($city['dongs'] as $d) $dlinks[] = [$pfx . 'local/' . $prov['slug'] . '/' . $city['slug'] . '/' . $d['slug'] . '/', $d['ko']];

    $body = '<h2>' . esc($city['ko']) . '에서 콜센터를 알아보신다면</h2>'
          . '<p>전화가 몇 통 오는지, 그중 몇 통을 놓치고 있는지부터 확인하는 편이 좋습니다. '
          . '규모를 먼저 정하고 시스템을 고르면 대개 안 쓰는 기능까지 사게 됩니다. '
          . '지금 불편한 지점을 기준으로 필요한 것만 담는 편이 총액이 낮습니다.</p>'
          . '<div class="callout"><p>지오테스는 인터넷전화 회선과 교환기, 상담 프로그램을 직접 개발해 공급합니다. '
          . '회선은 통신사에서, 장비는 장비사에서 따로 사실 필요가 없습니다. '
          . '전화가 안 될 때 연락할 곳도 한 곳입니다.</p></div>'
          . '<h2>업종별 안내</h2>'
          . '<p>업종마다 전화로 들어오는 내용이 다릅니다. 아래에서 해당 업종을 고르시면 '
          . '그 업종에서 반복해서 나온 요구와 기본 구성을 보실 수 있습니다.</p>'
          . link_grid($ilinks);
    if ($dlinks) $body .= '<h2>' . esc($city['ko']) . ' 지역</h2>'
                        . '<p>' . esc($city['ko']) . ' 안에서 문의가 들어오는 지역입니다. '
                        . '설치는 원격으로 되는 부분이 많아 여러 번 방문하지 않아도 됩니다.</p>'
                        . link_grid($dlinks);

    return render([
        'pfx' => $pfx,
        'title' => $city['ko'] . ' 콜센터 구축·고객관리 프로그램 | ' . BRAND,
        'desc' => $prov['ko'] . ' ' . $city['ko'] . ' 지역 콜센터 구축과 고객관리 프로그램 안내. 업종별 구성과 지역별 안내를 확인하실 수 있습니다.',
        'canonical' => SITE . '/local/' . $prov['slug'] . '/' . $city['slug'] . '/',
        'crumb' => '<a href="' . $pfx . '">홈</a> · <a href="' . $pfx . 'local/">지역</a> · <a href="' . $pfx . 'local/' . $prov['slug'] . '/">' . esc($prov['ko']) . '</a>',
        'eyebrow' => esc($prov['ko']),
        'h1' => esc($city['ko']) . ' 콜센터 구축',
        'sub' => esc($city['ko'] . '에서 전화 시스템을 알아보시는 분들을 위한 안내입니다.'),
        'aq' => $city['ko'] . '에서도 구축이 되나요?',
        'answer' => '됩니다. 지오테스는 <span class="hl">인터넷전화 회선과 교환기, 상담 프로그램을 직접 개발해 공급</span>합니다. '
                  . '인터넷 회선만 있으면 지역과 관계없이 구축할 수 있고, 회선과 시스템을 한 곳에서 계약하기 때문에 장애가 나도 연락할 곳이 한 곳입니다.',
        'faq' => [
            ['몇 명부터 구축할 수 있나요?', '정해진 최소 인원은 없습니다. 두세 명이 전화를 나눠 받는 곳부터 대형 콜센터까지 구성합니다.'],
            ['비용이 얼마나 드나요?', '규모와 구성에 따라 다릅니다. 시스템 구축비, 회선 이용료, 유지보수, 부가서비스 네 항목으로 나뉘며 현황을 보고 견적을 드립니다.'],
            ['상담 프로그램은 따로 사야 하나요?', '고객관리(CRM)와 녹취, 통계는 시스템 구축에 함께 들어갑니다. 프로그램만 따로 구매하는 항목이 없습니다.'],
            ['쓰던 번호를 그대로 쓸 수 있나요?', '번호 이전으로 유지할 수 있습니다. 안내문과 명함을 다시 만들지 않아도 됩니다.'],
        ],
        'body' => $body,
    ]);
}

/** 시도 허브 */
function page_prov_hub($prov, $pfx) {
    $links = [];
    foreach ($prov['cities'] as $c) $links[] = [$pfx . 'local/' . $prov['slug'] . '/' . $c['slug'] . '/', $c['ko']];
    return render([
        'pfx' => $pfx,
        'title' => $prov['ko'] . ' 콜센터 구축 | ' . BRAND,
        'desc' => $prov['ko'] . ' 지역 콜센터 구축과 기업 전화 안내. 시군구별로 확인하실 수 있습니다.',
        'canonical' => SITE . '/local/' . $prov['slug'] . '/',
        'crumb' => '<a href="' . $pfx . '">홈</a> · <a href="' . $pfx . 'local/">지역</a> · ' . esc($prov['ko']),
        'eyebrow' => '지역',
        'h1' => esc($prov['ko']) . ' 콜센터 구축',
        'sub' => esc($prov['ko'] . ' 안에서 지역을 골라 주세요.'),
        'aq' => $prov['ko'] . ' 전 지역에서 되나요?',
        'answer' => '됩니다. 인터넷전화 기반이라 <span class="hl">인터넷 회선만 있으면 어디서나 구축</span>할 수 있습니다.',
        'faq' => [
            ['설치하러 직접 오시나요?', '필요하면 방문합니다. 다만 설치와 설정은 원격으로 되는 부분이 많아 일정이 오래 걸리지 않습니다.'],
            ['수도권이 아니면 대응이 느리지 않나요?', '장애 대응은 원격으로 즉시 확인합니다. 회선과 시스템을 저희가 함께 공급하기 때문에 원인을 찾는 데 시간이 걸리지 않습니다.'],
            ['쓰던 번호를 그대로 쓸 수 있나요?', '번호 이전으로 유지할 수 있습니다. 지역번호도 그대로 씁니다.'],
        ],
        'body' => '<h2>' . esc($prov['ko']) . '에서 콜센터를 알아보신다면</h2>'
                . '<p>지역과 관계없이 같은 구성으로 구축합니다. 인터넷전화 방식이라 <strong>회선 공사가 필요 없고</strong>, '
                . '자리를 늘릴 때도 공사 없이 추가합니다. 지점이 여러 곳이면 하나의 내선 체계로 묶어 '
                . '지점 사이 통화료를 없앨 수 있습니다.</p>'
                . '<div class="callout"><p>지오테스는 2006년부터 인터넷전화와 컨택센터 솔루션을 직접 개발해 왔습니다. '
                . '회선과 시스템을 한 곳에서 계약하기 때문에 장애가 나도 연락할 곳이 한 곳입니다.</p></div>'
                . '<h2>' . esc($prov['ko']) . ' 지역</h2>' . link_grid($links),
    ]);
}

/** 전국 허브 */
function page_root($pfx) {
    global $PROV;
    $links = [];
    foreach ($PROV as $p) $links[] = [$pfx . 'local/' . $p['slug'] . '/', $p['ko']];
    return render([
        'pfx' => $pfx,
        'title' => '지역별 콜센터 구축 안내 | ' . BRAND,
        'desc' => '전국 시군구·읍면동별 콜센터 구축과 기업 전화 안내.',
        'canonical' => SITE . '/local/',
        'crumb' => '<a href="' . $pfx . '">홈</a> · 지역',
        'eyebrow' => '지역',
        'h1' => '지역별 안내',
        'sub' => '전국 어디서나 구축합니다. 지역을 골라 주세요.',
        'aq' => '지방에서도 구축이 되나요?',
        'answer' => '됩니다. 인터넷전화 기반이라 <span class="hl">인터넷 회선만 있으면 지역과 관계없이 구축</span>할 수 있습니다. '
                  . '회선 공사가 필요 없어 설치 부담도 적습니다.',
        'faq' => [],
        'body' => '<h2>시·도</h2>' . link_grid($links),
    ]);
}

// ---------------------------------------------------------------- 사이트맵

function sitemap_index() {
    global $PROV;
    $s = '<?xml version="1.0" encoding="UTF-8"?>' . "\n"
       . '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' . "\n";
    foreach ($PROV as $p) $s .= '  <sitemap><loc>' . SITE . '/local/sitemap-' . $p['slug'] . '.xml</loc></sitemap>' . "\n";
    return $s . '</sitemapindex>' . "\n";
}

function sitemap_prov($pslug) {
    global $IND, $SVC;
    $p = prov_full($pslug);
    if (!$p) return null;
    $today = date('Y-m-d');
    $u = ['/local/' . $p['slug'] . '/'];
    foreach ($p['cities'] as $c) {
        $base = '/local/' . $p['slug'] . '/' . $c['slug'] . '/';
        $u[] = $base;
        foreach ($IND as $t) $u[] = $base . $t['slug'] . '/';
        foreach ($c['dongs'] as $d) {
            $u[] = $base . $d['slug'] . '/';
            foreach ($SVC as $s) $u[] = $base . $d['slug'] . '/' . $s['slug'] . '/';
        }
    }
    $s = '<?xml version="1.0" encoding="UTF-8"?>' . "\n"
       . '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' . "\n";
    foreach ($u as $x) $s .= '  <url><loc>' . SITE . $x . '</loc><lastmod>' . $today . '</lastmod></url>' . "\n";
    return $s . '</urlset>' . "\n";
}

// ---------------------------------------------------------------- 라우팅

$path = parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH);
$path = trim($path, '/');
$seg  = $path === '' ? [] : explode('/', $path);

// 하위 폴더에 올려도 동작하도록 접두어를 계산한다 (/local/a/b/ → ../../../)
$depth = count($seg);
$pfx   = $depth > 0 ? str_repeat('../', $depth) : './';

function out($html, $type = 'text/html') {
    header('Content-Type: ' . $type . '; charset=utf-8');
    header('Cache-Control: public, max-age=600');
    echo $html;
    exit;
}

function not_found($pfx) {
    http_response_code(404);
    header('Content-Type: text/html; charset=utf-8');
    echo '<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8">'
       . '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
       . '<title>페이지를 찾을 수 없습니다 · ' . BRAND . '</title>'
       . '<style>body{font-family:Pretendard,system-ui,sans-serif;display:flex;min-height:100vh;align-items:center;'
       . 'justify-content:center;margin:0;color:#16121f;text-align:center}a{color:#6d4aff;font-weight:700}</style></head>'
       . '<body><div><h1 style="font-size:22px">페이지를 찾을 수 없어요</h1>'
       . '<p style="color:#64748b">요청하신 지역·주제 페이지가 없습니다.</p>'
       . '<p style="margin-top:18px"><a href="' . $pfx . 'local/">지역 안내</a> · <a href="' . $pfx . '">홈</a></p>'
       . '</div></body></html>';
    exit;
}

// PHP 내장 서버로 확인할 때는 정적 파일을 그대로 넘긴다 (운영에서는 .htaccess가 거른다)
if (php_sapi_name() === 'cli-server') {
    if ($path === '') {                       // 루트는 홈으로
        header('Content-Type: text/html; charset=utf-8');
        readfile(__DIR__ . '/index.html');
        exit;
    }
    $f = __DIR__ . '/' . $path;
    if (is_file($f)) return false;            // 정적 파일
    if (is_dir($f) && is_file($f . '/index.html')) {
        header('Content-Type: text/html; charset=utf-8');
        readfile($f . '/index.html');
        exit;
    }
}

if (!isset($seg[0]) || $seg[0] !== 'local') not_found($pfx);

// 사이트맵
if (count($seg) === 2 && $seg[1] === 'sitemap.xml') out(sitemap_index(), 'application/xml');
if (count($seg) === 2 && preg_match('#^sitemap-([a-z-]+)\.xml$#', $seg[1], $m)) {
    $x = sitemap_prov($m[1]);
    if ($x === null) not_found($pfx);
    out($x, 'application/xml');
}

$n = count($seg);

if ($n === 1) out(page_root($pfx));

$prov = $PROV[$seg[1]] ?? null;
if (!$prov) not_found($pfx);
if ($n === 2) out(page_prov_hub($prov, $pfx));

$city = city_full($seg[1], $seg[2]);
if (!$city) not_found($pfx);
if ($n === 3) out(page_city_hub($prov, $city, $pfx));

if ($n === 4) {
    if (isset($IND[$seg[3]]))       out(page_city_industry($prov, $city, $IND[$seg[3]], $pfx));
    $d = dong_of($city, $seg[3]);
    if ($d)                          out(page_dong_hub($prov, $city, $d, $pfx));
    not_found($pfx);
}

if ($n === 5) {
    $d = dong_of($city, $seg[3]);
    if ($d && isset($SVC[$seg[4]])) out(page_dong_service($prov, $city, $d, $SVC[$seg[4]], $pfx));
    not_found($pfx);
}

not_found($pfx);
