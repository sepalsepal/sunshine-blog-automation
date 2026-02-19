# Override 로그 디렉토리

> 생성일: 2026-02-12
> 규칙: RULES.md §22.15

---

## 목적

자동 품질 판정(quality_protocol.py) 결과를 김부장(Opus)이 수동으로 override할 때 기록하는 로그입니다.

---

## 디렉토리 구조

```
logs/override/
├── README.md              ← 이 파일
├── 20260212/
│   ├── 127_blog_override.json
│   └── ...
├── 20260213/
│   └── ...
└── ...
```

---

## 로그 파일 형식

**파일명:** `{food_id}_{platform}_override.json`

**구조:**
```json
{
  "food_id": 127,
  "food_name": "대파",
  "platform": "blog",
  "auto_score": {
    "structure": 5,
    "tone": 3,
    "accuracy": 5,
    "naturalness": 5,
    "total": 18
  },
  "auto_result": "FAIL",
  "auto_fail_reason": "TONE_MISMATCH",
  "override_by": "김부장",
  "override_result": "PASS",
  "override_reason": "톤 알고리즘 오탐 설명",
  "override_evidence": "캡션 내 실제 표현 증거",
  "timestamp": "2026-02-12T09:30:00",
  "algorithm_update_required": true,
  "notes": "추가 메모"
}
```

---

## 필드 설명

| 필드 | 타입 | 설명 |
|------|------|------|
| food_id | int | 음식 ID |
| food_name | string | 음식 한글명 |
| platform | string | blog / insta / threads |
| auto_score | object | 자동 채점 결과 (4개 차원 + 총점) |
| auto_result | string | PASS / FAIL |
| auto_fail_reason | string | FAIL 사유 코드 |
| override_by | string | override 담당자 |
| override_result | string | PASS / REJECT |
| override_reason | string | override 사유 |
| override_evidence | string | 판정 근거 |
| timestamp | string | ISO 8601 형식 |
| algorithm_update_required | bool | 알고리즘 수정 필요 여부 |
| notes | string | 추가 메모 |

---

## override 규칙 (§22.15)

### 허용
- 총점 미달 (14점 등)
- 개별 항목 미달 (톤 2점 등)

### 금지 (override 불가)
- ACCURACY_ERROR
- SAFETY_MISMATCH

---

## 누적 override 처리

| 동일 reason_code 횟수 | 처리 |
|-----------------------|------|
| 1회 | 로그 기록 후 진행 |
| 2회 | 알고리즘 튜닝 권고 (§22.17) |
| 3회+ | 수동 처리 전환 + 알고리즘 재설계 |

---

_WO-RULE-SUPPLEMENT-FINAL_
