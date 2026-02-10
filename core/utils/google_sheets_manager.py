"""
Google Sheets 콘텐츠 관리자
- 게시된 콘텐츠 시트 연동
- 콘텐츠 제작 전 중복 체크
- 콘텐츠 제작 후 자동 업데이트

사용법:
    from core.utils.google_sheets_manager import ContentSheetManager

    manager = ContentSheetManager()

    # 중복 체크
    if manager.is_published('banana'):
        print("이미 게시됨!")

    # 새 콘텐츠 추가
    manager.add_content('027', 'cabbage', '양배추', 'SAFE')
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False
    print("⚠️ gspread 미설치. pip install gspread google-auth 실행 필요")


class ContentSheetManager:
    """Google Sheets 콘텐츠 관리자"""

    # 시트 컬럼 정의
    COLUMNS = ['번호', '영문명', '한글명', '폴더명', '안전도', '게시상태', '게시일', '인스타URL']

    # Google Sheets API 범위
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]

    def __init__(self):
        """초기화 - 환경변수에서 설정 로드"""
        self.sheet_id = os.environ.get('GOOGLE_SHEET_ID')
        self.credentials_path = os.environ.get('GOOGLE_CREDENTIALS_PATH')
        self.worksheet_name = os.environ.get('GOOGLE_WORKSHEET_NAME', '게시콘텐츠')

        self._client = None
        self._sheet = None
        self._worksheet = None

        # 로컬 캐시 (CSV 백업)
        self.local_cache_path = Path(__file__).parent.parent.parent / 'config' / 'data' / 'published_contents.csv'

    @property
    def is_configured(self) -> bool:
        """Google Sheets 설정 여부 확인"""
        return bool(self.sheet_id and self.credentials_path and GSPREAD_AVAILABLE)

    def connect(self) -> bool:
        """Google Sheets 연결"""
        if not GSPREAD_AVAILABLE:
            print("❌ gspread 라이브러리 미설치")
            return False

        if not self.credentials_path:
            print("❌ GOOGLE_CREDENTIALS_PATH 환경변수 미설정")
            return False

        if not self.sheet_id:
            print("❌ GOOGLE_SHEET_ID 환경변수 미설정")
            return False

        try:
            creds = Credentials.from_service_account_file(
                self.credentials_path,
                scopes=self.SCOPES
            )
            self._client = gspread.authorize(creds)
            self._sheet = self._client.open_by_key(self.sheet_id)

            # 워크시트 가져오기 또는 생성
            try:
                self._worksheet = self._sheet.worksheet(self.worksheet_name)
            except gspread.WorksheetNotFound:
                self._worksheet = self._sheet.add_worksheet(
                    title=self.worksheet_name,
                    rows=200,
                    cols=10
                )
                # 헤더 추가
                self._worksheet.append_row(self.COLUMNS)

            print(f"✅ Google Sheets 연결 성공: {self._sheet.title}")
            return True

        except Exception as e:
            print(f"❌ Google Sheets 연결 실패: {e}")
            return False

    def get_all_contents(self) -> List[Dict[str, Any]]:
        """모든 콘텐츠 목록 가져오기"""
        if not self._worksheet:
            if not self.connect():
                return self._get_from_local_cache()

        try:
            records = self._worksheet.get_all_records()
            return records
        except Exception as e:
            print(f"⚠️ 시트 읽기 실패, 로컬 캐시 사용: {e}")
            return self._get_from_local_cache()

    def is_published(self, topic_en: str) -> bool:
        """해당 주제가 이미 게시되었는지 확인"""
        contents = self.get_all_contents()
        for content in contents:
            if content.get('영문명', '').lower() == topic_en.lower():
                return content.get('게시상태') == '게시완료'
        return False

    def get_content(self, topic_en: str) -> Optional[Dict[str, Any]]:
        """특정 주제 정보 가져오기"""
        contents = self.get_all_contents()
        for content in contents:
            if content.get('영문명', '').lower() == topic_en.lower():
                return content
        return None

    def add_content(
        self,
        number: str,
        topic_en: str,
        topic_kr: str,
        safety: str,
        status: str = '게시완료',
        publish_date: str = None,
        instagram_url: str = ''
    ) -> bool:
        """새 콘텐츠 추가 (중복 체크 포함)"""
        if not self._worksheet:
            if not self.connect():
                return self._add_to_local_cache(
                    number, topic_en, topic_kr, safety, status, publish_date, instagram_url
                )

        # 🔒 중복 체크 (Phase 4 추가)
        existing = self.get_content(topic_en)
        if existing:
            print(f"⚠️ '{topic_en}' 이미 존재함 - 업데이트로 전환")
            return self.update_content(topic_en, {
                '게시상태': status,
                '게시일': publish_date or datetime.now().strftime('%Y-%m-%d'),
                '인스타URL': instagram_url
            })

        if publish_date is None:
            publish_date = datetime.now().strftime('%Y-%m-%d')

        folder_name = f"{number}_{topic_en}_{topic_kr}_published"

        row = [number, topic_en, topic_kr, folder_name, safety, status, publish_date, instagram_url]

        try:
            self._worksheet.append_row(row)
            print(f"✅ 시트에 추가됨: {topic_kr} ({topic_en})")

            # 로컬 캐시도 업데이트
            self._add_to_local_cache(
                number, topic_en, topic_kr, safety, status, publish_date, instagram_url
            )
            return True

        except Exception as e:
            print(f"❌ 시트 추가 실패: {e}")
            return self._add_to_local_cache(
                number, topic_en, topic_kr, safety, status, publish_date, instagram_url
            )

    def update_content(self, topic_en: str, updates: Dict[str, Any]) -> bool:
        """기존 콘텐츠 업데이트"""
        if not self._worksheet:
            if not self.connect():
                return False

        try:
            # 해당 행 찾기
            cell = self._worksheet.find(topic_en, in_column=2)  # 영문명 컬럼
            if not cell:
                print(f"❌ '{topic_en}' 콘텐츠를 찾을 수 없음")
                return False

            row_num = cell.row

            # 업데이트할 컬럼 찾아서 수정
            for col_name, value in updates.items():
                if col_name in self.COLUMNS:
                    col_idx = self.COLUMNS.index(col_name) + 1
                    self._worksheet.update_cell(row_num, col_idx, value)

            print(f"✅ '{topic_en}' 업데이트 완료")
            return True

        except Exception as e:
            print(f"❌ 업데이트 실패: {e}")
            return False

    def get_next_number(self) -> str:
        """다음 콘텐츠 번호 가져오기"""
        contents = self.get_all_contents()
        if not contents:
            return '001'

        max_num = 0
        for content in contents:
            try:
                num = int(content.get('번호', '0'))
                max_num = max(max_num, num)
            except ValueError:
                continue

        return f"{max_num + 1:03d}"

    def get_unpublished_covers(self) -> List[str]:
        """게시되지 않은 커버 목록"""
        published = {c.get('영문명', '').lower() for c in self.get_all_contents()}

        # ready 폴더의 커버 확인
        ready_path = Path(__file__).parent.parent.parent / 'content' / 'images' / '000_cover' / '02_ready'
        if not ready_path.exists():
            return []

        unpublished = []
        for cover_file in ready_path.glob('cover_*.png'):
            # cover_123_한글명_english.png 형식 파싱
            name = cover_file.stem
            parts = name.split('_')
            if len(parts) >= 4:
                english_name = parts[-1].lower()
                if english_name not in published:
                    unpublished.append(english_name)

        return unpublished

    def sync_from_local(self) -> int:
        """로컬 CSV에서 시트로 동기화"""
        if not self._worksheet:
            if not self.connect():
                return 0

        local_data = self._get_from_local_cache()
        if not local_data:
            return 0

        # 시트 데이터 가져오기
        sheet_data = {c.get('영문명', '').lower() for c in self.get_all_contents()}

        added = 0
        for content in local_data:
            topic_en = content.get('영문명', '').lower()
            if topic_en and topic_en not in sheet_data:
                row = [
                    content.get('번호', ''),
                    content.get('영문명', ''),
                    content.get('한글명', ''),
                    content.get('폴더명', ''),
                    content.get('안전도', ''),
                    content.get('게시상태', ''),
                    content.get('게시일', ''),
                    content.get('인스타URL', '')
                ]
                try:
                    self._worksheet.append_row(row)
                    added += 1
                except:
                    pass

        print(f"✅ {added}개 항목 동기화 완료")
        return added

    def _get_from_local_cache(self) -> List[Dict[str, Any]]:
        """로컬 CSV 캐시에서 읽기"""
        if not self.local_cache_path.exists():
            return []

        import csv
        contents = []
        with open(self.local_cache_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                contents.append(row)
        return contents

    def _add_to_local_cache(
        self,
        number: str,
        topic_en: str,
        topic_kr: str,
        safety: str,
        status: str,
        publish_date: str,
        instagram_url: str
    ) -> bool:
        """로컬 CSV 캐시에 추가"""
        import csv

        folder_name = f"{number}_{topic_en}_{topic_kr}_published"

        # 파일이 없으면 생성
        if not self.local_cache_path.exists():
            self.local_cache_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.local_cache_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(self.COLUMNS)

        # 기존 데이터 확인 (중복 방지)
        existing = self._get_from_local_cache()
        for item in existing:
            if item.get('영문명', '').lower() == topic_en.lower():
                print(f"⚠️ '{topic_en}' 이미 존재함")
                return False

        # 추가
        with open(self.local_cache_path, 'a', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([number, topic_en, topic_kr, folder_name, safety, status, publish_date or '', instagram_url])

        print(f"✅ 로컬 캐시에 추가됨: {topic_kr}")
        return True

    def print_status(self):
        """현재 상태 출력"""
        contents = self.get_all_contents()

        published = [c for c in contents if c.get('게시상태') == '게시완료']
        pending = [c for c in contents if c.get('게시상태') != '게시완료']

        print("\n" + "="*50)
        print("📊 콘텐츠 현황")
        print("="*50)
        print(f"총 콘텐츠: {len(contents)}개")
        print(f"게시 완료: {len(published)}개")
        print(f"대기 중: {len(pending)}개")

        # 안전도별 분류
        safe = len([c for c in published if c.get('안전도') == 'SAFE'])
        caution = len([c for c in published if c.get('안전도') == 'CAUTION'])
        danger = len([c for c in published if c.get('안전도') == 'DANGER'])

        print(f"\n안전도별: SAFE {safe} | CAUTION {caution} | DANGER {danger}")
        print("="*50)


# 콘텐츠 제작 워크플로우 함수
def check_before_creation(topic_en: str) -> Dict[str, Any]:
    """
    콘텐츠 제작 전 체크

    Returns:
        {
            'can_create': bool,
            'reason': str,
            'existing': dict or None
        }
    """
    manager = ContentSheetManager()

    existing = manager.get_content(topic_en)

    if existing:
        if existing.get('게시상태') == '게시완료':
            return {
                'can_create': False,
                'reason': f"'{topic_en}'은 이미 게시되었습니다 (번호: {existing.get('번호')})",
                'existing': existing
            }
        else:
            return {
                'can_create': True,
                'reason': f"'{topic_en}' 제작 대기 중. 계속 진행 가능.",
                'existing': existing
            }

    return {
        'can_create': True,
        'reason': f"'{topic_en}' 신규 콘텐츠. 제작 가능.",
        'existing': None
    }


def update_after_publishing(
    topic_en: str,
    topic_kr: str,
    safety: str,
    instagram_url: str = ''
) -> bool:
    """
    콘텐츠 게시 후 시트 업데이트
    """
    manager = ContentSheetManager()

    existing = manager.get_content(topic_en)

    if existing:
        # 기존 콘텐츠 업데이트
        return manager.update_content(topic_en, {
            '게시상태': '게시완료',
            '게시일': datetime.now().strftime('%Y-%m-%d'),
            '인스타URL': instagram_url
        })
    else:
        # 신규 콘텐츠 추가
        next_num = manager.get_next_number()
        return manager.add_content(
            number=next_num,
            topic_en=topic_en,
            topic_kr=topic_kr,
            safety=safety,
            status='게시완료',
            instagram_url=instagram_url
        )


# CLI 테스트용
if __name__ == '__main__':
    manager = ContentSheetManager()

    print("\n🔍 설정 확인:")
    print(f"  - GOOGLE_SHEET_ID: {'✅' if manager.sheet_id else '❌ 미설정'}")
    print(f"  - GOOGLE_CREDENTIALS_PATH: {'✅' if manager.credentials_path else '❌ 미설정'}")
    print(f"  - gspread 설치: {'✅' if GSPREAD_AVAILABLE else '❌ 미설치'}")

    if manager.is_configured:
        if manager.connect():
            manager.print_status()
    else:
        print("\n📋 로컬 캐시 사용:")
        manager.print_status()
