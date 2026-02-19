#!/usr/bin/env python3
"""
# ============================================================
# 📁 CoverManager - 커버 이미지 자동 관리 시스템
# ============================================================
#
# 📋 역할:
#    1. 02_ready 폴더에서 사용 가능한 커버 조회
#    2. 콘텐츠 제작 시 커버 선택/매칭
#    3. 게시 완료 시 01_published 폴더로 자동 이동
#
# 🔄 워크플로우:
#    02_ready (대기) → 콘텐츠 제작 → 게시 → 01_published (완료)
#
# Author: 김대리 (📤 파일 관리 담당)
# Date: 2026-01-29
# ============================================================
"""

import os
import shutil
import json
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime


class CoverManager:
    """커버 이미지 자동 관리 클래스"""

    def __init__(self, base_path: Optional[str] = None):
        """
        초기화

        Args:
            base_path: 커버 폴더 기본 경로 (기본값: content/images/000_cover)
        """
        if base_path:
            self.base_path = Path(base_path)
        else:
            # 프로젝트 루트 기준 경로
            project_root = Path(__file__).parent.parent.parent
            self.base_path = project_root / "content" / "images" / "000_cover"

        self.ready_path = self.base_path / "02_ready"
        self.published_path = self.base_path / "01_published"
        self.archive_path = self.base_path / "archive"

        # 폴더 존재 확인
        self._ensure_folders()

    def _ensure_folders(self):
        """필요한 폴더가 없으면 생성"""
        for folder in [self.ready_path, self.published_path, self.archive_path]:
            folder.mkdir(parents=True, exist_ok=True)

    def get_ready_covers(self) -> List[Dict]:
        """
        사용 가능한 커버 목록 조회

        Returns:
            List of cover info dicts
        """
        covers = []
        for file in self.ready_path.glob("cover_*.png"):
            info = self._parse_cover_filename(file.name)
            if info:
                info['path'] = str(file)
                info['status'] = 'ready'
                covers.append(info)
        return sorted(covers, key=lambda x: x.get('number', 0))

    def get_published_covers(self) -> List[Dict]:
        """게시 완료된 커버 목록 조회"""
        covers = []
        for file in self.published_path.glob("cover_*.png"):
            info = self._parse_cover_filename(file.name)
            if info:
                info['path'] = str(file)
                info['status'] = 'published'
                covers.append(info)
        return sorted(covers, key=lambda x: x.get('number', 0))

    def _parse_cover_filename(self, filename: str) -> Optional[Dict]:
        """
        파일명에서 정보 추출

        파일명 형식: cover_{번호}_{한글명}_{영문명}.png
        예: cover_79_흰쌀밥_rice.png
        """
        try:
            name = filename.replace('.png', '')
            parts = name.split('_')

            if len(parts) >= 4 and parts[0] == 'cover':
                return {
                    'filename': filename,
                    'number': int(parts[1]),
                    'name_kr': parts[2],
                    'name_en': '_'.join(parts[3:])  # 영문명에 _가 포함될 수 있음
                }
        except (ValueError, IndexError):
            pass
        return None

    def find_cover_by_topic(self, topic: str, topic_kr: Optional[str] = None) -> Optional[Dict]:
        """
        주제에 맞는 커버 찾기

        Args:
            topic: 영문 주제명 (예: 'rice')
            topic_kr: 한글 주제명 (예: '흰쌀밥')

        Returns:
            매칭된 커버 정보 또는 None
        """
        covers = self.get_ready_covers()

        for cover in covers:
            # 영문명 매칭
            if topic.lower() in cover['name_en'].lower():
                return cover
            # 한글명 매칭
            if topic_kr and topic_kr in cover['name_kr']:
                return cover

        return None

    def move_to_published(self, cover_filename: str, publish_info: Optional[Dict] = None) -> bool:
        """
        게시 완료된 커버를 published 폴더로 이동

        Args:
            cover_filename: 이동할 커버 파일명
            publish_info: 게시 정보 (날짜, URL 등)

        Returns:
            성공 여부
        """
        src = self.ready_path / cover_filename
        dst = self.published_path / cover_filename

        if not src.exists():
            print(f"⚠️ 파일 없음: {src}")
            return False

        try:
            shutil.move(str(src), str(dst))
            print(f"✅ 커버 이동 완료: {cover_filename}")
            print(f"   {self.ready_path.name}/ → {self.published_path.name}/")

            # 이동 로그 기록
            self._log_movement(cover_filename, publish_info)
            return True

        except Exception as e:
            print(f"❌ 이동 실패: {e}")
            return False

    def move_to_archive(self, cover_filename: str, reason: str = "") -> bool:
        """
        사용하지 않을 커버를 archive로 이동

        Args:
            cover_filename: 이동할 커버 파일명
            reason: 아카이브 사유
        """
        # ready 또는 루트에서 찾기
        for src_folder in [self.ready_path, self.base_path]:
            src = src_folder / cover_filename
            if src.exists():
                dst = self.archive_path / cover_filename
                try:
                    shutil.move(str(src), str(dst))
                    print(f"📦 아카이브 이동: {cover_filename}")
                    if reason:
                        print(f"   사유: {reason}")
                    return True
                except Exception as e:
                    print(f"❌ 아카이브 실패: {e}")
                    return False

        print(f"⚠️ 파일 없음: {cover_filename}")
        return False

    def _log_movement(self, filename: str, publish_info: Optional[Dict] = None):
        """이동 로그 기록"""
        log_file = self.base_path / "cover_movement_log.json"

        # 기존 로그 로드
        logs = []
        if log_file.exists():
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            except:
                logs = []

        # 새 로그 추가
        log_entry = {
            'filename': filename,
            'moved_at': datetime.now().isoformat(),
            'from': 'ready',
            'to': 'published'
        }
        if publish_info:
            log_entry['publish_info'] = publish_info

        logs.append(log_entry)

        # 저장
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)

    def get_stats(self) -> Dict:
        """커버 현황 통계"""
        ready = len(list(self.ready_path.glob("cover_*.png")))
        published = len(list(self.published_path.glob("cover_*.png")))
        archived = len(list(self.archive_path.glob("cover_*.png")))
        root = len(list(self.base_path.glob("cover_*.png")))

        return {
            'ready': ready,
            'published': published,
            'archived': archived,
            'root': root,
            'total': ready + published + archived + root
        }

    def print_status(self):
        """현황 출력"""
        stats = self.get_stats()
        print("\n📊 커버 이미지 현황")
        print("=" * 40)
        print(f"  📁 01_published (게시완료): {stats['published']}개")
        print(f"  📁 02_ready (게시대기):     {stats['ready']}개")
        print(f"  📁 archive (아카이브):      {stats['archived']}개")
        print(f"  📁 루트 (미분류):           {stats['root']}개")
        print("-" * 40)
        print(f"  총계: {stats['total']}개")
        print("=" * 40)


