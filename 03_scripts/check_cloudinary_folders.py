import cloudinary
import cloudinary.api

# Cloudinary 설정
cloudinary.config(
    cloud_name="ddzbnrfei",
    api_key="786297442195463",
    api_secret="5XOALKL3aV3yUy_eE2QO5cFmI3k",
    secure=True
)

def check_folders():
    print("🚀 Cloudinary 폴더 현황 확인 중...\n")
    print("| 폴더명 | 이미지 수 | 상태 |")
    print("|---|---|---|")
    
    # 1. 루트 폴더 내의 하위 폴더 목록 가져오기
    try:
        folders_response = cloudinary.api.root_folders()
        folders = folders_response.get('folders', [])
        
        total_images = 0
        
        target_folders = ['pumpkin', 'cherry', 'blueberry', 'carrot', 'sweet_potato', 'broccoli', 'watermelon']
        
        for folder in folders:
            folder_name = folder['name']
            
            # 관심 있는 폴더만 확인 (또는 전체 확인)
            # if folder_name not in target_folders: continue
            
            # 2. 각 폴더의 리소스(이미지) 검색
            # expression으로 폴더 내 이미지 검색
            resources_response = cloudinary.Search()\
                .expression(f"folder:{folder_name}")\
                .max_results(500)\
                .execute()
                
            count = resources_response.get('total_count', 0)
            total_images += count
            
            status = "✅" if count >= 10 else "⚠️" if count > 0 else "❌"
            if folder_name == 'watermelon' and count == 9: status = "🔄"
            
            print(f"| {folder_name} | {count} | {status} |")
            
        print(f"\n총 이미지 수: {total_images}장")
        
    except Exception as e:
        print(f"❌ 에러 발생: {str(e)}")

if __name__ == "__main__":
    check_folders()
