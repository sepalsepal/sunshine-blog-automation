import os
import shutil
from moviepy import VideoFileClip

# 경로 설정
base_dir = "/Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine"
source_dirs = [
    os.path.join(base_dir, "햇살이_정리/12_동영상"),
    os.path.join(base_dir, "photo_sunshine")
]
target_dir = os.path.join(base_dir, "haetsali_videos")

# 대상 폴더 (임시로 99_unusable에 먼저 모아두고 나중에 수동 분류하거나, 
# 여기서는 일단 99_unusable에 다 넣고 사람이 옮기는 방식을 사용할 수도 있지만,
# 지시서에 따라 '카테고리별 폴더로 저장 로직'이 필요함. 
# 하지만 자동 분류가 어려우므로 일단 파일명에 힌트가 없다면 '99_unusable'로 보내고
# 나중에 사람이 분류하는게 현실적임. 
# 박피디 지시서의 예시 코드에는 "01_happy_eating"으로 하드코딩 되어 있었음.
# 여기서는 일단 모든 클립을 '99_unusable' (또는 '00_to_be_sorted')에 저장하거나,
# 원본 파일명에 특정 키워드가 있으면 분류하도록 시도.
# 하지만 키워드가 없으므로 '99_unusable'에 저장 후 수동 분류 가이드가 안전함.
# 또는 지시서 예시처럼 try-catch로 처리하되, 일단은 추출 성공한건 99_unusable로 보내서 
# 사용자가 분류하게 하는게 맞을듯. 지시서의 "01_happy_eating"은 예시일 뿐.
# ... 다시 보니 "카테고리별 폴더로 저장 로직" 주석이 있음.
# 근데 분류 모델이 없으니...
# 일단 '99_unusable' 폴더를 '00_unsorted' 처럼 활용하여 다 넣고, 
# 김대리가 보고서에서 "분류 필요"라고 하는게 맞음.
# 아니면 랜덤하게 분산? 아니면 일단 첫번째 폴더?
# 안전하게 '99_unusable'에 넣고, 파일명에 'eating' 등이 있으면 해당 폴더로 이동 시도.

# 키워드 매핑 (파일명 기반 간단 분류 시도)
keyword_map = {
    'eating': '01_happy_eating',
    'eat': '01_happy_eating',
    'sniff': '02_curious_sniff',
    'walk': '05_outdoor_walk',
    'run': '06_play_fetch',
    'play': '06_play_fetch',
    'sleep': '07_rest_sleep',
    'rest': '07_rest_sleep'
}

def extract_clips():
    print("🚀 동영상 5초 클립 추출 시작...")
    
    # 소스 파일 찾기
    video_files = []
    for s_dir in source_dirs:
        if not os.path.exists(s_dir): continue
        for root, _, files in os.walk(s_dir):
            for f in files:
                if f.lower().endswith(('.mp4', '.mov')):
                    video_files.append(os.path.join(root, f))
    
    print(f"총 {len(video_files)}개 동영상 파일 발견.")
    
    count = 0
    success = 0
    fail = 0
    
    for input_path in video_files:
        count += 1
        filename = os.path.basename(input_path)
        
        # 타겟 폴더 결정 (기본: 99_unusable)
        target_category = "99_unusable"
        for key, cat in keyword_map.items():
            if key in filename.lower():
                target_category = cat
                break
                
        output_folder = os.path.join(target_dir, target_category)
        output_filename = f"haetsali_clip_{filename}"
        if not output_filename.lower().endswith('.mp4'):
            output_filename = os.path.splitext(output_filename)[0] + ".mp4"
            
        output_path = os.path.join(output_folder, output_filename)
        
        # 이미 존재하면 스킵
        if os.path.exists(output_path):
            print(f"[{count}/{len(video_files)}] 이미 존재: {filename}")
            continue

        try:
            print(f"[{count}/{len(video_files)}] 처리 중: {filename} -> {target_category}")
            
            # 5초 클립 추출
            with VideoFileClip(input_path) as video:
                # 길이가 5초보다 짧으면 그대로, 길면 5초만
                duration = min(video.duration, 5)
                clip = video.subclipped(0, duration)
                
                # 오디오 코덱 설정하여 저장 (libx264, aac)
                # 99_unusable 폴더에 저장
                clip.write_videofile(
                    output_path, 
                    codec='libx264', 
                    audio_codec='aac', 
                    logger=None # 로그 끄기
                )
                
            success += 1
            
        except Exception as e:
            print(f"❌ 실패: {filename} - {str(e)}")
            fail += 1
            # 실패 시 원본을 99_unusable로 복사 시도 (옵션)
            # shutil.copy(input_path, os.path.join(target_dir, "99_unusable"))
            
    print("-" * 50)
    print(f"완료! 성공: {success}, 실패: {fail}, 총: {count}")

if __name__ == "__main__":
    extract_clips()
