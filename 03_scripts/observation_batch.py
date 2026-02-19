#!/usr/bin/env python3
"""
observation_batch.py - WO-OBSERVATION-BATCH 관찰 배치 실행
2026-02-12

모드: OBSERVATION_ONLY
대상: 10건 (SAFE 4, CAUTION 3, FORBIDDEN 3)
즉시 중단 조건:
  - override 1건
  - URL FAIL 2건+
  - BLOCKED 발생
  - Executor 예외
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.layers.generator import Generator
from pipeline.layers.validator import Validator
from pipeline.layers.executor import Executor
from pipeline.interfaces.layer_contract import (
    GeneratedContent,
    ValidationResult,
    ValidationStatus,
    ExecutionStatus,
    ContentStatus,
    PermissionDeniedError,
    ExecutionBlockedError,
    AutoBlockedError,
)


# ============================================================================
# 관찰 대상 정의
# ============================================================================

OBSERVATION_TARGETS = [
    # SAFE (4건)
    {"id": 1, "name": "호박", "safety": "SAFE"},
    {"id": 3, "name": "블루베리", "safety": "SAFE"},
    {"id": 5, "name": "고구마", "safety": "SAFE"},
    {"id": 6, "name": "사과", "safety": "SAFE"},
    # CAUTION (3건)
    {"id": 2, "name": "당근", "safety": "CAUTION"},
    {"id": 4, "name": "체리", "safety": "CAUTION"},
    {"id": 7, "name": "파인애플", "safety": "CAUTION"},
    # FORBIDDEN (3건)
    {"id": 20, "name": "프링글스", "safety": "FORBIDDEN"},
    {"id": 22, "name": "아보카도", "safety": "FORBIDDEN"},
    {"id": 23, "name": "콜라", "safety": "FORBIDDEN"},
]


# ============================================================================
# 즉시 중단 조건
# ============================================================================

class StopConditionTracker:
    """중단 조건 추적"""

    def __init__(self):
        self.override_count = 0
        self.url_fail_count = 0
        self.blocked_occurred = False
        self.executor_exception = False
        self.stop_reason: Optional[str] = None

    def record_override(self):
        self.override_count += 1
        if self.override_count >= 1:
            self.stop_reason = f"override 발생 ({self.override_count}건)"

    def record_url_fail(self):
        self.url_fail_count += 1
        if self.url_fail_count >= 2:
            self.stop_reason = f"URL FAIL 누적 ({self.url_fail_count}건)"

    def record_blocked(self, codes: List[str]):
        self.blocked_occurred = True
        self.stop_reason = f"BLOCKED 발생 (코드: {codes})"

    def record_executor_exception(self, error: str):
        self.executor_exception = True
        self.stop_reason = f"Executor 예외: {error}"

    def should_stop(self) -> bool:
        return self.stop_reason is not None

    def get_summary(self) -> Dict:
        return {
            "override_count": self.override_count,
            "url_fail_count": self.url_fail_count,
            "blocked_occurred": self.blocked_occurred,
            "executor_exception": self.executor_exception,
            "stop_reason": self.stop_reason
        }


# ============================================================================
# 샘플 캡션 생성 (테스트용)
# ============================================================================

def generate_sample_caption(food: Dict) -> str:
    """테스트용 샘플 캡션 생성"""
    name = food["name"]
    safety = food["safety"]

    if safety == "SAFE":
        return f"""[이미지 1번: 표지]
안녕하세요, 11살 골든리트리버 햇살이 엄마예요.
오늘은 {name}에 대해 알아볼게요.

[이미지 2번: 음식 사진]
{name}는 강아지에게 좋은 음식이에요.

[이미지 3번: 영양 정보]
영양 정보를 알려드릴게요. 비타민이 풍부해요.

[이미지 4번: 급여 방법]
급여 방법이에요. 잘 익혀서 주세요.

[이미지 5번: 급여량 표]
체중별 급여량이에요. 적당히 주세요.

[이미지 6번: 주의사항]
주의사항을 알려드릴게요.

[이미지 7번: 조리 방법]
조리 방법이에요.

