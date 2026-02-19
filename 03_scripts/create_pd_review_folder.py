#!/usr/bin/env python3
"""
create_pd_review_folder.py - 박PD_확인용 폴더 생성
WO-OVERNIGHT-FINAL Task 5

폴더 구조:
박PD_확인용/
├── README.md
├── PD_APPROVED.json
├── BASELINE_LOCKED.json
├── file_hashes.json
├── PD_REVIEW_SAMPLES.json
├── PD_MANUAL_CHECK.json
├── 01_독성매핑테이블/
├── 02_품질점수기준/
├── 03_캡션템플릿/
├── 04_샘플캡션/
└── 05_야간작업보고/
"""

import os
import sys
import json
import hashlib
import shutil
import random
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
PD_FOLDER = PROJECT_ROOT / "박PD_확인용"

# 원본 파일 경로
FILES = {
    "toxicity_mapping": PROJECT_ROOT / "config" / "toxicity_mapping.json",
    "scoring_criteria": PROJECT_ROOT / "config" / "scoring_criteria.json",
    "quality_judge": PROJECT_ROOT / ".claude" / "agents" / "quality_judge.md",
    "thread_templates": PROJECT_ROOT / "config" / "templates" / "thread_caption_templates.json",
}


def sha256_file(path: Path) -> str:
    """파일 SHA256 해시 계산"""
    if not path.exists():
        return "FILE_NOT_FOUND"
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def create_folder_structure():
    """폴더 구조 생성"""
    subfolders = [
        "01_독성매핑테이블",
        "02_품질점수기준",
        "03_캡션템플릿",
        "04_샘플캡션",
        "05_야간작업보고",
    ]

    PD_FOLDER.mkdir(exist_ok=True)
    for subfolder in subfolders:
        (PD_FOLDER / subfolder).mkdir(exist_ok=True)

    print(f"폴더 구조 생성 완료: {PD_FOLDER}")


def copy_files():
    """파일 복사"""
    # 독성 매핑 테이블
    if FILES["toxicity_mapping"].exists():
        shutil.copy(FILES["toxicity_mapping"], PD_FOLDER / "01_독성매핑테이블" / "toxicity_mapping.json")

    # 품질 점수 기준
    if FILES["scoring_criteria"].exists():
        shutil.copy(FILES["scoring_criteria"], PD_FOLDER / "02_품질점수기준" / "scoring_criteria.json")
    if FILES["quality_judge"].exists():
        shutil.copy(FILES["quality_judge"], PD_FOLDER / "02_품질점수기준" / "quality_judge.md")

    # 캡션 템플릿
    if FILES["thread_templates"].exists():
        shutil.copy(FILES["thread_templates"], PD_FOLDER / "03_캡션템플릿" / "thread_caption_templates.json")

    print("파일 복사 완료")


