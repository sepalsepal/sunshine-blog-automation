#!/usr/bin/env python3
"""
WO-2026-0205-002 PART 2: B그룹 바디+CTA 렌더링

- text.json 생성 + 바디2장 + CTA1장 렌더링
- 안전도별 배치 실행: FORBIDDEN → DANGER → CAUTION → SAFE
- v3.1 봉인 파이프라인 사용 (수정 없이 import만)
- 15항 validator strict 검증

사용법:
  python batch_render_b_group.py forbidden    # FORBIDDEN 배치만
  python batch_render_b_group.py danger       # DANGER 배치만
  python batch_render_b_group.py caution      # CAUTION 배치만
  python batch_render_b_group.py safe         # SAFE 배치만
  python batch_render_b_group.py all          # 전체 실행
"""

import os
import sys
import json
import hashlib
import shutil
from pathlib import Path
from datetime import datetime

try:
    from PIL import Image
except ImportError:
    print("[ERROR] Pillow 필요: pip install Pillow")
    sys.exit(1)

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)

from pipeline.pillow_overlay import (
    render_body,
    render_cta,
    build_validation_config,
    get_safety_color,
)
from pipeline.validators_strict import (
    validate_before_render,
    validate_v31_slide,
    strip_emoji,
)

# ============================================
# 경로 설정
# ============================================
CONTENTS_DIR = PROJECT_ROOT / "contents" / "1_cover_only"
BODY_READY_DIR = PROJECT_ROOT / "contents" / "2_body_ready"
COVER_SOURCE_DIR = (
    PROJECT_ROOT / "backup_2026-02-03" / "content" / "images" / "000_cover" / "02_ready"
)
BEST_CTA_DIR = PROJECT_ROOT / "contents" / "sunshine" / "cta_source" / "best_cta"
TEXT_DIR = PROJECT_ROOT / "config" / "settings"
TARGET_SIZE = (1080, 1080)

# ============================================
# B그룹 전체 아이템 정의 (수의학 자료 기반)
# ============================================

