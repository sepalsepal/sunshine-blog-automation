# Agent Guide - Project Sunshine v3.0

14개 에이전트 상세 가이드

---

## Core Pipeline Agents (9개)

파이프라인 순서대로 실행되는 핵심 에이전트들.

---

### 1. PlannerAgent (김차장)

**역할:** 콘텐츠 기획 총괄
**파일:** `agents/planner.py`

| 항목 | 내용 |
|------|------|
| 입력 | `{"topic": "cherry"}` |
| 출력 | 10장 슬라이드 구조, 텍스트 데이터 |
| 핵심 기능 | 주제별 JSON 로드, 슬라이드 구성 |

```python
from agents import PlannerAgent
agent = PlannerAgent()
result = await agent.run({"topic": "cherry"})
# result.data["slides"] → 10장 슬라이드 데이터
```

---

### 2. FactCheckerAgent (최검증)

**역할:** 팩트체크/안전 검증
**파일:** `agents/fact_checker.py`

| 항목 | 내용 |
|------|------|
| 입력 | `{"topic": "grape"}` |
| 출력 | 안전 등급, 독성 정보, 급여 가이드 |
| 핵심 기능 | 600+ 식품 데이터베이스, 5단계 안전 등급 |

안전 등급:
- `SAFE` - 안전하게 급여 가능
- `CONDITIONAL` - 조건부 가능
- `CAUTION` - 주의 필요
- `DANGEROUS` - 위험
- `CRITICAL` - 절대 금지 (독성)

```python
from agents import FactCheckerAgent
agent = FactCheckerAgent()
safety = agent.check_food_safety("grape")
# {'safety_level': 'CRITICAL', 'toxic_compounds': ['tartaric_acid']}
```

---

### 3. PromptGeneratorAgent (김작가)

**역할:** AI 이미지 프롬프트 작성
**파일:** `agents/prompt_generator.py`

| 항목 | 내용 |
|------|------|
| 입력 | PlannerAgent 출력 (슬라이드 데이터) |
| 출력 | 10개 이미지 생성 프롬프트 |
| 핵심 기능 | 슬라이드별 최적 프롬프트 생성 |

---

### 4. ImageGeneratorAgent (이작가)

**역할:** AI 이미지 생성
**파일:** `agents/image_generator.py`

| 항목 | 내용 |
|------|------|
| 입력 | 이미지 프롬프트 목록 |
| 출력 | 10개 이미지 파일 경로 |
| 핵심 기능 | DALL-E/Stability AI 연동 |
| 이미지 규격 | 1080x1080px (1:1) |

---

### 5. TextOverlayAgent (박편집)

**역할:** 텍스트 오버레이 렌더링
**파일:** `agents/text_overlay.py`

| 항목 | 내용 |
|------|------|
| 입력 | 이미지 + 텍스트 데이터 |
| 출력 | 텍스트 합성된 최종 이미지 |
| 핵심 기능 | Puppeteer HTML 렌더링, 언더라인 |
| 렌더러 | `scripts/add_text_overlay_puppeteer.js` |

언더라인 규칙: `텍스트 너비 + 20px`

---

### 6. QualityCheckerAgent (박과장)

**역할:** 품질 검수
**파일:** `agents/quality_checker.py`

| 항목 | 내용 |
|------|------|
| 입력 | 최종 이미지 목록 |
| 출력 | 검수 점수, 합격/불합격 |
| 통과 기준 | 85점 이상 |
| 검수 항목 | 이미지 크기, 텍스트 가독성, 품질 |

---

### 7. CaptionAgent (이카피)

**역할:** 캡션/해시태그 생성
**파일:** `agents/caption.py`

| 항목 | 내용 |
|------|------|
| 입력 | `{"topic": "cherry"}` |
| 출력 | 캡션 텍스트, 30개 해시태그 |
| 핵심 기능 | 600+ 식품 DB, SEO 해시태그, 이모지 |

캡션 구조:
1. 인트로 (질문형)
2. 핵심 정보 (효능, 주의사항)
3. CTA (스와이프, 저장)
4. 해시태그 30개

---

### 8. PublisherAgent (김대리)

**역할:** Instagram 게시
**파일:** `agents/publisher.py`

| 항목 | 내용 |
|------|------|
| 입력 | 이미지, 캡션, 해시태그 |
| 출력 | Instagram 포스트 ID |
| API | Instagram Graph API, Cloudinary |
| 방식 | 10장 캐러셀 포스트 |

---

### 9. AnalyticsAgent (정분석)

**역할:** 성과 분석/추천
**파일:** `agents/analytics.py`

| 항목 | 내용 |
|------|------|
| 입력 | 포스트 인사이트 데이터 |
| 출력 | 분석 리포트, 다음 주제 추천 |
| 분석 항목 | 도달률, 인게이지먼트, 팔로워 증가 |

---

## Support Agents (5개)

파이프라인과 독립적으로 운영되는 보조 에이전트들.

---

### 10. SchedulerAgent (한스케줄)

**역할:** 콘텐츠 스케줄링
**파일:** `agents/scheduler.py`

| 항목 | 내용 |
|------|------|
| 핵심 기능 | 최적 포스팅 시간, 주간 스케줄, 큐 관리 |
| 최적 시간 | 평일 7-8시/12시/18-21시, 주말 9-11시/14-16시/20-21시 |

```python
from agents import SchedulerAgent
agent = SchedulerAgent()

# 주간 스케줄 생성
result = await agent.run({
    "action": "generate_schedule",
    "topics": ["cherry", "banana", "watermelon"],
    "posts_per_day": 1
})

# 큐에 추가
result = await agent.run({
    "action": "add_to_queue",
    "topic": "apple",
    "category": "fruit",
    "priority": 8
})

# 다음 포스팅 확인
result = await agent.run({"action": "get_next"})
```

