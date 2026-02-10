import cloudinary
import cloudinary.api
import cloudinary.uploader

cloudinary.config(
    cloud_name = "ddzbnrfei",
    api_key = "786297442195463",
    api_secret = "5XOALKL3aV3yUy_eE2QO5cFmI3k"
)

folder = "apple"

# 유지할 파일명 (00~09)
keep_files = [
    "apple_00_cover",
    "apple_01_result",
    "apple_02_benefit1",
    "apple_03_benefit2",
    "apple_04_benefit3",
    "apple_05_caution1",
    "apple_06_caution2",
    "apple_07_caution3",
    "apple_08_story",
    "apple_09_cta"
]

# 폴더의 모든 리소스 가져오기
result = cloudinary.api.resources(type="upload", prefix=folder, max_results=100)

delete_count = 0
keep_count = 0

for resource in result.get("resources", []):
    public_id = resource["public_id"]
    filename = public_id.split("/")[-1]
    
    if filename in keep_files:
        print(f"✅ 유지: {public_id}")
        keep_count += 1
    else:
        print(f"🗑️ 삭제: {public_id}")
        cloudinary.uploader.destroy(public_id)
        delete_count += 1

print(f"\n📊 결과: {keep_count}개 유지, {delete_count}개 삭제")