ITEMS = [
    # ═══════════════════════════════════════════
    # FORBIDDEN (5건, green_onion 스킵: 커버 없음)
    # ═══════════════════════════════════════════
    {
        "food_id": "brownie", "food_ko": "브라우니", "safety": "forbidden",
        "folder": "095_brownie_브라우니",
        "cover_file": "cover_95_브라우니_brownie.png",
        "body1": {"title": "절대 금지!", "subtitle": "초콜릿 함유, 테오브로민 독성"},
        "body2": {"title": "증상 & 대처", "subtitle": "구토, 경련 시 즉시 동물병원"},
        "cta": {"title": "저장 & 공유", "subtitle": "주변 견주에게 알려주세요!"},
    },
    {
        "food_id": "reeses", "food_ko": "리세스", "safety": "forbidden",
        "folder": "124_reeses_리세스",
        "cover_file": "cover_124_리세스_reeses.png",
        "body1": {"title": "절대 금지!", "subtitle": "초콜릿+고당분, 독성 위험"},
        "body2": {"title": "증상 & 대처", "subtitle": "구토, 떨림 시 즉시 동물병원"},
        "cta": {"title": "저장 & 공유", "subtitle": "주변 견주에게 알려주세요!"},
    },
    {
        "food_id": "soju", "food_ko": "소주", "safety": "forbidden",
        "folder": "128_soju_소주",
        "cover_file": "cover_128_소주_soju.png",
        "body1": {"title": "절대 금지!", "subtitle": "알코올, 간과 신장에 치명적"},
        "body2": {"title": "증상 & 대처", "subtitle": "구토, 의식 저하 시 응급 이송"},
        "cta": {"title": "저장 & 공유", "subtitle": "주변 견주에게 알려주세요!"},
    },
    {
        "food_id": "pizza", "food_ko": "피자", "safety": "forbidden",
        "folder": "121_pizza_피자",
        "cover_file": "cover_121_피자_pizza.png",
        "body1": {"title": "절대 금지!", "subtitle": "마늘+양파 함유, 적혈구 파괴"},
        "body2": {"title": "위험 성분", "subtitle": "마늘, 양파, 고지방, 고나트륨"},
        "cta": {"title": "저장 & 공유", "subtitle": "주변 견주에게 알려주세요!"},
    },
    {
        "food_id": "ramen", "food_ko": "라면", "safety": "forbidden",
        "folder": "086_ramen_라면",
        "cover_file": "cover_75_라면_ramen.png",
        "body1": {"title": "절대 금지!", "subtitle": "양파+마늘 함유, 고나트륨"},
        "body2": {"title": "위험 성분", "subtitle": "나트륨 과다, 양파와 마늘 독성"},
        "cta": {"title": "저장 & 공유", "subtitle": "주변 견주에게 알려주세요!"},
    },

    # ═══════════════════════════════════════════
    # DANGER (16건, lemon 스킵: 폴더 없음)
    # ═══════════════════════════════════════════
    {
        "food_id": "bibimbap", "food_ko": "비빔밥", "safety": "danger",
        "folder": "081_bibimbap_비빔밥",
        "cover_file": "cover_81_비빔밥_bibimbap.png",
        "body1": {"title": "위험해요!", "subtitle": "마늘, 참기름, 고추장 함유"},
        "body2": {"title": "위험 성분", "subtitle": "양념류 독성, 고나트륨 주의"},
        "cta": {"title": "저장 & 공유", "subtitle": "주변 견주에게 알려주세요!"},
    },
    {
        "food_id": "jjajangmyeon", "food_ko": "짜장면", "safety": "danger",
        "folder": "082_jjajangmyeon_짜장면",
        "cover_file": "cover_82_짜장면_jjajangmyeon.png",
        "body1": {"title": "위험해요!", "subtitle": "양파+마늘+고지방 춘장"},
        "body2": {"title": "위험 성분", "subtitle": "양파 독성, 고나트륨, 고지방"},
        "cta": {"title": "저장 & 공유", "subtitle": "주변 견주에게 알려주세요!"},
    },
    {
        "food_id": "bulgogi", "food_ko": "불고기", "safety": "danger",
        "folder": "090_bulgogi_불고기",
        "cover_file": "cover_90_불고기_bulgogi.png",
        "body1": {"title": "위험해요!", "subtitle": "간장+마늘+양파 양념 위험"},
        "body2": {"title": "위험 성분", "subtitle": "양념 독성, 당분, 고나트륨"},
        "cta": {"title": "저장 & 공유", "subtitle": "주변 견주에게 알려주세요!"},
    },
    {
        "food_id": "cake", "food_ko": "케이크", "safety": "danger",
        "folder": "091_cake_케이크",
        "cover_file": "cover_91_케이크_cake.png",
        "body1": {"title": "위험해요!", "subtitle": "고당분+고지방, 비만 유발"},
        "body2": {"title": "위험 성분", "subtitle": "설탕, 버터, 초콜릿 포함 가능"},
        "cta": {"title": "저장 & 공유", "subtitle": "주변 견주에게 알려주세요!"},
    },
    {
        "food_id": "dakgangjeong", "food_ko": "닭강정", "safety": "danger",
        "folder": "102_dakgangjeong_닭강정",
        "cover_file": "cover_102_닭강정_dakgangjeong.png",
        "body1": {"title": "위험해요!", "subtitle": "튀김+양념, 고지방 고당분"},
        "body2": {"title": "위험 성분", "subtitle": "튀김 기름, 설탕, 마늘 양념"},
        "cta": {"title": "저장 & 공유", "subtitle": "주변 견주에게 알려주세요!"},
    },
    {
        "food_id": "milk", "food_ko": "바나나우유", "safety": "danger",
        "folder": "152_banana_milk_바나나우유",
        "cover_file": "cover_106_바나나우유_banana_milk.png",
        "body1": {"title": "위험해요!", "subtitle": "유당+고당분, 소화 장애"},
        "body2": {"title": "위험 성분", "subtitle": "유당불내증, 설탕, 인공향료"},
        "cta": {"title": "저장 & 공유", "subtitle": "주변 견주에게 알려주세요!"},
    },
    {
        "food_id": "doritos", "food_ko": "도리토스", "safety": "danger",
        "folder": "113_doritos_도리토스",
        "cover_file": "cover_113_도리토스_doritos.png",
        "body1": {"title": "위험해요!", "subtitle": "고나트륨+양파 파우더 함유"},
        "body2": {"title": "위험 성분", "subtitle": "인공조미료, 양파, 고나트륨"},
        "cta": {"title": "저장 & 공유", "subtitle": "주변 견주에게 알려주세요!"},
    },
    {
        "food_id": "fanta", "food_ko": "환타", "safety": "danger",
        "folder": "114_fanta_환타",
        "cover_file": "cover_114_환타_fanta.png",
        "body1": {"title": "위험해요!", "subtitle": "고당분 탄산, 비만 유발"},
        "body2": {"title": "위험 성분", "subtitle": "설탕, 인공색소, 탄산가스"},
        "cta": {"title": "저장 & 공유", "subtitle": "주변 견주에게 알려주세요!"},
    },
    {
        "food_id": "lays", "food_ko": "레이즈", "safety": "danger",
        "folder": "118_lays_레이즈",
        "cover_file": "cover_118_레이즈_lays.png",
        "body1": {"title": "위험해요!", "subtitle": "고나트륨+고지방, 비만 유발"},
        "body2": {"title": "위험 성분", "subtitle": "나트륨 과다, 튀김 기름"},
        "cta": {"title": "저장 & 공유", "subtitle": "주변 견주에게 알려주세요!"},
    },
    {
        "food_id": "milkis", "food_ko": "밀키스", "safety": "danger",
        "folder": "119_milkis_밀키스",
        "cover_file": "cover_119_밀키스_milkis.png",
        "body1": {"title": "위험해요!", "subtitle": "고당분 탄산, 유제품 함유"},
        "body2": {"title": "위험 성분", "subtitle": "설탕, 유당, 탄산, 인공향료"},
        "cta": {"title": "저장 & 공유", "subtitle": "주변 견주에게 알려주세요!"},
    },
    {
        "food_id": "skittles", "food_ko": "스키틀즈", "safety": "danger",
        "folder": "127_skittles_스키틀즈",
        "cover_file": "cover_127_스키틀즈_skittles.png",
        "body1": {"title": "위험해요!", "subtitle": "설탕 덩어리, 인공색소 다량"},
        "body2": {"title": "위험 성분", "subtitle": "설탕, 인공색소, 산미료"},
        "cta": {"title": "저장 & 공유", "subtitle": "주변 견주에게 알려주세요!"},
    },
    {
        "food_id": "starburst", "food_ko": "스타버스트", "safety": "danger",
        "folder": "130_starburst_스타버스트",
        "cover_file": "cover_130_스타버스트_starburst.png",
        "body1": {"title": "위험해요!", "subtitle": "고당분 캔디, 치아 손상"},
        "body2": {"title": "위험 성분", "subtitle": "설탕, 옥수수시럽, 인공향료"},
        "cta": {"title": "저장 & 공유", "subtitle": "주변 견주에게 알려주세요!"},
    },
    {
        "food_id": "sprite", "food_ko": "스프라이트", "safety": "danger",
        "folder": "133_sprite_스프라이트",
        "cover_file": "cover_133_스프라이트_sprite.png",
        "body1": {"title": "위험해요!", "subtitle": "고당분 탄산, 위장 자극"},
        "body2": {"title": "위험 성분", "subtitle": "설탕, 탄산, 구연산"},
        "cta": {"title": "저장 & 공유", "subtitle": "주변 견주에게 알려주세요!"},
    },
    {
        "food_id": "raisin", "food_ko": "건포도", "safety": "danger",
        "folder": "062_raisin_건포도",
        "cover_file": "cover_61_건포도_raisin_DANGER.png",
        "body1": {"title": "위험해요!", "subtitle": "포도 농축, 신부전 유발 가능"},
        "body2": {"title": "증상 & 대처", "subtitle": "구토, 무기력 시 즉시 병원"},
        "cta": {"title": "저장 & 공유", "subtitle": "주변 견주에게 알려주세요!"},
    },
    {
        "food_id": "bacon", "food_ko": "베이컨", "safety": "danger",
        "folder": "105_bacon_베이컨",
        "cover_file": "cover_105_베이컨_bacon.png",
        "body1": {"title": "위험해요!", "subtitle": "고지방+고나트륨, 췌장염 위험"},
        "body2": {"title": "위험 성분", "subtitle": "포화지방, 아질산염, 과다 나트륨"},
        "cta": {"title": "저장 & 공유", "subtitle": "주변 견주에게 알려주세요!"},
    },
    {
        "food_id": "donut", "food_ko": "도넛", "safety": "danger",
        "folder": "092_donut_도넛",
        "cover_file": "cover_92_도넛_donut.png",
        "body1": {"title": "위험해요!", "subtitle": "고당분+고지방, 비만과 당뇨"},
        "body2": {"title": "위험 성분", "subtitle": "설탕, 튀김 기름, 초콜릿 코팅"},
        "cta": {"title": "저장 & 공유", "subtitle": "주변 견주에게 알려주세요!"},
    },

    # ═══════════════════════════════════════════
    # CAUTION (17건, persimmon_ripe/plum/dumpling 스킵)
    # ═══════════════════════════════════════════
    {
        "food_id": "nuts", "food_ko": "견과류", "safety": "caution",
        "folder": "031_nuts_견과류",
        "cover_file": "cover_31_견과류_nuts.png",
        "body1": {"title": "조건부 OK!", "subtitle": "무염, 소량만 급여 가능"},
        "body2": {"title": "주의사항", "subtitle": "마카다미아 절대 금지, 고지방"},
        "cta": {"title": "저장 & 공유", "subtitle": "주변 견주에게 알려주세요!"},
    },
    {
        "food_id": "almonds", "food_ko": "아몬드", "safety": "caution",
        "folder": "032_almonds_아몬드",
        "cover_file": "cover_32_아몬드_almonds.png",
        "body1": {"title": "조건부 OK!", "subtitle": "무염, 잘게 부숴서 소량만"},
        "body2": {"title": "주의사항", "subtitle": "고지방, 질식 위험, 소화 어려움"},
        "cta": {"title": "저장 & 공유", "subtitle": "주변 견주에게 알려주세요!"},
    },
    {
        "food_id": "baguette", "food_ko": "바게트", "safety": "caution",
        "folder": "034_baguette_바게트",
        "cover_file": "cover_34_바게트_baguette.png",
        "body1": {"title": "조건부 OK!", "subtitle": "플레인만, 소량 급여 가능"},
        "body2": {"title": "주의사항", "subtitle": "버터/마늘빵 금지, 탄수화물 주의"},
        "cta": {"title": "저장 & 공유", "subtitle": "주변 견주에게 알려주세요!"},
    },
    {
        "food_id": "tteokguk", "food_ko": "떡국", "safety": "caution",
        "folder": "077_tteokguk_떡국",
        "cover_file": "cover_77_떡국_tteokguk2.png",
        "body1": {"title": "조건부 OK!", "subtitle": "떡만 소량, 국물은 위험"},
        "body2": {"title": "주의사항", "subtitle": "떡 질식 위험, 대파/마늘 국물 금지"},
        "cta": {"title": "저장 & 공유", "subtitle": "주변 견주에게 알려주세요!"},
    },
    {
        "food_id": "kimbap", "food_ko": "김밥", "safety": "caution",
        "folder": "080_kimbap_김밥",
        "cover_file": "cover_80_김밥_kimbap.png",
        "body1": {"title": "조건부 OK!", "subtitle": "밥+김+당근만 소량 가능"},
        "body2": {"title": "주의사항", "subtitle": "단무지/시금치/참기름 주의"},
        "cta": {"title": "저장 & 공유", "subtitle": "주변 견주에게 알려주세요!"},
    },
    {
        "food_id": "udon", "food_ko": "우동", "safety": "caution",
        "folder": "083_udon_우동",
        "cover_file": "cover_83_우동_udon.png",
        "body1": {"title": "조건부 OK!", "subtitle": "면만 소량, 국물은 고나트륨"},
        "body2": {"title": "주의사항", "subtitle": "국물 금지, 양파/대파 제거 필수"},
        "cta": {"title": "저장 & 공유", "subtitle": "주변 견주에게 알려주세요!"},
    },
    {
        "food_id": "toast", "food_ko": "토스트", "safety": "caution",
        "folder": "087_toast_토스트",
        "cover_file": "cover_87_토스트_toast.png",
        "body1": {"title": "조건부 OK!", "subtitle": "플레인만 소량, 잼 금지"},
        "body2": {"title": "주의사항", "subtitle": "버터/잼 금지, 밀 알러지 주의"},
        "cta": {"title": "저장 & 공유", "subtitle": "주변 견주에게 알려주세요!"},
    },
    {
        "food_id": "muffin", "food_ko": "머핀", "safety": "caution",
        "folder": "096_muffin_머핀",
        "cover_file": "cover_96_머핀_muffin.png",
        "body1": {"title": "조건부 OK!", "subtitle": "플레인만, 초코/건포도 금지"},
        "body2": {"title": "주의사항", "subtitle": "고당분, 초콜릿 머핀 절대 금지"},
        "cta": {"title": "저장 & 공유", "subtitle": "주변 견주에게 알려주세요!"},
    },
    {
        "food_id": "pancake", "food_ko": "팬케이크", "safety": "caution",
        "folder": "097_pancake_팬케이크",
        "cover_file": "cover_97_팬케이크_pancake.png",
        "body1": {"title": "조건부 OK!", "subtitle": "플레인만, 시럽 금지"},
        "body2": {"title": "주의사항", "subtitle": "시럽/버터 금지, 밀 알러지 주의"},
        "cta": {"title": "저장 & 공유", "subtitle": "주변 견주에게 알려주세요!"},
    },
    {
        "food_id": "waffle", "food_ko": "와플", "safety": "caution",
        "folder": "098_waffle_와플",
        "cover_file": "cover_98_와플_waffle.png",
        "body1": {"title": "조건부 OK!", "subtitle": "플레인만, 토핑 금지"},
        "body2": {"title": "주의사항", "subtitle": "초코/시럽 금지, 고당분 주의"},
        "cta": {"title": "저장 & 공유", "subtitle": "주변 견주에게 알려주세요!"},
    },
    {
        "food_id": "cereal", "food_ko": "시리얼", "safety": "caution",
        "folder": "099_cereal_시리얼",
        "cover_file": "cover_99_시리얼_cereal.png",
        "body1": {"title": "조건부 OK!", "subtitle": "무당 플레인만 소량 가능"},
        "body2": {"title": "주의사항", "subtitle": "초코/설탕 시리얼 금지"},
        "cta": {"title": "저장 & 공유", "subtitle": "주변 견주에게 알려주세요!"},
    },
    {
        "food_id": "granola", "food_ko": "그래놀라", "safety": "caution",
        "folder": "100_granola_그래놀라",
        "cover_file": "cover_100_그래놀라_granola.png",
        "body1": {"title": "조건부 OK!", "subtitle": "무당 소량만, 건포도 제거"},
        "body2": {"title": "주의사항", "subtitle": "건포도/초코칩 제거 필수"},
        "cta": {"title": "저장 & 공유", "subtitle": "주변 견주에게 알려주세요!"},
    },
    {
        "food_id": "meatball", "food_ko": "미트볼", "safety": "caution",
        "folder": "103_meatball_미트볼",
        "cover_file": "cover_103_미트볼_meatball.png",
        "body1": {"title": "조건부 OK!", "subtitle": "수제 무양념 고기만 가능"},
        "body2": {"title": "주의사항", "subtitle": "양파/마늘 양념 금지, 고지방"},
        "cta": {"title": "저장 & 공유", "subtitle": "주변 견주에게 알려주세요!"},
    },
    {
        "food_id": "croissant", "food_ko": "크루아상", "safety": "caution",
        "folder": "111_croissant_크루아상",
        "cover_file": "cover_111_크루아상_croissant.png",
        "body1": {"title": "조건부 OK!", "subtitle": "플레인 소량만, 속재료 금지"},
        "body2": {"title": "주의사항", "subtitle": "고지방 버터, 초코 충전물 금지"},
        "cta": {"title": "저장 & 공유", "subtitle": "주변 견주에게 알려주세요!"},
    },
    {
        "food_id": "perrier", "food_ko": "페리에", "safety": "caution",
        "folder": "120_perrier_페리에",
        "cover_file": "cover_120_페리에_perrier.png",
        "body1": {"title": "조건부 OK!", "subtitle": "소량은 괜찮지만 불필요"},
        "body2": {"title": "주의사항", "subtitle": "탄산 가스로 복부팽만 주의"},
        "cta": {"title": "저장 & 공유", "subtitle": "주변 견주에게 알려주세요!"},
    },
    {
        "food_id": "ritz", "food_ko": "리츠", "safety": "caution",
        "folder": "125_ritz_리츠",
        "cover_file": "cover_125_리츠_ritz.png",
        "body1": {"title": "조건부 OK!", "subtitle": "1-2개 소량만, 양파 확인"},
        "body2": {"title": "주의사항", "subtitle": "고나트륨, 양파 파우더 확인"},
        "cta": {"title": "저장 & 공유", "subtitle": "주변 견주에게 알려주세요!"},
    },
    {
        "food_id": "mushroom", "food_ko": "버섯", "safety": "caution",
        "folder": "175_mushroom_버섯",
        "cover_file": "cover_165_버섯_mushroom.png",
        "body1": {"title": "조건부 OK!", "subtitle": "식용 버섯만 익혀서 소량"},
        "body2": {"title": "주의사항", "subtitle": "야생 버섯 절대 금지, 익혀서만"},
        "cta": {"title": "저장 & 공유", "subtitle": "주변 견주에게 알려주세요!"},
    },

    # ═══════════════════════════════════════════
    # SAFE (13건, 19건 스킵: 폴더/커버 없음)
    # ═══════════════════════════════════════════
    {
        "food_id": "bean_sprouts", "food_ko": "숙주나물", "safety": "safe",
        "folder": "040_bean_sprouts_숙주나물",
        "cover_file": "cover_39_숙주나물_bean_sprouts3.png",
        "body1": {"title": "먹어도 돼요!", "subtitle": "익혀서 급여, 식이섬유 풍부"},
        "body2": {"title": "급여 방법", "subtitle": "데쳐서 무양념, 소량 급여"},
        "cta": {"title": "저장 & 공유", "subtitle": "주변 견주에게 알려주세요!"},
    },
    {
        "food_id": "melon", "food_ko": "멜론", "safety": "safe",
        "folder": "046_melon_멜론",
        "cover_file": "cover_46_멜론_melon2.png",
        "body1": {"title": "먹어도 돼요!", "subtitle": "수분 보충, 비타민 풍부"},
        "body2": {"title": "급여 방법", "subtitle": "씨와 껍질 제거, 소량 급여"},
        "cta": {"title": "저장 & 공유", "subtitle": "주변 견주에게 알려주세요!"},
    },
    {
        "food_id": "pomegranate", "food_ko": "석류", "safety": "caution",
        "folder": "050_pomegranate_석류",
        "cover_file": "cover_49_석류_pomegranate.png",
        "body1": {"title": "조건부 OK!", "subtitle": "과육만 소량, 씨앗 주의"},
        "body2": {"title": "주의사항", "subtitle": "씨앗 장폐색 위험, 타닌 주의"},
        "cta": {"title": "저장 & 공유", "subtitle": "주변 견주에게 알려주세요!"},
    },
    {
        "food_id": "kimchi", "food_ko": "김치", "safety": "danger",
        "folder": "066_kimchi_김치",
        "cover_file": "cover_65_김치_kimchi.png",
        "body1": {"title": "위험해요!", "subtitle": "마늘+양파+고추 함유"},
        "body2": {"title": "위험 성분", "subtitle": "마늘/양파 독성, 고나트륨"},
        "cta": {"title": "저장 & 공유", "subtitle": "주변 견주에게 알려주세요!"},
    },
    {
        "food_id": "quail_egg", "food_ko": "메추리알", "safety": "safe",
        "folder": "070_quail_egg_메추리알",
        "cover_file": "cover_69_메추리알_quail_egg.png",
        "body1": {"title": "먹어도 돼요!", "subtitle": "완숙으로 급여, 단백질 풍부"},
        "body2": {"title": "급여 방법", "subtitle": "껍질 제거, 1일 1-2개 적당"},
        "cta": {"title": "저장 & 공유", "subtitle": "주변 견주에게 알려주세요!"},
    },
    {
        "food_id": "fried_chicken", "food_ko": "후라이드치킨", "safety": "danger",
        "folder": "153_fried_chicken_후라이드치킨",
        "cover_file": "cover_72_후라이드치킨_fried_chicken2.png",
        "body1": {"title": "위험해요!", "subtitle": "튀김 기름, 고지방 고나트륨"},
        "body2": {"title": "위험 성분", "subtitle": "튀김옷, 양념, 뼈 질식 위험"},
        "cta": {"title": "저장 & 공유", "subtitle": "주변 견주에게 알려주세요!"},
    },
    {
        "food_id": "chicken_skewer", "food_ko": "닭꼬치", "safety": "danger",
        "folder": "101_chicken_skewer_닭꼬치",
        "cover_file": "cover_101_닭꼬치_chicken_skewer.png",
        "body1": {"title": "위험해요!", "subtitle": "양념+꼬치, 소화기 손상 위험"},
        "body2": {"title": "위험 성분", "subtitle": "꼬치 삼킴 위험, 양념 독성"},
        "cta": {"title": "저장 & 공유", "subtitle": "주변 견주에게 알려주세요!"},
    },
    {
        "food_id": "chicken_breast", "food_ko": "닭가슴살", "safety": "safe",
        "folder": "139_chicken_breast_닭가슴살",
        "cover_file": "cover_139_닭가슴살_chicken_breast.png",
        "body1": {"title": "먹어도 돼요!", "subtitle": "고단백 저지방, 최고의 간식"},
        "body2": {"title": "급여 방법", "subtitle": "익혀서 무양념, 뼈 제거 필수"},
        "cta": {"title": "저장 & 공유", "subtitle": "주변 견주에게 알려주세요!"},
    },
    {
        "food_id": "white_fish", "food_ko": "흰살생선", "safety": "safe",
        "folder": "132_white_fish_흰살생선",
        "cover_file": "cover_132_흰살생선_white_fish.png",
        "body1": {"title": "먹어도 돼요!", "subtitle": "저지방 고단백, 오메가3 풍부"},
        "body2": {"title": "급여 방법", "subtitle": "익혀서 무양념, 뼈 완전 제거"},
        "cta": {"title": "저장 & 공유", "subtitle": "주변 견주에게 알려주세요!"},
    },
    {
        "food_id": "asparagus", "food_ko": "아스파라거스", "safety": "safe",
        "folder": "170_asparagus_아스파라거스",
        "cover_file": "cover_161_아스파라거스_asparagus.png",
        "body1": {"title": "먹어도 돼요!", "subtitle": "비타민K 풍부, 항산화 효과"},
        "body2": {"title": "급여 방법", "subtitle": "익혀서 잘게 썰어 소량 급여"},
        "cta": {"title": "저장 & 공유", "subtitle": "주변 견주에게 알려주세요!"},
    },
    {
        "food_id": "beet", "food_ko": "비트", "safety": "safe",
        "folder": "176_beet_비트",
        "cover_file": "cover_166_비트_beet.png",
        "body1": {"title": "먹어도 돼요!", "subtitle": "항산화 성분, 해독 효과"},
        "body2": {"title": "급여 방법", "subtitle": "익혀서 소량, 소변 색 변화 정상"},
        "cta": {"title": "저장 & 공유", "subtitle": "주변 견주에게 알려주세요!"},
    },
    {
        "food_id": "peas", "food_ko": "완두콩", "safety": "safe",
        "folder": "172_peas_완두콩",
        "cover_file": "cover_164_완두콩_peas.png",
        "body1": {"title": "먹어도 돼요!", "subtitle": "식이섬유와 비타민 풍부"},
        "body2": {"title": "급여 방법", "subtitle": "익혀서 소량, 가스 발생 주의"},
        "cta": {"title": "저장 & 공유", "subtitle": "주변 견주에게 알려주세요!"},
    },
]