Actions: `generate_schedule`, `add_to_queue`, `get_next`, `analyze`, `get_status`

---

### 11. MultiPlatformAgent (박멀티)

**역할:** 멀티 플랫폼 포스팅
**파일:** `agents/multi_platform.py`

| 항목 | 내용 |
|------|------|
| 지원 플랫폼 | Instagram, Facebook, Twitter, Threads, Pinterest, TikTok |
| 핵심 기능 | 콘텐츠 자동 최적화, 크로스 포스팅 |

플랫폼별 제한:
| Platform | Caption | Hashtags | Images |
|----------|---------|----------|--------|
| Instagram | 2200자 | 30개 | 10장 |
| Facebook | 63206자 | 30개 | 10장 |
| Twitter | 280자 | 10개 | 4장 |
| Threads | 500자 | 10개 | 10장 |
| Pinterest | 500자 | 20개 | 1장 |

```python
from agents import MultiPlatformAgent
agent = MultiPlatformAgent()

# 콘텐츠 최적화
result = await agent.run({
    "action": "adapt",
    "platform": "twitter",
    "content": {"caption": "...", "hashtags": [...], "images": [...]}
})

# 요구사항 검증
result = await agent.run({"action": "validate", "platform": "instagram", "content": {...}})
```

Actions: `cross_post`, `adapt`, `validate`, `status`

---

### 12. RetryAgent (이리트라이)

**역할:** 실패 자동 재시도
**파일:** `agents/retry.py`

| 항목 | 내용 |
|------|------|
| 실패 유형 | network, rate_limit, auth, validation, resource, timeout, unknown |
| 재시도 전략 | immediate, linear, exponential, fibonacci |
| 복구 판단 | 자동 (auth/validation은 재시도 불가) |

```python
from agents import RetryAgent
agent = RetryAgent()

# 실패 작업 등록
result = await agent.run({
    "action": "add",
    "task_id": "post_001",
    "task_type": "instagram_post",
    "error": "Connection timeout",
    "agent_name": "PublisherAgent"
})

# 대기 중인 작업 모두 재시도
result = await agent.run({"action": "process_all"})

# 통계 확인
result = await agent.run({"action": "stats"})
```

Actions: `add`, `retry`, `process_all`, `stats`, `list`, `clear`

---

### 13. TrendAgent (최트렌드)

**역할:** 트렌드 분석
**파일:** `agents/trend.py`

| 항목 | 내용 |
|------|------|
| 핵심 기능 | 계절 추천, 이벤트 대응, 해시태그 분석, 주간 계획 |
| 이벤트 | 14개 한국 기념일 자동 대응 |

```python
from agents import TrendAgent
agent = TrendAgent()

# 계절별 추천
result = await agent.run({"action": "seasonal"})

# 콘텐츠 추천 (점수 기반)
result = await agent.run({
    "action": "recommend",
    "topics": ["banana", "cherry", "watermelon", "salmon"],
    "count": 5
})

# 주간 계획 자동 생성
result = await agent.run({
    "action": "plan",
    "topics": ["banana", "cherry", "apple", "carrot", "chicken"]
})
```

Actions: `seasonal`, `events`, `hashtags`, `score`, `recommend`, `plan`, `hashtag_analysis`

---

### 14. TemplateAgent (김템플릿)

**역할:** 템플릿 관리
**파일:** `agents/template.py`

| 항목 | 내용 |
|------|------|
| 카테고리 | fruit, vegetable, meat, seafood, dairy, dangerous |
| A/B 변형 | A(기본), B(결론 먼저), C(주의점 강조) |
| 검증 | 슬라이드 수, 필수 필드, 텍스트 길이 |

```python
from agents import TemplateAgent
agent = TemplateAgent()

# 템플릿 생성
result = await agent.run({
    "action": "generate",
    "topic": "banana",
    "topic_kr": "바나나",
    "category": "fruit",
    "is_safe": True
})

# 텍스트 데이터 검증
result = await agent.run({
    "action": "validate",
    "text_data": [...]
})

# A/B 테스트 변형
result = await agent.run({
    "action": "ab_variation",
    "text_data": [...],
    "variation": "B"
})
```

Actions: `generate`, `validate`, `list`, `ab_variation`, `ab_analysis`, `save_template`, `get_style`

---

## Agent 개발 가이드

### 새 에이전트 추가 방법

1. `agents/` 에 파일 생성
2. `BaseAgent` 상속
3. `name` property, `execute` method 구현
4. `agents/__init__.py`에 등록
5. 테스트 작성

```python
from .base import BaseAgent, AgentResult

class MyNewAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "MyNewAgent"

    async def execute(self, input_data):
        action = input_data.get("action", "default")
        # 로직 구현
        return AgentResult(success=True, data={"result": "..."})
```

### BaseAgent 제공 기능

| 메서드 | 용도 |
|--------|------|
| `run(input_data)` | 메인 실행 (검증→전처리→실행→후처리) |
| `run_sync(input_data)` | 동기 실행 |
| `validate_input(data)` | 입력 검증 (오버라이드 가능) |
| `pre_execute(data)` | 전처리 (오버라이드 가능) |
| `post_execute(result)` | 후처리 (오버라이드 가능) |
| `log(message, level)` | 로깅 |
| `reset()` | 상태 초기화 |
| `get_last_result()` | 마지막 결과 조회 |

---

*Last Updated: 2026-01-23*
