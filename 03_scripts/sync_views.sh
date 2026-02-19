#!/bin/bash
# sync_views.sh - 🔒_views 폴더 심볼릭 링크 동기화
# 옵션 D' - content_map.json 기준으로 상태별 바로가기 생성
#
# 사용법: ./sync_views.sh

set -e

BASE_DIR="/Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine"
IMAGES_DIR="$BASE_DIR/content/images"
VIEWS_DIR="$IMAGES_DIR/🔒_views"
CONTENT_MAP="$BASE_DIR/config/data/content_map.json"

echo "=== 🔒_views 동기화 시작 ==="
echo "   content_map: $CONTENT_MAP"
echo ""

# 1. 기존 심볼릭 링크 제거
echo "1. 기존 링크 정리..."
rm -f "$VIEWS_DIR/published/"* 2>/dev/null || true
rm -f "$VIEWS_DIR/ready/"* 2>/dev/null || true
rm -f "$VIEWS_DIR/in_progress/"* 2>/dev/null || true
rm -f "$VIEWS_DIR/blocked/"* 2>/dev/null || true

# 2. 폴더 존재 확인
mkdir -p "$VIEWS_DIR/published" "$VIEWS_DIR/ready" "$VIEWS_DIR/in_progress" "$VIEWS_DIR/blocked"

# 3. content_map에서 상태별 링크 생성
echo "2. 심볼릭 링크 생성..."

published_count=0
ready_count=0
in_progress_count=0
blocked_count=0

# jq로 content_map 파싱
if ! command -v jq &> /dev/null; then
    echo "   ⚠️ jq 미설치 - Python fallback 사용"

    # Python으로 JSON 파싱
    python3 << 'PYTHON_SCRIPT'
import json
import os

base_dir = "/Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine"
images_dir = f"{base_dir}/content/images"
views_dir = f"{images_dir}/🔒_views"
content_map_path = f"{base_dir}/config/data/content_map.json"

with open(content_map_path, 'r') as f:
    data = json.load(f)

counts = {"published": 0, "ready": 0, "in_progress": 0, "blocked": 0}

for topic, info in data.get("contents", {}).items():
    folder = info.get("folder", "")
    status = info.get("status", "")

    if not folder or not status:
        continue

    source = f"{images_dir}/{folder}"
    if not os.path.exists(source):
        continue

    target_dir = f"{views_dir}/{status}"
    if not os.path.exists(target_dir):
        os.makedirs(target_dir, exist_ok=True)

    link_path = f"{target_dir}/{folder}"
    rel_source = f"../../{folder}"

    if os.path.islink(link_path):
        os.unlink(link_path)

    os.symlink(rel_source, link_path)
    counts[status] = counts.get(status, 0) + 1
    print(f"   ✓ {status}/{folder}")

print(f"\n=== 동기화 완료 ===")
print(f"   published: {counts['published']}건")
print(f"   ready: {counts['ready']}건")
print(f"   in_progress: {counts['in_progress']}건")
print(f"   blocked: {counts['blocked']}건")
PYTHON_SCRIPT

else
    # jq 사용
    jq -r '.contents | to_entries[] | "\(.value.folder)|\(.value.status)"' "$CONTENT_MAP" | while IFS='|' read -r folder status; do
        if [ -z "$folder" ] || [ -z "$status" ]; then
            continue
        fi

        source_dir="$IMAGES_DIR/$folder"
        if [ ! -d "$source_dir" ]; then
            continue
        fi

        target_dir="$VIEWS_DIR/$status"
        link_path="$target_dir/$folder"
        rel_source="../../$folder"

        ln -sf "$rel_source" "$link_path"
        echo "   ✓ $status/$folder"
    done

    echo ""
    echo "=== 동기화 완료 ==="
    echo "   published: $(ls -1 "$VIEWS_DIR/published" 2>/dev/null | wc -l | tr -d ' ')건"
    echo "   ready: $(ls -1 "$VIEWS_DIR/ready" 2>/dev/null | wc -l | tr -d ' ')건"
    echo "   in_progress: $(ls -1 "$VIEWS_DIR/in_progress" 2>/dev/null | wc -l | tr -d ' ')건"
    echo "   blocked: $(ls -1 "$VIEWS_DIR/blocked" 2>/dev/null | wc -l | tr -d ' ')건"
fi

echo ""
echo "🔒 열람 전용: _views 폴더에서는 파일 수정 금지"
echo "   수정 필요 시 원본 폴더(images/XXX_topic/)에서 작업"
