#!/bin/bash
# auto_backup_github.sh - GitHub 자동 백업
# 사용법: crontab -e → 0 0 * * * /path/to/auto_backup_github.sh

cd /Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine

# 현재 시간
TIMESTAMP=$(date +%Y-%m-%d_%H:%M)

# 백업 대상 파일 확인
if [ -f "RULES.md" ] && [ -f "CLAUDE.md" ]; then
    # 변경사항 있으면 커밋
    if [ -n "$(git status --porcelain RULES.md CLAUDE.md scripts/)" ]; then
        git add RULES.md CLAUDE.md scripts/
        git commit -m "[AUTO-BACKUP] ${TIMESTAMP}"
        git push origin main
        echo "✅ GitHub 백업 완료: ${TIMESTAMP}"
    else
        echo "ℹ️ 변경사항 없음: ${TIMESTAMP}"
    fi
else
    echo "❌ 백업 대상 파일 없음"
    exit 1
fi
