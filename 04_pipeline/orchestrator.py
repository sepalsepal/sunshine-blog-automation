#!/usr/bin/env python3
"""
orchestrator.py - 계층 조율자
WO-LIGHTWEIGHT-SEPARATION

책임:
- 계층 순차 호출
- 결과 전달
- 로그 기록

제한:
- 각 계층 내부 로직 수정 불가
- 결과 변조 불가
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

import sys
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.layers.generator import Generator
from pipeline.layers.validator import Validator
from pipeline.layers.executor import Executor
from pipeline.interfaces.layer_contract import (
    GeneratedContent,
    ValidationResult,
    ExecutionResult,
    ValidationStatus,
    ExecutionStatus,
    AutoBlockedError,
    ValidationFailedError,
    ExecutionBlockedError,
)


class Orchestrator:
    """
    계층 조율자

    계층 순차 호출만 담당
    각 계층 내부 로직 수정 불가
    결과 전달만 수행
    """

    def __init__(self, log_dir: Optional[Path] = None):
        self.generator = Generator()
        self.validator = Validator()
        self.executor = Executor()

        self.log_dir = log_dir or PROJECT_ROOT / "logs" / "orchestrator"
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self._run_log = []

    def run(
        self,
        food_id: int,
        platform: str = "blog",
        action: str = "batch"
    ) -> Dict[str, Any]:
        """
        3계층 순차 실행

        Args:
            food_id: 음식 ID
            platform: 플랫폼 (blog/insta/threads)
            action: 실행 유형 (batch/publish/save)

        Returns:
            실행 결과 딕셔너리

        Raises:
            AutoBlockedError: 금지 코드로 자동 차단 시
            ValidationFailedError: 검증 실패 시
        """
        self._run_log = []
        start_time = datetime.now()

        result = {
            "food_id": food_id,
            "platform": platform,
            "action": action,
            "start_time": start_time.isoformat(),
            "layers": {}
        }

        try:
            # =========================================================
            # Step 1: Generate (Layer 1)
            # =========================================================
            content = self.generator.generate_caption(food_id, platform)
            self._log_layer("generator", content.to_dict())
            result["layers"]["generator"] = content.to_dict()

            # =========================================================
            # Step 2: Validate (Layer 2)
            # =========================================================
            validation = self.validator.validate(content)
            self._log_layer("validator", validation.to_dict())
            result["layers"]["validator"] = validation.to_dict()

            # =========================================================
            # Step 3: Execute (Layer 3) - PASS일 때만
            # =========================================================
            if validation.status == ValidationStatus.PASS:
                if action == "publish":
                    execution = self.executor.publish(validation)
                elif action == "save":
                    execution = self.executor.save(validation)
                else:
                    execution = self.executor.execute(validation)

                self._log_layer("executor", execution.to_dict())
                result["layers"]["executor"] = execution.to_dict()
                result["final_status"] = "EXECUTED"

            elif validation.status == ValidationStatus.BLOCKED:
                # 금지 코드로 자동 차단
                self._log_layer("blocked", {
                    "reason": validation.reason,
                    "fail_codes": validation.fail_codes
                })
                result["layers"]["blocked"] = {
                    "reason": validation.reason,
                    "fail_codes": validation.fail_codes
                }
                result["final_status"] = "BLOCKED"
                raise AutoBlockedError(validation.reason)

            else:
                # 일반 FAIL
                self._log_layer("failed", {
                    "reason": validation.reason,
                    "fail_codes": validation.fail_codes,
                    "allow_override": validation.allow_override,
                    "requires_approval": validation.requires_approval
                })
                result["layers"]["failed"] = {
                    "reason": validation.reason,
                    "fail_codes": validation.fail_codes
                }
                result["final_status"] = "FAILED"
                raise ValidationFailedError(validation.reason)

        except (AutoBlockedError, ValidationFailedError):
            raise
        except Exception as e:
            result["error"] = str(e)
            result["final_status"] = "ERROR"
            raise

        finally:
            end_time = datetime.now()
            result["end_time"] = end_time.isoformat()
            result["duration_ms"] = (end_time - start_time).total_seconds() * 1000

            # 로그 저장
            self._save_run_log(food_id, result)

        return result

    def run_batch(
        self,
        food_ids: List[int],
        platform: str = "blog",
        action: str = "batch"
    ) -> List[Dict[str, Any]]:
        """
        배치 실행

        Args:
            food_ids: 음식 ID 목록
            platform: 플랫폼
            action: 실행 유형

        Returns:
            실행 결과 목록
        """
        results = []
        for food_id in food_ids:
            try:
                result = self.run(food_id, platform, action)
                results.append(result)
            except (AutoBlockedError, ValidationFailedError) as e:
                results.append({
                    "food_id": food_id,
                    "final_status": "BLOCKED" if isinstance(e, AutoBlockedError) else "FAILED",
                    "error": str(e)
                })

        return results

    def dry_run(
        self,
        food_id: int,
        platform: str = "blog"
    ) -> Dict[str, Any]:
        """
        드라이런 (실행 없이 검증까지만)

        Args:
            food_id: 음식 ID
            platform: 플랫폼

        Returns:
            검증 결과 딕셔너리
        """
        # Generate
        content = self.generator.generate_caption(food_id, platform)

        # Validate
        validation = self.validator.validate(content)

        return {
            "food_id": food_id,
            "platform": platform,
            "mode": "dry_run",
            "generator": content.to_dict(),
            "validator": validation.to_dict(),
            "would_execute": validation.status == ValidationStatus.PASS
        }

    def _log_layer(self, layer: str, data: Dict):
        """계층 실행 로그 기록"""
        self._run_log.append({
            "layer": layer,
            "timestamp": datetime.now().isoformat(),
            "data": data
        })

    def _save_run_log(self, food_id: int, result: Dict):
        """실행 로그 파일 저장"""
        date_str = datetime.now().strftime("%Y%m%d")
        log_file = self.log_dir / date_str / f"{food_id}_run.json"
        log_file.parent.mkdir(parents=True, exist_ok=True)

        with open(log_file, "w", encoding="utf-8") as f:
            json.dump({
                "result": result,
                "layer_logs": self._run_log
            }, f, ensure_ascii=False, indent=2)


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="3계층 파이프라인 Orchestrator")
    parser.add_argument("--food-id", type=int, required=True, help="음식 ID")
    parser.add_argument("--platform", default="blog", help="플랫폼")
    parser.add_argument("--action", default="batch", help="실행 유형")
    parser.add_argument("--dry-run", action="store_true", help="드라이런 모드")

    args = parser.parse_args()

    orchestrator = Orchestrator()

    try:
        if args.dry_run:
            result = orchestrator.dry_run(args.food_id, args.platform)
            print("\n=== Dry Run 결과 ===")
            print(f"Food ID: {result['food_id']}")
            print(f"Platform: {result['platform']}")
            print(f"Would Execute: {result['would_execute']}")
            print(f"\nValidator Status: {result['validator']['status']}")
            print(f"Score: {result['validator']['total']}/20")
        else:
            result = orchestrator.run(args.food_id, args.platform, args.action)
            print("\n=== 실행 결과 ===")
            print(f"Food ID: {result['food_id']}")
            print(f"Final Status: {result['final_status']}")
            print(f"Duration: {result.get('duration_ms', 0):.2f}ms")

    except AutoBlockedError as e:
        print(f"\n[BLOCKED] 금지 코드로 자동 차단: {e}")
    except ValidationFailedError as e:
        print(f"\n[FAILED] 검증 실패: {e}")
    except Exception as e:
        print(f"\n[ERROR] 오류 발생: {e}")


if __name__ == "__main__":
    main()
