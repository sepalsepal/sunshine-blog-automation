#!/usr/bin/env python3
"""Dashboard DB 초기화 + 샘플 데이터"""
import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent / "dashboard.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # runs 테이블 생성
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content_name TEXT NOT NULL,
            status_json JSON NOT NULL,
            log_text TEXT NOT NULL,
            created_at DATETIME NOT NULL,
            completed_at DATETIME,
            final_status TEXT
        )
    """)

    conn.commit()
    print("✅ DB 테이블 생성 완료")
    return conn

def insert_sample_data(conn):
    cursor = conn.cursor()

    # 샘플 1: 완료된 실행
    sample1_status = [
        {"node_name": "입력", "agent": "김차장", "applied_rules": ["00룰"], "status": "✅ 완료", "failed_reason": None, "attempts": 0},
        {"node_name": "텍스트작성", "agent": "김작가", "applied_rules": ["01룰", "02룰"], "status": "✅ 완료", "failed_reason": None, "attempts": 0},
        {"node_name": "이미지생성", "agent": "이디자이너", "applied_rules": ["03룰"], "status": "✅ 완료", "failed_reason": None, "attempts": 0},
        {"node_name": "검증", "agent": "박검수", "applied_rules": ["04룰", "05룰"], "status": "✅ 완료", "failed_reason": None, "attempts": 0},
    ]

    cursor.execute("""
        INSERT INTO runs (content_name, status_json, log_text, created_at, completed_at, final_status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        "001_호박",
        json.dumps(sample1_status, ensure_ascii=False),
        "모든 노드 정상 완료",
        (datetime.now() - timedelta(hours=2)).isoformat(),
        (datetime.now() - timedelta(hours=1, minutes=45)).isoformat(),
        "SUCCESS"
    ))

    # 샘플 2: 실패한 실행
    sample2_status = [
        {"node_name": "입력", "agent": "김차장", "applied_rules": ["00룰"], "status": "✅ 완료", "failed_reason": None, "attempts": 0},
        {"node_name": "텍스트작성", "agent": "김작가", "applied_rules": ["01룰", "02룰"], "status": "❌ 실패", "failed_reason": "마침표 누락", "attempts": 1},
        {"node_name": "이미지생성", "agent": "이디자이너", "applied_rules": ["03룰"], "status": "⏸️ 대기", "failed_reason": None, "attempts": 0},
        {"node_name": "검증", "agent": "박검수", "applied_rules": ["04룰", "05룰"], "status": "⏸️ 대기", "failed_reason": None, "attempts": 0},
    ]

    cursor.execute("""
        INSERT INTO runs (content_name, status_json, log_text, created_at, completed_at, final_status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        "035_감자",
        json.dumps(sample2_status, ensure_ascii=False),
        "텍스트작성 노드에서 실패: 01룰 위반 (마침표 누락)",
        (datetime.now() - timedelta(minutes=30)).isoformat(),
        None,
        "FAILED"
    ))

    # 샘플 3: 진행 중인 실행
    sample3_status = [
        {"node_name": "입력", "agent": "김차장", "applied_rules": ["00룰"], "status": "✅ 완료", "failed_reason": None, "attempts": 0},
        {"node_name": "텍스트작성", "agent": "김작가", "applied_rules": ["01룰", "02룰"], "status": "✅ 완료", "failed_reason": None, "attempts": 0},
        {"node_name": "이미지생성", "agent": "이디자이너", "applied_rules": ["03룰"], "status": "🔄 진행중", "failed_reason": None, "attempts": 0},
        {"node_name": "검증", "agent": "박검수", "applied_rules": ["04룰", "05룰"], "status": "⏸️ 대기", "failed_reason": None, "attempts": 0},
    ]

    cursor.execute("""
        INSERT INTO runs (content_name, status_json, log_text, created_at, completed_at, final_status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        "057_초콜릿",
        json.dumps(sample3_status, ensure_ascii=False),
        "이미지생성 진행 중...",
        datetime.now().isoformat(),
        None,
        "RUNNING"
    ))

    conn.commit()
    print("✅ 샘플 데이터 3개 삽입 완료")

def verify_data(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT id, content_name, final_status FROM runs")
    rows = cursor.fetchall()

    print("\n📋 DB 검증:")
    for row in rows:
        print(f"  ID={row[0]}, 콘텐츠={row[1]}, 상태={row[2]}")

    return len(rows) > 0

if __name__ == "__main__":
    print("=" * 50)
    print("Dashboard DB 초기화")
    print("=" * 50)

    conn = init_db()
    insert_sample_data(conn)
    success = verify_data(conn)
    conn.close()

    print()
    if success:
        print("✅ DB 생성 + 샘플 데이터 완료")
    else:
        print("❌ 검증 실패")
