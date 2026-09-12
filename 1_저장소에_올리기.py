#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
이 폴더를 GitHub 저장소 구조로 정리하고 업로드까지 해준다.

사용법 — 이 파일이 있는 폴더에서:
    python 1_저장소에_올리기.py

git 이 설치돼 있으면 바로 push 까지 하고,
없으면 폴더만 정리해서 드래그 업로드 방법을 안내한다.
"""

import os
import shutil
import subprocess
import sys

REPO = "https://github.com/wonbi/insta-threads-auto.git"
HERE = os.path.dirname(os.path.abspath(__file__))

# (현재 위치, 저장소에서의 위치)
MOVES = [
    ("scripts/post.py",              "post.py"),
    ("scripts/get_token.py",         "get_token.py"),
    ("scripts/refresh_token.py",     "refresh_token.py"),
    ("workflows/daily-post.yml",     ".github/workflows/daily-post.yml"),
    ("workflows/monthly-refresh.yml", ".github/workflows/monthly-refresh.yml"),
    ("media-README.md",              "media/README.md"),
    ("workflows/이파일어디에넣나요.md", None),   # 삭제 대상
]


def run(*args, check=True):
    return subprocess.run(args, cwd=HERE, check=check,
                          capture_output=True, text=True, encoding="utf-8")


def step1_restructure():
    print("1) 폴더 구조 정리")
    for src, dst in MOVES:
        s = os.path.join(HERE, src.replace("/", os.sep))
        if not os.path.exists(s):
            continue
        if dst is None:
            os.remove(s)
            print(f"   삭제  {src}")
            continue
        d = os.path.join(HERE, dst.replace("/", os.sep))
        os.makedirs(os.path.dirname(d), exist_ok=True)
        shutil.move(s, d)
        print(f"   이동  {src}  ->  {dst}")

    # 빈 폴더 정리
    for folder in ("scripts", "workflows"):
        p = os.path.join(HERE, folder)
        if os.path.isdir(p) and not os.listdir(p):
            os.rmdir(p)
            print(f"   정리  {folder}/")

    os.makedirs(os.path.join(HERE, "media"), exist_ok=True)
    print("   완료\n")


def step2_push():
    if not shutil.which("git"):
        return False

    print("2) GitHub 업로드")
    if not os.path.isdir(os.path.join(HERE, ".git")):
        run("git", "init")
    run("git", "branch", "-M", "main", check=False)
    run("git", "remote", "remove", "origin", check=False)
    run("git", "remote", "add", "origin", REPO, check=False)

    # 커밋에 필요한 신원 정보 (이 폴더에만 적용)
    run("git", "config", "user.name", "wonbi", check=False)
    run("git", "config", "user.email", "wonbi@users.noreply.github.com", check=False)

    run("git", "add", "-A")
    r = run("git", "commit", "-m", "자동 발행 시스템 추가", check=False)
    if r.returncode != 0 and "nothing to commit" not in (r.stdout + r.stderr):
        print(r.stdout, r.stderr)

    print("   push 중… 로그인 창이 뜨면 GitHub 계정으로 승인하세요.")
    r = run("git", "push", "-u", "origin", "main", "--force", check=False)
    if r.returncode != 0:
        print("   push 실패:")
        print(r.stdout, r.stderr)
        return False

    print("   ✅ 업로드 완료\n")
    return True


def main():
    print("=" * 55)
    print(" 쓰레드·인스타 자동 발행 — 저장소 올리기")
    print("=" * 55 + "\n")

    step1_restructure()

    if step2_push():
        print("저장소를 확인하세요:")
        print("  https://github.com/wonbi/insta-threads-auto")
    else:
        print("2) git 으로 올리지 못했습니다. 수동으로 올려주세요.\n")
        print("   ① https://github.com/wonbi/insta-threads-auto/upload 접속")
        print("   ② 이 폴더(인스타쓰레드자동올리기)를 통째로 드래그해서 놓기")
        print("      → 폴더째 드래그하면 .github/workflows 경로가 그대로 유지됩니다")
        print("   ③ 아래 초록색 Commit changes 클릭")

    print("\n끝났으면 Claude 에게 알려주세요.")
    input("\n엔터를 누르면 창이 닫힙니다…")


if __name__ == "__main__":
    main()
