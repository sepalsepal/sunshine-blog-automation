# AOC v0.4 (Agent Operating Contract)

> **버전:** v0.4 (Day 9 업데이트)
> **작성일:** 2026-01-31
> **기준 문서:** Project_Sunshine_Execution_Guidebook_v1.1.md

---

## 공통 계약 (모든 에이전트 적용)

```
[Agent Contract — Hard Mode]

1. 이 에이전트는 질문하지 않는다.
   - 판단 가능 → 판단한다.
   - 판단 불가 → "FAIL-REASON: [사유]"만 출력한다.
   - 인간 확인 지점 외의 질문은 금지한다.

   ⚠️ 예외 1조건:
   - 외부 시스템 상태 불명확 시 (API 응답 스펙 불일치 등)
   - 질문 형식 고정: "ENV-QUESTION: [확인 필요 항목 1줄]"
   - 인간 대화 질문 ❌ / 시스템 확인 질문만 ⭕

2. 선택지는 항상 3개 이하로 제시한다.

3. 판단 기준은 수치만 사용한다.
   - "좋다/나쁘다"는 금지.
   - "85점/기준 90점 미달"로 표현한다.

4. 출력에는 반드시 포함:
   - Self-score (0~100)
   - 실패 예상 포인트 3개
   - 소요 시간

5. FAIL 선언 후 규칙:
   - 원인 유형 1개 선택 (F1~F5 중)
   - 재시도 전략 1개 자동 제안
   - 동일 FAIL 3회 누적 시 → 자동 중단 + PD님 알림

6. FAIL 유형 (5가지 강제 분류):
   - F1: 판단 불가 (정보 부족으로 결정 못함)
   - F2: 기준 충돌 (두 규칙이 모순) ⚠️ 특례 적용
   - F3: 데이터 부족 (입력 데이터 미확보)
   - F4: 규칙 위반 (기존 규칙에 명시적 위배)
   - F5: 반복 실패 (동일 시도 2회 이상 실패)

7. F2 처리 특례:
   - 최초 2회: FAIL 기록 + 계속 진행
   - 3회 누적 시에만 자동 중단
   - Day 7, 14 회복점에서 반드시 리뷰

8. 질문 금지 강화 (v0.3.1 Phase 2 추가):
   - 에이전트 질문 발생 = 즉시 L2 FAIL
   - 질문 로그는 "개선 대상"이 아닌 "구조 위반"으로 기록
   - 동일 세션 내 질문 2회 = 자동 중단
   - 목적: "사람 호출 자동화"로 퇴행 방지
```

---

## ⚠️ v0.3 추가: 캡션-안전분류 제약 로직 (Caption Safety Constraint)

> **목적:** F2 (기준 충돌) 구조적 재발 방지
> **배경:** Day 5~6 테스트에서 icecream, kitkat 캡션/이미지 불일치 발생

### 안전 분류 정의

| 분류 | 정의 | 캡션 템플릿 |
|------|------|-------------|
| **SAFE** | 안전한 음식 | ✅ 먹어도 돼요 |
| **CAUTION** | 주의 필요 | ⚠️ 주의사항 확인 |
| **DANGER** | 위험한 음식 | 🚫 급여를 권장하지 않습니다 |
| **FORBIDDEN** | 절대 금지 | 🚫 절대 먹이면 안 돼요 |

### 강제 적용 규칙

```
[Pre-Check: Agent A 콘텐츠 생성 전 필수]

1. 음식 안전 분류 확인 (SAFE/CAUTION/DANGER/FORBIDDEN)
2. 분류에 맞는 캡션 템플릿 선택 (강제)
3. 템플릿 외 캡션 사용 금지

DANGER/FORBIDDEN → "✅ 먹어도 돼요" 사용 시 즉시 FAIL
SAFE → "🚫 급여 금지" 사용 시 즉시 FAIL
```

### 검증 로직 (Agent B 사전 검사)

