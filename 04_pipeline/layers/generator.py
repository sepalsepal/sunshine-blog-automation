#!/usr/bin/env python3
"""
generator.py - Layer 1: 콘텐츠 생성 계층
WO-LIGHTWEIGHT-SEPARATION + WO-STRATEGY-MATRIX

책임:
- 캡션 생성
- 이미지 생성
- 템플릿 적용
- 전략 기반 콘텐츠 분기 (WO-STRATEGY-MATRIX)

제한:
- Validator 접근 불가
- Executor 접근 불가
- override 권한 없음
- Validation 결과 수정 불가
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List, Tuple

import sys
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.interfaces.layer_contract import (
    GeneratedContent,
    ContentStatus,
    LayerAccessControl,
    PermissionDeniedError,
)


# =============================================================================
# Strategic Errors
# =============================================================================

class IntentSafetyViolationError(Exception):
    """Safety × Intent 규칙 위반"""
    pass


class TemplateNotFoundError(Exception):
    """템플릿 파일 없음"""
    pass


class Generator:
    """
    Layer 1: 콘텐츠 생성 전담

    Validator, Executor 직접 접근 불가
    override 권한 없음
    """

    LAYER_NAME = "generator"

    def __init__(self):
        self.food_data_path = PROJECT_ROOT / "config" / "food_data.json"
        self.templates_path = PROJECT_ROOT / "config" / "templates"
        self._food_data = None

    @property
    def food_data(self) -> Dict:
        """food_data.json 로드 (캐싱)"""
        if self._food_data is None:
            if self.food_data_path.exists():
                with open(self.food_data_path, "r", encoding="utf-8") as f:
                    self._food_data = json.load(f)
            else:
                self._food_data = {}
        return self._food_data

    def generate_caption(
        self,
        food_id: int,
        platform: str = "blog"
    ) -> GeneratedContent:
        """
        캡션 생성

        Args:
            food_id: 음식 ID
            platform: blog / insta / threads

        Returns:
            GeneratedContent 객체
        """
        # 권한 확인
        LayerAccessControl.check_permission(self.LAYER_NAME, "generate_caption")

        # 음식 데이터 로드
        food_info = self.food_data.get(str(food_id), {})
        food_name = food_info.get("name", f"Unknown#{food_id}")
        safety = food_info.get("safety", "SAFE").upper()

        # 캡션 생성 로직 (실제 구현은 기존 코드 활용)
        caption = self._build_caption(food_id, food_info, platform)

        return GeneratedContent(
            layer=self.LAYER_NAME,
            food_id=food_id,
            food_name=food_name,
            content_type="caption",
            content=caption,
            safety=safety,
            generated_at=datetime.now().isoformat(),
            status=ContentStatus.GENERATED,
            metadata={
                "platform": platform,
                "version": "v3.1"
            }
        )

    def generate_image(
        self,
        food_id: int,
        image_type: str = "cover"
    ) -> GeneratedContent:
        """
        이미지 생성 (메타데이터)

        Args:
            food_id: 음식 ID
            image_type: cover / infographic / photo

        Returns:
            GeneratedContent 객체
        """
        # 권한 확인
        LayerAccessControl.check_permission(self.LAYER_NAME, "generate_image")

        food_info = self.food_data.get(str(food_id), {})
        food_name = food_info.get("name", f"Unknown#{food_id}")
        safety = food_info.get("safety", "SAFE").upper()

        return GeneratedContent(
            layer=self.LAYER_NAME,
            food_id=food_id,
            food_name=food_name,
            content_type="image",
            content=f"[Image placeholder: {image_type} for {food_name}]",
            safety=safety,
            generated_at=datetime.now().isoformat(),
            status=ContentStatus.GENERATED,
            metadata={
                "image_type": image_type,
                "resolution": "1080x1080"
            }
        )

    def apply_template(
        self,
        food_id: int,
        template_name: str
    ) -> GeneratedContent:
        """
        템플릿 적용

        Args:
            food_id: 음식 ID
            template_name: 템플릿 이름

        Returns:
            GeneratedContent 객체
        """
        # 권한 확인
        LayerAccessControl.check_permission(self.LAYER_NAME, "apply_template")

        food_info = self.food_data.get(str(food_id), {})
        food_name = food_info.get("name", f"Unknown#{food_id}")
        safety = food_info.get("safety", "SAFE").upper()

        # 템플릿 로드
        template_file = self.templates_path / f"{template_name}.json"
        template_content = ""
        if template_file.exists():
            with open(template_file, "r", encoding="utf-8") as f:
                template_data = json.load(f)
                template_content = json.dumps(template_data, ensure_ascii=False)

        return GeneratedContent(
            layer=self.LAYER_NAME,
            food_id=food_id,
            food_name=food_name,
            content_type="template",
            content=template_content,
            safety=safety,
            generated_at=datetime.now().isoformat(),
            status=ContentStatus.GENERATED,
            metadata={
                "template_name": template_name
            }
        )

    def _build_caption(
        self,
        food_id: int,
        food_info: Dict,
        platform: str
    ) -> str:
        """
        캡션 빌드 로직 (내부 메서드)
        실제 구현은 기존 캡션 생성 로직 활용
        """
        food_name = food_info.get("name", "음식")
        safety = food_info.get("safety", "SAFE").upper()

        # 간단한 플레이스홀더 캡션
        if platform == "blog":
            return f"[블로그 캡션] {food_name} - Safety: {safety}"
        elif platform == "insta":
            return f"[인스타 캡션] {food_name} - Safety: {safety}"
        elif platform == "threads":
            return f"[쓰레드 캡션] {food_name} - Safety: {safety}"
        else:
            return f"[캡션] {food_name}"

    # =========================================================================
    # 금지 메서드 (계층 침범 방지)
    # =========================================================================

    def _blocked_validator_access(self):
        """Validator 접근 시도 시 차단"""
        raise PermissionDeniedError(
            "Generator는 Validator 접근 불가 (계층 분리 원칙)"
        )

    def _blocked_executor_access(self):
        """Executor 접근 시도 시 차단"""
        raise PermissionDeniedError(
            "Generator는 Executor 접근 불가 (계층 분리 원칙)"
        )

    def _blocked_override(self):
        """override 시도 시 차단"""
        raise PermissionDeniedError(
            "Generator는 override 권한 없음 (계층 분리 원칙)"
        )

    def _blocked_modify_validation(self):
        """Validation 결과 수정 시도 시 차단"""
        raise PermissionDeniedError(
            "Generator는 Validation 결과 수정 불가 (계층 분리 원칙)"
        )

    # 금지 작업 래퍼 (테스트용)
    def validate(self, *args, **kwargs):
        """금지: validate"""
        LayerAccessControl.check_permission(self.LAYER_NAME, "validate")

    def override(self, *args, **kwargs):
        """금지: override"""
        LayerAccessControl.check_permission(self.LAYER_NAME, "override")

    def execute(self, *args, **kwargs):
        """금지: execute"""
        LayerAccessControl.check_permission(self.LAYER_NAME, "execute")

    def modify_validation(self, *args, **kwargs):
        """금지: modify_validation"""
        LayerAccessControl.check_permission(self.LAYER_NAME, "modify_validation")


# =============================================================================
# Strategic Generator (WO-STRATEGY-MATRIX)
# =============================================================================

class StrategicGenerator(Generator):
    """
    전략 기반 콘텐츠 생성기
    WO-STRATEGY-MATRIX: 3축 (Intent × Platform × Format) 매트릭스

    기능:
    - strategic_meta 기반 템플릿 선택
    - Safety × Intent 규칙 검증
    - 플랫폼별 최적 포맷 자동 선택
    """

    def __init__(self):
        super().__init__()
        self.strategic_path = PROJECT_ROOT / "config" / "templates" / "strategic"
        self._intent_safety_map = None
        self._platform_format_map = None
        self._matrix = None

    # =========================================================================
    # 설정 로더
    # =========================================================================

    @property
    def intent_safety_map(self) -> Dict:
        """intent_safety_map.json 로드"""
        if self._intent_safety_map is None:
            path = self.strategic_path / "intent_safety_map.json"
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    self._intent_safety_map = json.load(f)
            else:
                self._intent_safety_map = {}
        return self._intent_safety_map

    @property
    def platform_format_map(self) -> Dict:
        """platform_format_map.json 로드"""
        if self._platform_format_map is None:
            path = self.strategic_path / "platform_format_map.json"
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    self._platform_format_map = json.load(f)
            else:
                self._platform_format_map = {}
        return self._platform_format_map

    @property
    def matrix(self) -> Dict:
        """matrix.json 로드"""
        if self._matrix is None:
            path = self.strategic_path / "matrix.json"
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    self._matrix = json.load(f)
            else:
                self._matrix = {}
        return self._matrix

    # =========================================================================
    # 전략 기반 생성
    # =========================================================================

    def generate(
        self,
        food_id: int,
        platform: str,
        strategic_meta: Optional[Dict] = None
    ) -> GeneratedContent:
        """
        전략 기반 콘텐츠 생성

        Args:
            food_id: 음식 ID
            platform: blog / insta / thread
            strategic_meta: 전략 메타데이터 (없으면 자동 생성)

        Returns:
            GeneratedContent 객체
        """
        # 권한 확인
        LayerAccessControl.check_permission(self.LAYER_NAME, "generate")

        # 음식 데이터 로드
        food_info = self.food_data.get(str(food_id), {})
        food_name = food_info.get("name", f"Unknown#{food_id}")
        safety = food_info.get("safety", "SAFE").upper()

        # strategic_meta 생성 또는 로드
        if strategic_meta is None:
            strategic_meta = self._build_default_strategic_meta(safety)

        # Safety × Intent 검증
        self._validate_intent_safety(safety, strategic_meta.get("intent", "AUTHORITY"))

        # 플랫폼별 템플릿 선택
        template_id, template_data = self._select_template(
            platform=platform.upper(),
            intent=strategic_meta.get("intent", "AUTHORITY"),
            format_type=strategic_meta.get("format")
        )

        # 콘텐츠 렌더링
        content = self._render_content(
            food_id=food_id,
            food_info=food_info,
            platform=platform,
            template_data=template_data,
            strategic_meta=strategic_meta
        )

        return GeneratedContent(
            layer=self.LAYER_NAME,
            food_id=food_id,
            food_name=food_name,
            content_type="caption",
            content=content,
            safety=safety,
            generated_at=datetime.now().isoformat(),
            status=ContentStatus.GENERATED,
            metadata={
                "platform": platform,
                "template_id": template_id,
                "intent": strategic_meta.get("intent"),
                "format": template_data.get("_meta", {}).get("format"),
                "version": "v4.0-strategic"
            }
        )

    # =========================================================================
    # 내부 메서드
    # =========================================================================

    def _build_default_strategic_meta(self, safety: str) -> Dict:
        """기본 strategic_meta 생성"""
        rules = self.intent_safety_map.get("safety_intent_rules", {})
        safety_rules = rules.get(safety, {})

        default_intent = safety_rules.get("default_intent", "AUTHORITY")
        emotion = self.intent_safety_map.get("emotion_mapping", {}).get(
            safety, {}
        ).get(default_intent, "trust")
        risk_level = self.intent_safety_map.get("risk_level_mapping", {}).get(
            safety, "low"
        )

        return {
            "intent": default_intent,
            "primary_goal": "save" if safety == "FORBIDDEN" else "dwell_time",
            "emotion_axis": emotion,
            "risk_level": risk_level,
            "experiment_flag": False
        }

    def _validate_intent_safety(self, safety: str, intent: str) -> None:
        """Safety × Intent 규칙 검증"""
        rules = self.intent_safety_map.get("safety_intent_rules", {})
        safety_rules = rules.get(safety, {})

        forbidden_intents = safety_rules.get("forbidden_intents", [])

        if intent in forbidden_intents:
            raise IntentSafetyViolationError(
                f"Safety={safety}에서 Intent={intent} 사용 불가. "
                f"허용: {safety_rules.get('allowed_intents', [])}"
            )

        # 제한적 Intent 체크 (승인 필요)
        restricted = safety_rules.get("restricted_intents", {})
        if intent in restricted:
            # 현재는 경고만 (실제 승인 로직은 별도 구현)
            pass

    def _select_template(
        self,
        platform: str,
        intent: str,
        format_type: Optional[str] = None
    ) -> Tuple[str, Dict]:
        """플랫폼 × Intent × Format 기반 템플릿 선택"""
        # format_type이 없으면 추천 포맷 사용
        if format_type is None:
            recommendation = self.platform_format_map.get(
                "intent_format_recommendation", {}
            )
            format_type = recommendation.get(intent, {}).get(platform, "DATA")

        # 템플릿 ID 생성
        template_id = f"{platform}_{intent}_{format_type}_v1"

        # 템플릿 파일 로드
        platform_lower = platform.lower()
        template_path = (
            PROJECT_ROOT / "config" / "templates" / platform_lower /
            f"{template_id}.json"
        )

        if not template_path.exists():
            # 폴백: 기본 템플릿
            fallback_templates = {
                "BLOG": "BLOG_AUTHORITY_DATA_v1",
                "INSTA": "INSTA_TRUST_WARNING_v1",
                "THREAD": "THREAD_TRUST_WARNING_v1"
            }
            template_id = fallback_templates.get(platform, template_id)
            template_path = (
                PROJECT_ROOT / "config" / "templates" / platform_lower /
                f"{template_id}.json"
            )

        if template_path.exists():
            with open(template_path, "r", encoding="utf-8") as f:
                template_data = json.load(f)
        else:
            template_data = {"_meta": {"template_id": template_id}}

        return template_id, template_data

    def _render_content(
        self,
        food_id: int,
        food_info: Dict,
        platform: str,
        template_data: Dict,
        strategic_meta: Dict
    ) -> str:
        """템플릿 기반 콘텐츠 렌더링"""
        food_name = food_info.get("name", "음식")
        safety = food_info.get("safety", "SAFE").upper()
        intent = strategic_meta.get("intent", "AUTHORITY")
        template_format = template_data.get("_meta", {}).get("format", "DATA")

        # 플랫폼별 렌더링
        if platform.upper() == "BLOG":
            return self._render_blog(
                food_name, safety, intent, template_format, template_data
            )
        elif platform.upper() == "INSTA":
            return self._render_insta(
                food_name, safety, intent, template_format, template_data
            )
        elif platform.upper() == "THREAD":
            return self._render_thread(
                food_name, safety, intent, template_format, template_data
            )
        else:
            return f"[{platform}] {food_name} - {intent}/{template_format}"

    def _render_blog(
        self,
        food_name: str,
        safety: str,
        intent: str,
        template_format: str,
        template_data: Dict
    ) -> str:
        """블로그 콘텐츠 렌더링"""
        structure = template_data.get("structure", {})
        sections = structure.get("sections", [])
        slide_mapping = template_data.get("slide_mapping", {})

        # 슬라이드 헤더 생성
        lines = []
        for slide_num, mapping in sorted(slide_mapping.items(), key=lambda x: int(x[0])):
            section_id = mapping.get("section", "intro")
            image_type = mapping.get("image_type", "photo")

            # 섹션 찾기
            section_label = section_id
            for sec in sections:
                if sec.get("id") == section_id:
                    section_label = sec.get("label", section_id)
                    break

            lines.append(f"[이미지 {slide_num}번: {section_label}]")

            # FORBIDDEN이고 WARNING 포맷이면 경고 톤
            if safety == "FORBIDDEN" and template_format == "WARNING":
                if section_id == "alert_header":
                    lines.append(f"{food_name}는 절대 금지예요! 정말 위험해요.")
                elif section_id == "danger_explanation":
                    lines.append("독성 성분이 있어 치명적이에요.")
                elif section_id == "symptoms":
                    lines.append("섭취 시 심각한 증상이 나타나요.")
                elif section_id == "emergency":
                    lines.append("즉시 동물병원에 가세요. 응급 상황이에요.")
                elif section_id == "prevention":
                    lines.append("절대 주지 마세요. 위험해요.")
                elif section_id == "conclusion":
                    lines.append("햇살이 엄마도 절대 주지 않아요.")
            else:
                # SAFE/CAUTION 친근한 톤
                lines.append(f"안녕하세요, 햇살이 엄마예요. {food_name}에 대해 알려드릴게요.")

            lines.append("")

        return "\n".join(lines)

    def _render_insta(
        self,
        food_name: str,
        safety: str,
        intent: str,
        template_format: str,
        template_data: Dict
    ) -> str:
        """인스타그램 콘텐츠 렌더링"""
        carousel = template_data.get("carousel", {})
        cards = carousel.get("cards", [])

        lines = []
        for card in cards:
            card_num = card.get("card_num", 1)
            card_type = card.get("type", "content")
            content = card.get("content", {})

            headline = content.get("headline", "")
            lines.append(f"[카드 {card_num}] {headline}")

            if card_type == "save_cta":
                lines.append("저장해두세요! 나중에 유용해요.")
            elif card_type == "hook" and safety == "FORBIDDEN":
                lines.append(f"{food_name} 절대 주지 마세요!")

            lines.append("")

        # 캡션 추가
        caption_template = template_data.get("caption", {})
        max_length = caption_template.get("max_length", 2200)
        lines.append(f"[캡션 - 최대 {max_length}자]")
        lines.append(f"{food_name} 관련 정보를 알려드릴게요.")

        return "\n".join(lines)

    def _render_thread(
        self,
        food_name: str,
        safety: str,
        intent: str,
        template_format: str,
        template_data: Dict
    ) -> str:
        """쓰레드 콘텐츠 렌더링"""
        post = template_data.get("post", {})
        max_chars = post.get("max_chars", 500)
        structure = post.get("structure", [])

        lines = []
        for section in structure:
            section_id = section.get("id", "content")
            template = section.get("template", "")

            if template:
                text = template.replace("{topic}", food_name)
                lines.append(text)
            elif section_id == "hook":
                if safety == "FORBIDDEN":
                    lines.append(f"🚨 {food_name} 강아지한테 절대 주지 마세요")
                else:
                    lines.append(f"{food_name} 강아지한테 줘도 될까요? 🤔")
            elif section_id == "warning":
                lines.append("정말 위험합니다. 독성 성분이 있어요.")
            elif section_id == "action":
                lines.append("더 자세한 정보는 프로필에서!")

        content = "\n".join(lines)

        # 글자수 제한
        if len(content) > max_chars:
            content = content[:max_chars-3] + "..."

        return content

    # =========================================================================
    # 유틸리티
    # =========================================================================

    def get_recommended_config(
        self,
        food_id: int,
        platform: str
    ) -> Dict:
        """음식 ID와 플랫폼에 대한 추천 설정 반환"""
        food_info = self.food_data.get(str(food_id), {})
        safety = food_info.get("safety", "SAFE").upper()

        # 기본 strategic_meta
        strategic_meta = self._build_default_strategic_meta(safety)

        # 추천 포맷
        intent = strategic_meta["intent"]
        recommendation = self.platform_format_map.get(
            "intent_format_recommendation", {}
        )
        format_type = recommendation.get(intent, {}).get(platform.upper(), "DATA")

        # 템플릿 ID
        template_id = f"{platform.upper()}_{intent}_{format_type}_v1"

        return {
            "food_id": food_id,
            "platform": platform,
            "safety": safety,
            "strategic_meta": strategic_meta,
            "recommended_format": format_type,
            "template_id": template_id
        }
