# Golden↔Production 파일 매핑표

**버전:** 1.0
**승인일:** 2026-02-14
**승인자:** PD
**성격:** 골든 샘플 → 실제 생산 파일 네이밍 규칙 (레드2 리스크 A 대응)

---

## 1. 캡션 템플릿 매핑

### 1.1 골든 샘플 경로
```
rules/01_Caption/{Platform}/{Safety}/Golden_{Platform}_{Safety}_Template.txt
```

### 1.2 생산 파일 경로
```
contents/{NNN}_{Food}/01_Insta&Thread/{Food}_{Safety}_Insta_Caption.txt
contents/{NNN}_{Food}/01_Insta&Thread/{Food}_{Safety}_Thread_Caption.txt
contents/{NNN}_{Food}/02_Blog/{Food}_{Safety}_Blog_Caption.txt
```

### 1.3 매핑 테이블

| 골든 샘플 | 생산 파일 | 변환 규칙 |
|----------|----------|----------|
| `Golden_Insta_Safe_Template.txt` | `{Food}_Safe_Insta_Caption.txt` | Platform 위치 이동 |
| `Golden_Insta_Caution_Template.txt` | `{Food}_Caution_Insta_Caption.txt` | Platform 위치 이동 |
| `Golden_Insta_Danger_Template.txt` | `{Food}_Danger_Insta_Caption.txt` | Platform 위치 이동 |
| `Golden_Insta_Forbidden_Template.txt` | `{Food}_Forbidden_Insta_Caption.txt` | Platform 위치 이동 |
| `Golden_Thread_Safe_Template.txt` | `{Food}_Safe_Thread_Caption.txt` | Platform 위치 이동 |
| `Golden_Thread_Caution_Template.txt` | `{Food}_Caution_Thread_Caption.txt` | Platform 위치 이동 |
| `Golden_Thread_Danger_Template.txt` | `{Food}_Danger_Thread_Caption.txt` | Platform 위치 이동 |
| `Golden_Thread_Forbidden_Template.txt` | `{Food}_Forbidden_Thread_Caption.txt` | Platform 위치 이동 |
| `Golden_Blog_Safe_Template.txt` | `{Food}_Safe_Blog_Caption.txt` | Platform 위치 이동 |
| `Golden_Blog_Caution_Template.txt` | `{Food}_Caution_Blog_Caption.txt` | Platform 위치 이동 |
| `Golden_Blog_Danger_Template.txt` | `{Food}_Danger_Blog_Caption.txt` | Platform 위치 이동 |
| `Golden_Blog_Forbidden_Template.txt` | `{Food}_Forbidden_Blog_Caption.txt` | Platform 위치 이동 |

### 1.4 네이밍 공식

```
골든: Golden_{Platform}_{Safety}_Template.txt
생산: {Food}_{Safety}_{Platform}_Caption.txt

변환:
- "Golden_" 제거
- "_Template" → "_Caption"
- {Food} 추가 (앞)
- Platform과 Safety 순서 교체
```

---

## 2. 이미지 파일 매핑

### 2.1 공통 이미지 (Common)

| 골든 샘플 | 생산 파일 | 위치 |
|----------|----------|------|
| `01_Cover/Golden_Cover_Sample.png` | `{Food}_Common_01_Cover.png` | 루트 |
| `02_Food/Golden_Food_Sample.png` | `{Food}_Common_02_Food.png` | 루트 |
| `03_DogWithFood/Golden_DogWithFood_Sample.png` | `{Food}_Insta_03_Dog.png` | 01_Insta&Thread/ |
| `08_HaetsalReal/Golden_HaetsalReal_Sample.png` | `{Food}_Common_08_HaetsalReal.png` | 루트 |

### 2.2 블로그 슬라이드 (안전도별)

**골든 샘플 경로:** `00_rules/02_Image_rules/Blog_04-07/{Safety}/`

```
Blog_04-07/
├── SAFE/           ← SAFE 안전도 골든 샘플
├── CAUTION/        ← CAUTION 안전도 골든 샘플
├── DANGER/         ← DANGER 안전도 골든 샘플
└── FORBIDDEN/      ← FORBIDDEN 안전도 골든 샘플
```

#### SAFE (안전)

| 골든 샘플 | 생산 파일 |
|----------|----------|
| `Blog_04-07/SAFE/Golden_Blog_Safe_03_Nutrition.png` | `{Food}_Blog_03_Nutrition.png` |
| `Blog_04-07/SAFE/Golden_Blog_Safe_04_Feeding.png` | `{Food}_Blog_04_Feeding.png` |
| `Blog_04-07/SAFE/Golden_Blog_Safe_05_Amount.png` | `{Food}_Blog_05_Amount.png` |
| `Blog_04-07/SAFE/Golden_Blog_Safe_06_Caution.png` | `{Food}_Blog_06_Caution.png` |
| `Blog_04-07/SAFE/Golden_Blog_Safe_07_Cooking.png` | `{Food}_Blog_07_Cooking.png` |

