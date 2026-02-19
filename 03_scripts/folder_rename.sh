#!/bin/bash
# 폴더명 정리 - 상태 접미사 제거
# 옵션 D' 실행

cd /Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine/content/images

echo "=== 폴더명 정리 시작 ==="
echo ""

count=0

for dir in */; do
  # 슬래시 제거
  dirname="${dir%/}"

  # _published 또는 _제작완료 제거
  newname=$(echo "$dirname" | sed 's/_published$//' | sed 's/_제작완료$//')

  if [ "$dirname" != "$newname" ]; then
    echo "  $dirname → $newname"
    mv "$dirname" "$newname"
    count=$((count + 1))
  fi
done

echo ""
echo "=== 완료: ${count}개 폴더 리네이밍 ==="
