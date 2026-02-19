#!/usr/bin/env python3
"""
Instagram 댓글 자동 응답 시스템 v1.0

기능:
- 새 댓글 감지 (polling 방식)
- 키워드 기반 자동 응답
- 응답 템플릿 관리
- 스팸 필터링
- 응답 이력 기록

사용법:
    from core.utils.comment_responder import CommentResponder

    responder = CommentResponder()
    responder.run_polling()  # 데몬 모드
    responder.process_new_comments()  # 단일 실행

Note:
    Instagram Graph API 권한 필요:
    - instagram_manage_comments (댓글 응답)
    - instagram_basic (기본 조회)

    권한 없을 시 시뮬레이션 모드로 동작

담당: 송지영 대리 (마케팅)
"""

import json
import os
import re
import random
import time
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

# 프로젝트 루트 설정
ROOT = Path(__file__).parent.parent.parent

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [CommentResponder] %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 파일 경로
TEMPLATES_FILE = ROOT / "config/settings/comment_templates.json"
RESPONSE_HISTORY_FILE = ROOT / "config/data/comment_response_history.json"
STATS_FILE = ROOT / "config/data/instagram_stats.json"

# .env 로드
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass


class ResponseType(Enum):
    """응답 유형"""
    KEYWORD_MATCH = "keyword"
    EMOJI_MATCH = "emoji"
    DEFAULT = "default"
    SKIPPED = "skipped"
    SPAM = "spam"


@dataclass
class Comment:
    """댓글 데이터"""
    id: str
    text: str
    username: str
    user_id: str
    timestamp: str
    post_id: str
    parent_id: Optional[str] = None  # 대댓글인 경우

    @classmethod
    def from_api(cls, data: Dict) -> 'Comment':
        """API 응답에서 Comment 객체 생성"""
        return cls(
            id=data.get("id", ""),
            text=data.get("text", ""),
            username=data.get("username", ""),
            user_id=data.get("from", {}).get("id", ""),
            timestamp=data.get("timestamp", ""),
            post_id=data.get("media", {}).get("id", ""),
            parent_id=data.get("parent_id")
        )


@dataclass
class ResponseRecord:
    """응답 기록"""
    comment_id: str
    comment_text: str
    username: str
    post_id: str
    response_text: str
    response_type: str
    template_key: Optional[str]
    responded_at: str
    simulated: bool = False


