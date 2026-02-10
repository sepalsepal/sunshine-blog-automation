# Project Sunshine 표지 이미지 제작 프롬프트 가이드

> **버전:** 2.0 (하이브리드)
> **작성일:** 2026-01-29
> **Owner:** PD
> **Review Cycle:** 분기 1회

---

## 1. 사용 방법

**맨 윗줄의 음식/음료 이름만 변경**하면 됩니다. 나머지는 AI가 자동으로 다양하게 생성합니다.

```
예시: CHERRY → MANGO → BANANA → KITKAT
```

**제작 도구:** Higgsfield + 레퍼런스 이미지 첨부

---

## 2. 최종 프롬프트

```
CHERRY

High-quality photograph. A senior 11-year-old Golden Retriever female named 'Haetsal', with a significantly white muzzle and face, golden fur, black nose and eyes, smiling brightly looking at the item above on a dining table.

CONTAINER RULE:
- Fresh Food/Fruit/Vegetable → dog bowl from pet brands (Le Creuset Pet, Diggs, MiaCara, Cloud7, Fable Pets, PETKIT, HARIO WAN, Waggo, Harry Barker, Messy Mutts, Kong, Outward Hound, PetRageous, Loving Pets, Frisco, 바잇미, 페슬러, 브리더랩, 뽀시래기, 아르르)
- Beverage → iconic container or cup from premium brands (Riedel, Baccarat, Zwiesel, Duralex, Le Creuset, Iittala, Hasami, Kinto, Acme, Loveramics, Fellow, Wedgwood, Noritake, Bodum, Hario)
- Branded drink (Sprite, Coca-Cola, etc.) → original brand can/bottle
- Packaged snack/food (KitKat, Oreo, Pepero, etc.) → original brand packaging clearly visible, no plate or bowl
- Dog treats/food (Orijen, Acana, Ziwi Peak, etc.) → original brand packaging clearly visible, no bowl

Background is a trendy 2026 Korean apartment living room with warm indirect lighting. Ceiling fan with 3 blades. Indoor plants: monstera, bird of paradise, peace lily, and areca palm. Floor standing lamp. Mr. Maria Brown lamp placed by the window.

VARIATION: Randomly vary time of day, lighting mood, bowl brand selection, dog's expression, slight head angle, camera angle (front, slightly left, slightly right), dog's gaze (at camera, at food, at window), weather outside window (sunny, cloudy, rainy, snowy), table style (white marble, natural oak, walnut, white lacquer, terrazzo, concrete, glass with gold legs, Scandinavian birch, black marble, ceramic tile top), season hints, and occasionally add a cute bandana or scarf on the dog each generation.

Background slightly defocused, focus on dog and item.

(Layout Constraint: Top of dog's head at 40% from top. Container bottom at 90% from top. Item realistically sized.)
```

---

## 3. CONTAINER RULE (용기 규칙)

| 카테고리 | 용기 | 예시 |
|----------|------|------|
| 신선 식품/과일/채소 | 반려견 식기 브랜드 | 사과, 바나나, 당근, 브로콜리 |
| 음료 | 해당 음료 대표 용기 | 커피→컵, 바나나우유→노란병 |
| 브랜드 음료 | 원래 브랜드 캔/병 | 스프라이트, 코카콜라 |
| 포장 과자/식품 | 원래 포장 그대로 | 킷캣, 오레오, 빼빼로 |
| 반려견 간식/사료 | 원래 포장 그대로 | 오리젠, 아카나, 지위픽 |

---

## 4. 반려견 식기 브랜드 (20개)

| 등급 | 브랜드 |
|------|--------|
| **프리미엄** | Le Creuset Pet, Diggs, MiaCara, Cloud7, Fable Pets |
| **중고가** | PETKIT, HARIO WAN, Waggo, Harry Barker, Messy Mutts |
| **인기** | Kong, Outward Hound, PetRageous, Loving Pets, Frisco |
| **한국** | 바잇미, 페슬러, 브리더랩, 뽀시래기, 아르르 |

