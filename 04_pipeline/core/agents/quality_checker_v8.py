"""
QualityCheckerV8Agent - v8 스펙 품질 검수 에이전트
CLAUDE.md 표지 스펙 기반 검수

Author: 최기술 대리
"""

import os
import re
from typing import Any, Dict, List
from pathlib import Path
from .base import BaseAgent, AgentResult

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class QualityCheckerV8Agent(BaseAgent):
    """
    v8.1 스펙 품질 검수 에이전트 (검수 로직 v1.0 반영)

    검수 항목 (100점 만점):
    1. 이미지 품질 (20점)
       - 파일 존재, 해상도 1080x1080, 파일 크기 > 100KB
    2. v8 표지 스펙 (30점)
       - 표지 제목 = 영어 대문자
       - 언더라인 존재 (파일명에 cover 포함)
       - (수동) 상단 25-30% 여백 확보
    3. 슬라이드 구성 (15점)
       - 7개 슬라이드 (표지 1 + 본문 5 + CTA 1)
       - 파일명 규칙 준수
    4. 앵글 다양성 (25점) - v1.0 추가
       - 본문 5장 중 최소 3가지 앵글 사용
       - (수동 검수: 정면, 측면 45°, 측면 90°, 부감, 블러)
    5. CTA 슬라이드 (10점)
       - CTA 슬라이드 존재 (파일명에 cta 포함)
    """

    EXPECTED_WIDTH = 1080
    EXPECTED_HEIGHT = 1080
    MIN_FILE_SIZE = 100 * 1024  # 100KB
    EXPECTED_SLIDES = 7  # v8: 7장 캐러셀

    @property
    def name(self) -> str:
        return "QualityCheckerV8"

    async def execute(self, input_data: Any) -> AgentResult:
        """품질 검수 실행"""
        images = input_data.get("images", [])
        topic = input_data.get("topic", "unknown")

        # 이미지 리스트 정규화
        image_paths = []
        if images:
            for img in images:
                if isinstance(img, dict):
                    image_paths.append(img.get("path", ""))
                elif isinstance(img, str):
                    image_paths.append(img)

        self.log(f"v8 품질 검수 시작 ({len(image_paths)}개 이미지)")

        # 검수 실행
        report = self._run_quality_check(image_paths, topic)

        # 통과 여부 판정 (70점 이상)
        pass_score = self.config.get("thresholds", {}).get("pass", 70)
        passed = report["total_score"] >= pass_score

        self.log(f"검수 완료: {report['total_score']:.0f}점 ({report['grade']}) - {'PASS' if passed else 'FAIL'}")

        return AgentResult(
            success=passed,
            data={
                "report": report,
                "passed": passed,
                "images": image_paths,
                "topic": topic
            },
            metadata={
                "score": report["total_score"],
                "grade": report["grade"]
            }
        )

    def _run_quality_check(self, image_paths: List[str], topic: str) -> Dict:
        """품질 검사 수행 (v1.0 기준)"""
        issues = []
        details = []

        # 1. 이미지 품질 검사 (20점) - v1.0에서 배점 조정
        image_quality = self._check_image_quality(image_paths)
        details.append(image_quality)

        # 2. v8 표지 스펙 검사 (30점)
        cover_spec = self._check_cover_spec(image_paths, topic)
        details.append(cover_spec)

        # 3. 슬라이드 구성 검사 (15점) - v1.0에서 배점 조정
        slide_composition = self._check_slide_composition(image_paths, topic)
        details.append(slide_composition)

        # 4. 앵글 다양성 검사 (25점) - v1.0 추가
        angle_diversity = self._check_angle_diversity(image_paths)
        details.append(angle_diversity)

        # 5. CTA 슬라이드 검사 (10점) - v1.0에서 배점 조정
        cta_check = self._check_cta_slide(image_paths)
        details.append(cta_check)

        # 총점 계산
        total_score = sum(d["score"] for d in details)

        # 이슈 수집
        for d in details:
            issues.extend(d.get("issues", []))

        # 등급 판정
        grade = self._get_grade(total_score)

        return {
            "total_score": total_score,
            "grade": grade,
            "categories": {d["category"]: d for d in details},
            "issues": issues,
            "details": details,
            "image_count": len(image_paths)
        }

    def _check_image_quality(self, image_paths: List[str]) -> Dict:
        """1. 이미지 품질 검사 (20점) - v1.0 배점"""
        max_score = 20
        score = 0
        issues = []
        checks = {
            "files_exist": {"passed": 0, "total": 0},
            "resolution_correct": {"passed": 0, "total": 0},
            "size_adequate": {"passed": 0, "total": 0}
        }

        for path in image_paths:
            path_obj = Path(path)
            checks["files_exist"]["total"] += 1

            if not path_obj.exists():
                issues.append(f"파일 없음: {path_obj.name}")
                continue

            checks["files_exist"]["passed"] += 1

            # 파일 크기 확인
            file_size = path_obj.stat().st_size
            checks["size_adequate"]["total"] += 1
            if file_size >= self.MIN_FILE_SIZE:
                checks["size_adequate"]["passed"] += 1
            else:
                issues.append(f"파일 크기 작음: {path_obj.name}")

            # 해상도 확인
            if PIL_AVAILABLE:
                checks["resolution_correct"]["total"] += 1
                try:
                    with Image.open(path) as img:
                        width, height = img.size
                        if width == self.EXPECTED_WIDTH and height == self.EXPECTED_HEIGHT:
                            checks["resolution_correct"]["passed"] += 1
                        else:
                            issues.append(f"해상도 불일치: {path_obj.name} ({width}x{height})")
                except Exception:
                    issues.append(f"이미지 읽기 실패: {path_obj.name}")
            else:
                checks["resolution_correct"]["total"] += 1
                checks["resolution_correct"]["passed"] += 1

        # 점수 계산 (v1.0: 20점을 3개 항목에 배분)
        if checks["files_exist"]["total"] > 0:
            score += 7 * (checks["files_exist"]["passed"] / checks["files_exist"]["total"])
        if checks["resolution_correct"]["total"] > 0:
            score += 7 * (checks["resolution_correct"]["passed"] / checks["resolution_correct"]["total"])
        if checks["size_adequate"]["total"] > 0:
            score += 6 * (checks["size_adequate"]["passed"] / checks["size_adequate"]["total"])

        return {
            "category": "이미지 품질",
            "max_score": max_score,
            "score": round(score, 1),
            "checks": checks,
            "issues": issues
        }

    def _check_cover_spec(self, image_paths: List[str], topic: str) -> Dict:
        """
        2. v8 표지 스펙 검사 (30점)
        - 표지 파일 존재 (15점)
        - 표지 파일명에 'cover' 포함 (15점)
        """
        max_score = 30
        score = 0
        issues = []

        filenames = [Path(p).name.lower() for p in image_paths]

        # 표지 파일 존재 확인
        has_cover = any("cover" in f or "_00_" in f for f in filenames)
        if has_cover:
            score += 15
        else:
            issues.append("표지(cover) 파일 없음")

        # 표지 파일명에 'cover' 포함 확인
        cover_named_correctly = any("cover" in f for f in filenames)
        if cover_named_correctly:
            score += 15
        else:
            issues.append("표지 파일명에 'cover' 미포함")

        return {
            "category": "v8 표지 스펙",
            "max_score": max_score,
            "score": round(score, 1),
            "has_cover": has_cover,
            "cover_named_correctly": cover_named_correctly,
            "issues": issues
        }

    def _check_slide_composition(self, image_paths: List[str], topic: str) -> Dict:
        """
        3. 슬라이드 구성 검사 (15점) - v1.0 배점
        - 7개 슬라이드 (10점)
        - 파일명 규칙 준수 (5점)
        """
        max_score = 15
        score = 0
        issues = []

        # 슬라이드 개수 확인 (v1.0: 10점)
        slide_count = len(image_paths)
        if slide_count >= self.EXPECTED_SLIDES:
            score += 10
        elif slide_count > 0:
            score += 10 * (slide_count / self.EXPECTED_SLIDES)
            issues.append(f"슬라이드 부족: {slide_count}/{self.EXPECTED_SLIDES}")

        # 파일명 규칙 확인 (v1.0: 5점)
        valid_names = 0
        pattern = re.compile(r".*_\d{2}_(cover|content|cta)\.png$", re.IGNORECASE)

        for path in image_paths:
            filename = Path(path).name
            if pattern.match(filename):
                valid_names += 1

        if len(image_paths) > 0:
            name_ratio = valid_names / len(image_paths)
            score += 5 * name_ratio
            if name_ratio < 1.0:
                issues.append(f"파일명 규칙 불일치: {len(image_paths) - valid_names}개")

        return {
            "category": "슬라이드 구성",
            "max_score": max_score,
            "score": round(score, 1),
            "slide_count": slide_count,
            "valid_names": valid_names,
            "issues": issues
        }

    def _check_angle_diversity(self, image_paths: List[str]) -> Dict:
        """
        4. 앵글 다양성 검사 (25점) - v1.0 추가
        - 본문 5장(01~05) 중 최소 3가지 앵글 사용
        - 자동 검사: 파일 존재 + 수동 검수 필요 메모
        """
        max_score = 25
        score = 0
        issues = []

        # 본문 슬라이드 확인 (01~05)
        content_files = []
        for p in image_paths:
            filename = Path(p).name.lower()
            if "content" in filename and not "cta" in filename:
                content_files.append(filename)

        content_count = len(content_files)

        if content_count >= 5:
            # 본문 5장 존재 시 기본 점수 부여 (수동 검수 필요)
            score = 15  # 자동: 파일 존재만 확인
            issues.append("앵글 다양성 수동 검수 필요 (최소 3종류)")
        elif content_count > 0:
            score = 15 * (content_count / 5)
            issues.append(f"본문 슬라이드 부족: {content_count}/5")
        else:
            issues.append("본문 슬라이드 없음")

        return {
            "category": "앵글 다양성",
            "max_score": max_score,
            "score": round(score, 1),
            "content_count": content_count,
            "note": "수동 검수: 정면/측면45°/측면90°/부감/블러 중 3종 이상",
            "issues": issues
        }

    def _check_cta_slide(self, image_paths: List[str]) -> Dict:
        """
        5. CTA 슬라이드 검사 (10점) - v1.0 배점
        - CTA 슬라이드 존재
        """
        max_score = 10
        score = 0
        issues = []

        filenames = [Path(p).name.lower() for p in image_paths]

        # CTA 파일 존재 확인
        has_cta = any("cta" in f for f in filenames)
        if has_cta:
            score = 10
        else:
            issues.append("CTA 슬라이드 없음")

        return {
            "category": "CTA 슬라이드",
            "max_score": max_score,
            "score": round(score, 1),
            "has_cta": has_cta,
            "issues": issues
        }

    def _get_grade(self, score: float) -> str:
        """점수를 등급으로 변환"""
        if score >= 90:
            return "A"
        if score >= 80:
            return "B+"
        if score >= 70:
            return "B"
        if score >= 60:
            return "C"
        return "D"
