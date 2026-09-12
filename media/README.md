# media

올릴 영상·이미지 파일을 여기에 넣고, `queue.csv` 의 `files` 열에 **파일 이름만** 적는다.

## 규칙
- 파일명은 영문·숫자·하이픈만 (한글·공백·괄호는 CDN 에서 깨진다)
- 개당 **20MB 이하** (jsDelivr CDN 제한)
- 이미지: **JPG만** (PNG·WebP는 인스타그램이 거부)
- 영상: MP4 (H.264 + AAC), 9:16, 3초~90초, 30fps 권장

## 20MB 넘는 영상 줄이기
```
ffmpeg -i 원본.mp4 -vf "scale=1080:-2" -c:v libx264 -crf 28 -preset slow -c:a aac -b:a 96k 출력.mp4
```