---

## 5. VARIATION 요소 (자동 변화)

| 요소 | 변화 범위 |
|------|-----------|
| 시간대/조명 | 아침 골든아워, 한낮 자연광, 오후, 저녁 램프, 밤 실내조명 |
| 강아지 표정 | 혀 내밀기, 입 다문 미소, 호기심 표정 |
| 머리 각도 | 정면, 약간 왼쪽 기울임, 약간 오른쪽 기울임 |
| 카메라 앵글 | 정면, 약간 왼쪽에서, 약간 오른쪽에서 |
| 시선 | 카메라 응시, 음식 바라보기, 창밖 보기 |
| 창밖 날씨 | 맑음, 흐림, 비, 눈 |
| 테이블 스타일 | 흰 대리석, 오크, 월넛, 테라조, 콘크리트, 유리, 블랙 대리석 등 10종 |
| 계절 힌트 | 봄꽃, 여름 녹음, 가을 단풍, 겨울 눈 |
| 액세서리 | 가끔 반다나/스카프 착용 |

---

## 6. 고정 배경 요소

| 카테고리 | 요소 |
|----------|------|
| 천장 | 3날개 팬 |
| 식물 | 몬스테라, 여인초, 스파티필름, 아레카 야자 |
| 조명 | 스탠드 램프, Mr. Maria Brown 램프 (창가) |

---

## 7. PPL 전략 요약

| 영역 | PPL 가치 | 비고 |
|------|:--------:|------|
| 반려견 식기 | ★★★★★ | 브랜드 선명하게 노출 (Le Creuset Pet 등) |
| 반려견 간식/사료 | ★★★★★ | 원래 포장 그대로 노출 |
| 액세서리 (반다나) | ★★★ | 가끔 노출로 자연스러움 유지 |
| 배경 소품 | ★ | 디포커스로 브랜드 인식 어려움 |

---

## 8. 레이아웃 규격

```
┌─────────────────────────────┐
│                             │ ← 상단 40% (여백)
│        [텍스트 공간]         │
├─────────────────────────────┤
│                             │
│       🐕 햇살이 머리         │ ← 40% 위치
│                             │
│                             │
│       🥗 음식/용기           │ ← 90% 위치 (하단)
└─────────────────────────────┘
```

### 기본 규칙 vs 예외 케이스

| 구분 | 강아지 머리 | 용기 하단 | 적용 상황 |
|------|:----------:|:--------:|----------|
| **기본 규칙** | 40% | 90% | 일반 표지 |
| 클로즈업 컷 | 50% | 95% | 음식 강조 필요 시 |
| 세로 콘텐츠 | 35% | 85% | 스토리/릴스용 |
| 브랜드 PPL | 45% | 88% | 로고 가독성 확보 |

> **참고:** 위 규칙은 기본 가이드이며, 콘텐츠 목적에 따라 ±5% 범위 내 조정 가능.
> 예외 적용 시 PD 승인 필요.

---

## 9. PPL 브랜드 삽입 SAFE ZONE (권장)

### 로고/제품 가시성 기준

| 항목 | 최소 | 권장 | 비고 |
|------|:----:|:----:|------|
| 로고 크기 | 50px | 80px+ | 브랜드 인식 가능 |
| 제품 노출 비율 | 15% | 20~25% | 프레임 대비 |
| 햇살이 시선 방향 | - | 제품 쪽 70%+ | 자연스러운 노출 |

### SAFE ZONE 위치

```
┌─────────────────────────────┐
│  ⚠️ 텍스트 영역 (PPL 불가)   │
├─────────────────────────────┤
│         ┌─────┐             │
│         │LOGO │ ← SAFE ZONE │
│    🐕   └─────┘  (우측 하단) │
│                             │
│       🥗 [브랜드 제품]       │
└─────────────────────────────┘
```

---

*© 2026 Project Sunshine | @sunshinedogfood*
