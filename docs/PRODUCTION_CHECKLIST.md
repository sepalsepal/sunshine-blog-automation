# SunFlow Production Checklist

> **목적:** SunFlow v1.1을 건드리지 않아도 되는 완성 상태 확인
> **기준:** 모든 항목 체크 완료 시 Production Ready

---

## 1. 핵심 기능 (Must Have)

### 콘텐츠 생성
- [x] AI 이미지 생성 (FLUX.2 Pro)
- [x] PPT 템플릿 텍스트 오버레이
- [x] 캡션 자동 생성
- [x] 해시태그 자동 생성
- [x] 표지 프롬프트 v2.0 (CONTAINER RULE)

### 게시 시스템
- [x] Instagram Graph API 연동
- [x] Cloudinary CDN 업로드
- [x] 캐러셀 게시
- [x] 게시 이력 추적

### 품질 관리
- [x] G1 게이트 (글 검수)
- [x] G2 게이트 (이미지 검수)
- [x] G3 게이트 (합성 검수)
- [x] AI 표기 자동 추가

---

## 2. 자동화 (Automation)

### 스케줄링
- [x] 오전 9시 커버 소스 처리
- [x] 오후 6시 자동 게시
- [x] 자정 자동 백업
- [x] launchd 서비스 등록

### 큐 관리
- [x] ContentQueue 우선순위 관리
- [x] 자동 게시 스케줄러
- [x] 실패 시 자동 재시도 (3회)

---

## 3. 운영 안정성 (Reliability)

### 모니터링
- [x] 헬스체크 (7개 컴포넌트)
- [x] Trace ID 추적 (SF-YYYYMMDD-XXXXXX)
- [x] 에러 집계 (일일/주간)
- [x] Streamlit 대시보드

### 장애 대응
- [x] 서킷 브레이커 (4개 회로)
- [x] 롤백 포인트 관리
- [x] 자동 백업 (30일 보존)
- [x] 토큰 만료 60일 전 알림

### 알림
- [x] 텔레그램 봇 연동
- [x] 게시 성공/실패 알림
- [x] 장애 알림

---

## 4. 문서화 (Documentation)

### 운영 문서
- [x] SUNFLOW.md (서비스 개요)
- [x] OPERATIONS.md (운영 매뉴얼)
- [x] PLAYBOOK.md (장애 대응)
- [x] CLAUDE.md (개발 규칙)
- [x] PERFORMANCE_CRITERIA.md (성과 기준 정의)
- [x] PLATFORM_FAILURE_POLICY.md (플랫폼 실패 정책)

### 전략 문서
- [x] REVENUE_STRATEGY.md (매출 전략)
- [x] 수익화 로드맵 (Phase 1~4)
- [x] PPL 전략
- [x] PPL_PREREQUISITES.md (PPL/스폰서십 최소 조건)

### 콘텐츠 제작 문서
- [x] PROMPT_GUIDE_v2.md (표지 이미지 제작)

---

## 5. 확장 준비 (Expansion Ready)

### 멀티플랫폼
- [x] multi_platform.py 모듈
- [x] X (Twitter) 어댑터
- [x] Threads 어댑터
- [x] 콘텐츠 자동 변환

### 수익화
- [x] 제휴 링크 구조
- [x] PPL 프롬프트 삽입 체계
- [x] 광고 표기 자동화

---

## 6. 보안 (Security)

### 인증
- [x] API 키 .env 분리
- [x] 토큰 만료 모니터링
- [x] 시크릿 노출 방지

### 계정 보호
- [x] Rate Limit 준수
- [x] 일일 게시 제한
- [x] 댓글 응답 제한 (50/일)

---

## 7. 테스트 (Testing)

### 기능 테스트
- [x] 헬스체크 통과
- [x] 백업/복원 테스트
- [x] 트레이스 생성 테스트
- [x] 서킷 브레이커 테스트

### 통합 테스트
- [ ] 전체 파이프라인 dry-run
- [ ] 멀티플랫폼 테스트 게시

---

## 최종 확인

### 실행 명령어 (모두 성공해야 함)

```bash
# 1. 헬스체크
python3 core/utils/health_check.py
# 예상: Overall Status: HEALTHY

# 2. 서킷 브레이커
python3 core/utils/circuit_breaker.py status
# 예상: 4/4 CLOSED

# 3. 백업 상태
python3 core/utils/backup_manager.py status
# 예상: 백업 1개 이상

# 4. 토큰 상태
python3 core/utils/token_monitor.py status
# 예상: 정상 (60일 남음)

# 5. 멀티플랫폼 상태
python3 core/utils/multi_platform.py status
# 예상: 설정 상태 표시
```

### Production Ready 선언 조건

```
□ 위 체크리스트 95% 이상 완료
□ 헬스체크 HEALTHY
□ 백업 1회 이상 성공
□ 테스트 게시 성공 (dry-run)
□ 문서 10개 이상 완성 (현재 11개 ✅)
```

---

## 서명

- [ ] **김부장**: Production Ready 승인
- [ ] **PD**: 최종 확인

**승인일:** _______________

---

*SunFlow v1.2 Production Checklist*
*작성일: 2026-01-30*
*Updated: v1.2 - 비즈니스 기준 문서 추가*
