# Image Generation API Research

Project Sunshine v3.0 - 이미지 생성 API 비교 분석

---

## Executive Summary

Project Sunshine은 1080x1080px (1:1) Instagram 캐러셀 이미지를 자동 생성합니다.
현재 `ImageGeneratorAgent`에서 사용할 최적의 API를 선정하기 위한 조사 결과입니다.

**추천 순위:**
1. **Flux (Black Forest Labs)** - 가성비 + 품질 최적 밸런스
2. **Stability AI (SDXL/SD3)** - 가격 최저, 커스터마이징 우수
3. **OpenAI GPT Image 1.5** - 최고 품질, 비용 높음

---

## 1. OpenAI (DALL-E / GPT Image)

### 모델 현황

| 모델 | 상태 | 비고 |
|------|------|------|
| DALL-E 2 | Deprecated (2026.05.12) | 레거시 |
| DALL-E 3 | Deprecated (2026.05.12) | 현재 사용 중 |
| GPT Image 1 | Active | 플래그십 |
| GPT Image 1.5 | Active (최신) | 추천 |

### 가격

| 모델 | 품질 | 가격/장 |
|------|------|---------|
| DALL-E 3 | Standard (1024x1024) | $0.04 |
| DALL-E 3 | HD (1024x1792) | $0.12 |
| GPT Image 1.5 | Low | ~$0.01 |
| GPT Image 1.5 | Medium | ~$0.04 |
| GPT Image 1.5 | High | ~$0.17 |

### 지원 해상도

- 1024x1024 (정사각)
- 1024x1536 (세로) - **Project Sunshine에 적합**
- 1536x1024 (가로)

### 장단점

| 장점 | 단점 |
|------|------|
| 최고 품질 이미지 | 비용 높음 (High 품질) |
| 텍스트 렌더링 우수 | DALL-E 3 곧 종료 |
| 안정적인 API | Rate limit 제한적 (실제 ~15/min) |
| 프롬프트 이해도 최상 | 1장씩만 생성 (n=1) |

### 월 비용 추정 (30개 포스트 x 10장 = 300장/월)

- Low: $3/월
- Medium: $12/월
- High: $51/월

---

## 2. Stability AI (Stable Diffusion)

### 모델 현황

| 모델 | 가격/장 | 특징 |
|------|---------|------|
| SD 1.5 | $0.006 | 레거시, 빠름 |
| SDXL | $0.011 | 표준, 안정적 |
| SD3 | $0.037 | 최신, 고품질 |
| Stable Image Ultra | $0.08 | 최고 품질 |

### 지원 해상도 (SDXL)

- 1024x1024 (정사각 1:1)
- 832x1216 (세로 2:3) - **Project Sunshine에 근접**
- 768x1344 (세로 9:16)
- 1152x896 (가로 4:3)
- 커스텀 해상도 가능

### 주요 기능

- Text-to-Image
- Image-to-Image (강도 조절)
- Inpainting (부분 수정)
- Outpainting (확장)
- Upscaling (4K까지)
- ControlNet (정밀 제어)
- Search & Replace

### 라이선스

- **Community License**: 연매출 $1M 미만 무료 (무제한)
- **Enterprise**: 커스텀 가격

### 장단점

| 장점 | 단점 |
|------|------|
| 최저 가격 ($0.006~) | 품질 편차 존재 |
| 오픈소스 기반 | 프롬프트 엔지니어링 필요 |
| 커스터마이징 자유도 높음 | 텍스트 렌더링 약함 |
| 다양한 기능 (inpaint 등) | API 안정성 이슈 간헐적 |
| 커뮤니티 라이선스 무료 | |

### 월 비용 추정 (300장/월)

- SD 1.5: $1.8/월
- SDXL: $3.3/월
- SD3: $11.1/월
- Ultra: $24/월

---

## 3. Leonardo AI

### 플랜

| 플랜 | 가격 | 크레딧 |
|------|------|--------|
| Free | $0 | 150 토큰/일 |
| Basic API | $9/월 | 3,500 크레딧 (비소멸) |
| Starter | $12/월 | 구독 토큰 |
| Creator | $28/월 | 구독 토큰 |
| Maestro | $48/월 | 대용량 |

### 지원 해상도

