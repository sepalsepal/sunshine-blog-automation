# /batch threads - 쓰레드 배치 처리

쓰레드 콘텐츠를 대량 생성/게시합니다.

## 중요: 이미지 공유 정책

```
⚠️ 쓰레드는 인스타그램 이미지를 공유합니다.
   cover, body, pipeline 작업은 사용할 수 없습니다.
```

| 작업 | 가능 여부 | 이유 |
|------|----------|------|
| `cover` | ❌ 불가 | 인스타 이미지 공유 |
| `body` | ❌ 불가 | 인스타 이미지 공유 |
| `pipeline` | ❌ 불가 | cover/body 포함 |
| `caption` | ✅ 가능 | 쓰레드 전용 (짧은 버전) |
| `publish` | ✅ 가능 | 쓰레드 게시 |
| `validate` | ✅ 가능 | 캡션 검증 |

## 사용 가능한 작업

| 작업 | 설명 | 규칙 |
|------|------|------|
| `caption` | 쓰레드 캡션 (짧은 버전) | §6.6 |
| `publish` | 쓰레드 게시 | §9.4 |
| `validate` | 캡션 검증 | §6 |

## 예시

```bash
# 가능
/batch threads caption 060-070    # 쓰레드 캡션 11개
/batch threads publish 3_approved # 승인된 전체 게시
/batch threads validate all       # 전체 캡션 검증

# 불가능 (에러 발생)
/batch threads cover 060-070      # ❌ 에러
/batch threads body 060-070       # ❌ 에러
/batch threads pipeline 060       # ❌ 에러
```

## caption 작업

### 인스타 캡션과의 차이

| 항목 | 인스타 | 쓰레드 |
|------|--------|--------|
| 길이 | 긴 버전 (파스타 전체) | 짧은 버전 |
| 급여량 | 4줄 상세 | 1줄 요약 |
| 해시태그 | 12~16개 | 3~5개 |
| CTA | 저장/팔로우 | 댓글/공유 |

### 쓰레드 캡션 구조

```
{안전 이모지} 강아지 {음식명}, {결론 한 줄}

{핵심 주의사항 1~2개}

📏 급여량: 소형견 Xg, 중형견 Xg, 대형견 Xg

💬 궁금한 점은 댓글로 남겨주세요!

#강아지{음식명} #강아지간식 #펫스타그램 #{추가1} #{추가2}
```

### 생성 파일
```
{콘텐츠}/caption_threads.txt
```

## publish 작업

### 실행 내용
1. §9.4 쓰레드 게시 SOP 적용
2. 인스타 이미지 URL 확인 (Cloudinary)
3. 쓰레드 캡션 로드
4. Threads API 캐러셀 생성
5. permalink 저장

### 전제 조건
- 인스타 이미지가 이미 Cloudinary에 업로드되어 있어야 함
- 인스타 게시 후 쓰레드 게시 권장

### 실행 순서 권장
```bash
/batch insta publish 060-070    # 먼저 인스타 게시
/batch threads publish 060-070  # 그 다음 쓰레드 게시
```

## validate 작업

### 검증 항목
- 캡션 파일 존재
- 안전 이모지 존재
- 해시태그 3~5개
- 길이 적정 (500자 이하)

### 결과 형식
```
060: ✅ PASS - 캡션 검증 통과
061: ❌ FAIL - 해시태그 12개 (3~5개 필요)
```

## 에러 메시지

| 에러 | 메시지 |
|------|--------|
| cover 시도 | "쓰레드는 인스타 이미지 공유. /batch insta cover 사용" |
| body 시도 | "쓰레드는 인스타 이미지 공유. /batch insta body 사용" |
| pipeline 시도 | "쓰레드는 이미지 공유. /batch insta pipeline 사용" |
| 인스타 이미지 없음 | "인스타 이미지 먼저 생성 필요: /batch insta pipeline {대상}" |
