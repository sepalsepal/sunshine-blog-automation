# 🔄 Ralph Wiggum 검증 루프 설정

Project Sunshine 파이프라인에 Ralph Wiggum 기법을 적용합니다.

## Ralph Wiggum이란?
"될 때까지 반복" - 실패해도 포기하지 않고 성공할 때까지 계속 시도하는 자동화 기법

## 설정

### 1. 플러그인 설치
```bash
claude plugin install @anthropic/ralph-wiggum
```

### 2. 프로젝트별 설정
```json
{
  "ralph-wiggum": {
    "maxIterations": 20,
    "completionPromise": "DONE",
    "retryDelay": 5000,
    "hooks": {
      "onIteration": "log",
      "onSuccess": "notify",
      "onMaxReached": "alert"
    }
  }
}
```

## 적용 시나리오

### 시나리오 1: 이미지 생성 검증
```
/ralph-loop:ralph-loop "
1. cherry 주제로 이미지 10장 생성
2. 각 이미지 품질 검증 (해상도, 텍스트 가독성)
3. 실패한 이미지 재생성
4. 모든 이미지가 품질 기준 통과하면 DONE
" --max-iterations 10
```

### 시나리오 2: 전체 파이프라인 실행
```
/ralph-loop:ralph-loop "
1. cherry 파이프라인 실행
2. 각 단계 검증:
   - 텍스트: 맞춤법, 팩트 체크
   - 이미지: 품질 검증
   - 캡션: 해시태그 중복 확인
3. 박과장 검수 점수 85점 이상이면 DONE
4. 미달 시 해당 단계 재실행
" --max-iterations 15 --completion-promise "검수 점수: 85"
```

### 시나리오 3: Instagram 게시 확인
```
/ralph-loop:ralph-loop "
1. Instagram Graph API로 게시
2. 게시 상태 확인 (API 응답)
3. 실제 Instagram에서 게시물 확인 (Puppeteer)
4. 게시 성공 확인되면 DONE
" --max-iterations 5
```

## 사용 명령어

### 루프 시작
```
/ralph-loop:ralph-loop "<프롬프트>" --completion-promise "DONE" --max-iterations 20
```

### 루프 취소
```
/ralph-loop:cancel-ralph
```

### 도움말
```
/ralph-loop:help
```

## 주의사항

1. **API 비용 주의**: 무한 루프 방지를 위해 max-iterations 설정 필수
2. **실제 게시 주의**: 테스트 시 --dry-run 사용
3. **completion-promise 명확히**: 성공 조건을 정확하게 설정
4. **로그 확인**: 각 반복의 결과를 logs/에 기록

## 연동 Hook (AgentStop)

`hooks.json`의 `AgentStop` hook과 연동되어:
- 파이프라인 완료 시 자동으로 검증 루프 실행
- 검증 실패 시 종료 차단 후 재시도
- 최대 반복 도달 시 수동 검토 알림
