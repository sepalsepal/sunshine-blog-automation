#!/usr/bin/env python3
"""
# ============================================================
# A/B Test Manager - Instagram Contents A/B Testing System
# ============================================================
#
# Purpose:
#    - Track multiple versions (A/B) of same topic content
#    - Compare performance metrics (likes, comments, saves)
#    - Auto-determine winner after test period (7 days default)
#    - Generate test result reports
#
# Test Variables:
#    - caption: Different caption styles
#    - hashtags: Different hashtag strategies
#    - post_time: Different posting times
#    - cover_style: Different cover image styles
#
# Author: Kim Young-Hyun (Senior Designer)
# Date: 2026-01-30
# ============================================================
"""

import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Literal
from dataclasses import dataclass, field, asdict
from enum import Enum
import statistics


class TestStatus(str, Enum):
    """A/B Test Status"""
    DRAFT = "draft"           # Test planned but not started
    RUNNING = "running"       # Test in progress
    COMPLETED = "completed"   # Test completed, winner determined
    CANCELLED = "cancelled"   # Test cancelled


class TestVariable(str, Enum):
    """Testable Variables"""
    CAPTION = "caption"
    HASHTAGS = "hashtags"
    POST_TIME = "post_time"
    COVER_STYLE = "cover_style"
    CTA_TEXT = "cta_text"
    EMOJI_STYLE = "emoji_style"


@dataclass
class VariantMetrics:
    """Performance metrics for a variant"""
    likes: int = 0
    comments: int = 0
    saves: int = 0
    reach: int = 0
    impressions: int = 0
    engagement_rate: float = 0.0

    def calculate_engagement_rate(self, followers: int = 1) -> float:
        """Calculate engagement rate"""
        if followers <= 0:
            followers = 1
        total_engagement = self.likes + self.comments + self.saves
        self.engagement_rate = (total_engagement / followers) * 100
        return self.engagement_rate

    def total_engagement(self) -> int:
        """Total engagement count"""
        return self.likes + self.comments + self.saves


@dataclass
class Variant:
    """A/B Test Variant"""
    variant_id: str                     # 'A' or 'B'
    post_id: Optional[str] = None       # Instagram post ID
    instagram_url: Optional[str] = None
    published_at: Optional[str] = None

    # Test variable values
    caption: Optional[str] = None
    hashtags: Optional[List[str]] = None
    post_time: Optional[str] = None     # HH:MM format
    cover_style: Optional[str] = None

    # Performance metrics
    metrics: VariantMetrics = field(default_factory=VariantMetrics)

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ABTest:
    """A/B Test Definition"""
    test_id: str                        # Unique test ID (e.g., ab_strawberry_001)
    topic_en: str                       # Topic in English
    topic_kr: str                       # Topic in Korean

    # Test configuration
    variable: TestVariable              # What we're testing
    hypothesis: str                     # What we expect to learn

    # Variants
    variant_a: Variant = field(default_factory=lambda: Variant(variant_id='A'))
    variant_b: Variant = field(default_factory=lambda: Variant(variant_id='B'))

    # Test period
    start_date: Optional[str] = None    # ISO format
    end_date: Optional[str] = None      # ISO format
    duration_days: int = 7              # Test duration in days

    # Status and results
    status: TestStatus = TestStatus.DRAFT
    winner: Optional[str] = None        # 'A', 'B', or 'tie'
    confidence_level: float = 0.0       # Statistical confidence

    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""


