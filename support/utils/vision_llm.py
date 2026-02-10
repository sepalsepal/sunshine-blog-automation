"""
Vision LLM 도구
Gemini Vision을 사용한 이미지 분석

Phase 7: VLM 자동검수 시스템 (Gemini 버전)
비용: $0 (Gemini Free Tier)
"""

import os
import base64
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

ROOT = Path(__file__).parent.parent

# 새로운 google-genai 패키지 임포트
try:
    from google import genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

# PIL 임포트
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None


class VisionLLM:
    """
    Vision LLM 도구 (Gemini 버전)

    Gemini Vision을 사용하여
    이미지 분석 및 크리에이티브 검수 수행

    Features:
    - 미적 균형 분석
    - 감성 품질 분석
    - 스토리텔링 분석
    - 다양성 분석
    - Gold Standard 비교

    비용: $0 (Gemini Free Tier - 15 RPM, 1500 RPD)
    """

    def __init__(self, api_key: str = None):
        """
        VisionLLM 초기화

        Args:
            api_key: Gemini API 키 (없으면 환경변수에서 로드)
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.client = None
        self.model_name = "gemini-2.0-flash"  # 최신 모델
        self._initialized = False

        if GEMINI_AVAILABLE and self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
                self._initialized = True
            except Exception as e:
                print(f"[VisionLLM] Gemini 초기화 실패: {e}")

    def is_available(self) -> bool:
        """VLM 사용 가능 여부"""
        return self._initialized and self.client is not None

    def _load_image(self, image_path: str) -> Optional[Any]:
        """이미지 로드"""
        if not PIL_AVAILABLE:
            return None
        try:
            return Image.open(image_path)
        except Exception as e:
            print(f"[VisionLLM] 이미지 로드 실패: {image_path} - {e}")
            return None

    def _parse_json_response(self, response_text: str) -> Dict:
        """JSON 응답 파싱"""
        text = response_text.strip()

        # JSON 블록 추출
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            parts = text.split("```")
            if len(parts) >= 2:
                text = parts[1]

        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            # JSON 파싱 실패 시 기본 구조 반환
            return {"error": "JSON 파싱 실패", "raw": response_text[:500]}

    async def analyze_image(self, image_path: str, prompt: str) -> Dict[str, Any]:
        """
        단일 이미지 분석

        Args:
            image_path: 이미지 경로
            prompt: 분석 프롬프트

        Returns:
            분석 결과 딕셔너리
        """
        if not self.is_available():
            return {"error": "VLM 미연결", "vlm_used": False}

        image = self._load_image(image_path)
        if image is None:
            return {"error": f"이미지 로드 실패: {image_path}", "vlm_used": False}

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[prompt, image]
            )
            return {
                "response": response.text,
                "vlm_used": True
            }
        except Exception as e:
            return {"error": str(e), "vlm_used": False}

    async def analyze_images(self, image_paths: List[str], prompt: str) -> Dict[str, Any]:
        """
        다중 이미지 분석

        Args:
            image_paths: 이미지 경로 리스트
            prompt: 분석 프롬프트

        Returns:
            분석 결과 딕셔너리
        """
        if not self.is_available():
            return {"error": "VLM 미연결", "vlm_used": False}

        # 이미지 로드 (최대 5장)
        images = []
        for path in image_paths[:5]:
            img = self._load_image(path)
            if img:
                images.append(img)

        if not images:
            return {"error": "이미지 로드 실패", "vlm_used": False}

        try:
            # Gemini에 이미지들과 프롬프트 전달
            contents = [prompt] + images
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents
            )
            return {
                "response": response.text,
                "vlm_used": True,
                "image_count": len(images)
            }
        except Exception as e:
            return {"error": str(e), "vlm_used": False}

    async def analyze_aesthetic(self, image_paths: List[str]) -> Dict[str, Any]:
        """
        미적 균형 분석

        평가 항목 (각 5점, 총 25점):
        1. 표지 제목 크기/위치 균형
        2. 언더라인 비율
        3. 전체적 시각적 균형
        4. 색감/톤 일관성
        5. 텍스트 가독성
        """
        if not self.is_available():
            return self._default_result("aesthetic", 15)

        prompt = """이 Instagram 캐러셀 이미지들의 미적 균형을 평가해주세요.

평가 항목 (각 5점, 총 25점):
1. visual_balance: 표지 제목 크기/위치 균형
2. underline_ratio: 언더라인과 제목 비율
3. overall_composition: 전체적 시각적 균형
4. color_consistency: 색감/톤 일관성
5. text_readability: 텍스트 가독성