# ============================================================
# 🔄 게시 후 자동 이동 훅 (Hook)
# ============================================================

def on_publish_complete(topic: str, topic_kr: str, publish_result: Dict) -> bool:
    """
    게시 완료 후 호출되는 훅 함수

    Args:
        topic: 영문 주제명
        topic_kr: 한글 주제명
        publish_result: 게시 결과 (instagram_url, post_id 등)

    Returns:
        커버 이동 성공 여부

    Usage:
        # 게시 완료 후 호출
        from core.utils.cover_manager import on_publish_complete

        result = publisher.publish(...)
        if result.success:
            on_publish_complete('rice', '흰쌀밥', {
                'instagram_url': result.url,
                'post_id': result.post_id,
                'date': '2026-01-29'
            })
    """
    manager = CoverManager()

    # 주제에 맞는 커버 찾기
    cover = manager.find_cover_by_topic(topic, topic_kr)

    if cover:
        return manager.move_to_published(
            cover['filename'],
            publish_info={
                'topic': topic,
                'topic_kr': topic_kr,
                **publish_result
            }
        )
    else:
        print(f"⚠️ '{topic}' ({topic_kr}) 주제의 커버를 찾을 수 없습니다.")
        return False


# ============================================================
# 🧪 테스트 / CLI
# ============================================================

if __name__ == "__main__":
    manager = CoverManager()

    print("\n🔍 커버 매니저 테스트")
    print("=" * 50)

    # 현황 출력
    manager.print_status()

    # 사용 가능한 커버 목록
    ready = manager.get_ready_covers()
    print(f"\n📋 사용 가능한 커버 ({len(ready)}개):")
    for cover in ready[:5]:
        print(f"  - {cover['number']:03d}: {cover['name_kr']} ({cover['name_en']})")
    if len(ready) > 5:
        print(f"  ... 외 {len(ready) - 5}개")
