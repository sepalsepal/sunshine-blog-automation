import gspread
from datetime import datetime
import json
import os
from dotenv import load_dotenv

load_dotenv()

# ⚠️ [주의] 구글 서비스 계정 키 파일이 있어야 작동합니다.
# 파일명: google_service_account.json
SERVICE_ACCOUNT_FILE = 'google_service_account.json'
SHEET_NAME = os.getenv("ARCHIVE_SHEET_NAME", "Antigravity_Post_Archive")

import streamlit as st

def _get_sheet_client():
    try:
        # 1. 로컬 파일 확인
        if os.path.exists(SERVICE_ACCOUNT_FILE):
            gc = gspread.service_account(filename=SERVICE_ACCOUNT_FILE)
            return gc
            
        # 2. Streamlit Cloud Secrets 확인
        if "google_credentials" in st.secrets:
            # st.secrets는 AttrDict 형태일 수 있으므로 dict로 변환
            creds_dict = dict(st.secrets["google_credentials"])
            gc = gspread.service_account_from_dict(creds_dict)
            return gc
            
        print(f"⚠️ 인증 파일 '{SERVICE_ACCOUNT_FILE}'이 없고, Secrets 설정도 없습니다.")
        return None
    except Exception as e:
        print(f"❌ 구글 시트 인증 에러: {e}")
        return None

def _get_or_create_worksheet(gc, sheet_name):
    try:
        sh = gc.open(sheet_name)
    except gspread.SpreadsheetNotFound:
        sh = gc.create(sheet_name)
        print(f"✅ 새 시트 생성됨: {sh.url}")
        # (주의: 서비스 계정 이메일로 생성되므로, 본인 계정에 공유해야 함)
    return sh.sheet1

def archive_post(title, content, link, topic):
    """게시물 정보 저장"""
    gc = _get_sheet_client()
    
    archive_data = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "topic": topic,
        "title": title,
        "link": link
    }
    
    if not gc:
        # Google Sheets 실패 시 로컬 백업
        return _local_backup(archive_data)

    try:
        wks = _get_or_create_worksheet(gc, SHEET_NAME)
        
        # 헤더 확인 및 생성
        header = ["ID", "Date", "Topic", "Title", "Link"]
        if wks.row_values(1) != header:
            wks.insert_row(header, 1)

        # 데이터 추가
        next_id = len(wks.get_all_values()) # 간단 ID 생성
        row = [
            next_id,
            archive_data["date"],
            topic,
            title,
            link
        ]
        wks.append_row(row)
        print(f"✅ 아카이빙 성공: {title}")
        return True
        
    except Exception as e:
        print(f"❌ 아카이빙 실패: {e}")
        # 실패 시 로컬 백업
        return _local_backup(archive_data)


def _local_backup(data):
    """
    Google Sheets 실패 시 로컬 JSON 백업
    파일: archive_backup.json
    """
    BACKUP_FILE = "archive_backup.json"
    
    try:
        # 기존 데이터 로드
        if os.path.exists(BACKUP_FILE):
            with open(BACKUP_FILE, 'r', encoding='utf-8') as f:
                backup_list = json.load(f)
        else:
            backup_list = []
        
        # 데이터 추가
        data['id'] = len(backup_list) + 1
        backup_list.append(data)
        
        # 저장
        with open(BACKUP_FILE, 'w', encoding='utf-8') as f:
            json.dump(backup_list, f, ensure_ascii=False, indent=2)
        
        print(f"💾 로컬 백업 저장됨: {BACKUP_FILE} (총 {len(backup_list)}개)")
        return True
        
    except Exception as e:
        print(f"❌ 로컬 백업도 실패: {e}")
        return False


def get_backup_count():
    """로컬 백업 개수 확인"""
    BACKUP_FILE = "archive_backup.json"
    if os.path.exists(BACKUP_FILE):
        with open(BACKUP_FILE, 'r', encoding='utf-8') as f:
            return len(json.load(f))
    return 0

