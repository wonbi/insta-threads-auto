#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
콘텐츠 자동 생성기

facts.json 의 사실 풀을 돌려가며 앞으로 N일치 콘텐츠를 만든다.
  · reels.json 대본 생성  → make_reel.py 가 MP4 로 뽑음
  · queue.csv 에 인스타 1 + 쓰레드 2 씩 추가

    python generate_content.py            # 큐가 비는 만큼 14일치 채움
    python generate_content.py --days 21  # 21일치
    python generate_content.py --force    # 이미 채워진 날짜도 다시 생성

매주 GitHub Actions(weekly-content.yml)가 이걸 실행하므로
사람 손이 안 들어가도 큐가 계속 이어진다.
"""

import argparse
import csv
import datetime
import json
import os
import random

ROOT = os.path.dirname(os.path.abspath(__file__))
KST = datetime.timezone(datetime.timedelta(hours=9))
FIELDS = ["date", "time", "platform", "type", "files", "caption", "status", "result"]

CTA_REEL = "공구·셀러 문의 → 프로필 링크"
CTA_IG = ("위탁이라 재고 부담 없고 공급가도 저렴합니다.\n"
          "최소 수량이랑 공급가는 프로필 링크로 문의 주세요.")
CTA_IG_SHORT = "최소 수량이랑 공급가는 프로필 링크로 문의 주세요."

# 인스타 캡션에 붙는 '셀러 입장' 한 줄 — 영상은 제품, 캡션은 장사 얘기
SELLER_LINES = [
    "매일 쓰고 다 쓰면 다시 사는 물건입니다. 한 번 팔고 끝나지 않아요.",
    "설명이 길게 필요 없어서 공구에서 전환이 빠릅니다.",
    "싱크대 앞에서 같이 쓰이는 것들이라 묶으면 장바구니가 커집니다.",
    "소비 속도가 빨라서 재주문 주기가 짧습니다.",
    "써 보면 바로 아는 차이라 후기가 잘 붙습니다.",
    "계절을 안 타서 일 년 내내 돌릴 수 있습니다.",
]
TAGS = ("#공동구매 #공구셀러 #위탁판매 #생활용품도매 #국내산 "
        "#스마트스토어 #폐쇄몰 #셀러모집 #찐한국")

TIMES = {"threads_1": "15:00", "instagram": "18:00", "threads_2": "20:00"}


def load(name):
    with open(os.path.join(ROOT, name), encoding="utf-8") as f:
        return json.load(f)


def read_queue():
    path = os.path.join(ROOT, "queue.csv")
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_queue(rows):
    with open(os.path.join(ROOT, "queue.csv"), "w",
              encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in FIELDS})


def pick(seq, rng, used):
    """최근에 쓴 건 피해서 고른다."""
    fresh = [x for x in seq if x not in used]
    chosen = rng.choice(fresh if fresh else seq)
    used.append(chosen)
    if len(used) > max(3, len(seq) // 2):
        used.pop(0)
    return chosen


def ig_caption(fact, rng, used_sell):
    """영상은 제품을 보여주고, 캡션은 '이걸 팔면 어떻게 되는지'를 말한다."""
    parts = [fact["ig"]]
    if fact["product"] == "거래조건":          # 이미 셀러 얘기라 덧붙이지 않는다
        parts.append(CTA_IG_SHORT)
    else:
        parts.append(pick(SELLER_LINES, rng, used_sell))
        parts.append(CTA_IG)
    parts.append(TAGS)
    return "\n\n".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=14)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    data = load("facts.json")
    facts = data["facts"]
    cta_cards = data["cta_cards"]
    posts = load("threads.json")          # 쓰레드용 긴 글

    rows = read_queue()
    have = {r["date"] for r in rows if r.get("date")}

    today = datetime.datetime.now(KST).date()
    targets = []
    d = today + datetime.timedelta(days=1)
    while len(targets) < args.days:
        if args.force or d.isoformat() not in have:
            targets.append(d)
        d += datetime.timedelta(days=1)

    if not targets:
        print("채울 날짜가 없습니다.")
        return

    # --force 로 다시 만들 때는 그 날짜의 기존 행을 먼저 걷어낸다
    redo = {t.isoformat() for t in targets}
    rows = [r for r in rows if r.get("date") not in redo]

    # 날짜 기반 시드 — 같은 주에 두 번 돌려도 결과가 같다
    rng = random.Random(targets[0].toordinal())
    order = list(range(len(facts)))
    rng.shuffle(order)
    porder = list(range(len(posts)))
    rng.shuffle(porder)

    reels, new_rows = [], []
    used_cta, used_sell = [], []

    for i, day in enumerate(targets):
        fact = facts[order[i % len(facts)]]
        rid = f"reel-{day:%m%d}"

        imgs = fact["imgs"]
        cards = [
            {"kicker": fact["kicker"], "head": fact["head"],
             "body": fact["body"], "img": imgs[0], "cta": CTA_REEL},
            {"kicker": "", "head": fact["sub_head"],
             "body": fact["sub_body"], "img": imgs[1], "cta": CTA_REEL},
        ]
        c = pick(cta_cards, rng, used_cta)
        cards.append({**c, "img": imgs[2], "cta": CTA_REEL})
        reels.append({"id": rid, "hold": 3.4, "cards": cards})

        # 쓰레드 긴 글 2편 — 같은 날 같은 품목이 겹치지 않게 고른다
        a = posts[porder[(i * 2) % len(posts)]]
        b = posts[porder[(i * 2 + 1) % len(posts)]]
        if a["product"] == b["product"]:
            for step in range(2, len(posts)):
                alt = posts[porder[(i * 2 + step) % len(posts)]]
                if alt["product"] != a["product"]:
                    b = alt
                    break

        day_s = day.isoformat()
        new_rows += [
            {"date": day_s, "time": TIMES["threads_1"], "platform": "threads",
             "type": "image" if a.get("img") else "text", "files": a.get("img", ""),
             "caption": a["text"].replace("\n", "\\n")},
            {"date": day_s, "time": TIMES["instagram"], "platform": "instagram",
             "type": "video", "files": rid + ".mp4",
             "caption": ig_caption(fact, rng, used_sell).replace("\n", "\\n")},
            {"date": day_s, "time": TIMES["threads_2"], "platform": "threads",
             "type": "image" if b.get("img") else "text", "files": b.get("img", ""),
             "caption": b["text"].replace("\n", "\\n")},
        ]

    with open(os.path.join(ROOT, "reels.json"), "w", encoding="utf-8") as f:
        json.dump(reels, f, ensure_ascii=False, indent=1)

    rows += new_rows
    rows.sort(key=lambda r: (r.get("date", ""), r.get("time", "")))
    write_queue(rows)

    print(f"{targets[0]} ~ {targets[-1]}  {len(targets)}일치 생성")
    print(f"  릴스 {len(reels)}편 · 큐 {len(new_rows)}행 추가 (전체 {len(rows)}행)")


if __name__ == "__main__":
    main()
