#!/usr/bin/env python3
"""
이미지 검증 스크립트
PostToolUse hook과 연동되어 이미지 생성 후 자동 실행됩니다.
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Tuple


def get_latest_image(output_dir: str = "outputs") -> Optional[Path]:
    """가장 최근 생성된 이미지 찾기"""
    output_path = Path(output_dir)
    if not output_path.exists():
        return None
        
    images = []
    for ext in ['*.png', '*.jpg', '*.jpeg']:
        images.extend(output_path.rglob(ext))
        
    if not images:
        return None
        
    return max(images, key=lambda p: p.stat().st_mtime)


def verify_image_size(image_path: Path, expected_size: Tuple[int, int] = (1080, 1080)) -> dict:
    """이미지 크기 검증"""
    try:
        from PIL import Image
        with Image.open(image_path) as img:
            actual_size = img.size
            passed = actual_size == expected_size
            return {
                "check": "size",
                "passed": passed,
                "expected": expected_size,
                "actual": actual_size,
                "message": f"{'✅' if passed else '❌'} 크기: {actual_size} (기준: {expected_size})"
            }
    except ImportError:
        return {
            "check": "size",
            "passed": None,
            "message": "⚠️ PIL 라이브러리 없음 - 크기 검증 스킵"
        }
    except Exception as e:
        return {
            "check": "size",
            "passed": False,
            "message": f"❌ 에러: {str(e)}"
        }


def verify_image_format(image_path: Path) -> dict:
    """이미지 포맷 검증"""
    valid_formats = ['.png', '.jpg', '.jpeg']
    ext = image_path.suffix.lower()
    passed = ext in valid_formats
    return {
        "check": "format",
        "passed": passed,
        "actual": ext,
        "message": f"{'✅' if passed else '❌'} 포맷: {ext}"
    }


def verify_file_size(image_path: Path, max_mb: float = 10.0) -> dict:
    """파일 크기 검증 (Instagram 제한)"""
    size_mb = image_path.stat().st_size / (1024 * 1024)
    passed = size_mb <= max_mb
    return {
        "check": "file_size",
        "passed": passed,
        "actual_mb": round(size_mb, 2),
        "max_mb": max_mb,
        "message": f"{'✅' if passed else '❌'} 파일 크기: {size_mb:.2f}MB (제한: {max_mb}MB)"
    }


def verify_image_quality(image_path: Path) -> dict:
    """이미지 품질 검증 (기본적인 검사)"""
    try:
        from PIL import Image
        with Image.open(image_path) as img:
            # 이미지가 열리면 기본적으로 유효
            mode = img.mode
            valid_modes = ['RGB', 'RGBA', 'L']
            passed = mode in valid_modes
            return {
                "check": "quality",
                "passed": passed,
                "mode": mode,
                "message": f"{'✅' if passed else '⚠️'} 색상 모드: {mode}"
            }
    except Exception as e:
        return {
            "check": "quality",
            "passed": False,
            "message": f"❌ 품질 검증 실패: {str(e)}"
        }


def verify_image(image_path: Path) -> List[dict]:
    """이미지 전체 검증"""
    results = []
    
    # 파일 존재 확인
    if not image_path.exists():
        return [{
            "check": "existence",
            "passed": False,
            "message": f"❌ 파일이 존재하지 않습니다: {image_path}"
        }]
    
    results.append({
        "check": "existence",
        "passed": True,
        "message": f"✅ 파일 존재: {image_path.name}"
    })
    
    # 각 검증 실행
    results.append(verify_image_format(image_path))
    results.append(verify_image_size(image_path))
    results.append(verify_file_size(image_path))
    results.append(verify_image_quality(image_path))
    
    return results


def print_results(image_path: Path, results: List[dict]):
    """결과 출력"""
    print("\n" + "="*50)
    print(f"🖼️ 이미지 검증: {image_path.name}")
    print("="*50)
    
    passed_count = sum(1 for r in results if r.get('passed') == True)
    total_count = sum(1 for r in results if r.get('passed') is not None)
    
    for result in results:
        print(result['message'])
    
    print("-"*50)
    
    if passed_count == total_count:
        print(f"✅ 검증 완료: {passed_count}/{total_count} 통과")
        return True
    else:
        print(f"⚠️ 일부 실패: {passed_count}/{total_count} 통과")
        return False


def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='이미지 검증 스크립트')
    parser.add_argument('--image', '-i', help='검증할 이미지 경로')
    parser.add_argument('--latest', action='store_true', help='가장 최근 이미지 검증')
    parser.add_argument('--output-dir', '-o', default='outputs', help='출력 디렉토리')
    parser.add_argument('--strict', action='store_true', help='실패 시 종료 코드 1')
    
    args = parser.parse_args()
    
    # 이미지 경로 결정
    if args.image:
        image_path = Path(args.image)
    elif args.latest:
        image_path = get_latest_image(args.output_dir)
        if not image_path:
            print("❌ 검증할 이미지를 찾을 수 없습니다.")
            sys.exit(1)
    else:
        print("사용법: python verify_image.py --image <경로> 또는 --latest")
        sys.exit(1)
    
    # 검증 실행
    results = verify_image(image_path)
    success = print_results(image_path, results)
    
    # 종료 코드
    if args.strict and not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