def create_readme():
    """README.md 생성"""
    content = """# 박PD 확인용 폴더

> 생성일시: {timestamp}
> 작성자: 최부장 (Claude Code)
> 상태: PD 승인 대기

---

## 확인 체크리스트

### 작업 1: 독성 매핑 테이블
- [ ] 11개 카테고리 확인
- [ ] 37개 FORBIDDEN 음식 매핑 확인
- [ ] 출처 URL 확인 (FAIL 항목은 PD_MANUAL_CHECK.json 참조)

### 작업 2: 품질 점수 프로토콜
- [ ] 20점 체계 확인 (각 차원 5점)
- [ ] PASS 조건 확인 (총점 ≥15 AND 각 항목 ≥3)
- [ ] 종료 조건 확인

### 작업 3: food_data.json 수정
- [ ] 36건 FORBIDDEN nutrients 교체 확인
- [ ] diff 로그 확인

### 작업 4: 쓰레드 캡션 템플릿
- [ ] SAFE/CAUTION/FORBIDDEN 템플릿 확인
- [ ] 톤앤매너 적절성 확인

### 작업 5: 전체 검증
- [ ] PD_REVIEW_SAMPLES.json 샘플 검토 (8건)
- [ ] 파일 해시 무결성 확인

---

## 승인 방법

승인하려면 `PD_APPROVED.json`의 `approved` 필드를 `true`로 변경하세요.

```json
{{
  "approved": true,
  "approved_by": "박세준",
  "approved_at": "2026-02-12T09:00:00",
  "batch_allowed": true
}}
```

---

## 파일 목록

- `PD_APPROVED.json` - 승인 상태 (수정 필요)
- `BASELINE_LOCKED.json` - 파일 해시 (읽기 전용)
- `file_hashes.json` - 전체 파일 해시
- `PD_REVIEW_SAMPLES.json` - 랜덤 샘플 8건
- `PD_MANUAL_CHECK.json` - URL 검증 실패 항목

---

_WO-OVERNIGHT-20260211-FINAL_
""".format(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    with open(PD_FOLDER / "README.md", "w", encoding="utf-8") as f:
        f.write(content)

    print("README.md 생성 완료")


def create_pd_approved():
    """PD_APPROVED.json 생성"""
    content = {
        "approved": False,
        "approved_by": None,
        "approved_at": None,
        "batch_allowed": False,
        "notes": "PD 확인 후 approved를 true로 변경하세요"
    }

    with open(PD_FOLDER / "PD_APPROVED.json", "w", encoding="utf-8") as f:
        json.dump(content, f, ensure_ascii=False, indent=2)

    print("PD_APPROVED.json 생성 완료")


def create_baseline_locked():
    """BASELINE_LOCKED.json 생성"""
    hashes = {}
    for name, path in FILES.items():
        hashes[path.name] = sha256_file(path)

    content = {
        "version": "v1",
        "locked_at": datetime.now().isoformat(),
        "files": hashes,
        "status": "READ_ONLY",
        "note": "이 파일의 해시는 변경하지 마세요"
    }

    with open(PD_FOLDER / "BASELINE_LOCKED.json", "w", encoding="utf-8") as f:
        json.dump(content, f, ensure_ascii=False, indent=2)

    print("BASELINE_LOCKED.json 생성 완료")
    return hashes


def create_file_hashes(baseline_hashes: dict):
    """file_hashes.json 생성"""
    content = {
        "created_at": datetime.now().isoformat(),
        "hashes": baseline_hashes
    }

    with open(PD_FOLDER / "file_hashes.json", "w", encoding="utf-8") as f:
        json.dump(content, f, ensure_ascii=False, indent=2)

    print("file_hashes.json 생성 완료")


def create_review_samples(baseline_hashes: dict):
    """PD_REVIEW_SAMPLES.json 생성 (8건 랜덤 샘플)"""
    # seed = SHA256 앞 8자리 + 날짜
    toxicity_hash = baseline_hashes.get("toxicity_mapping.json", "00000000")
    date_str = datetime.now().strftime("%Y%m%d")
    seed_str = toxicity_hash[:8] + date_str
    seed = int(seed_str, 16) % (2**32)
    random.seed(seed)

    # 37개 FORBIDDEN 음식에서 8건 추출
    food_data = json.load(open(PROJECT_ROOT / "config" / "food_data.json"))
    toxicity = json.load(open(PROJECT_ROOT / "config" / "toxicity_mapping.json"))

    forbidden_ids = []
    for fid, data in food_data.items():
        if data.get("safety", "").upper() == "FORBIDDEN":
            forbidden_ids.append(int(fid))

    sample_ids = random.sample(forbidden_ids, min(8, len(forbidden_ids)))

    samples = []
    for fid in sample_ids:
        fid_str = str(fid)
        food_info = food_data.get(fid_str, {})
        tox_info = toxicity.get("food_mapping", {}).get(fid_str, {})

        # 출처 URL 가져오기
        primary_toxin = tox_info.get("primary_toxin", "")
        source_urls = []
        if primary_toxin and primary_toxin in toxicity.get("toxicity_categories", {}):
            sources = toxicity["toxicity_categories"][primary_toxin].get("sources", [])
            source_urls = [s.get("url") for s in sources]

        samples.append({
            "food_id": fid,
            "food_name": food_info.get("name", "Unknown"),
            "safety": food_info.get("safety", ""),
            "primary_toxin": primary_toxin,
            "toxic_compounds": tox_info.get("toxic_compounds", []),
            "source_urls": source_urls
        })

    content = {
        "created_at": datetime.now().isoformat(),
        "seed": seed_str,
        "total_samples": len(samples),
        "extraction_rule": "37개 FORBIDDEN 중 20% = 8건 랜덤 추출",
        "samples": samples
    }

    with open(PD_FOLDER / "PD_REVIEW_SAMPLES.json", "w", encoding="utf-8") as f:
        json.dump(content, f, ensure_ascii=False, indent=2)

    print(f"PD_REVIEW_SAMPLES.json 생성 완료 ({len(samples)}건)")


def create_sample_captions():
    """샘플 캡션 복사"""
    # SAFE 샘플: #136 참외
    # 2026-02-13: 플랫 구조 - 경로 업데이트
    safe_paths = [
        PROJECT_ROOT / "01_contents" / "136_chamoe" / "02_Blog" / "caption.txt",
        PROJECT_ROOT / "01_contents" / "136_chamoe" / "01_Insta&Thread" / "caption.txt",
    ]
    for path in safe_paths:
        if path.exists():
            shutil.copy(path, PD_FOLDER / "04_샘플캡션" / "SAFE_참외_sample.txt")
            break

    # FORBIDDEN 샘플: #127 대파
    # 2026-02-13: 플랫 구조 - 경로 업데이트
    forbidden_paths = [
        PROJECT_ROOT / "01_contents" / "127_green_onion" / "02_Blog" / "caption.txt",
        PROJECT_ROOT / "01_contents" / "127_green_onion" / "01_Insta&Thread" / "caption.txt",
    ]
    for path in forbidden_paths:
        if path.exists():
            shutil.copy(path, PD_FOLDER / "04_샘플캡션" / "FORBIDDEN_대파_sample.txt")
            break

    print("샘플 캡션 복사 완료")


def create_overnight_report():
    """야간 작업 보고서 복사/생성"""
    # 기존 보고서가 있으면 복사
    existing_report = PROJECT_ROOT / "logs" / "WO-OVERNIGHT-20260211-v2_REPORT.md"
    if existing_report.exists():
        shutil.copy(existing_report, PD_FOLDER / "05_야간작업보고" / "overnight_report.md")

    # 요약 보고서 생성
    summary = """# WO-OVERNIGHT-20260211-FINAL 완료 보고

> 작성일시: {timestamp}
> 작성자: 최부장 (Claude Code)

---

## 작업 요약

| Task | 항목 | 상태 | 비고 |
|------|------|------|------|
| 1 | 독성 매핑 테이블 | ✅ 완료 | 11개 카테고리, 37개 음식, URL 검증 (15/19 PASS) |
| 2 | 품질 점수 프로토콜 | ✅ 완료 | 20점 체계, FAIL 코드 정의 |
| 3 | food_data.json 수정 | ✅ 완료 | 36건 수정, diff 로그 기록 |
| 4 | 쓰레드 캡션 템플릿 | ✅ 완료 | SAFE/CAUTION/FORBIDDEN 3종 |
| 5 | 전체 검증 + PD 폴더 | ✅ 완료 | 이 문서 |

---

## URL 검증 결과

- 총 URL: 19개
- PASS: 15개
- FAIL: 4개 (PD_MANUAL_CHECK.json 참조)

---

## 승인 대기

PD_APPROVED.json에서 `approved: true`로 변경 후 배치 실행 가능.

---

_WO-OVERNIGHT-20260211-FINAL_
""".format(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    with open(PD_FOLDER / "05_야간작업보고" / "summary_report.md", "w", encoding="utf-8") as f:
        f.write(summary)

    print("야간 작업 보고서 생성 완료")


def set_readonly():
    """baseline 파일 읽기 전용 설정"""
    baseline_files = [
        PD_FOLDER / "BASELINE_LOCKED.json",
        PD_FOLDER / "file_hashes.json",
    ]

    for path in baseline_files:
        if path.exists():
            os.chmod(path, 0o444)
            print(f"chmod 444: {path.name}")


def main():
    print("=" * 60)
    print("박PD_확인용 폴더 생성")
    print("=" * 60)

    create_folder_structure()
    copy_files()
    create_readme()
    create_pd_approved()
    baseline_hashes = create_baseline_locked()
    create_file_hashes(baseline_hashes)
    create_review_samples(baseline_hashes)
    create_sample_captions()
    create_overnight_report()
    set_readonly()

    print("\n" + "=" * 60)
    print("완료!")
    print(f"폴더: {PD_FOLDER}")
    print("=" * 60)


if __name__ == "__main__":
    main()
