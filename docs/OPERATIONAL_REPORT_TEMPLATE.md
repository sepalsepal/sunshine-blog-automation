# SunFlow 30일 실운영 리포트

> **기간:** {START_DATE} ~ {END_DATE}
> **작성일:** {REPORT_DATE}
> **작성자:** 김부장 (자동 생성)
> **버전:** v1.3

---

## Executive Summary

| 지표 | 목표 | 실제 | 상태 |
|------|:----:|:----:|:----:|
| 가동률 | 98%+ | {UPTIME}% | {UPTIME_STATUS} |
| 게시 성공률 | 95%+ | {PUBLISH_SUCCESS}% | {PUBLISH_STATUS} |
| 평균 참여율 | 10%+ | {ENGAGEMENT}% | {ENGAGEMENT_STATUS} |
| 팔로워 증가 | +500 | {FOLLOWER_GROWTH} | {FOLLOWER_STATUS} |

**종합 판정:** {OVERALL_STATUS}

---

## 1. 시스템 안정성

### 1.1 가동률 (Uptime)

```
일간 가동률 추이 (30일)
┌────────────────────────────────────────────────────────────┐
│ {UPTIME_CHART}                                              │
│                                                             │
│ ████████████████████████████ 98.5%                         │
└────────────────────────────────────────────────────────────┘
```

| 주차 | 가동률 | 헬스체크 성공 | 헬스체크 실패 |
|:----:|:------:|:------------:|:------------:|
| Week 1 | {W1_UPTIME}% | {W1_SUCCESS} | {W1_FAIL} |
| Week 2 | {W2_UPTIME}% | {W2_SUCCESS} | {W2_FAIL} |
| Week 3 | {W3_UPTIME}% | {W3_SUCCESS} | {W3_FAIL} |
| Week 4 | {W4_UPTIME}% | {W4_SUCCESS} | {W4_FAIL} |
| **합계** | **{TOTAL_UPTIME}%** | **{TOTAL_SUCCESS}** | **{TOTAL_FAIL}** |

### 1.2 서킷 브레이커 이벤트

| 회로 | OPEN 횟수 | 평균 복구 시간 | 최장 복구 시간 |
|------|:---------:|:-------------:|:-------------:|
| instagram | {IG_OPEN} | {IG_MTTR} | {IG_MAX} |
| cloudinary | {CD_OPEN} | {CD_MTTR} | {CD_MAX} |
| fal_ai | {FAL_OPEN} | {FAL_MTTR} | {FAL_MAX} |
| telegram | {TG_OPEN} | {TG_MTTR} | {TG_MAX} |

### 1.3 백업 현황

| 항목 | 값 |
|------|-----|
| 총 백업 횟수 | {BACKUP_COUNT} |
| 성공률 | {BACKUP_SUCCESS}% |
| 총 용량 | {BACKUP_SIZE} |
| 최근 백업 | {LAST_BACKUP} |

---

## 2. 게시 성과

### 2.1 게시 현황

| 주차 | 시도 | 성공 | 실패 | 성공률 |
|:----:|:----:|:----:|:----:|:------:|
| Week 1 | {W1_ATTEMPT} | {W1_PUB_SUCCESS} | {W1_PUB_FAIL} | {W1_PUB_RATE}% |
| Week 2 | {W2_ATTEMPT} | {W2_PUB_SUCCESS} | {W2_PUB_FAIL} | {W2_PUB_RATE}% |
| Week 3 | {W3_ATTEMPT} | {W3_PUB_SUCCESS} | {W3_PUB_FAIL} | {W3_PUB_RATE}% |
| Week 4 | {W4_ATTEMPT} | {W4_PUB_SUCCESS} | {W4_PUB_FAIL} | {W4_PUB_RATE}% |
| **합계** | **{TOTAL_ATTEMPT}** | **{TOTAL_PUB_SUCCESS}** | **{TOTAL_PUB_FAIL}** | **{TOTAL_PUB_RATE}%** |

### 2.2 재시도 통계

