# SunFlow 플랫폼별 실패 허용 정책

> **목적:** 크로스 포스팅 시 부분 실패 처리 방침 명문화
> **Owner:** 김대리 (업로드/게시)
> **Review Cycle:** 분기 1회
> **Last Updated:** 2026-01-30

---

## 1. 플랫폼 우선순위

| 순위 | 플랫폼 | 역할 | 실패 시 영향 |
|:----:|--------|------|:------------:|
| 1 | **Instagram** | 메인 채널, 매출 창출 | 치명적 (P0) |
| 2 | X (Twitter) | 트래픽 유입, 실시간 정보 | 중요 (P1) |
| 3 | Threads | 커뮤니티, 대화형 | 낮음 (P2) |
| 4 | YouTube | 장기 자산 (향후) | 낮음 (P2) |

---

## 2. 실패 허용 정책

### 2.1 기본 원칙

```
Instagram 성공 = 전체 성공으로 간주
Instagram 실패 = 전체 실패 (모든 플랫폼 게시 중단)
```

### 2.2 시나리오별 처리

| 시나리오 | Instagram | X | Threads | 처리 방침 |
|----------|:---------:|:-:|:-------:|-----------|
| A | ✅ | ✅ | ✅ | 완전 성공 |
| B | ✅ | ✅ | ❌ | **부분 성공** - 계속 진행, Threads 로그만 |
| C | ✅ | ❌ | ✅ | **부분 성공** - 계속 진행, X 로그만 |
| D | ✅ | ❌ | ❌ | **부분 성공** - Instagram만 성공으로 처리 |
| E | ❌ | - | - | **전체 실패** - 즉시 중단, 재시도 |

### 2.3 부분 성공 처리 규칙

```python
# 부분 성공 판정 로직
def evaluate_cross_post_result(results: Dict[Platform, CrossPostResult]) -> str:
    instagram_success = results.get(Platform.INSTAGRAM, {}).success

    if not instagram_success:
        return "FAILURE"  # 전체 실패

    other_failures = [p for p, r in results.items()
                      if p != Platform.INSTAGRAM and not r.success]

    if not other_failures:
        return "SUCCESS"  # 완전 성공
    else:
        return "PARTIAL"  # 부분 성공
```

---

## 3. 플랫폼별 재시도 정책

### 3.1 Instagram (메인)

| 항목 | 값 |
|------|-----|
| 최대 재시도 | 3회 |
| 재시도 간격 | 30초, 60초, 120초 (지수 백오프) |
| 서킷 브레이커 | failure_threshold=3, recovery_timeout=300초 |
| 실패 시 조치 | 텔레그램 알림 → 수동 게시 |

### 3.2 X (Twitter)

| 항목 | 값 |
|------|-----|
| 최대 재시도 | 2회 |
| 재시도 간격 | 10초, 30초 |
| 서킷 브레이커 | failure_threshold=5, recovery_timeout=180초 |
| 실패 시 조치 | 로그 기록, 다음 게시 시 재시도 |

### 3.3 Threads

| 항목 | 값 |
|------|-----|
| 최대 재시도 | 1회 |
| 재시도 간격 | 10초 |
| 서킷 브레이커 | 없음 (Instagram 토큰 공유) |
| 실패 시 조치 | 로그 기록만, 별도 알림 없음 |

---

## 4. 서킷 브레이커 연동

### 4.1 회로 상태별 동작

| 회로 상태 | Instagram | X | Threads |
|-----------|:---------:|:-:|:-------:|
| CLOSED | 정상 게시 | 정상 게시 | 정상 게시 |
| OPEN | ❌ 게시 중단, 즉시 알림 | ⏸️ 스킵, 로그 | ⏸️ 스킵, 로그 |
| HALF_OPEN | 테스트 게시 1회 | 테스트 게시 1회 | 테스트 게시 1회 |

### 4.2 회로 설정

```python
CIRCUITS = {
    "instagram": CircuitBreaker(
        name="instagram",
        failure_threshold=3,      # 3회 실패 시 OPEN
        recovery_timeout=300,     # 5분 후 HALF_OPEN
        half_open_max_calls=1     # 테스트 1회
    ),
    "x": CircuitBreaker(
        name="x",
        failure_threshold=5,      # 5회 실패 시 OPEN
        recovery_timeout=180,     # 3분 후 HALF_OPEN
        half_open_max_calls=2
    ),
    "threads": CircuitBreaker(
        name="threads",
        failure_threshold=5,
        recovery_timeout=120,     # 2분 후 HALF_OPEN
        half_open_max_calls=2
    ),
}
```

### 4.3 서킷 브레이커 작동 조건 (구체적)

| 플랫폼 | OPEN 조건 | 예시 |
|--------|-----------|------|
| Instagram | 10분 내 3회 연속 4xx/5xx 응답 | 토큰 만료, Rate Limit |
| Instagram | 10분 내 3회 연속 타임아웃 (30초+) | API 지연 |
| X | 10분 내 5회 연속 실패 | 인증 오류 |
| Threads | 10분 내 5회 연속 실패 | API 오류 |

