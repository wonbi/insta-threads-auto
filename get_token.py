#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
쓰레드 장기 토큰(60일) 발급 도우미. 최초 1회만 실행.

  python get_token.py

Meta 앱 대시보드에서 준비할 것
  - Threads 앱 ID / 앱 시크릿
  - 리디렉션 콜백 URL (HTTPS 필수, 예: https://example.com/ )
"""

import json
import sys
import urllib.parse
import urllib.request

AUTH = "https://threads.net/oauth/authorize"
TOKEN = "https://graph.threads.net/oauth/access_token"
LONG = "https://graph.threads.net/access_token"
ME = "https://graph.threads.net/v1.0/me"
SCOPES = "threads_basic,threads_content_publish"


def get(url, params):
    with urllib.request.urlopen(url + "?" + urllib.parse.urlencode(params), timeout=60) as r:
        return json.loads(r.read().decode())


def post(url, params):
    req = urllib.request.Request(url, data=urllib.parse.urlencode(params).encode(), method="POST")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def main():
    app_id = input("Threads 앱 ID: ").strip()
    app_secret = input("Threads 앱 시크릿: ").strip()
    redirect = input("리디렉션 콜백 URL (앱에 등록한 값 그대로): ").strip()

    url = AUTH + "?" + urllib.parse.urlencode({
        "client_id": app_id,
        "redirect_uri": redirect,
        "scope": SCOPES,
        "response_type": "code",
    })

    print("\n1) 아래 주소를 브라우저에 붙여넣고 로그인 후 권한을 허용하세요.\n")
    print(url)
    print("\n2) 허용하면 주소창이 콜백 URL 로 바뀝니다. 그 주소 전체를 복사해 붙여넣으세요.\n")

    pasted = input("리디렉션된 전체 주소: ").strip()
    qs = urllib.parse.parse_qs(urllib.parse.urlparse(pasted).query)
    code = qs.get("code", [""])[0].split("#")[0]
    if not code:
        print("주소에서 code 값을 찾지 못했습니다.")
        return 1

    short = post(TOKEN, {
        "client_id": app_id,
        "client_secret": app_secret,
        "grant_type": "authorization_code",
        "redirect_uri": redirect,
        "code": code,
    })

    longlived = get(LONG, {
        "grant_type": "th_exchange_token",
        "client_secret": app_secret,
        "access_token": short["access_token"],
    })

    token = longlived["access_token"]
    me = get(ME, {"fields": "id,username", "access_token": token})

    print("\n" + "=" * 60)
    print("GitHub Secrets 에 아래 두 값을 등록하세요")
    print("=" * 60)
    print(f"THREADS_USER_ID = {me['id']}   (계정: @{me.get('username','')})")
    print(f"THREADS_TOKEN   = {token}")
    print(f"\n유효기간: 약 {longlived.get('expires_in', 5184000)//86400}일")
    print("만료 전 refresh_token.py 로 갱신하세요.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
