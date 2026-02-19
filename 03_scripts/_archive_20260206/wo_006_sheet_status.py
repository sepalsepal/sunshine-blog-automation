#!/usr/bin/env python3
"""
WO-2026-0205-006-R2 (최종): 구글시트 현황 체크
================================================

1. F열(게시상태): 실제 폴더 위치에 맞게 업데이트
2. G열: SHA256 해시 비교 (bg 없으면 렌더링 이미지 비교)
3. H~K열: 파일 존재 → "완료", 미존재 → "-"
4. L~M열: 승인/게시 → "완료", 미해당 → "-"
5. 공란 없음 — 모든 셀에 값 기입

사용법:
    .venv/bin/python services/scripts/wo_006_sheet_status.py
"""

import hashlib
import json
import os
import sys
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / '.env')

import gspread
from google.oauth2.service_account import Credentials

# ──────────────────────────────
# 상수
# ──────────────────────────────
CONTENT_BASE = PROJECT_ROOT / "contents"
STATUS_DIR_MAP = {
    "1_cover_only": "cover_only",
    "2_body_ready": "body_ready",
    "3_approved": "approved",
}
COVER_SOURCES_DIR = CONTENT_BASE / "0_cover_sources"

# 시트 컬럼 (1-indexed)
COL_ENGNAME = 2    # B
COL_FOLDER = 4     # D
COL_STATUS = 6     # F: 게시상태
COL_HASHCHECK = 7  # G
COL_COVER = 8      # H
COL_BODY1 = 9      # I
COL_BODY2 = 10     # J
COL_CTA = 11       # K
COL_APPROVE = 12   # L
COL_PUBLISH = 13   # M


# ──────────────────────────────
# 유틸리티
# ──────────────────────────────
def sha256_file(path: Path) -> str | None:
    if not path or not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_folder_index() -> dict:
    """
    contents/ 전체를 스캔하여 {폴더명: (actual_status, Path)} 맵 생성.
    """
    index = {}
    for dirname, status in STATUS_DIR_MAP.items():
        base = CONTENT_BASE / dirname
        if not base.exists():
            continue
        for d in base.iterdir():
            if d.is_dir() and not d.name.startswith('.'):
                index[d.name] = (status, d)

    # 4_posted (월별 하위)
    posted_dir = CONTENT_BASE / "4_posted"
    if posted_dir.exists():
        for month in posted_dir.iterdir():
            if month.is_dir():
                for d in month.iterdir():
                    if d.is_dir() and not d.name.startswith('.'):
                        index[d.name] = ("posted", d)

    return index


def find_folder(folder_index: dict, folder_name: str, eng_name: str):
    """
    폴더 인덱스에서 매칭. 반환: (actual_status, Path) 또는 (None, None)
    """
    # 1) 폴더명 정확 매칭
    if folder_name in folder_index:
        return folder_index[folder_name]

    # 2) 영문명으로 부분 매칭 (split by _)
    for fname, (st, path) in folder_index.items():
        parts = fname.lower().split('_')
        if eng_name.lower() in parts:
            return (st, path)

    # 3) 유연한 매칭 (contains)
    eng_lower = eng_name.lower()
    for fname, (st, path) in folder_index.items():
        if eng_lower in fname.lower():
            return (st, path)

    return (None, None)


def find_file(folder: Path, eng_name: str, suffix: str) -> Path | None:
    """폴더 내 {eng_name}_{suffix}.{ext} 경로 반환."""
    if not folder or not folder.exists():
        return None
    eng_lower = eng_name.lower()
    for ext in ['png', 'jpg', 'jpeg']:
        target = folder / f"{eng_name}_{suffix}.{ext}"
        if target.exists():
            return target
    for f in folder.iterdir():
        if f.is_file() and f.name.lower().startswith(f"{eng_lower}_{suffix}."):
            return f
    return None


def file_exists(folder: Path, eng_name: str, suffix: str) -> bool:
    return find_file(folder, eng_name, suffix) is not None