class ABTestManager:
    """
    A/B Test Manager for Instagram Contents

    Features:
        - Create and manage A/B tests
        - Track variant performance
        - Auto-determine winner
        - Generate reports

    Usage:
        manager = ABTestManager()

        # Create test
        test = manager.create_test(
            topic_en='strawberry',
            topic_kr='딸기',
            variable=TestVariable.CAPTION,
            hypothesis='Emoji-rich captions get more engagement'
        )

        # Register variants
        manager.register_variant(test.test_id, 'A', post_id='123', caption='Short caption')
        manager.register_variant(test.test_id, 'B', post_id='456', caption='Long detailed caption')

        # Update metrics
        manager.update_metrics(test.test_id, 'A', likes=50, comments=10)
        manager.update_metrics(test.test_id, 'B', likes=30, comments=5)

        # Check winner
        result = manager.determine_winner(test.test_id)
    """

    def __init__(self, data_path: Optional[str] = None):
        """
        Initialize ABTestManager

        Args:
            data_path: Path to ab_tests.json (default: config/data/ab_tests.json)
        """
        if data_path:
            self.data_path = Path(data_path)
        else:
            project_root = Path(__file__).parent.parent.parent
            self.data_path = project_root / "config" / "data" / "ab_tests.json"

        # Ensure directory exists
        self.data_path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing tests
        self.tests: Dict[str, ABTest] = {}
        self._load_tests()

    def _load_tests(self) -> None:
        """Load tests from JSON file"""
        if self.data_path.exists():
            try:
                with open(self.data_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                for test_id, test_data in data.get('tests', {}).items():
                    self.tests[test_id] = self._dict_to_test(test_data)

            except (json.JSONDecodeError, Exception) as e:
                print(f"Warning: Failed to load AB tests: {e}")
                self.tests = {}

    def _save_tests(self) -> None:
        """Save tests to JSON file"""
        data = {
            'tests': {
                test_id: self._test_to_dict(test)
                for test_id, test in self.tests.items()
            },
            'last_updated': datetime.now().isoformat()
        }

        with open(self.data_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _test_to_dict(self, test: ABTest) -> Dict:
        """Convert ABTest to dict for JSON serialization"""
        return {
            'test_id': test.test_id,
            'topic_en': test.topic_en,
            'topic_kr': test.topic_kr,
            'variable': test.variable.value if isinstance(test.variable, TestVariable) else test.variable,
            'hypothesis': test.hypothesis,
            'variant_a': self._variant_to_dict(test.variant_a),
            'variant_b': self._variant_to_dict(test.variant_b),
            'start_date': test.start_date,
            'end_date': test.end_date,
            'duration_days': test.duration_days,
            'status': test.status.value if isinstance(test.status, TestStatus) else test.status,
            'winner': test.winner,
            'confidence_level': test.confidence_level,
            'created_at': test.created_at,
            'updated_at': test.updated_at,
            'notes': test.notes
        }

    def _variant_to_dict(self, variant: Variant) -> Dict:
        """Convert Variant to dict"""
        return {
            'variant_id': variant.variant_id,
            'post_id': variant.post_id,
            'instagram_url': variant.instagram_url,
            'published_at': variant.published_at,
            'caption': variant.caption,
            'hashtags': variant.hashtags,
            'post_time': variant.post_time,
            'cover_style': variant.cover_style,
            'metrics': {
                'likes': variant.metrics.likes,
                'comments': variant.metrics.comments,
                'saves': variant.metrics.saves,
                'reach': variant.metrics.reach,
                'impressions': variant.metrics.impressions,
                'engagement_rate': variant.metrics.engagement_rate
            },
            'metadata': variant.metadata
        }

    def _dict_to_test(self, data: Dict) -> ABTest:
        """Convert dict to ABTest"""
        test = ABTest(
            test_id=data['test_id'],
            topic_en=data['topic_en'],
            topic_kr=data['topic_kr'],
            variable=TestVariable(data['variable']),
            hypothesis=data['hypothesis'],
            start_date=data.get('start_date'),
            end_date=data.get('end_date'),
            duration_days=data.get('duration_days', 7),
            status=TestStatus(data.get('status', 'draft')),
            winner=data.get('winner'),
            confidence_level=data.get('confidence_level', 0.0),
            created_at=data.get('created_at', datetime.now().isoformat()),
            updated_at=data.get('updated_at', datetime.now().isoformat()),
            notes=data.get('notes', '')
        )

        # Load variants
        if 'variant_a' in data:
            test.variant_a = self._dict_to_variant(data['variant_a'])
        if 'variant_b' in data:
            test.variant_b = self._dict_to_variant(data['variant_b'])

        return test

    def _dict_to_variant(self, data: Dict) -> Variant:
        """Convert dict to Variant"""
        metrics_data = data.get('metrics', {})
        metrics = VariantMetrics(
            likes=metrics_data.get('likes', 0),
            comments=metrics_data.get('comments', 0),
            saves=metrics_data.get('saves', 0),
            reach=metrics_data.get('reach', 0),
            impressions=metrics_data.get('impressions', 0),
            engagement_rate=metrics_data.get('engagement_rate', 0.0)
        )

        return Variant(
            variant_id=data.get('variant_id', 'A'),
            post_id=data.get('post_id'),
            instagram_url=data.get('instagram_url'),
            published_at=data.get('published_at'),
            caption=data.get('caption'),
            hashtags=data.get('hashtags'),
            post_time=data.get('post_time'),
            cover_style=data.get('cover_style'),
            metrics=metrics,
            metadata=data.get('metadata', {})
        )

    def _generate_test_id(self, topic_en: str) -> str:
        """Generate unique test ID"""
        existing = [t for t in self.tests.keys() if t.startswith(f"ab_{topic_en}_")]
        next_num = len(existing) + 1
        return f"ab_{topic_en}_{next_num:03d}"

    # ============================================================
    # Test Management
    # ============================================================

    def create_test(
        self,
        topic_en: str,
        topic_kr: str,
        variable: TestVariable,
        hypothesis: str,
        duration_days: int = 7,
        notes: str = ""
    ) -> ABTest:
        """
        Create a new A/B test

        Args:
            topic_en: English topic name
            topic_kr: Korean topic name
            variable: What variable to test
            hypothesis: Expected outcome
            duration_days: Test duration (default 7)
            notes: Additional notes

        Returns:
            Created ABTest object
        """
        test_id = self._generate_test_id(topic_en)

        test = ABTest(
            test_id=test_id,
            topic_en=topic_en,
            topic_kr=topic_kr,
            variable=variable,
            hypothesis=hypothesis,
            duration_days=duration_days,
            notes=notes
        )

        self.tests[test_id] = test
        self._save_tests()

        print(f"[ABTest] Created: {test_id}")
        print(f"  Topic: {topic_kr} ({topic_en})")
        print(f"  Variable: {variable.value}")
        print(f"  Hypothesis: {hypothesis}")

        return test

    def get_test(self, test_id: str) -> Optional[ABTest]:
        """Get test by ID"""
        return self.tests.get(test_id)

    def list_tests(
        self,
        status: Optional[TestStatus] = None,
        topic_en: Optional[str] = None
    ) -> List[ABTest]:
        """
        List tests with optional filters

        Args:
            status: Filter by status
            topic_en: Filter by topic

        Returns:
            List of matching tests
        """
        result = list(self.tests.values())

        if status:
            result = [t for t in result if t.status == status]

        if topic_en:
            result = [t for t in result if t.topic_en == topic_en]

        return sorted(result, key=lambda t: t.created_at, reverse=True)

    def delete_test(self, test_id: str) -> bool:
        """Delete a test"""
        if test_id in self.tests:
            del self.tests[test_id]
            self._save_tests()
            print(f"[ABTest] Deleted: {test_id}")
            return True
        return False

    # ============================================================
    # Variant Registration
    # ============================================================

    def register_variant(
        self,
        test_id: str,
        variant_id: Literal['A', 'B'],
        post_id: str,
        instagram_url: Optional[str] = None,
        caption: Optional[str] = None,
        hashtags: Optional[List[str]] = None,
        post_time: Optional[str] = None,
        cover_style: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Register a published variant

        Args:
            test_id: Test ID
            variant_id: 'A' or 'B'
            post_id: Instagram post ID
            instagram_url: Post URL
            caption: Caption text (if testing caption)
            hashtags: Hashtag list (if testing hashtags)
            post_time: Post time HH:MM (if testing post time)
            cover_style: Cover style description (if testing cover)
            metadata: Additional metadata

        Returns:
            Success status
        """
        test = self.tests.get(test_id)
        if not test:
            print(f"[ABTest] Test not found: {test_id}")
            return False

        variant = Variant(
            variant_id=variant_id,
            post_id=post_id,
            instagram_url=instagram_url,
            published_at=datetime.now().isoformat(),
            caption=caption,
            hashtags=hashtags,
            post_time=post_time,
            cover_style=cover_style,
            metadata=metadata or {}
        )

        if variant_id == 'A':
            test.variant_a = variant
        else:
            test.variant_b = variant

        # Check if both variants are registered to start test
        if test.variant_a.post_id and test.variant_b.post_id:
            if test.status == TestStatus.DRAFT:
                test.status = TestStatus.RUNNING
                test.start_date = datetime.now().isoformat()
                test.end_date = (datetime.now() + timedelta(days=test.duration_days)).isoformat()
                print(f"[ABTest] Test started: {test_id}")

        test.updated_at = datetime.now().isoformat()
        self._save_tests()

        print(f"[ABTest] Registered variant {variant_id} for {test_id}")
        return True

    # ============================================================
    # Metrics Update
    # ============================================================

    def update_metrics(
        self,
        test_id: str,
        variant_id: Literal['A', 'B'],
        likes: Optional[int] = None,
        comments: Optional[int] = None,
        saves: Optional[int] = None,
        reach: Optional[int] = None,
        impressions: Optional[int] = None,
        followers: int = 1
    ) -> bool:
        """
        Update variant metrics

        Args:
            test_id: Test ID
            variant_id: 'A' or 'B'
            likes: Like count
            comments: Comment count
            saves: Save count
            reach: Reach count
            impressions: Impression count
            followers: Current follower count (for engagement rate)

        Returns:
            Success status
        """
        test = self.tests.get(test_id)
        if not test:
            return False

        variant = test.variant_a if variant_id == 'A' else test.variant_b

        if likes is not None:
            variant.metrics.likes = likes
        if comments is not None:
            variant.metrics.comments = comments
        if saves is not None:
            variant.metrics.saves = saves
        if reach is not None:
            variant.metrics.reach = reach
        if impressions is not None:
            variant.metrics.impressions = impressions

        variant.metrics.calculate_engagement_rate(followers)
        test.updated_at = datetime.now().isoformat()

        self._save_tests()
        return True

    def sync_from_instagram_stats(
        self,
        test_id: str,
        stats_path: Optional[str] = None
    ) -> bool:
        """
        Sync metrics from instagram_stats.json

        Args:
            test_id: Test ID
            stats_path: Path to instagram_stats.json

        Returns:
            Success status
        """
        test = self.tests.get(test_id)
        if not test:
            return False

        if not stats_path:
            project_root = Path(__file__).parent.parent.parent
            stats_path = project_root / "config" / "data" / "instagram_stats.json"

        try:
            with open(stats_path, 'r', encoding='utf-8') as f:
                stats = json.load(f)

            posts = stats.get('posts', {})
            followers = stats.get('account', {}).get('followers', 1)

            # Update variant A
            if test.variant_a.post_id and test.variant_a.post_id in posts:
                post_data = posts[test.variant_a.post_id]
                self.update_metrics(
                    test_id, 'A',
                    likes=post_data.get('likes', 0),
                    comments=post_data.get('comments', 0),
                    followers=followers
                )

            # Update variant B
            if test.variant_b.post_id and test.variant_b.post_id in posts:
                post_data = posts[test.variant_b.post_id]
                self.update_metrics(
                    test_id, 'B',
                    likes=post_data.get('likes', 0),
                    comments=post_data.get('comments', 0),
                    followers=followers
                )

            print(f"[ABTest] Synced metrics for {test_id}")
            return True

        except Exception as e:
            print(f"[ABTest] Sync failed: {e}")
            return False

    # ============================================================
    # Winner Determination
    # ============================================================

    def determine_winner(
        self,
        test_id: str,
        force: bool = False
    ) -> Optional[Dict]:
        """
        Determine test winner

        Args:
            test_id: Test ID
            force: Force determination even if test not ended

        Returns:
            Result dict with winner and analysis
        """
        test = self.tests.get(test_id)
        if not test:
            return None

        # Check if test period ended
        if not force and test.end_date:
            end_dt = datetime.fromisoformat(test.end_date)
            if datetime.now() < end_dt:
                remaining = (end_dt - datetime.now()).days
                return {
                    'status': 'running',
                    'message': f'Test still running. {remaining} days remaining.',
                    'test_id': test_id
                }

        # Calculate scores
        a_engagement = test.variant_a.metrics.total_engagement()
        b_engagement = test.variant_b.metrics.total_engagement()

        a_rate = test.variant_a.metrics.engagement_rate
        b_rate = test.variant_b.metrics.engagement_rate

        # Determine winner
        if a_engagement == b_engagement:
            winner = 'tie'
            confidence = 0.0
        elif a_engagement > b_engagement:
            winner = 'A'
            if b_engagement > 0:
                confidence = min(100, ((a_engagement - b_engagement) / b_engagement) * 100)
            else:
                confidence = 100.0
        else:
            winner = 'B'
            if a_engagement > 0:
                confidence = min(100, ((b_engagement - a_engagement) / a_engagement) * 100)
            else:
                confidence = 100.0

        # Update test
        test.winner = winner
        test.confidence_level = round(confidence, 2)
        test.status = TestStatus.COMPLETED
        test.updated_at = datetime.now().isoformat()

        self._save_tests()

        result = {
            'status': 'completed',
            'test_id': test_id,
            'topic': f"{test.topic_kr} ({test.topic_en})",
            'variable': test.variable.value,
            'winner': winner,
            'confidence': f"{confidence:.1f}%",
            'variant_a': {
                'engagement': a_engagement,
                'rate': f"{a_rate:.2f}%",
                'likes': test.variant_a.metrics.likes,
                'comments': test.variant_a.metrics.comments,
                'saves': test.variant_a.metrics.saves
            },
            'variant_b': {
                'engagement': b_engagement,
                'rate': f"{b_rate:.2f}%",
                'likes': test.variant_b.metrics.likes,
                'comments': test.variant_b.metrics.comments,
                'saves': test.variant_b.metrics.saves
            },
            'recommendation': self._generate_recommendation(test, winner)
        }

        return result

    def _generate_recommendation(self, test: ABTest, winner: str) -> str:
        """Generate actionable recommendation"""
        if winner == 'tie':
            return f"No significant difference in {test.variable.value}. Consider testing other variables."

        winning_variant = test.variant_a if winner == 'A' else test.variant_b

        recommendations = {
            TestVariable.CAPTION: f"Use {'shorter' if len(winning_variant.caption or '') < 100 else 'longer'} caption style for future posts.",
            TestVariable.HASHTAGS: f"Use hashtag set: {', '.join((winning_variant.hashtags or [])[:3])}...",
            TestVariable.POST_TIME: f"Optimal posting time: {winning_variant.post_time or 'N/A'}",
            TestVariable.COVER_STYLE: f"Preferred cover style: {winning_variant.cover_style or 'N/A'}",
            TestVariable.CTA_TEXT: "Apply winning CTA pattern to future content.",
            TestVariable.EMOJI_STYLE: f"{'Emoji-rich' if winning_variant.metadata.get('emoji_count', 0) > 5 else 'Minimal emoji'} style performs better."
        }

        return recommendations.get(test.variable, "Apply winning variant strategy to future content.")

    # ============================================================
    # Auto-Check Running Tests
    # ============================================================

    def check_completed_tests(self) -> List[Dict]:
        """
        Check all running tests and determine winners for completed ones

        Returns:
            List of completed test results
        """
        results = []

        for test in self.tests.values():
            if test.status == TestStatus.RUNNING:
                if test.end_date:
                    end_dt = datetime.fromisoformat(test.end_date)
                    if datetime.now() >= end_dt:
                        result = self.determine_winner(test.test_id)
                        if result and result.get('status') == 'completed':
                            results.append(result)

        if results:
            print(f"[ABTest] Auto-completed {len(results)} test(s)")

        return results

    # ============================================================
    # Reports
    # ============================================================

    def generate_report(self, test_id: str) -> str:
        """
        Generate detailed test report

        Args:
            test_id: Test ID

        Returns:
            Formatted report string
        """
        test = self.tests.get(test_id)
        if not test:
            return f"Test not found: {test_id}"

        # Build report
        lines = [
            "=" * 60,
            f"A/B TEST REPORT: {test_id}",
            "=" * 60,
            "",
            f"Topic: {test.topic_kr} ({test.topic_en})",
            f"Variable Tested: {test.variable.value}",
            f"Hypothesis: {test.hypothesis}",
            "",
            f"Status: {test.status.value.upper()}",
            f"Duration: {test.duration_days} days",
            f"Start: {test.start_date or 'Not started'}",
            f"End: {test.end_date or 'Not set'}",
            "",
            "-" * 60,
            "VARIANT A",
            "-" * 60,
            f"  Post ID: {test.variant_a.post_id or 'Not published'}",
            f"  URL: {test.variant_a.instagram_url or 'N/A'}",
            f"  Published: {test.variant_a.published_at or 'N/A'}",
            "",
            f"  Likes: {test.variant_a.metrics.likes}",
            f"  Comments: {test.variant_a.metrics.comments}",
            f"  Saves: {test.variant_a.metrics.saves}",
            f"  Total Engagement: {test.variant_a.metrics.total_engagement()}",
            f"  Engagement Rate: {test.variant_a.metrics.engagement_rate:.2f}%",
            "",
            "-" * 60,
            "VARIANT B",
            "-" * 60,
            f"  Post ID: {test.variant_b.post_id or 'Not published'}",
            f"  URL: {test.variant_b.instagram_url or 'N/A'}",
            f"  Published: {test.variant_b.published_at or 'N/A'}",
            "",
            f"  Likes: {test.variant_b.metrics.likes}",
            f"  Comments: {test.variant_b.metrics.comments}",
            f"  Saves: {test.variant_b.metrics.saves}",
            f"  Total Engagement: {test.variant_b.metrics.total_engagement()}",
            f"  Engagement Rate: {test.variant_b.metrics.engagement_rate:.2f}%",
            "",
        ]

        if test.status == TestStatus.COMPLETED:
            lines.extend([
                "=" * 60,
                "RESULT",
                "=" * 60,
                f"  Winner: Variant {test.winner}",
                f"  Confidence: {test.confidence_level:.1f}%",
                "",
                f"  Recommendation: {self._generate_recommendation(test, test.winner)}",
                "",
            ])

        lines.extend([
            "-" * 60,
            f"Created: {test.created_at}",
            f"Last Updated: {test.updated_at}",
            f"Notes: {test.notes or 'None'}",
            "=" * 60,
        ])

        return "\n".join(lines)

    def generate_summary_report(self) -> str:
        """Generate summary of all tests"""
        tests = list(self.tests.values())

        if not tests:
            return "No A/B tests found."

        completed = [t for t in tests if t.status == TestStatus.COMPLETED]
        running = [t for t in tests if t.status == TestStatus.RUNNING]
        draft = [t for t in tests if t.status == TestStatus.DRAFT]

        lines = [
            "=" * 60,
            "A/B TEST SUMMARY",
            "=" * 60,
            "",
            f"Total Tests: {len(tests)}",
            f"  - Completed: {len(completed)}",
            f"  - Running: {len(running)}",
            f"  - Draft: {len(draft)}",
            "",
        ]

        if completed:
            lines.extend([
                "-" * 60,
                "COMPLETED TESTS",
                "-" * 60,
            ])
            for test in completed:
                a_eng = test.variant_a.metrics.total_engagement()
                b_eng = test.variant_b.metrics.total_engagement()
                lines.append(
                    f"  [{test.test_id}] {test.topic_kr} ({test.variable.value})"
                )
                lines.append(
                    f"    Winner: {test.winner} | A:{a_eng} vs B:{b_eng} | Confidence: {test.confidence_level:.1f}%"
                )
            lines.append("")

        if running:
            lines.extend([
                "-" * 60,
                "RUNNING TESTS",
                "-" * 60,
            ])
            for test in running:
                if test.end_date:
                    end_dt = datetime.fromisoformat(test.end_date)
                    remaining = (end_dt - datetime.now()).days
                    remaining_str = f"{remaining} days left"
                else:
                    remaining_str = "No end date"
                lines.append(
                    f"  [{test.test_id}] {test.topic_kr} ({test.variable.value}) - {remaining_str}"
                )
            lines.append("")

        lines.append("=" * 60)

        return "\n".join(lines)

    def get_stats(self) -> Dict:
        """Get test statistics"""
        tests = list(self.tests.values())

        completed = [t for t in tests if t.status == TestStatus.COMPLETED]
        a_wins = len([t for t in completed if t.winner == 'A'])
        b_wins = len([t for t in completed if t.winner == 'B'])
        ties = len([t for t in completed if t.winner == 'tie'])

        # Variable breakdown
        variable_counts = {}
        for test in tests:
            var = test.variable.value
            variable_counts[var] = variable_counts.get(var, 0) + 1

        return {
            'total': len(tests),
            'completed': len(completed),
            'running': len([t for t in tests if t.status == TestStatus.RUNNING]),
            'draft': len([t for t in tests if t.status == TestStatus.DRAFT]),
            'a_wins': a_wins,
            'b_wins': b_wins,
            'ties': ties,
            'by_variable': variable_counts
        }


# ============================================================
# Convenience Functions
# ============================================================

def create_ab_test(
    topic_en: str,
    topic_kr: str,
    variable: str,
    hypothesis: str,
    duration_days: int = 7
) -> ABTest:
    """
    Convenience function to create A/B test

    Args:
        topic_en: English topic name
        topic_kr: Korean topic name
        variable: Variable to test (caption, hashtags, post_time, cover_style)
        hypothesis: What you expect to learn
        duration_days: Test duration

    Returns:
        Created ABTest
    """
    manager = ABTestManager()
    return manager.create_test(
        topic_en=topic_en,
        topic_kr=topic_kr,
        variable=TestVariable(variable),
        hypothesis=hypothesis,
        duration_days=duration_days
    )


def get_test_status(test_id: str) -> Optional[Dict]:
    """Get test status and metrics"""
    manager = ABTestManager()
    test = manager.get_test(test_id)

    if not test:
        return None

    return {
        'test_id': test.test_id,
        'topic': f"{test.topic_kr} ({test.topic_en})",
        'status': test.status.value,
        'variable': test.variable.value,
        'variant_a': {
            'engagement': test.variant_a.metrics.total_engagement(),
            'post_id': test.variant_a.post_id
        },
        'variant_b': {
            'engagement': test.variant_b.metrics.total_engagement(),
            'post_id': test.variant_b.post_id
        },
        'winner': test.winner,
        'end_date': test.end_date
    }


def check_and_complete_tests() -> List[Dict]:
    """Check all running tests and complete those past end date"""
    manager = ABTestManager()
    return manager.check_completed_tests()


# ============================================================
# CLI / Test
# ============================================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("A/B Test Manager - Test Run")
    print("=" * 60)

    manager = ABTestManager()

    # Create sample test
    test = manager.create_test(
        topic_en='strawberry',
        topic_kr='딸기',
        variable=TestVariable.CAPTION,
        hypothesis='Emoji-rich captions get 20% more engagement',
        duration_days=7,
        notes='Testing caption style impact'
    )

    # Register variants
    manager.register_variant(
        test.test_id, 'A',
        post_id='test_post_a_123',
        instagram_url='https://instagram.com/p/abc123',
        caption='Short and simple caption without many emojis.'
    )

    manager.register_variant(
        test.test_id, 'B',
        post_id='test_post_b_456',
        instagram_url='https://instagram.com/p/def456',
        caption='Emoji-rich caption with lots of emojis and excitement!'
    )

    # Simulate metrics
    manager.update_metrics(test.test_id, 'A', likes=45, comments=8, saves=12, followers=100)
    manager.update_metrics(test.test_id, 'B', likes=62, comments=15, saves=28, followers=100)

    # Determine winner (force for demo)
    result = manager.determine_winner(test.test_id, force=True)

    # Print report
    print("\n" + manager.generate_report(test.test_id))

    # Print summary
    print("\n" + manager.generate_summary_report())

    # Stats
    stats = manager.get_stats()
    print(f"\nStats: {stats}")

    # Cleanup demo test
    manager.delete_test(test.test_id)
    print("\n(Demo test cleaned up)")