# ============================================
# 스킵 항목 (폴더 또는 커버 없음)
# ============================================
SKIPPED = [
    {"food_id": "green_onion", "food_ko": "대파", "safety": "forbidden", "reason": "커버 소스 없음"},
    {"food_id": "lemon", "food_ko": "레몬", "safety": "danger", "reason": "폴더 없음"},
    {"food_id": "persimmon_ripe", "food_ko": "홍시", "safety": "caution", "reason": "폴더+커버 없음"},
    {"food_id": "plum", "food_ko": "자두", "safety": "caution", "reason": "폴더 없음"},
    {"food_id": "dumpling", "food_ko": "만두", "safety": "caution", "reason": "폴더+커버 없음"},
    {"food_id": "raspberry", "food_ko": "라즈베리", "safety": "safe", "reason": "폴더 없음"},
    {"food_id": "cranberry", "food_ko": "크랜베리", "safety": "safe", "reason": "폴더+커버 없음"},
    {"food_id": "coconut", "food_ko": "코코넛", "safety": "safe", "reason": "폴더 없음"},
    {"food_id": "lettuce", "food_ko": "상추", "safety": "safe", "reason": "폴더 없음"},
    {"food_id": "green_beans", "food_ko": "강낭콩", "safety": "safe", "reason": "폴더 없음"},
    {"food_id": "bell_pepper", "food_ko": "파프리카", "safety": "safe", "reason": "폴더+커버 없음"},
    {"food_id": "napa_cabbage", "food_ko": "배추", "safety": "safe", "reason": "폴더+커버 없음"},
    {"food_id": "radish", "food_ko": "무", "safety": "safe", "reason": "폴더+커버 없음"},
    {"food_id": "corn", "food_ko": "옥수수", "safety": "safe", "reason": "폴더+커버 없음"},
    {"food_id": "pork", "food_ko": "돼지고기", "safety": "safe", "reason": "폴더+커버 없음"},
    {"food_id": "turkey", "food_ko": "칠면조", "safety": "safe", "reason": "폴더+커버 없음"},
    {"food_id": "lamb", "food_ko": "양고기", "safety": "safe", "reason": "폴더+커버 없음"},
    {"food_id": "venison", "food_ko": "사슴고기", "safety": "safe", "reason": "폴더+커버 없음"},
    {"food_id": "rabbit", "food_ko": "토끼고기", "safety": "safe", "reason": "폴더+커버 없음"},
    {"food_id": "chicken_liver", "food_ko": "닭간", "safety": "safe", "reason": "폴더+커버 없음"},
    {"food_id": "beef_liver", "food_ko": "소간", "safety": "safe", "reason": "폴더+커버 없음"},
    {"food_id": "heart", "food_ko": "심장(소/닭)", "safety": "safe", "reason": "폴더+커버 없음"},
    {"food_id": "tripe", "food_ko": "양(위장)", "safety": "safe", "reason": "폴더+커버 없음"},
    {"food_id": "bone_broth", "food_ko": "사골국물", "safety": "safe", "reason": "폴더+커버 없음"},
    {"food_id": "cod", "food_ko": "대구", "safety": "safe", "reason": "폴더+커버 없음"},
]


