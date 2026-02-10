"""
MultiPlatformAgent - 멀티 플랫폼 포스팅 에이전트
Project Sunshine Agent System
이름: 박멀티

역할:
- 여러 SNS 플랫폼 동시 포스팅
- 플랫폼별 콘텐츠 최적화
- 크로스 포스팅 관리
- 플랫폼별 형식 변환
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from enum import Enum

from .base import BaseAgent, AgentResult


class Platform(Enum):
    """지원 플랫폼"""
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    TWITTER = "twitter"
    THREADS = "threads"
    PINTEREST = "pinterest"
    TIKTOK = "tiktok"


class MultiPlatformAgent(BaseAgent):
    """
    멀티 플랫폼 포스팅 전문 에이전트 (박멀티)

    기능:
    1. 여러 플랫폼 동시 포스팅
    2. 플랫폼별 콘텐츠 형식 최적화
    3. 크로스 포스팅 관리
    4. 플랫폼별 API 연동
    """

    # 플랫폼별 제한사항
    PLATFORM_LIMITS = {
        Platform.INSTAGRAM: {
            "max_caption_length": 2200,
            "max_hashtags": 30,
            "max_images": 10,
            "image_ratio": ["1:1", "4:5", "1.91:1"],
            "max_video_length": 60,  # 초
        },
        Platform.FACEBOOK: {
            "max_caption_length": 63206,
            "max_hashtags": 30,
            "max_images": 10,
            "image_ratio": ["any"],
        },
        Platform.TWITTER: {
            "max_caption_length": 280,
            "max_hashtags": 10,
            "max_images": 4,
            "image_ratio": ["16:9", "1:1"],
        },
        Platform.THREADS: {
            "max_caption_length": 500,
            "max_hashtags": 10,
            "max_images": 10,
            "image_ratio": ["any"],
        },
        Platform.PINTEREST: {
            "max_caption_length": 500,
            "max_hashtags": 20,
            "max_images": 1,
            "image_ratio": ["2:3", "1:1"],
        },
        Platform.TIKTOK: {
            "max_caption_length": 2200,
            "max_hashtags": 100,
            "max_images": 35,
            "video_required": True,
        },
    }

    def __init__(self, config_path: Optional[str] = None):
        super().__init__(config_path)
        self._history_file = Path(__file__).parent.parent / "logs" / "multiplatform_history.json"
        self._credentials = {}
        self._load_credentials()

    @property
    def name(self) -> str:
        return "MultiPlatformAgent"

    def _load_credentials(self) -> None:
        """플랫폼별 인증 정보 로드"""
        creds_file = Path(__file__).parent.parent / "config" / "platform_credentials.json"
        if creds_file.exists():
            try:
                with open(creds_file, 'r', encoding='utf-8') as f:
                    self._credentials = json.load(f)
            except Exception as e:
                self.log(f"인증 정보 로드 실패: {e}", level="warning")

    def adapt_content_for_platform(
        self,
        platform: Platform,
        caption: str,
        hashtags: List[str],
        images: List[str]
    ) -> Dict:
        """
        플랫폼에 맞게 콘텐츠 최적화

        Args:
            platform: 대상 플랫폼
            caption: 원본 캡션
            hashtags: 해시태그 목록
            images: 이미지 경로 목록

        Returns:
            플랫폼 최적화된 콘텐츠
        """
        limits = self.PLATFORM_LIMITS.get(platform, {})

        # 캡션 길이 조정
        max_caption = limits.get("max_caption_length", 2200)
        adapted_caption = caption[:max_caption-3] + "..." if len(caption) > max_caption else caption

        # 해시태그 수 조정
        max_hashtags = limits.get("max_hashtags", 30)
        adapted_hashtags = hashtags[:max_hashtags]

        # 이미지 수 조정
        max_images = limits.get("max_images", 10)
        adapted_images = images[:max_images]

        # 플랫폼별 특수 처리
        if platform == Platform.TWITTER:
            # 트위터는 해시태그를 캡션에 포함
            hashtag_str = " ".join([f"#{tag}" for tag in adapted_hashtags[:5]])
            remaining_length = max_caption - len(hashtag_str) - 2
            adapted_caption = adapted_caption[:remaining_length] + "\n\n" + hashtag_str
            adapted_hashtags = []  # 캡션에 포함되었으므로 별도 해시태그 없음

        elif platform == Platform.PINTEREST:
            # 핀터레스트는 첫 이미지만 사용
            adapted_images = adapted_images[:1]

        return {
            "platform": platform.value,
            "caption": adapted_caption,
            "hashtags": adapted_hashtags,
            "images": adapted_images,
            "optimized": True,
            "limits_applied": {
                "caption_truncated": len(caption) > max_caption,
                "hashtags_truncated": len(hashtags) > max_hashtags,
                "images_truncated": len(images) > max_images
            }
        }

    def validate_platform_requirements(
        self,
        platform: Platform,
        content: Dict
    ) -> Dict:
        """
        플랫폼 요구사항 검증

        Args:
            platform: 대상 플랫폼
            content: 콘텐츠 데이터

        Returns:
            검증 결과
        """
        limits = self.PLATFORM_LIMITS.get(platform, {})
        issues = []
        warnings = []

        # 캡션 길이 검증
        caption = content.get("caption", "")
        max_caption = limits.get("max_caption_length", 2200)
        if len(caption) > max_caption:
            issues.append(f"캡션이 너무 깁니다 ({len(caption)}/{max_caption})")

        # 해시태그 수 검증
        hashtags = content.get("hashtags", [])
        max_hashtags = limits.get("max_hashtags", 30)
        if len(hashtags) > max_hashtags:
            warnings.append(f"해시태그가 많습니다 ({len(hashtags)}/{max_hashtags})")

        # 이미지 수 검증
        images = content.get("images", [])
        max_images = limits.get("max_images", 10)
        if len(images) > max_images:
            issues.append(f"이미지가 너무 많습니다 ({len(images)}/{max_images})")

        # 비디오 필수 검증 (TikTok)
        if limits.get("video_required") and not content.get("video"):
            issues.append("비디오가 필요합니다")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "platform": platform.value
        }

    async def post_to_platform(
        self,
        platform: Platform,
        content: Dict
    ) -> Dict:
        """
        특정 플랫폼에 포스팅 (실제 API 호출)

        Args:
            platform: 대상 플랫폼
            content: 포스팅할 콘텐츠

        Returns:
            포스팅 결과
        """
        # 플랫폼 인증 확인
        if platform.value not in self._credentials:
            return {
                "success": False,
                "platform": platform.value,
                "error": f"{platform.value} 인증 정보가 없습니다",
                "needs_setup": True
            }

        # 플랫폼별 포스팅 로직
        self.log(f"{platform.value}에 포스팅 중...")

        try:
            if platform == Platform.INSTAGRAM:
                result = await self._post_to_instagram(content)
            elif platform == Platform.FACEBOOK:
                result = await self._post_to_facebook(content)
            elif platform == Platform.TWITTER:
                result = await self._post_to_twitter(content)
            elif platform == Platform.THREADS:
                result = await self._post_to_threads(content)
            elif platform == Platform.PINTEREST:
                result = await self._post_to_pinterest(content)
            elif platform == Platform.TIKTOK:
                result = await self._post_to_tiktok(content)
            else:
                result = {"success": False, "error": "지원하지 않는 플랫폼"}

            result["platform"] = platform.value
            result["posted_at"] = datetime.now().isoformat()
            return result

        except Exception as e:
            return {
                "success": False,
                "platform": platform.value,
                "error": str(e)
            }

    async def _post_to_instagram(self, content: Dict) -> Dict:
        """Instagram 포스팅 (Publisher 에이전트 연동)"""
        # 실제 구현 시 PublisherAgent 호출
        return {
            "success": True,
            "message": "Instagram 포스팅 준비 완료",
            "use_publisher_agent": True
        }

    async def _post_to_facebook(self, content: Dict) -> Dict:
        """Facebook 포스팅"""
        # Facebook Graph API 구현 예정
        return {
            "success": False,
            "message": "Facebook API 연동 준비 중",
            "status": "not_implemented"
        }

    async def _post_to_twitter(self, content: Dict) -> Dict:
        """Twitter/X 포스팅"""
        # Twitter API v2 구현 예정
        return {
            "success": False,
            "message": "Twitter API 연동 준비 중",
            "status": "not_implemented"
        }

    async def _post_to_threads(self, content: Dict) -> Dict:
        """Threads 포스팅"""
        # Threads API 구현 예정
        return {
            "success": False,
            "message": "Threads API 연동 준비 중",
            "status": "not_implemented"
        }

    async def _post_to_pinterest(self, content: Dict) -> Dict:
        """Pinterest 포스팅"""
        # Pinterest API 구현 예정
        return {
            "success": False,
            "message": "Pinterest API 연동 준비 중",
            "status": "not_implemented"
        }

    async def _post_to_tiktok(self, content: Dict) -> Dict:
        """TikTok 포스팅"""
        # TikTok API 구현 예정
        return {
            "success": False,
            "message": "TikTok API 연동 준비 중",
            "status": "not_implemented"
        }

    async def cross_post(
        self,
        content: Dict,
        platforms: List[Platform]
    ) -> Dict:
        """
        여러 플랫폼에 동시 포스팅

        Args:
            content: 원본 콘텐츠
            platforms: 포스팅할 플랫폼 목록

        Returns:
            플랫폼별 포스팅 결과
        """
        results = {}
        tasks = []

        for platform in platforms:
            # 플랫폼별 콘텐츠 최적화
            adapted = self.adapt_content_for_platform(
                platform=platform,
                caption=content.get("caption", ""),
                hashtags=content.get("hashtags", []),
                images=content.get("images", [])
            )

            # 비동기 포스팅 태스크 생성
            task = self.post_to_platform(platform, adapted)
            tasks.append((platform, task))

        # 병렬 실행
        for platform, task in tasks:
            result = await task
            results[platform.value] = result

        # 결과 요약
        success_count = sum(1 for r in results.values() if r.get("success"))
        total_count = len(results)

        return {
            "results": results,
            "summary": {
                "total": total_count,
                "success": success_count,
                "failed": total_count - success_count
            }
        }

    def get_platform_status(self) -> Dict:
        """모든 플랫폼 연결 상태 확인"""
        status = {}
        for platform in Platform:
            status[platform.value] = {
                "connected": platform.value in self._credentials,
                "limits": self.PLATFORM_LIMITS.get(platform, {})
            }
        return status

    async def execute(self, input_data: Any) -> AgentResult:
        """
        멀티 플랫폼 작업 실행

        input_data 형식:
        {
            "action": "cross_post" | "adapt" | "validate" | "status",
            "platforms": ["instagram", "facebook"],
            "content": {
                "caption": "...",
                "hashtags": [...],
                "images": [...]
            }
        }
        """
        try:
            action = input_data.get("action", "status")

            if action == "cross_post":
                content = input_data.get("content", {})
                platform_names = input_data.get("platforms", ["instagram"])
                platforms = [Platform(p) for p in platform_names if p in [p.value for p in Platform]]

                if not platforms:
                    return AgentResult(
                        success=False,
                        error="유효한 플랫폼이 없습니다"
                    )

                result = await self.cross_post(content, platforms)

                return AgentResult(
                    success=result["summary"]["success"] > 0,
                    data=result,
                    metadata={"action": action, "platforms": [p.value for p in platforms]}
                )

            elif action == "adapt":
                platform_name = input_data.get("platform", "instagram")
                try:
                    platform = Platform(platform_name)
                except ValueError:
                    return AgentResult(
                        success=False,
                        error=f"알 수 없는 플랫폼: {platform_name}"
                    )

                content = input_data.get("content", {})
                adapted = self.adapt_content_for_platform(
                    platform=platform,
                    caption=content.get("caption", ""),
                    hashtags=content.get("hashtags", []),
                    images=content.get("images", [])
                )

                return AgentResult(
                    success=True,
                    data=adapted,
                    metadata={"action": action, "platform": platform_name}
                )

            elif action == "validate":
                platform_name = input_data.get("platform", "instagram")
                try:
                    platform = Platform(platform_name)
                except ValueError:
                    return AgentResult(
                        success=False,
                        error=f"알 수 없는 플랫폼: {platform_name}"
                    )

                content = input_data.get("content", {})
                validation = self.validate_platform_requirements(platform, content)

                return AgentResult(
                    success=validation["valid"],
                    data=validation,
                    metadata={"action": action, "platform": platform_name}
                )

            elif action == "status":
                return AgentResult(
                    success=True,
                    data=self.get_platform_status(),
                    metadata={"action": action}
                )

            else:
                return AgentResult(
                    success=False,
                    error=f"알 수 없는 액션: {action}"
                )

        except Exception as e:
            self.log(f"멀티플랫폼 오류: {e}", level="error")
            return AgentResult(
                success=False,
                error=str(e)
            )


# 테스트용 코드
if __name__ == "__main__":
    async def test():
        agent = MultiPlatformAgent()

        # 플랫폼 상태 확인
        result = await agent.run({"action": "status"})
        print("플랫폼 상태:", result)

        # 콘텐츠 적응 테스트
        result = await agent.run({
            "action": "adapt",
            "platform": "twitter",
            "content": {
                "caption": "강아지가 먹어도 되는 과일! 바나나는 칼륨이 풍부하고 소화가 잘 돼서 강아지에게 좋은 간식이에요.",
                "hashtags": ["강아지", "반려견", "바나나", "강아지간식", "펫푸드"],
                "images": ["image1.jpg", "image2.jpg"]
            }
        })
        print("Twitter 적응:", result)

    asyncio.run(test())