[이미지 8번: 햇살이]
우리 햇살이도 좋아해요."""

    elif safety == "CAUTION":
        return f"""[이미지 1번: 표지]
안녕하세요, 11살 골든리트리버 햇살이 엄마예요.
오늘은 {name}에 대해 알아볼게요.

[이미지 2번: 음식 사진]
{name}는 주의가 필요한 음식이에요.

[이미지 3번: 주의사항]
주의사항을 먼저 알려드릴게요. 조심해야 해요.

[이미지 4번: 위험 요소]
위험 요소가 있어요. 꼭 확인하세요.

[이미지 5번: 급여 방법]
급여 방법이에요. 반드시 익혀서 주세요.

[이미지 6번: 급여량 표]
체중별 급여량이에요. 소량만 주세요.

[이미지 7번: 증상]
문제 시 나타나는 증상이에요.

[이미지 8번: 햇살이]
햇살이는 가끔만 먹어요."""

    else:  # FORBIDDEN
        return f"""[이미지 1번: 표지]
안녕하세요, 11살 골든리트리버 햇살이 엄마예요.
오늘은 {name}의 위험성을 알려드릴게요.

[이미지 2번: 경고]
{name}는 절대 금지예요! 정말 위험해요.

[이미지 3번: 독성 성분]
독성 성분이 있어요. 치명적이에요.

[이미지 4번: 위험 증상]
섭취 시 위험한 증상이 나타나요. 응급 상황이에요.

[이미지 5번: 응급 대처]
만약 먹었다면 즉시 병원에 가세요.

[이미지 6번: 주의사항]
절대 주지 마세요. 위험해요.

[이미지 7번: 대체 음식]
대신 이런 음식을 주세요.