# ============================================
# CTA 선택 (SHA256 해시)
# ============================================
def select_cta_image(food_id: str) -> Path:
    cta_files = sorted([f for f in BEST_CTA_DIR.iterdir()
                        if f.suffix.lower() in ('.jpg', '.jpeg', '.png')])
    if not cta_files:
        raise FileNotFoundError(f"CTA 이미지 없음: {BEST_CTA_DIR}")
    h = hashlib.sha256(food_id.encode()).hexdigest()
    idx = int(h, 16) % len(cta_files)
    return cta_files[idx]


# ============================================
# text.json 생성
# ============================================
def generate_text_json(item: dict) -> Path:
    food_id = item["food_id"]
    text_data = [
        {"slide": 0, "type": "cover", "title": food_id.upper().replace("_", " "), "subtitle": ""},
        {"slide": 1, "type": "content_bottom", "title": item["body1"]["title"], "subtitle": item["body1"]["subtitle"]},
        {"slide": 2, "type": "content_bottom", "title": item["body2"]["title"], "subtitle": item["body2"]["subtitle"]},
        {"slide": 3, "type": "cta", "title": item["cta"]["title"], "subtitle": item["cta"]["subtitle"]},
    ]
    out_path = TEXT_DIR / f"{food_id}_text.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(text_data, f, ensure_ascii=False, indent=4)
    return out_path


