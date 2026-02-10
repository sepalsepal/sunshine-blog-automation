# SYNC.md - 박리서치 ↔ 최기술 작업 동기화

---

## [2026-01-24] A/B 테스트 계획서 + 수익화 로드맵 완료

### 작업 결과

1) config/ab_test_plan.md - 7장 vs 10장 A/B 테스트 설계 ✅
2) config/monetization_roadmap.md - 팔로워별 수익화 전략 + 브랜드 20개 ✅

### A/B 테스트 핵심
- 테스트 기간: 4주 (그룹당 20개 포스트)
- 측정 지표: 공유율 > 저장율 > 참여율 > 완독률
- 통계: Two-Proportion Z-Test, α=0.05, 검정력 80%
- 연구 결과: 10장이 참여율 2.0%+로 7장(1.8~1.9%) 대비 우세
- 박리서치 의견: safe=10장, caution=7장, dangerous=5장 권장

### 수익화 핵심
- 즉시 시작 가능: 쿠팡파트너스 (팔로워 무관)
- 협찬 시작: 3,000명부터 (제품 제공)
- 유의미한 수익: 10,000명부터 (월 75만원 예상)
- 30,000명 목표: 월 365만원 예상 (앰배서더+협찬+제휴)
- 1순위 접근 브랜드: 바잇미, 보우와우, 사조 우다다

---

## [2026-01-24] 팩트체크 DB + 콘텐츠 캘린더 완료

### 작업 결과

| # | 파일 | 내용 | 상태 |
|---|------|------|------|
| 1 | `config/factcheck_database.json` | 15개 위험식품 독성용량 + 15개 안전식품 급여량 + 체중별 가이드 | ✅ |
| 2 | `config/content_calendar_2026.md` | 12개월 주차별 제철식재료 + 23개 기념일 + 시즌 전략 | ✅ |

### 팩트체크 DB 핵심
- 출처: ASPCA, AKC, Merck Veterinary Manual, PMC 논문, 대한수의사회
- 위험 식품 15종: 독성 성분, kg당 용량, 증상, 응급처치 포함
- 안전 식품 15종: 효능, 주의사항, 체중별 급여량 포함
- 10% 규칙: 간식은 하루 칼로리의 10% 이내
- 골든리트리버(30kg+): 하루 간식 한도 120~200kcal (100~150g)

### 캘린더 핵심
- 23개 기념일 연계 특집 콘텐츠 기획
- 12개월 × 4주 = 48주 제철 식재료 매칭
- 콘텐츠 믹스: 18:00 안전식품 / 19:30 팁·보충제 / 21:00 경고·특집

---

## [2026-01-24] 콘텐츠 확장 전략 조사 완료

### 작업 결과 요약

| # | 작업 | 파일 | 상태 |
|---|------|------|------|
| 1 | 주제 100개 확장 | `config/topics_expanded.json` | ✅ 완료 |
| 2 | 경쟁 계정 Top 10 분석 | `config/competitor_analysis.md` | ✅ 완료 |
| 3 | 해시태그 전략 | `config/hashtag_strategy.json` | ✅ 완료 |

### 1. 주제 확장 (31개 → 100개)

| 카테고리 | 기존 | 확장 후 | 안전/위험 |
|----------|------|---------|-----------|
| 과일 (안전) | 17 | 20 | safe |
| 과일 (위험) | 0 | 5 | dangerous |
| 채소 (안전) | 6 | 18 | safe |
| 채소 (위험) | 0 | 5 | dangerous |
| 육류/단백질 | 4 | 15 | safe |
| 해산물 | 3 | 10 | safe |
| 곡물/탄수화물 | 0 | 8 | safe |
| 유제품 | 1 | 4 | caution |
| 견과류/씨앗 | 0 | 5 | safe |
| 보충제/슈퍼푸드 | 0 | 5 | safe |
| 위험 식품 (경고) | 0 | 5 | dangerous |
| **합계** | **31** | **100** | - |

**신규 콘텐츠 전략:** 안전 85개 + 위험/경고 15개
- 경고 콘텐츠는 공유/저장률 2~3배 높음 (바이럴 효과)
- 하루 3포스팅: 안전 2개 + 위험/팁 1개 로테이션

### 2. 경쟁 분석 핵심 발견

**시장 공백 확인:**
> 한국어 + 강아지 음식 영양 정보 + AI 인포그래픽 캐러셀 = 경쟁자 거의 없음

- 영어권: 전문 영양사/수의사 계정 다수 (396K 최대)
- 한국어권: 귀여움 큐레이션 or 브랜드 홍보 위주
- @sunshinedogfood 포지션: "한국어 강아지 음식 정보 교육 1위"

### 3. 해시태그 전략

- 최적 개수: 15~20개
- 구성: 브랜드(3) + 대형(2) + 중형(3) + 니치(3~5) + 주제별(5~10)
- 주간 로테이션 4세트 (섀도우밴 방지)
- 계절별 추가 해시태그 세트 포함

---

## [2026-01-24] Flux 2 Pro 도입 ✅ 완료

### 현재 상태 (김부장 확인)

- fal.ai API 키 발급 ✅
- 연동 테스트 ✅
- 프롬프트 v2 승인 ✅
- `image_generator.py`: `fal` provider 구현 완료 (최기술)
- `config.yaml`: `provider: "fal"` 전환 완료

