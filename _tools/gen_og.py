# -*- coding: utf-8 -*-
"""
공유용 이미지(og:image) 생성 —  python _tools/gen_og.py
  → dist/assets/og.png  (1200x630)

이게 없으면 카카오톡·문자로 링크를 보낼 때 브라우저가 페이지의 첫 이미지를 집어갑니다.
구축사례 페이지에서는 고객사 로고가 잡혀서 마치 그 회사 페이지처럼 보입니다.
"""
import os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
OUT = os.path.join(ROOT, "dist", "assets", "og.png")

W, H = 1200, 630
INK = (22, 18, 31)
BRAND = (109, 74, 255)
MINT = (53, 224, 161)
WHITE = (255, 255, 255)
GREY = (168, 174, 190)

FONTS = [r"C:\Windows\Fonts\malgunbd.ttf", r"C:\Windows\Fonts\malgun.ttf"]


def font(size, bold=True):
    path = FONTS[0] if bold else FONTS[1]
    if not os.path.exists(path):
        path = FONTS[1] if os.path.exists(FONTS[1]) else None
    return ImageFont.truetype(path, size) if path else ImageFont.load_default()


def main():
    img = Image.new("RGB", (W, H), INK)
    d = ImageDraw.Draw(img)

    # 배경 장식 — 오른쪽 아래 큰 원, 왼쪽 위 작은 원
    d.ellipse([W - 210, H - 210, W + 150, H + 150], fill=(41, 30, 78))
    d.ellipse([-90, -90, 120, 120], fill=(35, 26, 66))

    # 로고
    d.text((80, 74), "지오", font=font(40), fill=WHITE)
    lw = d.textlength("지오", font=font(40))
    d.text((80 + lw, 74), "테스", font=font(40), fill=BRAND)

    # 제목
    d.text((80, 190), "전화번호부터 AI까지", font=font(66), fill=WHITE)
    d.text((80, 278), "한 회사가 구축해 드립니다", font=font(66), fill=WHITE)

    # 밑줄 (초록)
    y = 278 + 92
    d.rounded_rectangle([80, y, 80 + 470, y + 9], radius=5, fill=MINT)

    # 설명
    d.text((80, 424), "콜센터 구축 · IPCC · 고객관리 CRM · ARS · 통화녹취 · AI 컨택센터",
           font=font(27, bold=False), fill=GREY)

    # 아래 줄 — 실적과 연락처
    d.text((80, 510), "2006년부터 20년", font=font(30), fill=WHITE)
    x = 80 + d.textlength("2006년부터 20년", font=font(30)) + 22
    d.text((x, 512), "·", font=font(28), fill=GREY)
    d.text((x + 20, 510), "120여 곳 구축", font=font(30), fill=WHITE)
    x2 = x + 20 + d.textlength("120여 곳 구축", font=font(30)) + 22
    d.text((x2, 512), "·", font=font(28), fill=GREY)
    d.text((x2 + 20, 510), "1555-5528", font=font(30), fill=MINT)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    img.save(OUT, "PNG", optimize=True)
    kb = os.path.getsize(OUT) // 1024
    print(f"→ dist/assets/og.png  ({W}x{H}, {kb}KB)")


if __name__ == "__main__":
    main()