| 지표 | 값 |
|------|-----|
| 평균 재시도 횟수 | {AVG_RETRY} |
| 최대 재시도 횟수 | {MAX_RETRY} |
| 1회 성공률 | {FIRST_TRY_SUCCESS}% |
| 재시도 후 성공률 | {RETRY_SUCCESS}% |

### 2.3 게시 시간 분석

| 시간대 | 게시 수 | 평균 참여율 | 권장 |
|--------|:-------:|:----------:|:----:|
| 06-09시 | {T1_COUNT} | {T1_ENG}% | {T1_REC} |
| 09-12시 | {T2_COUNT} | {T2_ENG}% | {T2_REC} |
| 12-15시 | {T3_COUNT} | {T3_ENG}% | {T3_REC} |
| 15-18시 | {T4_COUNT} | {T4_ENG}% | {T4_REC} |
| 18-21시 | {T5_COUNT} | {T5_ENG}% | {T5_REC} |
| 21-24시 | {T6_COUNT} | {T6_ENG}% | {T6_REC} |

---

## 3. Instagram 성과

### 3.1 팔로워 추이

```
팔로워 증가 추이 (30일)
┌────────────────────────────────────────────────────────────┐
│ {FOLLOWER_CHART}                                            │
│                                                             │
│ 시작: {START_FOLLOWERS} → 종료: {END_FOLLOWERS} (+{GROWTH}) │
└────────────────────────────────────────────────────────────┘
```

| 주차 | 시작 | 종료 | 증감 | 일평균 |
|:----:|:----:|:----:|:----:|:------:|
| Week 1 | {W1_F_START} | {W1_F_END} | {W1_F_CHANGE} | {W1_F_AVG} |
| Week 2 | {W2_F_START} | {W2_F_END} | {W2_F_CHANGE} | {W2_F_AVG} |
| Week 3 | {W3_F_START} | {W3_F_END} | {W3_F_CHANGE} | {W3_F_AVG} |
| Week 4 | {W4_F_START} | {W4_F_END} | {W4_F_CHANGE} | {W4_F_AVG} |

### 3.2 참여율 분석

| 지표 | 평균 | 최고 | 최저 |
|------|:----:|:----:|:----:|
| 좋아요 | {AVG_LIKES} | {MAX_LIKES} | {MIN_LIKES} |
| 댓글 | {AVG_COMMENTS} | {MAX_COMMENTS} | {MIN_COMMENTS} |
| 저장 | {AVG_SAVES} | {MAX_SAVES} | {MIN_SAVES} |
| 공유 | {AVG_SHARES} | {MAX_SHARES} | {MIN_SHARES} |
| **참여율** | **{AVG_ENGAGEMENT}%** | **{MAX_ENGAGEMENT}%** | **{MIN_ENGAGEMENT}%** |

### 3.3 콘텐츠 성과 TOP 5

| 순위 | 주제 | 게시일 | 좋아요 | 저장 | 참여율 |
|:----:|------|--------|:------:|:----:|:------:|
| 1 | {TOP1_TOPIC} | {TOP1_DATE} | {TOP1_LIKES} | {TOP1_SAVES} | {TOP1_ENG}% |
| 2 | {TOP2_TOPIC} | {TOP2_DATE} | {TOP2_LIKES} | {TOP2_SAVES} | {TOP2_ENG}% |
| 3 | {TOP3_TOPIC} | {TOP3_DATE} | {TOP3_LIKES} | {TOP3_SAVES} | {TOP3_ENG}% |
| 4 | {TOP4_TOPIC} | {TOP4_DATE} | {TOP4_LIKES} | {TOP4_SAVES} | {TOP4_ENG}% |
| 5 | {TOP5_TOPIC} | {TOP5_DATE} | {TOP5_LIKES} | {TOP5_SAVES} | {TOP5_ENG}% |

---

## 4. 비용 분석

### 4.1 API 사용량

| 서비스 | 호출 수 | 비용 | 단가 |
|--------|:-------:|:----:|:----:|
| fal.ai (FLUX.2 Pro) | {FAL_CALLS} | ${FAL_COST} | ${FAL_UNIT}/img |
| Cloudinary | {CD_CALLS} | ${CD_COST} | - |
| Instagram Graph API | {IG_CALLS} | $0 | - |
| Telegram | {TG_CALLS} | $0 | - |
| **합계** | - | **${TOTAL_COST}** | - |

