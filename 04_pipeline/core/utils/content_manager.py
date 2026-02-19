#!/usr/bin/env python3
"""
# ============================================================
# 📁 ContentManager - 콘텐츠 폴더 자동 관리 시스템
# ============================================================
#
# 📋 역할:
#    1. 콘텐츠 제작 시 폴더 생성 (###_음식이름/)
#    2. 게시 완료 시 폴더명 변경 (###_음식이름_published/)
#    3. 커버 이미지 자동 연동 (02_ready → 01_published)
#
# 🔄 워크플로우:
#    제작: 079_흰쌀밥/ + cover_79 사용
#    게시: 079_흰쌀밥_published/ + cover_79 이동
#
# Author: 김대리 (📤 파일 관리 담당)
# Date: 2026-01-29
# ============================================================
"""

import os
import shutil
import json
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from datetime import datetime

from .cover_manager import CoverManager


class ContentManager:
    """콘텐츠 폴더 자동 관리 클래스"""

    def __init__(self, base_path: Optional[str] = None):
        """
        초기화

        Args:
            base_path: 이미지 폴더 기본 경로 (기본값: content/images)
        """
        if base_path:
            self.base_path = Path(base_path)
        else:
            project_root = Path(__file__).parent.parent.parent
            self.base_path = project_root / "content" / "images"

        self.cover_manager = CoverManager()

    def get_next_number(self) -> int:
        """
        다음 콘텐츠 번호 조회

        기존 폴더들의 번호를 확인하여 다음 번호 반환
        """
        max_num = 0
        for folder in self.base_path.iterdir():
            if folder.is_dir():
                name = folder.name
                # ###_음식이름 또는 ###_음식이름_published 패턴
                if name[:3].isdigit():
                    try:
                        num = int(name[:3])
                        max_num = max(max_num, num)
                    except ValueError:
                        pass
        return max_num + 1

    def create_content_folder(
        self,
        topic_en: str,
        topic_kr: str,
        number: Optional[int] = None
    ) -> Tuple[Path, Optional[Dict]]:
        """
        콘텐츠 제작용 폴더 생성

        Args:
            topic_en: 영문 주제명 (예: 'rice')
            topic_kr: 한글 주제명 (예: '흰쌀밥')
            number: 콘텐츠 번호 (없으면 자동 할당)

        Returns:
            (폴더 경로, 매칭된 커버 정보)
        """
        if number is None:
            number = self.get_next_number()

        folder_name = f"{number:03d}_{topic_kr}"
        folder_path = self.base_path / folder_name

        # 폴더 생성
        folder_path.mkdir(parents=True, exist_ok=True)
        (folder_path / "archive").mkdir(exist_ok=True)

        print(f"📁 콘텐츠 폴더 생성: {folder_name}/")

        # 매칭되는 커버 찾기
        cover = self.cover_manager.find_cover_by_topic(topic_en, topic_kr)
        if cover:
            print(f"🖼️ 매칭 커버: {cover['filename']}")
        else:
            print(f"⚠️ 매칭 커버 없음 - 수동 선택 필요")

        # 메타데이터 저장
        meta = {
            'number': number,
            'topic_en': topic_en,
            'topic_kr': topic_kr,
            'folder_name': folder_name,
            'cover': cover['filename'] if cover else None,
            'created_at': datetime.now().isoformat(),
            'status': 'draft'
        }
        meta_path = folder_path / 'content_meta.json'
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        return folder_path, cover

    def on_publish_complete(
        self,
        folder_path: str,
        publish_result: Dict
    ) -> bool:
        """
        게시 완료 후 호출 - 폴더명 변경 + 커버 이동

        Args:
            folder_path: 콘텐츠 폴더 경로
            publish_result: 게시 결과 (instagram_url, post_id 등)

        Returns:
            성공 여부
        """
        folder = Path(folder_path)

        if not folder.exists():
            print(f"❌ 폴더 없음: {folder_path}")
            return False

        # 이미 published 폴더인지 확인
        if folder.name.endswith('_published'):
            print(f"⚠️ 이미 게시 완료된 폴더: {folder.name}")
            return True

        # 1. 폴더명 변경 (###_음식이름 → ###_음식이름_published)
        new_name = f"{folder.name}_published"
        new_path = folder.parent / new_name

        try:
            folder.rename(new_path)
            print(f"✅ 폴더 변경: {folder.name}/ → {new_name}/")
        except Exception as e:
            print(f"❌ 폴더 변경 실패: {e}")
            return False

        # 2. 메타데이터 업데이트
        meta_path = new_path / 'content_meta.json'
        if meta_path.exists():
            try:
                with open(meta_path, 'r', encoding='utf-8') as f:
                    meta = json.load(f)

                meta['status'] = 'published'
                meta['published_at'] = datetime.now().isoformat()
                meta['publish_result'] = publish_result

                with open(meta_path, 'w', encoding='utf-8') as f:
                    json.dump(meta, f, ensure_ascii=False, indent=2)

                # 3. 커버 이미지 이동
                if meta.get('cover'):
                    self.cover_manager.move_to_published(
                        meta['cover'],
                        publish_info=publish_result
                    )

            except Exception as e:
                print(f"⚠️ 메타데이터 업데이트 실패: {e}")

        return True

    def get_draft_contents(self) -> List[Dict]:
        """제작 중인 콘텐츠 목록"""
        drafts = []
        for folder in self.base_path.iterdir():
            if folder.is_dir() and not folder.name.endswith('_published'):
                if folder.name[:3].isdigit() and '_' in folder.name:
                    meta_path = folder / 'content_meta.json'
                    if meta_path.exists():
                        try:
                            with open(meta_path, 'r', encoding='utf-8') as f:
                                meta = json.load(f)
                            meta['folder_path'] = str(folder)
                            drafts.append(meta)
                        except:
                            pass
        return sorted(drafts, key=lambda x: x.get('number', 0))

    def get_published_contents(self) -> List[Dict]:
        """게시 완료된 콘텐츠 목록"""
        published = []
        for folder in self.base_path.iterdir():
            if folder.is_dir() and folder.name.endswith('_published'):
                meta_path = folder / 'content_meta.json'
                if meta_path.exists():
                    try:
                        with open(meta_path, 'r', encoding='utf-8') as f:
                            meta = json.load(f)
                        meta['folder_path'] = str(folder)
                        published.append(meta)
                    except:
                        pass
        return sorted(published, key=lambda x: x.get('number', 0))

    def get_stats(self) -> Dict:
        """콘텐츠 현황 통계"""
        draft = 0
        published = 0

        for folder in self.base_path.iterdir():
            if folder.is_dir():
                name = folder.name
                if name[:3].isdigit() and '_' in name:
                    if name.endswith('_published'):
                        published += 1
                    else:
                        draft += 1

        return {
            'draft': draft,
            'published': published,
            'total': draft + published
        }

    def print_status(self):
        """현황 출력"""
        stats = self.get_stats()
        cover_stats = self.cover_manager.get_stats()

        print("\n" + "=" * 50)
        print("📊 콘텐츠 & 커버 현황")
        print("=" * 50)

        print("\n[ 콘텐츠 폴더 ]")
        print(f"  📝 제작중 (draft):     {stats['draft']}개")
        print(f"  ✅ 게시완료 (published): {stats['published']}개")

        print("\n[ 커버 이미지 ]")
        print(f"  📁 게시대기 (ready):    {cover_stats['ready']}개")
        print(f"  📁 게시완료 (published): {cover_stats['published']}개")

        print("\n" + "=" * 50)