def check_cover_ne_body(folder: Path, eng_name: str, has_body: bool) -> str:
    """
    G열: 커버 ≠ 바디 SHA256 비교.

    비교 소스 우선순위:
      cover: _00_bg.png > 0_cover_sources 원본 > metadata > _00.png
      body:  _01_bg.png > _body_clean.png > _01.png

    반환: "확인" | "불일치" | "-"
    """
    if not folder or not has_body:
        return "-"

    archive = folder / "archive"

    # ── Cover hash ──
    cover_hash = None

    # 1) archive/_00_bg
    if archive and archive.exists():
        for ext in ['png', 'jpg']:
            bg = archive / f"{eng_name}_00_bg.{ext}"
            if bg.exists():
                cover_hash = sha256_file(bg)
                break

    # 2) 0_cover_sources
    if cover_hash is None and COVER_SOURCES_DIR.exists():
        eng_lower = eng_name.lower()
        for f in COVER_SOURCES_DIR.iterdir():
            if f.is_file() and eng_lower in f.name.lower() and 'cover' in f.name.lower():
                cover_hash = sha256_file(f)
                break

    # 3) metadata cover_source 참조
    if cover_hash is None:
        meta_path = folder / "metadata.json"
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text())
                cover_src = meta.get("clean_cover_source") or meta.get("cover_source")
                if cover_src and COVER_SOURCES_DIR.exists():
                    for f in COVER_SOURCES_DIR.iterdir():
                        if f.is_file() and f.name == cover_src:
                            cover_hash = sha256_file(f)
                            break
            except Exception:
                pass

    # 4) 렌더링된 _00.png
    if cover_hash is None:
        rendered = find_file(folder, eng_name, "00")
        if rendered:
            cover_hash = sha256_file(rendered)

    # ── Body hash ──
    body_hash = None

    if archive and archive.exists():
        # _01_bg
        for ext in ['png', 'jpg']:
            bg = archive / f"{eng_name}_01_bg.{ext}"
            if bg.exists():
                body_hash = sha256_file(bg)
                break
        # _body_clean
        if body_hash is None:
            for ext in ['png', 'jpg']:
                clean = archive / f"{eng_name}_body_clean.{ext}"
                if clean.exists():
                    body_hash = sha256_file(clean)
                    break

    # 렌더링된 _01.png (bg 없을 때 대안)
    if body_hash is None:
        rendered = find_file(folder, eng_name, "01")
        if rendered:
            body_hash = sha256_file(rendered)

    # ── 비교 ──
    if cover_hash and body_hash:
        return "불일치" if cover_hash == body_hash else "확인"

    # metadata R1 검증 결과 참조
    meta_path = folder / "metadata.json"
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text())
            if meta.get("cover_ne_body_sha256") == "PASS":
                return "확인"
        except Exception:
            pass

    return "-"


