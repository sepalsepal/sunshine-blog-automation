# SAFETY_MATRIX v1.0

**버전:** 1.0
**승인일:** 2026-02-14
**승인자:** PD
**성격:** SSOT (Single Source of Truth) - 안전도 정의 유일 기준

---

## 1. 안전도 정의

| 등급 | 코드 | 색상 | 의미 |
|------|------|------|------|
| SAFE | 🟢 | #4CAF50 | 안전하게 급여 가능 |
| CAUTION | 🟡 | #FFD93D | 조건부 급여 가능 (조리/소량/주의 필요) |
| DANGER | 🔴 | #FF6B6B | 위험 - 소량만 가끔 또는 피하는 것이 좋음 |
| FORBIDDEN | ⛔ | #FF5252 | 절대 금지 - 독성 또는 치명적 위험 |

---

## 2. 안전도 판정 기준

### 2.1 SAFE (안전)

```
조건:
- 익혀도 생으로도 급여 가능
- 특별한 조건 없이 간식으로 적합
- 알려진 독성 성분 없음
- 소화 문제 보고 희박

예시: 호박, 당근, 사과(씨 제외), 블루베리
```

### 2.2 CAUTION (주의)

```
조건:
- 조리 필수 (생 급여 금지)
- 특정 부위 제거 필수 (씨, 껍질 등)
- 과다 급여 시 문제 가능
- 일부 개체에서 알레르기 가능

예시: 체리(씨 제거), 파인애플(껍질 제거), 브로콜리(소량)
```

### 2.3 DANGER (위험)

```
조건:
- 독성 성분 일부 포함
- 소량만 가끔 급여 가능
- 특정 품종/개체에 위험
- 과다 섭취 시 응급 상황 가능

예시: 양파 소량, 마늘 소량, 카페인 음료
```

### 2.4 FORBIDDEN (금지)

```
조건:
- 확인된 독성 물질 포함
- 소량도 위험
- 섭취 시 응급 처치 필요
- 치명적 결과 가능

예시: 포도, 건포도, 초콜릿, 자일리톨, 마카다미아
```

---

## 3. FORBIDDEN 특수 규칙

### 3.1 캡션 하드블록

```
FORBIDDEN 캡션에 다음 섹션 포함 금지:
❌ 급여량 (dosage)
❌ 급여 방법 (feeding_method)
❌ 조리법 (cooking)
❌ "줘도 돼요" 표현
❌ "괜찮아요" 표현
❌ "주셔도" 표현
```

### 3.2 FORBIDDEN 필수 포함

```
✅ "절대 금지" 또는 "절대 안 돼요"
✅ 독성 이유 설명
✅ 응급 대처 (동물병원)
✅ 위험량 명시 (해당 시)
```

### 3.3 슬라이드 구조 차이

| SAFE/CAUTION | DANGER | FORBIDDEN |
|--------------|--------|-----------|
| 03_Nutrition | 03_Nutrition | 03_Toxicity |
| 04_Feeding | 04_Risk | 04_Symptoms |
| 05_Amount | 05_Symptoms | 05_Emergency |
| 06_Caution | 06_Emergency | 06_Alternative |
| 07_Cooking | 07_Alternative | 07_Warning |

---

## 4. 안전도 분기 규칙

### 4.1 분기 판단 = 코드 (LLM 위임 금지)

```python
# 올바른 방식 (코드 분기)
if food_data["safety"] == "FORBIDDEN":
    template = "templates/forbidden.txt"
else:
    template = f"templates/{food_data['safety'].lower()}.txt"

# 금지된 방식 (LLM 판단)
# prompt = "이 음식이 안전한지 판단해서..."  ❌
```

### 4.2 SSOT = food_data.json

```
- 안전도는 food_data.json의 safety 필드가 유일 기준
- LLM이 안전도를 추론/변경하는 것 금지
- 안전도 변경 시 food_data.json 직접 수정 + PD 승인
```

---

## 5. 안전도 색상 적용

### 5.1 커버 뱃지

```
SAFE: 배경 #4CAF50, 텍스트 #FFFFFF
CAUTION: 배경 #FFD93D, 텍스트 #333333
DANGER: 배경 #FF6B6B, 텍스트 #FFFFFF
FORBIDDEN: 배경 #FF5252, 텍스트 #FFFFFF
```

### 5.2 인포그래픽 헤더

```
SAFE: 민트 그라데이션 (#A8E6CF → 투명)
CAUTION: 노랑 그라데이션 (#FFD93D → 투명)
DANGER: 빨강 그라데이션 (#FF6B6B → 투명)
FORBIDDEN: 진빨강 그라데이션 (#FF5252 → 투명)
```

---

## 6. Validator 안전도 검증

```
Stage 3 체크리스트:
□ food_data.safety ↔ 캡션 톤 일치
□ FORBIDDEN 금지어 포함 여부
□ FORBIDDEN 필수어 존재 여부
□ 안전도별 슬라이드 구조 일치
□ 색상 코드 정확성
```

---

## 변경 이력

| 버전 | 날짜 | 변경 내용 | 승인자 |
|------|------|----------|--------|
| 1.0 | 2026-02-14 | 최초 작성 | PD |
