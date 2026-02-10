# /publish - 인스타+쓰레드 게시

## 필수 인자
- `$ARGUMENTS` = 콘텐츠 번호 또는 이름 (예: 060, 후라이드치킨)

## 인자 검증
인자가 없으면 아래 메시지 출력 후 중단:
```
사용법: /publish <콘텐츠번호 또는 이름>
예시: /publish 060
      /publish 후라이드치킨
```

## 실행 절차

### 1. RULES.md 확인
- §9 게시 SOP 확인

### 2. 게시 전 점검 (§9.2)
```
□ 이미지 전체 존재 (표지 + 본문 8장)
□ 전 슬라이드 1080x1080
□ 캡션 파일 존재
□ 안전도 이모지 정확
□ AI 고지 포함
□ 해시태그 12~16개
□ 캡션-본문 안전도 일치
```
→ **1개라도 FAIL = 게시 중단 + PD 보고**

### 3. Validator 전체 실행 (15개)
- pre_publish_validator.py 실행
- FAIL 시 즉시 중단

### 4. Cloudinary 업로드 (§9.3)
```
① 구글시트에서 기존 Cloudinary URL 확인
② URL 존재 → 재업로드 금지, 기존 URL 사용
③ URL 없음 → 신규 업로드
④ 업로드 후 구글시트에 URL 기록
```

### 5. Instagram 게시
- Graph API 캐러셀 생성
- container → carousel → publish
- permalink 저장

### 6. Threads 게시
- Threads API 캐러셀 생성 (동일 캡션)
- permalink 저장

### 7. 게시 후 처리
- 상태 → posted 변경
- 게시일시 기록
- 폴더 이동: `3_approved/` → `4_posted/`

### 8. 결과 보고
```
✅ {음식명} 게시 완료
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📸 Instagram: {permalink}
🧵 Threads: {permalink}
📄 슬라이드: {N}장
🕐 게시: {시각}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## 예외 처리 (§9.7)

| 상황 | 처리 |
|------|------|
| 토큰 만료 | PD에게 재발급 요청 |
| Rate limit | 60초 대기 후 1회 재시도 |
| 이미지/캡션 누락 | 게시 중단 + PD 보고 |
| Validator FAIL | 게시 중단 + FAIL 항목 안내 |
| Cloudinary URL 존재 | 재업로드 금지 |

## 금지 사항
- Validator FAIL 상태에서 게시 시도 금지 (§10.3.5)
- 점검 FAIL 시 자의적 수정 금지 → PD/김부장 보고 후 대기
- Cloudinary 중복 업로드 금지
