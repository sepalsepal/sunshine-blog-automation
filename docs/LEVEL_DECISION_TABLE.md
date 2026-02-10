# L1 / L1-C / L2 판정 테이블 (Draft)

> **상태:** DRAFT - 확정 아님
> **작성일:** 2026-01-31 (Day 11 야간)
> **기준 문서:** AOC v0.4, PHASE2_RULES.md
> **Day 11 실제 적용 결과:** 9건 검증 → 7건 L1, 2건 L2

---

## 레벨 정의 요약

| 레벨 | 안전 분류 | 조건 | 처리 | 예시 |
|:----:|----------|------|------|------|
| **L1** | SAFE | 무조건 안전 | AUTO_PUBLISH | 당근, 사과, 소고기, 연어 |
| **L1** | FORBIDDEN | 무조건 금지 | AUTO_PUBLISH | 포도, 초콜릿, 자일리톨 |
| **L1-C** | CAUTION | 조건 4가지 충족 | AUTO (조건부) | - (테스트 필요) |
| **L2** | CAUTION | 조건 미충족 | HUMAN_QUEUE | 참치, 케일, 치즈 |
| **L2** | CONDITIONAL | 조건 의존 | HUMAN_QUEUE | 달걀(익힌것만), 요거트 |
| **L3** | DANGER | 복합 판단 필요 | HUMAN_QUEUE | - (Phase 2에서 미사용) |

---

## L1: AUTO_PUBLISH

### 대상
- **SAFE:** 무조건 안전한 음식
- **FORBIDDEN:** 무조건 금지 음식 (경고 콘텐츠)

### 판정 조건
```
다음 모두 충족 시 L1:
□ safety_class == SAFE 또는 FORBIDDEN
□ topics_expanded.json에 등록됨
□ Agent B 평균 70점+
□ Agent D Red Flag 0개
□ 질문 발생 0회
```

### Day 11 L1 판정 결과

| 콘텐츠 | 안전 분류 | topics 등록 | 최종 판정 |
|--------|:--------:|:-----------:|:--------:|
| beef (소고기) | SAFE | ✅ | **L1** |
| salmon (연어) | SAFE | ✅ | **L1** |
| chicken (닭고기) | SAFE | ✅ | **L1** |
| celery (셀러리) | SAFE | ✅ | **L1** |
| zucchini (애호박) | SAFE | ✅ | **L1** |
| potato (감자) | SAFE | ✅ | **L1** |
| burdock (우엉) | SAFE | ✅ (추가됨) | **L1** |

### L1 처리 흐름
```
음식 → SAFE/FORBIDDEN 확인 → Agent 5종 평가 → 기준 충족 → 자동 게시
                                              └→ 미충족 → 재시도 1회 → 실패 시 L2로 강등
```

---

## L1-C: AUTO_PUBLISH (조건부)

### 대상
- **CAUTION:** 주의 필요 음식 중 조건 충족 시

### 판정 조건 (4가지 모두 충족 필수)
```
□ safety_class == CAUTION
□ warning_text_present == True (경고 문구 포함)
□ warning_position == first_2_lines (첫 2줄에 경고)
□ emoji_or_icon_present == True (⚠️ 또는 아이콘)
```

### L1-C 검증 로직 (의사코드)
```python
def is_L1_C_eligible(content):
    """L1-C 자격 검증"""

    # 1. 안전 분류 확인
    if content.safety_class != "CAUTION":
        return False, "안전 분류가 CAUTION이 아님"

    # 2. 경고 문구 포함 확인
    warning_keywords = ["주의", "조심", "적게", "소량", "과다 금지"]
    has_warning = any(kw in content.caption for kw in warning_keywords)
    if not has_warning:
        return False, "경고 문구 미포함"

    # 3. 경고 위치 확인 (첫 2줄)
    first_2_lines = "\n".join(content.caption.split("\n")[:2])
    warning_in_first_2 = any(kw in first_2_lines for kw in warning_keywords)
    if not warning_in_first_2:
        return False, "경고가 첫 2줄에 없음"

    # 4. 이모지/아이콘 확인
    warning_emojis = ["⚠️", "🚨", "❗", "⛔"]
    has_emoji = any(emoji in content.caption for emoji in warning_emojis)
    if not has_emoji:
        return False, "경고 이모지 없음"

    return True, "L1-C 자격 충족"
```

### L1-C 테스트 대상 (Phase 2.5 예정)
```
후보:
- tuna (참치): CAUTION - 수은 주의
- kale (케일): CAUTION - 옥살산 주의
- yogurt (요거트): CAUTION - 무당/소량

테스트 방법:
1. L1-C 4가지 조건 수동 충족
2. Agent 평가 → 기준 충족 확인
3. 테스트 게시 (모니터링 24시간)
4. 이상 없으면 L1-C 공식 적용
```

