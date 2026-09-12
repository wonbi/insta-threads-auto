# 쓰레드 · 인스타그램 매일 자동 발행 세팅

내 PC를 켜둘 필요 없이, **GitHub 서버가 매일 정해진 시각에 대신 올려주는** 구조입니다.
Meta 공식 API를 쓰기 때문에 계정 정지 위험이 없고, 월 비용은 0원입니다.

```
media/ 폴더에 영상·이미지 올리기
        ↓
queue.csv 에 날짜 / 시각 / 캡션 적기
        ↓
GitHub Actions 가 매시간 확인 → 해당 시각이 되면
        ↓
Threads API + Instagram API 로 자동 발행
```

---

## 전체 순서 (처음 1회, 약 40~60분)

| 단계 | 내용 | 소요 |
|---|---|---|
| 1 | 인스타 계정을 프로 계정으로 전환 | 2분 |
| 2 | ~~GitHub 저장소 만들고 파일 올리기~~ ✅ 완료 | — |
| 3 | Meta 개발자 앱 만들기 (인스타 + 쓰레드) | 20분 |
| 4 | 토큰 4개 발급해서 GitHub Secrets 에 등록 | 15분 |
| 5 | 테스트 발행 1회 | 5분 |

이후로는 **파일 넣고 CSV 한 줄 쓰는 것**이 전부입니다.

---

## 1단계 · 인스타 프로 계정 전환

인스타 앱 → 설정 → 계정 종류 및 도구 → **프로페셔널 계정으로 전환** → 크리에이터 선택.

> API 자동 발행은 프로 계정(비즈니스·크리에이터)에서만 됩니다. 개인 계정은 불가합니다.
> 페이스북 페이지 연결은 **필요 없습니다** (Instagram Login 방식 사용).

---

## 2단계 · GitHub 저장소 ✅ 완료

저장소: **https://github.com/wonbi/insta-threads-auto** (Public)

```
insta-threads-auto/
├── post.py                 발행 스크립트
├── get_token.py            쓰레드 토큰 발급
├── refresh_token.py        토큰 갱신
├── queue.csv               발행 큐
├── media/                  영상·이미지 넣는 곳
└── .github/workflows/
    ├── daily-post.yml      매시간 자동 실행
    └── monthly-refresh.yml 매달 토큰 갱신
```

> Public 인 이유 — 미디어 파일을 CDN 공개 주소로 Meta 서버에 넘겨야 해서입니다.
> 어차피 발행할 콘텐츠라 공개돼도 문제없고, **토큰은 Secrets 에 암호화 저장**되므로 안전합니다.

---

## 3단계 · Meta 개발자 앱 만들기