# ============================================================
# 🔄 통합 게시 완료 훅
# ============================================================

def on_content_published(
    content_folder: str,
    topic_en: str,
    topic_kr: str,
    publish_result: Dict
) -> bool:
    """
    게시 완료 후 호출되는 통합 훅

    1. 콘텐츠 폴더명 변경 (→ _published)
    2. 커버 이미지 이동 (02_ready → 01_published)
    3. 메타데이터 업데이트

    Args:
        content_folder: 콘텐츠 폴더 경로
        topic_en: 영문 주제명
        topic_kr: 한글 주제명
        publish_result: 게시 결과

    Returns:
        성공 여부

    Usage:
        from core.utils.content_manager import on_content_published

        # 게시 성공 후
        on_content_published(
            content_folder='/path/to/079_흰쌀밥',
            topic_en='rice',
            topic_kr='흰쌀밥',
            publish_result={
                'instagram_url': 'https://...',
                'post_id': '123456',
                'date': '2026-01-29'
            }
        )
    """
    manager = ContentManager()
    return manager.on_publish_complete(content_folder, publish_result)


# ============================================================
# 🧪 테스트 / CLI
# ============================================================

if __name__ == "__main__":
    manager = ContentManager()

    print("\n🔍 콘텐츠 매니저 테스트")
    manager.print_status()

    # 제작 중인 콘텐츠
    drafts = manager.get_draft_contents()
    if drafts:
        print(f"\n📝 제작 중인 콘텐츠 ({len(drafts)}개):")
        for d in drafts[:5]:
            print(f"  - {d.get('folder_name')}: {d.get('topic_kr')}")