```python
def caption_safety_check(food_name, caption_text, safety_classification):
    """
    v0.3 캡션-안전분류 정합성 검사
    Agent B 평가 전 필수 실행
    """
    SAFE_INDICATORS = ["먹어도 돼요", "급여 가능", "✅"]
    DANGER_INDICATORS = ["먹이면 안", "급여 금지", "권장하지 않", "🚫", "❌"]

    caption_appears_safe = any(ind in caption_text for ind in SAFE_INDICATORS)
    caption_appears_danger = any(ind in caption_text for ind in DANGER_INDICATORS)

    # DANGER/FORBIDDEN 음식인데 SAFE 캡션 → F2 FAIL
    if safety_classification in ["DANGER", "FORBIDDEN"]:
        if caption_appears_safe and not caption_appears_danger:
            return {
                "result": "FAIL",
                "fail_type": "F2",
                "reason": f"{food_name}: 안전 분류 {safety_classification}인데 캡션이 SAFE 톤"
            }

    # SAFE 음식인데 DANGER 캡션 → F2 FAIL
    if safety_classification == "SAFE":
        if caption_appears_danger and not caption_appears_safe:
            return {
                "result": "FAIL",
                "fail_type": "F2",
                "reason": f"{food_name}: 안전 분류 SAFE인데 캡션이 DANGER 톤"
            }

    return {"result": "PASS"}
```

### F2 재발 시 조치

```
F2 재발 감지 → 즉시 STOP → 캡션 수정 → 재테스트
재수정 후에도 F2 → 구조적 문제로 판정 → Phase 진입 불가
```

---

## ⚠️ v0.4 추가: AUTO_PUBLISH 등급화 (Day 9)

> **목적:** 안전 분류별 자동화 수준 차등 적용
> **배경:** Day 9 스트레스 테스트 결과 - CONDITIONAL 음식 분기 검증 완료

### AUTO_PUBLISH_LEVEL 정의

| 레벨 | 안전 분류 | 판정 | 사람 개입 |
|:----:|----------|------|:--------:|
| **L1** | SAFE, FORBIDDEN | AUTO_PUBLISH | 없음 |
| **L2** | CONDITIONAL, CAUTION | HUMAN_QUEUE | 필요 |
| **L3** | DANGER | HUMAN_QUEUE | 필수 |

### 레벨별 처리 규칙

```
[L1 - AUTO_PUBLISH]
- 대상: SAFE (안전), FORBIDDEN (절대 금지)
- 이유: 판단 명확 (무조건 OK 또는 무조건 NG)
- 처리: Agent 5종 평가 → 기준 충족 시 자동 게시
- 질문: 0회 필수

[L2 - HUMAN_QUEUE]
- 대상: CONDITIONAL (조건부 가능), CAUTION (주의 필요)
- 이유: 조건에 따라 판단 달라짐
- 처리: Agent 5종 평가 → HUMAN_QUEUE 전송 → 사람 확인
- 예시: cheese(저염만), egg(익힌것만), grape(소량만)

[L3 - HUMAN_QUEUE (강화)]
- 대상: DANGER (위험)
- 이유: 독성/알레르기 위험 - 추가 검증 필수
- 처리: Agent 5종 평가 + Agent D 강화 검사 → HUMAN_QUEUE
- Red Flag 0개 필수
```

### 분류 판정 로직

```python
def get_auto_publish_level(food_name, safety_classification):
    """
    v0.4 AUTO_PUBLISH 레벨 판정
    """
    if safety_classification in ["SAFE", "FORBIDDEN"]:
        return "L1"  # AUTO_PUBLISH 가능
    elif safety_classification in ["CONDITIONAL", "CAUTION"]:
        return "L2"  # HUMAN_QUEUE 필수
    elif safety_classification == "DANGER":
        return "L3"  # HUMAN_QUEUE + 강화 검증
    else:
        return "L2"  # UNKNOWN → 안전하게 사람 확인
```

### Day 9 검증 결과

| 테스트 | 분류 | 예상 레벨 | 실제 판정 | 결과 |
|--------|------|:--------:|----------|:----:|
| cheese | CONDITIONAL | L2 | HUMAN_QUEUE | ✅ |
| egg | CONDITIONAL | L2 | HUMAN_QUEUE | ✅ |
| fake_food | UNKNOWN | L2 | F1 FAIL | ✅ |

---

## Agent A: 콘텐츠 생성 에이전트

