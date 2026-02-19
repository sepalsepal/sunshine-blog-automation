"""
SunFlow Multi-Platform Manager
- Instagram, X (Twitter), Threads 통합 관리
- 콘텐츠 자동 변환 및 게시
- 플랫폼별 최적화
"""

import os
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from abc import ABC, abstractmethod

# 프로젝트 루트
PROJECT_ROOT = Path(__file__).parent.parent.parent


class Platform(Enum):
    """지원 플랫폼"""
    INSTAGRAM = "instagram"
    X = "x"  # Twitter
    THREADS = "threads"
    YOUTUBE = "youtube"


@dataclass
class PlatformContent:
    """플랫폼별 콘텐츠"""
    platform: Platform
    text: str
    images: List[str]
    hashtags: List[str]
    link: Optional[str] = None
    metadata: Dict = None


@dataclass
class CrossPostResult:
    """크로스 포스팅 결과"""
    platform: Platform
    success: bool
    post_id: Optional[str]
    post_url: Optional[str]
    error: Optional[str]
    timestamp: str


class PlatformAdapter(ABC):
    """플랫폼 어댑터 추상 클래스"""

    @abstractmethod
    async def post(self, content: PlatformContent) -> CrossPostResult:
        """콘텐츠 게시"""
        pass

    @abstractmethod
    def validate(self, content: PlatformContent) -> Tuple[bool, str]:
        """콘텐츠 유효성 검사"""
        pass


class XAdapter(PlatformAdapter):
    """X (Twitter) 어댑터"""

    # X 제한사항
    MAX_TEXT_LENGTH = 280
    MAX_IMAGES = 4

    def __init__(self):
        self.api_key = os.environ.get("X_API_KEY")
        self.api_secret = os.environ.get("X_API_SECRET")
        self.access_token = os.environ.get("X_ACCESS_TOKEN")
        self.access_secret = os.environ.get("X_ACCESS_SECRET")

    def validate(self, content: PlatformContent) -> Tuple[bool, str]:
        """X 콘텐츠 유효성 검사"""
        # 텍스트 길이 체크
        full_text = content.text
        if content.hashtags:
            full_text += " " + " ".join(f"#{tag}" for tag in content.hashtags[:3])

        if len(full_text) > self.MAX_TEXT_LENGTH:
            return False, f"텍스트가 너무 김 ({len(full_text)}/{self.MAX_TEXT_LENGTH})"

        # 이미지 개수 체크
        if len(content.images) > self.MAX_IMAGES:
            return False, f"이미지가 너무 많음 ({len(content.images)}/{self.MAX_IMAGES})"

        return True, "OK"

    async def post(self, content: PlatformContent) -> CrossPostResult:
        """X에 게시"""
        # 유효성 검사
        valid, msg = self.validate(content)
        if not valid:
            return CrossPostResult(
                platform=Platform.X,
                success=False,
                post_id=None,
                post_url=None,
                error=msg,
                timestamp=datetime.now().isoformat()
            )

        # API 키 확인
        if not all([self.api_key, self.api_secret, self.access_token, self.access_secret]):
            return CrossPostResult(
                platform=Platform.X,
                success=False,
                post_id=None,
                post_url=None,
                error="X API 키가 설정되지 않음",
                timestamp=datetime.now().isoformat()
            )

        # TODO: 실제 X API 호출 구현
        # tweepy 또는 requests로 구현

        # 임시 성공 응답 (API 연동 전)
        return CrossPostResult(
            platform=Platform.X,
            success=True,
            post_id="mock_x_post_id",
            post_url="https://x.com/sunshinedogfood/status/mock",
            error=None,
            timestamp=datetime.now().isoformat()
        )


