import firebase_admin
from firebase_admin import credentials, storage
import os
import sys

# ⚠️ Firebase 서비스 계정 키 파일 경로
# (사용자가 직접 이 파일을 프로젝트 폴더에 넣어야 함)
CRED_PATH = "firebase_key.json"
BUCKET_NAME = os.getenv("FIREBASE_BUCKET_NAME", "sunshine-imageworks.firebasestorage.app") # 스크린샷 확인값

_is_initialized = False

def initialize_firebase():
    global _is_initialized
    if _is_initialized:
        return True

    if not os.path.exists(CRED_PATH):
        print(f"⚠️ [Firebase] 키 파일('{CRED_PATH}')이 없습니다. 업로드를 건너뜁니다.")
        return False

    try:
        cred = credentials.Certificate(CRED_PATH)
        # 이미 초기화되었는지 확인 (중복 초기화 방지)
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred, {
                'storageBucket': BUCKET_NAME
            })
        _is_initialized = True
        print("✅ [Firebase] 초기화 성공")
        return True
    except Exception as e:
        print(f"❌ [Firebase] 초기화 실패: {e}")
        return False

def upload_file(local_path, destination_blob_name=None):
    """
    로컬 파일을 Firebase Storage에 업로드합니다.
    :param local_path: 로컬 파일 경로 (예: "images/photo.png")
    :param destination_blob_name: 저장소 내 경로 (None이면 로컬 파일명 사용)
    :return: 업로드된 파일의 공개 URL (또는 None)
    """
    if not initialize_firebase():
        return None

    if not os.path.exists(local_path):
        print(f"❌ [Firebase] 파일 없음: {local_path}")
        return None

    if destination_blob_name is None:
        destination_blob_name = os.path.basename(local_path)

    try:
        bucket = storage.bucket()
        blob = bucket.blob(destination_blob_name)
        
        # 메타데이터 설정 (선택 사항)
        blob.metadata = {"uploaded_by": "antigravity_bot"}
        
        blob.upload_from_filename(local_path)
        
        # 공개 URL 생성 (버킷이 공개 설정되어 있어야 함, 혹은 signed url 사용)
        # 여기서는 간단히 make_public() 사용 (보안 정책에 따라 다를 수 있음)
        # blob.make_public() 
        # public_url = blob.public_url
        
        print(f"   ☁️ [Firebase] 업로드 완료: {destination_blob_name}")
        return f"gs://{BUCKET_NAME}/{destination_blob_name}"
        
    except Exception as e:
        print(f"   ❌ [Firebase] 업로드 중 에러: {e}")
        return None

def upload_directory(source_dir, destination_dir):
    """
    폴더 전체를 Firebase Storage에 업로드합니다. (재귀적)
    :param source_dir: 로컬 소스 폴더 경로
    :param destination_dir: Storage 내 저장될 폴더 경로
    """
    if not initialize_firebase():
        return

    print(f"📦 [Backup] 폴더 백업 시작: {source_dir} -> {destination_dir}")
    
    # 무시할 폴더/파일 목록
    IGNORE_LIST = ['.venv', '.git', '__pycache__', '.DS_Store', 'node_modules']
    
    count = 0
    for root, dirs, files in os.walk(source_dir):
        # 무시할 폴더 제외 (in-place modification)
        dirs[:] = [d for d in dirs if d not in IGNORE_LIST]
        
        for file in files:
            if file in IGNORE_LIST:
                continue
                
            local_path = os.path.join(root, file)
            
            # 상대 경로 계산 (source_dir 기준)
            relative_path = os.path.relpath(local_path, source_dir)
            
            # Storage 경로 생성
            blob_path = os.path.join(destination_dir, relative_path)
            
            # 윈도우 경로(\)를 클라우드 경로(/)로 변환
            blob_path = blob_path.replace("\\", "/")
            
            print(f"   ⬆️ 업로드 중: {relative_path}")
            upload_file(local_path, blob_path)
            count += 1
            
    print(f"✅ [Backup] 총 {count}개 파일 백업 완료!")

