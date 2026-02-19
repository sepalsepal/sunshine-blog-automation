"""
# ============================================================
# 🚀 PublisherAgent - 게시 에이전트
# ============================================================
#
# 📋 이 파일의 역할:
#    우리가 만든 이미지들을 인터넷에 올리는 역할을 해요!
#    1. Cloudinary (이미지 저장소)에 업로드
#    2. Instagram에 캐러셀(여러 장)로 게시
#
# 🎯 왜 두 단계로 나눠서 할까요?
#    Instagram은 우리 컴퓨터에 있는 파일을 직접 못 받아요.
#    그래서 먼저 Cloudinary라는 '클라우드 저장소'에 올리고,
#    그 URL(인터넷 주소)을 Instagram에 알려주는 방식이에요.
#
# 💡 비유하자면:
#    - Cloudinary = 구글 드라이브 같은 파일 저장소
#    - Instagram API = Instagram 앱 대신 코드로 게시하는 방법
#
# Author: 최기술 대리
# ============================================================
"""

# ============================================================
# 📦 필요한 라이브러리 가져오기 (import)
#
# 💡 import란?
#    다른 사람이 만든 코드를 가져다 쓰는 것이에요.
#    마치 레고 블록처럼, 이미 만들어진 기능을 조립해서 사용해요.
# ============================================================

import os           # 운영체제 기능 (환경변수 읽기 등)
import asyncio      # 비동기 처리 (여러 작업을 동시에!)
import aiohttp      # 인터넷 요청 보내기 (Instagram API 호출용)
import ssl          # SSL 인증서 처리
import certifi      # Mozilla CA 인증서 번들
from typing import Any, Dict, List, Optional  # 타입 힌트 (코드 가독성용)
from pathlib import Path  # 파일 경로 다루기
from .base import BaseAgent, AgentResult, retry  # 우리가 만든 기본 에이전트

# ------------------------------------------------------------
# ☁️ Cloudinary 라이브러리 불러오기
#
# try-except란?
#    "이 코드를 시도해보고, 안 되면 except로 가라"는 뜻이에요.
#    Cloudinary가 설치 안 됐을 수도 있으니까 대비하는 거예요.
# ------------------------------------------------------------
try:
    import cloudinary
    import cloudinary.uploader
    import cloudinary.api
    CLOUDINARY_AVAILABLE = True  # 설치됨!
except ImportError:
    CLOUDINARY_AVAILABLE = False  # 설치 안 됨

# ------------------------------------------------------------
# 📸 Instagram Graph API 설정
#
# 💡 API 버전이란?
#    Meta(Facebook)는 Instagram API를 계속 업데이트해요.
#    버전을 명시해야 어떤 기능을 쓸지 알 수 있어요.
#    v21.0 = 2024년 기준 최신 버전
# ------------------------------------------------------------
INSTAGRAM_GRAPH_API_VERSION = "v21.0"
INSTAGRAM_GRAPH_API_BASE = f"https://graph.facebook.com/{INSTAGRAM_GRAPH_API_VERSION}"