# ============================================
# 단일 아이템 렌더링
# ============================================
def render_item(item: dict) -> dict:
    food_id = item["food_id"]
    safety = item["safety"]
    folder_name = item["folder"]
    cover_file = item["cover_file"]

    result = {"food_id": food_id, "success": False, "rendered": 0, "errors": []}

    # 폴더 확인
    src_folder = CONTENTS_DIR / folder_name
    if not src_folder.exists():
        result["errors"].append(f"폴더 없음: {src_folder}")
        return result

    # 커버 소스 확인
    cover_src = COVER_SOURCE_DIR / cover_file
    if not cover_src.exists():
        result["errors"].append(f"커버소스 없음: {cover_src}")
        return result

    # archive 생성
    archive_dir = src_folder / "archive"
    archive_dir.mkdir(exist_ok=True)

    slides_done = 0

    try:
        # ── Slide 1 (바디①) ──
        bg_01 = archive_dir / f"{food_id}_01_bg.png"
        shutil.copy2(cover_src, bg_01)

        v_config = build_validation_config("body", safety)
        rel_path = str(bg_01.relative_to(PROJECT_ROOT))
        validate_before_render("body", rel_path, v_config)

        img = Image.open(bg_01).resize(TARGET_SIZE, Image.LANCZOS)
        t = strip_emoji(item["body1"]["title"])
        s = strip_emoji(item["body1"]["subtitle"])
        img = render_body(img, t, s, safety)
        out_01 = src_folder / f"{food_id}_01.png"
        img.save(out_01, "PNG")
        validate_v31_slide("body", v_config, str(out_01.relative_to(PROJECT_ROOT)))
        slides_done += 1

        # ── Slide 2 (바디②) ──
        bg_02 = archive_dir / f"{food_id}_02_bg.png"
        shutil.copy2(cover_src, bg_02)

        v_config = build_validation_config("body", safety)
        rel_path = str(bg_02.relative_to(PROJECT_ROOT))
        validate_before_render("body", rel_path, v_config)

        img = Image.open(bg_02).resize(TARGET_SIZE, Image.LANCZOS)
        t = strip_emoji(item["body2"]["title"])
        s = strip_emoji(item["body2"]["subtitle"])
        img = render_body(img, t, s, safety)
        out_02 = src_folder / f"{food_id}_02.png"
        img.save(out_02, "PNG")
        validate_v31_slide("body", v_config, str(out_02.relative_to(PROJECT_ROOT)))
        slides_done += 1

        # ── Slide 3 (CTA) ──
        cta_src = select_cta_image(food_id)
        bg_03 = archive_dir / f"{food_id}_03_bg.png"
        shutil.copy2(cta_src, bg_03)

        v_config = build_validation_config("cta", safety)
        rel_path = str(bg_03.relative_to(PROJECT_ROOT))
        validate_before_render("cta", rel_path, v_config)

        img = Image.open(bg_03).resize(TARGET_SIZE, Image.LANCZOS)
        t = strip_emoji(item["cta"]["title"])
        s = strip_emoji(item["cta"]["subtitle"])
        img = render_cta(img, t, s, bg_path=rel_path)
        out_03 = src_folder / f"{food_id}_03.png"
        img.save(out_03, "PNG")
        validate_v31_slide("cta", v_config, str(out_03.relative_to(PROJECT_ROOT)))
        slides_done += 1

        result["success"] = True
        result["rendered"] = slides_done

    except Exception as e:
        result["errors"].append(str(e))
        result["rendered"] = slides_done

    return result


