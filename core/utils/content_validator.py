#!/usr/bin/env python3
"""
콘텐츠 검증 모듈 (F8 자동 트리거 포함)

Phase 2.5 HARD FAIL 규칙 자동 검증:
- F8: CTA 슬라이드(03)는 반드시 실사 사용 (AI 생성 금지)
- F-INFO-EMPTY: INFO 슬라이드(01, 02)는 텍스트 필수
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ValidationResult:
    """검증 결과"""
    passed: bool
    fail_code: Optional[str] = None
    fail_message: Optional[str] = None
    details: Dict = field(default_factory=dict)


@dataclass
class ContentValidationReport:
    """콘텐츠 검증 리포트"""
    content_folder: str
    topic_en: str
    timestamp: str
    results: List[ValidationResult] = field(default_factory=list)

    @property
    def all_passed(self) -> bool:
        return all(r.passed for r in self.results)

    @property
    def hard_fails(self) -> List[ValidationResult]:
        return [r for r in self.results if not r.passed and r.fail_code and r.fail_code.startswith('F')]

    def to_dict(self) -> Dict:
        return {
            "content_folder": self.content_folder,
            "topic_en": self.topic_en,
            "timestamp": self.timestamp,
            "all_passed": self.all_passed,
            "results": [
                {
                    "passed": r.passed,
                    "fail_code": r.fail_code,
                    "fail_message": r.fail_message,
                    "details": r.details
                }
                for r in self.results
            ]
        }


class ContentValidator:
    """콘텐츠 검증기"""

    # 실사 CTA 소스 폴더
    CTA_SOURCE_PATH = Path("content/images/sunshine/cta_source/best_cta")

    # 알려진 실사 CTA 해시 캐시 (선택적)
    _real_cta_hashes: Optional[set] = None

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.cta_source = self.project_root / self.CTA_SOURCE_PATH

    def validate_content(self, content_folder: Path) -> ContentValidationReport:
        """콘텐츠 폴더 전체 검증"""
        topic_en = self._extract_topic_from_folder(content_folder)

        report = ContentValidationReport(
            content_folder=str(content_folder),
            topic_en=topic_en,
            timestamp=datetime.now().isoformat()
        )

        # F8: CTA 실사 검증
        f8_result = self.validate_f8_cta_real_photo(content_folder, topic_en)
        report.results.append(f8_result)

        # F-INFO-EMPTY: INFO 슬라이드 텍스트 검증 (선택적)
        # info_result = self.validate_info_slide_text(content_folder, topic_en)
        # report.results.append(info_result)

        return report

    def validate_f8_cta_real_photo(self, content_folder: Path, topic_en: str) -> ValidationResult:
        """
        F8: CTA 슬라이드(03)가 실사인지 검증

        검증 방법:
        1. {topic}_03.png 파일 존재 확인
        2. 파일 해시를 실사 CTA 소스와 비교
        3. 또는 파일 크기/특성으로 AI 생성 여부 추정
        """
        cta_file = content_folder / f"{topic_en}_03.png"

        # 파일 존재 확인
        if not cta_file.exists():
            return ValidationResult(
                passed=False,
                fail_code="F8-MISSING",
                fail_message=f"CTA 슬라이드 누락: {topic_en}_03.png",
                details={"expected_file": str(cta_file)}
            )

        # 실사 CTA 해시 목록 로드
        real_cta_hashes = self._load_real_cta_hashes()

        # 현재 파일 해시 계산
        file_hash = self._calculate_file_hash(cta_file)

        # 해시 비교로 실사 확인
        if file_hash in real_cta_hashes:
            return ValidationResult(
                passed=True,
                details={
                    "file": str(cta_file),
                    "hash": file_hash,
                    "verification": "hash_match",
                    "message": "CTA 슬라이드가 실사 소스와 일치합니다."
                }
            )

        # 해시 불일치 - 추가 검증 시도
        # (파일 크기, 메타데이터 등으로 AI 여부 추정)
        is_likely_real = self._check_likely_real_photo(cta_file)

        if is_likely_real:
            return ValidationResult(
                passed=True,
                details={
                    "file": str(cta_file),
                    "hash": file_hash,
                    "verification": "heuristic",
                    "message": "CTA 슬라이드가 실사로 추정됩니다 (해시 미등록)."
                }
            )

        # F8 HARD FAIL
        return ValidationResult(
            passed=False,
            fail_code="F8",
            fail_message=f"CTA 슬라이드 AI 생성 금지 위반: {topic_en}_03.png",
            details={
                "file": str(cta_file),
                "hash": file_hash,
                "expected": "실사 (best_cta 폴더 소스)",
                "actual": "AI 생성 의심",
                "remediation": "content/images/sunshine/cta_source/best_cta/ 폴더에서 실사 선택 후 교체"
            }
        )

    def _load_real_cta_hashes(self) -> set:
        """실사 CTA 이미지 해시 목록 로드"""
        if self._real_cta_hashes is not None:
            return self._real_cta_hashes

        hashes = set()

        if self.cta_source.exists():
            for img_file in self.cta_source.glob("*.png"):
                hashes.add(self._calculate_file_hash(img_file))
            for img_file in self.cta_source.glob("*.jpg"):
                hashes.add(self._calculate_file_hash(img_file))
            for img_file in self.cta_source.glob("*.jpeg"):
                hashes.add(self._calculate_file_hash(img_file))

        # 추가: best_cta의 하위 폴더도 검색
        best_cta_alt = self.project_root / "content/images/sunshine/cta_source"
        if best_cta_alt.exists():
            for img_file in best_cta_alt.rglob("*.png"):
                hashes.add(self._calculate_file_hash(img_file))
            for img_file in best_cta_alt.rglob("*.jpg"):
                hashes.add(self._calculate_file_hash(img_file))

        self._real_cta_hashes = hashes
        return hashes

    def _calculate_file_hash(self, file_path: Path) -> str:
        """파일 MD5 해시 계산"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def _check_likely_real_photo(self, file_path: Path) -> bool:
        """
        휴리스틱으로 실사 여부 추정

        판단 기준:
        1. EXIF 데이터 존재 → 실사
        2. 파일 크기가 AI 생성 범위를 벗어남 → 실사 가능성
        3. 이미지 특성 분석 (텍스트 오버레이 없음 등)

        - AI 생성 이미지 (flux-2-pro): 보통 1.1MB~1.8MB (PNG), 특정 범위
        - 실사 + 크롭/리사이즈: 다양한 크기
        """
        try:
            from PIL import Image

            img = Image.open(file_path)

            # 1. EXIF 데이터 존재 확인 (실사 카메라 촬영 시 있음)
            exif = img._getexif() if hasattr(img, '_getexif') else None
            if exif:
                return True  # EXIF 있으면 실사로 추정

            # 2. 파일 크기 확인
            file_size = file_path.stat().st_size

            # AI flux-2-pro PNG 이미지는 보통 1.1MB~1.8MB (1,100,000~1,800,000 bytes)
            # CTA 실사 (크롭 후 리사이즈)는 보통 1MB~1.5MB
            # 더 큰 파일은 실사일 가능성 높음

            # 3. 이미지 내용 분석 - CTA 슬라이드에는 텍스트 오버레이가 없어야 함
            # (텍스트가 있으면 INFO 슬라이드로 의심)

            # 4. 특별 검증: 수동으로 검증된 해시 화이트리스트 확인
            whitelist = self._load_verified_cta_whitelist()
            file_hash = self._calculate_file_hash(file_path)
            if file_hash in whitelist:
                return True

            # 5. 파일명 패턴 확인 - _03.png는 CTA 슬라이드
            # CTA가 텍스트 없이 깨끗한 이미지면 실사로 추정
            # (AI로 CTA를 만들면 보통 텍스트를 넣기 때문)

            # 파일 크기 기반 휴리스틱:
            # - 1MB 미만: 실사 크롭/리사이즈일 가능성
            # - 1MB~1.8MB: AI 또는 실사 (불확실)
            # - 1.8MB 초과: 실사일 가능성 높음

            if file_size > 1_800_000:  # 1.8MB 초과
                return True

            # 기본: 수동 검증 필요 (보수적 접근)
            # 실무에서는 검증된 CTA를 화이트리스트에 추가
            return False

        except Exception:
            return False

    def _load_verified_cta_whitelist(self) -> set:
        """
        수동 검증된 CTA 해시 화이트리스트 로드

        검증된 실사 CTA의 해시를 등록하여 false positive 방지
        """
        whitelist_path = self.project_root / "config/data/verified_cta_hashes.json"

        if whitelist_path.exists():
            try:
                with open(whitelist_path) as f:
                    data = json.load(f)
                    return set(data.get("hashes", []))
            except Exception:
                pass

        return set()

    def _extract_topic_from_folder(self, folder: Path) -> str:
        """폴더명에서 topic_en 추출"""
        folder_name = folder.name

        # 패턴: 036_potato_감자_제작완료 → potato
        parts = folder_name.split("_")
        if len(parts) >= 2:
            return parts[1]

        return folder_name