class ThreadsAdapter(PlatformAdapter):
    """Threads 어댑터"""

    # Threads 제한사항
    MAX_TEXT_LENGTH = 500
    MAX_IMAGES = 10

    def __init__(self):
        # Threads는 Instagram과 동일 계정 사용
        self.access_token = os.environ.get("INSTAGRAM_ACCESS_TOKEN")

    def validate(self, content: PlatformContent) -> Tuple[bool, str]:
        """Threads 콘텐츠 유효성 검사"""
        if len(content.text) > self.MAX_TEXT_LENGTH:
            return False, f"텍스트가 너무 김 ({len(content.text)}/{self.MAX_TEXT_LENGTH})"

        if len(content.images) > self.MAX_IMAGES:
            return False, f"이미지가 너무 많음 ({len(content.images)}/{self.MAX_IMAGES})"

        return True, "OK"

    async def post(self, content: PlatformContent) -> CrossPostResult:
        """Threads에 게시"""
        valid, msg = self.validate(content)
        if not valid:
            return CrossPostResult(
                platform=Platform.THREADS,
                success=False,
                post_id=None,
                post_url=None,
                error=msg,
                timestamp=datetime.now().isoformat()
            )

        if not self.access_token:
            return CrossPostResult(
                platform=Platform.THREADS,
                success=False,
                post_id=None,
                post_url=None,
                error="Threads API 토큰이 설정되지 않음",
                timestamp=datetime.now().isoformat()
            )

        # TODO: 실제 Threads API 호출 구현
        # Meta Threads API 사용

        return CrossPostResult(
            platform=Platform.THREADS,
            success=True,
            post_id="mock_threads_post_id",
            post_url="https://threads.net/@sunshinedogfood/post/mock",
            error=None,
            timestamp=datetime.now().isoformat()
        )