**OPEN 시 자동 동작:**
- Instagram OPEN → **전체 게시 파이프라인 일시 중지** + 텔레그램 알림
- X/Threads OPEN → 해당 플랫폼만 스킵, Instagram은 정상 진행

**수동 리셋:**
```bash
python3 core/utils/circuit_breaker.py reset instagram
```

---

## 5. 알림 정책

### 5.1 알림 우선순위

| 상황 | 알림 채널 | 즉시 알림 |
|------|-----------|:---------:|
| Instagram 실패 | 텔레그램 + 로그 | ✅ 즉시 |
| X 3회 연속 실패 | 텔레그램 | ✅ 즉시 |
| Threads 실패 | 로그만 | ❌ |
| 부분 성공 | 텔레그램 (요약) | 🕐 일일 리포트 |

### 5.2 알림 메시지 템플릿

**완전 성공:**
```
✅ 크로스 포스팅 완료
📌 주제: {topic_kr}
- Instagram: ✅ {post_url}
- X: ✅ {x_url}
- Threads: ✅ {threads_url}
```

**부분 성공:**
```
⚠️ 크로스 포스팅 부분 성공
📌 주제: {topic_kr}
- Instagram: ✅ {post_url}
- X: ❌ {error}
- Threads: ✅ {threads_url}

※ Instagram 성공으로 처리됨
```

**전체 실패:**
```
🚨 게시 실패
📌 주제: {topic_kr}
- Instagram: ❌ {error}

⚠️ 수동 조치 필요
```

---

## 6. 실패 복구 절차

### 6.1 Instagram 실패 시

```
1. 자동 재시도 3회
2. 재시도 실패 → 텔레그램 알림
3. 서킷 OPEN → 5분 대기
4. HALF_OPEN → 테스트 게시
5. 계속 실패 → 수동 게시 (웹/앱)
6. 원인 분석 → 에러 집계 기록
```

### 6.2 X/Threads 실패 시

```
1. 자동 재시도 (X: 2회, Threads: 1회)
2. 재시도 실패 → 로그 기록
3. Instagram 성공했으면 → 부분 성공 처리
4. 다음 게시 시 자동 재시도 (서킷 CLOSED라면)
5. 연속 실패 시 → 일일 리포트에 포함
```

---

## 7. 모니터링 지표

### 7.1 일일 모니터링

| 지표 | 목표 | 경고 임계값 |
|------|:----:|:----------:|
| Instagram 성공률 | 98%+ | 95% 미만 |
| X 성공률 | 90%+ | 80% 미만 |
| Threads 성공률 | 85%+ | 70% 미만 |
| 크로스 포스팅 완전 성공률 | 85%+ | 75% 미만 |

### 7.2 주간 리포트 항목

```
- 플랫폼별 게시 성공/실패 건수
- 부분 성공 건수 및 원인
- 서킷 OPEN 발생 횟수
- 평균 복구 시간 (MTTR)
- 에러 유형별 집계
```

---

## 8. 예외 상황 처리

### 8.1 API 점검 시간

| 플랫폼 | 알려진 점검 시간 | 대응 |
|--------|-----------------|------|
| Instagram | 화요일 새벽 2~4시 (미국 시간) | 해당 시간 게시 스킵 |
| X | 불규칙 | 서킷 브레이커 의존 |
| Threads | Instagram과 동일 | Instagram과 동일 |

### 8.2 Rate Limit 초과

| 플랫폼 | Rate Limit | 대응 |
|--------|------------|------|
| Instagram | 일 25회 게시 | 큐잉 후 다음 날 게시 |
| X | 시간당 50회 | 1시간 대기 후 재시도 |
| Threads | 일 50회 | 큐잉 후 다음 날 게시 |

---

## 9. 의사결정 플로우차트

```
게시 요청
    │
    ▼
Instagram 게시 시도
    │
    ├─ 성공 ──────────────┐
    │                     │
    ▼                     ▼
실패                   X 게시 시도
    │                     │
    ▼                     ├─ 성공 ─┐
재시도 (3회)              │        │
    │                     ▼        ▼
    ├─ 성공 → X 게시      실패    Threads 게시
    │                     │        │
    ▼                     ▼        ├─ 성공 → 완전 성공
전체 실패              로그 기록   │
알림 발송              Threads →   ▼
수동 조치                │       실패
                        ▼        │
                    부분 성공     ▼
                    (X 제외)   부분 성공
                              (Threads 제외)
```

---

## 서명

- [ ] **김대리**: 실패 정책 확인
- [ ] **김부장**: 승인

**승인일:** _______________

---

*SunFlow Platform Failure Policy v1.0*
*작성일: 2026-01-30*