[developers.facebook.com](https://developers.facebook.com) → 로그인 → **내 앱 → 앱 만들기**

### 3-1. 인스타그램 설정

1. 앱 유형에서 **비즈니스** 선택 → 앱 이름 입력
2. 제품 추가 → **Instagram** → **Instagram API 설정 (Instagram 로그인 사용)**
3. **비즈니스 로그인 설정** 에서 권한에 아래가 포함되는지 확인
   - `instagram_business_basic`
   - `instagram_business_content_publish`
4. 같은 화면의 **Instagram 테스터 추가** 에 본인 인스타 계정을 추가하고,
   인스타 앱 → 설정 → 앱 및 웹사이트 → 테스터 초대 **수락**
5. **액세스 토큰 생성** 버튼을 눌러 토큰을 복사 → `IG_TOKEN`
6. 같은 화면에 표시되는 **Instagram 사용자 ID** 복사 → `IG_USER_ID`

> 본인 계정에만 올릴 거라면 **앱 검수(App Review)는 받지 않아도 됩니다.**
> 테스터로 등록된 계정은 개발 모드에서 그대로 동작합니다.

### 3-2. 쓰레드 설정

1. 같은 앱에서 제품 추가 → **Threads API**
2. **Threads 테스터 추가** 에 본인 계정 추가 → 쓰레드 앱에서 초대 수락
3. **Threads 앱 ID / 앱 시크릿** 복사해 둡니다
4. **리디렉션 콜백 URL** 에 HTTPS 주소를 하나 등록합니다.
   본인 사이트가 없으면 `https://example.com/` 처럼 아무 HTTPS 주소도 됩니다.
   (실제로 접속되는 페이지일 필요 없음 — 주소창의 `code` 값만 쓰면 됩니다)
5. 내 PC에서 파이썬으로 아래를 실행합니다.

```
python get_token.py
```

안내대로 주소를 브라우저에 붙여넣고 → 권한 허용 → 바뀐 주소 전체를 복사해 붙여넣으면
`THREADS_USER_ID` 와 `THREADS_TOKEN` 이 출력됩니다.

> 파이썬이 없으면 [python.org](https://www.python.org/downloads/) 에서 설치하고,
> 설치 화면의 **Add Python to PATH** 를 반드시 체크하세요.

---

## 4단계 · GitHub Secrets 등록

저장소 → **Settings → Secrets and variables → Actions → New repository secret**

| 이름 | 값 |
|---|---|
| `THREADS_USER_ID` | 3-2에서 받은 숫자 ID |
| `THREADS_TOKEN` | 3-2에서 받은 긴 토큰 |
| `IG_USER_ID` | 3-1에서 받은 숫자 ID |
| `IG_TOKEN` | 3-1에서 받은 긴 토큰 |

토큰 자동 갱신까지 쓰려면 하나 더:

| `GH_PAT` | GitHub 개인 액세스 토큰 (아래 참고) |

> GitHub → Settings → Developer settings → Personal access tokens → Fine-grained →
> 이 저장소만 선택 → Repository permissions 에서 **Secrets: Read and write** 허용

---

## 5단계 · 테스트 발행

1. `media/` 에 테스트용 JPG 하나 올리기 (예: `test.jpg`)
2. `queue.csv` 에 오늘 날짜로 한 줄 추가
3. 저장소 → **Actions → 자동 발행 → Run workflow**
   - 먼저 `dry_run` 체크하고 실행 → 주소가 제대로 만들어지는지 로그로 확인
   - 문제없으면 체크 해제하고 다시 실행 → 실제 발행

---

## 매일 하는 일 (이후 운영)

### ① 미디어 넣기
`media/` 폴더에 파일 업로드.

- 파일명은 **영문·숫자·하이픈만** (한글·공백은 CDN에서 깨짐)
- 개당 **20MB 이하**
- 이미지는 **JPG만** (PNG·WebP는 인스타가 거부)
- 영상은 MP4 / H.264 / AAC / 9:16 / 3~90초

20MB 넘는 영상은 이 명령으로 줄입니다.
```
ffmpeg -i 원본.mp4 -vf "scale=1080:-2" -c:v libx264 -crf 28 -preset slow -c:a aac -b:a 96k 출력.mp4
```

### ② queue.csv 한 줄 쓰기

```csv
date,time,platform,type,files,caption,status,result
2026-09-20,09:00,both,video,reel-01.mp4,"첫 줄에 후킹.\n\n본문.\n\n#태그",,
```

| 열 | 값 |
|---|---|
| `date` | 발행 날짜 `YYYY-MM-DD` (한국시간) |
| `time` | 발행 시각 `HH:MM` (한국시간, 매시 정각 기준으로 그 이후 첫 실행에 나감) |
| `platform` | `both` / `threads` / `instagram` |
| `type` | `text`(쓰레드 전용) / `image` / `video` / `carousel` |
| `files` | `media/` 안의 파일명. 캐러셀은 `a.jpg;b.jpg;c.jpg` |
| `caption` | 본문. 줄바꿈은 `\n`, 쉼표가 있으면 큰따옴표로 감싸기 |
| `status` | 비워두기 — 발행 후 자동으로 `done` 기록됨 |

한 달치를 미리 채워두면 그대로 매일 나갑니다.

---

## 자주 막히는 지점

| 증상 | 원인과 해결 |
|---|---|
| `media_url` 이 404 | jsDelivr 캐시. 파일 올리고 2~3분 기다린 뒤 재실행 |
| 이미지가 계속 실패 | PNG·WebP는 인스타가 거부합니다. JPG로 변환 |
| 영상 처리가 ERROR | 20MB 초과이거나 코덱 문제. 위 ffmpeg 명령으로 재인코딩 |
| 토큰 만료 (`OAuthException`) | 60일 지남. `monthly-refresh` 워크플로가 자동 갱신하지만, 놓쳤으면 3단계 재실행 |
| 파일명에 한글 | 영문으로 바꾸기 |
| 아무것도 안 올라감 | Actions 탭에서 실행 로그 확인. `발행할 항목 없음` 이면 date/time/status 열 확인 |

---

## 알아둘 제한

- **발행 한도** — 인스타 24시간당 100건, 쓰레드 24시간당 250건. 하루 1~3건이면 여유롭습니다.
- **토큰 수명** — 60일. 자동 갱신 워크플로를 켜두면 신경 쓸 일 없습니다.
- **스토리는 불가** — 인스타 API는 릴스·피드·캐러셀만 지원합니다.
- **크로스포스팅 아님** — 쓰레드와 인스타에 각각 별도로 올라갑니다.
- **GitHub Actions 크론은 몇 분 늦을 수 있습니다.** 정각에 딱 맞춰 나가지 않아도 정상입니다.

---

## 다음 단계 (원하면)

콘텐츠 제작까지 자동화하려면 Claude 스케줄 작업을 붙일 수 있습니다.
매일 아침 Claude가 소재를 찾아 카드뉴스 이미지와 캡션을 만들어 이 폴더에 넣고,
`queue.csv` 에 줄을 추가하는 식입니다. 필요하시면 말씀해 주세요.