class ContentTransformer:
    """콘텐츠 플랫폼별 변환기"""

    @staticmethod
    def from_instagram(
        caption: str,
        images: List[str],
        hashtags: List[str],
        topic_kr: str,
        link: str = None
    ) -> Dict[Platform, PlatformContent]:
        """Instagram 콘텐츠를 다른 플랫폼용으로 변환"""

        results = {}

        # Instagram 원본
        results[Platform.INSTAGRAM] = PlatformContent(
            platform=Platform.INSTAGRAM,
            text=caption,
            images=images,
            hashtags=hashtags,
            link=link
        )

        # X용 변환 (짧은 텍스트 + 이미지 1장)
        x_text = ContentTransformer._shorten_for_x(caption, topic_kr)
        results[Platform.X] = PlatformContent(
            platform=Platform.X,
            text=x_text,
            images=images[:1],  # 첫 번째 이미지만
            hashtags=hashtags[:3],  # 해시태그 3개만
            link=link
        )

        # Threads용 변환 (대화체 + 이미지)
        threads_text = ContentTransformer._convert_for_threads(caption, topic_kr)
        results[Platform.THREADS] = PlatformContent(
            platform=Platform.THREADS,
            text=threads_text,
            images=images[:1],  # 첫 번째 이미지
            hashtags=[],  # Threads는 해시태그 최소화
            link=link
        )

        return results

    @staticmethod
    def _shorten_for_x(caption: str, topic_kr: str) -> str:
        """X용 임팩트 텍스트 생성

        전략: 짧고 단언형, RT 유도
        - 200자 이하 권장 (280자 제한)
        - 해시태그 2~3개
        - "~임!" / "~됨" 톤
        """
        import random

        # 훅 템플릿
        hooks = [
            f"🐕 {topic_kr}, 강아지 먹어도 됨!",
            f"{topic_kr} 주기 전 이것만!",
            f"몰랐지? {topic_kr} 이렇게 줘야 함",
            f"{topic_kr} 급여 꿀팁 3초 정리",
        ]

        # CTA 템플릿 (브랜드 톤 유지)
        ctas = [
            "RT로 다른 견주한테 알려주세요 🐕",
            "견주 친구에게 공유해주세요",
            "알면 좋은 정보, RT 부탁드려요!",
        ]

        # 캡션에서 핵심 정보 2개 추출
        lines = [l.strip() for l in caption.split('\n') if l.strip()]
        core_infos = []

        for line in lines:
            if any(marker in line for marker in ['→', '좋', '주의', '적정', '껍질', '칼륨', '비타민']):
                clean_line = line.replace('•', '').replace('✅', '✅').replace('⚠️', '⚠️').strip()
                if 10 < len(clean_line) < 40:
                    core_infos.append(clean_line)
                    if len(core_infos) >= 2:
                        break

        # 톤 변환
        tone_map = {
            "좋아요": "Good",
            "입니다": "임",
            "합니다": "함",
            "됩니다": "됨",
            "에 ": " ",
        }

        converted_infos = []
        for info in core_infos[:2]:
            for formal, casual in tone_map.items():
                info = info.replace(formal, casual)
            converted_infos.append(info)

        # 조합
        hook = random.choice(hooks)
        cta = random.choice(ctas)
        hashtags = "#강아지간식 #반려견"

        if converted_infos:
            info_text = "\n".join(converted_infos)
            template = f"{hook}\n\n{info_text}\n\n{cta}\n\n{hashtags}"
        else:
            template = f"{hook}\n\n{cta}\n\n{hashtags}"

        # 280자 제한
        if len(template) > 280:
            template = f"{hook}\n\n{cta}\n\n{hashtags}"

        return template[:280]

    @staticmethod
    def _convert_for_threads(caption: str, topic_kr: str, food_info: dict = None) -> str:
        """Threads용 캐주얼 대화체 텍스트 생성

        전략: Instagram 정보형 → Threads 수다형
        - 300자 이하
        - 해시태그 없음
        - 친구한테 말하는 톤
        - 댓글 유도 CTA
        """
        import random

        # 공감형 훅 템플릿
        hooks = [
            f"우리 집 강아지만 {topic_kr} 좋아하나? 🐕",
            f"나만 몰랐나... {topic_kr} 줘도 되는 거였어?",
            f"{topic_kr} 주기 전에 이것만 알아두자!",
            f"우리 강아지한테 {topic_kr} 줬더니 ㅋㅋㅋ",
            f"다들 {topic_kr} 어떻게 주고 있어?",
        ]

        # CTA 템플릿
        ctas = [
            "너네 강아지는 이거 좋아해? 댓글 ㄱㄱ 🐕",
            "다들 어떻게 주고 있어? 궁금해!",
            "댓글로 알려줘~ 참고할게 ㅎㅎ",
            "우리 강아지만 그런 거 아니지? ㅋㅋ",
            "다른 음식도 궁금하면 댓글!",
        ]

        # 캡션에서 핵심 정보 추출
        lines = [l.strip() for l in caption.split('\n') if l.strip()]

        # 효능/주의사항 추출 시도
        core_info = ""
        for line in lines:
            # "✅", "⚠️", "→", "•" 등이 포함된 핵심 라인 찾기
            if any(marker in line for marker in ['→', '좋', '주의', '적정', '껍질']):
                # 이모지 및 기호 정리
                clean_line = line.replace('•', '').replace('✅', '').replace('⚠️', '').strip()
                if len(clean_line) < 50:
                    core_info = clean_line
                    break

        if not core_info and lines:
            # 첫 번째 의미있는 라인 사용
            for line in lines[1:5]:
                if len(line) > 10 and len(line) < 60:
                    core_info = line.replace('•', '').strip()
                    break

        # 톤 변환 (딱딱한 표현 → 캐주얼)
        tone_map = {
            "입니다": "야",
            "합니다": "해",
            "됩니다": "돼",
            "하세요": "해봐",
            "습니다": "어",
            "세요": "해",
        }

        for formal, casual in tone_map.items():
            core_info = core_info.replace(formal, casual)

        # 최종 조합
        hook = random.choice(hooks)
        cta = random.choice(ctas)

        if core_info:
            template = f"{hook}\n\n{core_info}\n\n{cta}"
        else:
            template = f"{hook}\n\n{cta}"

        # 300자 제한
        return template[:300]


