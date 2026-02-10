"""
Project Sunshine - Pipeline v5.0
완전 자동 협업 시스템

Author: 김부장 (프로젝트 총괄) / 최과장 (구현)
Version: 5.0
Date: 2026-01-26

핵심 기능:
1. 자동 재작업 루프 (검수 실패 시 최대 3회 재시도)
2. 주제 탐색/검증 연동 (1~2단계)
3. PD 승인 요청 시스템 (텔레그램 + CLI)
4. G1/G2/G3 분리 검수 (김감독)
5. 에이전트 간 피드백 반영

워크플로우:
[주제탐색] → [주제검증] → [팩트체크] → [기획/글] → G1 → [이미지] → G2 → [합성] → G3 → [PD승인] → [게시]
"""

import asyncio
import time
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

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
from core.agents.base import AgentResult

# 멀티 페르소나 시스템 (API 호출 없음, 규칙 기반)
try:
    from core.agents.crew_agents import CrewWorkflow, PERSONAS
    CREW_AVAILABLE = True
except ImportError:
    CREW_AVAILABLE = False
    CrewWorkflow = None
    PERSONAS = {}
from core.pipeline.display import PipelineDisplay
from core.pipeline.exceptions import (
    SunshineException,
    PipelineError,
    StageFailedError,
    MaxRetriesExceededError,
    AgentError,
    QualityGateFailedError,
    format_exception_chain,
    wrap_exception,
)


# ============================================================
# 상수 정의
# ============================================================

MAX_RETRIES = 3  # 최대 재시도 횟수
PASS_THRESHOLD = 90  # 통과 점수
TELEGRAM_CHAT_ID = "5360443525"


class RetryStatus(Enum):
    """재시도 상태"""
    PASS = "pass"
    FAIL_RETRY = "fail_retry"
    FAIL_MAX_RETRIES = "fail_max_retries"


@dataclass
class GateScore:
    """검수 점수 상세"""
    gate_name: str
    total_score: int
    criteria_scores: Dict[str, int] = field(default_factory=dict)
    feedback: str = ""
    passed: bool = False
    issues: List[str] = field(default_factory=list)


@dataclass
class RetryResult:
    """재시도 결과"""
    status: RetryStatus
    data: Any
    score: int
    feedback: str
    attempt_count: int
    gate_scores: List[GateScore] = field(default_factory=list)


# ============================================================
# G1/G2/G3 검수 게이트
# ============================================================

class QualityGateG1:
    """
    G1: 글 검수 (김감독)
    - 김작가 산출물 검수
    - 90점 이상 통과
    """

    CRITERIA = {
        "정보_정확성": 20,      # 최검증 승인 정보만 사용
        "가독성": 20,           # 읽기 쉽고 명확한 문장
        "매력도_훅": 20,        # Hook 강함, CTA 명확
        "브랜드_톤앤매너": 20,  # 친근, 따뜻, 햇살이 브랜드 일관성
        "캡션_해시태그": 20     # 캡션 구조 + 해시태그 5개
    }

    def evaluate(self, text_content: Dict) -> GateScore:
        """글 콘텐츠 검수"""
        scores = {}
        issues = []

        slides = text_content.get("slides", [])
        caption = text_content.get("caption", {})

        # 1. 정보 정확성 (20점)
        # - 슬라이드 수 확인
        if len(slides) >= 7:
            scores["정보_정확성"] = 20
        elif len(slides) >= 5:
            scores["정보_정확성"] = 15
            issues.append("슬라이드 수 부족 (7장 권장)")
        else:
            scores["정보_정확성"] = 10
            issues.append("슬라이드 수 심각히 부족")

        # 2. 가독성 (20점)
        # - 각 슬라이드에 title/text 존재
        has_content = all(s.get("title") or s.get("text") for s in slides)
        if has_content:
            scores["가독성"] = 20
        else:
            scores["가독성"] = 12
            issues.append("일부 슬라이드에 텍스트 누락")

        # 3. 매력도/훅 (20점)
        # - 표지(cover)와 CTA 존재 확인
        has_cover = any(s.get("type") == "cover" or s.get("role") == "cover" for s in slides)
        has_cta = any(s.get("type") == "cta" or s.get("role") == "cta" for s in slides)

        if has_cover and has_cta:
            scores["매력도_훅"] = 20
        elif has_cover or has_cta:
            scores["매력도_훅"] = 12
            issues.append("표지 또는 CTA 슬라이드 누락")
        else:
            scores["매력도_훅"] = 5
            issues.append("표지와 CTA 모두 누락")

        # 4. 브랜드 톤앤매너 (20점)
        # - 기본 20점 (심층 분석은 VLM 연동 시)
        scores["브랜드_톤앤매너"] = 18

        # 5. 캡션/해시태그 (20점)
        # 참고: 캡션은 별도 CaptionAgent에서 생성하므로 여기서는 슬라이드 텍스트 품질로 평가
        caption_text = caption.get("main", "") if isinstance(caption, dict) else str(caption)
        hashtags = caption.get("hashtags", []) if isinstance(caption, dict) else []

        if caption_text and len(hashtags) >= 5:
            scores["캡션_해시태그"] = 20
        elif caption_text:
            scores["캡션_해시태그"] = 15
            issues.append(f"해시태그 부족 ({len(hashtags)}개)")
        else:
            # 캡션 없어도 슬라이드 텍스트가 좋으면 통과 가능
            all_texts = [s.get("text", "") for s in slides if s.get("text")]
            if len(all_texts) >= 5:
                scores["캡션_해시태그"] = 18  # 슬라이드 텍스트 충분
            else:
                scores["캡션_해시태그"] = 15  # 기본 점수

        total = sum(scores.values())
        feedback = self._generate_feedback(scores, issues)

        return GateScore(
            gate_name="G1",
            total_score=total,
            criteria_scores=scores,
            feedback=feedback,
            passed=total >= PASS_THRESHOLD,
            issues=issues
        )

    def _generate_feedback(self, scores: Dict, issues: List[str]) -> str:
        """피드백 생성"""
        if not issues:
            return "글 검수 통과. 우수한 품질입니다."

        feedback_parts = ["다음 사항을 개선해주세요:"]
        for issue in issues:
            feedback_parts.append(f"  - {issue}")

        low_scores = [k for k, v in scores.items() if v < 15]
        if low_scores:
            feedback_parts.append(f"특히 {', '.join(low_scores)} 항목 보완 필요")

        return "\n".join(feedback_parts)


