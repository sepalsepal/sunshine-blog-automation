# 📦 Git 커밋 및 푸시

작업 완료 후 자동으로 커밋합니다.

## 커밋 규칙
- 자동 생성 커밋: `[auto] {작업내용} - {timestamp}`
- 수동 커밋: `[manual] {작업내용}`
- 긴급 수정: `[hotfix] {내용}`

## 실행 명령
```bash
cd /Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine

# 변경사항 확인
git status

# 스테이징
git add -A

# 커밋 (인자가 있으면 해당 메시지, 없으면 자동 생성)
if [ -n "$ARGUMENTS" ]; then
    git commit -m "[auto] $ARGUMENTS - $(date +%Y%m%d_%H%M%S)"
else
    git commit -m "[auto] 작업 완료 - $(date +%Y%m%d_%H%M%S)"
fi

# 상태 확인
git log --oneline -3
```

## 주의사항
- push는 수동으로 진행 (안전을 위해)
- 대용량 파일 (이미지 등)은 .gitignore 확인
- outputs/ 폴더는 기본적으로 제외됨
