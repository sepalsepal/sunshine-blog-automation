# PROJECT SUNSHINE – RULES.md

**버전:** 3.7
**최종 업데이트:** 2026-02-11
**성격:** 헌법. 최상위 규칙. 이 문서에 없으면 존재하지 않는다.

---

## 1. 규칙 우선순위

```
RULES.md > BOOTSTRAP.md > SYNC.md > 개별 규칙 문서
```

충돌 시 상위 문서가 우선한다.

---

## 2. LOCKED 규칙 목록

### 2.1 BLOG_RENDER v2.0 🔒

| 항목 | 값 | 변경 |
|------|-----|------|
| 이미지 | 8장 고정 | ❌ 불가 |
| 글자수 | 1,800자 ±10% (1,620~1,980) | ❌ 불가 |
| H2 | 4개 이상 | ❌ 불가 |
| 키워드 | 5회 이상 | ❌ 불가 |
| 발행 | 주 2회 | 조정 가능 |

**허용 범위:**
- 본문 내부 확장 (FAQ, 비교표, 레시피, 출처)
- 글자수 범위 내 조정

#### 2.1.1 블로그 이미지 구성 규칙 🔒 (v2.0 신규)

| 순번 | 이미지 | 유형 | 필수 요소 |
|------|--------|------|----------|
| 1장 | 표지 | 표지(한글) | COVER_RULES 표지(한글) 준수 |
| 2장 | 음식 사진 | 실사/AI | 음식 클로즈업 |
| 3~7장 | 본문 인포그래픽 | C2 인포그래픽 | C2 v2.0 규칙 준수 |
| 8장 | 햇살이 마무리 | **실사 전용** | 햇살이 실사 사진만 허용 |

**⚠️ 8장 규칙:**
- 반드시 **실사 햇살이 사진** 사용
- AI 생성 이미지 ❌ 금지
- C2 인포그래픽 ❌ 금지
- 텍스트 오버레이 없는 순수 실사 사진

**위반 시:** 즉시 재제작. FAIL 판정.

---

### 2.2 COVER_RULES 표지(영어) v1.0 🔒 - 인스타그램용

| 항목 | 값 | 허용 오차 |
|------|-----|----------|
| Y 위치 | 194px | ±10px |
| 폰트 크기 | 114px | 고정 |
| 그라데이션 | 없음 | - |
| 그림자 | 4px, 알파 128 | - |
| 언어 | 영어 대문자 | - |

**Validator 항목 (PASS/FAIL):**
- [ ] Y 위치: 184~204px 범위 내
- [ ] 폰트: NotoSansCJK-Black 또는 Arial Black
- [ ] 폰트 크기: 114px
- [ ] 그림자: 4px 오프셋
- [ ] 그라데이션: 없음
- [ ] 텍스트 색상: #FFFFFF

**1개라도 FAIL → 즉시 삭제 + 재제작**

---

### 2.3 COVER_RULES 표지(한글) v1.0 🔒 - 블로그용

| 항목 | 값 | 허용 오차 |
|------|-----|----------|
| Y 위치 | 80px | ±10px |
| 폰트 크기 | 120px | 고정 |
| 그라데이션 | 상단 25%, 알파 80 | - |
| 그림자 | 2px, 알파 100 | - |
| 언어 | 한글 | - |

**Validator 항목 (PASS/FAIL):**
- [ ] Y 위치: 70~90px 범위 내
- [ ] 폰트: NotoSansCJK-Black
- [ ] 폰트 크기: 120px
- [ ] 그림자: 2px 오프셋, 알파 100
- [ ] 그라데이션: 상단 25%, 알파 80
- [ ] 텍스트 색상: #FFFFFF

**1개라도 FAIL → 즉시 삭제 + 재제작**

**제작 코드:** COVER_RULES_FULL.md 참조 (코드 변경 금지)

---

### 2.4 C2 인포그래픽 v2.0 🔒 - 블로그용 (v1.0→v2.0 업그레이드)

**골든 샘플 경로:** `contents/0_Golden sample/Blog/` (영양성분, 급여방법, 급여량, 주의사항, 조리방법)

#### 2.4.1 필수 디자인 요소

