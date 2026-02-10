#!/usr/bin/env python3
"""
Google Sheets 포맷팅 스크립트 v2
- 배치 처리로 API 호출 최소화
- 헤더 스타일, 컬럼 너비, 색상 적용
"""

import os
import sys
import time
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    import gspread
    from gspread_formatting import (
        set_frozen, format_cell_range, format_cell_ranges,
        CellFormat, Color, TextFormat, Borders, Border,
        set_column_width, set_column_widths
    )
    from google.oauth2.service_account import Credentials
except ImportError as e:
    print(f"❌ pip install gspread gspread-formatting google-auth")
    sys.exit(1)


def connect_to_sheet():
    """Google Sheets 연결"""
    sheet_id = os.environ.get('GOOGLE_SHEET_ID')
    creds_path = os.environ.get('GOOGLE_CREDENTIALS_PATH')
    worksheet_name = os.environ.get('GOOGLE_WORKSHEET_NAME', '게시콘텐츠')

    if not sheet_id or not creds_path:
        print("❌ 환경변수 미설정")
        return None, None

    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]

    creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(sheet_id)
    worksheet = sheet.worksheet(worksheet_name)

    print(f"✅ 연결 성공: {sheet.title} / {worksheet_name}")
    return sheet, worksheet


def batch_format(worksheet):
    """배치 포맷팅 - API 호출 최소화"""
    print("🎨 포맷팅 시작...")

    all_values = worksheet.get_all_values()
    num_rows = len(all_values)
    print(f"   총 {num_rows}행 데이터")

    if num_rows <= 1:
        print("   ⚠️ 데이터 없음")
        return

    # === 배치 포맷 수집 ===
    formats = []

    # 1. 헤더 스타일
    header_format = CellFormat(
        backgroundColor=Color(0.2, 0.4, 0.6),
        textFormat=TextFormat(bold=True, foregroundColor=Color(1, 1, 1), fontSize=11),
        horizontalAlignment='CENTER',
        verticalAlignment='MIDDLE'
    )
    formats.append(('A1:H1', header_format))

    # 2. 데이터 영역 기본 스타일
    data_format = CellFormat(
        verticalAlignment='MIDDLE',
        horizontalAlignment='LEFT'
    )
    formats.append((f'A2:H{num_rows}', data_format))

    # 3. 번호열 중앙정렬
    center_format = CellFormat(horizontalAlignment='CENTER')
    formats.append((f'A2:A{num_rows}', center_format))
    formats.append((f'G2:G{num_rows}', center_format))

    # 4. URL열 작은 폰트
    url_format = CellFormat(textFormat=TextFormat(fontSize=9))
    formats.append((f'H2:H{num_rows}', url_format))

    # 5. 테두리
    border_format = CellFormat(
        borders=Borders(
            top=Border('SOLID', Color(0.8, 0.8, 0.8)),
            bottom=Border('SOLID', Color(0.8, 0.8, 0.8)),
            left=Border('SOLID', Color(0.8, 0.8, 0.8)),
            right=Border('SOLID', Color(0.8, 0.8, 0.8))
        )
    )
    formats.append((f'A1:H{num_rows}', border_format))

    # === 안전도/상태 색상 (배치 수집) ===
    safety_formats = {
        'SAFE': CellFormat(
            backgroundColor=Color(0.85, 0.95, 0.85),
            textFormat=TextFormat(foregroundColor=Color(0.1, 0.5, 0.1), bold=True),
            horizontalAlignment='CENTER'
        ),
        'CAUTION': CellFormat(
            backgroundColor=Color(1, 0.95, 0.8),
            textFormat=TextFormat(foregroundColor=Color(0.7, 0.5, 0), bold=True),
            horizontalAlignment='CENTER'
        ),
        'DANGER': CellFormat(
            backgroundColor=Color(1, 0.85, 0.85),
            textFormat=TextFormat(foregroundColor=Color(0.8, 0.2, 0.2), bold=True),
            horizontalAlignment='CENTER'
        ),
        'FORBIDDEN': CellFormat(
            backgroundColor=Color(0.9, 0.6, 0.6),
            textFormat=TextFormat(foregroundColor=Color(0.5, 0, 0), bold=True),
            horizontalAlignment='CENTER'
        )
    }

    status_formats = {
        '게시완료': CellFormat(
            backgroundColor=Color(0.8, 0.95, 0.8),
            textFormat=TextFormat(foregroundColor=Color(0, 0.5, 0), bold=True),
            horizontalAlignment='CENTER'
        ),
        '표지대기': CellFormat(
            backgroundColor=Color(1, 0.95, 0.7),
            textFormat=TextFormat(foregroundColor=Color(0.6, 0.4, 0), bold=True),
            horizontalAlignment='CENTER'
        )
    }

    # 안전도/상태 색상 배치 수집
    for i, row in enumerate(all_values[1:], start=2):
        if len(row) >= 5:
            safety = row[4].strip().upper()
            if safety in safety_formats:
                formats.append((f'E{i}', safety_formats[safety]))

        if len(row) >= 6:
            status = row[5].strip()
            if status in status_formats:
                formats.append((f'F{i}', status_formats[status]))

    # === 한번에 적용 ===
    print(f"   📝 {len(formats)}개 포맷 적용 중...")
    format_cell_ranges(worksheet, formats)
    print("   ✅ 셀 포맷 적용 완료")

    time.sleep(2)  # 잠시 대기

    # === 컬럼 너비 설정 ===
    print("   📏 컬럼 너비 설정 중...")
    widths = [
        ('A', 60),   # 번호
        ('B', 130),  # 영문명
        ('C', 100),  # 한글명
        ('D', 230),  # 폴더명
        ('E', 85),   # 안전도
        ('F', 90),   # 게시상태
        ('G', 100),  # 게시일
        ('H', 300),  # 인스타URL
    ]
    set_column_widths(worksheet, widths)
    print("   ✅ 컬럼 너비 설정 완료")

    time.sleep(1)

    # === 헤더 행 고정 ===
    print("   🔒 헤더 고정 중...")
    set_frozen(worksheet, rows=1)
    print("   ✅ 헤더 고정 완료")


def main():
    print("=" * 50)
    print("🎨 Google Sheets 포맷팅 v2")
    print("=" * 50)

    sheet, worksheet = connect_to_sheet()
    if not worksheet:
        return

    try:
        batch_format(worksheet)

        print("\n" + "=" * 50)
        print("✅ 포맷팅 완료!")
        print("=" * 50)

    except Exception as e:
        print(f"\n❌ 오류: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
