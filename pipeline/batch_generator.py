#!/usr/bin/env python3
"""
pipeline/batch_generator.py - §22.11~13 통합 파이프라인
v3.1: 6단계 순차 실행 구조 (pre → generate → post → gate)

사용법:
    from pipeline.batch_generator import SafetyPipeline, run_pipeline

    # 단일 콘텐츠 파이프라인
    result = run_pipeline(food_id=127)

    # 배치 실행
    pipeline = SafetyPipeline()
    results = pipeline.run_batch(food_ids=[1, 2, 3, 127])
"""

import json
from typing import Dict, List, Optional, Union, Callable, Any
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

import sys
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.enums.safety import Safety, get_safety, SafetyError
from pipeline.caption_generator import (
    get_caption_template,
    get_forbidden_keywords,
    CaptionTemplate,
)
from pipeline.validators import (
    GateController,
    GateStatus,
    GateError,
    gate_check,
    can_save,
    validate_before_generation,
    validate_after_generation,
    generate_structure_id,
)


# =============================================================================
# 설정
# =============================================================================

FOOD_DATA_PATH = PROJECT_ROOT / "config" / "food_data.json"
CONTENTS_DIR = PROJECT_ROOT / "contents"
LOGS_DIR = PROJECT_ROOT / "logs" / "pipeline"
STATUS_DIRS = ["1_cover_only", "2_body_ready", "3_approved", "4_posted"]


# =============================================================================
# 파이프라인 단계
# =============================================================================

class PipelineStage(Enum):
    """파이프라인 6단계"""
    INIT = "1_INIT"               # 초기화
    LOAD_DATA = "2_LOAD_DATA"     # 데이터 로드
    PRE_VALIDATE = "3_PRE_VALIDATE"   # 생성 전 검증
    GENERATE = "4_GENERATE"       # 콘텐츠 생성
    POST_VALIDATE = "5_POST_VALIDATE"  # 생성 후 검증
    GATE_CHECK = "6_GATE_CHECK"   # 게이트 체크 + 저장


# =============================================================================
# 파이프라인 결과
# =============================================================================

@dataclass
class PipelineResult:
    """파이프라인 실행 결과"""
    food_id: int
    safety: Optional[Safety] = None
    structure_id: str = ""

    success: bool = False
    stage_reached: PipelineStage = PipelineStage.INIT
    gate_status: Optional[GateStatus] = None

    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # 생성 결과
    caption_generated: bool = False
    images_generated: bool = False

    # 메타데이터
    timestamp: str = ""
    duration_ms: int = 0
    log_path: Optional[Path] = None


# =============================================================================
# SafetyPipeline
# =============================================================================