#### CAUTION (주의)

| 골든 샘플 | 생산 파일 |
|----------|----------|
| `Blog_04-07/CAUTION/Golden_Blog_CAUTION_03_Nutrition.png` | `{Food}_Blog_03_Nutrition.png` |
| `Blog_04-07/CAUTION/Golden_Blog_CAUTION_04_Feeding.png` | `{Food}_Blog_04_Feeding.png` |
| `Blog_04-07/CAUTION/Golden_Blog_CAUTION_05_Amount.png` | `{Food}_Blog_05_Amount.png` |
| `Blog_04-07/CAUTION/Golden_Blog_CAUTION_06_Caution.png` | `{Food}_Blog_06_Caution.png` |
| `Blog_04-07/CAUTION/Golden_Blog_CAUTION_07_Cooking.png` | `{Food}_Blog_07_Cooking.png` |

#### DANGER (위험)

| 골든 샘플 | 생산 파일 |
|----------|----------|
| `Blog_04-07/DANGER/Golden_Blog_DANGER_03_Nutrition.png` | `{Food}_Blog_03_Nutrition.png` |
| `Blog_04-07/DANGER/Golden_Blog_DANGER_04_Risk.png` | `{Food}_Blog_04_Risk.png` |
| `Blog_04-07/DANGER/Golden_Blog_DANGER_05_Symptoms.png` | `{Food}_Blog_05_Symptoms.png` |
| `Blog_04-07/DANGER/Golden_Blog_DANGER_06_Emergency.png` | `{Food}_Blog_06_Emergency.png` |
| `Blog_04-07/DANGER/Golden_Blog_DANGER_07_Alternative.png` | `{Food}_Blog_07_Alternative.png` |

#### FORBIDDEN (금지)

| 골든 샘플 | 생산 파일 |
|----------|----------|
| `Blog_04-07/FORBIDDEN/Golden_Blog_FORBIDDEN_03_Toxicity.png` | `{Food}_Blog_03_Toxicity.png` |
| `Blog_04-07/FORBIDDEN/Golden_Blog_FORBIDDEN_04_Symptoms.png` | `{Food}_Blog_04_Symptoms.png` |
| `Blog_04-07/FORBIDDEN/Golden_Blog_FORBIDDEN_05_Emergency.png` | `{Food}_Blog_05_Emergency.png` |
| `Blog_04-07/FORBIDDEN/Golden_Blog_FORBIDDEN_06_Alternative.png` | `{Food}_Blog_06_Alternative.png` |
| `Blog_04-07/FORBIDDEN/Golden_Blog_FORBIDDEN_07_Warning.png` | `{Food}_Blog_07_Warning.png` |

---

## 3. 변수 치환 규칙

### 3.1 {Food} 변수

```
소스: food_data.json의 english_name
형식: PascalCase
예시: Pumpkin, Carrot, Grape, Chocolate
```

### 3.2 {Safety} 변수

```
소스: food_data.json의 safety
값: Safe | Caution | Danger | Forbidden
형식: PascalCase (첫 글자 대문자)
```

### 3.3 {NNN} 변수

```
소스: food_data.json의 키 또는 폴더명
형식: 3자리 숫자 (001~175)
예시: 001, 052, 175
```

---

## 4. Validator 검증 규칙

### 4.1 파일명 검증

```python
def validate_production_filename(filename, food, safety, platform):
    """생산 파일명 검증"""
    expected_caption = f"{food}_{safety}_{platform}_Caption.txt"
    expected_cover = f"{food}_Common_01_Cover.png"
    expected_food = f"{food}_Common_02_Food.png"
    expected_haetsal = f"{food}_Common_08_HaetsalReal.png"

    # 슬라이드는 안전도별 매핑 테이블 참조
    ...
```

### 4.2 골든↔생산 불일치 시

```
Stage 1 FAIL → 파일명 규칙 위반
- 즉시 재생성
- 올바른 네이밍으로 저장
- 기존 파일 _backup 이동
```

---

## 5. 사용 예시

### 5.1 호박 (SAFE)

```
골든: Golden_Insta_Safe_Template.txt
생산: Pumpkin_Safe_Insta_Caption.txt

골든: Golden_Blog_Safe_03_Nutrition.png
생산: Pumpkin_Blog_03_Nutrition.png
```

### 5.2 포도 (FORBIDDEN)

```
골든: Golden_Insta_Forbidden_Template.txt
생산: Grape_Forbidden_Insta_Caption.txt

골든: Golden_Blog_Forbidden_03_Toxicity.png
생산: Grape_Blog_03_Toxicity.png
```

---

## 변경 이력

| 버전 | 날짜 | 변경 내용 | 승인자 |
|------|------|----------|--------|
| 1.0 | 2026-02-14 | 최초 작성 (레드2 리스크 A 대응) | PD |
