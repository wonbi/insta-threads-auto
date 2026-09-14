#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
쓰레드 / 인스타그램 자동 발행 스크립트

queue.csv 에서 '오늘' 날짜 행을 찾아 Threads, Instagram 에 발행한다.
미디어 파일은 media/ 폴더에 두고, jsDelivr CDN 공개 URL 로 Meta 서버에 전달한다.

환경변수 (GitHub Secrets 또는 .env)
  THREADS_USER_ID, THREADS_TOKEN
  IG_USER_ID, IG_TOKEN
  GH_REPO   예) wonbi/insta-threads-auto
  GH_BRANCH 기본값 main
"""

import csv
import os
import sys
import time
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))
ROOT = os.path.dirname(os.path.abspath(__file__))
QUEUE = os.path.join(ROOT, "queue.csv")

THREADS_API = "https://graph.threads.net/v1.0"
IG_API = "https://graph.instagram.com/v23.0"

DRY_RUN = os.environ.get("DRY_RUN", "").lower() in ("1", "true", "yes")


# ---------------------------------------------------------------- 유틸

def log(msg):
    print(f"[{datetime.now(KST):%H:%M:%S}] {msg}", flush=True)


def http(url, params=None, method="GET"):
    """Meta Graph API 호출. 실패 시 예외."""
    params = params or {}
    if method == "GET":
        url = url + "?" + urllib.parse.urlencode(params)
        data = None
    else:
        data = urllib.parse.urlencode(params).encode()

    req = urllib.request.Request(url, data=data, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        raise RuntimeError(f"{method} {url.split('?')[0]} -> {e.code}\n{body}") from None


def media_url(filename):
    """media/ 파일의 공개 CDN URL."""
    repo = os.environ["GH_REPO"].strip()
    branch = os.environ.get("GH_BRANCH", "main").strip()
    name = urllib.parse.quote(filename.strip())
    return f"https://cdn.jsdelivr.net/gh/{repo}@{branch}/media/{name}"


def wait_ready(check_fn, label, timeout=600):
    """컨테이너가 발행 가능 상태가 될 때까지 대기."""
    started = time.time()
    delay = 5
    while time.time() - started < timeout:
        state = check_fn()
        if state in ("FINISHED", "PUBLISHED"):
            return
        if state in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"{label} 처리 실패: {state}")
        log(f"  {label} 처리 중… ({state})")
        time.sleep(delay)
        delay = min(delay + 5, 20)
    raise RuntimeError(f"{label} 처리 시간 초과")


# ---------------------------------------------------------------- Threads

def threads_container(params):
    uid = os.environ["THREADS_USER_ID"]
    params["access_token"] = os.environ["THREADS_TOKEN"]
    return http(f"{THREADS_API}/{uid}/threads", params, "POST")["id"]


def threads_status(cid):
    r = http(f"{THREADS_API}/{cid}",
             {"fields": "status", "access_token": os.environ["THREADS_TOKEN"]})
    return r.get("status", "IN_PROGRESS")


def post_threads(kind, files, caption):
    if kind == "text":
        cid = threads_container({"media_type": "TEXT", "text": caption})

    elif kind == "image":
        cid = threads_container({"media_type": "IMAGE",
                                 "image_url": media_url(files[0]),
                                 "text": caption})

    elif kind == "video":
        cid = threads_container({"media_type": "VIDEO",
                                 "video_url": media_url(files[0]),
                                 "text": caption})

    elif kind == "carousel":
        children = []
        for f in files:
            key = "video_url" if f.lower().endswith((".mp4", ".mov")) else "image_url"
            mtype = "VIDEO" if key == "video_url" else "IMAGE"
            children.append(threads_container({
                "media_type": mtype, key: media_url(f), "is_carousel_item": "true"}))
            log(f"  캐러셀 항목 등록: {f}")
        for c in children:
            wait_ready(lambda c=c: threads_status(c), "쓰레드 캐러셀 항목")
        cid = threads_container({"media_type": "CAROUSEL",
                                 "children": ",".join(children),
                                 "text": caption})
    else:
        raise ValueError(f"지원하지 않는 타입: {kind}")

    wait_ready(lambda: threads_status(cid), "쓰레드 컨테이너")

    uid = os.environ["THREADS_USER_ID"]
    r = http(f"{THREADS_API}/{uid}/threads_publish",
             {"creation_id": cid, "access_token": os.environ["THREADS_TOKEN"]}, "POST")
    return r["id"]


# ---------------------------------------------------------------- Instagram

def ig_container(params):
    uid = os.environ["IG_USER_ID"]
    params["access_token"] = os.environ["IG_TOKEN"]
    return http(f"{IG_API}/{uid}/media", params, "POST")["id"]


def ig_status(cid):
    r = http(f"{IG_API}/{cid}",
             {"fields": "status_code", "access_token": os.environ["IG_TOKEN"]})
    return r.get("status_code", "IN_PROGRESS")


def post_instagram(kind, files, caption):
    if kind == "text":
        log("  인스타그램은 텍스트 전용 게시물을 지원하지 않음 → 건너뜀")
        return None

    if kind == "image":
        cid = ig_container({"image_url": media_url(files[0]), "caption": caption})

    elif kind == "video":
        cid = ig_container({"media_type": "REELS",
                            "video_url": media_url(files[0]),
                            "caption": caption,
                            "share_to_feed": "true"})

    elif kind == "carousel":
        children = []
        for f in files:
            p = {"is_carousel_item": "true"}
            if f.lower().endswith((".mp4", ".mov")):
                p["media_type"] = "VIDEO"
                p["video_url"] = media_url(f)
            else:
                p["image_url"] = media_url(f)
            children.append(ig_container(p))
            log(f"  캐러셀 항목 등록: {f}")
        for c in children:
            wait_ready(lambda c=c: ig_status(c), "인스타 캐러셀 항목")
        cid = ig_container({"media_type": "CAROUSEL",
                            "children": ",".join(children),
                            "caption": caption})
    else:
        raise ValueError(f"지원하지 않는 타입: {kind}")

    wait_ready(lambda: ig_status(cid), "인스타 컨테이너")

    uid = os.environ["IG_USER_ID"]
    r = http(f"{IG_API}/{uid}/media_publish",
             {"creation_id": cid, "access_token": os.environ["IG_TOKEN"]}, "POST")
    return r["id"]


# ---------------------------------------------------------------- 큐 처리

FIELDS = ["date", "time", "platform", "type", "files", "caption", "status", "result"]


def read_queue():
    with open(QUEUE, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_queue(rows):
    with open(QUEUE, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in FIELDS})


def git_sync():
    """queue.csv 변경분을 저장소에 즉시 반영한다 (--watch 중 중간 저장)."""
    import subprocess
    def run(*a):
        return subprocess.run(a, cwd=ROOT, capture_output=True, text=True)
    if not run("git", "status", "--porcelain", "queue.csv").stdout.strip():
        return
    run("git", "config", "user.name", "auto-post")
    run("git", "config", "user.email", "auto-post@users.noreply.github.com")
    run("git", "add", "queue.csv")
    run("git", "commit", "-m", f"발행 결과 기록 {datetime.now(KST):%Y-%m-%d %H:%M} KST")
    p = run("git", "push")
    if p.returncode != 0:
        run("git", "pull", "--rebase", "--autostash")
        p = run("git", "push")
    log("  큐 저장 " + ("완료" if p.returncode == 0 else "실패: " + p.stderr.strip()[:200]))


def publish_row(rows, i):
    r = rows[i]
    platform = (r.get("platform") or "both").strip().lower()
    kind = (r.get("type") or "text").strip().lower()
    files = [x for x in (r.get("files") or "").split(";") if x.strip()]
    caption = (r.get("caption") or "").replace("\\n", "\n").strip()
    targets = ["threads", "instagram"] if platform == "both" else [platform]

    log(f"── {i+1}행 | {platform} | {kind} | {files or '텍스트'}")
    results, ok = [], True
    for t in targets:
        try:
            if DRY_RUN:
                for f in files:
                    log(f"  [DRY] {media_url(f)}")
                log(f"  [DRY] {t} 발행 예정")
                results.append(f"{t}:DRY")
                continue
            mid = post_threads(kind, files, caption) if t == "threads" \
                else post_instagram(kind, files, caption)
            if mid:
                log(f"  ✅ {t} 발행 완료 (id={mid})")
                results.append(f"{t}:{mid}")
            else:
                results.append(f"{t}:skipped")
        except Exception as e:
            ok = False
            log(f"  ❌ {t} 실패: {e}")
            results.append(f"{t}:ERROR")
    rows[i]["status"] = "done" if ok else "error"
    rows[i]["result"] = " | ".join(results)
    return ok


def one_pass(push=False):
    """지금 발행할 수 있는 행을 모두 발행한다.
    반환: (발행 시도 수, 실패 수, 오늘 남은 행의 다음 예정 시각 'HH:MM' 또는 None)"""
    now = datetime.now(KST)
    today = now.strftime("%Y-%m-%d")
    now_hm = now.strftime("%H:%M")
    log(f"오늘 {today} {now_hm} (KST) 발행 대상 확인")

    rows = read_queue()
    todo, later = [], []
    for i, r in enumerate(rows):
        if r.get("date", "").strip() != today:
            continue
        if r.get("status", "").strip().lower() in ("done", "skip", "error"):
            continue
        want = (r.get("time") or "00:00").strip()
        if want > now_hm:
            later.append(want)
        else:
            todo.append(i)

    if not todo:
        log("지금 발행할 항목 없음" + (f" (다음 {min(later)})" if later else ""))
        return 0, 0, (min(later) if later else None)

    failed = 0
    for i in todo:
        if not publish_row(rows, i):
            failed += 1
        # 한 행 끝날 때마다 바로 기록한다.
        # (실행이 중간에 끊겨도 같은 글이 두 번 올라가지 않게)
        if not DRY_RUN:
            write_queue(rows)
            if push:
                git_sync()
    return len(todo), failed, (min(later) if later else None)


def watch():
    """한 번 깨어난 김에 오늘 남은 슬롯까지 지키고 있다가 제때 발행한다.

    GitHub 의 schedule 은 최대 몇 시간씩 밀리기 때문에, 실행될 때마다
    오늘 치가 끝날 때까지 살아 있는 편이 훨씬 정확하다."""
    deadline = datetime.now(KST) + timedelta(hours=5, minutes=20)
    failed_total = 0
    while True:
        _, failed, nxt = one_pass(push=True)
        failed_total += failed
        if nxt is None:
            log("오늘 치 발행 완료 — 종료")
            break
        now = datetime.now(KST)
        h, m = (int(x) for x in nxt.split(":"))
        target = now.replace(hour=h, minute=m, second=5, microsecond=0)
        if target <= now:
            target = now + timedelta(minutes=1)
        if target > deadline:
            log(f"다음 예정 {nxt} — 이 실행의 한계 시간을 넘어 종료 (다음 실행이 이어받음)")
            break
        wait = (target - now).total_seconds()
        log(f"다음 예정 {nxt} — {int(wait//60)}분 대기")
        time.sleep(wait)
    return 1 if failed_total else 0


def main():
    if "--watch" in sys.argv:
        return watch()
    _, failed, _ = one_pass()
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
