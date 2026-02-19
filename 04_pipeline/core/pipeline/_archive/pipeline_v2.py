"""
Project Sunshine - Pipeline v2.0
단계별 품질 게이트 및 합의 기반 파이프라인

Author: 김부장 (프로젝트 총괄)
Version: 2.0
Date: 2026-01-25

개선 사항:
1. 각 단계 완료 후 Quality Gate 검증
2. 복수 검토자 합의 시스템
3. 자동 수정 및 재검토 루프 (최대 3회)
4. 비용 발생 전 사전 검증 강화
5. 단계별 진행/중단 의사결정
"""

import asyncio
import time
from pathlib import Path
from typing import Dict, Optional, Any, List
from dataclasses import dataclass

# 프로젝트 임포트
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.agents import (
    PlannerAgent,
    PromptGeneratorAgent,
    ImageGeneratorAgent,
    TextOverlayAgent,
    QualityCheckerAgent,
    CaptionAgent,
    PublisherAgent,
)
from core.pipeline.quality_gate import (
    QualityGate,
    GateResult,
    GateStatus,
    auto_fix_prompt,
)
from core.pipeline.display import PipelineDisplay


@dataclass
class StageResult:
    """단계 실행 결과"""
    stage: str
    success: bool
    data: Any = None
    error: str = None
    gate_result: GateResult = None
    elapsed_time: float = 0.0
    revision_count: int = 0


