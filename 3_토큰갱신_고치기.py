#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
토큰 자동 갱신 고치기  (더블클릭 한 번)

지난번 폴더 정리 때 refresh_token.py 가 통째로 빠져서
토큰 갱신이 "파일 없음" 으로 실패했습니다. 그 파일을 넣고 올립니다.

이 파일은 저장소 폴더(= queue.csv 가 있는 폴더) 안에 두고 실행하세요.
"""

import base64, os, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
PAYLOAD = {'.github/workflows/monthly-refresh.yml': 'bmFtZTog7Yag7YGwIOyekOuPmSDqsLHsi6AKCiMg7J6l6riwIO2GoO2BsOydgCA2MOydvCDrp4zro4wuIOunpOuLrCAx7J287JeQIOqwseyLoO2VtCDrp4zro4zrpbwg66eJ64qU64ukLgojIOyCrOyghCDspIDruYQ6IHJlcG8g6raM7ZWc7J20IOyeiOuKlCDqsJzsnbgg7JWh7IS47IqkIO2GoO2BsOydhCBHSF9QQVQg7Iuc7YGs66a/7Jy866GcIOuTseuhnQojICAgR2l0SHViIOKGkiBTZXR0aW5ncyDihpIgRGV2ZWxvcGVyIHNldHRpbmdzIOKGkiBQZXJzb25hbCBhY2Nlc3MgdG9rZW5zIChmaW5lLWdyYWluZWQpCiMgICDihpIg7J20IOyggOyepeyGjCDshKDtg50g4oaSIFJlcG9zaXRvcnkgcGVybWlzc2lvbnMg4oaSIFNlY3JldHM6IFJlYWQgYW5kIHdyaXRlCgpvbjoKICBzY2hlZHVsZToKICAgIC0gY3JvbjogIjAgMTggMSAqICoiICAgIyDrp6Tri6wgMeydvCAwMzowMCBLU1QKICB3b3JrZmxvd19kaXNwYXRjaDoKCmpvYnM6CiAgcmVmcmVzaDoKICAgIHJ1bnMtb246IHVidW50dS1sYXRlc3QKICAgIHN0ZXBzOgogICAgICAtIHVzZXM6IGFjdGlvbnMvY2hlY2tvdXRAdjQKCiAgICAgIC0gdXNlczogYWN0aW9ucy9zZXR1cC1weXRob25AdjUKICAgICAgICB3aXRoOgogICAgICAgICAgcHl0aG9uLXZlcnNpb246ICIzLjEyIgoKICAgICAgLSBpZDogcmVmcmVzaAogICAgICAgIGVudjoKICAgICAgICAgIFRIUkVBRFNfVE9LRU46ICR7eyBzZWNyZXRzLlRIUkVBRFNfVE9LRU4gfX0KICAgICAgICAgIElHX1RPS0VOOiAke3sgc2VjcmV0cy5JR19UT0tFTiB9fQogICAgICAgIHJ1bjogcHl0aG9uIHJlZnJlc2hfdG9rZW4ucHkKCiAgICAgIC0gbmFtZTog7Iuc7YGs66a/IOyXheuNsOydtO2KuAogICAgICAgIGVudjoKICAgICAgICAgIEdIX1RPS0VOOiAke3sgc2VjcmV0cy5HSF9QQVQgfX0KICAgICAgICAgIE5FV19USFJFQURTOiAke3sgc3RlcHMucmVmcmVzaC5vdXRwdXRzLlRIUkVBRFNfVE9LRU4gfX0KICAgICAgICAgIE5FV19JRzogJHt7IHN0ZXBzLnJlZnJlc2gub3V0cHV0cy5JR19UT0tFTiB9fQogICAgICAgIHJ1bjogfAogICAgICAgICAgaWYgWyAtbiAiJE5FV19USFJFQURTIiBdOyB0aGVuCiAgICAgICAgICAgIGdoIHNlY3JldCBzZXQgVEhSRUFEU19UT0tFTiAtLWJvZHkgIiRORVdfVEhSRUFEUyIKICAgICAgICAgICAgZWNobyAi7JOw66CI65OcIO2GoO2BsCDqsLHsi6DrkKgiCiAgICAgICAgICBmaQogICAgICAgICAgaWYgWyAtbiAiJE5FV19JRyIgXTsgdGhlbgogICAgICAgICAgICBnaCBzZWNyZXQgc2V0IElHX1RPS0VOIC0tYm9keSAiJE5FV19JRyIKICAgICAgICAgICAgZWNobyAi7J247Iqk7YOAIO2GoO2BsCDqsLHsi6DrkKgiCiAgICAgICAgICBmaQo=',
 'refresh_token.py': 'IyEvdXNyL2Jpbi9lbnYgcHl0aG9uMwojIC0qLSBjb2Rpbmc6IHV0Zi04IC0qLQoiIiIK7J6l6riwIO2GoO2BsCg2MOydvCkg6rCx7IugLiDrp4zro4wg7KCE7JeQIOyLpO2Wie2VmOuptCDri6Tsi5wgNjDsnbzroZwg7Jew7J6l65Cc64ukLgpHaXRIdWIgQWN0aW9ucyDsnZggbW9udGhseS1yZWZyZXNoIOybjO2BrO2UjOuhnOqwgCDrp6Tri6wg7J6Q64+ZIOyLpO2Wie2VnOuLpC4KCuyImOuPmSDsi6Ttlok6CiAgVEhSRUFEU19UT0tFTj0uLi4gSUdfVE9LRU49Li4uIHB5dGhvbiByZWZyZXNoX3Rva2VuLnB5CiIiIgoKaW1wb3J0IGpzb24KaW1wb3J0IG9zCmltcG9ydCBzeXMKaW1wb3J0IHVybGxpYi5wYXJzZQppbXBvcnQgdXJsbGliLnJlcXVlc3QKCgpkZWYgZ2V0KHVybCwgcGFyYW1zKToKICAgIHdpdGggdXJsbGliLnJlcXVlc3QudXJsb3Blbih1cmwgKyAiPyIgKyB1cmxsaWIucGFyc2UudXJsZW5jb2RlKHBhcmFtcyksIHRpbWVvdXQ9NjApIGFzIHI6CiAgICAgICAgcmV0dXJuIGpzb24ubG9hZHMoci5yZWFkKCkuZGVjb2RlKCkpCgoKZGVmIG1haW4oKToKICAgIG91dCA9IHt9CgogICAgdCA9IG9zLmVudmlyb24uZ2V0KCJUSFJFQURTX1RPS0VOIikKICAgIGlmIHQ6CiAgICAgICAgdHJ5OgogICAgICAgICAgICByID0gZ2V0KCJodHRwczovL2dyYXBoLnRocmVhZHMubmV0L3JlZnJlc2hfYWNjZXNzX3Rva2VuIiwKICAgICAgICAgICAgICAgICAgICB7ImdyYW50X3R5cGUiOiAidGhfcmVmcmVzaF90b2tlbiIsICJhY2Nlc3NfdG9rZW4iOiB0fSkKICAgICAgICAgICAgb3V0WyJUSFJFQURTX1RPS0VOIl0gPSByWyJhY2Nlc3NfdG9rZW4iXQogICAgICAgICAgICBwcmludChmIuyTsOugiOuTnCDthqDtgbAg6rCx7IugIOyZhOujjCDigJQge3IuZ2V0KCdleHBpcmVzX2luJywgMCkvLzg2NDAwfeydvCDsl7DsnqUiKQogICAgICAgIGV4Y2VwdCBFeGNlcHRpb24gYXMgZToKICAgICAgICAgICAgcHJpbnQoZiLsk7DroIjrk5wg7Yag7YGwIOqwseyLoCDsi6TtjKg6IHtlfSIsIGZpbGU9c3lzLnN0ZGVycikKCiAgICBpID0gb3MuZW52aXJvbi5nZXQoIklHX1RPS0VOIikKICAgIGlmIGk6CiAgICAgICAgdHJ5OgogICAgICAgICAgICByID0gZ2V0KCJodHRwczovL2dyYXBoLmluc3RhZ3JhbS5jb20vcmVmcmVzaF9hY2Nlc3NfdG9rZW4iLAogICAgICAgICAgICAgICAgICAgIHsiZ3JhbnRfdHlwZSI6ICJpZ19yZWZyZXNoX3Rva2VuIiwgImFjY2Vzc190b2tlbiI6IGl9KQogICAgICAgICAgICBvdXRbIklHX1RPS0VOIl0gPSByWyJhY2Nlc3NfdG9rZW4iXQogICAgICAgICAgICBwcmludChmIuyduOyKpO2DgCDthqDtgbAg6rCx7IugIOyZhOujjCDigJQge3IuZ2V0KCdleHBpcmVzX2luJywgMCkvLzg2NDAwfeydvCDsl7DsnqUiKQogICAgICAgIGV4Y2VwdCBFeGNlcHRpb24gYXMgZToKICAgICAgICAgICAgcHJpbnQoZiLsnbjsiqTtg4Ag7Yag7YGwIOqwseyLoCDsi6TtjKg6IHtlfSIsIGZpbGU9c3lzLnN0ZGVycikKCiAgICAjIEdpdEh1YiBBY3Rpb25zIOyXkOyEnCDtm4Tsho0g7Iqk7YWd7J20IOydveydhCDsiJgg7J6I64+E66GdIOy2nOugpQogICAgZ2hfb3V0ID0gb3MuZW52aXJvbi5nZXQoIkdJVEhVQl9PVVRQVVQiKQogICAgaWYgZ2hfb3V0OgogICAgICAgIHdpdGggb3BlbihnaF9vdXQsICJhIiwgZW5jb2Rpbmc9InV0Zi04IikgYXMgZjoKICAgICAgICAgICAgZm9yIGssIHYgaW4gb3V0Lml0ZW1zKCk6CiAgICAgICAgICAgICAgICBwcmludChmIjo6YWRkLW1hc2s6Ont2fSIpICAgICAgIyDroZzqt7jsl5Ag7Yag7YGw7J20IOywje2eiOyngCDslYrqsowKICAgICAgICAgICAgICAgIGYud3JpdGUoZiJ7a309e3Z9XG4iKQogICAgZWxzZToKICAgICAgICBwcmludChqc29uLmR1bXBzKG91dCwgaW5kZW50PTIsIGVuc3VyZV9hc2NpaT1GYWxzZSkpCgogICAgcmV0dXJuIDAgaWYgb3V0IGVsc2UgMQoKCmlmIF9fbmFtZV9fID09ICJfX21haW5fXyI6CiAgICBzeXMuZXhpdChtYWluKCkpCg=='}


def run(*a):
    return subprocess.run(a, cwd=ROOT, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT)   # 한글 깨짐 방지: 바이트로 받음


def main():
    print("토큰 갱신 수리 스크립트")
    print("폴더:", ROOT)
    print()

    if not os.path.exists(os.path.join(ROOT, "queue.csv")):
        print("!! queue.csv 가 있는 폴더에 두고 실행하세요.")
        input("\n엔터를 누르면 닫힙니다...")
        return

    print("1) 파일 넣는 중")
    for rel, b64 in PAYLOAD.items():
        path = os.path.join(ROOT, *rel.split("/"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(base64.b64decode(b64))
        print("   -", rel)

    print()
    print("2) 깃허브에 올리는 중")
    run("git", "config", "user.name", "wonbi")
    run("git", "config", "user.email", "wonbi@users.noreply.github.com")
    run("git", "add", "-A")
    run("git", "commit", "-m", "refresh_token.py 복구")
    p = run("git", "push")
    if p.returncode != 0:
        run("git", "pull", "--rebase", "--autostash")
        p = run("git", "push")

    if p.returncode == 0:
        print("   OK 올라갔습니다")
    else:
        print("   !! 실패")
        print(p.stdout.decode("utf-8", "replace")[:800])
        print("   로그인 창이 떴는지 확인해 보세요 (Alt+Tab)")

    input("\n엔터를 누르면 닫힙니다...")


if __name__ == "__main__":
    main()