# ============================================================
# 🎯 PublisherAgent 클래스
#
# 클래스란?
#    비슷한 기능을 묶어놓은 '설계도'예요.
#    이 설계도로 실제 '게시 담당자'를 만들어요.
# ============================================================
class PublisherAgent(BaseAgent):
    """
    ╔════════════════════════════════════════════════════════╗
    ║  🚀 멀티 플랫폼 게시 에이전트                              ║
    ╠════════════════════════════════════════════════════════╣
    ║  이 에이전트가 하는 일:                                   ║
    ║  1. Cloudinary에 이미지 업로드                           ║
    ║  2. Instagram에 캐러셀 게시                              ║
    ║  3. (향후) Twitter, Threads 등 추가 예정                  ║
    ╚════════════════════════════════════════════════════════╝
    """

    # --------------------------------------------------------
    # 📌 에이전트 이름 설정
    #
    # @property란?
    #    함수인데 변수처럼 쓸 수 있게 해주는 마법이에요.
    #    agent.name 하면 "Publisher"가 나와요.
    # --------------------------------------------------------
    @property
    def name(self) -> str:
        return "Publisher"

    # --------------------------------------------------------
    # 🏗️ 초기화 함수 (__init__)
    #
    # __init__이란?
    #    에이전트가 '태어날 때' 실행되는 함수예요.
    #    필요한 준비를 여기서 해요.
    # --------------------------------------------------------
    def __init__(self, config_path: str = None):
        # 부모 클래스(BaseAgent)의 초기화 먼저 실행
        super().__init__(config_path)

        # Cloudinary 설정 실행
        self._setup_cloudinary()

    # --------------------------------------------------------
    # ☁️ Cloudinary 설정 함수
    #
    # Cloudinary란?
    #    이미지를 저장하고 관리해주는 클라우드 서비스예요.
    #    우리 이미지에 URL(인터넷 주소)을 만들어줘요.
    # --------------------------------------------------------
    def _setup_cloudinary(self):
        """Cloudinary 연결 설정"""

        # Cloudinary 라이브러리가 없으면 경고만 하고 넘어감
        if not CLOUDINARY_AVAILABLE:
            self.log("⚠️ Cloudinary 라이브러리가 설치되지 않았어요", level="warning")
            self.log("   해결: pip install cloudinary", level="warning")
            return

        # ----------------------------------------------------
        # 📌 환경변수에서 인증 정보 가져오기
        #
        # 환경변수(Environment Variable)란?
        #    비밀번호 같은 민감한 정보를 코드에 직접 쓰면 위험해요!
        #    그래서 컴퓨터 설정에 따로 저장해두는 방식이에요.
        #
        # 설정 방법 (터미널에서):
        #    export CLOUDINARY_API_KEY="여기에_키_입력"
        #    export CLOUDINARY_API_SECRET="여기에_시크릿_입력"
        # ----------------------------------------------------
        cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME", "ddzbnrfei")  # 기본값 있음
        api_key = os.getenv("CLOUDINARY_API_KEY")      # 환경변수에서 가져옴
        api_secret = os.getenv("CLOUDINARY_API_SECRET")  # 환경변수에서 가져옴

        # API 키가 있으면 Cloudinary 연결
        if api_key and api_secret:
            cloudinary.config(
                cloud_name=cloud_name,
                api_key=api_key,
                api_secret=api_secret,
                secure=True  # HTTPS 사용 (보안!)
            )
            self.log("✅ Cloudinary 연결 완료!")
        else:
            self.log("⚠️ Cloudinary API 키가 없어요", level="warning")
            self.log("   환경변수를 설정해주세요:", level="warning")
            self.log("   export CLOUDINARY_API_KEY='your_key'", level="warning")

    # ============================================================
    # 🎯 메인 실행 함수 (execute)
    #
    # ╔════════════════════════════════════════════════════════╗
    # ║  📋 전체 흐름도                                          ║
    # ╠════════════════════════════════════════════════════════╣
    # ║  1. QA 통과 확인                                        ║
    # ║     ↓                                                   ║
    # ║  2. 이미지 경로 수집                                     ║
    # ║     ↓                                                   ║
    # ║  3. Cloudinary에 업로드 → URL 획득                       ║
    # ║     ↓                                                   ║
    # ║  4. Instagram에 캐러셀 게시                              ║
    # ║     ↓                                                   ║
    # ║  5. 결과 반환                                           ║
    # ╚════════════════════════════════════════════════════════╝
    # ============================================================
    async def execute(self, input_data: Any) -> AgentResult:
        """
        🚀 게시 실행 - 메인 함수

        [입력 데이터 형식]
        input_data = {
            "images": ["이미지경로1", "이미지경로2", ...],
            "topic": "apple",      # 주제 (사과, 체리 등)
            "passed": True         # QA 통과 여부
        }

        [반환값]
        AgentResult = {
            "success": True/False,
            "data": { 업로드 결과들... }
        }
        """

        # --------------------------------------------------------
        # 📌 Step 1: QA 통과 확인
        #
        # 품질 검수(QA)를 통과하지 못한 이미지는 게시하면 안 돼요!
        # passed가 False면 바로 중단합니다.
        # --------------------------------------------------------
        if not input_data.get("passed", True):  # 기본값 True
            return AgentResult(
                success=False,
                error="❌ 품질 검수 실패 - 게시를 중단합니다",
                data={"reason": "QA failed"}
            )

        # --------------------------------------------------------
        # 📌 Step 2: 입력 데이터에서 정보 추출
        # --------------------------------------------------------
        images = input_data.get("images", [])   # 이미지 목록
        topic = input_data.get("topic", "unknown")  # 주제

        # --------------------------------------------------------
        # 📌 Step 3: 이미지 경로 정리
        #
        # 이미지가 여러 형식으로 올 수 있어요:
        #   - 문자열: "path/to/image.png"
        #   - 딕셔너리: {"path": "path/to/image.png"}
        # 둘 다 처리할 수 있게 정규화해요.
        # --------------------------------------------------------
        all_image_paths = []
        for img in images:
            # 딕셔너리 형식이면 "path" 키에서 꺼냄
            if isinstance(img, dict):
                path = img.get("path", "")
            else:
                path = img

            # 파일이 실제로 존재하는지 확인
            if path and Path(path).exists():
                all_image_paths.append(path)

        # --------------------------------------------------------
        # 📌 Step 3-1: 텍스트 합성본만 필터링
        #
        # ⚠️ 중요: Cloudinary + Instagram에는 텍스트 합성본만!
        #    파일명에 타입 접미사가 있는 것이 텍스트 합성본
        #    예: apple_00_cover.png, apple_01_result.png
        # --------------------------------------------------------
        type_suffixes = ['_cover', '_content', '_result', '_benefit', '_caution', '_amount', '_story', '_cta']

        image_paths = []
        for path in all_image_paths:
            filename = Path(path).name
            # 텍스트 합성본인지 확인
            is_overlay = any(suffix in filename for suffix in type_suffixes)
            if is_overlay:
                image_paths.append(path)

        # 텍스트 합성본이 없으면 전체 사용 (fallback)
        if not image_paths:
            image_paths = all_image_paths
            self.log(f"📌 텍스트 합성본 없음, 전체 이미지 사용: {len(image_paths)}장")
        else:
            self.log(f"📌 텍스트 합성본 선택: {len(image_paths)}장")

        # --------------------------------------------------------
        # 📌 Step 3-2: 이미지가 없으면 output_dir에서 찾기
        #
        # ⚠️ 중요: 중복 업로드 방지!
        #    output_dir에는 여러 종류의 이미지가 있을 수 있어요:
        #
        #    [텍스트 합성본] - Instagram에 올릴 최종 이미지!
        #    예: apple_00_cover.png, apple_01_result.png,
        #        apple_02_benefit1.png, apple_09_cta.png
        #    → 파일명에 타입 접미사(_cover, _result, _benefit 등)가 붙어있음
        #
        #    [기본 이미지] - 텍스트 없는 원본
        #    예: apple_00.png, apple_01.png
        #    → 숫자만 있는 단순한 파일명
        #
        #    Instagram에는 텍스트 합성본을 올려야 해요!
        # --------------------------------------------------------
        if not image_paths:
            output_dir = input_data.get("output_dir")
            if output_dir:
                output_path = Path(output_dir)
                if output_path.exists():
                    # 모든 .png 파일 목록 (숨김 파일 제외)
                    all_files = [f for f in os.listdir(output_path)
                                 if f.endswith('.png') and not f.startswith('.')]

                    # --------------------------------------------
                    # 📌 텍스트 합성본 파일 식별
                    #
                    # 텍스트 합성본 파일명 패턴:
                    # - {topic}_{번호}_{타입}.png
                    # - 타입: cover, result, benefit1~3, caution1~3, story, cta
                    #
                    # 기본 이미지 파일명 패턴:
                    # - {topic}_{번호}.png (타입 없음)
                    # --------------------------------------------
                    type_suffixes = ['_cover', '_content', '_result', '_benefit', '_caution', '_amount', '_story', '_cta']

                    # 텍스트 합성본 찾기 (타입 접미사가 있는 파일)
                    overlay_files = []
                    for f in all_files:
                        # topic으로 시작하고 타입 접미사가 있는 파일
                        if f.startswith(f"{topic}_"):
                            for suffix in type_suffixes:
                                if suffix in f:
                                    overlay_files.append(f)
                                    break

                    # 정렬 (번호 순서대로)
                    overlay_files = sorted(set(overlay_files))  # 중복 제거 후 정렬

                    # 기본 이미지 (타입 접미사 없는 파일)
                    base_files = []
                    for f in all_files:
                        if f.startswith(f"{topic}_"):
                            is_overlay = False
                            for suffix in type_suffixes:
                                if suffix in f:
                                    is_overlay = True
                                    break
                            if not is_overlay:
                                base_files.append(f)
                    base_files = sorted(base_files)

                    # --------------------------------------------
                    # 📌 이미지 선택 (텍스트 합성본 우선!)
                    # --------------------------------------------
                    if overlay_files:
                        # 텍스트 합성본 사용 (최대 10장)
                        selected_files = overlay_files[:10]
                        self.log(f"📌 텍스트 합성본 선택: {len(selected_files)}장")
                        for f in selected_files[:3]:  # 처음 3개만 로그
                            self.log(f"   → {f}")
                        if len(selected_files) > 3:
                            self.log(f"   → ... 외 {len(selected_files) - 3}개")
                    else:
                        # 텍스트 합성본 없으면 기본 이미지 사용
                        selected_files = base_files[:10]
                        self.log(f"📌 기본 이미지 선택: {len(selected_files)}장 (텍스트 합성본 없음)")

                    image_paths = [str(output_path / f) for f in selected_files]

        # 이미지가 하나도 없으면 에러
        if not image_paths:
            return AgentResult(
                success=False,
                error="❌ 업로드할 이미지가 없어요!"
            )

        self.log(f"📤 {len(image_paths)}개 이미지 업로드 시작")

        # --------------------------------------------------------
        # 📌 Step 4: 플랫폼별 게시 실행
        #
        # config.yaml에서 어떤 플랫폼에 게시할지 읽어와요.
        # 기본값: ["cloudinary"] (Cloudinary만)
        # --------------------------------------------------------
        platforms = self.config.get("platforms", ["cloudinary"])
        results = {}           # 각 플랫폼 결과 저장
        cloudinary_urls = []   # Cloudinary URL들 (Instagram에서 사용)

        # ----------------------------------------------------
        # ☁️ Cloudinary 먼저 처리
        #
        # ⚠️ 왜 Cloudinary를 먼저 할까요?
        #    Instagram은 이미지 파일을 직접 못 받아요.
        #    인터넷 URL이 필요해요!
        #    그래서 Cloudinary에 먼저 올려서 URL을 받아요.
        # ----------------------------------------------------
        if "cloudinary" in platforms:
            result = await self._upload_cloudinary(image_paths, topic)
            results["cloudinary"] = result

            # 업로드 성공하면 URL 목록 저장
            if result.get("success"):
                cloudinary_urls = [
                    u.get("secure_url")
                    for u in result.get("urls", [])
                ]

        # ----------------------------------------------------
        # 📸 나머지 플랫폼 처리
        # ----------------------------------------------------
        for platform in platforms:
            if platform == "cloudinary":
                continue  # 이미 위에서 처리함

            elif platform == "instagram":
                # Instagram은 Cloudinary URL이 필요!
                if cloudinary_urls:
                    result = await self._publish_instagram(cloudinary_urls, topic)
                else:
                    result = {
                        "success": False,
                        "error": "❌ Cloudinary URL이 없어요! 먼저 Cloudinary 업로드가 필요해요."
                    }
                results["instagram"] = result

        # --------------------------------------------------------
        # 📌 Step 5: 최종 결과 반환
        #
        # 하나라도 성공하면 전체 성공으로 처리해요.
        # --------------------------------------------------------
        any_success = any(r.get("success") for r in results.values())

        return AgentResult(
            success=any_success,
            data={
                "publish_results": results,
                "topic": topic,
                "uploaded_count": sum(
                    r.get("count", 0)
                    for r in results.values()
                    if r.get("success")
                )
            },
            metadata={
                "platforms": list(results.keys()),
                "success_platforms": [
                    p for p, r in results.items()
                    if r.get("success")
                ]
            }
        )

    # ============================================================
    # ☁️ Cloudinary 업로드 함수
    #
    # @retry란?
    #    실패하면 자동으로 다시 시도해요.
    #    max_attempts=3 → 최대 3번
    #    delay=2.0 → 2초 쉬었다가 재시도
    # ============================================================
    @retry(max_attempts=3, delay=2.0)
    async def _upload_cloudinary(self, image_paths: List[str], topic: str) -> Dict:
        """
        ☁️ Cloudinary에 이미지 업로드

        [왜 Cloudinary를 쓰나요?]
        1. 이미지에 URL(인터넷 주소)을 만들어줘요
        2. Instagram이 이 URL로 이미지를 가져가요
        3. 빠르고 안정적이에요!

        [입력]
        - image_paths: 업로드할 이미지 파일 경로들
        - topic: 주제 (폴더 이름으로 사용)

        [출력]
        {"success": True, "urls": [...], "count": 10}
        """

        # Cloudinary가 설치 안 됐으면 에러
        if not CLOUDINARY_AVAILABLE:
            return {
                "success": False,
                "error": "❌ Cloudinary 라이브러리가 없어요!\n   해결: pip install cloudinary"
            }

        # API 키가 없으면 시뮬레이션 모드로 실행
        if not os.getenv("CLOUDINARY_API_KEY"):
            self.log("🔸 Cloudinary 시뮬레이션 모드 (API 키 없음)", level="warning")
            return await self._simulate_cloudinary_upload(image_paths, topic)

        # ----------------------------------------------------
        # 📌 실제 업로드 시작
        # ----------------------------------------------------
        folder = f"project_sunshine/{topic}"  # 저장될 폴더
        urls = []      # 성공한 URL들
        errors = []    # 실패한 것들

        for i, image_path in enumerate(image_paths):
            try:
                # 파일 이름 생성 (예: apple_00, apple_01, ...)
                public_id = f"{topic}_{i:02d}"

                # --------------------------------------------
                # 🚀 Cloudinary에 업로드!
                #
                # cloudinary.uploader.upload() 함수 설명:
                #   - image_path: 업로드할 파일
                #   - folder: 저장할 폴더 이름
                #   - public_id: 파일 이름 (URL에 표시됨)
                #   - overwrite: 같은 이름 있으면 덮어쓰기
                # --------------------------------------------
                result = cloudinary.uploader.upload(
                    image_path,
                    folder=folder,
                    public_id=public_id,
                    overwrite=True,
                    resource_type="image"
                )

                # 성공! URL 저장
                urls.append({
                    "index": i,
                    "public_id": result.get("public_id"),
                    "secure_url": result.get("secure_url"),  # HTTPS URL
                    "format": result.get("format"),
                    "bytes": result.get("bytes")
                })

                self.log(f"  ✅ {Path(image_path).name} → Cloudinary")

            except Exception as e:
                # 실패... 에러 기록
                errors.append({
                    "index": i,
                    "file": Path(image_path).name,
                    "error": str(e)
                })
                self.log(f"  ❌ {Path(image_path).name}: {e}", level="error")

        # 하나라도 성공하면 성공으로 처리
        success = len(urls) > 0
        return {
            "success": success,
            "urls": urls,
            "count": len(urls),
            "errors": errors,
            "folder": folder
        }

    # ============================================================
    # 🔸 Cloudinary 시뮬레이션 (테스트용)
    # ============================================================
    async def _simulate_cloudinary_upload(self, image_paths: List[str], topic: str) -> Dict:
        """API 키 없을 때 가짜로 실행 (테스트용)"""
        folder = f"project_sunshine/{topic}"
        urls = []

        for i, image_path in enumerate(image_paths):
            # 가짜 URL 생성
            urls.append({
                "index": i,
                "public_id": f"{folder}/{topic}_{i:02d}",
                "secure_url": f"https://res.cloudinary.com/ddzbnrfei/image/upload/{folder}/{topic}_{i:02d}.png",
                "simulated": True  # 시뮬레이션임을 표시
            })
            self.log(f"  🔸 [SIM] {Path(image_path).name} → Cloudinary")

        return {
            "success": True,
            "urls": urls,
            "count": len(urls),
            "folder": folder,
            "simulated": True
        }

    # ============================================================
    # 📸 Instagram 캐러셀 게시 함수
    #
    # ╔════════════════════════════════════════════════════════════╗
    # ║  🎯 이 함수의 목적: 인스타그램에 캐러셀(여러 장) 게시          ║
    # ║                                                            ║
    # ║  💡 왜 필요한가?                                            ║
    # ║  - 우리가 만든 10장의 이미지를 인스타그램에 올리려면          ║
    # ║  - Meta(페이스북)에서 제공하는 API를 사용해야 해요            ║
    # ║  - API = 프로그램끼리 대화하는 방법이라고 생각하면 됩니다     ║
    # ╚════════════════════════════════════════════════════════════╝
    #
    # ┌─────────────────────────────────────────────────────────────┐
    # │  📋 Instagram 캐러셀 게시 3단계 흐름                          │
    # ├─────────────────────────────────────────────────────────────┤
    # │                                                             │
    # │  [1단계] 각 이미지 → 미디어 컨테이너 생성                      │
    # │          (아직 게시 X, 준비만 하는 거예요)                     │
    # │                     ↓                                       │
    # │  [2단계] 컨테이너들 → 캐러셀로 묶기                            │
    # │          (10장을 하나의 게시물로 합치기)                       │
    # │                     ↓                                       │
    # │  [3단계] 캐러셀 → 실제 게시!                                  │
    # │          (이때 비로소 인스타그램에 올라가요)                   │
    # │                                                             │
    # └─────────────────────────────────────────────────────────────┘
    # ============================================================
    async def _publish_instagram(self, image_urls: List[str], topic: str) -> Dict:
        """
        📸 인스타그램 캐러셀 게시 함수

        [입력 파라미터]
        - image_urls: Cloudinary에 업로드된 이미지 URL 리스트
                      예: ["https://res.cloudinary.com/.../apple_00.png", ...]
        - topic: 주제 (캡션 생성에 사용)
                 예: "apple", "cherry"

        [반환값]
        성공 시: {"success": True, "post_id": "...", "permalink": "..."}
        실패 시: {"success": False, "error": "에러 메시지"}

        [캐러셀 제한]
        - 최소 2장, 최대 10장까지 가능해요!
        """

        # --------------------------------------------------------
        # 📌 1단계: 환경변수에서 인증 정보 가져오기
        #
        # 💡 환경변수란?
        #    비밀번호처럼 민감한 정보를 코드에 직접 쓰지 않고
        #    컴퓨터 설정에 따로 저장해두는 방식이에요.
        #    보안상 매우 중요합니다!
        #
        # ⚠️ 설정 방법 (터미널에서):
        #    export INSTAGRAM_ACCESS_TOKEN="your_token"
        #    export INSTAGRAM_BUSINESS_ACCOUNT_ID="your_id"
        # --------------------------------------------------------
        access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
        ig_user_id = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID")

        # 토큰이나 계정 ID가 없으면 시뮬레이션 모드
        if not access_token or not ig_user_id:
            self.log("🔸 Instagram 시뮬레이션 모드 (토큰/계정ID 없음)", level="warning")
            self.log("   설정 방법:", level="warning")
            self.log("   export INSTAGRAM_ACCESS_TOKEN='your_token'", level="warning")
            self.log("   export INSTAGRAM_BUSINESS_ACCOUNT_ID='your_id'", level="warning")
            return await self._simulate_instagram_publish(image_urls, topic)

        # --------------------------------------------------------
        # 📌 2단계: 이미지 개수 확인 (최대 10장)
        #
        # 💡 Instagram 캐러셀은 최대 10장까지만 가능해요!
        #    11장 이상이면 앞에서 10장만 사용해요.
        # --------------------------------------------------------
        urls_to_post = image_urls[:10]  # 최대 10장
        self.log(f"📸 Instagram 캐러셀 게시 시작 ({len(urls_to_post)}장)")

        try:
            # ----------------------------------------------------
            # 📌 aiohttp 세션 시작
            #
            # 💡 aiohttp란?
            #    인터넷 요청을 보내는 라이브러리예요.
            #    async/await과 함께 사용하면 빠르게 처리할 수 있어요.
            #
            # 💡 async with란?
            #    사용이 끝나면 자동으로 연결을 정리해줘요.
            #    "with문 끝나면 알아서 닫아줘~" 같은 느낌이에요.
            # ----------------------------------------------------
            # SSL 컨텍스트 생성 (certifi CA 번들 사용)
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:

                # ================================================
                # 🎯 STEP 1: 각 이미지별 미디어 컨테이너 생성
                #
                # 💡 컨테이너란?
                #    이미지를 Instagram 서버에 '등록'하는 거예요.
                #    아직 게시는 안 되고, 준비만 하는 단계!
                #
                #    비유: 택배 보내기 전에 박스에 담는 것
                # ================================================
                container_ids = []  # 생성된 컨테이너 ID들 저장

                for i, url in enumerate(urls_to_post):
                    # 컨테이너 생성 요청
                    container_id = await self._create_instagram_media_container(
                        session=session,
                        ig_user_id=ig_user_id,
                        access_token=access_token,
                        image_url=url,
                        is_carousel_item=True  # 캐러셀 아이템임을 표시!
                    )

                    if container_id:
                        container_ids.append(container_id)
                        self.log(f"  [{i+1}/{len(urls_to_post)}] ✅ 미디어 컨테이너 생성 완료")
                    else:
                        self.log(f"  [{i+1}/{len(urls_to_post)}] ❌ 미디어 컨테이너 생성 실패", level="error")

                # ------------------------------------------------
                # ⚠️ 캐러셀은 최소 2장 필요!
                # ------------------------------------------------
                if len(container_ids) < 2:
                    return {
                        "success": False,
                        "error": f"❌ 캐러셀은 최소 2장이 필요해요! (현재: {len(container_ids)}장)"
                    }

                # ================================================
                # 🎯 STEP 2: 캐러셀 컨테이너 생성
                #
                # 💡 캐러셀 컨테이너란?
                #    여러 개의 미디어 컨테이너를 하나로 묶는 거예요.
                #    "이 이미지들을 한 게시물로 묶어줘!"
                # ================================================
                caption = self._generate_caption(topic)  # 캡션 생성

                carousel_id = await self._create_instagram_carousel(
                    session=session,
                    ig_user_id=ig_user_id,
                    access_token=access_token,
                    children_ids=container_ids,  # 위에서 만든 컨테이너들
                    caption=caption
                )

                if not carousel_id:
                    return {
                        "success": False,
                        "error": "❌ 캐러셀 컨테이너 생성 실패"
                    }

                self.log("✅ 캐러셀 컨테이너 생성 완료")

                # ================================================
                # 🎯 STEP 3: 실제 게시!
                #
                # 💡 이제 진짜로 Instagram에 올라가요!
                #    media_publish 엔드포인트를 호출합니다.
                #
                # ⚠️ Instagram은 미디어 처리에 시간이 필요해요!
                #    컨테이너 생성 후 10초 대기
                # ================================================
                # 미디어 상태 확인 (FINISHED 될 때까지 대기)
                self.log("⏳ Instagram 미디어 처리 상태 확인 중...")
                max_wait = 120  # 최대 120초 대기 (7장 이상일 경우 오래 걸림)
                wait_interval = 5  # 5초마다 체크
                waited = 0
                empty_count = 0  # 빈 상태 연속 횟수

                while waited < max_wait:
                    status_url = f"{INSTAGRAM_GRAPH_API_BASE}/{carousel_id}"
                    status_params = {
                        "fields": "status_code",
                        "access_token": access_token
                    }
                    async with session.get(status_url, params=status_params) as resp:
                        status_result = await resp.json()
                        status_code = status_result.get("status_code", "")
                        self.log(f"   상태: {status_code if status_code else '(처리중)'}")

                        if status_code == "FINISHED":
                            self.log("✅ 미디어 처리 완료!")
                            break
                        elif status_code == "ERROR":
                            self.log("❌ 미디어 처리 오류!", level="error")
                            return {
                                "success": False,
                                "error": "❌ Instagram 미디어 처리 오류"
                            }
                        elif not status_code:
                            empty_count += 1
                            if empty_count >= 10:  # 50초 이상 빈 상태면 진행
                                self.log("⚠️ 상태 확인 타임아웃, 게시 시도...")
                                break

                    await asyncio.sleep(wait_interval)
                    waited += wait_interval

                publish_result = await self._publish_instagram_media(
                    session=session,
                    ig_user_id=ig_user_id,
                    access_token=access_token,
                    creation_id=carousel_id
                )

                # ------------------------------------------------
                # 📌 결과 확인 (2026-02-04 강화)
                #
                # 🔐 게시 성공 판정 규칙:
                # 1. API 호출 성공 ≠ 게시 성공
                # 2. 성공 조건 = media_id 존재
                # 3. media_id 없으면 무조건 실패 처리
                # ------------------------------------------------
                raw_id = publish_result.get("id")
                post_id = str(raw_id) if raw_id else None  # 🔴 str() 변환 필수

                # media_id (post_id) 존재 여부 확인
                if not post_id:
                    # ❌ media_id 없음 = 게시 실패
                    error_info = publish_result.get("error", {})
                    error_msg = error_info.get("message", "media_id 없음") if isinstance(error_info, dict) else str(error_info)
                    self.log(f"❌ 게시 실패: media_id 없음 (응답: {publish_result})", level="error")
                    return {
                        "success": False,
                        "error": f"❌ 게시 실패: {error_msg}",
                        "raw_response": publish_result
                    }

                # media_id 유효성 검사 (Instagram media_id는 숫자로 구성)
                if not str(post_id).isdigit():
                    self.log(f"⚠️ 의심스러운 post_id 형식: {post_id}", level="warning")

                # 🎉 성공! (media_id 존재 확인됨)
                self.log(f"🎉 Instagram 게시 완료! (ID: {post_id})")

                # 게시물 정보 조회 (permalink = 게시물 URL)
                post_info = await self._get_instagram_post_info(
                    session, post_id, access_token
                )

                # permalink 존재 여부로 실제 게시 이중 확인
                permalink = post_info.get("permalink", "")
                if not permalink:
                    self.log(f"⚠️ permalink 조회 실패 - 게시물 존재 여부 불확실", level="warning")

                return {
                    "success": True,
                    "post_id": post_id,
                    "permalink": permalink,
                    "container_count": len(container_ids),
                    "caption": caption,
                    "verified": bool(permalink)  # permalink 조회 성공 여부
                }

        # --------------------------------------------------------
        # ⚠️ 에러 처리
        # --------------------------------------------------------
        except aiohttp.ClientError as e:
            # 네트워크 오류 (인터넷 연결 문제 등)
            return {
                "success": False,
                "error": f"❌ 네트워크 오류: {str(e)}\n   인터넷 연결을 확인해주세요!"
            }
        except Exception as e:
            # 기타 오류
            return {
                "success": False,
                "error": f"❌ Instagram 게시 오류: {str(e)}"
            }

    # ============================================================
    # 📦 미디어 컨테이너 생성 함수
    #
    # 💡 이 함수가 하는 일:
    #    이미지 URL을 Instagram 서버에 등록해요.
    #    등록하면 "컨테이너 ID"를 받아요.
    #    이 ID로 나중에 게시할 수 있어요!
    # ============================================================
    async def _create_instagram_media_container(
        self,
        session: aiohttp.ClientSession,
        ig_user_id: str,
        access_token: str,
        image_url: str,
        is_carousel_item: bool = False
    ) -> Optional[str]:
        """
        📦 Instagram 미디어 컨테이너 생성

        [API 엔드포인트]
        POST https://graph.facebook.com/v21.0/{ig-user-id}/media

        [필수 파라미터]
        - image_url: 이미지 URL (공개 접근 가능해야 해요!)
        - access_token: 인증 토큰
        - is_carousel_item: True면 캐러셀용

        [반환값]
        - 성공: 컨테이너 ID (문자열)
        - 실패: None
        """

        # API 엔드포인트 URL
        url = f"{INSTAGRAM_GRAPH_API_BASE}/{ig_user_id}/media"

        # 요청 파라미터
        params = {
            "image_url": image_url,
            "access_token": access_token
        }

        # 캐러셀 아이템이면 표시
        if is_carousel_item:
            params["is_carousel_item"] = "true"

        try:
            # POST 요청 보내기
            async with session.post(url, data=params) as response:
                result = await response.json()

                # 성공하면 ID 반환 (🔴 str() 변환 필수 - API가 int 반환할 수 있음)
                if "id" in result:
                    return str(result["id"])
                else:
                    # ----------------------------------------
                    # ⚠️ 에러 처리
                    # ----------------------------------------
                    error = result.get("error", {})
                    error_msg = error.get("message", "Unknown error")
                    error_code = error.get("code", "")

                    # 토큰 만료 체크 (190, 102는 토큰 관련 에러 코드)
                    if error_code in [190, 102]:
                        self.log(f"❌ Instagram 토큰이 만료됐어요!", level="error")
                        self.log(f"   새 토큰을 발급받아주세요.", level="error")
                    else:
                        self.log(f"❌ 컨테이너 생성 실패: {error_msg}", level="error")

                    return None

        except Exception as e:
            self.log(f"❌ 컨테이너 요청 오류: {e}", level="error")
            return None

    # ============================================================
    # 📦 캐러셀 컨테이너 생성 함수
    #
    # 💡 이 함수가 하는 일:
    #    여러 개의 미디어 컨테이너를 하나의 캐러셀로 묶어요.
    #    캡션(설명글)도 여기서 추가해요!
    # ============================================================
    async def _create_instagram_carousel(
        self,
        session: aiohttp.ClientSession,
        ig_user_id: str,
        access_token: str,
        children_ids: List[str],
        caption: str
    ) -> Optional[str]:
        """
        📦 Instagram 캐러셀 컨테이너 생성

        [API 엔드포인트]
        POST https://graph.facebook.com/v21.0/{ig-user-id}/media

        [필수 파라미터]
        - media_type: "CAROUSEL" (캐러셀임을 표시)
        - children: 미디어 컨테이너 ID들 (쉼표로 구분)
        - caption: 게시물 설명글

        [반환값]
        - 성공: 캐러셀 컨테이너 ID
        - 실패: None
        """

        url = f"{INSTAGRAM_GRAPH_API_BASE}/{ig_user_id}/media"

        params = {
            "media_type": "CAROUSEL",
            "children": ",".join(children_ids),  # ID들을 쉼표로 연결
            "caption": caption,
            "access_token": access_token
        }

        try:
            async with session.post(url, data=params) as response:
                result = await response.json()

                if "id" in result:
                    return str(result["id"])  # 🔴 str() 변환 필수
                else:
                    error = result.get("error", {})
                    self.log(f"❌ 캐러셀 생성 실패: {error.get('message', 'Unknown')}", level="error")
                    return None

        except Exception as e:
            self.log(f"❌ 캐러셀 요청 오류: {e}", level="error")
            return None

    # ============================================================
    # 🚀 미디어 게시 함수
    #
    # 💡 이 함수가 하는 일:
    #    준비된 캐러셀을 실제로 Instagram에 게시해요!
    #    이 함수가 호출되면 진짜로 올라가요!
    # ============================================================
    async def _publish_instagram_media(
        self,
        session: aiohttp.ClientSession,
        ig_user_id: str,
        access_token: str,
        creation_id: str
    ) -> Dict:
        """
        🚀 Instagram 미디어 게시 (최종 단계!)

        [API 엔드포인트]
        POST https://graph.facebook.com/v21.0/{ig-user-id}/media_publish

        [필수 파라미터]
        - creation_id: 캐러셀 컨테이너 ID

        [반환값]
        - 성공: {"id": "게시물ID"}
        - 실패: {"error": {...}}
        """

        url = f"{INSTAGRAM_GRAPH_API_BASE}/{ig_user_id}/media_publish"

        params = {
            "creation_id": creation_id,
            "access_token": access_token
        }

        try:
            async with session.post(url, data=params) as response:
                result = await response.json()
                # 상세 로깅
                self.log(f"📋 media_publish 응답: {result}")
                return result

        except Exception as e:
            return {"error": {"message": str(e)}}

    # ============================================================
    # 📋 게시물 정보 조회 함수
    # ============================================================
    async def _get_instagram_post_info(
        self,
        session: aiohttp.ClientSession,
        post_id: str,
        access_token: str
    ) -> Dict:
        """
        📋 게시물 정보 조회 (permalink 등)

        게시 후에 게시물 URL을 알아내기 위해 호출해요.
        """

        url = f"{INSTAGRAM_GRAPH_API_BASE}/{post_id}"

        params = {
            "fields": "id,permalink,timestamp,media_type",
            "access_token": access_token
        }

        try:
            async with session.get(url, params=params) as response:
                return await response.json()
        except Exception:
            return {}

    # ============================================================
    # ✏️ 캡션 생성 함수
    #
    # 💡 캡션이란?
    #    Instagram 게시물에 달리는 설명글이에요.
    #    해시태그도 여기에 포함돼요!
    #
    # 💡 좋은 캡션의 조건:
    #    1. 한국어로 친근하게 작성
    #    2. 이모지로 시각적 효과
    #    3. 핵심 정보 간결하게 전달
    #    4. 해시태그 20~30개 (노출 극대화!)
    # ============================================================
    def _generate_caption(self, topic: str) -> str:
        """
        ✏️ Instagram 캡션 생성

        [입력]
        - topic: 주제 (예: "apple", "cherry")

        [출력]
        - 완성된 캡션 문자열 (해시태그 30개 포함)
        """

        # config에서 캡션 템플릿 확인
        instagram_config = self.config.get("instagram", {})
        caption_template = instagram_config.get("caption_template", "")

        if caption_template:
            # 템플릿이 있으면 {topic}을 실제 주제로 교체
            return caption_template.replace("{topic}", topic)

        # --------------------------------------------------------
        # 📌 주제별 한국어 번역 및 상세 정보
        #
        # 각 과일/음식에 대한 정보:
        # - korean: 한국어 이름
        # - emoji: 대표 이모지
        # - can_eat: 급여 가능 여부 (O/X/△)
        # - benefit: 주요 효능
        # - caution: 주의사항
        # --------------------------------------------------------
        topic_info = {
            "apple": {
                "korean": "사과",
                "emoji": "🍎",
                "can_eat": "O",
                "benefit": "비타민C 풍부, 치아 건강에 도움",
                "caution": "씨앗은 반드시 제거! (시안화물 포함)"
            },
            "cherry": {
                "korean": "체리",
                "emoji": "🍒",
                "can_eat": "△",
                "benefit": "항산화 성분, 관절 건강에 좋음",
                "caution": "씨앗, 줄기, 잎은 독성! 과육만 소량 급여"
            },
            "banana": {
                "korean": "바나나",
                "emoji": "🍌",
                "can_eat": "O",
                "benefit": "칼륨 풍부, 소화에 좋음",
                "caution": "껍질 제거 필수, 과당 많아 소량만"
            },
            "blueberry": {
                "korean": "블루베리",
                "emoji": "🫐",
                "can_eat": "O",
                "benefit": "항산화 성분 최고! 눈 건강에 좋음",
                "caution": "냉동 블루베리도 OK, 세척 필수"
            },
            "strawberry": {
                "korean": "딸기",
                "emoji": "🍓",
                "can_eat": "O",
                "benefit": "비타민C 풍부, 면역력 강화",
                "caution": "꼭지 제거, 너무 많이 주면 설사 주의"
            },
            "watermelon": {
                "korean": "수박",
                "emoji": "🍉",
                "can_eat": "O",
                "benefit": "수분 보충 최고! 여름철 간식으로 딱",
                "caution": "씨앗, 껍질 제거 필수"
            },
            "grape": {
                "korean": "포도",
                "emoji": "🍇",
                "can_eat": "X",
                "benefit": "-",
                "caution": "⚠️ 절대 금지! 강아지에게 독성"
            },
            "carrot": {
                "korean": "당근",
                "emoji": "🥕",
                "can_eat": "O",
                "benefit": "눈 건강, 치아 건강에 좋음",
                "caution": "생으로 또는 익혀서 모두 OK"
            },
            "sweet_potato": {
                "korean": "고구마",
                "emoji": "🍠",
                "can_eat": "O",
                "benefit": "식이섬유 풍부, 소화에 좋음",
                "caution": "반드시 익혀서, 껍질 제거 권장"
            },
            "pumpkin": {
                "korean": "단호박",
                "emoji": "🎃",
                "can_eat": "O",
                "benefit": "소화 촉진, 변비 예방에 효과적",
                "caution": "씨앗 제거, 익혀서 급여"
            }
        }

        # 기본값 (등록되지 않은 주제용)
        info = topic_info.get(topic, {
            "korean": topic,
            "emoji": "🐕",
            "can_eat": "?",
            "benefit": "정보 확인 중",
            "caution": "수의사와 상담 권장"
        })

        korean = info["korean"]
        emoji = info["emoji"]
        can_eat = info["can_eat"]
        benefit = info["benefit"]
        caution = info["caution"]

        # --------------------------------------------------------
        # 📌 급여 가능 여부에 따른 메시지
        # --------------------------------------------------------
        if can_eat == "O":
            verdict = f"✅ 급여 가능!"
            verdict_detail = f"강아지에게 {korean} 줘도 돼요! 🎉"
        elif can_eat == "X":
            verdict = f"❌ 급여 금지!"
            verdict_detail = f"강아지에게 {korean}은 위험해요! 🚫"
        else:  # △ (조건부)
            verdict = f"⚠️ 주의해서 급여"
            verdict_detail = f"강아지 {korean}, 조건부로 가능해요!"

        # --------------------------------------------------------
        # 📌 해시태그 생성 (30개)
        #
        # 카테고리별로 분류:
        # 1. 주제 관련 (5개)
        # 2. 강아지 일반 (10개)
        # 3. 반려동물/펫 (5개)
        # 4. 견종 관련 (5개)
        # 5. 브랜드/기타 (5개)
        # --------------------------------------------------------
        hashtags = [
            # 1. 주제 관련 (5개)
            f"#강아지{korean}",
            f"#{korean}",
            f"#강아지{korean}먹어도되나요",
            f"#{korean}급여",
            f"#반려견{korean}",

            # 2. 강아지 일반 (10개)
            "#강아지간식",
            "#강아지먹이",
            "#강아지영양",
            "#강아지건강",
            "#강아지식단",
            "#강아지음식",
            "#강아지급여",
            "#강아지과일",
            "#강아지야채",
            "#강아지간식추천",

            # 3. 반려동물/펫 (5개)
            "#반려견",
            "#반려견간식",
            "#반려견영양",
            "#반려동물",
            "#펫푸드",

            # 4. 견종 관련 (5개)
            "#골든리트리버",
            "#말티즈",
            "#푸들",
            "#포메라니안",
            "#댕댕이",

            # 5. 브랜드/기타 (5개)
            "#projectsunshine",
            "#강아지정보",
            "#펫스타그램",
            "#멍스타그램",
            "#일상"
        ]

        # --------------------------------------------------------
        # 📌 최종 캡션 조합
        # --------------------------------------------------------
        caption = f"""{emoji} 강아지에게 {korean}를 줘도 될까요?

{verdict}
{verdict_detail}

━━━━━━━━━━━━━━━━━━━━

📌 핵심 정보
• 급여 가능: {can_eat}
• 효능: {benefit}
• 주의: {caution}

━━━━━━━━━━━━━━━━━━━━

👆 스와이프해서 자세한 정보를 확인하세요!
💾 저장해두고 필요할 때 확인하세요!

📍 더 많은 강아지 정보 → 프로필 링크 🔗

{' '.join(hashtags)}"""

        return caption

    # ============================================================
    # 🔸 Instagram 시뮬레이션 (테스트용)
    #
    # 💡 왜 시뮬레이션이 필요한가요?
    #    실제 토큰 없이도 코드가 잘 작동하는지 테스트할 수 있어요.
    #    실제 게시는 안 되지만, 전체 흐름을 확인할 수 있어요!
    # ============================================================
    async def _simulate_instagram_publish(self, image_urls: List[str], topic: str) -> Dict:
        """🔸 Instagram 게시 시뮬레이션 (테스트용)

        ⚠️ 중요 (2026-02-04 수정):
        시뮬레이션 결과는 simulated=True 플래그가 필수입니다.
        publish_content.py에서 이 플래그를 확인하여 실패로 처리합니다.
        """

        self.log("=" * 50)
        self.log("⚠️ [SIM] 시뮬레이션 모드 - 실제 게시 안 됨!")
        self.log("⚠️ Instagram 토큰/계정ID가 설정되지 않았습니다.")
        self.log("=" * 50)
        self.log(f"🔸 [SIM] Instagram 캐러셀 시뮬레이션 ({len(image_urls[:10])}장)")

        # 각 이미지 컨테이너 생성 시뮬레이션
        for i, url in enumerate(image_urls[:10]):
            self.log(f"  🔸 [SIM] [{i+1}/10] 미디어 컨테이너 생성")
            await asyncio.sleep(0.1)  # 약간의 딜레이 (실제처럼 보이게)

        self.log("🔸 [SIM] 캐러셀 컨테이너 생성 완료")
        self.log("🔸 [SIM] Instagram 게시 시뮬레이션 완료")
        self.log("⚠️ [SIM] 이것은 테스트 모드입니다. 실제 Instagram에는 게시되지 않았습니다!")

        return {
            "success": True,  # 시뮬레이션 자체는 성공 (테스트 목적)
            "post_id": "SIM_17895695668004550",  # 가짜 ID (SIM_ 접두사로 식별)
            "permalink": f"https://www.instagram.com/p/SIM_{topic}/",  # 가짜 URL
            "container_count": len(image_urls[:10]),
            "caption": self._generate_caption(topic),
            "simulated": True  # ⚠️ 필수! publish_content.py에서 이 플래그 확인
        }

    # ============================================================
    # 🐦 Twitter 게시 (미구현)
    # ============================================================
    async def _publish_twitter(self, image_paths: List[str], topic: str) -> Dict:
        """🐦 Twitter/X 게시 (향후 구현 예정)"""
        return {"success": False, "error": "Twitter API 미구현"}

    # ============================================================
    # 🧵 Threads 게시 (미구현)
    # ============================================================
    async def _publish_threads(self, image_paths: List[str], topic: str) -> Dict:
        """🧵 Threads 게시 (향후 구현 예정)"""
        return {"success": False, "error": "Threads API 미구현"}
