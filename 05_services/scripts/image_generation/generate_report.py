#!/usr/bin/env python3
"""
SunFlow 30일 실운영 리포트 생성기
- 수집된 메트릭 기반 자동 리포트 생성
- Markdown 형식 출력
"""

import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

# 프로젝트 루트 추가
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.utils.metrics_collector import MetricsCollector, MonthlyReport


def generate_markdown_report(report: MonthlyReport) -> str:
    """리포트 데이터를 Markdown으로 변환"""

    # 상태 이모지 결정
    def status_emoji(value: float, target: float) -> str:
        if value >= target:
            return "✅"
        elif value >= target * 0.9:
            return "⚠️"
        else:
            return "❌"

    uptime_status = status_emoji(report.total_uptime, 98)
    publish_status = status_emoji(report.total_publish_success_rate, 95)
    engagement_status = status_emoji(report.avg_engagement, 10)

    # 전체 상태
    if uptime_status == "✅" and publish_status == "✅":
        overall_status = "✅ HEALTHY"
    elif "❌" in [uptime_status, publish_status]:
        overall_status = "❌ NEEDS ATTENTION"
    else:
        overall_status = "⚠️ DEGRADED"

    md = f"""# SunFlow 30일 실운영 리포트

> **기간:** {report.period_start} ~ {report.period_end}
> **작성일:** {report.report_date}
> **자동 생성:** metrics_collector.py

---

## Executive Summary

| 지표 | 목표 | 실제 | 상태 |
|------|:----:|:----:|:----:|
| 가동률 | 98%+ | {report.total_uptime:.1f}% | {uptime_status} |
| 게시 성공률 | 95%+ | {report.total_publish_success_rate:.1f}% | {publish_status} |
| 평균 참여율 | 10%+ | {report.avg_engagement:.1f}% | {engagement_status} |
| 팔로워 증가 | +500 | {report.follower_growth:+d} | {"✅" if report.follower_growth >= 500 else "⚠️"} |

**종합 판정:** {overall_status}

---

## 1. 시스템 안정성

### 1.1 주간 가동률

| 주차 | 가동률 | 게시 성공률 | 에러 수 |
|:----:|:------:|:----------:|:-------:|
"""

    # 주간 데이터 추가
    for weekly in report.weekly_data:
        md += f"| Week {weekly.week_number} | {weekly.uptime_avg:.1f}% | {weekly.publish_success_rate:.1f}% | {weekly.error_count} |\n"

    md += f"""
### 1.2 비용 분석

| 항목 | 값 |
|------|-----|
| 총 비용 | ${report.total_cost:.2f} |
| 제작 콘텐츠 수 | {sum(d.publish_success for d in report.daily_data)}개 |
| **콘텐츠당 비용** | **${report.cost_per_content:.2f}** |
| 목표 ($0.50 이하) | {"✅ 달성" if report.cost_per_content <= 0.50 else "❌ 초과"} |

---

## 2. 에러 분석

| 심각도 | 건수 | 비율 |
|:------:|:----:|:----:|
| P0 (치명) | {report.error_summary.get('p0', 0)} | {report.error_summary.get('p0', 0) / max(report.error_summary.get('total', 1), 1) * 100:.1f}% |
| P1 (높음) | {report.error_summary.get('p1', 0)} | {report.error_summary.get('p1', 0) / max(report.error_summary.get('total', 1), 1) * 100:.1f}% |
| P2 (중간) | {report.error_summary.get('p2', 0)} | {report.error_summary.get('p2', 0) / max(report.error_summary.get('total', 1), 1) * 100:.1f}% |
| P3 (낮음) | {report.error_summary.get('p3', 0)} | {report.error_summary.get('p3', 0) / max(report.error_summary.get('total', 1), 1) * 100:.1f}% |
| **총계** | **{report.error_summary.get('total', 0)}** | 100% |

---

## 3. 권장사항

"""
    for i, rec in enumerate(report.recommendations, 1):
        md += f"{i}. {rec}\n"

    md += f"""
---

## 4. 다음 30일 목표

| 항목 | 현재 | 목표 |
|------|:----:|:----:|
| 가동률 | {report.total_uptime:.1f}% | 98%+ |
| 게시 성공률 | {report.total_publish_success_rate:.1f}% | 98%+ |
| 참여율 | {report.avg_engagement:.1f}% | 12%+ |
| 콘텐츠당 비용 | ${report.cost_per_content:.2f} | $0.40 이하 |

---

*SunFlow 자동 생성 리포트*
*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""

    return md


def main():
    """메인 실행"""
    import argparse

    parser = argparse.ArgumentParser(description='SunFlow 30일 리포트 생성')
    parser.add_argument('--days', type=int, default=30, help='리포트 기간 (일)')
    parser.add_argument('--output', type=str, help='출력 파일 경로')
    parser.add_argument('--format', choices=['json', 'md'], default='md', help='출력 형식')

    args = parser.parse_args()

    # 수집기 초기화
    collector = MetricsCollector()

    # 상태 확인
    status = collector.get_status()
    if status['status'] == 'empty':
        print("⚠️ 수집된 데이터가 없습니다.")
        print("   먼저 메트릭 수집을 시작하세요:")
        print("   python3 core/utils/metrics_collector.py test")
        return

    # 리포트 생성
    report = collector.generate_monthly_report(args.days)

    # 출력
    if args.format == 'json':
        from dataclasses import asdict
        output = json.dumps(asdict(report), ensure_ascii=False, indent=2)
    else:
        output = generate_markdown_report(report)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"✅ 리포트 저장: {output_path}")
    else:
        print(output)


if __name__ == "__main__":
    main()