class MultiPlatformManager:
    """멀티플랫폼 통합 관리자"""

    def __init__(self):
        self.adapters = {
            Platform.X: XAdapter(),
            Platform.THREADS: ThreadsAdapter(),
        }
        self.transformer = ContentTransformer()
        self.history_file = PROJECT_ROOT / "config" / "data" / "cross_post_history.json"
        self._load_history()

    def _load_history(self):
        """게시 이력 로드"""
        if self.history_file.exists():
            with open(self.history_file, 'r', encoding='utf-8') as f:
                self.history = json.load(f)
        else:
            self.history = {"posts": []}

    def _save_history(self):
        """게시 이력 저장"""
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)

    async def cross_post(
        self,
        caption: str,
        images: List[str],
        hashtags: List[str],
        topic_kr: str,
        topic_en: str,
        platforms: List[Platform] = None,
        link: str = None
    ) -> Dict[Platform, CrossPostResult]:
        """여러 플랫폼에 동시 게시"""

        if platforms is None:
            platforms = [Platform.X, Platform.THREADS]

        # 콘텐츠 변환
        contents = self.transformer.from_instagram(
            caption=caption,
            images=images,
            hashtags=hashtags,
            topic_kr=topic_kr,
            link=link
        )

        results = {}

        # 각 플랫폼에 게시
        for platform in platforms:
            if platform in self.adapters and platform in contents:
                adapter = self.adapters[platform]
                content = contents[platform]

                result = await adapter.post(content)
                results[platform] = result

                # 이력 저장
                self.history["posts"].append({
                    "topic_en": topic_en,
                    "topic_kr": topic_kr,
                    "platform": platform.value,
                    "success": result.success,
                    "post_url": result.post_url,
                    "timestamp": result.timestamp,
                    "error": result.error
                })

        self._save_history()
        return results

    def get_platform_status(self) -> Dict[str, Dict]:
        """플랫폼별 상태 확인"""
        status = {}

        for platform, adapter in self.adapters.items():
            # API 키 설정 여부 확인
            if platform == Platform.X:
                configured = all([
                    os.environ.get("X_API_KEY"),
                    os.environ.get("X_ACCESS_TOKEN")
                ])
            elif platform == Platform.THREADS:
                configured = bool(os.environ.get("INSTAGRAM_ACCESS_TOKEN"))
            else:
                configured = False

            # 최근 게시 이력
            recent_posts = [
                p for p in self.history.get("posts", [])
                if p["platform"] == platform.value
            ][-5:]

            status[platform.value] = {
                "configured": configured,
                "recent_posts": len(recent_posts),
                "last_post": recent_posts[-1] if recent_posts else None
            }

        return status

    def preview_content(
        self,
        caption: str,
        images: List[str],
        hashtags: List[str],
        topic_kr: str
    ) -> Dict[str, str]:
        """변환된 콘텐츠 미리보기"""
        contents = self.transformer.from_instagram(
            caption=caption,
            images=images,
            hashtags=hashtags,
            topic_kr=topic_kr
        )

        preview = {}
        for platform, content in contents.items():
            preview[platform.value] = {
                "text": content.text,
                "images_count": len(content.images),
                "hashtags": content.hashtags,
                "char_count": len(content.text)
            }

        return preview


# CLI 실행
if __name__ == "__main__":
    import sys

    manager = MultiPlatformManager()

    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == "status":
            status = manager.get_platform_status()
            print("\n=== 멀티플랫폼 상태 ===\n")
            for platform, info in status.items():
                configured = "✅" if info["configured"] else "❌"
                print(f"  {configured} {platform}")
                print(f"     설정됨: {info['configured']}")
                print(f"     최근 게시: {info['recent_posts']}건")
                if info['last_post']:
                    print(f"     마지막: {info['last_post']['timestamp'][:10]}")

        elif cmd == "preview":
            # 테스트 미리보기
            preview = manager.preview_content(
                caption="바나나는 강아지가 먹어도 되는 과일이에요! 🍌\n\n칼륨이 풍부해서 심장 건강에 좋아요.",
                images=["test.png"],
                hashtags=["강아지음식", "반려견", "바나나"],
                topic_kr="바나나"
            )
            print("\n=== 콘텐츠 미리보기 ===\n")
            for platform, info in preview.items():
                print(f"[{platform}]")
                print(f"  글자수: {info['char_count']}")
                print(f"  이미지: {info['images_count']}장")
                print(f"  해시태그: {info['hashtags']}")
                print(f"  텍스트:\n{info['text'][:200]}...")
                print()

        elif cmd == "test":
            # 테스트 게시 (dry-run)
            async def test_post():
                results = await manager.cross_post(
                    caption="테스트 캡션",
                    images=["test.png"],
                    hashtags=["테스트"],
                    topic_kr="테스트",
                    topic_en="test"
                )
                for platform, result in results.items():
                    status = "✅" if result.success else "❌"
                    print(f"  {status} {platform.value}: {result.post_url or result.error}")

            print("\n=== 테스트 게시 ===\n")
            asyncio.run(test_post())

        else:
            print("Usage: python multi_platform.py [status|preview|test]")
    else:
        # 기본: 상태 표시
        status = manager.get_platform_status()
        configured = sum(1 for s in status.values() if s["configured"])
        print(f"\n멀티플랫폼: {configured}/{len(status)} 설정됨")