# ============================================
# 폴더 이동 (1_cover_only → 2_body_ready)
# ============================================
def move_folder(item: dict):
    src = CONTENTS_DIR / item["folder"]
    dst = BODY_READY_DIR / item["folder"]
    if src.exists() and not dst.exists():
        shutil.move(str(src), str(dst))
        return True
    return False


# ============================================
# 배치 실행
# ============================================
def run_batch(batch_name: str):
    batch_items = [i for i in ITEMS if i["safety"] == batch_name.lower()]
    batch_skipped = [s for s in SKIPPED if s["safety"] == batch_name.lower()]

    if not batch_items and not batch_skipped:
        print(f"배치 '{batch_name}': 해당 항목 없음")
        return

    print(f"\n{'='*70}")
    print(f"[B그룹 배치: {batch_name.upper()}] {len(batch_items)}건 처리, {len(batch_skipped)}건 스킵")
    print(f"{'='*70}")

    if batch_skipped:
        print(f"\n⚠️ 스킵 항목 ({len(batch_skipped)}건):")
        for s in batch_skipped:
            print(f"  - {s['food_id']:<20} ({s['food_ko']}) : {s['reason']}")

    results = []
    for idx, item in enumerate(batch_items, 1):
        food_id = item["food_id"]
        print(f"\n[{idx}/{len(batch_items)}] {food_id} ({item['food_ko']})")

        # text.json 생성
        text_path = generate_text_json(item)
        print(f"  text.json: {text_path.name}")

        # 렌더링
        r = render_item(item)
        results.append(r)

        if r["success"]:
            # 폴더 이동
            moved = move_folder(item)
            move_str = "→ 2_body_ready/" if moved else "(이미 이동됨)"
            print(f"  ✅ {r['rendered']}/3장 렌더링 완료 {move_str}")
        else:
            print(f"  ❌ 실패 ({r['rendered']}/3장): {'; '.join(r['errors'])}")

    # 배치 결과 출력
    success_count = sum(1 for r in results if r["success"])
    total_rendered = sum(r["rendered"] for r in results)

    print(f"\n{'='*70}")
    print(f"[배치 완료: {batch_name.upper()}]")
    print(f"{'='*70}")
    print(f"  처리: {success_count}/{len(batch_items)}건")
    print(f"  렌더링: {total_rendered}/{len(batch_items) * 3}장")
    print(f"  스킵: {len(batch_skipped)}건")

    # 건별 결과 테이블
    print(f"\n  | # | 영문명{'':15} | text.json | 렌더링 | validators | 비고 |")
    print(f"  |---|{'':20}-|-----------|--------|-----------|------|")
    for i, r in enumerate(results, 1):
        tj = "✅"
        rn = f"{r['rendered']}/3"
        vl = "PASS" if r["success"] else "FAIL"
        note = "" if r["success"] else "; ".join(r["errors"])[:30]
        print(f"  | {i} | {r['food_id']:<20} | {tj:9} | {rn:6} | {vl:9} | {note} |")

    # 실패 건 상세
    failures = [r for r in results if not r["success"]]
    if failures:
        print(f"\n  실패 건 ({len(failures)}건):")
        for r in failures:
            print(f"    - {r['food_id']}: {'; '.join(r['errors'])}")

    # JSON 보고서 저장
    report = {
        "work_order": "WO-2026-0205-002",
        "batch": batch_name.upper(),
        "executed_at": datetime.now().isoformat(),
        "total_items": len(batch_items),
        "success_count": success_count,
        "total_rendered": total_rendered,
        "skipped": len(batch_skipped),
        "results": results,
        "skipped_items": batch_skipped,
    }
    report_path = PROJECT_ROOT / "config" / "data" / f"wo_002_batch_{batch_name.lower()}.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n  보고서: {report_path.name}")

    return results


# ============================================
# 메인
# ============================================
def main():
    if len(sys.argv) < 2:
        print("사용법: python batch_render_b_group.py <forbidden|danger|caution|safe|all>")
        sys.exit(1)

    target = sys.argv[1].lower()
    start_time = datetime.now()

    if target == "all":
        for batch in ["forbidden", "danger", "caution", "safe"]:
            run_batch(batch)
    elif target in ("forbidden", "danger", "caution", "safe"):
        run_batch(target)
    else:
        print(f"알 수 없는 배치: {target}")
        sys.exit(1)

    elapsed = (datetime.now() - start_time).total_seconds()
    print(f"\n총 소요: {elapsed:.1f}초")


if __name__ == "__main__":
    main()