class SafetyPipeline:
    """
    §22.11~13 안전도 분기 파이프라인

    6단계 순차 실행:
    1. INIT - 초기화
    2. LOAD_DATA - food_data.json 로드
    3. PRE_VALIDATE - §22.11 생성 전 검증
    4. GENERATE - 캡션/이미지 생성
    5. POST_VALIDATE - §22.12~13 생성 후 검증
    6. GATE_CHECK - 게이트 통과 시 저장
    """

    def __init__(
        self,
        strict: bool = True,
        save_on_pass: bool = False,
        caption_generator: Optional[Callable] = None,
        image_generator: Optional[Callable] = None,
    ):
        """
        Args:
            strict: True면 검증 실패 시 예외
            save_on_pass: True면 GATE_PASS 시 자동 저장
            caption_generator: 커스텀 캡션 생성 함수
            image_generator: 커스텀 이미지 생성 함수
        """
        self.strict = strict
        self.save_on_pass = save_on_pass
        self.caption_generator = caption_generator
        self.image_generator = image_generator

        # 캐시
        self._food_data_cache: Optional[Dict] = None

    def load_food_data(self) -> Dict:
        """food_data.json 로드 (캐시)"""
        if self._food_data_cache is None:
            with open(FOOD_DATA_PATH, "r", encoding="utf-8") as f:
                self._food_data_cache = json.load(f)
        return self._food_data_cache

    def get_food(self, food_id: int) -> Optional[Dict]:
        """특정 음식 데이터 조회"""
        data = self.load_food_data()
        return data.get(str(food_id))

    def run(self, food_id: int) -> PipelineResult:
        """
        단일 콘텐츠 파이프라인 실행

        Args:
            food_id: 음식 ID

        Returns:
            PipelineResult
        """
        start_time = datetime.now()

        result = PipelineResult(
            food_id=food_id,
            timestamp=start_time.strftime("%Y-%m-%d %H:%M:%S"),
        )

        try:
            # Stage 1: INIT
            result.stage_reached = PipelineStage.INIT

            # Stage 2: LOAD_DATA
            result.stage_reached = PipelineStage.LOAD_DATA
            food_data = self.get_food(food_id)

            if not food_data:
                result.errors.append(f"Food ID {food_id} not found")
                return self._finalize_result(result, start_time)

            # Safety 추출
            safety_str = food_data.get("safety", "SAFE")
            result.safety = get_safety(safety_str)
            result.structure_id = generate_structure_id(food_id, result.safety)

            # Stage 3: PRE_VALIDATE
            result.stage_reached = PipelineStage.PRE_VALIDATE
            gate = GateController(food_id=food_id, safety=result.safety)

            pre_ok = gate.pre_check(food_data, strict=self.strict)
            if not pre_ok:
                result.errors.extend(gate.all_errors)
                result.gate_status = gate.status
                return self._finalize_result(result, start_time)

            # Stage 4: GENERATE
            result.stage_reached = PipelineStage.GENERATE

            # 캡션 생성 (커스텀 또는 기본)
            if self.caption_generator:
                caption = self.caption_generator(food_id, result.safety, food_data)
            else:
                caption = self._default_caption_check(food_id)

            if caption:
                result.caption_generated = True
            else:
                result.warnings.append("캡션 생성 스킵 (기존 캡션 사용)")
                caption = self._load_existing_caption(food_id)

            if not caption:
                result.errors.append("캡션 없음 - 검증 불가")
                return self._finalize_result(result, start_time)

            # Stage 5: POST_VALIDATE
            result.stage_reached = PipelineStage.POST_VALIDATE

            post_ok = gate.post_check(caption, strict=self.strict)
            if not post_ok:
                result.errors.extend(gate.all_errors)
                result.warnings.extend(gate.all_warnings)
                result.gate_status = gate.status
                return self._finalize_result(result, start_time)

            # Stage 6: GATE_CHECK
            result.stage_reached = PipelineStage.GATE_CHECK

            if gate.can_proceed():
                result.success = True
                result.gate_status = GateStatus.GATE_PASS

                if self.save_on_pass:
                    self._save_content(food_id, result.safety, caption)
            else:
                result.gate_status = gate.status
                result.errors.extend(gate.all_errors)

            result.warnings.extend(gate.all_warnings)

        except GateError as e:
            result.errors.append(str(e))
            result.gate_status = e.status

        except Exception as e:
            result.errors.append(f"예외 발생: {type(e).__name__}: {e}")

        return self._finalize_result(result, start_time)

    def run_batch(
        self,
        food_ids: Optional[List[int]] = None,
        safety_filter: Optional[Safety] = None,
    ) -> Dict[str, Any]:
        """
        배치 파이프라인 실행

        Args:
            food_ids: 실행할 ID 목록 (None이면 전체)
            safety_filter: 특정 안전도만 필터

        Returns:
            {"results": [...], "stats": {...}}
        """
        if food_ids is None:
            # 전체 스캔
            food_data = self.load_food_data()
            food_ids = [int(k) for k in food_data.keys()]

        results = []
        stats = {
            "total": 0,
            "success": 0,
            "fail": 0,
            "by_safety": {"SAFE": 0, "CAUTION": 0, "FORBIDDEN": 0},
            "by_stage": {},
        }

        for food_id in sorted(food_ids):
            # 안전도 필터
            if safety_filter:
                food = self.get_food(food_id)
                if food:
                    s = get_safety(food.get("safety", "SAFE"))
                    if s != safety_filter:
                        continue

            result = self.run(food_id)
            results.append(result)

            stats["total"] += 1
            if result.success:
                stats["success"] += 1
            else:
                stats["fail"] += 1

            if result.safety:
                stats["by_safety"][result.safety.value] += 1

            stage = result.stage_reached.value
            stats["by_stage"][stage] = stats["by_stage"].get(stage, 0) + 1

        # 배치 로그 저장
        self._save_batch_log(results, stats)

        return {"results": results, "stats": stats}

    def _default_caption_check(self, food_id: int) -> Optional[str]:
        """
        기본 캡션 로드 (생성 아님)
        실제 생성은 caption_generator 함수로
        """
        return self._load_existing_caption(food_id)

    def _load_existing_caption(self, food_id: int) -> Optional[str]:
        """기존 캡션 파일 로드"""
        folder = self._find_content_folder(food_id)
        if not folder:
            return None

        # 캡션 파일 검색
        for subdir in ["insta", "blog", ""]:
            caption_path = folder / subdir / "caption.txt" if subdir else folder / "caption.txt"
            if caption_path.exists():
                return caption_path.read_text(encoding="utf-8")

        return None

    def _find_content_folder(self, food_id: int) -> Optional[Path]:
        """콘텐츠 폴더 찾기"""
        num_str = f"{food_id:03d}"
        for status_dir in STATUS_DIRS:
            status_path = CONTENTS_DIR / status_dir
            if not status_path.exists():
                continue
            for item in status_path.iterdir():
                if item.is_dir() and item.name.startswith(num_str):
                    return item
        return None

    def _save_content(self, food_id: int, safety: Safety, caption: str):
        """콘텐츠 저장 (구현 필요)"""
        # 실제 저장 로직은 별도 구현
        pass

    def _finalize_result(
        self,
        result: PipelineResult,
        start_time: datetime,
    ) -> PipelineResult:
        """결과 마무리"""
        end_time = datetime.now()
        result.duration_ms = int((end_time - start_time).total_seconds() * 1000)

        # 개별 로그 저장
        result.log_path = self._save_pipeline_log(result)

        return result

    def _save_pipeline_log(self, result: PipelineResult) -> Path:
        """파이프라인 로그 저장"""
        date_str = datetime.now().strftime("%Y%m%d")
        log_dir = LOGS_DIR / date_str
        log_dir.mkdir(parents=True, exist_ok=True)

        status = "PASS" if result.success else "FAIL"
        log_path = log_dir / f"{result.food_id:03d}_pipeline_{status}.log"

        with open(log_path, "w", encoding="utf-8") as f:
            f.write(f"{'='*60}\n")
            f.write(f"§22.11~13 Pipeline Log\n")
            f.write(f"{'='*60}\n\n")

            f.write(f"Timestamp: {result.timestamp}\n")
            f.write(f"Duration: {result.duration_ms}ms\n")
            f.write(f"Food ID: {result.food_id}\n")
            f.write(f"Safety: {result.safety.value if result.safety else 'N/A'}\n")
            f.write(f"Structure ID: {result.structure_id}\n\n")

            f.write(f"Stage Reached: {result.stage_reached.value}\n")
            f.write(f"Gate Status: {result.gate_status.value if result.gate_status else 'N/A'}\n")
            f.write(f"Success: {result.success}\n\n")

            if result.errors:
                f.write("[ERRORS]\n")
                for err in result.errors:
                    f.write(f"  - {err}\n")
                f.write("\n")

            if result.warnings:
                f.write("[WARNINGS]\n")
                for warn in result.warnings:
                    f.write(f"  - {warn}\n")
                f.write("\n")

            f.write("=== End of Log ===\n")

        return log_path

    def _save_batch_log(self, results: List[PipelineResult], stats: Dict):
        """배치 로그 저장"""
        date_str = datetime.now().strftime("%Y%m%d")
        time_str = datetime.now().strftime("%H%M%S")
        log_dir = LOGS_DIR / date_str
        log_dir.mkdir(parents=True, exist_ok=True)

        log_path = log_dir / f"batch_{time_str}.log"

        with open(log_path, "w", encoding="utf-8") as f:
            f.write(f"{'='*60}\n")
            f.write(f"§22.11~13 Batch Pipeline Log\n")
            f.write(f"{'='*60}\n\n")

            f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total: {stats['total']}\n")
            f.write(f"Success: {stats['success']}\n")
            f.write(f"Fail: {stats['fail']}\n\n")

            f.write("[By Safety]\n")
            for safety, count in stats['by_safety'].items():
                f.write(f"  {safety}: {count}\n")
            f.write("\n")

            f.write("[By Stage]\n")
            for stage, count in stats['by_stage'].items():
                f.write(f"  {stage}: {count}\n")
            f.write("\n")

            # 실패 목록
            fails = [r for r in results if not r.success]
            if fails:
                f.write("[FAILED ITEMS]\n")
                for r in fails:
                    f.write(f"  #{r.food_id:03d} [{r.safety.value if r.safety else 'N/A'}] "
                           f"@ {r.stage_reached.value}\n")
                    for err in r.errors[:2]:
                        f.write(f"    - {err[:80]}...\n" if len(err) > 80 else f"    - {err}\n")
                f.write("\n")

            f.write("=== End of Batch Log ===\n")


