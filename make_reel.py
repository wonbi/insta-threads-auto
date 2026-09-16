#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
찐한국 셀러 모집용 세로 릴스 생성기

reels.json 에 적힌 대본을 읽어 1080x1920 MP4 를 media/ 에 만든다.

    python make_reel.py                 # reels.json 전체 생성
    python make_reel.py reel-01         # 특정 한 편만

대본 형식 (reels.json)
[
  {
    "id": "reel-01",
    "cards": [
      {"kicker": "도매 단가", "head": "재고 없이\\n시작하는 방법", "body": "위탁도 됩니다"},
      ...
    ]
  }
]
"""

import glob
import json
import os
import shutil
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
FPS = 30
ROOT = os.path.dirname(os.path.abspath(__file__))
MEDIA = os.path.join(ROOT, "media")
ASSETS = os.path.join(ROOT, "assets")

# ── 브랜드 팔레트 (찐한국 네이비) ──────────────────────────────
NAVY = (26, 52, 122)
NAVY_DEEP = (14, 30, 74)
PAPER = (244, 245, 243)
WHITE = (255, 255, 255)
GREY = (122, 132, 140)
POINT = (205, 133, 42)          # 강조 키워드
LINE = (216, 221, 224)

KR = 1  # Noto Sans CJK 안에서 한국어 face 번호

# 한글 폰트 경로는 환경마다 다르다(깃허브 러너 업데이트로 바뀐 적 있음).
# 고정 경로 대신 찾아서 쓰고, 굵기가 없으면 가까운 굵기로 대체한다.
_FONT_DIRS = ["/usr/share/fonts", "/usr/local/share/fonts",
              os.path.expanduser("~/.fonts")]
_FALLBACK = {
    "black":   ["NotoSansCJK-Black", "NotoSansCJKkr-Black", "NotoSansKR-Black",
                "NotoSansCJK-Bold", "NotoSansCJK-Regular"],
    "bold":    ["NotoSansCJK-Bold", "NotoSansCJKkr-Bold", "NotoSansKR-Bold",
                "NotoSansCJK-Black", "NotoSansCJK-Regular"],
    "medium":  ["NotoSansCJK-Medium", "NotoSansCJKkr-Medium", "NotoSansKR-Medium",
                "NotoSansCJK-Regular"],
    "regular": ["NotoSansCJK-Regular", "NotoSansCJKkr-Regular", "NotoSansKR-Regular",
                "NotoSansCJK-Medium"],
}
_resolved = {}


def _find_font(weight):
    if weight in _resolved:
        return _resolved[weight]
    for stem in _FALLBACK[weight]:
        for d in _FONT_DIRS:
            for ext in (".ttc", ".otf", ".ttf"):
                hits = glob.glob(os.path.join(d, "**", stem + ext), recursive=True)
                if hits:
                    _resolved[weight] = sorted(hits)[0]
                    return _resolved[weight]
    # 마지막 수단 — 이름이 뭐든 CJK 폰트 아무거나
    for d in _FONT_DIRS:
        hits = [h for h in glob.glob(os.path.join(d, "**", "*CJK*"), recursive=True)
                if h.endswith((".ttc", ".otf", ".ttf"))]
        if hits:
            _resolved[weight] = sorted(hits)[0]
            return _resolved[weight]
    raise RuntimeError(
        "한글 폰트를 찾을 수 없습니다. fonts-noto-cjk 를 설치하세요.")


def font(weight, size):
    path = _find_font(weight)
    try:
        return ImageFont.truetype(path, size, index=KR)
    except Exception:
        # face 가 하나뿐인 파일(.otf 등)은 index 0
        return ImageFont.truetype(path, size, index=0)


def text_size(draw, s, fnt, spacing=0):
    box = draw.multiline_textbbox((0, 0), s, font=fnt, spacing=spacing)
    return box[2] - box[0], box[3] - box[1]


def wrap(draw, s, fnt, max_w):
    """글자 단위로 폭에 맞춰 줄바꿈 (한글이라 단어 단위는 어색함)."""
    out = []
    for para in s.split("\n"):
        line = ""
        for ch in para:
            t = line + ch
            if draw.textlength(t, font=fnt) > max_w and line:
                out.append(line)
                line = ch
            else:
                line = t
        out.append(line)
    return "\n".join(out)


# ── 카드 한 장 그리기 ─────────────────────────────────────────

def fit_cover(path, box_w, box_h):
    """이미지를 박스에 꽉 차게 잘라 맞춘다."""
    im = Image.open(path).convert("RGB")
    r = max(box_w / im.width, box_h / im.height)
    im = im.resize((int(im.width * r + 1), int(im.height * r + 1)), Image.LANCZOS)
    left = (im.width - box_w) // 2
    top = (im.height - box_h) // 3      # 위쪽을 조금 더 살린다
    return im.crop((left, top, left + box_w, top + box_h))


def draw_card(card, index, total, progress):
    """progress 0~1 : 등장 애니메이션용"""
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    # 상단 네이비 밴드
    d.rectangle([0, 0, W, 220], fill=NAVY)
    f_brand = font("black", 44)
    d.text((72, 96), "찐한국", font=f_brand, fill=WHITE)
    f_sub = font("medium", 26)
    d.text((72, 152), "국내산으로만 채운 생활", font=f_sub, fill=(176, 191, 224))

    # 진행 인디케이터
    seg_w = 46
    for i in range(total):
        x = W - 72 - (total - i) * (seg_w + 10) + 10
        col = WHITE if i <= index else (70, 95, 160)
        d.rectangle([x, 118, x + seg_w, 124], fill=col)

    # 제품 사진
    IMG_TOP, IMG_H = 220, 880
    photo = card.get("img")
    if photo:
        path = os.path.join(ASSETS, photo)
        if os.path.exists(path):
            img.paste(fit_cover(path, W, IMG_H), (0, IMG_TOP))
            d = ImageDraw.Draw(img)

    # 등장 오프셋 (아래에서 살짝 올라옴)
    ease = 1 - (1 - progress) ** 3
    dy = int((1 - ease) * 48)

    pad = 84
    max_w = W - pad * 2
    kicker = card.get("kicker", "")
    body = card.get("body", "")

    # 본문 블록 높이를 먼저 재서 세로 가운데에 놓는다
    f_h = font("black", 72 if photo else 92)
    head = wrap(d, card["head"], f_h, max_w)
    _, hh = text_size(d, head, f_h, spacing=20 if photo else 26)
    block = hh
    if kicker:
        block += (84 if photo else 108)
    if body:
        f_b = font("medium", 40 if photo else 46)
        bt = wrap(d, body, f_b, max_w)
        _, bh = text_size(d, bt, f_b, spacing=22)
        block += (44 if photo else 64) + 40 + bh

    top = (IMG_TOP + IMG_H) if photo else 220
    bottom = H - 190
    y = top + (bottom - top - block) // 2 + dy

    if kicker:
        f_k = font("bold", 34)
        d.text((pad, y), kicker, font=f_k, fill=POINT)
        d.line([pad, y + 58, pad + d.textlength(kicker, font=f_k), y + 58],
               fill=POINT, width=3)
        y += (84 if photo else 108)

    d.multiline_text((pad, y), head, font=f_h, fill=NAVY_DEEP, spacing=20 if photo else 26)
    y += hh + (44 if photo else 64)

    if body:
        d.line([pad, y, pad + 120, y], fill=LINE, width=4)
        y += 44
        d.multiline_text((pad, y), bt, font=f_b, fill=(70, 80, 88), spacing=22)

    # 하단 고정 CTA
    d.rectangle([0, H - 190, W, H], fill=NAVY_DEEP)
    f_c = font("bold", 40)
    cta = card.get("cta", "공구·셀러 문의 → 프로필 링크")
    tw = d.textlength(cta, font=f_c)
    d.text(((W - tw) / 2, H - 120), cta, font=f_c, fill=WHITE)

    return img


def build(reel, outdir):
    cards = reel["cards"]
    hold = reel.get("hold", 3.2)          # 카드당 노출 초
    anim = 0.45                            # 등장 애니메이션 초
    n = 0
    for i, card in enumerate(cards):
        frames = int(hold * FPS)
        anim_frames = int(anim * FPS)
        still = None
        for f in range(frames):
            path = os.path.join(outdir, f"{n:05d}.png")
            if f < anim_frames:
                draw_card(card, i, len(cards), f / anim_frames).save(path)
            else:
                # 애니메이션이 끝나면 화면이 고정이라 한 장만 그리고 복사한다
                if still is None:
                    draw_card(card, i, len(cards), 1.0).save(path)
                    still = path
                else:
                    shutil.copyfile(still, path)
            n += 1
    return n


def encode(outdir, dest):
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-framerate", str(FPS), "-i", os.path.join(outdir, "%05d.png"),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-profile:v", "high", "-preset", "slow", "-crf", "26",
        "-movflags", "+faststart",
        "-vf", "scale=1080:1920",
        dest,
    ]
    subprocess.run(cmd, check=True)


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None
    with open(os.path.join(ROOT, "reels.json"), encoding="utf-8") as f:
        reels = json.load(f)

    os.makedirs(MEDIA, exist_ok=True)
    made = []
    for reel in reels:
        if only and reel["id"] != only:
            continue
        dest = os.path.join(MEDIA, reel["id"] + ".mp4")
        tmp = tempfile.mkdtemp()
        try:
            frames = build(reel, tmp)
            encode(tmp, dest)
            mb = os.path.getsize(dest) / 1024 / 1024
            print(f"  {reel['id']}.mp4  {frames/FPS:.1f}초  {mb:.1f}MB")
            if mb > 19:
                print("    ⚠ 20MB 초과 — jsDelivr 가 못 받습니다. 카드 수를 줄이세요.")
            made.append(dest)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    print(f"\n{len(made)}편 생성 완료 → media/")


if __name__ == "__main__":
    main()
