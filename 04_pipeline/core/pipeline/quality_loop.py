"""
품질 검사 루프
Phase 4: 검수 실패 시 자동 재작업
Phase 6: 기준 상향 (80점→90점, 조건부 70→80점)

- 검수 실패 시 자동 재작업
- 최대 재시도 횟수 제한 (3회)
- 피드백 기반 개선
- 선택적 슬라이드 재생성

Flow:
ContentCrew → TechReview → CreativeReview
                  ↓              ↓
              FAIL(<90)      FAIL(<90)
                  ↓              ↓
              재생성 ←←←←←←←←←←←┘
              (최대 3회)
"""

import asyncio
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from pathlib import Path
import sys

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))


class ReviewResult(Enum):
    """검수 결과"""
    PASS = "pass"
    CONDITIONAL_PASS = "conditional_pass"
    FAIL = "fail"


class QualityGateFailed(Exception):
    """
    품질 게이트 실패 예외

    PD 승인 (2026-01-30):
    - success=False 시 무조건 raise
    - dry-run도 예외 없이 적용
    - 이 예외가 발생하면 게시 차단
    """
    def __init__(self, fail_point: str, attempts: int, last_score: float = 0, message: str = None):
        self.fail_point = fail_point
        self.attempts = attempts
        self.last_score = last_score
        self.message = message or f"품질 게이트 실패: {fail_point} (시도: {attempts}회, 점수: {last_score:.1f})"
        super().__init__(self.message)

    def __str__(self):
        return f"🚨 QualityGateFailed: {self.message}"


@dataclass
class RetryContext:
    """재시도 컨텍스트"""
    attempt: int = 0
    max_attempts: int = 3
    tech_feedbacks: List[str] = field(default_factory=list)
    creative_feedbacks: List[str] = field(default_factory=list)
    score_history: List[Dict[str, Any]] = field(default_factory=list)
    problem_slides: List[int] = field(default_factory=list)

    def can_retry(self) -> bool:
        """재시도 가능 여부"""
        return self.attempt < self.max_attempts

    def increment(self):
        """시도 횟수 증가"""
        self.attempt += 1

    def add_feedback(self, review_type: str, feedback: str, score: float):
        """피드백 추가"""
        if review_type == "tech":
            self.tech_feedbacks.append(feedback)
        else:
            self.creative_feedbacks.append(feedback)

        self.score_history.append({
            "attempt": self.attempt,
            "type": review_type,
            "score": score,
            "feedback": feedback,
            "timestamp": datetime.now().isoformat()
        })

    def get_improvement_prompt(self) -> str:
        """피드백 기반 개선 프롬프트 생성"""
        prompt_parts = []

        if self.tech_feedbacks:
            recent_tech = self.tech_feedbacks[-2:] if len(self.tech_feedbacks) > 2 else self.tech_feedbacks
            prompt_parts.append("기술 검수 개선 필요:\n" + "\n".join(f"- {f}" for f in recent_tech))

        if self.creative_feedbacks:
            recent_creative = self.creative_feedbacks[-2:] if len(self.creative_feedbacks) > 2 else self.creative_feedbacks
            prompt_parts.append("크리에이티브 개선 필요:\n" + "\n".join(f"- {f}" for f in recent_creative))

        return "\n\n".join(prompt_parts) if prompt_parts else ""

    def get_retry_strategy(self) -> str:
        """현재 시도에 맞는 재시도 전략"""
        if self.attempt <= 1:
            return "full_regeneration"  # 전체 재생성
        elif self.attempt == 2:
            return "selective_regeneration"  # 문제 슬라이드만
        else:
            return "manual_intervention"  # 수동 개입