- 512x512 ~ 2048x2048 (기본 생성)
- 업스케일: 최대 20MP
- 1024x1024 기본 권장

### 주요 기능

- Alchemy (고급 생성 엔진)
- Prompt Magic v3
- PhotoReal (포토리얼리스틱)
- Motion (비디오)
- Custom LoRA 모델 학습
- 업스케일러

### 통합 모델

- Leonardo Diffusion XL
- Leonardo Lightning XL (빠른 생성)
- FLUX.1 Kontext
- Ideogram
- Nano Banana Pro

### 장단점

| 장점 | 단점 |
|------|------|
| 다양한 모델 선택 | 복잡한 가격 체계 |
| 커스텀 모델 학습 | API 별도 과금 |
| UI + API 모두 제공 | 무료 대기시간 길음 (8-20분) |
| PhotoReal 고품질 | 크레딧 소모량 불투명 |

### 월 비용 추정 (300장/월)

- Basic API: $9/월 (3,500 크레딧 내 가능)
- 초과시: 수동 충전 필요

---

## 4. Flux (Black Forest Labs)

### 모델 라인업

| 모델 | 가격/장 | 특징 |
|------|---------|------|
| FLUX.1 [schnell] | 무료 (Together AI) | 빠른 생성 |
| FLUX.1 [pro] | ~$0.04 | 프로덕션용 |
| FLUX1.1 [pro] Ultra | $0.06 | 고해상도 |
| FLUX.2 [dev] | 오픈웨이트 | 32B 모델 |
| FLUX.2 [pro] | Premium | 최고 품질 |
| FLUX.2 [klein] | 최신 (2026.01) | 최고속 |

### 주요 기능

- Text-to-Image (프로덕션 그레이드)
- ControlNet 지원 (Canny, Depth)
- Redux (이미지 변형)
- Raw Mode (자연스러운 스타일)
- 일관된 인페인팅

### 장단점

| 장점 | 단점 |
|------|------|
| 프로덕션 품질 | 비교적 신생 서비스 |
| 합리적 가격 ($0.04~) | 일부 모델 오픈웨이트만 |
| 빠른 생성 속도 | 커뮤니티 자료 적음 |
| Together AI 무료 tier | 세로형 해상도 제한적 |
| 텍스트 렌더링 양호 | |

### 월 비용 추정 (300장/월)

- schnell (무료 tier): $0/월
- FLUX.1 pro: $12/월
- FLUX1.1 pro Ultra: $18/월

---

## 5. 기타 주목할 API

### Google Imagen 4

| 항목 | 내용 |
|------|------|
| 가격 | $0.02/장 (Fast), 상위 모델 미공개 |
| 해상도 | 최대 2K |
| 특징 | 텍스트 렌더링 우수, Gemini API 통합 |
| 추천도 | ★★★★☆ (엔터프라이즈 환경) |

### Ideogram 3.0

| 항목 | 내용 |
|------|------|
| 가격 | $0.01~$0.17/장 |
| 특징 | 텍스트 렌더링 업계 최고 |
| 추천도 | ★★★★☆ (텍스트 포함 이미지) |

### Midjourney

| 항목 | 내용 |
|------|------|
| 가격 | $10~$120/월 (구독) |
| API | 공식 API 없음 (3rd party만) |
| 특징 | 예술적 품질 최고 |
| 추천도 | ★★☆☆☆ (API 자동화 불가) |

### Adobe Firefly

| 항목 | 내용 |
|------|------|
| 가격 | $9.99~$29.99/월 |
| 특징 | Creative Cloud 통합, 상업적 안전 |
| 추천도 | ★★★☆☆ (Adobe 생태계 사용자) |

---

## 종합 비교표

