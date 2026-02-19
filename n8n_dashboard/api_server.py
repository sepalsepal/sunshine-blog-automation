#!/usr/bin/env python3
"""Dashboard API Server (Flask)"""
import sqlite3
import json
import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from pathlib import Path
from datetime import datetime

app = Flask(__name__)
CORS(app)

DB_PATH = Path(__file__).parent / "dashboard.db"
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678/webhook/rerun")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/api/runs/latest", methods=["GET"])
def get_latest_run():
    """최신 실행 1개 조회 (폴링용)"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, content_name, status_json, log_text, created_at, completed_at, final_status
        FROM runs ORDER BY id DESC LIMIT 1
    """)
    row = cursor.fetchone()
    conn.close()

    if row:
        return jsonify({
            "id": row["id"],
            "content_name": row["content_name"],
            "status": json.loads(row["status_json"]),
            "log_text": row["log_text"],
            "created_at": row["created_at"],
            "completed_at": row["completed_at"],
            "final_status": row["final_status"]
        })
    return jsonify(None)

@app.route("/api/runs", methods=["GET"])
def get_all_runs():
    """전체 실행 히스토리 조회"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, content_name, status_json, log_text, created_at, completed_at, final_status
        FROM runs ORDER BY id DESC LIMIT 50
    """)
    rows = cursor.fetchall()
    conn.close()

    return jsonify([{
        "id": row["id"],
        "content_name": row["content_name"],
        "status": json.loads(row["status_json"]),
        "log_text": row["log_text"],
        "created_at": row["created_at"],
        "completed_at": row["completed_at"],
        "final_status": row["final_status"]
    } for row in rows])

@app.route("/api/runs/<int:run_id>", methods=["GET"])
def get_run(run_id):
    """특정 실행 조회"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, content_name, status_json, log_text, created_at, completed_at, final_status
        FROM runs WHERE id = ?
    """, (run_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return jsonify({
            "id": row["id"],
            "content_name": row["content_name"],
            "status": json.loads(row["status_json"]),
            "log_text": row["log_text"],
            "created_at": row["created_at"],
            "completed_at": row["completed_at"],
            "final_status": row["final_status"]
        })
    return jsonify({"error": "Run not found"}), 404

@app.route("/api/runs/<int:run_id>/rerun", methods=["POST"])
def rerun_node(run_id):
    """노드 재실행 트리거"""
    data = request.json or {}
    node_name = data.get("node_name")

    # n8n 웹훅 호출 (실제 구현 시)
    # import requests
    # requests.post(N8N_WEBHOOK_URL, json={"run_id": run_id, "node_name": node_name})

    # DB에서 해당 노드 attempts 증가
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT status_json FROM runs WHERE id = ?", (run_id,))
    row = cursor.fetchone()

    if row:
        status = json.loads(row["status_json"])
        for node in status:
            if node["node_name"] == node_name:
                node["attempts"] = node.get("attempts", 0) + 1
                node["status"] = "🔄 재시도중"

        cursor.execute(
            "UPDATE runs SET status_json = ? WHERE id = ?",
            (json.dumps(status, ensure_ascii=False), run_id)
        )
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": f"{node_name} 재실행 트리거됨"})

    conn.close()
    return jsonify({"error": "Run not found"}), 404

@app.route("/api/runs", methods=["POST"])
def create_run():
    """새 실행 생성 (n8n에서 호출)"""
    data = request.json
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO runs (content_name, status_json, log_text, created_at, final_status)
        VALUES (?, ?, ?, ?, ?)
    """, (
        data.get("content_name", "Unknown"),
        json.dumps(data.get("status", []), ensure_ascii=False),
        data.get("log_text", ""),
        datetime.now().isoformat(),
        data.get("final_status", "RUNNING")
    ))

    run_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return jsonify({"id": run_id, "success": True})

@app.route("/api/runs/<int:run_id>", methods=["PATCH"])
def update_run(run_id):
    """실행 상태 업데이트 (n8n에서 호출)"""
    data = request.json
    conn = get_db()
    cursor = conn.cursor()

    updates = []
    params = []

    if "status" in data:
        updates.append("status_json = ?")
        params.append(json.dumps(data["status"], ensure_ascii=False))
    if "log_text" in data:
        updates.append("log_text = ?")
        params.append(data["log_text"])
    if "final_status" in data:
        updates.append("final_status = ?")
        params.append(data["final_status"])
        if data["final_status"] in ["SUCCESS", "FAILED"]:
            updates.append("completed_at = ?")
            params.append(datetime.now().isoformat())

    if updates:
        params.append(run_id)
        cursor.execute(f"UPDATE runs SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()

    conn.close()
    return jsonify({"success": True})

@app.route("/api/health", methods=["GET"])
def health():
    """헬스체크"""
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})

if __name__ == "__main__":
    print("=" * 50)
    print("Dashboard API Server")
    print("http://localhost:5001")
    print("=" * 50)
    app.run(host="0.0.0.0", port=5001, debug=True)