JSON 형식으로만 응답:
{
    "scores": {
        "visual_balance": 4,
        "underline_ratio": 3,
        "overall_composition": 4,
        "color_consistency": 5,
        "text_readability": 4
    },
    "total": 20,
    "feedback": "전반적인 평가 코멘트",
    "strengths": ["강점1", "강점2"],
    "improvements": ["개선점1", "개선점2"]
}"""

        result = await self.analyze_images(image_paths, prompt)

        if result.get("vlm_used"):
            parsed = self._parse_json_response(result.get("response", "{}"))
            parsed["vlm_used"] = True
            return parsed
        else:
            return self._default_result("aesthetic", 15, result.get("error"))

    async def analyze_emotion(self, image_paths: List[str]) -> Dict[str, Any]:
        """
        감성 품질 분석

        평가 항목 (각 5점, 총 25점):
        1. 자연스러움 (AI 느낌 탈피)
        2. 표정 다양성
        3. 따뜻함/일상감
        4. 보호자-반려견 관계
        5. 전체적 감성
        """
        if not self.is_available():
            return self._default_result("emotion", 15)

        prompt = """이 Instagram 캐러셀 이미지들의 감성 품질을 평가해주세요.

평가 항목 (각 5점, 총 25점):
1. authenticity: 자연스러움 (AI 또는 스톡 느낌이 아닌 진짜 반려견 사진 같은)
2. expression_variety: 강아지 표정 다양성
3. warmth: 따뜻함, 일상적인 분위기
4. relationship: 보호자-반려견 관계 표현
5. overall_emotion: 전체적 감성 품질

JSON 형식으로만 응답:
{
    "scores": {
        "authenticity": 4,
        "expression_variety": 3,
        "warmth": 4,
        "relationship": 3,
        "overall_emotion": 4
    },
    "total": 18,
    "feedback": "전반적인 평가 코멘트",
    "strengths": ["강점1", "강점2"],
    "improvements": ["개선점1", "개선점2"]
}"""

        result = await self.analyze_images(image_paths, prompt)

        if result.get("vlm_used"):
            parsed = self._parse_json_response(result.get("response", "{}"))
            parsed["vlm_used"] = True
            return parsed
        else:
            return self._default_result("emotion", 15, result.get("error"))

    async def analyze_storytelling(self, image_paths: List[str]) -> Dict[str, Any]:
        """
        스토리텔링 분석

        평가 항목 (각 5점, 총 25점):
        1. 슬라이드 간 흐름
        2. 정보 전달력
        3. 사람 등장 자연스러움
        4. 상황 다양성
        5. CTA 연결
        """
        if not self.is_available():
            return self._default_result("storytelling", 15)

        prompt = """이 Instagram 캐러셀 이미지들의 스토리텔링을 평가해주세요.

평가 항목 (각 5점, 총 25점):
1. narrative_flow: 슬라이드 간 자연스러운 흐름
2. information_delivery: 정보 전달력 (음식 정보가 잘 전달되는지)
3. human_presence: 사람(손, 조리 장면) 등장의 자연스러움
4. situation_variety: 다양한 상황/장면 연출
5. cta_connection: CTA(저장해두세요 등)가 자연스럽게 연결되는지

JSON 형식으로만 응답:
{
    "scores": {
        "narrative_flow": 4,
        "information_delivery": 4,
        "human_presence": 3,
        "situation_variety": 4,
        "cta_connection": 4
    },
    "total": 19,
    "feedback": "전반적인 평가 코멘트",
    "strengths": ["강점1", "강점2"],
    "improvements": ["개선점1", "개선점2"]
}"""

        result = await self.analyze_images(image_paths, prompt)

        if result.get("vlm_used"):
            parsed = self._parse_json_response(result.get("response", "{}"))
            parsed["vlm_used"] = True
            return parsed
        else:
            return self._default_result("storytelling", 15, result.get("error"))

    async def analyze_diversity(self, image_paths: List[str]) -> Dict[str, Any]:
        """
        다양성 분석

        평가 항목 (각 5점, 총 25점):
        1. 포즈 다양성 (앉기, 눕기, 서기, 올려다보기)
        2. 앵글 다양성 (정면, 측면, 위, 아래)
        3. 배경 다양성 (주방, 거실)
        4. 사람 등장 유무
        5. 음식 형태 다양성
        """
        if not self.is_available():
            return self._default_result("diversity", 15)

        prompt = """이 Instagram 캐러셀 이미지들의 다양성을 평가해주세요.

평가 항목 (각 5점, 총 25점):
1. pose_variety: 강아지 포즈 다양성 (앉기, 눕기, 서기, 올려다보기 등 4종 이상)
2. angle_variety: 카메라 앵글 다양성 (정면, 측면45도, 측면90도, 위에서, 블러 등 4종 이상)
3. background_variety: 배경 다양성 (주방, 거실 등 2종 이상)
4. human_appearance: 사람(손, 조리) 등장 (2장 이상)
5. food_form_variety: 음식 형태 다양성 (통째로, 썬 것, 접시 등 3종 이상)