---

## L2: HUMAN_QUEUE

### 대상
- **CAUTION:** L1-C 조건 미충족
- **CONDITIONAL:** 조건 의존 음식

### 판정 조건
```
다음 중 하나 이상 해당 시 L2:
□ safety_class == CAUTION + L1-C 조건 미충족
□ safety_class == CONDITIONAL
□ Agent B 평균 70점 미만
□ Agent D Red Flag 1개
□ 질문 발생 1회
```

### Day 11 L2 판정 결과

| 콘텐츠 | 안전 분류 | L2 판정 사유 |
|--------|:--------:|-------------|
| tuna (참치) | CAUTION | 수은 주의 - 경고 강화 필요 |
| kale (케일) | CAUTION | 옥살산 주의 - 신장 문제 시 주의 |

### L2 처리 흐름
```
음식 → CAUTION/CONDITIONAL 확인 → Agent 5종 평가 → HUMAN_QUEUE 전송
                                                    ↓
                                              사람 확인 → 승인 시 게시
                                                    └→ 반려 시 수정 후 재평가
```

### L2 HUMAN_QUEUE 확인 항목
```
□ 경고 문구 충분성
□ 급여 조건 명확성
□ 대상 제한 (소형견/대형견/신장질환 등)
□ 캡션-이미지 정합성
□ 전체 톤 적절성
```

---

## L3: HUMAN_QUEUE (강화)

### 대상
- **DANGER:** 위험 음식

### 판정 조건
```
□ safety_class == DANGER
□ Agent D 강화 검사 필수
□ Red Flag 0개 필수
□ 사람 승인 필수
```

### L3 처리 흐름
```
음식 → DANGER 확인 → Agent 5종 평가 + Agent D 강화 검사
                                    ↓
                            Red Flag 0개 → HUMAN_QUEUE
                                    └→ Red Flag 1개+ → 즉시 STOP
```

### Phase 2 L3 상태
```
현재: L3 콘텐츠 게시 보류
이유: Phase 2는 L1 안정화 우선
계획: Phase 3에서 L3 테스트 예정
```

---

## 판정 플로우차트

```
                     [콘텐츠 입력]
                          │
                          ▼
              ┌───────────────────────┐
              │   안전 분류 확인      │
              │ topics_expanded.json  │
              └───────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
          ▼               ▼               ▼
    ┌─────────┐     ┌─────────┐     ┌─────────┐
    │  SAFE   │     │ CAUTION │     │ DANGER  │
    │FORBIDDEN│     │CONDITION│     │         │
    └─────────┘     └─────────┘     └─────────┘
          │               │               │
          ▼               ▼               ▼
    ┌─────────┐     ┌─────────┐     ┌─────────┐
    │   L1    │     │ L1-C?   │     │   L3    │
    │ AUTO    │     │ 조건확인 │     │ HUMAN   │
    └─────────┘     └─────────┘     └─────────┘
                          │
                    ┌─────┴─────┐
                    │           │
                    ▼           ▼
              ┌─────────┐ ┌─────────┐
              │  L1-C   │ │   L2    │
              │(조건부) │ │ HUMAN   │
              └─────────┘ └─────────┘
```

---

## Day 11 판정 실적

### 판정 정확도
| 지표 | 결과 |
|------|:----:|
| L1 판정 정확도 | 100% (7/7) |
| L2 재분류 정확도 | 100% (2/2) |
| 오분류 | 0건 |
| 질문 발생 | 0회 |

### 발견 사항
```
1. tuna(참치): topics_expanded.json에서 CAUTION으로 이미 등록됨
   → L2로 정확히 분류됨

2. kale(케일): topics_expanded.json 미등록
   → 웹 검색으로 CAUTION (옥살산 주의) 확인
   → 수동 등록 후 L2로 분류

3. burdock(우엉): topics_expanded.json 미등록
   → 웹 검색으로 SAFE 확인
   → 수동 등록 후 L1로 분류
```

---

## L1-C 도입 로드맵

### Phase 2.5 (예정)
```
1. L1-C 조건 4가지 자동 검증 로직 구현
2. tuna/kale로 L1-C 테스트
3. 24시간 모니터링
4. 이상 없으면 L1-C 공식 적용
```

### Phase 3 (예정)
```
1. L1-C 자동 게시 활성화
2. L3 (DANGER) 콘텐츠 테스트
3. 전체 AUTO_PUBLISH 비율 측정
```

---

⚠️ DRAFT - 확정 아님
**작성자:** 김부장 (Claude Opus 4.5)
**검토 대기:** PD님