| 항목 | 내용 |
|------|------|
| **단일 목표** | 주어진 주제로 캐러셀 콘텐츠 생성 |
| **성공 기준** | Phase 1~2: Self-score 75점+ / Phase 3+: 85점+ |
| **포맷 규격** | 100% 충족 필수 |
| **금지 사항** | 톤 판단, 자동화 판단, 비용 판단 |
| **판단하지 않는 것** | "이게 좋은 콘텐츠인가?" (Agent B 담당) |
| **FAIL 조건** | 포맷 미충족 / 팩트 불확실 / 텍스트 길이 초과 |

### 출력 형식

```json
{
  "agent": "A",
  "task": "콘텐츠 생성",
  "topic": "[주제]",
  "self_score": 0-100,
  "format_compliance": true/false,
  "failure_points": ["point1", "point2", "point3"],
  "elapsed_time": "Xm Xs",
  "result": "PASS/FAIL",
  "fail_type": "F1-F5 (FAIL 시)",
  "retry_strategy": "전략 (FAIL 시)"
}
```

---

## Agent B: 품질 판단 에이전트 (v0.2 업데이트)

| 항목 | 내용 |
|------|------|
| **단일 목표** | Agent A 결과물의 품질 수치 평가 |
| **성공 기준** | 평가 항목 5개 모두 수치 출력 |
| **금지 사항** | 콘텐츠 수정, 대안 생성 |
| **판단하지 않는 것** | "자동화 가능한가?" (Agent C 담당) |
| **FAIL 조건** | 평가 불가 항목 2개 이상 |

### 평가 항목 (5개)

| # | 항목 | 범위 | 설명 |
|---|------|------|------|
| 1 | 정보 정확도 | 0~100 | 팩트 정확성 |
| 2 | 톤 일관성 | 0~100 | v1.1 톤 준수 |
| 3 | 포맷 적합성 | 0~100 | 슬라이드 규격 |
| 4 | 이미지-텍스트 정합성 | 0~100 | 메시지 일치 **(v0.2 강화)** |
| 5 | 플랫폼 정책 준수 | PASS/FAIL | Instagram 규정 |

### ⚠️ v0.2 강화: 이미지-텍스트 정합성 (Semantic Match)

```
기존 (v0.1): 시각적 일치만 검사
- 이미지에 있는 것이 텍스트에도 언급되는가?

신규 (v0.2): 시각적 일치 + 의미적 일치(semantic match) 포함
- 캡션이 "먹어도 돼요"인데 이미지가 "급여 금지" → FAIL (0점)
- 캡션 톤과 이미지 분위기 불일치 → 감점 (-20점)
- 안전 정보 불일치 (캡션 vs 이미지 텍스트) → FAIL (0점)

검사 항목:
1. 캡션 안전 판정 ↔ 이미지 내 안전 판정 일치
2. 캡션 톤 ↔ 이미지 분위기 일치
3. 캡션 주장 ↔ 이미지 시각적 증거 일치
```

### 출력 형식

```json
{
  "agent": "B",
  "task": "품질 판단",
  "scores": {
    "accuracy": 0-100,
    "tone": 0-100,
    "format": 0-100,
    "coherence": 0-100,
    "policy": "PASS/FAIL"
  },
  "average": 0-100,
  "failure_points": ["point1", "point2", "point3"],
  "elapsed_time": "Xm Xs",
  "result": "PASS/FAIL"
}
```

---

## Agent C: 자동화 판단 에이전트

| 항목 | 내용 |
|------|------|
| **단일 목표** | "이 콘텐츠가 사람 손 없이 게시 가능한가?" 판정 |
| **성공 기준** | PASS/FAIL 명확 판정 + 사람 개입 지점 0~3개 명시 |
| **금지 사항** | 콘텐츠 수정, 품질 판단 |
| **판단하지 않는 것** | "이게 좋은 콘텐츠인가?" (Agent B 담당) |
| **FAIL 조건** | 사람 개입 지점 4개 이상 |

### 출력 형식

