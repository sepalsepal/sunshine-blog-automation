import os
import sys

# 프로젝트 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "04_pipeline"))

import image_utils

def main():
    print("=== 📸 Real Blog Snapshot Test Mode ===")
    
    # [블로그 삽화용 리얼 스냅샷 테스트 프롬프트 3종]
    # 구글이 '폰카'로 대충 찍은 것처럼 리얼하게 그리는지 테스트합니다.
    
    prompts = [
        # 1. 감성 소품 샷 (산책 준비물) - 좀 더 거칠게 요청
        "Dog walking essentials laid out on a wooden table before going out: leather leash, water bottle, poop bags. Candid shot.",
        
        # 2. 음식 & 재료 샷 (건강 간식) - 부엌 조명 강조
        "Freshly steamed sweet potato cubes and broccoli on a simple white plate in a home kitchen. Natural window light.",
        
        # 3. 계절감/분위기 컷 (겨울 질감) - 클로즈업
        "Close-up texture shot of a thick beige knitted blanket on a sofa."
    ]

    # 이미지 생성 실행
    generated_files = image_utils.generate_images_hybrid(prompts)
    
    print("\n✅ 생성 완료! 이미지를 엽니다...")
    
    if generated_files:
        for file_path in generated_files:
            # 맥북에서 이미지 바로 열기
            os.system(f"open {file_path}")
    else:
        print("❌ 생성된 이미지가 없습니다.")

if __name__ == "__main__":
    main()