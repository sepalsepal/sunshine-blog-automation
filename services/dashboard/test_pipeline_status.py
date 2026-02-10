#!/usr/bin/env python3
"""
파이프라인 상태 테스트 스크립트
대시보드에서 실시간 업데이트를 확인하기 위한 시뮬레이션

실행: python services/dashboard/test_pipeline_status.py
"""

import time
import sys
from pathlib import Path

# 모듈 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.dashboard.status_updater import (
    get_updater, reset, start_pipeline,
    start_step, update_progress, complete_step, finish_pipeline,
    PIPELINE_STEPS
)


def simulate_pipeline(topic: str = "strawberry", speed: float = 1.0):
    """파이프라인 시뮬레이션"""
    print(f"\n🚀 파이프라인 시뮬레이션 시작: {topic}")
    print(f"   속도: {speed}x (낮을수록 느림)")
    print("-" * 50)

    # 초기화
    reset()
    time.sleep(0.5 / speed)

    # 파이프라인 시작
    start_pipeline(topic)
    print(f"✅ 파이프라인 시작됨")

    # 각 단계 실행
    for step in PIPELINE_STEPS:
        step_id = step["id"]
        name = step["name"]
        role = step["role"]
        emoji = step["emoji"]

        print(f"\n{emoji} [{step_id}] {role} ({name}) 시작...")

        # 단계 시작
        start_step(step_id)
        time.sleep(1.0 / speed)

        # 이미지 생성 단계는 진행률 표시
        if role == "이미지":
            for i in range(1, 5):
                update_progress(step_id, f"{i}/4장 생성 중...")
                print(f"   이미지 {i}/4장 생성 중...")
                time.sleep(0.8 / speed)

        # 검수 단계
        elif "검수" in role or "승인" in role:
            update_progress(step_id, "검수 중...")
            time.sleep(1.5 / speed)

        else:
            time.sleep(0.8 / speed)

        # 단계 완료
        complete_step(step_id, duration=2.5)
        print(f"   ✅ 완료")

    # 파이프라인 완료
    finish_pipeline(result={"status": "success", "topic": topic})
    print("\n" + "=" * 50)
    print(f"🎉 파이프라인 완료: {topic}")
    print("=" * 50)


if __name__ == "__main__":
    # 인자로 속도 조절 가능 (기본 1.0)
    speed = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0
    topic = sys.argv[2] if len(sys.argv) > 2 else "strawberry"

    print("\n" + "=" * 50)
    print("📊 대시보드에서 실시간 확인:")
    print("   streamlit run services/dashboard/app.py")
    print("   '🔄 자동 새로고침' 체크 필요")
    print("=" * 50)

    simulate_pipeline(topic, speed)
