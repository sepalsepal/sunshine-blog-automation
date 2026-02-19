"""
# ============================================================
# 📊 AnalyticsAgent - 데이터 분석 전문가 (정분석)
# ============================================================
#
# 📋 이 파일의 역할:
#    Instagram 게시물 성과를 분석하고 인사이트를 도출해요!
#    - 참여율/도달/저장 등 KPI 분석
#    - 최적 게시 시간 추천
#    - 콘텐츠 성과 패턴 파악
#    - 다음 주제 추천
#
# 🎯 왜 별도 에이전트로 분리했나요?
#    데이터 분석은 전문성이 필요해요!
#    - 단순 수치가 아닌 인사이트 도출
#    - 트렌드와 패턴 분석
#    - 예측 기반 추천
#    - A/B 테스트 결과 해석
#
# Author: 정분석 (Jung Bun-seok)
# ============================================================
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from .base import BaseAgent, AgentResult


class AnalyticsAgent(BaseAgent):
    """
    ╔════════════════════════════════════════════════════════╗
    ║  📊 데이터 분석 전문 에이전트 (정분석)                   ║
    ╠════════════════════════════════════════════════════════╣
    ║  이 에이전트가 하는 일:                                   ║
    ║  1. Instagram 인사이트 분석                              ║
    ║  2. 콘텐츠 성과 측정 및 랭킹                             ║
    ║  3. 최적 게시 시간 추천                                  ║
    ║  4. 다음 콘텐츠 주제 추천                                ║
    ║  5. 해시태그 성과 분석                                   ║
    ╚════════════════════════════════════════════════════════╝
    """

    @property
    def name(self) -> str:
        return "Analytics"

    # ========================================================
    # 📊 KPI 기준값
    # ========================================================
    KPI_BENCHMARKS = {
        "engagement_rate": {
            "excellent": 10.0,
            "good": 5.0,
            "average": 3.0,
            "poor": 1.0
        },
        "save_rate": {
            "excellent": 15.0,
            "good": 10.0,
            "average": 5.0,
            "poor": 2.0
        },
        "comment_target": 10,
        "follower_growth_weekly": 2.0  # %
    }

    # ========================================================
    # 📌 콘텐츠 카테고리
    # ========================================================
    CONTENT_CATEGORIES = {
        "safe_fruits": ["apple", "banana", "blueberry", "strawberry", "watermelon"],
        "safe_vegetables": ["carrot", "sweet_potato", "pumpkin"],
        "dangerous": ["grape", "onion", "chocolate", "avocado"],
        "conditional": ["cherry", "peach", "mango"]
    }

    # ========================================================
    # 📅 최적 시간대 데이터
    # ========================================================
    OPTIMAL_POSTING_TIMES = {
        "weekday_evening": {"days": [1, 2, 3, 4], "hours": [19, 20, 21], "boost": 1.35},
        "weekend_afternoon": {"days": [5, 6], "hours": [14, 15, 16], "boost": 1.25},
        "sunday_evening": {"days": [6], "hours": [19, 20], "boost": 1.20}
    }

    async def execute(self, input_data: Any) -> AgentResult:
        """
        📊 성과 분석 실행

        [입력]
        input_data = {
            "period": "7d",
            "posts": [
                {
                    "post_id": "...",
                    "topic": "apple",
                    "published_at": "2025-01-20T14:30:00",
                    "insights": {
                        "reach": 12500,
                        "impressions": 18700,
                        "likes": 850,
                        "comments": 45,
                        "saves": 120,
                        "shares": 30
                    }
                }
            ],
            "account_insights": {
                "followers": 15000,
                "follower_growth": 250,
                "profile_visits": 3200
            }
        }

        [출력]
        {
            "summary": {...},
            "performance_ranking": [...],
            "patterns": {...},
            "recommendations": {...},
            "alerts": [...]
        }
        """
        self.log("📊 성과 분석 시작")

        # 입력 데이터 파싱
        period = input_data.get("period", "7d")
        posts = input_data.get("posts", [])
        account_insights = input_data.get("account_insights", {})

        if not posts:
            self.log("⚠️ 분석할 게시물이 없습니다")
            return AgentResult(
                success=True,
                data=self._generate_empty_report(period),
                metadata={"agent": "jungbunseok", "posts_analyzed": 0}
            )

        # 1. 요약 통계 계산
        summary = self._calculate_summary(posts, account_insights)
        self.log(f"  ✓ 요약 통계 완료 (게시물 {len(posts)}개)")

        # 2. 성과 랭킹
        ranking = self._calculate_ranking(posts)
        self.log(f"  ✓ 성과 랭킹 완료 (TOP: {ranking[0]['topic'] if ranking else 'N/A'})")

        # 3. 패턴 분석
        patterns = self._analyze_patterns(posts)
        self.log("  ✓ 패턴 분석 완료")

        # 4. 추천 생성
        recommendations = self._generate_recommendations(posts, ranking, patterns)
        self.log("  ✓ 추천 생성 완료")

        # 5. 알림 생성
        alerts = self._generate_alerts(summary, posts, account_insights)
        self.log(f"  ✓ 알림 {len(alerts)}개 생성")

        # 분석 기간 계산
        analysis_period = self._calculate_period_string(posts, period)

        result_data = {
            "analysis_period": analysis_period,
            "summary": summary,
            "performance_ranking": ranking,
            "patterns": patterns,
            "recommendations": recommendations,
            "alerts": alerts,
            "report": self._generate_text_report(summary, ranking, patterns, recommendations, alerts)
        }

        self.log(f"✓ 분석 완료 (평균 참여율: {summary['avg_engagement_rate']:.1f}%)")

        return AgentResult(
            success=True,
            data=result_data,
            metadata={
                "agent": "jungbunseok",
                "posts_analyzed": len(posts),
                "analysis_period": analysis_period,
                "data_source": "Instagram Graph API"
            }
        )

    def _calculate_summary(self, posts: List[Dict], account_insights: Dict) -> Dict:
        """요약 통계 계산"""
        total_reach = 0
        total_engagement = 0
        engagement_rates = []

        for post in posts:
            insights = post.get("insights", {})
            reach = insights.get("reach", 0)
            likes = insights.get("likes", 0)
            comments = insights.get("comments", 0)
            saves = insights.get("saves", 0)
            shares = insights.get("shares", 0)

            total_reach += reach
            engagement = likes + comments + saves + shares
            total_engagement += engagement

            if reach > 0:
                rate = (engagement / reach) * 100
                engagement_rates.append({
                    "topic": post.get("topic", "unknown"),
                    "rate": rate
                })

        # 최고/최저 성과 찾기
        best = max(engagement_rates, key=lambda x: x["rate"]) if engagement_rates else None
        worst = min(engagement_rates, key=lambda x: x["rate"]) if engagement_rates else None

        avg_rate = sum(e["rate"] for e in engagement_rates) / len(engagement_rates) if engagement_rates else 0

        return {
            "total_posts": len(posts),
            "total_reach": total_reach,
            "total_engagement": total_engagement,
            "avg_engagement_rate": round(avg_rate, 2),
            "best_performing": best["topic"] if best else None,
            "worst_performing": worst["topic"] if worst else None,
            "followers": account_insights.get("followers", 0),
            "follower_growth": account_insights.get("follower_growth", 0),
            "profile_visits": account_insights.get("profile_visits", 0)
        }

    def _calculate_ranking(self, posts: List[Dict]) -> List[Dict]:
        """성과 랭킹 계산"""
        rankings = []

        for post in posts:
            insights = post.get("insights", {})
            reach = insights.get("reach", 0)
            likes = insights.get("likes", 0)
            comments = insights.get("comments", 0)
            saves = insights.get("saves", 0)
            shares = insights.get("shares", 0)

            engagement = likes + comments + saves + shares
            rate = (engagement / reach * 100) if reach > 0 else 0

            # 인사이트 문구 생성
            insight_text = self._generate_post_insight(post, rate, saves, comments)

            rankings.append({
                "topic": post.get("topic", "unknown"),
                "post_id": post.get("post_id"),
                "engagement_rate": round(rate, 2),
                "reach": reach,
                "likes": likes,
                "comments": comments,
                "saves": saves,
                "shares": shares,
                "insights": insight_text
            })

        # 참여율 기준 정렬
        rankings.sort(key=lambda x: x["engagement_rate"], reverse=True)

        # 순위 부여
        for i, item in enumerate(rankings):
            item["rank"] = i + 1

        return rankings

    def _generate_post_insight(self, post: Dict, rate: float, saves: int, comments: int) -> str:
        """개별 게시물 인사이트 문구 생성"""
        topic = post.get("topic", "unknown")
        insights = []

        # 참여율 기반
        if rate > 12:
            insights.append(f"{topic} 콘텐츠 매우 높은 반응!")
        elif rate > 8:
            insights.append(f"{topic} 콘텐츠 좋은 반응")

        # 저장 기반
        if saves > 150:
            insights.append("저장률 매우 높음 - 정보성 콘텐츠 효과적")
        elif saves > 100:
            insights.append("저장률 높음")

        # 댓글 기반
        if comments > 50:
            insights.append("댓글 활발 - 질문/토론 유도 성공")
        elif comments > 30:
            insights.append("댓글 반응 좋음")

        return " / ".join(insights) if insights else "표준 성과"

    def _analyze_patterns(self, posts: List[Dict]) -> Dict:
        """패턴 분석"""
        # 시간대별 분석
        time_performance = defaultdict(list)
        day_performance = defaultdict(list)
        category_performance = defaultdict(list)
        hashtag_performance = defaultdict(list)

        for post in posts:
            insights = post.get("insights", {})
            reach = insights.get("reach", 0)
            engagement = insights.get("likes", 0) + insights.get("comments", 0) + \
                         insights.get("saves", 0) + insights.get("shares", 0)
            rate = (engagement / reach * 100) if reach > 0 else 0

            # 시간 분석
            published_at = post.get("published_at")
            if published_at:
                try:
                    dt = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                    hour = dt.hour
                    day = dt.weekday()

                    time_slot = self._get_time_slot(hour)
                    time_performance[time_slot].append(rate)
                    day_performance[day].append(rate)
                except:
                    pass

            # 카테고리 분석
            topic = post.get("topic", "unknown")
            category = self._get_category(topic)
            category_performance[category].append(rate)

        # 최적 시간 계산
        best_time = self._find_best_time(time_performance, day_performance)

        # 최고 성과 카테고리
        best_category = self._find_best_category(category_performance)

        # 해시태그 분석 (샘플 데이터)
        hashtag_analysis = {
            "top_hashtags": ["#강아지간식", "#반려견영양", "#골든리트리버"],
            "low_performance": ["#일상", "#daily"],
            "recommendations": ["#펫스타그램 추가 권장"]
        }

        return {
            "best_posting_time": best_time,
            "best_content_type": best_category,
            "hashtag_performance": hashtag_analysis,
            "time_distribution": dict(time_performance),
            "day_distribution": {self._day_name(k): v for k, v in day_performance.items()}
        }

    def _get_time_slot(self, hour: int) -> str:
        """시간대 슬롯 반환"""
        if 6 <= hour < 12:
            return "오전 (6-12시)"
        elif 12 <= hour < 18:
            return "오후 (12-18시)"
        elif 18 <= hour < 24:
            return "저녁 (18-24시)"
        else:
            return "심야 (0-6시)"

    def _day_name(self, day: int) -> str:
        """요일 이름 반환"""
        days = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
        return days[day] if 0 <= day < 7 else "알수없음"

    def _get_category(self, topic: str) -> str:
        """토픽의 카테고리 반환"""
        for category, topics in self.CONTENT_CATEGORIES.items():
            if topic in topics:
                return category
        return "unknown"

    def _find_best_time(self, time_perf: Dict, day_perf: Dict) -> Dict:
        """최적 게시 시간 찾기"""
        # 시간대별 평균
        time_avg = {}
        for slot, rates in time_perf.items():
            if rates:
                time_avg[slot] = sum(rates) / len(rates)

        # 요일별 평균
        day_avg = {}
        for day, rates in day_perf.items():
            if rates:
                day_avg[day] = sum(rates) / len(rates)

        # 최고 시간대/요일 찾기
        best_time_slot = max(time_avg, key=time_avg.get) if time_avg else "저녁 (18-24시)"
        best_day = max(day_avg, key=day_avg.get) if day_avg else 1  # 화요일

        best_day_name = self._day_name(best_day) if isinstance(best_day, int) else "화요일"

        return {
            "day": best_day_name,
            "time": best_time_slot,
            "reason": f"해당 시간대 참여율이 평균 대비 높음"
        }

    def _find_best_category(self, category_perf: Dict) -> Dict:
        """최고 성과 카테고리 찾기"""
        category_avg = {}
        for cat, rates in category_perf.items():
            if rates:
                category_avg[cat] = sum(rates) / len(rates)

        if not category_avg:
            return {
                "type": "safe_fruits",
                "reason": "데이터 부족 - 기본 추천"
            }

        best_cat = max(category_avg, key=category_avg.get)

        category_names = {
            "safe_fruits": "급여 가능 과일",
            "safe_vegetables": "급여 가능 채소",
            "dangerous": "급여 금지 음식",
            "conditional": "조건부 급여 음식"
        }

        return {
            "type": category_names.get(best_cat, best_cat),
            "reason": f"해당 카테고리 평균 참여율 {category_avg[best_cat]:.1f}%"
        }

    def _generate_recommendations(self, posts: List[Dict], ranking: List[Dict],
                                   patterns: Dict) -> Dict:
        """추천 생성"""
        # 게시된 주제 목록
        posted_topics = {p.get("topic") for p in posts}

        # 미게시 주제 중 추천
        all_topics = []
        for topics in self.CONTENT_CATEGORIES.values():
            all_topics.extend(topics)

        next_topics = []
        for topic in all_topics:
            if topic not in posted_topics:
                category = self._get_category(topic)
                expected = "높음" if category in ["safe_fruits", "dangerous"] else "중간"
                reason = self._get_topic_reason(topic, category, ranking)
                next_topics.append({
                    "topic": topic,
                    "reason": reason,
                    "expected_engagement": expected
                })

        # 상위 3개만
        next_topics = next_topics[:3]

        # 게시 스케줄 추천
        best_time = patterns.get("best_posting_time", {})
        posting_schedule = {
            "recommended": f"{best_time.get('day', '화요일')} 19:00-21:00",
            "avoid": "월요일 오전"
        }

        # 콘텐츠 개선점
        improvements = self._generate_improvements(ranking)

        return {
            "next_topics": next_topics,
            "posting_schedule": posting_schedule,
            "content_improvements": improvements
        }

    def _get_topic_reason(self, topic: str, category: str, ranking: List[Dict]) -> str:
        """주제 추천 이유 생성"""
        topic_names = {
            "blueberry": "블루베리",
            "carrot": "당근",
            "watermelon": "수박",
            "sweet_potato": "고구마",
            "pumpkin": "단호박",
            "grape": "포도",
            "strawberry": "딸기"
        }

        korean_name = topic_names.get(topic, topic)

        if category == "safe_fruits":
            return f"과일 카테고리 인기 + {korean_name} 미게시"
        elif category == "safe_vegetables":
            return f"채소 카테고리 테스트 필요 - {korean_name}"
        elif category == "dangerous":
            return f"경고성 콘텐츠 높은 참여율 - {korean_name}"
        else:
            return f"{korean_name} 콘텐츠 테스트 권장"

    def _generate_improvements(self, ranking: List[Dict]) -> List[str]:
        """콘텐츠 개선점 생성"""
        improvements = []

        # 저조한 게시물 분석
        if ranking:
            worst = ranking[-1]
            if worst["engagement_rate"] < 5:
                improvements.append("저성과 콘텐츠 첫 슬라이드 재검토")

            # 저장률 체크
            avg_saves = sum(r["saves"] for r in ranking) / len(ranking)
            if avg_saves < 100:
                improvements.append("저장 유도 문구 강화 필요")

            # 댓글 체크
            avg_comments = sum(r["comments"] for r in ranking) / len(ranking)
            if avg_comments < 20:
                improvements.append("질문형 CTA로 댓글 유도")

        # 기본 추천
        improvements.extend([
            "첫 슬라이드 질문형 유지",
            "CTA 슬라이드 명확하게"
        ])

        return improvements[:5]  # 최대 5개

    def _generate_alerts(self, summary: Dict, posts: List[Dict],
                         account_insights: Dict) -> List[Dict]:
        """알림 생성"""
        alerts = []

        # 팔로워 증가 알림
        follower_growth = account_insights.get("follower_growth", 0)
        if follower_growth >= 100:
            alerts.append({
                "type": "positive",
                "message": f"📈 팔로워 {follower_growth}명 증가!"
            })
        elif follower_growth < -50:
            alerts.append({
                "type": "warning",
                "message": f"📉 팔로워 {abs(follower_growth)}명 이탈 감지"
            })

        # 참여율 알림
        avg_rate = summary.get("avg_engagement_rate", 0)
        if avg_rate >= 10:
            alerts.append({
                "type": "positive",
                "message": f"🎉 평균 참여율 {avg_rate:.1f}% - 훌륭한 성과!"
            })
        elif avg_rate < 3:
            alerts.append({
                "type": "warning",
                "message": f"⚠️ 평균 참여율 {avg_rate:.1f}% - 콘텐츠 전략 점검 필요"
            })

        # 특정 게시물 성과 알림
        for post in posts:
            insights = post.get("insights", {})
            reach = insights.get("reach", 0)
            engagement = insights.get("likes", 0) + insights.get("comments", 0) + \
                         insights.get("saves", 0)
            rate = (engagement / reach * 100) if reach > 0 else 0

            if rate >= 15:
                topic = post.get("topic", "")
                alerts.append({
                    "type": "positive",
                    "message": f"🏆 {topic} 콘텐츠 참여율 {rate:.1f}% - 대박!"
                })

        return alerts

    def _calculate_period_string(self, posts: List[Dict], period: str) -> str:
        """분석 기간 문자열 생성"""
        if not posts:
            return "데이터 없음"

        dates = []
        for post in posts:
            published_at = post.get("published_at")
            if published_at:
                try:
                    dt = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                    dates.append(dt)
                except:
                    pass

        if dates:
            start = min(dates).strftime("%Y-%m-%d")
            end = max(dates).strftime("%Y-%m-%d")
            return f"{start} ~ {end}"

        return f"최근 {period}"

    def _generate_empty_report(self, period: str) -> Dict:
        """빈 리포트 생성"""
        return {
            "analysis_period": f"최근 {period}",
            "summary": {
                "total_posts": 0,
                "total_reach": 0,
                "total_engagement": 0,
                "avg_engagement_rate": 0,
                "best_performing": None,
                "worst_performing": None
            },
            "performance_ranking": [],
            "patterns": {},
            "recommendations": {
                "next_topics": [
                    {"topic": "apple", "reason": "첫 콘텐츠 추천", "expected_engagement": "높음"},
                    {"topic": "banana", "reason": "인기 주제", "expected_engagement": "높음"}
                ],
                "posting_schedule": {
                    "recommended": "화요일 19:00-21:00",
                    "avoid": "월요일 오전"
                },
                "content_improvements": ["첫 콘텐츠 게시 후 분석 시작"]
            },
            "alerts": [
                {"type": "info", "message": "📊 분석할 게시물이 없습니다. 콘텐츠 게시 후 다시 확인해주세요."}
            ],
            "report": "분석할 데이터가 없습니다."
        }

    def _generate_text_report(self, summary: Dict, ranking: List[Dict],
                              patterns: Dict, recommendations: Dict,
                              alerts: List[Dict]) -> str:
        """텍스트 형식 리포트 생성"""
        lines = []
        lines.append("╔═══════════════════════════════════════════════════════════╗")
        lines.append("║  📊 성과 분석 리포트                                        ║")
        lines.append("╠═══════════════════════════════════════════════════════════╣")
        lines.append("║                                                           ║")
        lines.append("║  📈 요약                                                   ║")
        lines.append(f"║  ├─ 게시물: {summary['total_posts']}개                                           ║")
        lines.append(f"║  ├─ 총 도달: {summary['total_reach']:,}                              ║")
        lines.append(f"║  ├─ 총 참여: {summary['total_engagement']:,}                              ║")
        lines.append(f"║  └─ 평균 참여율: {summary['avg_engagement_rate']:.1f}%                                     ║")
        lines.append("║                                                           ║")
        lines.append("╠═══════════════════════════════════════════════════════════╣")

        if ranking:
            lines.append("║  🏆 TOP 콘텐츠                                              ║")
            lines.append("║                                                           ║")
            for i, item in enumerate(ranking[:3]):
                topic_emoji = {"apple": "🍎", "banana": "🍌", "cherry": "🍒",
                               "blueberry": "🫐", "strawberry": "🍓", "carrot": "🥕",
                               "grape": "🍇", "watermelon": "🍉"}.get(item["topic"], "🐕")
                lines.append(f"║  {i+1}위: {topic_emoji} {item['topic']} (참여율 {item['engagement_rate']}%)              ║")
            lines.append("║                                                           ║")
            lines.append("╠═══════════════════════════════════════════════════════════╣")

        lines.append("║  💡 추천                                                    ║")
        lines.append("║                                                           ║")
        next_topics = recommendations.get("next_topics", [])
        if next_topics:
            lines.append("║  📌 다음 주제                                              ║")
            for topic in next_topics[:2]:
                lines.append(f"║  • {topic['topic']}: {topic['reason'][:30]}           ║")
        lines.append("║                                                           ║")
        schedule = recommendations.get("posting_schedule", {})
        lines.append(f"║  📌 게시 시간: {schedule.get('recommended', '화요일 19:00')}                     ║")
        lines.append("║                                                           ║")
        lines.append("╚═══════════════════════════════════════════════════════════╝")

        return "\n".join(lines)

    # ========================================================
    # 🔧 유틸리티 메서드 (직접 호출용)
    # ========================================================

    def quick_analysis(self, posts: List[Dict]) -> Dict:
        """
        🔧 간편 분석 (동기 버전)

        다른 에이전트에서 직접 호출 가능
        """
        if not posts:
            return {"status": "no_data", "message": "분석할 게시물 없음"}

        total_engagement = 0
        total_reach = 0

        for post in posts:
            insights = post.get("insights", {})
            total_reach += insights.get("reach", 0)
            total_engagement += (
                insights.get("likes", 0) +
                insights.get("comments", 0) +
                insights.get("saves", 0)
            )

        avg_rate = (total_engagement / total_reach * 100) if total_reach > 0 else 0

        return {
            "status": "ok",
            "posts_count": len(posts),
            "total_reach": total_reach,
            "total_engagement": total_engagement,
            "avg_engagement_rate": round(avg_rate, 2)
        }

    def get_next_topic_suggestion(self, posted_topics: List[str]) -> Dict:
        """
        🔧 다음 주제 추천 (간편 버전)
        """
        posted_set = set(posted_topics)

        # 우선순위: 과일 > 채소 > 위험식품
        priority_order = ["safe_fruits", "safe_vegetables", "dangerous", "conditional"]

        for category in priority_order:
            for topic in self.CONTENT_CATEGORIES.get(category, []):
                if topic not in posted_set:
                    return {
                        "topic": topic,
                        "category": category,
                        "reason": f"미게시 주제 - {category} 카테고리"
                    }

        return {
            "topic": "apple",
            "category": "safe_fruits",
            "reason": "기본 추천 - 재게시 고려"
        }
