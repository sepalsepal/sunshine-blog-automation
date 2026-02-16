# 안전도별 슬라이드 네이밍 규칙

**버전:** 1.0
**승인일:** 2026-02-14
**승인자:** PD
**성격:** 블로그 슬라이드 03~07 안전도별 네이밍 강제 (레드2 리스크 B 대응)

---

## 1. 슬라이드 네이밍 매트릭스

### 1.1 SAFE 안전도

| 슬라이드 | 파일명 | 내용 |
|----------|--------|------|
| 03 | `{Food}_Blog_03_Nutrition.png` | 영양 성분 정보 |
| 04 | `{Food}_Blog_04_Feeding.png` | 급여 방법 |
| 05 | `{Food}_Blog_05_Amount.png` | 급여량 (4단계) |
| 06 | `{Food}_Blog_06_Caution.png` | 주의사항 |
| 07 | `{Food}_Blog_07_Cooking.png` | 조리 방법 |

**특징:** 긍정적 정보 중심, 급여량/조리법 포함

---

### 1.2 CAUTION 안전도

| 슬라이드 | 파일명 | 내용 |
|----------|--------|------|
| 03 | `{Food}_Blog_03_Nutrition.png` | 영양 성분 정보 |
| 04 | `{Food}_Blog_04_Feeding.png` | 급여 방법 (조건 강조) |
| 05 | `{Food}_Blog_05_Amount.png` | 급여량 (4단계, 제한 강조) |
| 06 | `{Food}_Blog_06_Caution.png` | 주의사항 (강조) |
| 07 | `{Food}_Blog_07_Cooking.png` | 안전한 조리 방법 |

**특징:** SAFE와 동일 구조, 내용에서 조건/주의 강조

---

### 1.3 DANGER 안전도

| 슬라이드 | 파일명 | 내용 |
|----------|--------|------|
| 03 | `{Food}_Blog_03_Nutrition.png` | 영양 성분 (위험 성분 강조) |
| 04 | `{Food}_Blog_04_Risk.png` | 위험 요소 |
| 05 | `{Food}_Blog_05_Symptoms.png` | 섭취 시 증상 |
| 06 | `{Food}_Blog_06_Emergency.png` | 응급 대처 |
| 07 | `{Food}_Blog_07_Alternative.png` | 대체 간식 |

**특징:** Feeding→Risk, Amount→Symptoms, Caution→Emergency, Cooking→Alternative

---

### 1.4 FORBIDDEN 안전도

| 슬라이드 | 파일명 | 내용 |
|----------|--------|------|
| 03 | `{Food}_Blog_03_Toxicity.png` | 독성 성분 |
| 04 | `{Food}_Blog_04_Symptoms.png` | 섭취 시 증상 |
| 05 | `{Food}_Blog_05_Emergency.png` | 응급 대처 |
| 06 | `{Food}_Blog_06_Alternative.png` | 대체 간식 |
| 07 | `{Food}_Blog_07_Warning.png` | 경고/주의 |

**특징:** Nutrition→Toxicity, 급여량/조리법 없음 (하드블록)

---

## 2. 슬라이드 내용별 차이

### 2.1 03번 슬라이드 (정보 유형)

| 안전도 | 파일명 | 내용 |
|--------|--------|------|
| SAFE | `03_Nutrition` | 영양소, 효능, 긍정적 정보 |
| CAUTION | `03_Nutrition` | 영양소 + 조건부 효능 |
| DANGER | `03_Nutrition` | 영양소 + 위험 성분 강조 |
| FORBIDDEN | `03_Toxicity` | 독성 성분, 위험 메커니즘 |

### 2.2 04번 슬라이드 (급여/위험)