# ──────────────────────────────
# 메인
# ──────────────────────────────
def main():
    print("=" * 75)
    print("  WO-2026-0205-006-R2 (최종): 구글시트 현황 체크")
    print(f"  시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 75)

    # 폴더 인덱스 구축
    folder_index = build_folder_index()
    print(f"\n  폴더 인덱스: {len(folder_index)}건")

    # Google Sheets 연결
    creds = Credentials.from_service_account_file(
        os.environ['GOOGLE_CREDENTIALS_PATH'],
        scopes=[
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
    )
    client = gspread.authorize(creds)
    sheet = client.open_by_key(os.environ['GOOGLE_SHEET_ID'])
    ws = sheet.worksheet(os.environ.get('GOOGLE_WORKSHEET_NAME', '게시콘텐츠'))

    all_data = ws.get_all_values()
    rows = all_data[1:]
    print(f"  시트 행: {len(rows)}건 (헤더 제외)")

    # 기존 posted 행 식별 (시트 기준)
    sheet_posted_rows = set()
    for idx, row in enumerate(rows):
        if len(row) >= COL_STATUS and row[COL_STATUS - 1] == 'posted':
            sheet_posted_rows.add(idx + 2)

    # posted가 아닌 행 수집
    non_posted = []
    for idx, row in enumerate(rows):
        row_num = idx + 2
        if row_num in sheet_posted_rows:
            continue
        non_posted.append((row_num, row))

    print(f"  기존 posted: {len(sheet_posted_rows)}건 (수정 안함)")
    print(f"  처리 대상: {len(non_posted)}건\n")

    # 업데이트 수집
    updates = []
    stats = {
        "status_changed": 0,
        "hash_ok": 0, "hash_fail": 0, "hash_dash": 0,
        "cover": 0, "body1": 0, "body2": 0, "cta": 0,
        "approved": 0, "new_posted": 0,
    }

    for row_num, row in non_posted:
        eng_name = row[COL_ENGNAME - 1] if len(row) >= COL_ENGNAME else ''
        folder_name = row[COL_FOLDER - 1] if len(row) >= COL_FOLDER else ''
        sheet_status = row[COL_STATUS - 1] if len(row) >= COL_STATUS else ''

        if not eng_name:
            continue

        # 실제 폴더 찾기
        actual_status, folder = find_folder(folder_index, folder_name, eng_name)

        # ─── F열: 게시상태 동기화 ───
        new_status = actual_status or sheet_status
        if new_status and new_status != sheet_status:
            updates.append((row_num, COL_STATUS, new_status))
            stats["status_changed"] += 1

        # ─── H~K열: 파일 존재 ───
        has_cover = file_exists(folder, eng_name, "00") if folder else False
        has_body1 = file_exists(folder, eng_name, "01") if folder else False
        has_body2 = file_exists(folder, eng_name, "02") if folder else False
        has_cta = file_exists(folder, eng_name, "03") if folder else False

        if has_cover: stats["cover"] += 1
        if has_body1: stats["body1"] += 1
        if has_body2: stats["body2"] += 1
        if has_cta: stats["cta"] += 1

        # ─── G열: SHA256 비교 ───
        has_any_body = has_body1 or has_body2 or has_cta
        hash_result = check_cover_ne_body(folder, eng_name, has_any_body)
        if hash_result == "확인":
            stats["hash_ok"] += 1
        elif hash_result == "불일치":
            stats["hash_fail"] += 1
        else:
            stats["hash_dash"] += 1

        # ─── L~M열: 승인/게시 ───
        effective_status = new_status or sheet_status
        is_approved = effective_status in ('approved', 'posted')
        is_posted = effective_status == 'posted'

        if is_approved: stats["approved"] += 1
        if is_posted: stats["new_posted"] += 1

        # ─── 값 결정 (공란 없이) ───
        vals = {
            COL_HASHCHECK: hash_result,
            COL_COVER: "완료" if has_cover else "-",
            COL_BODY1: "완료" if has_body1 else "-",
            COL_BODY2: "완료" if has_body2 else "-",
            COL_CTA: "완료" if has_cta else "-",
            COL_APPROVE: "완료" if is_approved else "-",
            COL_PUBLISH: "완료" if is_posted else "-",
        }

        for col, val in vals.items():
            current = row[col - 1] if len(row) >= col else ''
            if current != val:
                updates.append((row_num, col, val))

        # 로그
        status_mark = f"→{new_status}" if new_status != sheet_status else sheet_status
        c = "O" if has_cover else "-"
        b1 = "O" if has_body1 else "-"
        b2 = "O" if has_body2 else "-"
        ct = "O" if has_cta else "-"
        g = hash_result
        l_m = f"{'O' if is_approved else '-'}/{'O' if is_posted else '-'}"
        print(f"  행{row_num:3d} | {eng_name:22s} | {status_mark:20s} | G={g:4s} | {c} {b1} {b2} {ct} | L/M={l_m}")

    # ─── 요약 ───
    print(f"\n{'=' * 75}")
    print(f"  업데이트 요약")
    print(f"{'=' * 75}")
    print(f"  대상 행: {len(non_posted)}건")
    print(f"  F (상태변경): {stats['status_changed']}건")
    print(f"  G (해시비교): 확인={stats['hash_ok']} | 불일치={stats['hash_fail']} | -={stats['hash_dash']}")
    print(f"  H (표지): {stats['cover']}건 완료")
    print(f"  I (본문1): {stats['body1']}건 완료")
    print(f"  J (본문2): {stats['body2']}건 완료")
    print(f"  K (CTA): {stats['cta']}건 완료")
    print(f"  L (승인): {stats['approved']}건 완료")
    print(f"  M (게시): {stats['new_posted']}건 완료")
    print(f"  변경할 셀: {len(updates)}개")

    if not updates:
        print("\n  변경 사항 없음.")
        return

    # ─── Batch update ───
    print(f"\n  시트 업데이트 중...")
    cells_to_update = []
    for row_num, col, val in updates:
        col_letter = chr(64 + col)
        cells_to_update.append({
            'range': f"{col_letter}{row_num}",
            'values': [[val]]
        })

    batch_size = 100
    total_batches = (len(cells_to_update) + batch_size - 1) // batch_size
    for i in range(0, len(cells_to_update), batch_size):
        batch = cells_to_update[i:i + batch_size]
        batch_num = i // batch_size + 1
        ws.batch_update(batch, value_input_option='RAW')
        print(f"    배치 {batch_num}/{total_batches} 완료 ({len(batch)}셀)")

    print(f"\n  총 {len(updates)}셀 업데이트 완료")
    print(f"  완료: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