class SunshinePipelineV2:
    """
    Project Sunshine 파이프라인 v2.0
    단계별 품질 게이트 및 합의 기반 진행

    흐름:
    [기획] → Gate1 → [프롬프트] → Gate2 → [이미지] → Gate3 → [오버레이] → Gate4 → [최종검수] → [게시]

    각 Gate에서:
    1. 복수 검토자가 검토
    2. 75% 이상 합의 필요
    3. 불합격 시 자동 수정 후 재검토 (최대 3회)
    4. BLOCKING 이슈 발견 시 즉시 중단
    """

    MAX_REVISIONS = 3

    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = str(Path(__file__).parent.parent / "config" / "config.yaml")

        self.config_path = config_path
        self.agents = self._initialize_agents()
        self.stage_results: List[StageResult] = []

    def _initialize_agents(self):
        """에이전트 초기화"""
        return {
            "planner": PlannerAgent(self.config_path),
            "prompt": PromptGeneratorAgent(self.config_path),
            "image": ImageGeneratorAgent(self.config_path),
            "overlay": TextOverlayAgent(self.config_path),
            "qa": QualityCheckerAgent(self.config_path),
            "caption": CaptionAgent(self.config_path),
            "publish": PublisherAgent(self.config_path),
        }

    async def run(self, topic: str, skip_publish: bool = False) -> Dict:
        """
        파이프라인 v2.0 실행

        Args:
            topic: 콘텐츠 주제
            skip_publish: 게시 스킵 여부

        Returns:
            실행 결과 dict
        """
        print("\n" + "=" * 70)
        print("🌟 Project Sunshine Pipeline v2.0 - Quality Gate Enabled")
        print("=" * 70)
        print(f"📋 Topic: {topic}")
        print("=" * 70 + "\n")

        results = {}
        total_start = time.time()

        # ============================================================
        # Stage 1: 기획 (Planning)
        # ============================================================
        print("\n[STAGE 1/6] 📋 기획 (Planning)")
        print("-" * 50)

        plan_result = await self._run_stage_with_gate(
            stage_name="plan",
            agent_key="planner",
            input_data={"topic": topic},
            gate_name="Plan Review Gate"
        )

        if not plan_result.success:
            return self._create_failure_result("plan", plan_result)

        results["plan"] = plan_result.data
        print(f"✅ 기획 완료: {len(plan_result.data.get('slides', []))} 슬라이드")

        # ============================================================
        # Stage 2: 프롬프트 생성 (Prompt Generation)
        # ★ 가장 중요한 Gate - 이미지 생성 전 철저 검증 ★
        # ============================================================
        print("\n[STAGE 2/6] ✍️ 프롬프트 생성 (Prompt Generation)")
        print("-" * 50)
        print("⚠️  [CRITICAL GATE] 이미지 생성 비용 발생 전 최종 검증")

        prompt_result = await self._run_stage_with_gate(
            stage_name="prompt",
            agent_key="prompt",
            input_data=plan_result.data,
            gate_name="Prompt Review Gate (Pre-Image)",
            auto_fix_func=auto_fix_prompt
        )

        if not prompt_result.success:
            return self._create_failure_result("prompt", prompt_result)

        results["prompts"] = prompt_result.data
        print(f"✅ 프롬프트 완료: {len(prompt_result.data.get('prompts', []))}개")

        # ============================================================
        # Stage 3: 이미지 생성 (Image Generation)
        # ★ 비용 발생 단계 - Gate2 통과 후에만 진행 ★
        # ============================================================
        print("\n[STAGE 3/6] 🎨 이미지 생성 (Image Generation)")
        print("-" * 50)
        print("💰 API 비용 발생 단계 - 프롬프트 Gate 통과 확인됨")

        image_result = await self._run_stage_with_gate(
            stage_name="image",
            agent_key="image",
            input_data=prompt_result.data,
            gate_name="Image Review Gate"
        )

        if not image_result.success:
            return self._create_failure_result("image", image_result)

        results["images"] = image_result.data
        print(f"✅ 이미지 생성 완료: {len(image_result.data.get('images', []))}장")

        # ============================================================
        # Stage 4: 텍스트 오버레이 (Text Overlay)
        # ============================================================
        print("\n[STAGE 4/6] ✏️ 텍스트 오버레이 (Text Overlay)")
        print("-" * 50)

        overlay_input = {**image_result.data, "topic": topic}
        overlay_result = await self._run_stage_with_gate(
            stage_name="overlay",
            agent_key="overlay",
            input_data=overlay_input,
            gate_name="Overlay Review Gate"
        )

        if not overlay_result.success:
            return self._create_failure_result("overlay", overlay_result)

        results["overlay"] = overlay_result.data
        print(f"✅ 오버레이 완료: {overlay_result.data.get('count', 0)}장")

        # ============================================================
        # Stage 5: 최종 품질 검수 (Final QA)
        # ★ 모든 검토자 합의 필요 ★
        # ============================================================
        print("\n[STAGE 5/6] 🔍 최종 품질 검수 (Final QA)")
        print("-" * 50)
        print("⚠️  [FINAL GATE] 모든 검토자 합의 필요")

        qa_input = {
            **overlay_result.data,
            "images": [{"path": p} for p in overlay_result.data.get("output_images", [])],
            "topic": topic
        }

        qa_result = await self._run_stage_with_gate(
            stage_name="final",
            agent_key="qa",
            input_data=qa_input,
            gate_name="Final Quality Gate"
        )

        results["qa"] = qa_result.data

        if not qa_result.success:
            print("\n" + "=" * 70)
            print("🚫 최종 검수 불합격 - 게시 불가")
            print("=" * 70)
            return self._create_failure_result("qa", qa_result)

        # ============================================================
        # Stage 6: 캡션 생성 및 게시
        # ============================================================
        print("\n[STAGE 6/6] 📤 캡션 생성 및 게시")
        print("-" * 50)

        # 캡션 생성
        caption_input = {
            "topic": topic,
            "topic_kr": results["plan"].get("topic_kr", topic),
            "safety": results["plan"].get("safety", "safe"),
        }
        caption_result = await self.agents["caption"].run(caption_input)
        results["caption"] = caption_result.data if caption_result.success else {}

        # 게시
        if skip_publish:
            print("⏭️  게시 스킵됨 (--dry-run)")
            results["publish"] = {"skipped": True}
        else:
            publish_result = await self.agents["publish"].run(qa_result.data)
            results["publish"] = publish_result.data if publish_result.success else {}

        # ============================================================
        # 완료 요약
        # ============================================================
        total_elapsed = time.time() - total_start
        self._print_summary(results, total_elapsed)

        return {
            "success": True,
            "results": results,
            "stage_results": self.stage_results,
            "total_time": total_elapsed
        }

    async def _run_stage_with_gate(
        self,
        stage_name: str,
        agent_key: str,
        input_data: Any,
        gate_name: str,
        auto_fix_func=None
    ) -> StageResult:
        """
        단계 실행 + Quality Gate 검증

        Args:
            stage_name: 단계 이름
            agent_key: 에이전트 키
            input_data: 입력 데이터
            gate_name: 게이트 이름
            auto_fix_func: 자동 수정 함수 (옵션)

        Returns:
            StageResult
        """
        gate = QualityGate(gate_name, max_revisions=self.MAX_REVISIONS)
        revision_count = 0
        current_input = input_data

        while True:
            # 에이전트 실행
            start = time.time()
            agent_result = await self.agents[agent_key].run(current_input)
            elapsed = time.time() - start

            if not agent_result.success:
                result = StageResult(
                    stage=stage_name,
                    success=False,
                    error=agent_result.error,
                    elapsed_time=elapsed
                )
                self.stage_results.append(result)
                return result

            # Quality Gate 검토
            print(f"\n   🚦 Quality Gate 검토 중... ({gate_name})")
            gate_result = gate.review(agent_result.data, stage_name)

            # 리포트 출력
            print(gate.format_report(gate_result))

            if gate_result.can_proceed:
                # 통과
                result = StageResult(
                    stage=stage_name,
                    success=True,
                    data=agent_result.data,
                    gate_result=gate_result,
                    elapsed_time=elapsed,
                    revision_count=revision_count
                )
                self.stage_results.append(result)
                return result

            elif gate_result.needs_revision and auto_fix_func and revision_count < self.MAX_REVISIONS:
                # 자동 수정 시도
                revision_count += 1
                gate.increment_revision()
                print(f"   🔧 자동 수정 시도 ({revision_count}/{self.MAX_REVISIONS})...")

                # 수정된 입력으로 재실행
                all_issues = []
                for review in gate_result.reviews:
                    all_issues.extend(review.issues)

                current_input = auto_fix_func(agent_result.data, all_issues)
                print("   ↩️  수정 완료, 재검토 진행...")
                continue

            else:
                # 실패 (수정 불가 또는 최대 횟수 초과)
                result = StageResult(
                    stage=stage_name,
                    success=False,
                    data=agent_result.data,
                    error=f"Quality Gate 불합격 (합의율: {gate_result.consensus_score:.1f}%)",
                    gate_result=gate_result,
                    elapsed_time=elapsed,
                    revision_count=revision_count
                )
                self.stage_results.append(result)
                return result

    def _create_failure_result(self, stage: str, stage_result: StageResult) -> Dict:
        """실패 결과 생성"""
        return {
            "success": False,
            "failed_stage": stage,
            "error": stage_result.error,
            "gate_result": stage_result.gate_result,
            "stage_results": self.stage_results
        }

    def _print_summary(self, results: Dict, total_time: float):
        """실행 요약 출력"""
        print("\n" + "=" * 70)
        print("📊 Pipeline v2.0 실행 요약")
        print("=" * 70)

        for sr in self.stage_results:
            status = "✅" if sr.success else "❌"
            revision_info = f" (수정 {sr.revision_count}회)" if sr.revision_count > 0 else ""
            print(f"   {status} {sr.stage}: {sr.elapsed_time:.1f}초{revision_info}")

        print("-" * 70)
        print(f"   총 소요시간: {total_time:.1f}초")
        print("=" * 70 + "\n")


# ============================================================
# CLI 실행
# ============================================================

async def main():
    """테스트 실행"""
    import sys

    topic = sys.argv[1] if len(sys.argv) > 1 else "mango"
    skip_publish = "--dry-run" in sys.argv

    pipeline = SunshinePipelineV2()
    result = await pipeline.run(topic, skip_publish=skip_publish)

    if result["success"]:
        print("🎉 파이프라인 완료!")
    else:
        print(f"❌ 파이프라인 실패: {result.get('failed_stage')} 단계")
        print(f"   오류: {result.get('error')}")


if __name__ == "__main__":
    asyncio.run(main())
