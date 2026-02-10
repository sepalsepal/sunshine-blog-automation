# /batch insta - 인스타그램 배치 처리

인스타그램 콘텐츠를 대량 생성/게시합니다.

## 사용 가능한 작업

| 작업 | 설명 | 규칙 |
|------|------|------|
| `cover` | 인스타 표지 생성 | §8 |
| `body` | 본문 슬라이드 생성 | §2~§6 |
| `caption` | 인스타 캡션 작성 | §6.5~§6.6 |
| `pipeline` | 표지+본문+캡션 전체 | §2~§8 |
| `publish` | 인스타 게시 | §9 |
| `validate` | 인스타 Validator | 15개 |

## 예시

```bash
/batch insta cover 060-070      # 표지 11개 생성
/batch insta body 001,005,009   # 본문 3개 생성
/batch insta caption 3_approved # 승인 대기 전체 캡션
/batch insta pipeline 060       # 060 전체 파이프라인
/batch insta publish 3_approved # 승인된 전체 게시
/batch insta validate all       # 전체 검증
```

## cover 작업

### 실행 내용
1. 콘텐츠 폴더 찾기
2. §8 표지 규칙 적용
3. 표지 이미지 생성 (1080x1080)
4. Validator 자동 실행 (Hook)

### 생성 파일
```
{콘텐츠}/blog/01_표지_{음식명}.png
```

### 규칙 (§8)
- 폰트: BlackHanSans-Regular 120px
- 드롭쉐도우: offset=2, blur=3, alpha=100
- 상단 그라데이션: 25%, alpha 80→0
- Y 위치: 80px

## body 작업

### 실행 내용
1. §2~§6 본문 규칙 적용
2. 슬라이드 7장 생성 (03~07: C2 인포그래픽)
3. 본문 텍스트 생성
4. Validator 자동 실행

### 생성 파일
```
{콘텐츠}/blog/02_음식사진.png
{콘텐츠}/blog/03_영양성분.png
{콘텐츠}/blog/04_급여방법.png
{콘텐츠}/blog/05_급여량.png
{콘텐츠}/blog/06_주의사항.png
{콘텐츠}/blog/07_조리방법.png
{콘텐츠}/blog/08_햇살이.png  ← 실사 전용
{콘텐츠}/blog/본문.txt
```

## caption 작업

### 실행 내용
1. §6.5~§6.6 캡션 규칙 적용
2. 파스타 구조 캡션 생성
3. Validator 자동 실행

### 생성 파일
```
{콘텐츠}/caption_instagram.txt
```

### 파스타 구조
1. 안전 이모지 + 결론
2. 주의사항
3. 급여량 (4줄 형식)
4. 핵심 메시지
5. CTA
6. AI 고지
7. 해시태그 12~16개

## pipeline 작업

### 실행 순서
1. cover 실행 → FAIL 시 스킵
2. body 실행 → FAIL 시 스킵
3. caption 실행 → FAIL 시 스킵
4. 전체 Validator
5. 결과 보고

### 장점
- 한 콘텐츠 전체 작업을 한 번에
- 중간 FAIL 시 다음 콘텐츠로

## publish 작업

### 실행 내용
1. §9 게시 SOP 적용
2. 게시 전 Validator 전체 실행
3. Cloudinary 업로드 (기존 URL 확인)
4. Instagram Graph API 게시
5. permalink 저장
6. 폴더 이동 (→ 4_posted)

### 주의
- Validator FAIL 시 게시 차단
- Rate limit 시 60초 대기 후 재시도

## validate 작업

### 실행 내용
1. 15개 Validator 순차 실행
2. PASS/FAIL 결과 출력
3. FAIL 항목 상세 사유

### 결과 형식
```
060: ✅ PASS (15/15)
061: ❌ FAIL (13/15) - 표지 Y위치, 캡션 해시태그
062: ✅ PASS (15/15)
```
