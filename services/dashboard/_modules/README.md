# Dashboard Modules

## 현재 구조 (v5.2)

```
services/dashboard/
├── app.py                 # 메인 앱 (2037줄) - 분리 필요
├── _modules/
│   ├── __init__.py
│   ├── api_costs.py       # API 비용 뷰
│   ├── calendar_view.py   # 캘린더 뷰
│   └── gallery_view.py    # 갤러리 뷰
└── .thumbs/               # 썸네일 캐시
```

## 분리 계획 (v6.0 예정)

### app.py → 모듈 분리

| 함수 | 현재 위치 | 대상 모듈 | 줄 수 |
|------|----------|----------|-------|
| `show_dashboard()` | app.py:976 | dashboard_view.py | ~160 |
| `show_content_hub()` | app.py:1165 | content_hub.py | ~120 |
| `render_content_card()` | app.py:1246 | content_hub.py | ~40 |
| `render_detail_view()` | app.py:1287 | content_hub.py | ~80 |
| `render_gallery_modal()` | app.py:1367 | content_hub.py | ~190 |
| `show_production()` | app.py:1562 | production_view.py | ~250 |
| `render_pipeline_row()` | app.py:1810 | production_view.py | ~30 |
| `show_settings()` | app.py:1960 | settings_view.py | ~80 |

### 예상 결과

```
_modules/
├── dashboard_view.py    # 대시보드 (~200줄)
├── content_hub.py       # 콘텐츠 허브 (~450줄)
├── production_view.py   # 제작 (~300줄)
├── settings_view.py     # 설정 (~100줄)
├── api_costs.py         # API 비용 (기존)
├── calendar_view.py     # 캘린더 (기존)
└── gallery_view.py      # 갤러리 (기존)
```

### app.py 최종 목표: ~500줄
- 페이지 라우팅
- 공통 스타일
- 세션 관리
- 유틸리티 함수

## 우선순위

1. **P1**: content_hub.py 분리 (가장 큼)
2. **P2**: production_view.py 분리
3. **P3**: dashboard_view.py 분리
4. **P4**: settings_view.py 분리

## 작성일
2026-01-30
