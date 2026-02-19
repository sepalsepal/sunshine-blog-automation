"""
SunFlow Metrics Collector
- 30일 실운영 리포트용 자동 데이터 수집
- 헬스체크, 게시 현황, Instagram 통계, 비용 집계
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum

# 프로젝트 루트
PROJECT_ROOT = Path(__file__).parent.parent.parent


class MetricType(Enum):
    """메트릭 유형"""
    UPTIME = "uptime"
    PUBLISH = "publish"
    ENGAGEMENT = "engagement"
    COST = "cost"
    ERROR = "error"
    QUALITY_GATE = "quality_gate"


@dataclass
class DailyMetrics:
    """일간 메트릭"""
    date: str
    # 가동률
    health_checks_total: int = 0
    health_checks_success: int = 0
    health_checks_fail: int = 0
    uptime_percent: float = 0.0
    # 서킷 브레이커
    circuit_open_count: int = 0
    circuit_recovery_time_avg: float = 0.0
    # 게시
    publish_attempts: int = 0
    publish_success: int = 0
    publish_fail: int = 0
    retry_count: int = 0
    # Instagram
    followers: int = 0
    likes: int = 0
    comments: int = 0
    saves: int = 0
    shares: int = 0
    engagement_rate: float = 0.0
    # 비용
    fal_ai_calls: int = 0
    fal_ai_cost: float = 0.0
    cloudinary_calls: int = 0
    # 에러
    errors_total: int = 0
    errors_p0: int = 0
    errors_p1: int = 0
    errors_p2: int = 0
    errors_p3: int = 0
    # 품질 게이트
    g1_pass: int = 0
    g1_fail: int = 0
    g2_pass: int = 0
    g2_fail: int = 0
    g3_pass: int = 0
    g3_fail: int = 0


@dataclass
class WeeklyMetrics:
    """주간 메트릭 (집계용)"""
    week_number: int
    start_date: str
    end_date: str
    # 집계
    uptime_avg: float = 0.0
    publish_success_rate: float = 0.0
    engagement_avg: float = 0.0
    follower_start: int = 0
    follower_end: int = 0
    follower_change: int = 0
    total_cost: float = 0.0
    error_count: int = 0


@dataclass
class MonthlyReport:
    """월간 리포트 데이터"""
    period_start: str
    period_end: str
    report_date: str
    # 전체 요약
    total_uptime: float = 0.0
    total_publish_success_rate: float = 0.0
    avg_engagement: float = 0.0
    follower_growth: int = 0
    total_cost: float = 0.0
    cost_per_content: float = 0.0
    # 주간 데이터
    weekly_data: List[WeeklyMetrics] = field(default_factory=list)
    # 일간 데이터
    daily_data: List[DailyMetrics] = field(default_factory=list)
    # 콘텐츠 TOP 5
    top_content: List[Dict] = field(default_factory=list)
    # 에러 분석
    error_summary: Dict = field(default_factory=dict)
    # 권장사항
    recommendations: List[str] = field(default_factory=list)


class MetricsCollector:
    """메트릭 수집기"""

    def __init__(self):
        self.data_dir = PROJECT_ROOT / "config" / "data"
        self.metrics_file = self.data_dir / "daily_metrics.json"
        self.report_dir = PROJECT_ROOT / "reports"
        self._ensure_dirs()
        self._load_metrics()

    def _ensure_dirs(self):
        """디렉토리 생성"""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.report_dir.mkdir(parents=True, exist_ok=True)

    def _load_metrics(self):
        """저장된 메트릭 로드"""
        if self.metrics_file.exists():
            with open(self.metrics_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.metrics = {
                    d['date']: DailyMetrics(**d)
                    for d in data.get('daily', [])
                }
        else:
            self.metrics = {}

    def _save_metrics(self):
        """메트릭 저장"""
        data = {
            'daily': [asdict(m) for m in self.metrics.values()],
            'last_updated': datetime.now().isoformat()
        }
        with open(self.metrics_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_or_create_daily(self, date: str = None) -> DailyMetrics:
        """일간 메트릭 조회 또는 생성"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        if date not in self.metrics:
            self.metrics[date] = DailyMetrics(date=date)

        return self.metrics[date]

    # ===== 수집 메서드 =====

    def record_health_check(self, success: bool):
        """헬스체크 기록"""
        daily = self.get_or_create_daily()
        daily.health_checks_total += 1
        if success:
            daily.health_checks_success += 1
        else:
            daily.health_checks_fail += 1

        # 가동률 계산
        if daily.health_checks_total > 0:
            daily.uptime_percent = (
                daily.health_checks_success / daily.health_checks_total * 100
            )

        self._save_metrics()

    def record_circuit_event(self, circuit_name: str, recovery_time: float = None):
        """서킷 브레이커 이벤트 기록"""
        daily = self.get_or_create_daily()
        daily.circuit_open_count += 1

        if recovery_time:
            # 이동 평균 계산
            if daily.circuit_recovery_time_avg == 0:
                daily.circuit_recovery_time_avg = recovery_time
            else:
                daily.circuit_recovery_time_avg = (
                    daily.circuit_recovery_time_avg + recovery_time
                ) / 2

        self._save_metrics()

    def record_publish(self, success: bool, retry_count: int = 0):
        """게시 결과 기록"""
        daily = self.get_or_create_daily()
        daily.publish_attempts += 1

        if success:
            daily.publish_success += 1
        else:
            daily.publish_fail += 1

        daily.retry_count += retry_count
        self._save_metrics()

    def record_instagram_stats(
        self,
        followers: int,
        likes: int = 0,
        comments: int = 0,
        saves: int = 0,
        shares: int = 0
    ):
        """Instagram 통계 기록"""
        daily = self.get_or_create_daily()
        daily.followers = followers
        daily.likes = likes
        daily.comments = comments
        daily.saves = saves
        daily.shares = shares

        # 참여율 계산
        if followers > 0:
            total_engagement = likes + comments + saves + shares
            daily.engagement_rate = total_engagement / followers * 100

        self._save_metrics()

    def record_api_cost(self, service: str, calls: int, cost: float):
        """API 비용 기록"""
        daily = self.get_or_create_daily()

        if service == 'fal_ai':
            daily.fal_ai_calls += calls
            daily.fal_ai_cost += cost
        elif service == 'cloudinary':
            daily.cloudinary_calls += calls

        self._save_metrics()

    def record_error(self, severity: str):
        """에러 기록"""
        daily = self.get_or_create_daily()
        daily.errors_total += 1

        if severity == 'P0':
            daily.errors_p0 += 1
        elif severity == 'P1':
            daily.errors_p1 += 1
        elif severity == 'P2':
            daily.errors_p2 += 1
        else:
            daily.errors_p3 += 1

        self._save_metrics()

    def record_quality_gate(self, gate: str, passed: bool):
        """품질 게이트 기록"""
        daily = self.get_or_create_daily()

        if gate == 'G1':
            if passed:
                daily.g1_pass += 1
            else:
                daily.g1_fail += 1
        elif gate == 'G2':
            if passed:
                daily.g2_pass += 1
            else:
                daily.g2_fail += 1
        elif gate == 'G3':
            if passed:
                daily.g3_pass += 1
            else:
                daily.g3_fail += 1

        self._save_metrics()

    # ===== 집계 메서드 =====

    def get_weekly_metrics(self, week_start: str, week_end: str, week_num: int) -> WeeklyMetrics:
        """주간 메트릭 집계"""
        weekly = WeeklyMetrics(
            week_number=week_num,
            start_date=week_start,
            end_date=week_end
        )

        # 해당 주의 일간 데이터 수집
        daily_list = []
        current = datetime.strptime(week_start, '%Y-%m-%d')
        end = datetime.strptime(week_end, '%Y-%m-%d')

        while current <= end:
            date_str = current.strftime('%Y-%m-%d')
            if date_str in self.metrics:
                daily_list.append(self.metrics[date_str])
            current += timedelta(days=1)

        if not daily_list:
            return weekly

        # 집계
        weekly.uptime_avg = sum(d.uptime_percent for d in daily_list) / len(daily_list)

        total_attempts = sum(d.publish_attempts for d in daily_list)
        total_success = sum(d.publish_success for d in daily_list)
        if total_attempts > 0:
            weekly.publish_success_rate = total_success / total_attempts * 100

        weekly.engagement_avg = sum(d.engagement_rate for d in daily_list) / len(daily_list)

        weekly.follower_start = daily_list[0].followers
        weekly.follower_end = daily_list[-1].followers
        weekly.follower_change = weekly.follower_end - weekly.follower_start

        weekly.total_cost = sum(d.fal_ai_cost for d in daily_list)
        weekly.error_count = sum(d.errors_total for d in daily_list)

        return weekly

    def generate_monthly_report(self, days: int = 30) -> MonthlyReport:
        """월간 리포트 생성"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        report = MonthlyReport(
            period_start=start_date.strftime('%Y-%m-%d'),
            period_end=end_date.strftime('%Y-%m-%d'),
            report_date=datetime.now().strftime('%Y-%m-%d %H:%M')
        )

        # 일간 데이터 수집
        current = start_date
        while current <= end_date:
            date_str = current.strftime('%Y-%m-%d')
            if date_str in self.metrics:
                report.daily_data.append(self.metrics[date_str])
            current += timedelta(days=1)

        if not report.daily_data:
            return report

        # 주간 집계 (4주)
        for week_num in range(1, 5):
            week_start = start_date + timedelta(days=(week_num - 1) * 7)
            week_end = week_start + timedelta(days=6)
            if week_end > end_date:
                week_end = end_date

            weekly = self.get_weekly_metrics(
                week_start.strftime('%Y-%m-%d'),
                week_end.strftime('%Y-%m-%d'),
                week_num
            )
            report.weekly_data.append(weekly)

        # 전체 집계
        report.total_uptime = sum(d.uptime_percent for d in report.daily_data) / len(report.daily_data)

        total_attempts = sum(d.publish_attempts for d in report.daily_data)
        total_success = sum(d.publish_success for d in report.daily_data)
        if total_attempts > 0:
            report.total_publish_success_rate = total_success / total_attempts * 100

        report.avg_engagement = sum(d.engagement_rate for d in report.daily_data) / len(report.daily_data)

        if report.daily_data:
            report.follower_growth = report.daily_data[-1].followers - report.daily_data[0].followers

        report.total_cost = sum(d.fal_ai_cost for d in report.daily_data)

        total_content = sum(d.publish_success for d in report.daily_data)
        if total_content > 0:
            report.cost_per_content = report.total_cost / total_content

        # 에러 요약
        report.error_summary = {
            'total': sum(d.errors_total for d in report.daily_data),
            'p0': sum(d.errors_p0 for d in report.daily_data),
            'p1': sum(d.errors_p1 for d in report.daily_data),
            'p2': sum(d.errors_p2 for d in report.daily_data),
            'p3': sum(d.errors_p3 for d in report.daily_data)
        }

        # 권장사항 자동 생성
        report.recommendations = self._generate_recommendations(report)

        return report

    def _generate_recommendations(self, report: MonthlyReport) -> List[str]:
        """권장사항 자동 생성"""
        recs = []

        if report.total_uptime < 98:
            recs.append(f"가동률 개선 필요: 현재 {report.total_uptime:.1f}% → 목표 98%+")

        if report.total_publish_success_rate < 95:
            recs.append(f"게시 성공률 개선 필요: 현재 {report.total_publish_success_rate:.1f}% → 목표 95%+")

        if report.avg_engagement < 10:
            recs.append(f"참여율 개선 필요: 현재 {report.avg_engagement:.1f}% → 목표 10%+")

        if report.cost_per_content > 0.50:
            recs.append(f"비용 최적화 필요: 콘텐츠당 ${report.cost_per_content:.2f} → 목표 $0.50 이하")

        if report.error_summary.get('p0', 0) > 0:
            recs.append(f"P0 장애 발생: {report.error_summary['p0']}건 → 근본 원인 분석 필요")

        if not recs:
            recs.append("모든 지표 목표 달성 - 현재 상태 유지")

        return recs

    def save_report(self, report: MonthlyReport) -> str:
        """리포트 저장"""
        filename = f"report_{report.period_start}_{report.period_end}.json"
        filepath = self.report_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(asdict(report), f, ensure_ascii=False, indent=2)

        return str(filepath)

    def get_status(self) -> Dict:
        """현재 수집 상태"""
        total_days = len(self.metrics)

        if total_days == 0:
            return {
                'status': 'empty',
                'message': '수집된 데이터 없음',
                'total_days': 0
            }

        dates = sorted(self.metrics.keys())

        return {
            'status': 'active',
            'total_days': total_days,
            'first_date': dates[0],
            'last_date': dates[-1],
            'message': f'{total_days}일 데이터 수집됨 ({dates[0]} ~ {dates[-1]})'
        }


# 전역 인스턴스
_collector = None


def get_collector() -> MetricsCollector:
    """수집기 인스턴스 반환"""
    global _collector
    if _collector is None:
        _collector = MetricsCollector()
    return _collector


# ===== 편의 함수 =====

def record_health_check(success: bool):
    """헬스체크 기록"""
    get_collector().record_health_check(success)


def record_publish(success: bool, retry_count: int = 0):
    """게시 결과 기록"""
    get_collector().record_publish(success, retry_count)


def record_instagram_stats(**kwargs):
    """Instagram 통계 기록"""
    get_collector().record_instagram_stats(**kwargs)


def record_api_cost(service: str, calls: int, cost: float):
    """API 비용 기록"""
    get_collector().record_api_cost(service, calls, cost)


def record_error(severity: str):
    """에러 기록"""
    get_collector().record_error(severity)


def record_quality_gate(gate: str, passed: bool):
    """품질 게이트 기록"""
    get_collector().record_quality_gate(gate, passed)


# CLI
if __name__ == "__main__":
    import sys

    collector = get_collector()

    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == "status":
            status = collector.get_status()
            print(f"\n=== 메트릭 수집 상태 ===\n")
            print(f"  상태: {status['status']}")
            print(f"  메시지: {status['message']}")
            if status['total_days'] > 0:
                print(f"  기간: {status['first_date']} ~ {status['last_date']}")

        elif cmd == "report":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
            report = collector.generate_monthly_report(days)
            filepath = collector.save_report(report)
            print(f"\n=== 리포트 생성 완료 ===\n")
            print(f"  기간: {report.period_start} ~ {report.period_end}")
            print(f"  파일: {filepath}")
            print(f"\n  요약:")
            print(f"    가동률: {report.total_uptime:.1f}%")
            print(f"    게시 성공률: {report.total_publish_success_rate:.1f}%")
            print(f"    평균 참여율: {report.avg_engagement:.1f}%")
            print(f"    총 비용: ${report.total_cost:.2f}")

        elif cmd == "test":
            # 테스트 데이터 기록
            print("테스트 데이터 기록 중...")
            collector.record_health_check(True)
            collector.record_publish(True, retry_count=0)
            collector.record_instagram_stats(followers=1000, likes=150, comments=20, saves=30)
            collector.record_api_cost('fal_ai', 3, 0.15)
            collector.record_quality_gate('G1', True)
            collector.record_quality_gate('G2', True)
            print("완료!")

        else:
            print("Usage: python metrics_collector.py [status|report|test]")
    else:
        status = collector.get_status()
        print(f"메트릭 수집기: {status['message']}")
