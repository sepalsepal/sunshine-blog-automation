# /cover - 블로그 표지 생성

## 필수 인자
- `$ARGUMENTS` = 콘텐츠 번호 또는 이름 (예: 060, 후라이드치킨)

## 인자 검증
인자가 없으면 아래 메시지 출력 후 중단:
```
사용법: /cover <콘텐츠번호 또는 이름>
예시: /cover 060
      /cover 후라이드치킨
```

## 실행 절차

### 1. RULES.md 확인
- RULES.md §8 v2.0 표지 규칙 확인
- 불가침 항목 재확인

### 2. 콘텐츠 폴더 찾기
- `contents/` 하위에서 `$ARGUMENTS`와 일치하는 폴더 검색
- 번호(060) 또는 이름(후라이드치킨) 매칭

### 3. 표지 생성
- `services/scripts/blog_cover_v2.py` 실행
- 또는 RULES.md §8.8 코드 레퍼런스 기반 직접 생성

### 4. Validator 자동 실행
- Hook이 자동으로 cover_validator.py 실행
- FAIL 시 재제작 안내

### 5. 결과 보고
```
/cover 결과
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
콘텐츠: {번호}_{이름}
생성 파일: blog/01_표지_{음식명}.png
Validator: PASS/FAIL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## 규칙 (§8 v2.0)

| 항목 | 값 | 금지 |
|------|-----|------|
| 해상도 | 1080x1080 | 다른 해상도 |
| 폰트 | BlackHanSans-Regular | NotoSansCJK |
| 폰트 크기 | 120px | 조정 |
| 텍스트 색상 | #FFFFFF | 다른 색상 |
| Y 위치 | 80px | 변경 |
| 드롭쉐도우 | offset=2, blur=3, alpha=100 | stroke 사용 |
| 그라데이션 | 상단 25%, alpha 80→0 | 하단 그라데이션 |
| 언어 | 한글 음식명 | 영어 |

## 금지 사항
- stroke_width 사용 금지 (§8.6)
- 영어 텍스트 금지
- 서브타이틀/부제목 금지
- SAFE/CAUTION 뱃지 금지
- Cloudinary 중복 업로드 금지
