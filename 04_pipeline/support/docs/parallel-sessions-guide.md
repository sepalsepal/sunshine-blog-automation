# 🚀 Project Sunshine 병렬 세션 운영 가이드

Boris Cherny의 "5~10개 세션 병렬 운영" 전략을 적용합니다.

## 병렬 세션 구조

### 터미널 세션 (로컬)
```
Tab 1: 🎨 이미지 생성 (이작가)
Tab 2: 📝 텍스트 작성 (김작가)
Tab 3: ✅ 검증/테스트
Tab 4: 🔧 버그 수정
Tab 5: 📊 분석/모니터링
```

### 웹 세션 (claude.ai/code)
```
Session 1: 새 주제 기획
Session 2: 프롬프트 최적화
Session 3: 코드 리뷰
Session 4: 문서화
Session 5: 실험/테스트
```

## 운영 방법

### 1. 터미널 세션 설정
```bash
# iTerm2 / Terminal에서 탭 생성
# Cmd+T로 새 탭, 각 탭에 번호 지정

# Tab 1: 이미지 생성
cd ~/Desktop/Jun_AI/Dog_Contents/project_sunshine
claude

# Tab 2: 텍스트 작성
cd ~/Desktop/Jun_AI/Dog_Contents/project_sunshine
claude

# ... 반복
```

### 2. 시스템 알림 설정
Claude가 입력을 기다릴 때 알림을 받으려면:

**macOS:**
```bash
# Terminal 알림 활성화
defaults write com.apple.Terminal FocusFollowsMouse -bool true

# 또는 iTerm2 설정에서:
# Preferences > Profiles > Terminal > Notifications
```

### 3. 세션 간 작업 이동 (Teleport)
```bash
# 로컬 세션을 웹으로 이동
claude session export --format web

# 웹 세션을 로컬로 가져오기
claude session import --from-web
```

## 작업 분배 예시

### 새 주제 (grape) 추가 시

| 세션 | 작업 | 상태 |
|------|------|------|
| Tab 1 | grape 이미지 생성 | 🔄 진행중 |
| Tab 2 | grape 텍스트 작성 | 🔄 진행중 |
| Tab 3 | cherry 검증 | ✅ 완료 |
| Tab 4 | banana 버그 수정 | ⏸️ 대기 |
| Tab 5 | 전체 모니터링 | 👁️ 감시중 |
| Web 1 | mango 기획 | 🔄 진행중 |
| Web 2 | 프롬프트 실험 | 🔬 실험중 |

### 긴급 수정 시
1. Tab 4에서 버그 수정 작업
2. Tab 3에서 수정 검증
3. 완료 후 Tab 5에서 전체 상태 확인

## 모바일 활용 (iPhone Claude 앱)

### 아침 루틴
```
1. 전날 게시물 성과 확인 요청
2. 오늘 게시 주제 추천 요청
3. 나중에 데스크톱에서 결과 확인
```

### 이동 중
```
1. 새 주제 아이디어 브레인스토밍
2. 캡션 초안 작성
3. 해시태그 리서치
```

## 권장 워크플로우

### Daily Routine
```
09:00 - 모바일에서 오늘 작업 계획 시작
10:00 - 데스크톱 Tab 1-2에서 콘텐츠 생성
12:00 - Tab 3에서 오전 작업 검증
14:00 - 웹 세션에서 다음 주제 기획
16:00 - Tab 4-5에서 수정/모니터링
18:00 - 최종 검증 후 게시 (Tab 1)
```

### Weekly Routine
```
월: 주간 계획 수립 (웹 세션)
화-목: 콘텐츠 생성 (터미널 5개 병렬)
금: 검증 및 예약 게시 설정
토-일: 성과 분석 및 다음 주 준비
```

## 세션 상태 모니터링

### 대시보드 명령어
```bash
# 모든 세션 상태 확인
claude session list

# 특정 세션 상태 확인
claude session status --tab 1

# 대기 중인 세션 알림
claude session notify --waiting
```

## 주의사항

1. **세션 충돌 방지**: 같은 파일을 여러 세션에서 동시 수정 금지
2. **리소스 관리**: 5개 이상 세션 시 메모리 모니터링
3. **API 한도**: 병렬 실행 시 API 호출 속도 제한 주의
4. **컨텍스트 유지**: 각 세션의 목적을 명확히 구분

## 팁

> "한 세션을 완벽하게 운영이 아니라 여러 세션을 동시에 굴리는 운영" - Boris Cherny

- 각 세션에 명확한 역할 부여
- 작업 완료 시 다른 세션으로 이동
- 대기 시간을 다른 세션 작업으로 활용