class CommentResponder:
    """Instagram 댓글 자동 응답 시스템"""

    def __init__(self, simulation_mode: bool = None):
        """
        Args:
            simulation_mode: True면 실제 API 호출 없이 시뮬레이션
                           None이면 토큰 유무에 따라 자동 결정
        """
        self.access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
        self.instagram_id = os.getenv("INSTAGRAM_BUSINESS_ID")

        # 시뮬레이션 모드 자동 결정
        if simulation_mode is None:
            self.simulation_mode = not self._has_comment_permission()
        else:
            self.simulation_mode = simulation_mode

        if self.simulation_mode:
            logger.warning("시뮬레이션 모드로 동작합니다 (실제 응답 안함)")

        # 템플릿 및 이력 로드
        self.templates = self._load_templates()
        self.history = self._load_history()
        self.stats = self._load_stats()

        # 일일 통계
        self._daily_count = self._get_today_response_count()

    def _has_comment_permission(self) -> bool:
        """댓글 응답 권한 확인"""
        if not self.access_token:
            return False

        try:
            import requests
            url = f"https://graph.facebook.com/v18.0/me/permissions"
            params = {"access_token": self.access_token}
            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                permissions = response.json().get("data", [])
                for perm in permissions:
                    if perm.get("permission") == "instagram_manage_comments":
                        return perm.get("status") == "granted"
            return False
        except Exception as e:
            logger.warning(f"권한 확인 실패: {e}")
            return False

    def _load_templates(self) -> Dict[str, Any]:
        """응답 템플릿 로드"""
        if TEMPLATES_FILE.exists():
            with open(TEMPLATES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"response_templates": {}, "spam_filters": {}, "settings": {}}

    def _load_history(self) -> Dict[str, Any]:
        """응답 이력 로드"""
        if RESPONSE_HISTORY_FILE.exists():
            with open(RESPONSE_HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "responses": [],
            "responded_comments": set(),
            "user_last_response": {},
            "daily_counts": {},
            "last_updated": None
        }

    def _save_history(self):
        """응답 이력 저장"""
        # set을 list로 변환하여 저장
        history_to_save = {
            **self.history,
            "responded_comments": list(self.history.get("responded_comments", set())),
            "last_updated": datetime.now().isoformat()
        }

        RESPONSE_HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(RESPONSE_HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history_to_save, f, ensure_ascii=False, indent=2)
        logger.debug(f"응답 이력 저장: {RESPONSE_HISTORY_FILE}")

    def _load_stats(self) -> Dict[str, Any]:
        """Instagram 통계 로드 (게시물 목록용)"""
        if STATS_FILE.exists():
            with open(STATS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"posts": {}}

    def _get_today_response_count(self) -> int:
        """오늘 응답 수 조회"""
        today = datetime.now().strftime("%Y-%m-%d")
        return self.history.get("daily_counts", {}).get(today, 0)

    def _increment_daily_count(self):
        """일일 응답 수 증가"""
        today = datetime.now().strftime("%Y-%m-%d")
        if "daily_counts" not in self.history:
            self.history["daily_counts"] = {}
        self.history["daily_counts"][today] = self.history["daily_counts"].get(today, 0) + 1
        self._daily_count = self.history["daily_counts"][today]

    def _is_daily_limit_reached(self) -> bool:
        """일일 제한 도달 여부"""
        limit = self.templates.get("settings", {}).get("daily_limit", 50)
        return self._daily_count >= limit

    def _can_respond_to_user(self, username: str) -> bool:
        """사용자에게 응답 가능 여부 (쿨다운 체크)"""
        cooldown_hours = self.templates.get("settings", {}).get("cooldown_per_user_hours", 24)
        last_response = self.history.get("user_last_response", {}).get(username)

        if not last_response:
            return True

        try:
            last_time = datetime.fromisoformat(last_response)
            cooldown = timedelta(hours=cooldown_hours)
            return datetime.now() - last_time > cooldown
        except:
            return True

    def _is_spam(self, text: str) -> bool:
        """스팸 댓글 여부 확인"""
        filters = self.templates.get("spam_filters", {})

        # 최소 길이 체크
        min_length = filters.get("min_length", 2)
        if len(text.strip()) < min_length:
            return True

        # 패턴 체크
        patterns = filters.get("patterns", [])
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                logger.debug(f"스팸 패턴 감지: {pattern}")
                return True

        # 이모지 비율 체크 (순수 이모지만 체크, 한글 제외)
        max_emoji_ratio = filters.get("max_emoji_ratio", 0.8)
        # 더 정확한 이모지 패턴 (한글 범위 제외)
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map
            "\U0001F1E0-\U0001F1FF"  # flags
            "\U0001F900-\U0001F9FF"  # supplemental symbols
            "\U0001FA00-\U0001FA6F"  # chess symbols
            "\U0001FA70-\U0001FAFF"  # symbols and pictographs extended-A
            "\U00002600-\U000026FF"  # misc symbols
            "\U00002700-\U000027BF"  # dingbats
            "]+", flags=re.UNICODE
        )

        emojis = emoji_pattern.findall(text)
        emoji_count = sum(len(e) for e in emojis)

        # 텍스트가 순수 이모지로만 구성된 경우만 체크
        if len(text) > 0 and emoji_count / len(text) > max_emoji_ratio:
            logger.debug(f"이모지 비율 초과: {emoji_count}/{len(text)}")
            return True

        return False

    def _was_already_responded(self, comment_id: str) -> bool:
        """이미 응답한 댓글인지 확인"""
        responded = self.history.get("responded_comments", set())
        if isinstance(responded, list):
            responded = set(responded)
            self.history["responded_comments"] = responded
        return comment_id in responded

    def _find_matching_template(self, text: str) -> Tuple[Optional[str], Optional[str], ResponseType]:
        """
        텍스트에 맞는 템플릿 찾기

        Returns:
            (응답 텍스트, 템플릿 키, 응답 유형)
        """
        templates = self.templates.get("response_templates", {})
        text_lower = text.lower()

        # 우선순위별로 정렬
        sorted_templates = sorted(
            templates.items(),
            key=lambda x: x[1].get("priority", 99)
        )

        for key, template in sorted_templates:
            # 이모지 패턴 매칭
            emoji_patterns = template.get("emoji_patterns", [])
            for emoji in emoji_patterns:
                if emoji in text:
                    responses = template.get("responses", [])
                    if responses:
                        return random.choice(responses), key, ResponseType.EMOJI_MATCH

            # 키워드 매칭
            keywords = template.get("keywords", [])
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    responses = template.get("responses", [])
                    if responses:
                        return random.choice(responses), key, ResponseType.KEYWORD_MATCH

        # 기본 응답
        default_config = self.templates.get("default_response", {})
        if default_config.get("enabled", False):
            return default_config.get("template", "감사합니다!"), None, ResponseType.DEFAULT

        return None, None, ResponseType.SKIPPED

    def fetch_comments_for_post(self, post_id: str) -> List[Comment]:
        """게시물의 댓글 조회 (Graph API)"""
        if self.simulation_mode or not self.access_token:
            logger.info(f"[시뮬레이션] 게시물 {post_id} 댓글 조회 스킵")
            return []

        try:
            import requests

            url = f"https://graph.facebook.com/v18.0/{post_id}/comments"
            params = {
                "fields": "id,text,username,from,timestamp",
                "access_token": self.access_token
            }
            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                comments = [Comment.from_api(c) for c in data.get("data", [])]
                logger.info(f"게시물 {post_id}: {len(comments)}개 댓글 조회")
                return comments
            else:
                logger.warning(f"API 에러: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"댓글 조회 실패: {e}")
            return []

    def fetch_all_new_comments(self) -> List[Comment]:
        """모든 게시물의 새 댓글 수집"""
        all_comments = []
        posts = self.stats.get("posts", {})

        for post_id, post_data in posts.items():
            comments = self.fetch_comments_for_post(post_id)

            # 이미 응답한 댓글 필터링
            new_comments = [
                c for c in comments
                if not self._was_already_responded(c.id)
            ]
            all_comments.extend(new_comments)

        logger.info(f"총 {len(all_comments)}개 새 댓글 발견")
        return all_comments

    def reply_to_comment(self, comment: Comment, response_text: str) -> bool:
        """댓글에 답글 달기"""
        if self.simulation_mode:
            logger.info(
                f"[시뮬레이션] @{comment.username}에게 응답: "
                f"\"{comment.text[:30]}...\" -> \"{response_text}\""
            )
            return True

        if not self.access_token:
            logger.error("Access Token이 없습니다")
            return False

        try:
            import requests

            url = f"https://graph.facebook.com/v18.0/{comment.id}/replies"
            data = {
                "message": response_text,
                "access_token": self.access_token
            }
            response = requests.post(url, data=data, timeout=10)

            if response.status_code == 200:
                logger.info(f"응답 완료: @{comment.username}")
                return True
            else:
                logger.error(f"응답 실패: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"응답 API 호출 실패: {e}")
            return False

    def process_comment(self, comment: Comment) -> Optional[ResponseRecord]:
        """단일 댓글 처리"""
        # 일일 제한 체크
        if self._is_daily_limit_reached():
            logger.warning(f"일일 응답 제한 도달: {self._daily_count}")
            return None

        # 이미 응답한 댓글
        if self._was_already_responded(comment.id):
            logger.debug(f"이미 응답한 댓글: {comment.id}")
            return None

        # 사용자 쿨다운 체크
        if not self._can_respond_to_user(comment.username):
            logger.debug(f"쿨다운 중: @{comment.username}")
            return None

        # 스팸 필터링
        if self._is_spam(comment.text):
            logger.info(f"스팸 필터링: \"{comment.text[:30]}...\"")
            return ResponseRecord(
                comment_id=comment.id,
                comment_text=comment.text,
                username=comment.username,
                post_id=comment.post_id,
                response_text="",
                response_type=ResponseType.SPAM.value,
                template_key=None,
                responded_at=datetime.now().isoformat(),
                simulated=self.simulation_mode
            )

        # 매칭되는 응답 템플릿 찾기
        response_text, template_key, response_type = self._find_matching_template(comment.text)

        if not response_text:
            logger.debug(f"매칭 템플릿 없음: \"{comment.text[:30]}...\"")
            return None

        # 응답 딜레이 (자연스러움을 위해)
        delay_range = self.templates.get("settings", {}).get("response_delay_seconds", [30, 120])
        if len(delay_range) == 2 and not self.simulation_mode:
            delay = random.randint(delay_range[0], delay_range[1])
            logger.info(f"{delay}초 후 응답 예정...")
            time.sleep(delay)

        # 실제 응답
        success = self.reply_to_comment(comment, response_text)

        if success:
            # 기록 업데이트
            self._record_response(comment, response_text, template_key, response_type)

            return ResponseRecord(
                comment_id=comment.id,
                comment_text=comment.text,
                username=comment.username,
                post_id=comment.post_id,
                response_text=response_text,
                response_type=response_type.value,
                template_key=template_key,
                responded_at=datetime.now().isoformat(),
                simulated=self.simulation_mode
            )

        return None

    def _record_response(
        self,
        comment: Comment,
        response_text: str,
        template_key: Optional[str],
        response_type: ResponseType
    ):
        """응답 기록 저장"""
        # responded_comments 업데이트
        if "responded_comments" not in self.history:
            self.history["responded_comments"] = set()
        if isinstance(self.history["responded_comments"], list):
            self.history["responded_comments"] = set(self.history["responded_comments"])
        self.history["responded_comments"].add(comment.id)

        # 사용자 마지막 응답 시간
        if "user_last_response" not in self.history:
            self.history["user_last_response"] = {}
        self.history["user_last_response"][comment.username] = datetime.now().isoformat()

        # 응답 로그
        if "responses" not in self.history:
            self.history["responses"] = []

        record = ResponseRecord(
            comment_id=comment.id,
            comment_text=comment.text,
            username=comment.username,
            post_id=comment.post_id,
            response_text=response_text,
            response_type=response_type.value,
            template_key=template_key,
            responded_at=datetime.now().isoformat(),
            simulated=self.simulation_mode
        )
        self.history["responses"].append(asdict(record))

        # 일일 카운트 증가
        self._increment_daily_count()

        # 저장
        self._save_history()

    def process_new_comments(self) -> List[ResponseRecord]:
        """새 댓글 일괄 처리"""
        logger.info("=== 새 댓글 처리 시작 ===")

        comments = self.fetch_all_new_comments()
        results = []

        for comment in comments:
            if self._is_daily_limit_reached():
                logger.warning("일일 제한 도달, 처리 중단")
                break

            result = self.process_comment(comment)
            if result:
                results.append(result)

        logger.info(f"=== 처리 완료: {len(results)}개 응답 ===")
        return results

    def run_polling(self, interval_seconds: int = 300):
        """폴링 모드 실행 (데몬)

        Args:
            interval_seconds: 폴링 간격 (기본 5분)
        """
        logger.info(f"폴링 모드 시작 (간격: {interval_seconds}초)")

        try:
            while True:
                try:
                    results = self.process_new_comments()
                    logger.info(f"이번 사이클: {len(results)}개 응답, 오늘 총: {self._daily_count}")
                except Exception as e:
                    logger.error(f"처리 중 에러: {e}")

                logger.info(f"{interval_seconds}초 대기...")
                time.sleep(interval_seconds)

        except KeyboardInterrupt:
            logger.info("폴링 중단됨")

    def simulate_response(self, text: str) -> Dict[str, Any]:
        """테스트용: 텍스트에 대한 응답 시뮬레이션

        Args:
            text: 테스트할 댓글 텍스트

        Returns:
            시뮬레이션 결과
        """
        # 스팸 체크
        is_spam = self._is_spam(text)
        if is_spam:
            return {
                "input": text,
                "is_spam": True,
                "response": None,
                "template_key": None,
                "response_type": ResponseType.SPAM.value
            }

        # 템플릿 매칭
        response_text, template_key, response_type = self._find_matching_template(text)

        return {
            "input": text,
            "is_spam": False,
            "response": response_text,
            "template_key": template_key,
            "response_type": response_type.value
        }

    def get_stats(self) -> Dict[str, Any]:
        """응답 통계 조회"""
        today = datetime.now().strftime("%Y-%m-%d")

        responses = self.history.get("responses", [])

        # 유형별 통계
        type_counts = {}
        for r in responses:
            rtype = r.get("response_type", "unknown")
            type_counts[rtype] = type_counts.get(rtype, 0) + 1

        # 템플릿별 통계
        template_counts = {}
        for r in responses:
            tkey = r.get("template_key") or "none"
            template_counts[tkey] = template_counts.get(tkey, 0) + 1

        return {
            "total_responses": len(responses),
            "today_count": self.history.get("daily_counts", {}).get(today, 0),
            "daily_limit": self.templates.get("settings", {}).get("daily_limit", 50),
            "unique_users": len(self.history.get("user_last_response", {})),
            "by_type": type_counts,
            "by_template": template_counts,
            "simulation_mode": self.simulation_mode
        }

    def print_stats(self):
        """통계 출력"""
        stats = self.get_stats()

        print("\n" + "=" * 50)
        print("Instagram Comment Responder Stats")
        print("=" * 50)
        print(f"시뮬레이션 모드: {'ON' if stats['simulation_mode'] else 'OFF'}")
        print(f"총 응답 수: {stats['total_responses']}")
        print(f"오늘 응답: {stats['today_count']} / {stats['daily_limit']}")
        print(f"응답한 사용자 수: {stats['unique_users']}")

        print("\n유형별 분포:")
        for rtype, count in stats['by_type'].items():
            print(f"  - {rtype}: {count}")

        print("\n템플릿별 분포:")
        for tkey, count in stats['by_template'].items():
            print(f"  - {tkey}: {count}")
        print("=" * 50 + "\n")


def main():
    """CLI 진입점"""
    import argparse

    parser = argparse.ArgumentParser(description="Instagram 댓글 자동 응답 시스템")
    parser.add_argument("--poll", action="store_true", help="폴링 모드 실행")
    parser.add_argument("--interval", type=int, default=300, help="폴링 간격 (초)")
    parser.add_argument("--once", action="store_true", help="1회 실행 후 종료")
    parser.add_argument("--stats", action="store_true", help="통계 출력")
    parser.add_argument("--simulate", type=str, help="텍스트 응답 시뮬레이션")
    parser.add_argument("--force-simulate", action="store_true", help="강제 시뮬레이션 모드")

    args = parser.parse_args()

    responder = CommentResponder(simulation_mode=args.force_simulate or None)

    if args.stats:
        responder.print_stats()
    elif args.simulate:
        result = responder.simulate_response(args.simulate)
        print(f"\n입력: \"{args.simulate}\"")
        print(f"스팸: {result['is_spam']}")
        print(f"응답: {result['response']}")
        print(f"템플릿: {result['template_key']}")
        print(f"유형: {result['response_type']}\n")
    elif args.poll:
        responder.run_polling(interval_seconds=args.interval)
    elif args.once:
        results = responder.process_new_comments()
        print(f"\n처리 완료: {len(results)}개 응답")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
