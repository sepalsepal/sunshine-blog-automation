#!/usr/bin/env python3
"""
========================================
공식 이미지 생성 스크립트 (v1.0)
========================================

⚠️ 중요: 이 스크립트만 사용할 것!
- 다른 이미지 생성 스크립트 사용 금지
- 모델 ID 변경 금지

모델: fal-ai/flux-2-pro (FLUX 2.0 Pro)
크기: 1080x1080
작성: 김영현 과장
승인: 김부장 (2026-01-29)
"""

import os
import asyncio
import httpx
from pathlib import Path
from dotenv import load_dotenv
from PIL import Image
import io
import json
from datetime import datetime

# ============================================
# 🔒 하드코딩 설정 - 절대 수정 금지
# ============================================
MODEL_ID = "fal-ai/flux-2-pro"  # FLUX 2.0 Pro - 변경 금지!
IMAGE_SIZE = {"width": 1080, "height": 1080}
# ============================================

# .env 로드
ROOT = Path(__file__).parent.parent.parent
load_dotenv(ROOT / ".env")

FAL_KEY = os.getenv("FAL_KEY")
if FAL_KEY:
    os.environ["FAL_KEY"] = FAL_KEY

import fal_client


def verify_model_id():
    """모델 ID 검증 - 변조 방지"""
    if MODEL_ID != "fal-ai/flux-2-pro":
        raise RuntimeError("⛔ 모델 ID가 변조되었습니다! fal-ai/flux-2-pro만 사용 가능합니다.")
    return True


async def generate_image(prompt: str, output_path: Path, verbose: bool = True) -> dict:
    """
    fal.ai FLUX 2.0 Pro로 이미지 생성

    Args:
        prompt: 이미지 생성 프롬프트
        output_path: 저장 경로
        verbose: 상세 출력 여부

    Returns:
        dict: {"success": bool, "path": str, "model": str, "error": str|None}
    """
    # 모델 ID 검증
    verify_model_id()

    if verbose:
        print(f"  📸 생성 중: {output_path.name}")
        print(f"  🤖 모델: {MODEL_ID}")
        print(f"  📝 프롬프트: {prompt[:60]}...")

    try:
        # fal.ai FLUX 2.0 Pro 호출
        result = await asyncio.to_thread(
            fal_client.subscribe,
            MODEL_ID,  # 하드코딩된 모델 ID 사용
            arguments={
                "prompt": prompt,
                "image_size": IMAGE_SIZE,
                "num_images": 1,
                "output_format": "png",
                "safety_tolerance": "5",
            }
        )

        # 이미지 URL 추출
        image_url = result["images"][0]["url"]

        # 이미지 다운로드
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(image_url)
            response.raise_for_status()

            # PIL로 이미지 처리 및 저장
            img = Image.open(io.BytesIO(response.content))
            if img.size != (IMAGE_SIZE["width"], IMAGE_SIZE["height"]):
                img = img.resize(
                    (IMAGE_SIZE["width"], IMAGE_SIZE["height"]),
                    Image.Resampling.LANCZOS
                )

            # 폴더 생성
            output_path.parent.mkdir(parents=True, exist_ok=True)
            img.save(output_path, "PNG", optimize=True)

        if verbose:
            print(f"  ✅ 완료: {output_path}")

        return {
            "success": True,
            "path": str(output_path),
            "model": MODEL_ID,
            "error": None
        }

    except Exception as e:
        error_msg = f"{type(e).__name__}: {e}"
        if verbose:
            print(f"  ❌ 실패: {error_msg}")
        return {
            "success": False,
            "path": str(output_path),
            "model": MODEL_ID,
            "error": error_msg
        }


async def generate_batch(prompts: list[dict], output_dir: Path, prefix: str = "image") -> list[dict]:
    """
    여러 이미지 일괄 생성

    Args:
        prompts: [{"filename": "xxx.png", "prompt": "..."}, ...]
        output_dir: 출력 폴더
        prefix: 파일명 접두사 (filename 없을 때 사용)

    Returns:
        list[dict]: 각 이미지 생성 결과
    """
    verify_model_id()

    print("=" * 60)
    print(f"🎨 이미지 일괄 생성")
    print(f"🤖 모델: {MODEL_ID} (FLUX 2.0 Pro)")
    print(f"📁 출력: {output_dir}")
    print(f"📋 개수: {len(prompts)}장")
    print("=" * 60)

    results = []

    for i, item in enumerate(prompts):
        filename = item.get("filename", f"{prefix}_{i:02d}.png")
        prompt = item.get("prompt", "")

        if not prompt:
            print(f"  ⚠️ 스킵: {filename} (프롬프트 없음)")
            continue

        output_path = output_dir / filename

        # 이미 존재하면 스킵
        if output_path.exists():
            print(f"  ⏭️ 스킵: {filename} (이미 존재)")
            results.append({
                "success": True,
                "path": str(output_path),
                "model": MODEL_ID,
                "error": None,
                "skipped": True
            })
            continue

        result = await generate_image(prompt, output_path)
        results.append(result)

        # API 부하 방지
        if i < len(prompts) - 1:
            await asyncio.sleep(2)

    # 결과 요약
    success_count = sum(1 for r in results if r.get("success"))
    print("\n" + "=" * 60)
    print(f"✨ 완료: {success_count}/{len(prompts)}개 성공")
    print(f"🤖 사용 모델: {MODEL_ID}")
    print("=" * 60)

    return results


def get_model_info() -> dict:
    """현재 설정된 모델 정보 반환"""
    return {
        "model_id": MODEL_ID,
        "model_name": "FLUX 2.0 Pro",
        "image_size": IMAGE_SIZE,
        "verified": verify_model_id()
    }


# CLI 실행
if __name__ == "__main__":
    import sys

    print("=" * 60)
    print("🔒 공식 이미지 생성 스크립트")
    print(f"🤖 모델: {MODEL_ID} (변경 불가)")
    print("=" * 60)

    if len(sys.argv) < 3:
        print("\n사용법:")
        print("  python generate_images.py <output_path> <prompt>")
        print("\n예시:")
        print('  python generate_images.py ./test.png "A golden retriever"')
        sys.exit(1)

    output = Path(sys.argv[1])
    prompt = sys.argv[2]

    asyncio.run(generate_image(prompt, output))