[이미지 8번: 햇살이]
햇살이는 절대 먹지 않아요."""


# ============================================================================
# 관찰 배치 실행
# ============================================================================

class ObservationBatch:
    """관찰 배치 실행기"""

    def __init__(self):
        self.generator = Generator()
        self.validator = Validator()
        self.executor = Executor()
        self.tracker = StopConditionTracker()
        self.results: List[Dict] = []
        self.start_time = datetime.now()

    def run(self) -> Dict:
        """관찰 배치 실행"""
        print("=" * 60)
        print("WO-OBSERVATION-BATCH 관찰 배치 시작")
        print(f"시작 시간: {self.start_time.isoformat()}")
        print(f"대상: {len(OBSERVATION_TARGETS)}건")
        print("=" * 60)

        for idx, food in enumerate(OBSERVATION_TARGETS, 1):
            print(f"\n[{idx}/{len(OBSERVATION_TARGETS)}] {food['name']} (ID:{food['id']}, {food['safety']})")

            result = self._process_item(food)
            self.results.append(result)

            # 중단 조건 확인
            if self.tracker.should_stop():
                print(f"\n⚠️ 즉시 중단: {self.tracker.stop_reason}")
                break

        return self._generate_report()

    def _process_item(self, food: Dict) -> Dict:
        """개별 아이템 처리"""
        result = {
            "id": food["id"],
            "name": food["name"],
            "safety": food["safety"],
            "status": None,
            "score": None,
            "total": None,
            "fail_codes": [],
            "executed": False,
            "error": None
        }

        try:
            # 1. Generate (샘플 캡션)
            caption = generate_sample_caption(food)
            content = GeneratedContent(
                food_id=food["id"],
                food_name=food["name"],
                content_type="caption",
                content=caption,
                safety=food["safety"],
                status=ContentStatus.GENERATED
            )
            print(f"  → Generator: 완료")

            # 2. Validate
            validation = self.validator.validate(content)
            result["status"] = validation.status.value
            result["score"] = validation.score
            result["total"] = validation.total
            result["fail_codes"] = validation.fail_codes

            print(f"  → Validator: {validation.status.value} (총점: {validation.total}/20)")
            if validation.fail_codes:
                print(f"     코드: {validation.fail_codes}")

            # 중단 조건 체크: BLOCKED
            if validation.status == ValidationStatus.BLOCKED:
                self.tracker.record_blocked(validation.fail_codes)
                return result

            # 중단 조건 체크: FAIL + override 필요
            if validation.status == ValidationStatus.FAIL:
                if validation.allow_override:
                    # 관찰 모드에서는 override 시도 없이 기록만
                    print(f"     → override 가능 (관찰 모드: 시도 안 함)")
                return result

            # 3. Execute (PASS인 경우만)
            if validation.status == ValidationStatus.PASS:
                try:
                    execution = self.executor.execute(validation)
                    result["executed"] = (execution.status == ExecutionStatus.EXECUTED)
                    print(f"  → Executor: {execution.status.value}")
                except ExecutionBlockedError as e:
                    self.tracker.record_executor_exception(str(e))
                    result["error"] = str(e)
                except Exception as e:
                    self.tracker.record_executor_exception(str(e))
                    result["error"] = str(e)

        except PermissionDeniedError as e:
            result["error"] = f"PermissionDeniedError: {e}"
            print(f"  → 권한 오류: {e}")

        except Exception as e:
            result["error"] = str(e)
            print(f"  → 오류: {e}")

        return result

    def _generate_report(self) -> Dict:
        """결과 리포트 생성"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()

        # 통계 계산
        total = len(self.results)
        pass_count = sum(1 for r in self.results if r["status"] == "PASS")
        fail_count = sum(1 for r in self.results if r["status"] == "FAIL")
        blocked_count = sum(1 for r in self.results if r["status"] == "BLOCKED")
        executed_count = sum(1 for r in self.results if r["executed"])

        # Safety별 통계
        by_safety = {}
        for safety in ["SAFE", "CAUTION", "FORBIDDEN"]:
            items = [r for r in self.results if r["safety"] == safety]
            by_safety[safety] = {
                "total": len(items),
                "pass": sum(1 for r in items if r["status"] == "PASS"),
                "fail": sum(1 for r in items if r["status"] == "FAIL"),
                "blocked": sum(1 for r in items if r["status"] == "BLOCKED"),
            }

        report = {
            "work_order": "WO-OBSERVATION-BATCH",
            "mode": "OBSERVATION_ONLY",
            "timestamp": end_time.isoformat(),
            "duration_seconds": round(duration, 2),
            "planned": len(OBSERVATION_TARGETS),
            "processed": total,
            "completed": not self.tracker.should_stop(),
            "stop_conditions": self.tracker.get_summary(),
            "statistics": {
                "total": total,
                "pass": pass_count,
                "fail": fail_count,
                "blocked": blocked_count,
                "executed": executed_count,
                "pass_rate": f"{pass_count}/{total}" if total > 0 else "0/0"
            },
            "by_safety": by_safety,
            "results": self.results
        }

        return report


def save_report(report: Dict) -> Path:
    """리포트 저장"""
    log_dir = PROJECT_ROOT / "logs" / "observation_batch" / datetime.now().strftime("%Y%m%d")
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / "observation_results.json"
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    return log_file


def print_summary(report: Dict):
    """결과 요약 출력"""
    print("\n" + "=" * 60)
    print("WO-OBSERVATION-BATCH 결과 요약")
    print("=" * 60)

    stats = report["statistics"]
    print(f"\n처리 현황: {report['processed']}/{report['planned']}건")
    print(f"  - PASS:    {stats['pass']}건")
    print(f"  - FAIL:    {stats['fail']}건")
    print(f"  - BLOCKED: {stats['blocked']}건")
    print(f"  - 실행됨:  {stats['executed']}건")

    print(f"\nSafety별 현황:")
    for safety, data in report["by_safety"].items():
        print(f"  {safety}: {data['pass']}/{data['total']} PASS")

    stop = report["stop_conditions"]
    if stop["stop_reason"]:
        print(f"\n⚠️ 중단 사유: {stop['stop_reason']}")
    else:
        print(f"\n✅ 정상 완료")

    print(f"\n소요 시간: {report['duration_seconds']}초")


def main():
    """메인 실행"""
    batch = ObservationBatch()
    report = batch.run()

    # 저장
    log_file = save_report(report)
    print(f"\n결과 저장: {log_file}")

    # 요약 출력
    print_summary(report)

    # 종료 코드
    if report["completed"]:
        return 0
    else:
        return 1


if __name__ == "__main__":
    exit(main())
