# SunFlow 운영 매뉴얼

> 시스템 운영 및 유지보수 가이드

---

## 1. 일일 운영 체크리스트

### 오전 (09:00)
- [ ] 헬스체크 실행: `python core/utils/health_check.py`
- [ ] 커버 소스 처리 확인 (자동 실행됨)
- [ ] 텔레그램 알림 확인

### 오후 (18:00)
- [ ] 게시 스케줄 확인
- [ ] 콘텐츠 큐 확인: `python core/utils/content_queue.py status`
- [ ] 자동 게시 모니터링

### 야간 (22:00)
- [ ] 오늘 게시 결과 확인
- [ ] 통계 수집 확인
- [ ] 에러 로그 확인: `tail -50 config/logs/traces/*.log`

---

## 2. 주간 운영 체크리스트

### 월요일
- [ ] 주간 통계 리포트 생성
- [ ] A/B 테스트 결과 확인
- [ ] 백업 상태 확인: `python core/utils/backup_manager.py status`

### 금요일
- [ ] 다음 주 콘텐츠 큐 확인
- [ ] 커버 이미지 재고 확인
- [ ] 토큰 만료일 확인: `python core/utils/token_monitor.py status`

---

## 3. 시스템 명령어 모음

### 헬스체크
```bash
# 전체 상태 확인
python core/utils/health_check.py

# JSON 형식 출력
python core/utils/health_check.py --json
```

### 백업
```bash
# 수동 백업 생성
python core/utils/backup_manager.py create

# 백업 목록 확인
python core/utils/backup_manager.py list

# 백업 복원
python core/utils/backup_manager.py restore <backup_id>

# 자동 백업 실행
python core/utils/backup_manager.py auto
```

### 트레이스
```bash
# 최근 트레이스 목록
python core/utils/trace_manager.py list

# 특정 트레이스 상세
python core/utils/trace_manager.py show <trace_id>

# 테스트 트레이스 생성
python core/utils/trace_manager.py test
```

### 토큰 관리
```bash
# 토큰 상태 확인
python core/utils/token_monitor.py status

# 갱신 가이드 보기
python core/utils/token_monitor.py guide

# 만료일 설정 (60일 후)
python core/utils/token_monitor.py set-expiry 60
```

### 콘텐츠 큐
```bash
# 큐 상태 확인
python core/utils/content_queue.py status

# 다음 게시 콘텐츠 확인
python core/utils/content_queue.py next
```

### 커버 처리
```bash
# 상태 확인
bash services/scripts/install_cover_processor.sh status

# 즉시 실행
bash services/scripts/install_cover_processor.sh run

# 드라이런 테스트
bash services/scripts/install_cover_processor.sh test
```

---

## 4. 자동화 스케줄

| 시간 | 작업 | 담당 |
|------|------|------|
| 09:00 | 커버 소스 처리 | launchd (com.sunshine.cover) |
| 18:00 | 콘텐츠 자동 게시 | launchd (com.sunshine.publish) |
| 00:00 | 자동 백업 | launchd (com.sunshine.backup) |
| 매시간 | 통계 수집 | stats_collector_daemon.py |

### launchd 서비스 관리
```bash
# 서비스 목록 확인
launchctl list | grep sunshine

# 서비스 상태 확인
launchctl list com.sunshine.cover

# 서비스 중지
launchctl unload ~/Library/LaunchAgents/com.sunshine.cover.plist

# 서비스 시작
launchctl load ~/Library/LaunchAgents/com.sunshine.cover.plist
```

---

## 5. 로그 위치

| 로그 종류 | 경로 |
|----------|------|
| 트레이스 | `config/logs/traces/` |
| 커버 처리 | `config/logs/cover_processor_*.log` |
| 게시 결과 | `config/logs/publish_*.log` |
| 에러 | `config/logs/*_stderr.log` |

### 로그 확인 명령어
```bash
# 최근 에러 로그
tail -100 config/logs/*_stderr.log

# 실시간 로그 모니터링
tail -f config/logs/traces/trace_$(date +%Y%m%d).log

# 특정 Trace ID 검색
grep "SF-20260130-ABC123" config/logs/traces/*.log
```

---

## 6. 문제 해결 가이드

### 게시 실패 시
1. 에러 로그 확인: `tail -50 config/logs/*_stderr.log`
2. Trace ID로 추적: `python core/utils/trace_manager.py show <trace_id>`
3. 헬스체크 실행: `python core/utils/health_check.py`
4. 재시도: `python services/scripts/publish_content.py <topic> --retry`

### 토큰 만료 시
1. 상태 확인: `python core/utils/token_monitor.py status`
2. 갱신 가이드 확인: `python core/utils/token_monitor.py guide`
3. 토큰 갱신 후 .env 업데이트
4. 만료일 등록: `python core/utils/token_monitor.py set-expiry 60`

### 백업 복원 시
1. 백업 목록 확인: `python core/utils/backup_manager.py list`
2. 복원 실행: `python core/utils/backup_manager.py restore <backup_id>`
3. 서비스 재시작 (필요시)

---

## 7. 긴급 연락처

| 역할 | 담당 | 알림 채널 |
|------|------|----------|
| PD | - | 텔레그램 |
| 시스템 | 김부장 | 자동 알림 |
| 모니터링 | 대시보드 | Streamlit |

---

## 8. 버전 정보

- **문서 버전**: 1.0
- **최종 수정**: 2026-01-30
- **작성자**: 김부장
