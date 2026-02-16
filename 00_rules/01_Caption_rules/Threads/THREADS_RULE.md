# 쓰레드 캡션 규칙

## 버전: 1.1
## 최종 수정: 2026-02-16
## 승인: PD 승인 대기
## 변경: v1.0 → v1.1 이미지 1장 → 4장 (인스타 재사용)

---

## 목적

Threads 플랫폼 전용 숏폼 캡션 규칙을 정의한다.

---

## 플랫폼 특성

| 항목 | 쓰레드 | 인스타 (비교) |
|------|--------|-------------|
| 글자 제한 | 500자 | 2,200자 |
| 핵심 | 텍스트 훅 | 이미지 중심 |
| 알고리즘 | 추천 피드 (비팔로워 노출 높음) | 팔로워 + 추천 |
| 언어 순서 | **영어 먼저, 한국어 서브** | 한국어 먼저, 영어 아래 |
| 이미지 | 4장 (인스타 이미지 재사용) | 캐러셀 최대 10장 |
| 해시태그 | 2~3개 (적을수록 좋음) | 15개 |

---

## 공통 규칙

### 1. 언어 순서

```
영어 (메인) → 한국어 (서브)
```

쓰레드 추천 알고리즘은 글로벌 유저에게 노출. 영어가 도달률에 직접 영향.
한국어는 국내 팔로워 유지 + 계정 정체성 역할.

### 2. 캡션 구조 (500자 이내)

```
[1] 영문 후킹 — 스크롤 멈추는 첫 줄 (필수)
[2] 핵심 정보 — 결론 + 이유 2~3줄 (영문)
[3] 한국어 전환 — 햇살이 에피소드 1~2줄
[4] CTA + 해시태그 — 2~3개
```

### 3. 후킹 원칙

- **첫 줄이 전부.** 펼치기(See more) 전에 보이는 영역에서 승부
- 질문형 or 도발형 or 충격형 — 무관심이 최대 적
- 이모지는 첫 줄에 1개만 (시선 유도용)
- 문장 끝에 마침표 생략 가능 (캐주얼 톤)

### 4. 해시태그 규칙

- 총 2~3개 (쓰레드는 적을수록 자연스러움)
- 필수: #CanMyDogEatThis
- 선택: 음식별 태그 1개 + #DogFoodSafety or #DogMomLife

### 5. 이미지

- **4장 첨부** — 인스타 캐러셀 이미지 그대로 재사용 (추가 제작 비용 0)
- 텍스트 오버레이 없음 (01_Cover 포함, 쓰레드는 전체 오버레이 미적용)

| 순서 | 파일 | 역할 | 스크롤 스톱 효과 |
|------|------|------|-----------------|
| 1 | 01_Cover | 햇살이 + 음식 | 감정 트리거 ("귀엽다") |
| 2 | 02_Food | 음식 클로즈업 | 호기심 트리거 ("이거 뭐지?") |
| 3 | 03_DogWithFood | 준비 장면 | 동질감 트리거 ("나도 이러는데") |
| 4 | 09_CTA | 햇살이 실사 | 전환 트리거 ("팔로우해야지") |

**참고:** 인스타와 달리 쓰레드 커버에는 텍스트 오버레이를 적용하지 않는다.
인스타 커버 오버레이는 피드 썸네일에서 음식 식별 목적이나,
쓰레드는 텍스트 훅이 그 역할을 대체하므로 이미지 원본을 사용한다.

---

## 안전도별 후킹 패턴

### ✅ SAFE — "너도 검색해봤지?" (동질감)

**감정:** 안심 + 공감 + "나만 그런 게 아니었구나"
**톤:** 친근, 가벼움, 공유하고 싶은

후킹 패턴:
```
A. 공감형
   "You've definitely googled this at 2am"
   "Every dog parent has searched this at least once"

B. 허락형
   "Yes, your dog can eat [food]. Here's how"
   "Good news — [food] is safe for dogs"

C. 반려견 시점
   "My dog heard me slicing [food] from two rooms away"
   "The way my dog stares at me when I eat [food]..."
```

### 🟡 CAUTION — "안전한 줄 알았지?" (의외성)

**감정:** 반전 + "몰랐네" + 알려주고 싶은
**톤:** 약간의 긴장, 하지만 해결책 제시

후킹 패턴:
```
A. 반전형
   "[Food] is safe for dogs — but there's a catch"
   "You can feed your dog [food]. But most people do it wrong"

B. 조건형
   "Safe? Yes. But only if you follow these rules"
   "[Food] won't hurt your dog. The amount might"

C. 경고+해결형
   "Stop feeding your dog [food] like this"
   "The #1 mistake dog parents make with [food]"
```

### 🔴 DANGER — "이거 모르면 진짜 위험해" (경고)

**감정:** 긴장감 + 보호 본능 + 즉시 저장
**톤:** 긴급, 직접적, 부드러운 경고

후킹 패턴:
```
A. 경고형
   "🚨 [Food] can send your dog to the ER"
   "Most people don't know [food] is dangerous for dogs"

B. 숫자형
   "Just [N] [food] seeds can poison a small dog"
   "[Food] has a hidden toxin 90% of dog owners don't know about"

C. 행동 유도형
   "If your dog ate [food], read this right now"
   "Save this before your dog gets into [food]"
```

### ⛔ FORBIDDEN — "이거 주면 죽을 수도 있어" (충격)

**감정:** 충격 + 공유 의무감 + "당장 알려야 해"
**톤:** 단호, 직접적, 비난 없이