JSON 형식으로만 응답:
{
    "scores": {
        "pose_variety": 4,
        "angle_variety": 4,
        "background_variety": 3,
        "human_appearance": 3,
        "food_form_variety": 4
    },
    "total": 18,
    "detected": {
        "poses": ["sitting", "lying", "standing", "looking_up"],
        "angles": ["front", "side_45", "top_down"],
        "backgrounds": ["kitchen", "living_room"],
        "human_shots": 2,
        "food_forms": ["whole", "sliced", "bowl"]
    },
    "feedback": "전반적인 평가 코멘트",
    "improvements": ["개선점1", "개선점2"]
}"""

        result = await self.analyze_images(image_paths, prompt)

        if result.get("vlm_used"):
            parsed = self._parse_json_response(result.get("response", "{}"))
            parsed["vlm_used"] = True
            return parsed
        else:
            return self._default_result("diversity", 15, result.get("error"))

    async def compare_with_gold_standard(
        self,
        content_images: List[str],
        gold_images: List[str]
    ) -> Dict[str, Any]:
        """
        Gold Standard(체리)와 비교

        Returns:
            similarity_score (0-100), feedback, gaps
        """
        if not self.is_available():
            return {"similarity_score": 60, "feedback": "VLM 미연결", "gaps": [], "vlm_used": False}

        if not gold_images:
            return {"similarity_score": 60, "feedback": "Gold Standard 이미지 없음", "gaps": [], "vlm_used": False}

        # 이미지 로드
        content_imgs = [self._load_image(p) for p in content_images[:3]]
        content_imgs = [img for img in content_imgs if img is not None]
        gold_imgs = [self._load_image(p) for p in gold_images[:3]]
        gold_imgs = [img for img in gold_imgs if img is not None]

        if not content_imgs or not gold_imgs:
            return {"similarity_score": 60, "feedback": "이미지 로드 실패", "gaps": [], "vlm_used": False}

        prompt = """## Gold Standard (체리 콘텐츠 - 최고 품질 기준):
(앞쪽 3장 이미지)

## 평가 대상 콘텐츠:
(뒤쪽 3장 이미지)

위 Gold Standard(체리 콘텐츠)와 비교하여 평가 대상 콘텐츠의 품질을 평가해주세요.

비교 기준:
- 포즈 다양성 유사도
- 앵글 다양성 유사도
- 감성적 품질 유사도
- 전체적 완성도

JSON 형식으로만 응답:
{
    "similarity_score": 75,
    "comparison": {
        "pose_similarity": 80,
        "angle_similarity": 70,
        "emotion_similarity": 75,
        "overall_quality": 75
    },
    "feedback": "비교 평가 코멘트",
    "gaps": ["Gold Standard 대비 부족한 점1", "부족한 점2"],
    "strengths": ["잘된 점1", "잘된 점2"]
}"""

        try:
            # Gold 이미지 먼저, 평가 대상 이미지 나중에
            contents = [prompt] + gold_imgs + content_imgs
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents
            )
            parsed = self._parse_json_response(response.text)
            parsed["vlm_used"] = True
            return parsed
        except Exception as e:
            return {"similarity_score": 60, "feedback": str(e), "gaps": ["비교 실패"], "vlm_used": False}

    def _default_result(
        self,
        category: str,
        default_score: int,
        error: str = None
    ) -> Dict[str, Any]:
        """VLM 미연결 시 기본 결과"""
        return {
            "category": category,
            "scores": {},
            "total": default_score,
            "feedback": f"VLM 미연결 - 기본값 {default_score}점",
            "error": error,
            "vlm_used": False
        }


# 하위 호환성을 위한 별칭
VisionLLMTool = VisionLLM


# 테스트
if __name__ == "__main__":
    import asyncio
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")

    async def test():
        print("=" * 60)
        print("Phase 7: Gemini Vision LLM 테스트")
        print("=" * 60)

        tool = VisionLLM()
        print(f"\nGemini VLM 사용 가능: {tool.is_available()}")

        if tool.is_available():
            # 테스트 이미지
            test_dir = ROOT / "outputs" / "watermelon_publish_final"
            images = sorted([str(f) for f in test_dir.glob("*.png")])[:5]

            if images:
                print(f"\n테스트 이미지: {len(images)}장")
                for img in images:
                    print(f"  - {Path(img).name}")

                print("\n1. 미적 균형 분석...")
                result = await tool.analyze_aesthetic(images)
                print(f"   VLM 사용: {result.get('vlm_used', False)}")
                print(f"   총점: {result.get('total', 0)}/25")
                if result.get('feedback'):
                    print(f"   피드백: {result.get('feedback')[:100]}...")

                print("\n2. 감성 품질 분석...")
                result = await tool.analyze_emotion(images)
                print(f"   VLM 사용: {result.get('vlm_used', False)}")
                print(f"   총점: {result.get('total', 0)}/25")

                print("\n3. 다양성 분석...")
                result = await tool.analyze_diversity(images)
                print(f"   VLM 사용: {result.get('vlm_used', False)}")
                print(f"   총점: {result.get('total', 0)}/25")

                print("\n" + "=" * 60)
                print("테스트 완료!")
            else:
                print("테스트 이미지 없음")
        else:
            print("\nGemini API 키가 설정되지 않았습니다.")
            print("GEMINI_API_KEY 환경변수를 설정하세요.")

    asyncio.run(test())