### 이전 진단 결과 (참고용)
- 현재 posting_schedule: 하루 1개 (목표: 하루 3개)

**주제 현황:** 31개 topic 확보 (과일 17, 채소 6, 육류 4, 해산물 3, 유제품 1)
→ 하루 3개 기준 10일치. 추가 주제 확보 필요.

---

### 최기술님 작업 지시서

#### 작업 1: fal-client 패키지 설치
```bash
pip install fal-client
```

#### 작업 2: `.env.example` 추가
```bash
# Flux 2 Pro (fal.ai)
FAL_KEY=your_fal_api_key
```

#### 작업 3: `.env`에 실제 키 추가
- fal.ai 가입: https://fal.ai → GitHub 로그인
- Dashboard → API Keys → Create Key
- `.env`에 `FAL_KEY=fal_xxxxx` 추가

#### 작업 4: `config.yaml` 수정 (line 48~66)

```yaml
  image_generator:
    enabled: true
    provider: "flux2pro"  # ← 변경
    batch_size: 10
    retry_attempts: 3

    # Flux 2 Pro (fal.ai) 설정 ← 추가
    flux2pro:
      endpoint: "fal-ai/flux-2-pro"
      image_size: "square_hd"      # 1024x1024
      output_format: "png"
      safety_tolerance: 2

    # DALL-E 3 설정 (백업)
    dalle3:
      model: "dall-e-3"
      size: "1024x1024"
      quality: "hd"

    # Stability AI 설정 (백업)
    stability:
      engine: "stable-diffusion-xl-1024-v1-0"
      steps: 30
      cfg_scale: 7
```

#### 작업 5: `image_generator.py` 수정

추가할 코드:
1. `execute()` 메서드에 분기 추가:
```python
elif provider == "flux2pro":
    images = await self._generate_flux2pro(prompts, topic)
```

2. 새 메서드 추가:
```python
@retry(max_attempts=3, delay=2.0)
async def _generate_flux2pro(self, prompts: List, topic: str) -> List[Dict]:
    """Flux 2 Pro (fal.ai) API로 이미지 생성"""
    import fal_client
    import os
    import aiohttp

    base_path = Path(self.config.get("_global", {}).get("paths", {}).get("images", "."))
    flux_config = self.config.get("flux2pro", {})
    images = []

    for p in prompts:
        result = fal_client.subscribe(
            flux_config.get("endpoint", "fal-ai/flux-2-pro"),
            arguments={
                "prompt": p["prompt"],
                "image_size": flux_config.get("image_size", "square_hd"),
                "output_format": flux_config.get("output_format", "png"),
                "safety_tolerance": flux_config.get("safety_tolerance", 2),
            }
        )

        # 이미지 다운로드
        image_url = result["images"][0]["url"]
        image_path = base_path / topic / f"{topic}_{p['index']:02d}_{p['type']}.png"
        image_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as resp:
                image_path.write_bytes(await resp.read())

        images.append({
            "index": p["index"],
            "type": p["type"],
            "path": str(image_path),
            "exists": True,
            "seed": result.get("seed")
        })

        self.log(f"  [{p['index']}/{len(prompts)}] {p['type']} 생성 완료")

    return images
```

#### 작업 6: `api_keys` 섹션 추가 (config.yaml 마지막)
```yaml
api_keys:
  fal: "${FAL_KEY}"          # ← 추가
  gemini: "${GEMINI_API_KEY}"
  openai: "${OPENAI_API_KEY}"
  # ...
```

---

### 비용 예측

| 항목 | 수치 |
|------|------|
| 하루 포스팅 | 3개 |
| 포스팅당 이미지 | 10장 (캐러셀) |
| 하루 이미지 | 30장 |
| 월 이미지 | ~900장 |
| 장당 비용 | $0.03 |
| **월 예상 비용** | **$27 (약 36,000원)** |

> 주의: 이전 보고에서 "하루 3포스팅 = 월 90장"으로 계산했으나,
> 캐러셀 10장 기준이면 **월 900장**입니다. 비용 재확인 필요.

---

### 리스크 및 주의사항

1. **fal_client.subscribe()는 동기 함수** → async 래퍼 필요할 수 있음
2. **리사이즈 순서**: Flux는 1024x1024 생성 → 1080x1080 리사이즈 → 텍스트 오버레이 (CLAUDE.md 규칙)
3. **API Rate Limit**: fal.ai 무료 티어 제한 확인 필요
4. **네트워크 에러**: 이미지 다운로드 실패 시 retry 로직 포함됨

---

### 테스트 방법
```bash
# 1. 단일 이미지 테스트
python -c "
import fal_client, os
os.environ['FAL_KEY'] = 'your_key'
r = fal_client.subscribe('fal-ai/flux-2-pro', arguments={
    'prompt': 'golden retriever looking at fresh chicken breast, studio food photography, white background',
    'image_size': 'square_hd',
    'output_format': 'png'
})
print(r['images'][0]['url'])
"

# 2. 파이프라인 드라이런
python cli.py cherry --dry-run
```

---

**상태:** ✅ 사전 조사 완료, 최기술님 작업 대기
**다음 단계:** 최기술님이 작업 4~5 구현 후 → 박리서치 검증