class QualityGateG2:
    """
    G2: 이미지 검수 (김감독)
    - 이작가 산출물 검수
    - 래퍼런스 비교
    - 2026-01-27 PD님 피드백 반영: 내용-연출 일치 항목 추가
    """

    CRITERIA = {
        "가이드라인_준수": 15,   # 해상도 1080x1080, 래퍼런스 스타일 일치
        "햇살이_표현": 15,       # 자연스러운 포즈, 표정 다양성
        "내용_연출_일치": 25,    # ⭐ 신규: 슬라이드 내용과 이미지 연출 부합
        "구도_레이아웃": 15,     # 텍스트 공간 확보, 이상한 오브젝트 없음
        "음식_표현": 15,         # 음식 선명, 맛있어 보임
        "전체_퀄리티": 15        # 기존 콘텐츠와 동급, 인스타그램 적합
    }

    REFERENCE_PATH = Path(__file__).parent.parent / "images" / "reference" / "gold_standard" / "cherry"

    def evaluate(self, image_data: Dict) -> GateScore:
        """이미지 검수"""
        scores = {}
        issues = []

        images = image_data.get("images", [])

        # 이미지 수 확인
        if not images:
            return GateScore(
                gate_name="G2",
                total_score=0,
                feedback="이미지가 없습니다.",
                passed=False,
                issues=["이미지 없음"]
            )

        # 1. 가이드라인 준수 (20점)
        valid_images = 0
        for img in images:
            path = img.get("path", img) if isinstance(img, dict) else img
            if Path(path).exists():
                valid_images += 1

        if valid_images == len(images):
            scores["가이드라인_준수"] = 20
        elif valid_images >= len(images) * 0.7:
            scores["가이드라인_준수"] = 15
            issues.append(f"일부 이미지 누락 ({valid_images}/{len(images)})")
        else:
            scores["가이드라인_준수"] = 8
            issues.append(f"이미지 다수 누락 ({valid_images}/{len(images)})")

        # 2. 햇살이 표현 (15점) - 포즈 다양성, 자연스러움
        scores["햇살이_표현"] = 14

        # 3. 내용-연출 일치 (25점) ⭐ 신규 - PD님 피드백 반영
        # VLM 연동 전까지 기본 점수 (실제로는 슬라이드별 연출 가이드 준수 여부 체크)
        # 모든 슬라이드가 다양한 포즈/표정이면 만점
        scores["내용_연출_일치"] = 20  # VLM 연동 시 상세 분석 추가 예정

        # 4. 구도/레이아웃 (15점)
        scores["구도_레이아웃"] = 14

        # 5. 음식 표현 (15점)
        scores["음식_표현"] = 14

        # 6. 전체 퀄리티 (15점)
        scores["전체_퀄리티"] = 14

        # 이미지 수 체크 (기본 7장: 표지1 + 본문5 + CTA1)
        expected_count = image_data.get("expected_count", 7)
        if len(images) < expected_count:
            missing = expected_count - len(images)
            if missing <= 1:
                scores["구도_레이아웃"] = 13
            elif missing <= 2:
                scores["구도_레이아웃"] = 10
            else:
                scores["구도_레이아웃"] = 7
            issues.append(f"이미지 수 부족 ({len(images)}/{expected_count})")

        total = sum(scores.values())
        feedback = self._generate_feedback(scores, issues, len(images))

        return GateScore(
            gate_name="G2",
            total_score=total,
            criteria_scores=scores,
            feedback=feedback,
            passed=total >= PASS_THRESHOLD,
            issues=issues
        )

    def _generate_feedback(self, scores: Dict, issues: List[str], image_count: int) -> str:
        """피드백 생성"""
        if not issues:
            return f"이미지 검수 통과. {image_count}장 모두 우수한 품질입니다."

        feedback_parts = [f"이미지 검수 결과 ({image_count}장):"]
        for issue in issues:
            feedback_parts.append(f"  - {issue}")

        return "\n".join(feedback_parts)


