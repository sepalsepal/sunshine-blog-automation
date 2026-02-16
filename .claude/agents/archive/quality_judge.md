# 품질 판정 에이전트 프로토콜 (김부장용)

> 버전: 2.0 | 최종 수정: 2026-02-12
> 이 문서는 김부장(Opus)이 콘텐츠 품질을 판정할 때 참조하는 에이전트 프로토콜입니다.

---

## 1. 역할 정의

**에이전트명**: 품질 판정 에이전트 (Quality Judge)
**담당자**: 김부장 (Opus)
**책임**: 캡션 콘텐츠 품질 평가 및 PASS/FAIL 판정

---

## 2. 점수 체계 (20점 만점)

### 2.1 평가 차원

| 차원 | 배점 | 기준 |
|------|------|------|
| 구조 일치 | 0~5 | 골든 샘플과 섹션 수, 순서 일치 |
| 톤앤매너 | 0~5 | "햇살이 엄마" 말투 일관성 |
| 정보 정확성 | 0~5 | 독성 매핑 테이블과 일치 |
| 자연스러움 | 0~5 | 어색한 표현 없음 |

### 2.2 PASS 조건 (AND 연산)

```
PASS = (총점 ≥ 15) AND (각 항목 ≥ 3)
```

- 총점 15점 미만 → FAIL
- 어느 한 항목이라도 3점 미만 → FAIL

---

## 3. FAIL 사유 코드

| 코드 | 의미 | 조치 |
|------|------|------|
| STRUCTURE_MISMATCH | 구조 일치 <3 | 슬라이드 구조 재검토 |
| TONE_MISMATCH | 톤앤매너 <3 | 말투 톤 수정 |
| ACCURACY_ERROR | 정보 정확성 <3 | 데이터 소스 재확인 |
| UNNATURAL | 자연스러움 <3 | 문장 다듬기 |
| LOW_TOTAL | 총점 <15 | 전반 재검토 |

---

## 4. 종료 조건 (Hard Gate)

### 4.1 동일 항목 2회 FAIL

```python
if same_item_fail_count >= 2:
    # 해당 항목 중단
    raise ItemTerminationError(f"{food_id} 2회 FAIL - 수동 검토 필요")
```

### 4.2 동일 안전도 3회 연속 FAIL

```python
if consecutive_fail_count[safety] >= 3:
    # 배치 중단
    raise BatchTerminationError(f"{safety} 3회 연속 FAIL - 배치 중단")
```

---

## 5. 골든 샘플

| ID | 이름 | 안전도 | 기대 점수 |
|----|------|--------|-----------|
| #127 | 대파 | FORBIDDEN | 20/20 |
| #136 | 참외 | SAFE | 20/20 |

**근거**: 75% 기준 (20 × 0.75 = 15)

---

## 6. 판정 프로세스

### 6.1 자동 판정

```bash
python3 pipeline/quality_protocol.py --food-id {ID} --verbose
```

### 6.2 김부장 수동 검토

자동 판정 결과가 **FAIL**인 경우:

1. 자동 판정 결과 확인
2. 각 차원별 감점 사유 검토
3. 수정 필요 항목 명시
4. 최종 판정 (승인/반려/수정요청)

### 6.3 판정 기록 양식

```json
{
  "food_id": 127,
  "food_name": "대파",
  "safety": "FORBIDDEN",
  "auto_score": {
    "structure": 5,
    "tone": 5,
    "accuracy": 5,
    "naturalness": 5,
    "total": 20
  },
  "auto_result": "PASS",
  "manual_review": false,
  "final_result": "PASS",
  "reviewer": "김부장",
  "timestamp": "2026-02-12T04:00:00",
  "notes": ""
}
```

---

## 7. 안전도별 판정 기준

### 7.1 SAFE

- 긍정적 톤 허용
- "급여해도 좋아요", "건강에 좋은" 표현 허용
- 급여량, 영양 정보 정확성 확인

### 7.2 CAUTION

- 조건부 긍정 톤
- "소량만", "익혀서" 등 제한 조건 명시 필수
- 주의사항 섹션 필수

### 7.3 FORBIDDEN

- 경고 톤 필수
- "절대 금지", "위험", "독성" 표현 포함
- 긍정 표현 완전 배제 (건강에 좋, 좋아요, 추천 등)
- toxicity_mapping.json 독성 정보 반영

---

## 8. 예외 처리

### 8.1 캡션 파일 없음

```
결과: FAIL
사유: 캡션 파일 없음
조치: 콘텐츠 폴더 확인, 캡션 생성 필요
```

### 8.2 데이터 불일치

```
food_data.json ≠ toxicity_mapping.json
결과: 판정 보류
조치: PD 보고, 데이터 정합성 확인
```

### 8.3 판정 기준 충돌

- scoring_criteria.json > 이 문서 > 자의적 판단
- 김부장 판단이 자동 판정과 충돌 시: 사유 기록 필수

---

## 9. 통신 프로토콜

### 9.1 판정 요청

```
[품질 판정 요청]
대상: #{food_id} {food_name}
안전도: {safety}
플랫폼: {platform}
```

### 9.2 판정 결과

```
[품질 판정 결과]
대상: #{food_id} {food_name}
━━━━━━━━━━━━━━━━━━━━
구조 일치: {score}/5 - {details}
톤앤매너: {score}/5 - {details}
정보 정확성: {score}/5 - {details}
자연스러움: {score}/5 - {details}
━━━━━━━━━━━━━━━━━━━━
총점: {total}/20
결과: {PASS/FAIL}
사유: {fail_reasons}
━━━━━━━━━━━━━━━━━━━━
```

---

## 10. 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|-----------|
| 1.0 | 2026-02-12 | 초기 작성 (100점 체계) |
| 2.0 | 2026-02-12 | 20점 체계로 변경, FAIL 코드 추가 |

---

_이 문서는 scoring_criteria.json 및 RULES.md §22.11-13과 연동됩니다._
