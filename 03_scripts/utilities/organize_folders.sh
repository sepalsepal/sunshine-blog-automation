#!/bin/bash
# organize_folders.sh
# 콘텐츠 폴더 구조 정리 스크립트 (v8.2)
# 작성: 최기술 대리
# 지시: 김부장 마스터 지시서 Part 2

set -e

cd "$(dirname "$0")/.."
ROOT=$(pwd)
OUTPUTS="$ROOT/outputs"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📁 콘텐츠 폴더 구조 정리 (v8.2)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 정리할 콘텐츠 목록
CONTENTS="strawberry apple pineapple cherries blueberry carrot pumpkin banana broccoli"

for content in $CONTENTS; do
  echo "📦 $content 정리 중..."

  # 1. _final 폴더 생성
  mkdir -p "$OUTPUTS/${content}_final"
  echo "   ✅ ${content}_final/ 생성"

  # 2. _temp 폴더 생성
  mkdir -p "$OUTPUTS/${content}_temp"
  mkdir -p "$OUTPUTS/${content}_temp/rejected"
  echo "   ✅ ${content}_temp/ 생성"

  # 3. 기존 버전 폴더들을 temp로 이동
  for old_folder in "$OUTPUTS/${content}_v"*; do
    if [ -d "$old_folder" ]; then
      version=$(basename "$old_folder" | sed "s/${content}_//")
      if [ ! -d "$OUTPUTS/${content}_temp/$version" ]; then
        mv "$old_folder" "$OUTPUTS/${content}_temp/$version"
        echo "   📦 ${content}_${version} → ${content}_temp/${version}"
      else
        echo "   ⚠️  ${content}_temp/${version} 이미 존재, 스킵"
      fi
    fi
  done

  # 4. 기존 _final 폴더 내용을 새 구조로 복사 (있는 경우)
  # broccoli_v8_final 같은 형태가 있으면 처리
  for final_folder in "$OUTPUTS/${content}_v"*"_final"; do
    if [ -d "$final_folder" ]; then
      echo "   📋 ${final_folder} 에서 최종 파일 복사..."
      # 최종 렌더링된 파일만 복사 (broccoli_0X_*.png 형식)
      for img in "$final_folder/${content}_0"*.png; do
        if [ -f "$img" ]; then
          cp "$img" "$OUTPUTS/${content}_final/"
          echo "      ✅ $(basename "$img")"
        fi
      done
      # 캡션 파일 복사
      if [ -f "$final_folder/caption.txt" ]; then
        cp "$final_folder/caption.txt" "$OUTPUTS/${content}_final/"
        echo "      ✅ caption.txt"
      fi
    fi
  done

  echo ""
done

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 폴더 정리 완료!"
echo ""
echo "📂 새 구조:"
echo "   outputs/"
echo "   ├── [콘텐츠]_final/  # 게시용 최종 이미지"
echo "   └── [콘텐츠]_temp/   # 테스트/버전별 이미지"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