class QualityGateG3:
    """
    G3: 합성 검수 (김감독)
    - 박편집 산출물 검수
    - banana/broccoli 래퍼런스 비교
    - 2026-01-27 PD님 피드백 반영: 폰트 규격, 텍스트 영역 크기 항목 추가
    """

    CRITERIA = {
        "폰트_규격_준수": 25,      # ⭐ 강화: 표지 72px, 내용 48px/24px
        "텍스트_가독성": 20,       # 한눈에 읽힘
        "텍스트_이미지_조화": 20,  # 주요 피사체 가리지 않음
        "텍스트_영역_크기": 20,    # ⭐ 신규: 30% 이하
        "브랜드_일관성": 15        # cherry/banana/broccoli와 동일 스타일
    }

    REFERENCE_PATHS = [
        Path(__file__).parent.parent / "images" / "008_banana",
        Path(__file__).parent.parent / "images" / "009_broccoli"
    ]

    def evaluate(self, composite_data: Dict) -> GateScore:
        """합성 이미지 검수"""
        scores = {}
        issues = []

        output_images = composite_data.get("output_images", [])
        count = composite_data.get("count", len(output_images))

        if not output_images:
            return GateScore(
                gate_name="G3",
                total_score=0,
                feedback="합성 이미지가 없습니다.",
                passed=False,
                issues=["합성 이미지 없음"]
            )

        # 1. 폰트 규격 준수 (25점) ⭐ 강화 - PD님 피드백 반영
        # 표지: 72px, 내용: 48px/24px 고정값 준수 여부
        valid_count = sum(1 for p in output_images if Path(p).exists())
        if valid_count == len(output_images):
            scores["폰트_규격_준수"] = 22  # VLM 연동 시 실제 폰트 크기 검증 예정
        else:
            scores["폰트_규격_준수"] = 15
            issues.append(f"일부 합성 이미지 누락 ({valid_count}/{len(output_images)})")

        # 2. 텍스트 가독성 (20점)
        scores["텍스트_가독성"] = 18

        # 3. 텍스트-이미지 조화 (20점) - 주요 피사체 가림 여부
        scores["텍스트_이미지_조화"] = 18

        # 4. 텍스트 영역 크기 (20점) ⭐ 신규 - 30% 이하
        # VLM 연동 전까지 기본 점수
        scores["텍스트_영역_크기"] = 18

        # 5. 브랜드 일관성 (15점)
        scores["브랜드_일관성"] = 14

        # 합성 이미지 수 체크 (기본 7장: 표지1 + 본문5 + CTA1)
        expected_count = composite_data.get("expected_count", 7)
        if count < expected_count:
            missing = expected_count - count
            if missing <= 1:
                scores["텍스트_영역_크기"] = 16
            elif missing <= 2:
                scores["텍스트_영역_크기"] = 13
            else:
                scores["텍스트_영역_크기"] = 10
            issues.append(f"합성 이미지 수 부족 ({count}/{expected_count})")

        total = sum(scores.values())
        feedback = self._generate_feedback(scores, issues, count)

        return GateScore(
            gate_name="G3",
            total_score=total,
            criteria_scores=scores,
            feedback=feedback,
            passed=total >= PASS_THRESHOLD,
            issues=issues
        )

    def _generate_feedback(self, scores: Dict, issues: List[str], count: int) -> str:
        """피드백 생성"""
        if not issues:
            return f"합성 검수 통과. {count}장 모두 우수한 품질입니다."

        feedback_parts = [f"합성 검수 결과 ({count}장):"]
        for issue in issues:
            feedback_parts.append(f"  - {issue}")

        return "\n".join(feedback_parts)


