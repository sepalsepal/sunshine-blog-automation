# Rule Versioning Policy

> 규칙 버전 관리 정책입니다.
> v2 규칙이 나올 때 과거 콘텐츠가 갑자기 FAIL 되는 사고를 방지합니다.

---

## 핵심 원칙

### 1. 생성 규칙과 검증 규칙은 동일 버전이어야 한다

```
생성 시: cover_v1 규칙으로 생성
검증 시: cover_v1 규칙으로 검증

❌ cover_v1으로 생성 → cover_v2로 검증 (버전 불일치)
```

### 2. 과거 콘텐츠는 생성 당시 규칙으로만 검증한다

```
2026-01-20 생성 콘텐츠 → cover_v1 검증
2026-02-10 생성 콘텐츠 → cover_v2 검증 (v2 출시 후)

❌ 2026-01-20 콘텐츠를 cover_v2로 재검증
```

---

## 메타데이터 필수 필드

### 생성 시 기록

```json
{
  "food_id": "celery",
  "rule_name": "cover_v1",
  "rule_version": "1.0.0",
  "rule_hash": "1b1c6f1a23f68664",
  "created_at": "2026-02-03T14:00:00"
}
```

| 필드 | 용도 |
|------|------|
| `rule_name` | 어떤 규칙인지 (cover_v1, body_safe_v1) |
| `rule_version` | 세부 버전 (1.0.0, 1.0.1) |
| `rule_hash` | 규칙 파일 해시 (변조 감지) |

---

## 검증 조건

### 버전 일치 검증

```python
def verify_rule_version(image_metadata, verifier):
    """규칙 버전 일치 여부 확인"""
    
    image_version = image_metadata.get('rule_version')
    supported_version = verifier.supported_version
    
    if image_version != supported_version:
        return {
            "pass": False,
            "reason": "RULE_VERSION_MISMATCH",
            "detail": f"이미지: {image_version}, 검증기: {supported_version}"
        }
    
    return {"pass": True}
```

### 해시 일치 검증

```python
def verify_rule_hash(image_metadata, current_rule_hash):
    """규칙 해시 일치 여부 확인"""
    
    image_hash = image_metadata.get('rule_hash')
    
    if image_hash != current_rule_hash:
        return {
            "pass": False,
            "reason": "RULE_HASH_MISMATCH",
            "detail": f"이미지: {image_hash}, 현재: {current_rule_hash}"
        }
    
    return {"pass": True}
```

---

## 버전 업데이트 시나리오

### 시나리오 1: 마이너 업데이트 (1.0.0 → 1.0.1)

```
변경 내용: 오타 수정, 설명 보완
영향: 없음
조치: rule_hash만 업데이트

기존 콘텐츠: 그대로 PASS
신규 콘텐츠: 새 hash로 생성
```

### 시나리오 2: 메이저 업데이트 (v1 → v2)

```
변경 내용: 레이아웃 변경, 필수 요소 추가
영향: 기존 콘텐츠와 호환 불가
조치: 
  - 새 rule_name (cover_v2)
  - 기존 콘텐츠는 cover_v1 검증기로 계속 검증
  - 신규 콘텐츠만 cover_v2 적용
```

### 버전 호환성 매트릭스

```
┌─────────────┬─────────────┬─────────────┐
│  생성 규칙   │  검증 규칙   │    결과     │
├─────────────┼─────────────┼─────────────┤
│  cover_v1   │  cover_v1   │  ✅ PASS    │
│  cover_v1   │  cover_v2   │  ❌ BLOCK   │
│  cover_v2   │  cover_v1   │  ❌ BLOCK   │
│  cover_v2   │  cover_v2   │  ✅ PASS    │
└─────────────┴─────────────┴─────────────┘
```

---

## 규칙 파일 구조

### 현재 규칙 목록

```
config/rules/
├── cover_v1.json          # 표지 규칙 v1
├── body_safe_v1.json      # SAFE 본문 규칙 v1
├── body_caution_v1.json   # CAUTION 본문 규칙 v1
├── body_danger_v1.json    # DANGER 본문 규칙 v1
└── versions.json          # 버전 관리 메타
```

### versions.json 예시

```json
{
  "current": {
    "cover": "cover_v1",
    "body_safe": "body_safe_v1",
    "body_caution": "body_caution_v1",
    "body_danger": "body_danger_v1"
  },
  "supported": ["v1"],
  "deprecated": [],
  "history": [
    {
      "version": "v1",
      "released": "2026-02-02",
      "status": "active"
    }
  ]
}
```

---

## 오폭 방지 체크리스트

새 규칙 버전 출시 전 확인:

- [ ] 기존 콘텐츠 검증기 유지되는가?
- [ ] 버전 불일치 시 BLOCK 처리되는가?
- [ ] 신규 콘텐츠만 새 규칙 적용되는가?
- [ ] versions.json 업데이트했는가?
- [ ] 변경 사항 문서화했는가?

---

**작성:** 김부장 + 레드2
**승인:** 박세준 PD
**버전:** 1.0.0
**날짜:** 2026-02-03