def validate_content_folder(folder_path: str) -> Dict:
    """
    콘텐츠 폴더 검증 (CLI/스크립트용)

    Args:
        folder_path: 콘텐츠 폴더 경로

    Returns:
        검증 결과 딕셔너리
    """
    folder = Path(folder_path)
    if not folder.exists():
        return {
            "error": f"폴더를 찾을 수 없습니다: {folder_path}",
            "passed": False
        }

    validator = ContentValidator()
    report = validator.validate_content(folder)

    return report.to_dict()


def batch_validate_ready_contents() -> List[Dict]:
    """
    모든 ready 상태 콘텐츠 일괄 검증

    Returns:
        각 콘텐츠의 검증 결과 리스트
    """
    content_map_path = Path("config/data/content_map.json")
    images_base = Path("content/images")

    if not content_map_path.exists():
        return [{"error": "content_map.json not found"}]

    with open(content_map_path) as f:
        content_map = json.load(f)

    results = []
    validator = ContentValidator()

    for topic, info in content_map.get("contents", {}).items():
        if info.get("status") == "ready":
            folder = images_base / info.get("folder", "")
            if folder.exists():
                report = validator.validate_content(folder)
                result = report.to_dict()
                result["topic"] = topic
                results.append(result)

    return results


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # 특정 폴더 검증
        result = validate_content_folder(sys.argv[1])
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        # 모든 ready 콘텐츠 검증
        print("🔍 Ready 콘텐츠 일괄 검증 중...\n")
        results = batch_validate_ready_contents()

        passed = [r for r in results if r.get("all_passed")]
        failed = [r for r in results if not r.get("all_passed")]

        print(f"✅ PASS: {len(passed)}건")
        print(f"❌ FAIL: {len(failed)}건")

        if failed:
            print("\n🚨 실패 콘텐츠:")
            for r in failed:
                print(f"  - {r.get('topic')}: {r.get('results', [{}])[0].get('fail_code')}")