class QualityControlLoop:
    """
    품질 검사 루프 관리자

    검수 실패 시 자동으로 재생성하고
    최대 3회까지 재시도
    """

    # 점수 기준 (Phase 6: 기준 상향)
    TECH_PASS_SCORE = 90       # 80 → 90
    CREATIVE_PASS_SCORE = 90   # 80 → 90
    CONDITIONAL_PASS_SCORE = 80  # 70 → 80

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.max_retries = self.config.get("max_retries", 3)

        # Crews는 lazy 초기화
        self._crews_initialized = False
        self._content_crew = None
        self._text_overlay_crew = None
        self._tech_review_crew = None
        self._creative_review_crew = None

        # 로거
        self._logger = None

    def _init_crews(self):
        """Crews lazy 초기화"""
        if self._crews_initialized:
            return

        from core.crews import (
            ContentCrew,
            TextOverlayCrew,
            TechReviewCrew,
            CreativeReviewCrew
        )

        self._content_crew = ContentCrew()
        self._text_overlay_crew = TextOverlayCrew()
        self._tech_review_crew = TechReviewCrew()
        self._creative_review_crew = CreativeReviewCrew()

        self._crews_initialized = True

    def _init_logger(self):
        """로거 초기화"""
        if self._logger is None:
            try:
                from support.utils.logger import PipelineLogger
                self._logger = PipelineLogger()
            except ImportError:
                self._logger = SimpleLogger()

    def log(self, message: str, level: str = "info"):
        """로깅"""
        self._init_logger()
        if level == "info":
            self._logger.info(message)
        elif level == "warning":
            self._logger.warning(message)
        elif level == "error":
            self._logger.error(message)

    async def run_with_quality_loop(
        self,
        storyboard_path: str,
        slides: List[Dict],
        prompts: List[Dict],
        food_name: str,
        food_name_kr: str,
        output_base_dir: str
    ) -> Dict[str, Any]:
        """
        품질 검사 루프 실행

        Args:
            storyboard_path: 스토리보드 파일 경로
            slides: 슬라이드 정보 리스트
            prompts: 프롬프트 리스트
            food_name: 영문 음식명
            food_name_kr: 한글 음식명
            output_base_dir: 기본 출력 디렉토리

        Returns:
            {
                "success": bool,
                "images_dir": str,
                "tech_score": float,
                "creative_score": float,
                "attempts": int,
                "score_history": list
            }
        """
        self._init_crews()
        self._init_logger()

        context = RetryContext(max_attempts=self.max_retries)
        start_time = time.time()

        print(f"\n{'━'*60}")
        print(f"🔄 품질 검사 루프 시작")
        print(f"{'━'*60}")
        print(f"   최대 재시도: {context.max_attempts}회")
        print(f"   통과 기준: Tech {self.TECH_PASS_SCORE}점, Creative {self.CREATIVE_PASS_SCORE}점")
        print()

        while context.can_retry():
            context.increment()
            strategy = context.get_retry_strategy()

            # P1 fix: 재시도 간 exponential backoff (API rate limit 방지)
            if context.attempt > 1:
                delay = min(2 ** (context.attempt - 1), 30)  # 2, 4, 8... 최대 30초
                print(f"\n   ⏳ 재시도 전 {delay}초 대기 (backoff)...")
                await asyncio.sleep(delay)

            print(f"\n{'─'*60}")
            print(f"🔄 시도 {context.attempt}/{context.max_attempts} (전략: {strategy})")
            print(f"{'─'*60}")

            try:
                # 1. 이미지 생성
                raw_dir = str(Path(output_base_dir) / f"v{context.attempt}")
                content_result = await self._generate_content(
                    slides=slides,
                    prompts=prompts,
                    food_name=food_name,
                    output_dir=raw_dir,
                    improvement_prompt=context.get_improvement_prompt() if context.attempt > 1 else None,
                    problem_slides=context.problem_slides if strategy == "selective_regeneration" else None
                )

                if not content_result.get("success", False) and not content_result.get("images"):
                    self.log(f"이미지 생성 실패", "error")
                    continue

                # 2. 텍스트 오버레이
                final_dir = str(Path(output_base_dir).parent / f"{food_name}_final_v{context.attempt}")
                overlay_result = await self._apply_text_overlay(
                    input_dir=raw_dir,
                    output_dir=final_dir,
                    slides=slides,
                    food_name=food_name
                )

                # 3. 기술 검수
                tech_result = await self._run_tech_review(final_dir, food_name)

                print(f"\n   🔧 기술 검수: {tech_result['score']:.1f}점 ({tech_result['result'].value})")

                if tech_result["result"] == ReviewResult.FAIL:
                    context.add_feedback("tech", tech_result.get("feedback", "기술 검수 실패"), tech_result["score"])
                    self.log(f"기술 검수 실패: {tech_result['score']:.1f}점", "warning")

                    # NEEDS_REVISION 로그 기록 (Q2: 경고로 분류, 재시도 허용)
                    self._log_needs_revision(
                        step="tech_review",
                        score=tech_result["score"],
                        retry_count=context.attempt,
                        feedback=tech_result.get("feedback", "")
                    )

                    if not context.can_retry():
                        self._create_fail_result(context, "tech_review", tech_result)
                    continue

                # 4. 크리에이티브 검수
                creative_result = await self._run_creative_review(final_dir, food_name)

                print(f"   🎭 크리에이티브: {creative_result['score']:.1f}점 ({creative_result['result'].value})")

                if creative_result["result"] == ReviewResult.FAIL:
                    context.add_feedback("creative", creative_result.get("feedback", "크리에이티브 검수 실패"), creative_result["score"])

                    # 문제 슬라이드 식별 (다음 시도를 위해)
                    if creative_result.get("problem_slides"):
                        context.problem_slides = creative_result["problem_slides"]

                    self.log(f"크리에이티브 검수 실패: {creative_result['score']:.1f}점", "warning")

                    # NEEDS_REVISION 로그 기록 (Q2: 경고로 분류, 재시도 허용)
                    self._log_needs_revision(
                        step="creative_review",
                        score=creative_result["score"],
                        retry_count=context.attempt,
                        feedback=creative_result.get("feedback", "")
                    )

                    if not context.can_retry():
                        return self._create_fail_result(context, "creative_review", creative_result)
                    continue

                # 5. 통과!
                total_time = time.time() - start_time

                print(f"\n{'━'*60}")
                print(f"✅ 품질 검사 통과!")
                print(f"{'━'*60}")
                print(f"   시도 횟수: {context.attempt}회")
                print(f"   기술 검수: {tech_result['score']:.1f}점")
                print(f"   크리에이티브: {creative_result['score']:.1f}점")
                print(f"   소요 시간: {total_time:.1f}초")
                print(f"{'━'*60}")

                return {
                    "success": True,
                    "images_dir": final_dir,
                    "tech_score": tech_result["score"],
                    "tech_grade": tech_result.get("grade", ""),
                    "creative_score": creative_result["score"],
                    "creative_grade": creative_result.get("grade", ""),
                    "attempts": context.attempt,
                    "score_history": context.score_history,
                    "duration": total_time
                }

            except Exception as e:
                self.log(f"품질 루프 오류: {e}", "error")
                import traceback
                traceback.print_exc()

                if not context.can_retry():
                    return self._create_fail_result(context, "error", {"error": str(e)})

        # 최대 재시도 초과
        return self._create_fail_result(context, "max_retries_exceeded", {})

    async def _generate_content(
        self,
        slides: List[Dict],
        prompts: List[Dict],
        food_name: str,
        output_dir: str,
        improvement_prompt: Optional[str] = None,
        problem_slides: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """이미지 생성"""
        print(f"\n   🎨 이미지 생성...")

        # 스킵 모드 체크 (테스트용)
        if self.config.get("skip_generation", False):
            print(f"      (스킵 - 기존 파일 사용)")
            return {"success": True, "output_dir": output_dir, "images": []}

        # 프롬프트에 개선사항 추가
        enhanced_prompts = prompts
        if improvement_prompt:
            enhanced_prompts = []
            for p in prompts:
                enhanced = {
                    **p,
                    "prompt": f"{p['prompt']}\n\nIMPROVEMENTS:\n{improvement_prompt}"
                }
                enhanced_prompts.append(enhanced)

        # 선택적 재생성 (v5.1: 문제 슬라이드만 재생성)
        if problem_slides:
            print(f"      🎯 문제 슬라이드만 재생성: {problem_slides}")
            # 문제가 있는 슬라이드만 필터링하여 재생성
            enhanced_prompts = [p for p in enhanced_prompts if p.get("index") in problem_slides]
            print(f"      📝 재생성 대상: {len(enhanced_prompts)}장")

        result = self._content_crew.run(
            topic=food_name,
            slides=[{"prompt": p["prompt"]} for p in enhanced_prompts],
            output_dir=output_dir,
            skip_generation=self.config.get("skip_generation", False)
        )

        return result

    async def _apply_text_overlay(
        self,
        input_dir: str,
        output_dir: str,
        slides: List[Dict],
        food_name: str
    ) -> Dict[str, Any]:
        """텍스트 오버레이"""
        print(f"\n   ✍️ 텍스트 오버레이...")

        result = self._text_overlay_crew.run(
            input_dir=input_dir,
            output_dir=output_dir,
            slides=slides,
            food_name=food_name
        )

        return result

    async def _run_tech_review(
        self,
        content_dir: str,
        food_name: str
    ) -> Dict[str, Any]:
        """기술 검수"""
        result = self._tech_review_crew.run(
            content_dir=content_dir,
            food_name=food_name
        )

        score = result.get("percentage", 0)
        grade = result.get("grade", "F")

        if score >= self.TECH_PASS_SCORE:
            review_result = ReviewResult.PASS
        elif score >= self.CONDITIONAL_PASS_SCORE:
            review_result = ReviewResult.CONDITIONAL_PASS
        else:
            review_result = ReviewResult.FAIL

        # 피드백 생성
        feedback_parts = []
        details = result.get("details", {})

        file_struct = details.get("file_structure", {})
        if not file_struct.get("pass", True):
            feedback_parts.append("파일 구조 문제")

        return {
            "result": review_result,
            "score": score,
            "grade": grade,
            "feedback": ", ".join(feedback_parts) if feedback_parts else "기술 검수 통과",
            "details": details,
            "pass": result.get("pass", False)
        }

    async def _run_creative_review(
        self,
        content_dir: str,
        food_name: str
    ) -> Dict[str, Any]:
        """크리에이티브 검수"""
        result = self._creative_review_crew.run(
            content_dir=content_dir,
            food_name=food_name
        )

        score = result.get("total_score", 0)
        grade = result.get("grade", "F")

        if score >= self.CREATIVE_PASS_SCORE:
            review_result = ReviewResult.PASS
        elif score >= self.CONDITIONAL_PASS_SCORE:
            review_result = ReviewResult.CONDITIONAL_PASS
        else:
            review_result = ReviewResult.FAIL

        # 피드백 생성
        feedback_parts = []
        categories = result.get("categories", {})

        for cat_name, cat_data in categories.items():
            if cat_data.get("improvements"):
                feedback_parts.extend(cat_data["improvements"][:2])

        # 문제 슬라이드 식별 (VLM에서 제공하는 경우)
        problem_slides = []
        gold_comp = result.get("gold_comparison", {})
        if gold_comp.get("gaps"):
            feedback_parts.extend(gold_comp["gaps"][:2])

        return {
            "result": review_result,
            "score": score,
            "grade": grade,
            "feedback": ", ".join(feedback_parts[:3]) if feedback_parts else "크리에이티브 검수",
            "details": categories,
            "problem_slides": problem_slides,
            "pass": result.get("pass", False)
        }

    def _create_fail_result(
        self,
        context: RetryContext,
        fail_point: str,
        last_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        실패 결과 생성 및 강제 중단

        PD 승인 (2026-01-30):
        - success=False 시 무조건 raise
        - dry-run도 예외 없이 적용
        - 반환값 무시 방지를 위해 예외 발생
        """
        print(f"\n{'━'*60}")
        print(f"❌ 품질 검사 실패 - 게시 차단")
        print(f"{'━'*60}")
        print(f"   실패 지점: {fail_point}")
        print(f"   시도 횟수: {context.attempt}회")
        print(f"   🚨 QualityGateFailed 예외 발생")
        print(f"{'━'*60}")

        # P1 fix: 실패 시 중간 버전 디렉토리 정리 (마지막 버전만 유지)
        self._cleanup_failed_attempts(context)

        # 실패 로그 기록 (NEEDS_REVISION 추적용)
        self._log_gate_failure(context, fail_point, last_result)

        # 마지막 점수 추출
        last_score = 0
        if context.score_history:
            last_score = context.score_history[-1].get("score", 0)

        # 🚨 PD 승인 (2026-01-30): 강제 예외 발생
        # 반환값 무시로 인한 검수 실패 콘텐츠 게시 차단
        raise QualityGateFailed(
            fail_point=fail_point,
            attempts=context.attempt,
            last_score=last_score,
            message=f"품질 게이트 실패: {fail_point} (시도: {context.attempt}회)"
        )

    def _log_gate_failure(
        self,
        context: RetryContext,
        fail_point: str,
        last_result: Dict[str, Any]
    ) -> None:
        """
        품질 게이트 실패 로그 기록

        목적 (Q3): 시스템 취약점 패턴 추출
        형식: JSONL (error_aggregator.py와 호환)
        """
        import json

        log_dir = ROOT / "config" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = log_dir / "quality_gate_failures.jsonl"

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "gate_status": "REJECTED" if fail_point != "needs_revision" else "NEEDS_REVISION",
            "failure_reason": fail_point,
            "retry_count": context.attempt,
            "pipeline_step": fail_point,
            "score_history": context.score_history,
            "tech_feedbacks": context.tech_feedbacks[-3:] if context.tech_feedbacks else [],
            "creative_feedbacks": context.creative_feedbacks[-3:] if context.creative_feedbacks else [],
            "last_result_summary": {
                "score": last_result.get("score", 0),
                "feedback": last_result.get("feedback", "")[:200]
            } if last_result else {}
        }

        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
            print(f"   📝 실패 로그 기록: {log_file.name}")
        except Exception as e:
            print(f"   ⚠️ 로그 기록 실패: {e}")

    def _log_needs_revision(
        self,
        step: str,
        score: float,
        retry_count: int,
        feedback: str
    ) -> None:
        """
        NEEDS_REVISION 로그 기록

        Q2 정의: 경고(WARNING) - 재시도 허용, 3회 후 에러 승격
        Q3 목적: 시스템 취약점 패턴 추출
        """
        import json

        log_dir = ROOT / "config" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        log_file = log_dir / "needs_revision.jsonl"

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "gate_status": "NEEDS_REVISION",
            "pipeline_step": step,
            "score": score,
            "retry_count": retry_count,
            "feedback": feedback[:200] if feedback else "",
            "can_retry": retry_count < 3
        }

        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"   ⚠️ NEEDS_REVISION 로그 기록 실패: {e}")

    def _cleanup_failed_attempts(self, context: RetryContext) -> None:
        """P1 fix: 실패한 시도들의 임시 디렉토리 정리 (마지막 버전만 유지)"""
        import shutil

        if not hasattr(self, '_output_base_dir') or not self._output_base_dir:
            return

        base_dir = Path(self._output_base_dir)
        if not base_dir.exists():
            return

        # v1, v2 등 이전 버전 디렉토리 삭제 (마지막 버전만 유지)
        for i in range(1, context.attempt):
            version_dir = base_dir / f"v{i}"
            if version_dir.exists():
                try:
                    shutil.rmtree(version_dir)
                    print(f"   🗑️ 정리됨: {version_dir.name}")
                except Exception as e:
                    print(f"   ⚠️ 정리 실패: {version_dir.name} - {e}")


class SimpleLogger:
    """간단한 로거"""
    def info(self, msg): print(f"[INFO] {msg}")
    def warning(self, msg): print(f"[WARN] {msg}")
    def error(self, msg): print(f"[ERROR] {msg}")


# 테스트
if __name__ == "__main__":
    import asyncio

    async def test():
        loop = QualityControlLoop(config={
            "max_retries": 3,
            "skip_generation": True
        })

        result = await loop.run_with_quality_loop(
            storyboard_path="storyboards/broccoli_storyboard.md",
            slides=[{"index": 0, "type": "cover", "text": {"title": "BROCCOLI"}}],
            prompts=[{"index": 0, "prompt": "test"}],
            food_name="broccoli",
            food_name_kr="브로콜리",
            output_base_dir="outputs/broccoli_temp"
        )

        print(f"\n결과: {'성공' if result['success'] else '실패'}")

    asyncio.run(test())
