"""
# ============================================================
# 🔬 FactCheckerAgent - 팩트체커 (최검증)
# ============================================================
#
# 📋 이 파일의 역할:
#    강아지 음식 정보의 정확성을 검증해요!
#    - 급여 가능 여부 확인
#    - 독성 정보 검증
#    - 급여량 적정성 확인
#    - 위험 정보 차단
#
# 🎯 왜 팩트체커가 중요한가요?
#    잘못된 정보는 강아지 건강에 치명적일 수 있어요!
#    예: 포도를 "급여 가능"으로 표시하면 → 급성 신부전 위험
#
# ⚠️ 면책 조항:
#    이 정보는 일반적인 가이드라인입니다.
#    개별 강아지의 상태에 따라 다를 수 있으므로
#    새 음식은 수의사와 상담 후 급여하세요.
#
# Author: 최검증 (Choi Geom-jeung)
# ============================================================
"""

from typing import Any, Dict, List, Optional
from .base import BaseAgent, AgentResult


class FactCheckerAgent(BaseAgent):
    """
    ╔════════════════════════════════════════════════════════╗
    ║  🔬 수의학 정보 검증 에이전트 (최검증)                     ║
    ╠════════════════════════════════════════════════════════╣
    ║  이 에이전트가 하는 일:                                   ║
    ║  1. 급여 가능 여부 검증                                   ║
    ║  2. 독성 정보 확인                                       ║
    ║  3. 급여량 적정성 검토                                    ║
    ║  4. 위험 콘텐츠 차단                                     ║
    ╚════════════════════════════════════════════════════════╝
    """

    @property
    def name(self) -> str:
        return "FactChecker"

    # ========================================================
    # 📚 수의학 검증 데이터베이스
    # ========================================================
    FOOD_DATABASE = {
        # ==================== 과일류 ====================
        "apple": {
            "korean": "사과",
            "can_eat": "O",
            "toxic_parts": ["씨앗 (시안화물)", "씨방/코어"],
            "safe_parts": ["과육"],
            "benefits": [
                "비타민C - 면역력 강화",
                "식이섬유 - 소화 촉진",
                "수분 함량 높음"
            ],
            "cautions": [
                "씨앗은 반드시 제거 (시안화물 함유)",
                "씨방(코어) 부분도 제거 권장",
                "과당이 있으므로 과다 급여 금지"
            ],
            "amount": {
                "small": "10-20g (5kg 이하)",
                "medium": "20-40g (5-15kg)",
                "large": "40-80g (15kg 이상)"
            },
            "frequency": "주 2-3회",
            "severity": "SAFE",
            "sources": ["ASPCA", "AKC"]
        },
        "grape": {
            "korean": "포도",
            "can_eat": "X",
            "toxic_parts": ["전체 (과육, 껍질, 씨앗 모두)"],
            "safe_parts": [],
            "benefits": [],
            "cautions": [
                "⚠️ 절대 금지! 소량도 위험",
                "급성 신부전 유발 가능",
                "건포도도 동일하게 위험"
            ],
            "amount": {"all": "급여 금지"},
            "frequency": "절대 금지",
            "severity": "CRITICAL",
            "emergency": {
                "symptoms": ["구토", "설사", "무기력", "소변량 감소"],
                "action": "즉시 동물병원 방문"
            },
            "sources": ["ASPCA Animal Poison Control", "VCA Hospitals"]
        },
        "cherry": {
            "korean": "체리",
            "can_eat": "△",
            "toxic_parts": ["씨앗 (시안화물)", "줄기", "잎"],
            "safe_parts": ["과육만"],
            "benefits": [
                "항산화 성분",
                "관절 건강에 도움"
            ],
            "cautions": [
                "씨앗/줄기/잎은 시안화물 함유!",
                "과육만 소량 급여 가능",
                "씨앗 제거 철저히"
            ],
            "amount": {"all": "1-2알 (씨 완전 제거)"},
            "frequency": "가끔 (주 1회 이하)",
            "severity": "CAUTION",
            "sources": ["ASPCA", "PetMD"]
        },
        "banana": {
            "korean": "바나나",
            "can_eat": "O",
            "toxic_parts": [],
            "safe_parts": ["과육"],
            "benefits": [
                "칼륨 풍부 - 근육/심장 건강",
                "비타민B6 - 에너지 대사",
                "식이섬유 - 소화 촉진"
            ],
            "cautions": [
                "껍질 제거 필수",
                "과당 많아 소량만 급여",
                "과다 섭취 시 변비 가능"
            ],
            "amount": {
                "small": "1-2조각 (5kg 이하)",
                "medium": "3-4조각 (5-15kg)",
                "large": "반 개 이하 (15kg 이상)"
            },
            "frequency": "주 2-3회",
            "severity": "SAFE",
            "sources": ["AKC", "PetMD"]
        },
        "blueberry": {
            "korean": "블루베리",
            "can_eat": "O",
            "toxic_parts": [],
            "safe_parts": ["전체"],
            "benefits": [
                "항산화 성분 최고 - 노화 방지",
                "안토시아닌 - 눈 건강",
                "비타민C/K - 면역력"
            ],
            "cautions": [
                "세척 필수 (농약 제거)",
                "냉동 블루베리도 OK",
                "처음엔 소량으로 시작"
            ],
            "amount": {"all": "체중 5kg당 5-6알"},
            "frequency": "매일 가능",
            "severity": "SAFE",
            "sources": ["AKC", "ASPCA"]
        },
        "strawberry": {
            "korean": "딸기",
            "can_eat": "O",
            "toxic_parts": [],
            "safe_parts": ["과육", "씨앗(작아서 무해)"],
            "benefits": [
                "비타민C 풍부",
                "항산화 성분",
                "치아 미백 효과"
            ],
            "cautions": [
                "꼭지/잎 제거",
                "세척 필수",
                "과다 섭취 시 설사 가능"
            ],
            "amount": {"all": "체중 5kg당 1개"},
            "frequency": "주 2-3회",
            "severity": "SAFE",
            "sources": ["AKC", "PetMD"]
        },
        "watermelon": {
            "korean": "수박",
            "can_eat": "O",
            "toxic_parts": ["씨앗 (장폐색 위험)", "껍질"],
            "safe_parts": ["과육"],
            "benefits": [
                "수분 92% - 탈수 예방",
                "비타민A/C",
                "여름철 최고 간식"
            ],
            "cautions": [
                "씨앗 반드시 제거 (장폐색)",
                "껍질 제거 (소화 어려움)",
                "과당 있어 적당량만"
            ],
            "amount": {"all": "체중 5kg당 50g"},
            "frequency": "여름철 매일 가능",
            "severity": "SAFE",
            "sources": ["AKC", "ASPCA"]
        },

        # ==================== 채소류 ====================
        "carrot": {
            "korean": "당근",
            "can_eat": "O",
            "toxic_parts": [],
            "safe_parts": ["전체"],
            "benefits": [
                "베타카로틴 - 눈 건강",
                "저칼로리 - 다이어트 간식",
                "치아 건강 - 플라그 제거"
            ],
            "cautions": [
                "생/익힌 것 모두 OK",
                "큰 조각은 질식 주의",
                "처음엔 소량으로"
            ],
            "amount": {"all": "체중 5kg당 30g"},
            "frequency": "매일 가능",
            "severity": "SAFE",
            "sources": ["AKC", "PetMD"]
        },
        "sweet_potato": {
            "korean": "고구마",
            "can_eat": "O",
            "toxic_parts": ["생 고구마 (소화 어려움)"],
            "safe_parts": ["익힌 고구마"],
            "benefits": [
                "식이섬유 풍부",
                "비타민A/C",
                "소화에 좋음"
            ],
            "cautions": [
                "반드시 익혀서 급여",
                "껍질 제거 권장",
                "과다 섭취 시 가스"
            ],
            "amount": {"all": "체중 5kg당 30g"},
            "frequency": "주 2-3회",
            "severity": "SAFE",
            "sources": ["AKC", "ASPCA"]
        },

        # ==================== 절대 금지 ====================
        "onion": {
            "korean": "양파",
            "can_eat": "X",
            "toxic_parts": ["전체"],
            "safe_parts": [],
            "benefits": [],
            "cautions": ["절대 금지! 용혈성 빈혈 유발"],
            "amount": {"all": "급여 금지"},
            "severity": "CRITICAL",
            "sources": ["ASPCA Animal Poison Control"]
        },
        "garlic": {
            "korean": "마늘",
            "can_eat": "X",
            "toxic_parts": ["전체"],
            "safe_parts": [],
            "benefits": [],
            "cautions": ["절대 금지! 양파보다 5배 독성"],
            "amount": {"all": "급여 금지"},
            "severity": "CRITICAL",
            "sources": ["ASPCA Animal Poison Control"]
        },
        "chocolate": {
            "korean": "초콜릿",
            "can_eat": "X",
            "toxic_parts": ["전체"],
            "safe_parts": [],
            "benefits": [],
            "cautions": ["절대 금지! 테오브로민 독성"],
            "amount": {"all": "급여 금지"},
            "severity": "CRITICAL",
            "sources": ["ASPCA Animal Poison Control"]
        },
        "xylitol": {
            "korean": "자일리톨",
            "can_eat": "X",
            "toxic_parts": ["전체"],
            "safe_parts": [],
            "benefits": [],
            "cautions": ["절대 금지! 저혈당/간부전", "껌, 사탕 주의"],
            "amount": {"all": "급여 금지"},
            "severity": "CRITICAL",
            "sources": ["ASPCA Animal Poison Control", "FDA"]
        }
    }

    # 면책 문구
    DISCLAIMER = """
📋 면책 조항
이 정보는 일반적인 가이드라인입니다.
개별 강아지의 건강 상태, 알레르기, 나이에 따라
반응이 다를 수 있습니다.

새로운 음식을 급여하기 전 반드시 수의사와
상담하시기 바랍니다.
"""

    async def execute(self, input_data: Any) -> AgentResult:
        """
        🔬 팩트체크 실행

        [입력]
        input_data = {
            "topic": "apple",
            "content": {
                "can_eat": true,
                "benefits": [...],
                ...
            }
        }

        [출력]
        - verified: True/False
        - corrections: 수정 필요 항목
        - verified_info: 검증된 정보
        """
        # 입력 데이터 추출
        if isinstance(input_data, str):
            topic = input_data
            content = None
        else:
            topic = input_data.get("topic", "unknown")
            content = input_data.get("content")

        self.log(f"🔬 '{topic}' 팩트체크 시작")

        # 데이터베이스에서 검증 정보 조회
        if topic not in self.FOOD_DATABASE:
            self.log(f"⚠️ '{topic}' 데이터베이스에 없음", level="warning")
            return AgentResult(
                success=True,
                data={
                    "topic": topic,
                    "verified": False,
                    "error": f"'{topic}'에 대한 검증 데이터 없음",
                    "recommendation": "수의사와 상담 권장"
                }
            )

        db_info = self.FOOD_DATABASE[topic]

        # 검증 결과 생성
        result = self._verify_content(topic, content, db_info)

        # 심각도에 따른 로그
        if db_info["severity"] == "CRITICAL":
            self.log(f"🚨 위험! '{topic}'은 급여 금지 식품입니다!", level="error")
        elif db_info["severity"] == "CAUTION":
            self.log(f"⚠️ 주의! '{topic}'은 조건부 급여 가능", level="warning")
        else:
            self.log(f"✅ '{topic}' 검증 완료 - 급여 가능")

        return AgentResult(
            success=True,
            data=result,
            metadata={
                "agent": "choigeomjeung",
                "sources": db_info.get("sources", [])
            }
        )

    def _verify_content(self, topic: str, content: Optional[Dict], db_info: Dict) -> Dict:
        """콘텐츠 검증 및 결과 생성"""
        corrections = []
        is_correct = True

        # 콘텐츠가 있으면 검증
        if content:
            # can_eat 검증
            if "can_eat" in content:
                db_can_eat = db_info["can_eat"]
                content_can_eat = "O" if content["can_eat"] else "X"

                if db_can_eat == "X" and content_can_eat == "O":
                    # 위험! 독성 식품을 급여 가능으로 표시
                    corrections.append({
                        "field": "can_eat",
                        "original": content_can_eat,
                        "corrected": db_can_eat,
                        "severity": "CRITICAL",
                        "reason": f"{db_info['korean']}은 강아지에게 독성이 있습니다!"
                    })
                    is_correct = False

        return {
            "topic": topic,
            "verified": is_correct,
            "verification_result": {
                "can_eat": db_info["can_eat"],
                "is_correct": is_correct,
                "severity": db_info["severity"]
            },
            "verified_info": {
                "korean": db_info["korean"],
                "can_eat": db_info["can_eat"],
                "toxic_parts": db_info["toxic_parts"],
                "safe_parts": db_info["safe_parts"],
                "benefits": db_info["benefits"],
                "cautions": db_info["cautions"],
                "amount": db_info["amount"],
                "frequency": db_info.get("frequency", "확인 필요")
            },
            "corrections": corrections,
            "disclaimer": self.DISCLAIMER,
            "emergency": db_info.get("emergency"),
            "sources": db_info.get("sources", [])
        }

    def check_food_safety(self, topic: str) -> Dict:
        """
        🔧 간편 안전성 체크 (동기 버전)

        빠른 확인용:
        result = checker.check_food_safety("grape")
        if result["can_eat"] == "X":
            block_content()
        """
        if topic not in self.FOOD_DATABASE:
            return {
                "topic": topic,
                "can_eat": "?",
                "severity": "UNKNOWN",
                "message": "데이터베이스에 없는 식품입니다. 수의사와 상담하세요."
            }

        info = self.FOOD_DATABASE[topic]
        return {
            "topic": topic,
            "korean": info["korean"],
            "can_eat": info["can_eat"],
            "severity": info["severity"],
            "cautions": info["cautions"],
            "message": self._get_safety_message(info)
        }

    def _get_safety_message(self, info: Dict) -> str:
        """안전성 메시지 생성"""
        can_eat = info["can_eat"]
        korean = info["korean"]

        if can_eat == "O":
            return f"✅ {korean}은 강아지에게 안전합니다. 적정량을 지켜 급여하세요."
        elif can_eat == "X":
            return f"🚨 {korean}은 강아지에게 독성이 있습니다! 절대 급여하지 마세요!"
        else:
            return f"⚠️ {korean}은 조건부로 급여 가능합니다. 주의사항을 꼭 확인하세요."

    def get_emergency_info(self, topic: str) -> Optional[Dict]:
        """응급 정보 조회"""
        if topic in self.FOOD_DATABASE:
            return self.FOOD_DATABASE[topic].get("emergency")
        return None
