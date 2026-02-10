# SunFlow 장애 대응 플레이북

> 장애 상황별 대응 절차

---

## 장애 등급 정의

| 등급 | 정의 | 대응 시간 | 예시 |
|:----:|------|:--------:|------|
| P0 | 서비스 중단 | 즉시 | 게시 완전 불가, 토큰 만료 |
| P1 | 주요 기능 장애 | 1시간 | 이미지 생성 실패, API 오류 |
| P2 | 부분 기능 장애 | 4시간 | 통계 수집 실패, 알림 오류 |
| P3 | 경미한 이슈 | 24시간 | UI 오류, 로그 누락 |

---

## P0: 서비스 중단

### 시나리오 1: Instagram 토큰 만료

**증상:**
- 게시 실패 (401 Unauthorized)
- API 호출 전체 실패

**진단:**
```bash
python core/utils/token_monitor.py status
```

**대응:**
1. 토큰 갱신 가이드 확인
   ```bash
   python core/utils/token_monitor.py guide
   ```

2. 새 토큰 발급 (Meta Developer Console)

3. .env 파일 업데이트
   ```bash
   vi .env
   # INSTAGRAM_ACCESS_TOKEN="새_토큰"
   ```

4. 토큰 만료일 등록
   ```bash
   python core/utils/token_monitor.py set-expiry 60
   ```

5. 게시 재시도
   ```bash
   python services/scripts/publish_content.py <topic> --retry
   ```

**예방:**
- 토큰 만료 60일 전 알림 활성화
- 주간 토큰 상태 확인

---

### 시나리오 2: Cloudinary 업로드 실패

**증상:**
- 이미지 업로드 실패
- CDN URL 생성 불가

**진단:**
```bash
python core/utils/health_check.py
# cloudinary 컴포넌트 확인
```

**대응:**
1. API 키 확인
   ```bash
   grep CLOUDINARY .env
   ```

2. 사용량 확인 (Cloudinary 콘솔)

3. 로컬 이미지 백업 확인
   ```bash
   ls -la content/images/<topic>/
   ```

4. 수동 업로드 시도
   ```bash
   python -c "from services.scripts.upload_cloudinary import upload; upload('<path>')"
   ```

**예방:**
- 사용량 모니터링
- 백업 CDN 고려

---

## P1: 주요 기능 장애

### 시나리오 3: 이미지 생성 실패 (FLUX.2 Pro)

**증상:**
- 이미지 생성 API 오류
- 타임아웃

**진단:**
```bash
# 최근 트레이스 확인
python core/utils/trace_manager.py list

# 에러 로그 확인
tail -50 config/logs/*_stderr.log
```

**대응:**
1. API 상태 확인 (fal.ai 상태 페이지)

2. 재시도 (자동 3회)
   ```bash
   python services/scripts/generate_images.py <topic> --retry
   ```

3. 대체 이미지 사용 (archive에서)
   ```bash
   ls content/images/<topic>/archive/
   ```

**예방:**
- 이미지 사전 생성
- 재시도 로직 활성화

---

### 시나리오 4: Instagram API Rate Limit

**증상:**
- 429 Too Many Requests
- 게시 지연

**진단:**
```bash
grep "429" config/logs/*.log
```

**대응:**
1. 대기 (자동)
   - RetryManager가 지수 백오프 적용
   - 5분 → 15분 → 30분

2. 수동 대기
   ```bash
   # 1시간 후 재시도
   sleep 3600 && python services/scripts/publish_content.py <topic>
   ```

3. 게시 스케줄 조정
   - 일일 게시 횟수 감소

**예방:**
- 일일 게시 1건 유지
- 댓글 응답 속도 제한

---

## P2: 부분 기능 장애

### 시나리오 5: 통계 수집 실패

**증상:**
- instagram_stats.json 미갱신
- 대시보드 데이터 오래됨

**진단:**
```bash
cat config/data/instagram_stats.json | head -20
# last_updated 확인
```

**대응:**
1. 수동 수집
   ```bash
   python services/scripts/instagram_stats_collector.py --force
   ```

2. 데몬 재시작
   ```bash
   python services/scripts/stats_collector_daemon.py restart
   ```

**예방:**
- 데몬 상태 모니터링
- 헬스체크에 포함

---

### 시나리오 6: 텔레그램 알림 실패

**증상:**
- 알림 미수신
- 봇 응답 없음

**진단:**
```bash
python core/utils/health_check.py
# telegram 컴포넌트 확인
```

**대응:**
1. 봇 토큰 확인
   ```bash
   grep TELEGRAM .env
   ```

2. 봇 재시작
   ```bash
   python services/scripts/telegram_bot.py
   ```

3. 테스트 메시지 전송
   ```bash
   python -c "
   from services.scripts.telegram_notifier import TelegramNotifier
   TelegramNotifier()._send_message('테스트')
   "
   ```

**예방:**
- 봇 상태 주기적 확인
- 대체 알림 채널 구성

---

## 공통 대응 절차

### 1. 장애 인지
```bash
# 헬스체크
python core/utils/health_check.py

# 최근 트레이스
python core/utils/trace_manager.py list
```

### 2. 로그 수집
```bash
# 에러 로그 수집
tail -200 config/logs/*_stderr.log > /tmp/error_$(date +%Y%m%d).log

# 트레이스 수집
cp config/logs/traces/SF-*.json /tmp/traces_$(date +%Y%m%d)/
```

### 3. 복구 후 검증
```bash
# 헬스체크 재실행
python core/utils/health_check.py

# 테스트 게시 (dry-run)
python services/scripts/publish_content.py test_topic --dry-run
```

### 4. 사후 조치
- 장애 원인 분석
- CLAUDE.md 실수 기록 업데이트
- 재발 방지책 수립

---

## 롤백 절차

### 설정 롤백
```bash
# 백업 목록 확인
python core/utils/backup_manager.py list

# 특정 시점으로 복원
python core/utils/backup_manager.py restore <backup_id>
```

### 코드 롤백
```bash
# 최근 커밋 확인
git log --oneline -10

# 특정 커밋으로 복원
git checkout <commit_hash> -- <file_path>
```

---

## 에스컬레이션

| 시간 | 조치 |
|------|------|
| 0분 | 자동 알림 (텔레그램) |
| 30분 | 재시도 3회 완료 |
| 1시간 | PD 알림 |
| 4시간 | 수동 개입 필요 |

---

## 체크리스트

### 장애 대응 시
- [ ] 헬스체크 실행
- [ ] 에러 로그 확인
- [ ] Trace ID 수집
- [ ] 복구 시도
- [ ] 검증 테스트
- [ ] 사후 분석

### 복구 완료 시
- [ ] 정상 동작 확인
- [ ] 대기 중 작업 처리
- [ ] 알림 전송
- [ ] 문서화

---

**문서 버전**: 1.0
**최종 수정**: 2026-01-30
**작성자**: 김부장
