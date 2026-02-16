# QC 체크리스트

## 버전: 1.0
## 최종 수정: 2026-02-14

---

## 목적

콘텐츠 품질 검수 시 사용할 전체 체크리스트를 정의한다.

---

## 검증 항목

### 1. 파일 존재

| 파일 | 위치 | 필수 |
|------|------|------|
| Common_01_Cover.png | 루트 | ✅ |
| Common_02_Food.png | 루트 | ⚠️ (없으면 경고) |
| Common_08_Cta.png | 루트 | ✅ |
| {Food}_{Safety}_Insta_Caption.txt | 01_Insta&Thread/ | ✅ |
| {Food}_{Safety}_Thread_Caption.txt | 01_Insta&Thread/ | ✅ |
| {Food}_{Safety}_Blog_Caption.txt | 02_Blog/ | ✅ |
| Blog_03~07.png | 02_Blog/ | ✅ |

---

### 2. 네이밍 검증

```
□ PascalCase 준수
□ {Food}_{Safety}_{Platform}_Caption.txt 형식
□ 안전도 food_data 일치
□ 폴더명 {번호}_{PascalCase} 형식
```

---

### 3. 캡션 내용 검증

```
□ 제목: "강아지 {음식명} 먹어도 되나요?" 형식
□ 구조: 결론 → 주의 → 금지 → 급여 → 핵심 → CTA → AI고지 → 해시태그
□ 급여량 4단계 모두 포함
□ 체감 단위 포함
□ CTA 존재
□ AI 고지 존재
□ 해시태그 12~16개 (인스타/블로그)
□ 쓰레드: 해시태그 없음, 5-7줄
□ FORBIDDEN: 급여법/조리법 없음
```

---

### 4. 이미지 검증

```
□ 해상도 1080x1080 (커버) 또는 1080x1350 (슬라이드)
□ 안전도 색상 일치 (픽셀 샘플링)
□ 텍스트 가독성
□ 그라데이션 존재 (커버)
□ 카드 레이아웃 (인포그래픽)
□ 8장: 실사 햇살이 사진
```

---

### 5. food_data 일치

```
□ 안전도 일치
□ 영양성분 정확
□ 급여량 정확
□ 주의사항 포함
```

---

## PASS/FAIL 기준

### PASS 조건

모든 필수 항목 합격

### FAIL 조건 — 즉시 불합격

```
□ FORBIDDEN 음식에 급여법/조리법 포함
□ 제목이 질문형이 아님
□ 안전도 불일치
□ 파일 누락 (필수 항목)
□ 해상도 미달
```

### WARNING — 경고 (통과하되 기록)

```
□ 해시태그 11개 이하 또는 17개 이상
□ Common_02_Food 미존재 (PD TODO)
□ 00_Clean 파일 미식별
□ 글자수 범위 초과/미달
```

---

## 자동 QC 스크립트

```bash
python scripts/auto_qc.py {폴더번호}
python scripts/auto_qc.py --all
```

**출력:** qc_result.json

---

## 결과 형식

```json
{
  "folder": "001_Pumpkin",
  "result": "PASS",
  "checks": {
    "file_exists": "PASS",
    "naming": "PASS",
    "caption_content": "PASS",
    "image_quality": "PASS",
    "food_data_match": "PASS"
  },
  "warnings": [],
  "failures": []
}
```

---

## 불합격 시 조치

1. 불합격 사유 확인
2. 해당 항목 재작업
3. auto_qc.py 재실행
4. PASS 확인 후 다음 단계

---

## 참조

- 불합격 사례: `./REJECTION_CASES.md`
