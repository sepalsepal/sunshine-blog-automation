# 🎨 4장 캐러셀 이미지 제작 가이드

**작성일:** 2026-01-27  
**작성자:** 세준 PD / 김부장  
**수신:** 김차장 (Gemini - 이미지 프롬프트)  
**프로젝트:** Project Sunshine (@sunshinedogfood)

---

## 📋 개요

| 항목 | 내용 |
|------|------|
| 캐러셀 구성 | 4장 (표지 1장 + 본문 3장) |
| 캐릭터 | 햇살이 (11세 시니어 골든리트리버, 흰 주둥이) |
| 제작 도구 | Higgsfield (레퍼런스 이미지 필수 첨부) |
| 텍스트 | PPT 템플릿에서 별도 작업 (이미지에 텍스트 삽입 금지) |

---

## 🖼️ 슬라이드 1: 표지

### 레이아웃

```
┌─────────────────────────────────────┐
│  ██████ TEXT ZONE (상단 15%) ██████ │  ← 영문 타이틀 들어갈 자리
├─────────────────────────────────────┤
│                                     │
│                                     │
│      DOG IMAGE ZONE (중앙 55%)      │  ← 강아지 얼굴/상체
│      - 정면 응시                    │
│      - 밝은 미소                    │
│                                     │
├─────────────────────────────────────┤
│     FOOD IMAGE ZONE (하단 30%)      │  ← 그릇에 담긴 음식
│     - 예쁜 세라믹 그릇              │
│     - 대리석 테이블                 │
└─────────────────────────────────────┘
```

### 표지 프롬프트

```
High-quality photograph. A senior 11-year-old Golden Retriever female named 'Haetsal', with a significantly white muzzle and face, golden fur, black nose and eyes, smiling brightly looking at [음식명] in a pretty ceramic bowl on a dining table. Background is a trendy 2026 Korean apartment living room with warm yellow indirect lighting.

(Layout Constraint Checklist: 
- TEXT ZONE: Upper 15% of frame - soft blurred background only, no dog parts
- DOG IMAGE ZONE: Center 55% of frame - dog's face and upper body, looking at camera
- FOOD IMAGE ZONE: Lower 30% of frame - ceramic bowl with food on marble table)
```

### 완성 레퍼런스

![표지 레퍼런스](슬라이드1.jpeg)

- 텍스트 "ORANGE"가 강아지 얼굴을 가리지 않음
- 강아지가 정면을 보며 밝게 웃음
- 음식이 예쁜 그릇에 담겨 하단에 배치

---

## 🖼️ 슬라이드 2~4: 본문 (3장 동일 레이아웃)

### 레이아웃

```
┌─────────────────────────────────────┐
│                                     │
│                                     │
│      DOG IMAGE ZONE (상단 60%)      │  ← 강아지 얼굴/상체
│      - 음식 냄새 맡는 중            │
│      - 또는 먹는 중                 │
│                                     │
├─────────────────────────────────────┤
│     FOOD IMAGE ZONE (10%)           │  ← 접시에 담긴 음식
├─────────────────────────────────────┤
│  ██ MAIN TEXT ZONE (하단 20%) ██    │  ← 메인 텍스트
│  ██ SUB TEXT ZONE (하단 10%) ██     │  ← 서브 텍스트
└─────────────────────────────────────┘
```

### 본문 프롬프트

```
A warm, cinematic photograph of a senior golden retriever with white muzzle leaning forward to sniff/eat [음식명] from a small white ceramic plate.

(Layout Constraint Checklist:
- DOG IMAGE ZONE: Upper 60% of frame - dog's face and upper body
- FOOD IMAGE ZONE: Around 60-70% line - plate with food on rustic wooden table  
- TEXT ZONE: Lower 30% of frame - must be clear for text overlay)

Shallow depth of field, creamy bokeh background, cozy home kitchen atmosphere, warm color temperature, realistic fur texture.

Shot on full-frame camera, 50mm lens, f/1.8, natural light.

Negative: cluttered background, humans, hands, text, watermark
```

### 완성 레퍼런스

![본문 레퍼런스](슬라이드3.jpeg)

- 강아지가 음식 냄새를 맡거나 먹는 중
- 텍스트 "먹어도 돼요!" + "과육만 소량급여 OK"가 하단에 배치
- 텍스트가 강아지/음식을 가리지 않음

---

## 📐 4장 구성표

| 슬라이드 | 용도 | 이미지 분위기 | 텍스트 (PPT) |
|:--------:|------|--------------|-------------|
| 1 | 표지 | 밝은 미소, 음식 바라봄 | 영문 타이틀 (예: PEACH) |
| 2 | 급여법 | 음식 냄새 맡는 중 | 먹어도 돼요! + 서브 |
| 3 | 효능 | 행복하게 먹는 중 | 효능 메인 + 서브 |
| 4 | 주의 | 차분하게 앉아있음 | 주의사항 + 서브 |

---

## ✅ 체크리스트 (이미지 생성 후)

### 표지 체크

| # | 항목 | 확인 |
|---|------|:----:|
| 1 | 상단 15%에 강아지 얼굴이 침범하지 않는가? | ⬜ |
| 2 | 강아지가 정면을 보며 웃고 있는가? | ⬜ |
| 3 | 음식이 하단 30% 영역 내에 있는가? | ⬜ |
| 4 | 햇살이 특성 (흰 주둥이) 유지되었는가? | ⬜ |

### 본문 체크

| # | 항목 | 확인 |
|---|------|:----:|
| 1 | 하단 30%에 강아지/음식이 침범하지 않는가? | ⬜ |
| 2 | 강아지가 음식과 상호작용하고 있는가? | ⬜ |
| 3 | 따뜻한 톤이 유지되는가? | ⬜ |
| 4 | 4장 모두 일관된 분위기인가? | ⬜ |

---

## ⚠️ 절대 금지사항

1. **텍스트 영역 침범** - 표지 상단 15%, 본문 하단 30%는 비워둘 것
2. **이미지에 텍스트 삽입** - PPT에서 처리
3. **강아지 얼굴 가림** - 눈, 코, 입 모두 보여야 함
4. **레퍼런스 없이 생성** - Higgsfield에서 반드시 레퍼런스 첨부

---

## 🔄 제작 워크플로우

```
[1] 김차장: 주제별 프롬프트 4개 생성 (위 템플릿 활용)
     ↓
[2] PD님: Higgsfield에서 4장 생성 (레퍼런스 첨부)
     ↓
[3] 김부장: 레이아웃 검수 (체크리스트 확인)
     ↓
[4] PPT 템플릿: 텍스트 오버레이
     ↓
[5] PNG 내보내기 → 게시
```

---

## 📁 음식별 교체 예시

| 주제 | [음식명] 교체 |
|------|--------------|
| Peach | fresh peaches / peeled peach slices |
| Watermelon | fresh watermelon / watermelon cubes |
| Grape | fresh grapes / seedless grape halves |
| Broccoli | fresh broccoli / steamed broccoli florets |
| Banana | fresh bananas / sliced banana pieces |

---

**끝.**
