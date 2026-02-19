# Project Sunshine Dashboard MVP v1.1

## 실행 방법

```bash
cd dashboard
./start.sh
```

또는 수동 실행:
```bash
cd dashboard
source venv/bin/activate
python3 api_server.py &
python3 -m http.server 8080
```

## 접속

- **Dashboard UI**: http://localhost:8080
- **API Server**: http://localhost:5001

## API 엔드포인트

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/health` | 헬스체크 |
| GET | `/api/runs/latest` | 최신 실행 1개 (폴링용) |
| GET | `/api/runs` | 전체 실행 히스토리 |
| GET | `/api/runs/:id` | 특정 실행 상세 |
| POST | `/api/runs` | 새 실행 생성 (n8n용) |
| PATCH | `/api/runs/:id` | 실행 상태 업데이트 |
| POST | `/api/runs/:id/rerun` | 노드 재실행 트리거 |

## 파일 구조

```
dashboard/
├── index.html        # React + Tailwind UI
├── api_server.py     # Flask API 서버
├── init_db.py        # DB 초기화 스크립트
├── rules_parser.py   # RULES.md 파서
├── dashboard.db      # SQLite DB
├── start.sh          # 시작 스크립트
├── venv/             # Python 가상환경
└── README.md
```

## DB 스키마

```sql
CREATE TABLE runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content_name TEXT NOT NULL,
    status_json JSON NOT NULL,
    log_text TEXT NOT NULL,
    created_at DATETIME NOT NULL,
    completed_at DATETIME,
    final_status TEXT
);
```

## n8n 연동

n8n에서 Dashboard로 상태 전송:

```javascript
// 새 실행 시작
POST /api/runs
{
    "content_name": "035_감자",
    "status": [...],
    "log_text": "",
    "final_status": "RUNNING"
}

// 상태 업데이트
PATCH /api/runs/:id
{
    "status": [...],
    "log_text": "노드 완료",
    "final_status": "SUCCESS"
}
```