후킹 패턴:
```
A. 충격형
   "🚫 [Food] can kill your dog. No, not just 'make them sick.' Kill."
   "There is NO safe amount of [food] for dogs. Zero."

B. 숨겨진 위험형
   "[Food] is hiding in your kitchen right now"
   "You're probably feeding your dog [food] without knowing it"

C. 비난 없는 경고형
   "I didn't know this either — and I've had dogs for 11 years"
   "Nobody told me [food] was this dangerous"
```

---

## 골든 샘플 4종

---

### ✅ SAFE 골든 샘플 — 사과 (Apple)

```
You've definitely googled "can my dog eat apples" at least once 🍎

Yes — apples are safe for dogs.
→ Rich in fiber, vitamin C, low calorie
→ Remove seeds & core (contain cyanide)
→ Cut into small pieces, skin OK if washed

Serving: small dogs 15-20g, medium 30-40g, large 50-70g

우리 햇살이는 사과 깎는 소리에 어디서든 달려와요 🐾

#CanMyDogEatThis #ApplesForDogs
```

---

### 🟡 CAUTION 골든 샘플 — 단팥빵 (Red Bean Bread)

```
Red bean bread is safe for dogs — but there's a catch 🍞

🟡 High sugar + wheat gluten = digestive stress
→ Bread part only, tiny amounts
→ Max once a week, thumbnail-sized piece
→ No choco or cream varieties
→ Not for diabetic or overweight dogs

우리 햇살이는 봉지 바스락 소리만 들어도 귀가 쫑긋.
하지만 한 입이 최대야 🐾

#CanMyDogEatThis #DogFoodSafety
```

---

### 🔴 DANGER 골든 샘플 — 체리 (Cherry)

```
🚨 Most people don't know cherries are dangerous for dogs

The flesh? Technically OK in tiny amounts.
The seeds, stems, leaves? Contain cyanide.

→ Small dogs: even 1-2 pits can be fatal
→ Swallowed pit = intestinal blockage risk
→ Symptoms: breathing difficulty, bright red gums, vomiting
→ If your dog ate cherry pits → vet IMMEDIATELY

Safe alternative: blueberries 🫐

햇살이가 아무리 간절한 눈빛을 보내도, 이건 엄마가 지켜야 할 선이에요 🐾

#CanMyDogEatThis #DogSafety
```

---

### ⛔ FORBIDDEN 골든 샘플 — 양파 (Onion)

```
🚫 Onions can kill your dog. Not "make them sick." Kill.

There is NO safe amount. Raw, cooked, powdered — all toxic.

→ Destroys red blood cells (thiosulfate)
→ 5g per 1kg body weight = fatal
→ Symptoms appear 1-3 DAYS later
→ Hidden in: broth, sauces, seasoning, baby food
→ If your dog ate ANY amount → vet NOW

11년째 키우면서 양파만큼은 철저하게 관리해요.
몰랐다면 괜찮아요. 지금 알았으니까요 🐾

#CanMyDogEatThis #ToxicFoodForDogs
```

---

## 안전도별 구조 차이 요약

| 항목 | SAFE | CAUTION | DANGER | FORBIDDEN |
|------|------|---------|--------|-----------|
| 첫 줄 톤 | 공감/가벼움 | 반전/의외성 | 경고/긴장 | 충격/단호 |
| 이모지 위치 | 첫 줄 끝 | 첫 줄 끝 | 첫 줄 앞 🚨 | 첫 줄 앞 🚫 |
| 급여량 | ✅ 포함 | ✅ 포함 (제한 강조) | ❌ 없음 (대안 제시) | ❌ 없음 |
| 증상/응급 | ❌ 없음 | ❌ 없음 | ✅ 포함 | ✅ 포함 (상세) |
| 대안 식품 | ❌ 없음 | ❌ 없음 | ✅ 제시 | ❌ 없음 |
| 숨은 위험 | ❌ 없음 | ❌ 없음 | ❌ 없음 | ✅ 포함 |
| 한국어 비중 | 에피소드 1~2줄 | 에피소드 1~2줄 | 에피소드 1~2줄 | 에피소드 1~2줄 + 후킹 |
| CTA | 없음 (자연스러운 공유 유도) | 없음 | Save this | Share this |

---

## Validator 체크리스트

```
□ 500자 이내
□ 첫 줄 = 영문 후킹 (스크롤 스톱)
□ 영어 메인, 한국어 서브
□ 햇살이 에피소드 포함 (한국어)
□ 해시태그 2~3개
□ #CanMyDogEatThis 필수
□ 안전도별 이모지 위치 준수
□ 이미지 4장 첨부 (01_Cover + 02_Food + 03_DogWithFood + 09_CTA)
□ 텍스트 오버레이 없음 (전체)
□ 안전도별 구조 차이 준수
```

**1개라도 FAIL → 재작성**

---

## 인스타 연동 전략

### 크로스포스팅 원칙
```
인스타 이미지 4장 (01, 02, 03, 09) → 쓰레드 그대로 재사용
캡션만 숏폼으로 변환 (500자 이내)
추가 이미지 제작 비용 = 0
```

### 쓰레드 → 인스타 유입 흐름
```
쓰레드 (텍스트 훅으로 관심 유발)
  ↓ "Full guide on my IG 👆"
인스타 (상세 캡션 + 캐러셀로 정보 전달)
  ↓ "Blog link in bio"
블로그 (SEO + 상세 정보)
```

쓰레드 캡션 마지막에 인스타 유도 문구 추가 가능 (선택):
- "Full breakdown on my Instagram → @sunshinedogfood"
- 단, 매 포스트마다 넣으면 스팸 느낌 → 3회 중 1회 정도

---

**문서 버전:** v1.1
**승인:** PD 승인 대기