### 4.2 콘텐츠당 비용

| 지표 | 값 |
|------|-----|
| 총 제작 콘텐츠 | {TOTAL_CONTENT}개 |
| 총 비용 | ${TOTAL_COST} |
| **콘텐츠당 비용** | **${COST_PER_CONTENT}** |
| 목표 (콘텐츠당 $0.50 이하) | {COST_STATUS} |

---

## 5. 에러 분석

### 5.1 에러 유형별 집계

| 유형 | 건수 | 비율 | 주요 원인 |
|------|:----:|:----:|----------|
| API 오류 | {ERR_API} | {ERR_API_PCT}% | {ERR_API_CAUSE} |
| 네트워크 | {ERR_NET} | {ERR_NET_PCT}% | {ERR_NET_CAUSE} |
| 인증 | {ERR_AUTH} | {ERR_AUTH_PCT}% | {ERR_AUTH_CAUSE} |
| 데이터 | {ERR_DATA} | {ERR_DATA_PCT}% | {ERR_DATA_CAUSE} |
| 기타 | {ERR_OTHER} | {ERR_OTHER_PCT}% | {ERR_OTHER_CAUSE} |

### 5.2 평균 복구 시간 (MTTR)

| 심각도 | 건수 | 평균 MTTR | 목표 | 상태 |
|--------|:----:|:---------:|:----:|:----:|
| P0 (치명) | {P0_COUNT} | {P0_MTTR} | 30분 | {P0_STATUS} |
| P1 (높음) | {P1_COUNT} | {P1_MTTR} | 2시간 | {P1_STATUS} |
| P2 (중간) | {P2_COUNT} | {P2_MTTR} | 24시간 | {P2_STATUS} |
| P3 (낮음) | {P3_COUNT} | {P3_MTTR} | 72시간 | {P3_STATUS} |

---

## 6. 품질 게이트 통과율

| 게이트 | 통과 | 실패 | 통과율 | 목표 |
|--------|:----:|:----:|:------:|:----:|
| G1 (글 검수) | {G1_PASS} | {G1_FAIL} | {G1_RATE}% | 90%+ |
| G2 (이미지 검수) | {G2_PASS} | {G2_FAIL} | {G2_RATE}% | 85%+ |
| G3 (합성 검수) | {G3_PASS} | {G3_FAIL} | {G3_RATE}% | 85%+ |

---

## 7. 결론 및 권장사항

### 7.1 달성 현황

| 목표 | 기준 | 실제 | 달성 |
|------|:----:|:----:|:----:|
| 시스템 가동률 | 98%+ | {UPTIME}% | {UPTIME_ACHIEVED} |
| 게시 성공률 | 95%+ | {PUBLISH_SUCCESS}% | {PUBLISH_ACHIEVED} |
| 참여율 | 10%+ | {ENGAGEMENT}% | {ENGAGEMENT_ACHIEVED} |
| 콘텐츠당 비용 | $0.50 이하 | ${COST_PER_CONTENT} | {COST_ACHIEVED} |
| P0 장애 | 0건 | {P0_COUNT}건 | {P0_ACHIEVED} |

### 7.2 권장사항

1. **{RECOMMENDATION_1}**
2. **{RECOMMENDATION_2}**
3. **{RECOMMENDATION_3}**

### 7.3 다음 30일 목표

| 항목 | 현재 | 다음 목표 |
|------|:----:|:---------:|
| 팔로워 | {END_FOLLOWERS} | {NEXT_FOLLOWER_TARGET} |
| 일평균 참여율 | {AVG_ENGAGEMENT}% | {NEXT_ENGAGEMENT_TARGET}% |
| 게시 성공률 | {PUBLISH_SUCCESS}% | 98%+ |

---

## 서명

- [ ] **김부장**: 리포트 검토
- [ ] **PD**: 최종 승인

**승인일:** _______________

---

*SunFlow 30일 실운영 리포트*
*자동 생성: {REPORT_DATE}*