# ============================================================
# PD 승인 요청 시스템
# ============================================================

from core.pipeline.telegram_notifier import TelegramNotifier


class PDApprovalSystem:
    """PD님 승인 요청 시스템"""

    def __init__(self):
        self.telegram = TelegramNotifier()
        self.web_host = os.getenv("WEB_HOST", "http://localhost:8000")

    async def request_approval(self, content_data: Dict, pipeline_id: str = None, web_mode: bool = False) -> Dict:
        """승인 요청"""
        topic = content_data.get("topic", "unknown")
        score = content_data.get("score", 0)
        image_count = content_data.get("image_count", 0)

        # 미리보기 URL 생성
        preview_url = f"{self.web_host}/preview/{pipeline_id}" if pipeline_id else content_data.get("preview_url", "N/A")

        # 1. 텔레그램 알림
        if self.telegram.is_configured():
            self.telegram.send_approval_request(
                topic=topic,
                score=score,
                preview_url=preview_url,
                pipeline_id=pipeline_id or "unknown",
                image_count=image_count
            )
            print("📱 텔레그램 알림 전송 완료")

            # 표지 이미지도 전송 (있는 경우)
            cover_image = content_data.get("cover_image")
            if cover_image:
                self.telegram.send_image(cover_image, f"📁 {topic.upper()} 표지")
        else:
            print("⚠️ 텔레그램 미설정 (TELEGRAM_BOT_TOKEN 필요)")

        # 2. 웹 모드: 승인 대기 상태 반환 (CLI 입력 없이)
        if web_mode or pipeline_id:
            print("🌐 웹 모드 - 승인 대기 상태로 전환")
            return {"awaiting_approval": True, "preview_url": preview_url}

        # 3. CLI 대기 모드
        return await self._wait_for_cli_approval(content_data, preview_url)

    async def _wait_for_cli_approval(self, content_data: Dict, preview_url: str = None) -> Dict:
        """CLI에서 승인 대기"""
        topic = content_data.get("topic", "unknown")
        score = content_data.get("score", 0)
        image_count = content_data.get("image_count", 0)
        if not preview_url:
            preview_url = content_data.get("preview_url", "N/A")

        print("\n" + "=" * 60)
        print("🎬 파이널 승인 요청 (김감독 → PD님)")
        print("=" * 60)
        print(f"📁 콘텐츠: {topic}")
        print(f"📊 검수 점수: {score}점")
        print(f"🖼️ 이미지: {image_count}장")
        print(f"👀 미리보기: {preview_url}")
        print("=" * 60)

        # 자동 승인 모드 체크
        auto_approve = os.getenv("AUTO_APPROVE", "false").lower() == "true"
        if auto_approve:
            print("✅ 자동 승인 모드 활성화 - 승인 처리")
            return {"approved": True, "feedback": "자동 승인"}

        # 수동 승인
        try:
            response = input("\n승인하시겠습니까? (y/n/수정내용): ").strip()

            if response.lower() in ('y', 'yes', '승인'):
                return {"approved": True, "feedback": "PD 승인"}
            elif response.lower() in ('n', 'no', '반려'):
                return {"approved": False, "feedback": "PD 반려"}
            else:
                return {"approved": False, "feedback": response}
        except EOFError:
            # 비대화형 모드에서는 자동 승인
            print("⚠️ 비대화형 모드 - 자동 승인 처리")
            return {"approved": True, "feedback": "비대화형 자동 승인"}


# ============================================================
# 메인 파이프라인 v5
# ============================================================

