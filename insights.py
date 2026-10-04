#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""발행된 글의 성과(조회·좋아요·댓글 등)를 Meta API에서 읽어 insights.csv 로 저장한다."""
import csv, json, os, urllib.parse, urllib.request, urllib.error

TH = "https://graph.threads.net/v1.0"
IG = "https://graph.instagram.com/v23.0"
TH_TOKEN = os.environ["THREADS_TOKEN"]
IG_TOKEN = os.environ["IG_TOKEN"]


def get(url, params):
    url = url + "?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            return json.loads(r.read().decode()), ""
    except urllib.error.HTTPError as e:
        try:
            msg = json.loads(e.read().decode()).get("error", {}).get("message", "")
        except Exception:
            msg = ""
        return None, f"{e.code} {msg}"[:120]
    except Exception as e:
        return None, str(e)[:120]


def metrics(base, token, names):
    """여러 지표를 한 번에 요청하고, 실패하면 하나씩 다시 시도한다."""
    out, err = {}, ""
    d, e = get(base + "/insights", {"metric": ",".join(names), "access_token": token})
    if d is None:
        for n in names:
            d1, e1 = get(base + "/insights", {"metric": n, "access_token": token})
            if d1 is None:
                err = e1
                continue
            for it in d1.get("data", []):
                v = it.get("values", [{}])[0].get("value", it.get("total_value", {}).get("value"))
                out[it["name"]] = v
        return out, err
    for it in d.get("data", []):
        v = it.get("values", [{}])[0].get("value", it.get("total_value", {}).get("value"))
        out[it["name"]] = v
    return out, ""


rows = list(csv.DictReader(open("queue.csv", encoding="utf-8-sig", newline="")))
res = []
for r in rows:
    if r["status"] != "done" or ":" not in r["result"]:
        continue
    for part in r["result"].split("|"):
        plat, _, mid = part.strip().partition(":")
        if plat not in ("threads", "instagram") or not mid.isdigit():
            continue
        kind = "토스" if ("toss" in r["comment"] or "토스" in r["comment"]) else "꿀팁"
        title = r["caption"].replace("\\n", " ").strip()
        if title.startswith("[광고]"):
            title = title[4:].strip()
        title = title[:40]
        if plat == "threads":
            m, err = metrics(f"{TH}/{mid}", TH_TOKEN, ["views", "likes", "replies", "reposts", "quotes", "shares"])
            info, _ = get(f"{TH}/{mid}", {"fields": "permalink,timestamp", "access_token": TH_TOKEN})
        else:
            m, err = metrics(f"{IG}/{mid}", IG_TOKEN, ["views", "reach", "likes", "comments", "saved", "shares", "total_interactions"])
            info, _ = get(f"{IG}/{mid}", {"fields": "permalink,timestamp", "access_token": IG_TOKEN})
        info = info or {}
        res.append(dict(date=r["date"], time=r["time"], platform=plat, kind=kind, type=r["type"], title=title,
                        id=mid, views=m.get("views", ""), reach=m.get("reach", ""), likes=m.get("likes", ""),
                        replies=m.get("replies", m.get("comments", "")), reposts=m.get("reposts", ""),
                        quotes=m.get("quotes", ""), shares=m.get("shares", ""), saved=m.get("saved", ""),
                        permalink=info.get("permalink", ""), error=err))
        print(plat, mid, m, err, flush=True)

F = ["date", "time", "platform", "kind", "type", "title", "id", "views", "reach", "likes", "replies",
     "reposts", "quotes", "shares", "saved", "permalink", "error"]
with open("insights.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=F)
    w.writeheader()
    w.writerows(res)
print("rows:", len(res))
