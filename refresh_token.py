#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
장기 토큰(60일) 갱신. 만료 전에 실행하면 다시 60일로 연장된다.
GitHub Actions 의 monthly-refresh 워크플로가 매달 자동 실행한다.

수동 실행:
  THREADS_TOKEN=... IG_TOKEN=... python refresh_token.py
"""

import json
import os
import sys
import urllib.parse
import urllib.request


def get(url, params):
    with urllib.request.urlopen(url + "?" + urllib.parse.urlencode(params), timeout=60) as r:
        return json.loads(r.read().decode())


def main():
    out = {}

    t = os.environ.get("THREADS_TOKEN")
    if t:
        try:
            r = get("https://graph.threads.net/refresh_access_token",
                    {"grant_type": "th_refresh_token", "access_token": t})
            out["THREADS_TOKEN"] = r["access_token"]
            print(f"쓰레드 토큰 갱신 완료 — {r.get('expires_in', 0)//86400}일 연장")
        except Exception as e:
            print(f"쓰레드 토큰 갱신 실패: {e}", file=sys.stderr)

    i = os.environ.get("IG_TOKEN")
    if i:
        try:
            r = get("https://graph.instagram.com/refresh_access_token",
                    {"grant_type": "ig_refresh_token", "access_token": i})
            out["IG_TOKEN"] = r["access_token"]
            print(f"인스타 토큰 갱신 완료 — {r.get('expires_in', 0)//86400}일 연장")
        except Exception as e:
            print(f"인스타 토큰 갱신 실패: {e}", file=sys.stderr)

    # GitHub Actions 에서 후속 스텝이 읽을 수 있도록 출력
    gh_out = os.environ.get("GITHUB_OUTPUT")
    if gh_out:
        with open(gh_out, "a", encoding="utf-8") as f:
            for k, v in out.items():
                print(f"::add-mask::{v}")      # 로그에 토큰이 찍히지 않게
                f.write(f"{k}={v}\n")
    else:
        print(json.dumps(out, indent=2, ensure_ascii=False))

    return 0 if out else 1


if __name__ == "__main__":
    sys.exit(main())