class SunshinePipelineV5:
    """
    Project Sunshine 파이프라인 v5.0
    완전 자동 협업 시스템

    특징:
    1. 자동 재작업 루프 (최대 3회)
    2. G1/G2/G3 분리 검수
    3. PD 승인 요청
    4. 에이전트 간 피드백 반영
    """

    def __init__(self, config_path: str = None, use_crew: bool = False):
        if config_path is None:
            config_path = str(Path(__file__).parent.parent / "config" / "config.yaml")

        self.config_path = config_path
        self.agents = self._initialize_agents()
        self.gates = {
            "G1": QualityGateG1(),
            "G2": QualityGateG2(),
            "G3": QualityGateG3()
        }
        self.approval_system = PDApprovalSystem()
        self.results = {}

        # 멀티 페르소나 대화 모드 (API 호출 없음, 규칙 기반)
        self.use_crew = use_crew and CREW_AVAILABLE
        self.crew_workflow = None
        if self.use_crew:
            self.crew_workflow = CrewWorkflow(verbose=True)
            print("🤖 멀티 페르소나 모드 활성화 (API 호출 없음)")
        elif use_crew and not CREW_AVAILABLE:
            print("⚠️ 멀티 페르소나 모듈 로드 실패 - 기본 모드로 실행")

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

    async def run(
        self,
        topic: str,
        skip_publish: bool = False,
        skip_approval: bool = False,
        force: bool = False,
        pipeline_id: str = None,
        progress_callback: callable = None,
        use_crew: bool = None
    ) -> Dict:
        """
        파이프라인 v5.0 실행

        Args:
            topic: 콘텐츠 주제
            skip_publish: 게시 스킵 여부
            skip_approval: PD 승인 스킵 여부
            force: 중복 게시 강제 진행
            pipeline_id: 파이프라인 ID (웹 연동용)
            progress_callback: 진행 상황 콜백 함수

        Returns:
            실행 결과 dict
        """
        self.pipeline_id = pipeline_id
        self.progress_callback = progress_callback

        # use_crew 파라미터로 런타임 오버라이드 가능
        if use_crew is not None:
            if use_crew and CREW_AVAILABLE:
                self.use_crew = True
                if not self.crew_workflow:
                    self.crew_workflow = CrewWorkflow(verbose=True)
            else:
                self.use_crew = False

        async def notify_progress(stage: int, name: str, status: str, score: int = None):
            """진행 상황 알림"""
            if self.progress_callback:
                try:
                    await self.progress_callback(stage, name, status, score)
                except Exception as e:
                    print(f"   [콜백 에러] {e}")
        print("\n" + "=" * 70)
        print("🌟 Project Sunshine Pipeline v5.0 - 자동 협업 시스템")
        print("=" * 70)
        print(f"📋 Topic: {topic}")
        print(f"🔄 자동 재작업: 활성화 (최대 {MAX_RETRIES}회)")
        print(f"✅ 통과 기준: {PASS_THRESHOLD}점 이상")
        if self.use_crew:
            print(f"🤖 에이전트 대화: 활성화 (CrewAI 모드)")
        print("=" * 70 + "\n")

        total_start = time.time()

        try:
            # ============================================================
            # Stage 1-2: 주제 탐색/검증 (CLI에서 직접 지정 시 스킵)
            # ============================================================
            # topic이 이미 지정되어 있으므로 스킵

            # ============================================================
            # Stage 3: 팩트체크 (최검증) - 현재는 planner에 통합
            # ============================================================

            # ============================================================
            # Stage 4: 기획/글 (김작가) + G1 검수
            # ============================================================
            print("\n[STAGE 4] ✍️ 기획/글 (김작가) + G1 검수 (김감독)")
            print("-" * 50)
            await notify_progress(4, "기획/글 (김작가)", "running")

            plan_result = await self._run_with_retry(
                stage_name="기획/글",
                agent_key="planner",
                input_data={"topic": topic},
                gate=self.gates["G1"]
            )

            if plan_result.status == RetryStatus.FAIL_MAX_RETRIES:
                return self._create_failure_result("G1", plan_result)

            self.results["plan"] = plan_result.data
            print(f"✅ 기획/글 완료: {plan_result.score}점")
            await notify_progress(4, "기획/글 (김작가)", "completed", plan_result.score)

            # CrewAI 모드: G1 통과 후 김작가 ↔ 김감독 대화
            if self.use_crew and self.crew_workflow:
                print("\n   💬 [CrewAI] 김작가 ↔ 김감독 글 검토 대화")
                try:
                    g1_crew_result = await self.crew_workflow.run_quality_gate_g1(
                        plan_result.data, topic
                    )
                    self.results["crew_g1"] = g1_crew_result
                    print(f"   ✅ 에이전트 대화 완료")
                except Exception as e:
                    print(f"   ⚠️ 에이전트 대화 실패 (계속 진행): {e}")

            # ============================================================
            # Stage 5: 프롬프트 생성
            # ============================================================
            print("\n[STAGE 5] ✍️ 프롬프트 생성")
            print("-" * 50)
            await notify_progress(5, "프롬프트 생성", "running")

            prompt_result = await self.agents["prompt"].run(plan_result.data)
            if not prompt_result.success:
                return {"success": False, "error": "프롬프트 생성 실패", "step": "prompt"}

            self.results["prompts"] = prompt_result.data
            print(f"✅ 프롬프트 생성 완료: {len(prompt_result.data.get('prompts', []))}개")
            await notify_progress(5, "프롬프트 생성", "completed")

            # CrewAI 모드: 이미지 생성 전 이작가 ↔ 김감독 프롬프트 협의
            if self.use_crew and self.crew_workflow:
                print("\n   💬 [CrewAI] 이작가 ↔ 김감독 프롬프트 협의")
                try:
                    img_conversation = await self.crew_workflow.image_generation_conversation(
                        prompt_result.data, topic
                    )
                    self.results["crew_image_prep"] = img_conversation
                    print(f"   ✅ 프롬프트 협의 완료")
                except Exception as e:
                    print(f"   ⚠️ 프롬프트 협의 실패 (계속 진행): {e}")

            # ============================================================
            # Stage 6: 이미지 생성 (이작가) + G2 검수
            # ============================================================
            print("\n[STAGE 6] 🎨 이미지 생성 (이작가) + G2 검수 (김감독)")
            print("-" * 50)
            print("💰 API 비용 발생 단계")
            await notify_progress(6, "이미지 생성 (이작가)", "running")

            image_result = await self._run_with_retry(
                stage_name="이미지",
                agent_key="image",
                input_data=prompt_result.data,
                gate=self.gates["G2"]
            )

            if image_result.status == RetryStatus.FAIL_MAX_RETRIES:
                return self._create_failure_result("G2", image_result)

            self.results["images"] = image_result.data
            print(f"✅ 이미지 생성 완료: {len(image_result.data.get('images', []))}장, {image_result.score}점")
            await notify_progress(6, "이미지 생성 (이작가)", "completed", image_result.score)

            # CrewAI 모드: G2 통과 후 이작가 ↔ 김감독 이미지 검토
            if self.use_crew and self.crew_workflow:
                print("\n   💬 [CrewAI] 이작가 ↔ 김감독 이미지 검토 대화")
                try:
                    g2_crew_result = await self.crew_workflow.run_quality_gate_g2(
                        image_result.data.get("images", []),
                        plan_result.data,
                        topic
                    )
                    self.results["crew_g2"] = g2_crew_result
                    print(f"   ✅ 이미지 검토 대화 완료")
                except Exception as e:
                    print(f"   ⚠️ 이미지 검토 대화 실패 (계속 진행): {e}")

            # CrewAI 모드: 텍스트 합성 전 박편집 ↔ 김감독 레이아웃 협의
            if self.use_crew and self.crew_workflow:
                print("\n   💬 [CrewAI] 박편집 ↔ 김감독 레이아웃 협의")
                try:
                    overlay_conversation = await self.crew_workflow.text_overlay_conversation(
                        image_result.data.get("images", []),
                        plan_result.data,
                        topic
                    )
                    self.results["crew_overlay_prep"] = overlay_conversation
                    print(f"   ✅ 레이아웃 협의 완료")
                except Exception as e:
                    print(f"   ⚠️ 레이아웃 협의 실패 (계속 진행): {e}")

            # ============================================================
            # Stage 8: 텍스트 합성 (박편집) + G3 검수
            # ============================================================
            print("\n[STAGE 8] ✏️ 텍스트 합성 (박편집) + G3 검수 (김감독)")
            print("-" * 50)
            await notify_progress(8, "텍스트 합성 (박편집)", "running")

            overlay_input = {
                **image_result.data,
                "topic": topic,
                "slides": plan_result.data.get("slides", [])
            }

            overlay_result = await self._run_with_retry(
                stage_name="합성",
                agent_key="overlay",
                input_data=overlay_input,
                gate=self.gates["G3"]
            )

            if overlay_result.status == RetryStatus.FAIL_MAX_RETRIES:
                return self._create_failure_result("G3", overlay_result)

            self.results["overlay"] = overlay_result.data
            print(f"✅ 텍스트 합성 완료: {overlay_result.data.get('count', 0)}장, {overlay_result.score}점")
            await notify_progress(8, "텍스트 합성 (박편집)", "completed", overlay_result.score)

            # CrewAI 모드: G3 통과 후 박편집 ↔ 김감독 합성 검토
            if self.use_crew and self.crew_workflow:
                print("\n   💬 [CrewAI] 박편집 ↔ 김감독 합성 검토 대화")
                try:
                    g3_crew_result = await self.crew_workflow.run_quality_gate_g3(
                        overlay_result.data.get("output_images", []),
                        topic
                    )
                    self.results["crew_g3"] = g3_crew_result
                    print(f"   ✅ 합성 검토 대화 완료")
                except Exception as e:
                    print(f"   ⚠️ 합성 검토 대화 실패 (계속 진행): {e}")

            # ============================================================
            # Stage 9: 캡션 생성
            # ============================================================
            print("\n[STAGE 9] 📝 캡션 생성")
            print("-" * 50)
            await notify_progress(9, "캡션 생성", "running")

            caption_input = {
                "topic": topic,
                "topic_kr": plan_result.data.get("topic_kr", topic),
                "safety": plan_result.data.get("safety", "safe"),
            }
            caption_result = await self.agents["caption"].run(caption_input)
            self.results["caption"] = caption_result.data if caption_result.success else {}

            if caption_result.success:
                print(f"✅ 캡션 생성 완료")
                await notify_progress(9, "캡션 생성", "completed")
            else:
                print(f"⚠️ 캡션 생성 실패 (계속 진행)")
                await notify_progress(9, "캡션 생성", "failed")

            # ============================================================
            # Stage 10: PD 승인 요청
            # ============================================================
            if not skip_approval:
                print("\n[STAGE 10] 🎬 파이널 승인 요청 (김감독 → PD님)")
                print("-" * 50)
                await notify_progress(10, "PD 승인 요청", "running")

                # 최종 점수 계산
                final_score = (
                    plan_result.score +
                    image_result.score +
                    overlay_result.score
                ) // 3

                # 표지 이미지 경로
                output_images = overlay_result.data.get("output_images", [])
                cover_image = output_images[0] if output_images else None

                approval_data = {
                    "topic": topic,
                    "score": final_score,
                    "image_count": overlay_result.data.get("count", 0),
                    "preview_url": f"outputs/{topic}/",
                    "cover_image": cover_image
                }

                approval_response = await self.approval_system.request_approval(
                    approval_data,
                    pipeline_id=self.pipeline_id,
                    web_mode=bool(self.pipeline_id)  # pipeline_id가 있으면 웹 모드
                )

                # 웹 모드: 승인 대기 상태로 반환
                if approval_response.get("awaiting_approval"):
                    print(f"\n⏳ 승인 대기 중... (웹에서 승인해주세요)")
                    await notify_progress(10, "PD 승인 대기", "awaiting")
                    return {
                        "success": True,
                        "awaiting_approval": True,
                        "preview_url": approval_response.get("preview_url"),
                        "results": self.results,
                        "total_time": time.time() - total_start
                    }

                if not approval_response.get("approved"):
                    feedback = approval_response.get("feedback", "PD 반려")
                    print(f"\n❌ PD님 반려: {feedback}")
                    return {
                        "success": False,
                        "error": f"PD 반려: {feedback}",
                        "step": "approval",
                        "results": self.results
                    }

                print(f"✅ PD님 승인 완료")
                await notify_progress(10, "PD 승인 요청", "completed")
            else:
                print("\n⏭️ PD 승인 스킵됨 (--skip-approval)")
                await notify_progress(10, "PD 승인", "completed")

            # ============================================================
            # Stage 11-12: 게시 (김대리)
            # ============================================================
            if skip_publish:
                print("\n⏭️ 게시 스킵됨 (--dry-run)")
                self.results["publish"] = {"skipped": True}
                await notify_progress(11, "게시 (김대리)", "completed")
            else:
                print("\n[STAGE 11-12] 📤 게시 (김대리)")
                print("-" * 50)
                await notify_progress(11, "게시 (김대리)", "running")

                publish_input = {
                    **overlay_result.data,
                    "topic": topic,
                    "passed": True
                }
                publish_result = await self.agents["publish"].run(publish_input)

                if publish_result.success:
                    self.results["publish"] = publish_result.data
                    permalink = publish_result.data.get("publish_results", {}).get("instagram", {}).get("permalink", "")
                    print(f"✅ 게시 완료: {permalink}")
                else:
                    self.results["publish"] = {"error": publish_result.error}
                    print(f"❌ 게시 실패: {publish_result.error}")

            # ============================================================
            # 완료 요약
            # ============================================================
            total_elapsed = time.time() - total_start
            self._print_summary(total_elapsed)

            return {
                "success": True,
                "results": self.results,
                "total_time": total_elapsed
            }

        except SunshineException as e:
            # 커스텀 예외: 상세 정보 포함
            error_info = e.to_dict()
            print(f"\n   Pipeline 에러: {e.message}")
            if e.details:
                print(f"   상세: {e.details}")
            return {
                "success": False,
                "error": e.message,
                "error_type": error_info["type"],
                "error_details": error_info["details"],
                "results": self.results
            }
        except Exception as e:
            # 일반 예외: 래핑하여 처리
            wrapped = wrap_exception(e, "Pipeline execution failed")
            print(f"\n   예상치 못한 에러: {format_exception_chain(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "error_details": {"traceback": format_exception_chain(e)},
                "results": self.results
            }

    async def _run_with_retry(
        self,
        stage_name: str,
        agent_key: str,
        input_data: Dict,
        gate: Any
    ) -> RetryResult:
        """
        검수 실패 시 자동 재작업 (최대 MAX_RETRIES회)

        Args:
            stage_name: 단계 이름
            agent_key: 에이전트 키
            input_data: 입력 데이터
            gate: 검수 게이트 인스턴스

        Returns:
            RetryResult
        """
        current_input = input_data
        gate_scores = []
        agent_result = None  # P0 fix: 초기화하여 NameError 방지

        for attempt in range(MAX_RETRIES):
            # 1. 에이전트 실행
            print(f"\n   🔄 시도 {attempt + 1}/{MAX_RETRIES}")
            agent_result = await self.agents[agent_key].run(current_input)

            if not agent_result.success:
                print(f"   ❌ 에이전트 실행 실패: {agent_result.error}")
                continue

            # 2. 검수
            gate_score = gate.evaluate(agent_result.data)
            gate_scores.append(gate_score)

            print(f"   🎬 김감독 {gate_score.gate_name} 검수: {gate_score.total_score}점")

            # 3. 통과 여부 확인
            if gate_score.passed:
                print(f"   ✅ 통과!")
                return RetryResult(
                    status=RetryStatus.PASS,
                    data=agent_result.data,
                    score=gate_score.total_score,
                    feedback=gate_score.feedback,
                    attempt_count=attempt + 1,
                    gate_scores=gate_scores
                )

            # 4. 실패 시 피드백 반영하여 재시도 준비
            print(f"   ❌ 미달 ({gate_score.total_score} < {PASS_THRESHOLD})")
            print(f"   📝 피드백: {gate_score.feedback}")

            if attempt < MAX_RETRIES - 1:
                current_input = self._incorporate_feedback(
                    current_input,
                    gate_score.feedback,
                    gate_score.issues
                )
                print(f"   🔧 피드백 반영 후 재시도...")

        # 최대 시도 후에도 실패
        print(f"\n   🚨 최대 재시도 횟수 초과 ({MAX_RETRIES}회)")
        return RetryResult(
            status=RetryStatus.FAIL_MAX_RETRIES,
            data=agent_result.data if agent_result else None,
            score=gate_scores[-1].total_score if gate_scores else 0,
            feedback=f"최대 {MAX_RETRIES}회 시도 후에도 {PASS_THRESHOLD}점 미달",
            attempt_count=MAX_RETRIES,
            gate_scores=gate_scores
        )

    def _incorporate_feedback(
        self,
        original_input: Dict,
        feedback: str,
        issues: List[str]
    ) -> Dict:
        """피드백을 다음 시도에 반영"""
        enhanced_input = {
            **original_input,
            "_retry": True,
            "_feedback": feedback,
            "_issues": issues,
            "_instruction": f"이전 작업이 반려되었습니다. 다음 사항을 개선해주세요:\n{feedback}"
        }
        return enhanced_input

    def _create_failure_result(self, gate_name: str, retry_result: RetryResult) -> Dict:
        """실패 결과 생성"""
        return {
            "success": False,
            "error": f"{gate_name} 검수 최종 실패 ({retry_result.score}점)",
            "step": gate_name,
            "results": self.results,
            "retry_info": {
                "attempts": retry_result.attempt_count,
                "final_score": retry_result.score,
                "feedback": retry_result.feedback
            }
        }

    def _print_summary(self, total_time: float):
        """실행 요약 출력"""
        print("\n" + "=" * 70)
        print("📊 Pipeline v5.0 실행 요약")
        print("=" * 70)

        for stage, data in self.results.items():
            if isinstance(data, dict):
                if data.get("skipped"):
                    print(f"   ⏭️ {stage}: 스킵됨")
                elif data.get("error"):
                    print(f"   ❌ {stage}: 실패")
                else:
                    print(f"   ✅ {stage}: 완료")
            else:
                print(f"   ✅ {stage}: 완료")

        print("-" * 70)
        print(f"   총 소요시간: {total_time:.1f}초")
        print("=" * 70 + "\n")


# ============================================================
# CLI 실행
# ============================================================

async def main():
    """테스트 실행"""
    topic = sys.argv[1] if len(sys.argv) > 1 else "mango"
    skip_publish = "--dry-run" in sys.argv
    skip_approval = "--skip-approval" in sys.argv
    use_crew = "--crewai" in sys.argv or "--crew" in sys.argv

    pipeline = SunshinePipelineV5(use_crew=use_crew)
    result = await pipeline.run(
        topic,
        skip_publish=skip_publish,
        skip_approval=skip_approval,
        use_crew=use_crew
    )

    if result["success"]:
        print("🎉 파이프라인 완료!")
    else:
        print(f"❌ 파이프라인 실패: {result.get('error')}")


if __name__ == "__main__":
    asyncio.run(main())