| 항목 | 값 | PASS/FAIL |
|------|-----|-----------|
| 해상도 | 1080x1080 | FAIL: 미달 시 |
| 상단 헤더 | 그라데이션 (민트→투명) | FAIL: 없으면 |
| 헤더 제목 | 볼드, 큰 폰트, 중앙 정렬 | FAIL: 없으면 |
| 헤더 부제목 | 작은 폰트, 제목 아래 | 선택 |
| 카드형 레이아웃 | 각 항목별 박스/카드 | FAIL: 단순 나열 시 |
| 번호 아이콘 | 컬러풀 원형 뱃지 | FAIL: 없으면 |
| 항목 제목 | 볼드 텍스트 | FAIL: 없으면 |
| 항목 설명 | 제목 아래 부연 설명 (회색/작은 폰트) | FAIL: 없으면 |
| 하단 보조 요소 | TIP 박스 / 주의사항 / 주석 중 1개 이상 | FAIL: 없으면 |
| 배경 기본색 | 크림/베이지 (#FFF8E7 계열) | 권고 |

#### 2.4.2 C2 폰트 규칙 🔒 (위치별 고정)

| 위치 | 폰트 | 크기 | 색상 | 비고 |
|------|------|------|------|------|
| 헤더 제목 | NotoSansCJK-Bold | 60px | 컬러 (민트/빨강 등 주제별) | 중앙 정렬 |
| 헤더 부제목 | NotoSansCJK-Regular | 24px | #666666 또는 흰색 | 제목 아래, 중앙 정렬 |
| 카드 제목 | NotoSansCJK-Bold | 36px | #333333 (진한 회색~검정) | 왼쪽 정렬 |
| 카드 설명 | NotoSansCJK-Regular | 22px | #888888 (회색) | 제목 아래, 왼쪽 정렬 |
| 수치/강조값 | NotoSansCJK-Bold | 44px | 컬러 (주황/초록 등) | 오른쪽 정렬 |
| 단위 | NotoSansCJK-Regular | 28px | 수치와 동색 | 수치 옆 |
| 하단 주석 | NotoSansCJK-Regular | 18px | #AAAAAA | 중앙 정렬 |
| TIP/주의 박스 | NotoSansCJK-Regular | 20px | #666666 | 박스 내부 |
| SAFE/CAUTION 뱃지 | NotoSansCJK-Bold | 24px | 흰색 on 컬러배경 | 우상단 |

**최소 가독성 규칙:**
```
• 카드 설명 최소 22px (이하 금지)
• 하단 주석 최소 18px (이하 금지)
• 모든 텍스트는 안티앨리어싱 적용
• 배경 대비 명도차 최소 4.5:1 (WCAG AA 기준)
```

**Validator (PASS/FAIL):**
```
□ 각 위치별 폰트 크기 규칙 준수
□ 카드 설명 22px 이상
□ 모든 텍스트 가독 가능 (깨짐 없음)
□ 단위 표기 정확 (μg, mg, g 구분)
```

---

#### 2.4.3 카드 유형별 필수 요소

| 카드 유형 | 필수 요소 | 골든 샘플 |
|----------|----------|----------|
| 영양성분 | SAFE 뱃지, 성분명+효능+수치, 하단 주석 | 고구마 3번 |
| 급여방법/안전 | DO/DON'T 구분, 초록✅/빨강❌ 아이콘 | 고구마 4번 |
| 급여량 | 표 형태(구분/체중/급여량), 주의사항 박스 | 고구마 5번 |
| 주의사항 | 번호+제목+설명, 하단 응급 안내 | 고구마 6번 |
| 조리방법 | STEP 번호, 단계명+설명, TIP 박스 | 고구마 7번 |

#### 2.4.4 금지 사항

| 금지 | 이유 |
|------|------|
| 번호+텍스트만 나열 | 하한선 미달 |
| 설명 없는 제목만 | 정보 부족 |
| 하단 보조 요소 없음 | 완성도 미달 |
| 단색 플랫 배경만 | 디자인 미달 |
| 그라데이션 헤더 없음 | 골든 샘플 미준수 |

#### 2.4.5 Validator 체크리스트 (PASS/FAIL)

```
□ 해상도 1080x1080
□ 상단 그라데이션 헤더 존재
□ 헤더 제목 존재
□ 카드형 레이아웃 (항목별 박스)
□ 컬러풀 번호 아이콘
□ 항목별 제목 + 설명 구조
□ 하단 보조 요소 1개 이상
□ 텍스트 가독성 (배경 대비)
□ 폰트 크기 규칙 준수 (§2.4.2)
□ 폰트 깨짐 없음
□ 단위 표기 정확 (μg/mg/g 구분)
```

**1개라도 FAIL → 재제작. 게시 불가.**

---

### 2.5 콘텐츠 핵심 정보 🔒 (v3.6 신규)

**소비자가 알고 싶은 것 2가지:**
1. **먹어도 되나?** (안전도)
2. **얼마나?** (체중별 급여량)

#### 급여량 4단계 (필수)

| 구분 | 체중 |
|------|------|
| 소형견 | 5kg 이하 |
| 중형견 | 5~15kg |
| 대형견 | 15~30kg |
| 초대형견 | 30kg 이상 |

**→ 인스타, 블로그 캡션 모두 4단계 급여량 필수 포함**

#### 블로그 캡션 규칙

| 항목 | 규칙 |
|------|------|
| 화자 | "11살 골든리트리버 햇살이를 키우는 엄마" |
| 톤 | 사랑스런 반려견 보호자의 따뜻한 경험 공유 |
| 관점 | "우리 햇살이한테 줘봤더니...", "저희 아이는..." |
| 이미지 표시 | `[이미지 N번: 설명]` 형태로 삽입 위치 명시 |

**금지 표현:**
- ❌ "햇살이네 강아지 음식 연구소"
- ❌ "전문가에 따르면", "연구 결과"
- ❌ 딱딱한 정보 전달 톤
- ❌ AI 티 나는 표현 (일관된 패턴, 과한 이모지)

**권장 표현:**
- ✅ "안녕하세요, 11살 골든리트리버 햇살이 엄마예요"
- ✅ 햇살이 이야기, 보호자 경험담
- ✅ 애정 어린 조언
- ✅ 다양한 문장 패턴 (AI 티 안 나게)

---

### 2.6 IG_RENDER v3.3 🔒 - 인스타그램용

| 항목 | 값 |
|------|-----|
| 해상도 | 1080x1080 |
| 폰트 | NotoSansCJK |
| validator | 15개 통과 필수 |
| 캡션 | 파스타 규칙 |

---

### 2.7 인스타 캡션 템플릿 v1.0 🔒

```
🥕 강아지 [음식명], 줘도 되나요?

[안전도에 따른 답변]

📏 체중별 급여량

소형견 (5kg 이하) — [g범위] ([직관적 단위])
중형견 (5~15kg) — [g범위] ([직관적 단위])
대형견 (15~30kg) — [g범위] ([직관적 단위])
초대형견 (30kg 이상) — [g범위] ([직관적 단위])

✅ 급여 팁
• [팁1]
• [팁2]
• [팁3]

[햇살이 경험담 1~2문장]

처음 주실 땐 조금만! 반응 보고 늘려주세요.

#강아지[음식명] #강아지간식 #반려견음식 ...
```

**필수 요소:**
- 4단계 급여량 (소형/중형/대형/초대형)
- 직관적 단위 (조각, 개, 스푼 등)
- 햇살이 경험담

**금지:**
- 임의 요약/축약
- 급여량 단계 생략
- 직관적 단위 생략

---

### 2.8 블로그 캡션 템플릿 v1.0 🔒

```
[이미지 1번: 표지]

안녕하세요, 11살 골든리트리버 햇살이 엄마예요.

[도입부 - 음식 소개 + 햇살이 이야기]

[이미지 2번: 음식 사진]


## [질문형 제목]

[본문 - 안전도, 영양 정보]

[이미지 3번: 영양 정보]


## [급여 방법 제목]

[본문 - 생/익힌 차이, 조리법]

[이미지 4번: 급여 방법]


## 얼마나 주면 될까요?

**소형견 (5kg 이하)** — [g범위] ([직관적 단위])
**중형견 (5~15kg)** — [g범위] ([직관적 단위])
**대형견 (15~30kg)** — [g범위] ([직관적 단위])
**초대형견 (30kg 이상)** — [g범위] ([직관적 단위])

[이미지 5번: 급여량 표]


## 주의할 점

[주의사항 본문]

[이미지 6번: 주의사항]


## 간단 조리법

[조리 단계]

[이미지 7번: 조리 방법]


[마무리 - 햇살이 이야기]

[이미지 8번: 햇살이 실사]

ℹ️ 일부 이미지는 AI로 생성되었습니다.

#강아지[음식명] #강아지간식 ...
```

**필수 요소:**
- [이미지 N번: 설명] 8개
- 4단계 급여량 + 직관적 단위
- H2 4개 이상
- 햇살이 엄마 톤

---

## 3. 역할 분담

| 역할 | 담당 | 업무 |
|------|------|------|
| PD | 박세준 | 최종 승인, 규칙 변경 권한 |
| 김부장 | Opus | 전략, 판단, 지시 |
| 최부장 | Claude Code | 실행, 코딩 |
| 레드2 | (내부) | 검증, 리스크 분석 |

```
김부장 = 전략/지시 (작업 직접 안 함)
최부장 = 실행 (지시받아 작업)
```

---

## 4. 금지 사항

| # | 금지 | 이유 |
|---|------|------|
| 1 | 🔒 LOCKED 규칙 변경 | 검증 완료 기준 |
| 2 | 문서 외 기준 인용 | 단일 진실원 원칙 |
| 3 | 기억 기반 판단 | 오류 발생원 |
| 4 | 레퍼런스 이미지 수정 | 기준 훼손 |
| 5 | "이전 합의" 논리 | 문서에 없으면 없음 |
| 6 | Validator FAIL 상태로 게시 | 품질 기준 미달 |

---

## 5. 작업 프로토콜

### 5.1 룰 확인 (세션 시작)

**트리거:** "룰 확인", "규칙 확인", "rule check"

**응답 포맷:**
```
━━━━━━━━━━━━━━━━━━━━━━
📋 현재 작업: [WO-XXX] [작업명]
━━━━━━━━━━━━━━━━━━━━━━

[적용 규칙]
[불가침 항목] ❌
[허용 범위] ✅
[Validator 체크리스트] ← v3.0 신규
[현재 상태]
[다음 단계]
━━━━━━━━━━━━━━━━━━━━━━
```

#### 5.1.1 Validator 체크리스트 응답 (v3.0 신규) 🔒

**"룰 확인" 호출 시, 해당 작업의 Validator를 반드시 출력한다.**

블로그 작업 시:
```
[Validator 체크리스트]
━ BLOG_RENDER v2.0 ━
□ 이미지 8장
□ 글자수 1,620~1,980자
□ H2 4개 이상
□ 키워드 5회 이상

━ 이미지 구성 ━
□ 1장: 표지(한글) - COVER_RULES 준수
□ 2장: 음식 사진
□ 3~7장: C2 인포그래픽 v2.0 준수
□ 8장: 햇살이 실사 사진

━ C2 인포그래픽 (3~7장 각각) ━
□ 해상도 1080x1080
□ 상단 그라데이션 헤더
□ 카드형 레이아웃
□ 번호 아이콘 + 제목 + 설명
□ 하단 보조 요소

━ 표지(한글) ━
□ Y 위치 70~90px
□ 폰트 120px
□ 그라데이션 상단 25%
□ 그림자 2px

→ 전체 PASS 시만 게시 가능
→ 1개 FAIL = 재제작
```

---

### 5.2 커밋 (세션 종료)

**트리거:** "커밋", "commit", "작업 완료"

**응답 포맷:**
```
━━━━━━━━━━━━━━━━━━━━━━
✅ COMMIT: [WO-XXX] [작업명]
━━━━━━━━━━━━━━━━━━━━━━

[완료 항목]
[Validator 결과] ← v3.0 신규
[생성 파일]
[변경 사항]
[다음 작업 예고]
[커밋 시간]
━━━━━━━━━━━━━━━━━━━━━━
```

**커밋 시 Validator 결과 필수 포함:**
```
[Validator 결과]
━ BLOG_RENDER v2.0 ━
✅ 이미지 8장
✅ 글자수 1,856자
✅ H2 9개
✅ 키워드 44회

━ C2 인포그래픽 (3~7장) ━
✅ 3장: 영양성분 - PASS
✅ 4장: 급여방법 - PASS
✅ 5장: 급여량 - PASS
✅ 6장: 주의사항 - PASS
✅ 7장: 조리방법 - PASS

━ 표지(한글) ━
✅ Y: 80px - PASS
✅ 폰트: 120px - PASS

→ 전체 PASS ✅ 게시 가능
```

---

## 6. 콘텐츠 규칙

### 6.1 안전 등급

| 등급 | 색상 | 의미 |
|------|------|------|
| SAFE | 🟢 초록 | 급여 가능 |
| CAUTION | 🟡 노랑 | 주의 필요 |
| DANGER | 🔴 빨강 | 위험 |
| FORBIDDEN | 🔴 빨강 | 절대 금지 |

---

### 6.2 캡션 규칙 (파스타 규칙)

```
1. 안전 이모지 (🟢/🟡/🔴)
2. 주의사항 리스트
3. 체중별 급여량
4. 핵심 메시지
5. CTA
6. AI 공시
7. 해시태그 12~16개
```

---

### 6.3 보호자 동질감 규칙 🔒 (v3.0 신규)

**원칙:** "수의사 블로그"가 아니라 "같은 견주 블로그"

모든 블로그 캡션에 아래 3개 요소를 필수 포함한다.

| # | 위치 | 필수 요소 | 예시 |
|---|------|----------|------|
| 1 | 도입부 | "나도 이걸 검색했었다" 경험 고백 | "저도 처음에 네이버에 이 질문을 검색했었어요" |
| 2 | 본문 중간 | 햇살이 실제 경험 에피소드 최소 2회 | 첫 급여 반응, 선호 형태, 노령견 특이사항 등 |
| 3 | 마무리 | "같은 고민 하는 보호자에게" 메시지 | "같은 고민을 하고 계실 보호자분들을 위해 직접 정리하고 있습니다" |

**톤 규칙:**
```
✅ "~더라고요", "~했었어요", "~해보니까"  (경험 공유)
✅ "저도 처음엔 몰랐는데", "검색해봤던 기억이 나요"  (동질감)
✅ 햇살이 이름 직접 언급 + 구체 행동 묘사  (실감)
❌ "~입니다", "~해주세요"만 반복  (교과서 톤)
❌ 햇살이 언급 없이 정보만 나열  (동질감 부재)
❌ "안전합니다", "좋습니다"만 반복  (수의사 톤)
```

**Validator (PASS/FAIL):**
```
□ 도입부에 "검색/고민 경험" 표현 있음
□ 본문에 햇살이 에피소드 2회 이상
□ 마무리에 "같은 보호자" 메시지 있음
□ 경험 공유 톤 ("~더라고요" 등) 사용
```
**1개라도 FAIL → 캡션 재작성**

---

### 6.4 블로그 팩트체크 필수 항목 🔒 (v3.0 신규)

모든 블로그 캡션은 아래 항목을 경쟁 블로그 대비 누락 없이 포함해야 한다.

| # | 항목 | 설명 |
|---|------|------|
| 1 | 왜 익혀야 하는지 과학적 이유 | 트립신 억제인자 등 구체적 근거 |
| 2 | 독성/위험 부위 경고 | 해당 음식의 줄기·씨·껍질 등 위험 부위 |
| 3 | 기저 질환 견 주의 | 당뇨·신장·알레르기 등 해당 시 수의사 상담 안내 |
| 4 | 조리법 차이 | 찌기 vs 굽기 vs 삶기 중 최적 방법과 이유 |
| 5 | 가공식품 경고 | 시판 간식·양념 제품 금지 안내 |

**Validator:** 해당 음식에 적용 가능한 항목이 누락되면 FAIL

---

### 6.5 포스트 제목 규칙 🔒

• 형식: **"강아지 {음식명} 먹어도 되나요?"**
• 질문형 고정. 다른 형식 금지.
• 금지 표현: 노령견, 급여량, 주의사항, 완벽 정리 등 한정/나열 표현
• 신규 콘텐츠부터 적용. 기존 게시물은 별도 지시 시 수정.

예시:
```
✅ 강아지 호박 먹어도 되나요?
✅ 강아지 연어 먹어도 되나요?
❌ 11살 노령견 호박 급여량·주의사항
❌ 호박 급여량 가이드
```

---

### 6.6 급여량 작성 형식 🔒

• 4줄 고정 (소형견/중형견/대형견/초대형견 각각 줄바꿈)
• 각 줄: "{사이즈}({체중})은 하루 {그람}g ({체감 단위} {이모지})"
• 체감 단위 필수: 저울 없이 판단 가능한 표현 (한 줌, 한 조각 등)
• 음식 형태에 따라 체감 비유 조정
• 한 문단에 뭉쳐 쓰기 금지

**형식 예시:**
```
## 📏 체중별 적정 급여량

소형견(5kg 이하)은 하루 10~20g (한두 조각 🍃)
중형견(5~15kg)은 20~40g (어른 손 한 줌 정도 ✋)
대형견(15~30kg)은 40~60g (종이컵 반 컵 정도 🥤)
초대형견(30kg 이상)은 60~80g이 적당합니다 (종이컵 한 컵 🥤)
```

**체감 단위 가이드:**

| 그람 범위 | 체감 단위 예시 |
|-----------|----------------|
| 5~10g | 엄지손톱 크기, 한 조각 |
| 10~20g | 한두 조각, 티스푼 2~3개 |
| 20~40g | 어른 손 한 줌, 탁구공 크기 |
| 40~60g | 종이컵 반 컵, 주먹 반 개 |
| 60~80g | 종이컵 한 컵, 어른 주먹 하나 |
| 80~100g | 밥공기 반 그릇 |

**음식 형태별 조정:**
- 과일류: "한 조각", "한 쪽"
- 채소류: "한 줌", "한 주먹"
- 육류: "엄지 한 마디", "손바닥 절반"
- 액체류(수프 등): "종이컵 반 컵"

※ 신규 콘텐츠부터 즉시 적용. 기존 게시물은 별도 지시 시 수정.

---

### 6.7 네이밍 규칙

```
✅ 허용: *_clean.png
❌ 금지: *_bg.png
```

---

## 7. 폴더 구조 규칙 🔒 (v3.0 신규)

### 7.0 골든 샘플 경로 🔒

```
contents/0_Golden sample/
├── Blog/                    ← 블로그 레퍼런스
│   ├── 01_표지.png
│   ├── 03_영양성분.png
│   ├── 04_급여방법.png
│   ├── 05_급여량.png
│   ├── 06_주의사항.png
│   ├── 07_조리방법.png
│   └── 본문.txt
└── Insta/                   ← 인스타 레퍼런스
    ├── pasta_cover.png
    └── caption.txt
```

**⚠️ 절대 삭제 금지:** 이 폴더는 모든 콘텐츠의 품질 기준이 되는 레퍼런스입니다.
- 삭제/이동/수정 시 PD 승인 필수
- Cloudinary + 노션에 백업 완료 상태

---

### 7.1 블로그 산출물 경로

```
각 음식 폴더 내 /blog 하위 폴더에 저장
```

**규칙:**
```
{음식폴더}/blog/           ← 블로그 산출물 위치
{음식폴더}/blog/01_표지_{음식명}.png
{음식폴더}/blog/02_음식사진.png
{음식폴더}/blog/03_{내용}.png
{음식폴더}/blog/04_{내용}.png
{음식폴더}/blog/05_{내용}.png
{음식폴더}/blog/06_{내용}.png
{음식폴더}/blog/07_{내용}.png
{음식폴더}/blog/08_햇살이.png
{음식폴더}/blog/본문.txt
{음식폴더}/blog/README.txt
```

**예시:**
```
contents/posted/001_sweet_potato_고구마/blog/
contents/body_ready/010_pumpkin_호박/blog/
```

**규칙:**
- 블로그 산출물은 반드시 해당 음식 폴더의 `/blog` 하위에 위치
- 음식 폴더가 posted에 있으면 posted 내, body_ready에 있으면 body_ready 내
- 음식 폴더의 현재 위치를 따름 (강제 이동 아님)

### 7.2 파일 네이밍 규칙

```
블로그 이미지: {순번}_{내용}_{음식명}.png
  예: 01_표지_호박.png, 03_영양성분_호박.png

블로그 본문: 본문.txt
블로그 설명: README.txt
```

---

## 8. 표지 규칙 v2.0 🔒

골든 샘플: 고구마 표지 (Pillow 픽셀 분석으로 측정)

### 8.1 해상도
• **1080 x 1080px 고정** (Instagram 정사각형)
• 1024, 1200 등 다른 해상도 금지

### 8.2 배경 이미지
• AI 생성 실사풍 이미지
• 구도: 강아지(햇살이) + 음식 접시
• 강아지: 정면 또는 약간 측면, 상반신 이상 노출
• 음식: 하단 1/3 영역에 배치, 그릇에 담긴 형태
• 배경: 실내 (거실/주방), 자연광 느낌

### 8.3 음식명 텍스트

| 항목 | 값 | 비고 |
|------|---|------|
| 내용 | 음식명 한글 (예: "호박") | 영어 금지 |
| 폰트 | BlackHanSans-Regular | 1순위 (NanumGothic-ExtraBold 대체) |
| 폰트 크기 | 120px | 글자당 폭 ~114px 기준 |
| 색상 | #FFFFFF (순백) | RGBA(255,255,255,255) |
| X 정렬 | 중앙 정렬 | center_x = 50% |
| Y 위치 | 상단 80px | 고정값 (비율 아님) |

### 8.4 드롭 쉐도우 (Drop Shadow) ⚠️ v2 변경

| 항목 | 값 | 비고 |
|------|---|------|
| 방식 | 별도 레이어 + GaussianBlur | stroke 사용 금지! |
| 색상 | RGBA(0,0,0,100) | alpha=100 |
| 오프셋 | X=2px, Y=2px | offset=2 |
| 블러 | radius=3 | ImageFilter.GaussianBlur |

**⚠️ 중요:** stroke_width 사용 금지. 반드시 드롭 쉐도우 레이어 방식 사용.

### 8.5 상단 그라데이션 오버레이 ⚠️ v2 신규

| 항목 | 값 |
|------|---|
| 영역 | 상단 25% (270px) |
| 색상 | 검정 (0,0,0) |
| 알파 | 80 → 0 (선형 감소) |
| 목적 | 텍스트 가독성 향상 |

### 8.6 금지 사항
• 영어 텍스트 금지
• 서브타이틀/부제목 금지 (음식명만)
• SAFE/CAUTION 뱃지 금지
• 하단 그라데이션 금지
• 워터마크 금지
• **stroke_width 사용 금지** (v2 추가)
• **Cloudinary 중복 업로드 금지** (기존 URL 존재 시 재업로드 금지)

### 8.7 Validator 체크리스트 (PASS/FAIL)

```
□ 해상도 1080x1080
□ 음식명 한글 텍스트 존재
□ 영어 텍스트 없음
□ 폰트: BlackHanSans-Regular 120px
□ 텍스트 색상: 흰색
□ 드롭 쉐도우: offset=2, alpha=100, blur=3
□ 상단 그라데이션: 25%, alpha 80→0
□ Y 위치: 80px (상단 기준)
□ X 정렬: 중앙
□ 배경 이미지에 강아지 + 음식 포함
```

→ 1개 FAIL = 표지 재제작

### 8.8 Pillow 렌더링 코드 레퍼런스 (v2)

```python
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# 상수
TARGET_SIZE = 1080
FONT_SIZE = 120
Y_POSITION = 80
SHADOW_OFFSET = 2
SHADOW_ALPHA = 100
SHADOW_BLUR = 3
GRADIENT_PERCENT = 0.25
GRADIENT_MAX_ALPHA = 80

# 폰트
font = ImageFont.truetype("BlackHanSans-Regular.ttf", FONT_SIZE)

# 텍스트 위치 계산
bbox = draw.textbbox((0, 0), "음식명", font=font)
text_w = bbox[2] - bbox[0]
x = (TARGET_SIZE - text_w) // 2
y = Y_POSITION

# 1. 상단 그라데이션 레이어
gradient_layer = Image.new('RGBA', (TARGET_SIZE, TARGET_SIZE), (0,0,0,0))
gradient_draw = ImageDraw.Draw(gradient_layer)
gradient_height = int(TARGET_SIZE * GRADIENT_PERCENT)
for y_grad in range(gradient_height):
    alpha = int(GRADIENT_MAX_ALPHA * (1 - y_grad / gradient_height))
    gradient_draw.line([(0, y_grad), (TARGET_SIZE, y_grad)], fill=(0,0,0,alpha))

# 2. 드롭 쉐도우 레이어 (blur 적용)
shadow_layer = Image.new('RGBA', (TARGET_SIZE, TARGET_SIZE), (0,0,0,0))
shadow_draw = ImageDraw.Draw(shadow_layer)
shadow_draw.text((x + SHADOW_OFFSET, y + SHADOW_OFFSET), "음식명",
                 font=font, fill=(0,0,0,SHADOW_ALPHA))
shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=SHADOW_BLUR))

# 3. 메인 텍스트 레이어
text_layer = Image.new('RGBA', (TARGET_SIZE, TARGET_SIZE), (0,0,0,0))
text_draw = ImageDraw.Draw(text_layer)
text_draw.text((x, y), "음식명", font=font, fill=(255,255,255,255))

# 4. 합성: 배경 + 그라데이션 + 쉐도우 + 텍스트
result = Image.alpha_composite(img.convert('RGBA'), gradient_layer)
result = Image.alpha_composite(result, shadow_layer)
result = Image.alpha_composite(result, text_layer)
```

---

## 9. 게시 SOP 🔒

### 9.1 트리거
PD가 "{번호}번 {음식명} 게시" 또는 "{음식명} 게시하자"로 지시하면
김부장 작업지시서 없이 최부장이 직접 실행.
별도 지시 없으면 Instagram + Threads 둘 다 게시.

### 9.2 게시 전 점검
```
□ 이미지 전체 존재 (표지 + 본문)
□ 전 슬라이드 1080x1080
□ 캡션 파일 존재
□ 안전도 이모지 정확
□ AI 고지 포함
□ 해시태그 12~16개
□ 캡션-본문 안전도 일치
→ 1개 FAIL = 게시 중단 + PD 보고
```

### 9.3 Instagram 게시

**[STEP 1] Cloudinary URL 확인**
```
① 구글시트에서 해당 콘텐츠의 Cloudinary URL 확인
② URL이 이미 존재하면 → 그대로 사용. 업로드 하지 않음.
③ URL이 없는 슬라이드만 → 신규 업로드
④ 업로드 후 구글시트에 URL 기록

⚠ 이미 URL이 있는 이미지를 다시 업로드하는 것 금지.
```

**[STEP 2~3] Graph API 게시**
1. Graph API 캐러셀 생성 (container → carousel → publish)
2. permalink 저장

### 9.4 Threads 게시
1. Threads API 캐러셀 생성 (동일 캡션)
2. permalink 저장

### 9.5 게시 후 처리
• 상태 → posted 변경
• 게시일시 기록

### 9.6 보고 형식
```
✅ {음식명} 게시 완료
📸 Instagram: {permalink}
🧵 Threads: {permalink}
📄 슬라이드: {N}장
🕐 게시: {시각}
```

### 9.7 예외 처리
• 토큰 만료 → PD에게 재발급 요청
• Rate limit → 60초 대기 후 1회 재시도
• 이미지/캡션 누락 → 게시 중단 + PD 보고
• 점검 FAIL 시 자의적 수정 금지. PD 또는 김부장 보고 후 대기.
• **Cloudinary URL 이미 존재 → 재업로드 금지, 기존 URL 사용**

---

## 10. 레드2 확장 모델 (블로그 2편부터)

| 요소 | 설명 |
|------|------|
| 상단 요약 박스 | 결론 먼저 |
| 비교표 | 종류별/옵션별 |
| FAQ 5개 | 검색 질의 대응 |
| 간단 레시피 | 조리법 1개 |
| 출처 박스 | 전문성 표현 |

---

## 11. 방 이동 프로토콜

### 필수 첨부 파일
1. BOOTSTRAP.md
2. RULES.md
3. SYNC_[날짜].md
4. RULE_CHECK_PROTOCOL.md

### 첫 발화
```
"BOOTSTRAP.md 읽었고, RULES.md 기준으로만 작업합니다.
 SYNC_[날짜].md 참조. 룰 확인."
```

---

## 12. Validator 총괄 규칙 🔒 (v3.0 신규)

### 11.1 원칙

```
1. 모든 산출물은 Validator 통과 후에만 게시 가능
2. Validator는 PASS/FAIL만 반환 (중간 등급 없음)
3. 1개라도 FAIL = 전체 FAIL → 재제작
4. 김부장·최부장 주관적 판단 개입 금지
5. "괜찮아 보이는데" = 규칙 위반
```

### 11.2 Validator 적용 범위

| 산출물 | Validator |
|--------|-----------|
| 블로그 표지(한글) | COVER_RULES 표지(한글) Validator |
| 블로그 C2 이미지 | C2 인포그래픽 v2.0 Validator |
| 블로그 8장 (햇살이) | 실사 확인 Validator |
| 블로그 본문 | BLOG_RENDER v2.0 Validator |
| 인스타 표지(영어) | COVER_RULES 표지(영어) Validator |
| 인스타 캐러셀 | IG_RENDER v3.3 Validator |

### 11.3 Validator FAIL 시 프로세스

```
FAIL 발생
  → 즉시 작업 중단
  → FAIL 항목 명시
  → 해당 항목만 재제작
  → 재검증
  → 전체 PASS 시만 진행
```

---

## 13. 파일 조작 안전 규칙 🔒 (v3.4 신규)

### 13.1 원칙

```
1. 파일 복사/이동/삭제 전에 기존 파일 존재 여부 반드시 확인
2. 덮어쓰기 전 백업 생성 필수
3. 스크립트 실행 전 --dry-run (또는 시뮬레이션) 먼저 실행
4. 휴지통 비우기/영구 삭제는 PD 명시적 승인 후에만 실행
```

### 13.2 파일 복사/이동 스크립트 실행 전 체크리스트

```
□ 대상 폴더에 기존 파일 있는지 ls 또는 find로 확인
□ 기존 파일 있으면 덮어쓰기 전 백업 (*.bak 또는 _backup/ 폴더)
□ --dry-run 또는 시뮬레이션 모드 먼저 실행
□ dry-run 결과 PD에게 보고 후 실행 승인 받기
□ 실행 후 결과 확인 및 보고
```

### 13.3 금지 사항

| # | 금지 | 이유 |
|---|------|------|
| 1 | 기존 파일 확인 없이 복사/이동 | 데이터 손실 |
| 2 | 백업 없이 덮어쓰기 | 복구 불가 |
| 3 | dry-run 없이 대량 작업 | 예측 불가 |
| 4 | rm -rf 무단 실행 | 데이터 손실 |
| 5 | 휴지통 자동 비우기 | 복구 불가 |

### 13.4 위반 시 처리

```
위반 발생
  → 즉시 작업 중단
  → 피해 범위 파악
  → PD에게 보고
  → 복구 시도 (백업/Cloudinary/git 등)
  → 재발 방지책 수립
```

### 13.5 폴더 삭제 금지 규칙 🔒

```
1. rm -rf 명령 실행 전 PD 승인 필수
2. "backup confirmed" 주장 시 실제 파일 개수 검증
3. 마이그레이션 시 원본 삭제 전 diff 확인
4. 삭제 전 반드시 Cloudinary 업로드 완료 확인
```

**rm -rf 실행 전 체크리스트:**
```
□ PD에게 삭제 대상 폴더/파일 목록 보고
□ PD 명시적 승인 ("삭제해", "OK" 등) 확인
□ 백업 주장 시: ls -la로 파일 개수 실제 확인
□ 마이그레이션 시: find | wc -l로 원본/대상 파일 수 비교
□ 콘텐츠 폴더 삭제 시: Cloudinary에 해당 이미지 업로드 완료 확인
□ 삭제 명령 실행 전 --dry-run 또는 echo로 대상 확인
```

**🚨 절대 삭제 금지 폴더:**
```
❌ contents/0_Golden sample/  ← 골든 샘플 (레퍼런스)
❌ .claude/                   ← Claude 설정/훅
❌ scripts/                   ← 핵심 스크립트
```

**금지:**
```
❌ PD 승인 없이 rm -rf 실행
❌ "백업했다"고 주장만 하고 검증 없이 삭제
❌ 마이그레이션 완료 확인 없이 원본 삭제
❌ Cloudinary 업로드 없이 로컬 원본 삭제
❌ 0_Golden sample 폴더 삭제/이동/수정
```

### 13.6 사고 기록

| 날짜 | 사고 | 원인 | 손실 |
|------|------|------|------|
| 2026-02-03 | content/ 폴더 삭제 | "backup confirmed" 주장 후 검증 없이 rm -rf | 승인완료 53개 포함 전체 |
| 2026-02-10 | 호박 블로그 파일 덮어씀 | 기존 파일 확인 없이 복사 | 3~7번 한글 파일 |

---

## 14. 상태 동기화 원칙 🔒 (v3.8 전면 개정)

### 14.1 Source of Truth

```
인스타그램 게시 여부가 최종 진실(Source of Truth)
```

| 인스타 상태 | 로컬/노션 조치 |
|------------|---------------|
| 게시됨 | 무조건 4_posted + 게시완료 |
| 미게시 | 현재 상태 유지 |

### 14.2 자동 동기화 규칙

```
인스타에 게시됨 = 무조건 게시완료
- 로컬: 4_posted 폴더로 자동 이동
- 노션: "게시완료" 자동 업데이트
- instagram_url 자동 저장
- 묻지 않고 자동 수정
```

### 14.3 불일치 처리

**발견 즉시 자동 수정 (승인 불필요):**
```
if 인스타_게시됨 and 로컬_상태 != "4_posted":
    → 4_posted로 자동 이동
    → 노션 "게시완료" 업데이트
    → 로그 기록
```

### 14.4 sync 명령 동작

`/insta sync` 또는 `python3 scripts/sync_instagram_to_local.py` 실행 시:
1. 인스타 전수 스캔
2. 불일치 자동 수정 (묻지 않음)
3. 결과 리포트 출력

### 14.5 원자 트랜잭션 (Atomic Transaction)

```python
def sync_post_atomic(content_id, instagram_url):
    """원자적 동기화 - 전부 성공하거나 전부 실패"""

    log = {
        "content_id": content_id,
        "instagram_url": instagram_url,
        "local_move": None,
        "notion_update": None,
        "final_status": None,
        "timestamp": datetime.now().isoformat()
    }

    try:
        # Step 1: 로컬 이동
        original_path = move_to_posted(content_id)
        log["local_move"] = "success"

        # Step 2: 노션 업데이트 (재시도 로직 포함)
        for attempt in range(3):
            try:
                update_notion_status(content_id, "게시완료", instagram_url)
                log["notion_update"] = "success"
                break
            except RateLimitError:
                time.sleep(60)
            except Exception as e:
                if attempt == 2:
                    raise e

        log["final_status"] = "POSTED_SYNCED"
        save_sync_log(log)
        return True

    except Exception as e:
        # 롤백: 로컬 원위치
        if log["local_move"] == "success":
            rollback_local_move(content_id, original_path)
            log["local_move"] = "rolled_back"

        log["final_status"] = "FAILED"
        log["error"] = str(e)
        save_sync_log(log)
        return False
```

### 14.6 상태 전이 규칙

```
┌─────────────┐     게시 성공      ┌─────────────┐
│ 3_approved  │ ─────────────────→ │  4_posted   │
└─────────────┘                    └─────────────┘
       │                                  │
       │ 실패 시 롤백                      │ 인스타 확인
       ↓                                  ↓
┌─────────────┐                    ┌─────────────┐
│  원위치     │                    │  게시완료   │
└─────────────┘                    └─────────────┘
```

### 14.7 3중 검증 (Triple Check)

```python
def triple_check():
    insta_count = get_instagram_post_count()  # 인스타 게시물 수
    notion_posted = get_notion_posted_count()  # 노션 게시완료 수
    local_posted = count_local_4_posted()      # 로컬 4_posted 수

    # 3중 일치 확인
    assert insta_count == notion_posted == local_posted

    # 노션 게시완료 중 인스타 미존재 확인
    orphan = find_notion_without_insta()
    assert len(orphan) == 0
```

**실행:** `python3 scripts/notion_check.py`

### 14.8 동기화 로그

모든 동기화 작업은 `config/logs/sync_YYYYMMDD.jsonl`에 기록:

```json
{
  "content_id": 35,
  "instagram_url": "https://...",
  "local_move": "success",
  "notion_update": "success",
  "final_status": "POSTED_SYNCED",
  "timestamp": "2026-02-11T11:30:00"
}
```

---

## 15. 이미지-캡션 일치 검증 🔒 (v3.7 신규)

### 15.1 자동 FAIL 조건

```
이미지-캡션 불일치 = 게시 불가 = FAIL
```

| 조건 | 판정 | 조치 |
|------|------|------|
| 급여량 숫자 불일치 (이미지 ≠ 캡션) | FAIL | 재생성 필수 |
| 안전도 표현 불일치 (SAFE/CAUTION/FORBIDDEN) | FAIL | 재생성 필수 |
| 특수문자 깨짐 감지 (⊠, □, 토푸박스) | FAIL | 스크립트 수정 후 재생성 |
| 급여량 직관 단위 누락 | FAIL | food_data.json 보완 후 재생성 |

### 15.2 급여량 표기 규칙

```
급여량 = g 단위 + 직관 단위 (둘 다 필수)
```

**올바른 예시:**
```
소형견 — 10~20g (동전 크기 2~3조각)
중형견 — 20~40g (손가락 한 마디 3~4조각)
대형견 — 40~60g (중간 당근 1/3개)
초대형견 — 60~80g (중간 당근 1/2개)
```

**FAIL 예시:**
```
소형견 — 10~20g           ← 직관 단위 누락 = FAIL
```

### 15.3 특수문자 금지 규칙

```
이미지 내 이모지/특수문자 사용 금지
```

**금지:**
```
❌ ⚠️ ✅ 💡 🏥 등 이모지
❌ ✓ ✗ 등 특수 체크 기호
```

**허용:**
```
✅ 도형 (원, 사각형, 삼각형) + 텍스트 조합
✅ V / X 텍스트 (도형 안에 배치)
✅ [주의] [TIP] 등 대괄호 텍스트
```

### 15.4 검증 시점

```
이미지 생성 직후 → Validator 실행 → PASS 시에만 게시 가능
```

| 시점 | 검증 항목 |
|------|----------|
| 생성 직후 | 특수문자 깨짐, 직관 단위 포함 여부 |
| 배치 전 | 캡션과 이미지 급여량/안전도 일치 |
| 최종 | 전체 PASS 확인 후 게시 |

---

## 16. 햇살이 표지 이미지 생성 규칙 🔒 (v2.0)

### 16.1 프롬프트 v2.0 (전문)

```
[FOOD_NAME]

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

### 16.2 사용법

```
맨 윗줄의 [FOOD_NAME]만 변경 → 나머지 AI 자동 생성
```

| 예시 변경 | 비고 |
|----------|------|
| CHERRY | 과일 |
| BANANA MILK | 음료 |
| KITKAT | 포장 과자 |
| ORIJEN | 반려견 사료 |

**제작 도구:** Higgsfield + 레퍼런스 이미지 첨부

### 16.3 CONTAINER RULE (용기 규칙)

| 카테고리 | 용기 | 예시 |
|----------|------|------|
| 신선 식품/과일/채소 | 반려견 식기 브랜드 | 사과, 당근, 브로콜리 |
| 음료 | 해당 음료 대표 용기 | 커피→컵, 바나나우유→노란병 |
| 브랜드 음료 | 원래 브랜드 캔/병 | 스프라이트, 코카콜라 |
| 포장 과자/식품 | 원래 포장 그대로 | 킷캣, 오레오, 빼빼로 |
| 반려견 간식/사료 | 원래 포장 그대로 | 오리젠, 아카나, 지위픽 |

### 16.4 반려견 식기 브랜드 (20개)

| 등급 | 브랜드 |
|------|--------|
| **프리미엄** | Le Creuset Pet, Diggs, MiaCara, Cloud7, Fable Pets |
| **중고가** | PETKIT, HARIO WAN, Waggo, Harry Barker, Messy Mutts |
| **인기** | Kong, Outward Hound, PetRageous, Loving Pets, Frisco |
| **한국** | 바잇미, 페슬러, 브리더랩, 뽀시래기, 아르르 |

### 16.5 VARIATION 요소 (자동 변화)

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

### 16.6 고정 배경 요소

| 카테고리 | 요소 |
|----------|------|
| 천장 | 3날개 팬 |
| 식물 | 몬스테라, 여인초, 스파티필름, 아레카 야자 |
| 조명 | 스탠드 램프, Mr. Maria Brown 램프 (창가) |

### 16.7 레이아웃 규격

```
┌─────────────────────────────┐
│                             │ ← 상단 40% (여백/텍스트)
│        [텍스트 공간]         │
├─────────────────────────────┤
│                             │
│       강아지 머리 위치       │ ← 40% 위치
│                             │
│                             │
│       음식/용기 하단         │ ← 90% 위치
└─────────────────────────────┘
```

| 구분 | 강아지 머리 | 용기 하단 | 적용 상황 |
|------|:----------:|:--------:|----------|
| **기본 규칙** | 40% | 90% | 일반 표지 |
| 클로즈업 컷 | 50% | 95% | 음식 강조 필요 시 |
| 세로 콘텐츠 | 35% | 85% | 스토리/릴스용 |
| 브랜드 PPL | 45% | 88% | 로고 가독성 확보 |

### 16.8 품질 기준

| 항목 | 기준 | FAIL 조건 |
|------|------|----------|
| 해상도 | 1080x1080 이상 | 저해상도 |
| 햇살이 얼굴 | 흰 주둥이, 골든 털 | 다른 개 생성 |
| 음식 위치 | 테이블 위 | 공중 부유 |
| 배경 | 한국 아파트 거실 | 야외, 펫샵 |
| 포커스 | 햇살이 + 음식 | 배경에 포커스 |

### 16.9 버전 이력

| 버전 | 날짜 | 주요 변경 |
|------|------|----------|
| v1.0 | 2026-01-15 | 최초 작성 |
| v1.5 | 2026-01-22 | CONTAINER RULE 추가 |
| v2.0 | 2026-01-29 | VARIATION 요소, 레이아웃 규격, 브랜드 목록 확장 |

---

## 17. 변경 이력

| 날짜 | 버전 | 내용 |
|------|------|------|
| 2026-02-06 | 1.0 | 최초 작성 |
| 2026-02-08 | 1.5 | IG_RENDER v3.3 추가 |
| 2026-02-10 | 2.0 | BLOG_RENDER, COVER_RULES, 룰 확인/커밋 프로토콜 추가 |
| 2026-02-10 | 3.0 | C2 v2.0 업그레이드, 폴더 규칙, Validator 체계, 이미지 구성 규칙, 실사 규칙, 보호자 동질감 규칙, 팩트체크 필수 항목, §8 표지 규칙(해상도·폰트·외곽선·Y위치 고정) 추가 |
| 2026-02-10 | 3.1 | §8 표지 규칙 v2.0: stroke→드롭쉐도우(offset=2,blur=3), 상단 그라데이션(25%,alpha80→0), Y위치 80px, 폰트 BlackHanSans-Regular |
| 2026-02-10 | 3.2 | §6.6 급여량 작성 형식 추가: 4줄 고정, 체감 단위 병기 (한 줌, 한 조각 등) |
| 2026-02-10 | 3.3 | §6.5 포스트 제목 규칙, §9 게시 SOP 추가, 섹션 번호 재정렬 (§9→§10, §10→§11, §11→§12, §12→§13) |
| 2026-02-10 | 3.4 | §13 파일 조작 안전 규칙 추가: 기존 파일 확인, 백업 필수, dry-run 선행, 사고 기록 |
| 2026-02-10 | 3.5 | §13.5 폴더 삭제 금지 규칙 추가: rm -rf PD 승인 필수, backup 검증, 마이그레이션 diff 확인 |
| 2026-02-11 | 3.6 | §2.5 콘텐츠 핵심 정보, §2.7 인스타 캡션 템플릿, §2.8 블로그 캡션 템플릿, §14 상태 동기화 원칙 추가 |
| 2026-02-11 | 3.7 | §15 이미지-캡션 일치 검증 추가: 급여량 일치, 안전도 일치, 특수문자 금지, 직관 단위 필수 |
| 2026-02-11 | 3.8 | §14 원자 트랜잭션 전면 개정, §16 햇살이 표지 프롬프트 v2.0 추가, 변경 이력 §17로 이동 |

---

## v3.0 변경 요약

| 항목 | v2.0 | v3.0 |
|------|------|------|
| C2 인포그래픽 | v1.0 (3항목) | v2.0 (Validator 8항목) |
| BLOG_RENDER | v1.0 (5항목) | v2.0 (이미지 구성 규칙 추가) |
| 8장 이미지 | 규칙 없음 | 실사 전용 🔒 |
| 폴더 구조 | 암묵 규칙 | 명문화 🔒 |
| Validator | 없음 | 전체 산출물 PASS/FAIL 🔒 |
| 룰 확인 응답 | 규칙+상태 | 규칙+상태+Validator 체크리스트 |
| 커밋 응답 | 완료+파일 | 완료+파일+Validator 결과 |
| 표지 검증 | 규칙만 존재 | Validator PASS/FAIL 체계 |
| 표지 텍스트 | 규칙 없음 | §8 v2.0 드롭쉐도우·상단그라데이션·Y=80px 🔒 |
| 캡션 톤 | 규칙 없음 | 보호자 동질감 규칙 🔒 |
| 팩트체크 | 규칙 없음 | 블로그 팩트체크 필수 항목 🔒 |

---

**끝.**