| API | 가격/장 | 품질 | 속도 | 텍스트 렌더링 | API 안정성 | 자동화 적합 |
|-----|---------|------|------|--------------|-----------|-------------|
| GPT Image 1.5 | $0.04~0.17 | ★★★★★ | ★★★☆☆ | ★★★★★ | ★★★★★ | ★★★★★ |
| Stability AI (SDXL) | $0.011 | ★★★☆☆ | ★★★★★ | ★★☆☆☆ | ★★★★☆ | ★★★★★ |
| Stability AI (SD3) | $0.037 | ★★★★☆ | ★★★★☆ | ★★★☆☆ | ★★★★☆ | ★★★★★ |
| Leonardo AI | ~$0.03 | ★★★★☆ | ★★★★☆ | ★★★☆☆ | ★★★☆☆ | ★★★★☆ |
| Flux pro | $0.04 | ★★★★★ | ★★★★★ | ★★★★☆ | ★★★★☆ | ★★★★★ |
| Flux schnell | 무료 | ★★★☆☆ | ★★★★★ | ★★★☆☆ | ★★★★☆ | ★★★★★ |
| Google Imagen 4 | $0.02 | ★★★★★ | ★★★★☆ | ★★★★★ | ★★★★★ | ★★★★☆ |
| Ideogram 3.0 | $0.01~0.17 | ★★★★☆ | ★★★★☆ | ★★★★★ | ★★★★☆ | ★★★★☆ |

---

## Project Sunshine 추천안

### 요구사항

- 해상도: 1080x1080px (1:1 정사각형)
- 월 생산량: 300장 (30 포스트 x 10장)
- 스타일: 귀여운 강아지 + 음식 일러스트/사진
- 텍스트: Puppeteer로 별도 오버레이 (API 텍스트 불필요)
- 자동화: 완전 자동 파이프라인

### 추천 전략: 하이브리드 접근

#### Option A: 비용 최소화 (월 $3~12)
```
1차: Flux schnell (무료, Together AI) - 초안 생성
2차: Stability SDXL ($0.011) - 프로덕션 대체
백업: SD3 ($0.037) - 품질 이슈시
```

#### Option B: 품질 우선 (월 $12~18)
```
1차: Flux pro ($0.04) - 주력
백업: GPT Image 1.5 Medium ($0.04) - 특수 프롬프트
```

#### Option C: 최고 품질 (월 $50+)
```
1차: GPT Image 1.5 High ($0.17) - 전체
백업: Flux pro Ultra ($0.06) - 대안
```

### 최종 추천: Option B (Flux pro 주력)

**이유:**
1. 프로덕션 품질 보장
2. 합리적 비용 ($12/월)
3. API 안정성 높음
4. 빠른 생성 속도 (파이프라인에 적합)
5. 텍스트는 Puppeteer 오버레이로 처리하므로 텍스트 렌더링 중요도 낮음
6. 세로형 이미지 지원

---

## 구현 가이드

### ImageGeneratorAgent 업데이트 방향

```python
# agents/image_generator.py 업데이트 예시

class ImageGeneratorAgent(BaseAgent):
    PROVIDERS = {
        "flux": {
            "api_url": "https://api.bfl.ml/v1/flux-pro-1.1",
            "cost_per_image": 0.04,
            "max_resolution": "1024x1536",
        },
        "openai": {
            "api_url": "https://api.openai.com/v1/images/generations",
            "model": "gpt-image-1.5",
            "cost_per_image": 0.04,  # medium quality
        },
        "stability": {
            "api_url": "https://api.stability.ai/v2beta/stable-image/generate/sd3",
            "cost_per_image": 0.037,
        }
    }

    async def execute(self, input_data):
        provider = input_data.get("provider", "flux")
        prompts = input_data.get("prompts", [])

        images = []
        for prompt in prompts:
            image = await self._generate(provider, prompt)
            images.append(image)

        return AgentResult(success=True, data={"images": images})
```

### 환경변수 추가 (.env)

```bash
# Image Generation APIs
FLUX_API_KEY=your_flux_api_key
OPENAI_API_KEY=your_openai_api_key
STABILITY_API_KEY=your_stability_api_key
```

---

## 참고 자료

- [OpenAI Image API](https://platform.openai.com/docs/guides/image-generation)
- [Stability AI Platform](https://platform.stability.ai/)
- [Black Forest Labs (Flux)](https://bfl.ai/)
- [Leonardo AI API](https://leonardo.ai/api/)
- [Google Imagen API](https://cloud.google.com/vertex-ai/generative-ai/docs/image/overview)
- [Ideogram API](https://ideogram.ai/features/api-pricing)
- [Together AI](https://www.together.ai/)

---

*Research Date: 2026-01-23*
*Author: Claude (Project Sunshine R&D)*