# =============================================================================
# 편의 함수
# =============================================================================

def run_pipeline(
    food_id: int,
    strict: bool = True,
) -> PipelineResult:
    """단일 파이프라인 실행"""
    pipeline = SafetyPipeline(strict=strict)
    return pipeline.run(food_id)


def run_forbidden_scan() -> Dict:
    """FORBIDDEN 콘텐츠만 스캔"""
    pipeline = SafetyPipeline(strict=False)
    return pipeline.run_batch(safety_filter=Safety.FORBIDDEN)


# =============================================================================
# 테스트
# =============================================================================

def test_pipeline():
    """파이프라인 테스트"""
    print("=" * 60)
    print("§22.11~13 Safety Pipeline 테스트")
    print("=" * 60)

    pipeline = SafetyPipeline(strict=False)

    # 테스트 1: 단일 실행
    print("\n[테스트 1] 단일 파이프라인 (food_id=1)")
    result = pipeline.run(1)
    print(f"  Safety: {result.safety.value if result.safety else 'N/A'}")
    print(f"  Stage: {result.stage_reached.value}")
    print(f"  Success: {result.success}")
    print(f"  Duration: {result.duration_ms}ms")

    if result.errors:
        print(f"  Errors: {len(result.errors)}")
        for err in result.errors[:2]:
            print(f"    - {err[:60]}...")

    # 테스트 2: FORBIDDEN 스캔
    print("\n[테스트 2] FORBIDDEN 스캔")
    batch_result = pipeline.run_batch(safety_filter=Safety.FORBIDDEN)
    stats = batch_result["stats"]
    print(f"  Total: {stats['total']}")
    print(f"  Success: {stats['success']}")
    print(f"  Fail: {stats['fail']}")

    return True


if __name__ == "__main__":
    test_pipeline()