```json
{
  "agent": "C",
  "task": "자동화 판정",
  "auto_publishable": true/false,
  "human_intervention_points": ["point1", "point2"],
  "intervention_count": 0-3,
  "failure_points": ["point1", "point2", "point3"],
  "elapsed_time": "Xm Xs",
  "result": "PASS/FAIL"
}
```

---

## Agent D: 실패 예측 에이전트

| 항목 | 내용 |
|------|------|
| **단일 목표** | 게시 전 Red Flag 사전 감지 |
| **성공 기준** | 위험 항목 0~5개 + 위험도 점수 출력 |
| **금지 사항** | 콘텐츠 수정, PASS/FAIL 판정 |
| **판단하지 않는 것** | "이걸 고칠 수 있는가?" (Agent A 재시도) |
| **FAIL 조건** | 위험 항목 감지 불가 |

### 체크 항목 (5개)

| # | 항목 | 설명 |
|---|------|------|
| 1 | 독성 음식 안전 표기 | DANGER 음식 경고 누락 |
| 2 | 중복 주제 | 기게시 확인 |
| 3 | 이미지 내 텍스트 가독성 | 글자 잘림, 대비 부족 |
| 4 | 해시태그 정책 위반 | 금지 태그, 개수 초과 |
| 5 | AI 생성 표기 누락 | 필수 문구 확인 |

### 출력 형식

```json
{
  "agent": "D",
  "task": "실패 예측",
  "red_flags": [
    {"item": "항목명", "severity": "HIGH/MEDIUM/LOW", "detail": "설명"}
  ],
  "red_flag_count": 0-5,
  "risk_score": 0-100,
  "failure_points": ["point1", "point2", "point3"],
  "elapsed_time": "Xm Xs",
  "result": "PASS/FAIL"
}
```

---

## Agent E: 비용/재사용성 에이전트

| 항목 | 내용 |
|------|------|
| **단일 목표** | API 비용 추정 + 다른 프로젝트 재사용 가능성 평가 |
| **성공 기준** | 비용 수치 출력 + 재사용성 점수 (0~100) |
| **금지 사항** | 콘텐츠/품질 판단 |
| **판단하지 않는 것** | 콘텐츠 내용 |
| **FAIL 조건** | 비용 추정 불가 |

### 출력 형식

```json
{
  "agent": "E",
  "task": "비용/재사용성",
  "cost": {
    "image_api": "$X.XX",
    "text_api": "$X.XX",
    "total": "$X.XX"
  },
  "daily_limit": "$3.00",
  "within_budget": true/false,
  "reusability_score": 0-100,
  "reusable_components": ["component1", "component2"],
  "failure_points": ["point1", "point2", "point3"],
  "elapsed_time": "Xm Xs",
  "result": "PASS/FAIL"
}
```

---

## 합의 노드 판정 규칙

### Phase 1~2 (초기) 자동 게시 조건

| Agent | 조건 |
|-------|------|
| B | 평균 70점+ / 전항목 60점+ |
| C | PASS + 사람 개입 ≤ 1개 |
| D | Red Flag ≤ 1개 (RF1-TAGGED) |
| E | 비용 일일 상한 이내 |

### Phase 3+ (정규) 자동 게시 조건

| Agent | 조건 |
|-------|------|
| B | 평균 80점+ / 전항목 70점+ |
| C | PASS + 사람 개입 0개 |
| D | Red Flag 0개 |
| E | 비용 일일 상한 이내 |

### 판정 흐름

```
ALL PASS → 자동 게시
1개 FAIL → Agent A 재시도 (1회)
2개+ FAIL → 자동 중단 + PD님 알림
Agent D Red Flag 2개+ → 즉시 중단
```

---

**마지막 업데이트:** 2026-01-31 (Day 9)
**버전:** v0.4

---

## 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|----------|
| v0.1 | Day 1 | 초기 버전 - 5 Agent 체계 정의 |
| v0.2 | Day 5 | Agent B 의미 정합성(semantic match) 강화 |
| v0.3 | Day 7 | 캡션-안전분류 제약 로직 추가 (F2 재발 방지) |
| v0.3.1 | Day 8 | 질문=FAIL 규칙 추가 (Phase 2 진입) |
| v0.4 | Day 9 | AUTO_PUBLISH 등급화 (L1/L2/L3) 추가
