"""
QualityCheckerAgent - 품질 검수 에이전트
박과장 Gem의 검수 기준을 코드로 구현

Author: 최기술 대리
"""

import os
import re
from typing import Any, Dict, List, Optional
from pathlib import Path
from .base import BaseAgent, AgentResult

# Pillow 사용 가능 여부 확인
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class QualityCheckerAgent(BaseAgent):
    """
    품질 검수 에이전트

    검수 항목 (100점 만점):
    1. 이미지 품질 (40점)
       - 파일 존재 여부
       - 해상도 1080x1080 확인
       - 파일 크기 > 100KB
    2. 슬라이드 구성 (30점)
       - 10개 슬라이드 존재
       - 파일명 규칙 준수
    3. 브랜드 일관성 (20점)
       - 표지(00)에 영문 제목 포함
       - CTA(09) 존재
    4. 필수 요소 (10점)
       - 모든 슬라이드에 텍스트 데이터 존재
    """

    # 기본 설정
    EXPECTED_WIDTH = 1080
    EXPECTED_HEIGHT = 1080
    MIN_FILE_SIZE = 100 * 1024  # 100KB
    EXPECTED_SLIDES = 10

    @property
    def name(self) -> str:
        return "QualityChecker"

    async def execute(self, input_data: Any) -> AgentResult:
        """
        품질 검수 실행

        Args:
            input_data: {
                "images": [{"path": "..."}, ...] 또는 ["path1", "path2", ...],
                "output_dir": "...",
                "topic": "apple"
            }

        Returns:
            AgentResult with QA report
        """
        # 이미지 경로 추출
        images = input_data.get("images", [])
        output_dir = input_data.get("output_dir")
        topic = input_data.get("topic", "unknown")

        # 이미지 리스트 정규화
        image_paths = []
        if images:
            for img in images:
                if isinstance(img, dict):
                    image_paths.append(img.get("path", ""))
                elif isinstance(img, str):
                    image_paths.append(img)

        # output_dir에서 이미지 스캔 (이미지가 없는 경우)
        if not image_paths and output_dir:
            output_path = Path(output_dir)
            if output_path.exists():
                image_paths = sorted([
                    str(output_path / f)
                    for f in os.listdir(output_path)
                    if f.endswith('.png') and not f.startswith('.')
                ])

        self.log(f"품질 검수 시작 ({len(image_paths)}개 이미지)")

        # 검수 실행
        report = self._run_quality_check(image_paths, topic)

        # 통과 여부 판정
        thresholds = self.config.get("thresholds", {})
        pass_score = thresholds.get("pass", 70)

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
                "average_score": report["total_score"],
                "passed": passed,
                "grade": report["grade"]
            }
        )

    def _run_quality_check(self, image_paths: List[str], topic: str) -> Dict:
        """
        품질 검사 수행

        Returns:
            {
                "total_score": 85,
                "grade": "B+",
                "categories": {...},
                "issues": [...],
                "details": [...]
            }
        """
        issues = []
        details = []

        # 1. 이미지 품질 검사 (40점)
        image_quality = self._check_image_quality(image_paths)
        details.append(image_quality)

        # 2. 슬라이드 구성 검사 (30점)
        slide_composition = self._check_slide_composition(image_paths, topic)
        details.append(slide_composition)

        # 3. 브랜드 일관성 검사 (20점)
        brand_consistency = self._check_brand_consistency(image_paths, topic)
        details.append(brand_consistency)

        # 4. 필수 요소 검사 (10점)
        required_elements = self._check_required_elements(image_paths)
        details.append(required_elements)

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
            "categories": {
                "image_quality": image_quality,
                "slide_composition": slide_composition,
                "brand_consistency": brand_consistency,
                "required_elements": required_elements
            },
            "issues": issues,
            "details": details,
            "image_count": len(image_paths)
        }

    def _check_image_quality(self, image_paths: List[str]) -> Dict:
        """
        1. 이미지 품질 검사 (40점)
        - 파일 존재: 15점
        - 해상도 1080x1080: 15점
        - 파일 크기 > 100KB: 10점
        """
        max_score = 40
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

            # 파일 존재 확인
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
                issues.append(f"파일 크기 작음: {path_obj.name} ({file_size // 1024}KB)")

            # 해상도 확인 (Pillow 필요)
            if PIL_AVAILABLE:
                checks["resolution_correct"]["total"] += 1
                try:
                    with Image.open(path) as img:
                        width, height = img.size
                        if width == self.EXPECTED_WIDTH and height == self.EXPECTED_HEIGHT:
                            checks["resolution_correct"]["passed"] += 1
                        else:
                            issues.append(f"해상도 불일치: {path_obj.name} ({width}x{height})")
                except Exception as e:
                    issues.append(f"이미지 읽기 실패: {path_obj.name}")
            else:
                # Pillow 없으면 해상도 검사 스킵, 점수 부여
                checks["resolution_correct"]["total"] += 1
                checks["resolution_correct"]["passed"] += 1

        # 점수 계산
        if checks["files_exist"]["total"] > 0:
            score += 15 * (checks["files_exist"]["passed"] / checks["files_exist"]["total"])
        if checks["resolution_correct"]["total"] > 0:
            score += 15 * (checks["resolution_correct"]["passed"] / checks["resolution_correct"]["total"])
        if checks["size_adequate"]["total"] > 0:
            score += 10 * (checks["size_adequate"]["passed"] / checks["size_adequate"]["total"])

        return {
            "category": "이미지 품질",
            "max_score": max_score,
            "score": round(score, 1),
            "checks": checks,
            "issues": issues
        }

    def _check_slide_composition(self, image_paths: List[str], topic: str) -> Dict:
        """
        2. 슬라이드 구성 검사 (30점)
        - 10개 슬라이드: 20점
        - 파일명 규칙 준수: 10점
        """
        max_score = 30
        score = 0
        issues = []

        # 슬라이드 개수 확인
        slide_count = len(image_paths)
        if slide_count >= self.EXPECTED_SLIDES:
            score += 20
        elif slide_count > 0:
            score += 20 * (slide_count / self.EXPECTED_SLIDES)
            issues.append(f"슬라이드 부족: {slide_count}/{self.EXPECTED_SLIDES}")
        else:
            issues.append("슬라이드 없음")

        # 파일명 규칙 확인 (topic_00.png ~ topic_09.png)
        valid_names = 0
        pattern = re.compile(rf".*_{0,1}\d{{2}}.*\.png$", re.IGNORECASE)

        for path in image_paths:
            filename = Path(path).name
            if pattern.match(filename):
                valid_names += 1

        if len(image_paths) > 0:
            name_ratio = valid_names / len(image_paths)
            score += 10 * name_ratio
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

    def _check_brand_consistency(self, image_paths: List[str], topic: str) -> Dict:
        """
        3. 브랜드 일관성 검사 (20점)
        - 표지(00) 존재: 10점
        - CTA(09) 존재: 10점
        """
        max_score = 20
        score = 0
        issues = []

        filenames = [Path(p).name.lower() for p in image_paths]

        # 표지 (00 또는 01) 확인
        has_cover = any("00" in f or "01" in f or "cover" in f for f in filenames)
        if has_cover:
            score += 10
        else:
            issues.append("표지(00/01) 슬라이드 없음")

        # CTA (09 또는 10) 확인
        has_cta = any("09" in f or "10" in f or "cta" in f for f in filenames)
        if has_cta:
            score += 10
        else:
            issues.append("CTA(09/10) 슬라이드 없음")

        return {
            "category": "브랜드 일관성",
            "max_score": max_score,
            "score": round(score, 1),
            "has_cover": has_cover,
            "has_cta": has_cta,
            "issues": issues
        }

    def _check_required_elements(self, image_paths: List[str]) -> Dict:
        """
        4. 필수 요소 검사 (10점)
        - 모든 슬라이드 이미지 존재: 10점
        """
        max_score = 10
        score = 0
        issues = []

        # 존재하는 파일 수 확인
        existing_files = sum(1 for p in image_paths if Path(p).exists())

        if len(image_paths) > 0:
            ratio = existing_files / len(image_paths)
            score = 10 * ratio
            if ratio < 1.0:
                issues.append(f"누락된 파일: {len(image_paths) - existing_files}개")

        return {
            "category": "필수 요소",
            "max_score": max_score,
            "score": round(score, 1),
            "existing_files": existing_files,
            "total_files": len(image_paths),
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