| 안전도 | 파일명 | 내용 |
|--------|--------|------|
| SAFE | `04_Feeding` | 급여 방법 (DO/DON'T) |
| CAUTION | `04_Feeding` | 조건부 급여 방법 |
| DANGER | `04_Risk` | 위험 요소 목록 |
| FORBIDDEN | `04_Symptoms` | 섭취 시 증상 |

### 2.3 05번 슬라이드 (급여량/증상)

| 안전도 | 파일명 | 내용 |
|--------|--------|------|
| SAFE | `05_Amount` | 급여량 4단계 |
| CAUTION | `05_Amount` | 급여량 4단계 (제한) |
| DANGER | `05_Symptoms` | 섭취 시 증상 |
| FORBIDDEN | `05_Emergency` | 응급 대처 |

### 2.4 06번 슬라이드 (주의/응급)

| 안전도 | 파일명 | 내용 |
|--------|--------|------|
| SAFE | `06_Caution` | 일반 주의사항 |
| CAUTION | `06_Caution` | 강화된 주의사항 |
| DANGER | `06_Emergency` | 응급 대처 |
| FORBIDDEN | `06_Alternative` | 대체 간식 |

### 2.5 07번 슬라이드 (조리/대체/경고)

| 안전도 | 파일명 | 내용 |
|--------|--------|------|
| SAFE | `07_Cooking` | 조리 방법 |
| CAUTION | `07_Cooking` | 안전한 조리 방법 |
| DANGER | `07_Alternative` | 대체 간식 |
| FORBIDDEN | `07_Warning` | 최종 경고 |

---

## 3. Validator 검증

### 3.1 파일명 검증 코드

```python
SLIDE_NAMES = {
    "SAFE": ["Nutrition", "Feeding", "Amount", "Caution", "Cooking"],
    "CAUTION": ["Nutrition", "Feeding", "Amount", "Caution", "Cooking"],
    "DANGER": ["Nutrition", "Risk", "Symptoms", "Emergency", "Alternative"],
    "FORBIDDEN": ["Toxicity", "Symptoms", "Emergency", "Alternative", "Warning"]
}

def validate_slide_naming(filename, safety):
    """슬라이드 파일명 검증"""
    expected_names = SLIDE_NAMES.get(safety, [])

    for i, name in enumerate(expected_names, start=3):
        expected = f"_Blog_{i:02d}_{name}.png"
        if expected in filename:
            return True, i, name

    return False, None, None
```

### 3.2 FAIL 조건

```
- SAFE/CAUTION 음식에 Risk, Symptoms, Emergency, Toxicity, Warning 사용 → FAIL
- DANGER/FORBIDDEN 음식에 Amount, Cooking 사용 → FAIL
- FORBIDDEN 음식에 Feeding 사용 → FAIL (하드블록 위반)
```

### 3.3 자동 수정

```
FAIL 시:
1. 기존 파일 _backup 이동
2. 올바른 네이밍으로 재생성
3. Stage 1 재검증
```

---

## 4. 인포그래픽 디자인 차이

### 4.1 색상 테마

| 안전도 | 헤더 색상 | 배경 색상 |
|--------|----------|----------|
| SAFE | 민트 (#A8E6CF) | 크림 (#FFF8E7) |
| CAUTION | 노랑 (#FFD93D) | 연노랑 (#FFFDE7) |
| DANGER | 빨강 (#FF6B6B) | 연빨강 (#FFEBEE) |
| FORBIDDEN | 진빨강 (#FF5252) | 연빨강 (#FFCDD2) |

### 4.2 아이콘/뱃지

| 안전도 | 뱃지 | 아이콘 |
|--------|------|--------|
| SAFE | 🟢 SAFE | ✅ 초록 체크 |
| CAUTION | 🟡 CAUTION | ⚠️ 노랑 경고 |
| DANGER | 🔴 DANGER | ❌ 빨강 금지 |
| FORBIDDEN | ⛔ FORBIDDEN | 🚨 응급 |

---

## 5. 예시

### 5.1 호박 (SAFE)

```
contents/001_Pumpkin/02_Blog/
├── Pumpkin_Blog_03_Nutrition.png
├── Pumpkin_Blog_04_Feeding.png
├── Pumpkin_Blog_05_Amount.png
├── Pumpkin_Blog_06_Caution.png
└── Pumpkin_Blog_07_Cooking.png
```

### 5.2 포도 (FORBIDDEN)

```
contents/052_Grape/02_Blog/
├── Grape_Blog_03_Toxicity.png
├── Grape_Blog_04_Symptoms.png
├── Grape_Blog_05_Emergency.png
├── Grape_Blog_06_Alternative.png
└── Grape_Blog_07_Warning.png
```

---

## 변경 이력

| 버전 | 날짜 | 변경 내용 | 승인자 |
|------|------|----------|--------|
| 1.0 | 2026-02-14 | 최초 작성 (레드2 리스크 B 대응) | PD |
