#!/usr/bin/env python3
"""
Project Sunshine - CLI v5.0
콘텐츠 자동화 파이프라인 CLI (자동 협업 시스템)
Author: 최기술 대리 / 최과장

주요 명령어:
- python cli.py                  : 주제 탐색 모드 (1~2단계)
- python cli.py <topic>          : 다이렉트 모드 (3단계부터)
- python cli.py <topic> --v5     : v5 파이프라인 (자동 재작업)
- python cli.py schedule ...     : 스케줄 관리
- python cli.py trend ...        : 트렌드 분석
- python cli.py template ...     : 템플릿 관리
- python cli.py backup ...       : 백업 관리
- python cli.py retry ...        : 재시도 관리

v5 특징:
- 자동 재작업 루프 (검수 실패 시 최대 3회 재시도)
- G1/G2/G3 분리 검수 (김감독)
- PD 승인 요청 시스템
"""

import asyncio
import sys
import time
import json
from pathlib import Path
from datetime import datetime

# 프로젝트 루트 추가
sys.path.insert(0, str(Path(__file__).parent))

from core.agents import (
    PlannerAgent,
    PromptGeneratorAgent,
    ImageGeneratorAgent,
    TextOverlayAgent,
    QualityCheckerAgent,
    CaptionAgent,
    PublisherAgent,
    # New agents
    SchedulerAgent,
    MultiPlatformAgent,
    RetryAgent,
    TrendAgent,
    TemplateAgent,
)
from core.pipeline.display import PipelineDisplay
from core.pipeline.pipeline_v5 import SunshinePipelineV5


# ============================================================
# 게시 이력 관리 클래스
# - posted_history.json 파일을 읽고 쓰는 유틸리티
# - CLI 명령어와 파이프라인에서 공통으로 사용
# Author: 최기술 대리
# ============================================================
class PublishingHistory:
    """게시 이력 추적 시스템 (config/posted_history.json)"""

    def __init__(self):
        self.history_file = Path(__file__).parent / "config" / "posted_history.json"
        self.data = self._load()

    def _load(self) -> dict:
        """JSON 파일에서 이력 데이터 로드"""
        if self.history_file.exists():
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"posted": [], "last_updated": ""}

    def _save(self):
        """변경된 데이터를 JSON 파일에 저장"""
        self.data["last_updated"] = datetime.now().strftime("%Y-%m-%d")
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def is_published(self, topic: str) -> bool:
        """해당 주제가 이미 게시되었는지 확인"""
        return any(p["topic"] == topic for p in self.data["posted"])

    def get_posted_date(self, topic: str) -> str:
        """게시된 날짜 반환 (없으면 빈 문자열)"""
        for p in self.data["posted"]:
            if p["topic"] == topic:
                return p.get("date", "")
        return ""

    def add_published(self, topic: str, topic_kr: str = ""):
        """게시 완료 항목 추가"""
        for p in self.data["posted"]:
            if p["topic"] == topic:
                return  # 이미 존재

        entry = {
            "topic": topic,
            "topic_kr": topic_kr or topic,
            "date": datetime.now().strftime("%Y-%m-%d"),
        }
        self.data["posted"].append(entry)
        self._save()

    def show_history(self):
        """게시 이력 출력"""
        posted = self.data["posted"]

        if not posted:
            print("\n게시 이력이 없습니다.")
            return

        print(f"\n[게시 완료 목록] ({len(posted)}건)")
        for i, p in enumerate(posted, 1):
            date_str = p.get("date", "-")
            print(f"  {i}. {p.get('topic_kr', p['topic'])} ({p['topic']}) - {date_str}")
        print(f"  마지막 업데이트: {self.data['last_updated']}")


class SunshinePipeline:
    """Project Sunshine 메인 파이프라인 (시각화 버전)"""

    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = str(Path(__file__).parent / "config" / "config.yaml")

        self.config_path = config_path
        self.agents = self._initialize_agents()

    def _initialize_agents(self):
        """에이전트 초기화"""
        return {
            "planner": PlannerAgent(self.config_path),
            "prompt": PromptGeneratorAgent(self.config_path),
            "image": ImageGeneratorAgent(self.config_path),
            "overlay": TextOverlayAgent(self.config_path),
            "qa": QualityCheckerAgent(self.config_path),
            "caption": CaptionAgent(self.config_path),
            "publish": PublisherAgent(self.config_path),
        }

    async def run(self, topic: str, skip_publish: bool = False, force: bool = False) -> dict:
        """
        전체 파이프라인 실행 (시각화 포함)

        Args:
            topic: 콘텐츠 주제 (예: "cherry", "apple")
            skip_publish: True면 게시 단계 스킵
            force: True면 중복 게시 강제 진행

        Returns:
            최종 결과 dict
        """
        # 중복 게시 체크
        history = PublishingHistory()
        if history.is_published(topic):
            posted_date = history.get_posted_date(topic)
            if not force:
                print(f"\n❌ {topic}는 {posted_date}에 이미 게시됨.")
                print(f"   중복 게시하려면 --force 옵션 사용.")
                return {"success": False, "error": "중복 게시 차단", "step": "duplicate_check"}
            else:
                print(f"\n⚠️ 중복 게시 진행... ({topic}, 기존 게시일: {posted_date})")

        display = PipelineDisplay(topic)
        display.start()

        results = {}

        # Step 1: 기획
        display.start_step("planner")
        start = time.time()
        plan_result = await self.agents["planner"].run({"topic": topic})
        elapsed = time.time() - start

        if not plan_result.success:
            display.fail_step("planner", elapsed, plan_result.error or "Unknown error")
            return {"success": False, "error": "기획 실패", "step": "planner"}

        slides_count = len(plan_result.data.get("slides", []))
        display.complete_step("planner", elapsed, f"{slides_count} slides planned")
        results["plan"] = plan_result.data

        # Step 2: 프롬프트 생성
        display.start_step("prompt")
        start = time.time()
        prompt_result = await self.agents["prompt"].run(plan_result.data)
        elapsed = time.time() - start

        if not prompt_result.success:
            display.fail_step("prompt", elapsed, prompt_result.error or "Unknown error")
            return {"success": False, "error": "프롬프트 생성 실패", "step": "prompt"}

        prompt_count = len(prompt_result.data.get("prompts", []))
        display.complete_step("prompt", elapsed, f"{prompt_count} prompts generated")
        results["prompts"] = prompt_result.data

        # Step 3: 이미지 생성
        display.start_step("image")
        start = time.time()
        image_result = await self.agents["image"].run(prompt_result.data)
        elapsed = time.time() - start

        if not image_result.success:
            display.fail_step("image", elapsed, image_result.error or "Unknown error")
            return {"success": False, "error": "이미지 생성 실패", "step": "image"}

        image_count = len(image_result.data.get("images", []))
        display.complete_step("image", elapsed, f"{image_count} images ready")
        results["images"] = image_result.data

        # Step 4: 텍스트 오버레이
        display.start_step("overlay")
        start = time.time()
        # topic을 명시적으로 전달
        overlay_input = {**image_result.data, "topic": topic}
        overlay_result = await self.agents["overlay"].run(overlay_input)
        elapsed = time.time() - start

        if not overlay_result.success:
            display.fail_step("overlay", elapsed, overlay_result.error or "Unknown error")
            return {"success": False, "error": "오버레이 실패", "step": "overlay"}

        overlay_count = overlay_result.data.get("count", 0)
        display.complete_step("overlay", elapsed, f"{overlay_count} overlays applied")
        results["overlay"] = overlay_result.data

        # Step 5: 품질 검수
        display.start_step("qa")
        start = time.time()
        # overlay 결과에 images 배열 추가
        qa_input = {
            **overlay_result.data,
            "images": [{"path": p} for p in overlay_result.data.get("output_images", [])],
            "topic": topic
        }
        qa_result = await self.agents["qa"].run(qa_input)
        elapsed = time.time() - start

        qa_report = qa_result.data.get("report", {}) if qa_result.data else {}
        score = qa_report.get("total_score", qa_report.get("average_score", 0))
        grade = self._get_grade(score)

        if not qa_result.success:
            display.complete_step("qa", elapsed, f"Score: {score:.0f}/100 ({grade}) - FAILED", success=False)
            results["qa"] = qa_result.data
            result = {"success": False, "error": "품질 검수 실패", "step": "qa", "results": results}
            display.show_summary(result)
            return result

        display.complete_step("qa", elapsed, f"Score: {score:.0f}/100 ({grade})")
        results["qa"] = qa_result.data

        # Step 6: 캡션 생성
        display.start_step("caption")
        start = time.time()
        caption_input = {
            "topic": topic,
            "topic_kr": results["plan"].get("topic_kr", topic),
            "safety": results["plan"].get("safety", "safe"),
        }
        caption_result = await self.agents["caption"].run(caption_input)
        elapsed = time.time() - start

        if caption_result.success:
            ht_count = caption_result.data.get("caption", {}).get("hashtag_count", 0)
            display.complete_step("caption", elapsed, f"caption + {ht_count} hashtags")
            results["caption"] = caption_result.data
        else:
            display.complete_step("caption", elapsed, "caption failed (non-blocking)", success=False)
            results["caption"] = {}

        # Step 7: 게시
        if skip_publish:
            display.skip_step("publish")
            results["publish"] = {"skipped": True}
        else:
            display.start_step("publish")
            start = time.time()
            publish_result = await self.agents["publish"].run(qa_result.data)
            elapsed = time.time() - start

            if publish_result.success:
                uploaded = publish_result.data.get("publish_results", {}).get("instagram", {})
                display.complete_step("publish", elapsed, "uploaded to Instagram")

                # 게시 성공 시 이력에 자동 기록
                topic_kr = results.get("plan", {}).get("topic_kr", topic)
                history.add_published(topic=topic, topic_kr=topic_kr)
            else:
                display.complete_step("publish", elapsed, publish_result.error or "Failed", success=False)

            results["publish"] = publish_result.data

        final_result = {"success": True, "results": results}
        display.show_summary(final_result)
        return final_result

    def _get_grade(self, score: float) -> str:
        """점수를 등급으로 변환"""
        if score >= 90:
            return "A"
        if score >= 80:
            return "B+"
        if score >= 70:
            return "B"
        if score >= 60:
            return "C"
        return "D"


async def run_single_agent(agent_name: str, topic: str, config_path: str = None):
    """단일 에이전트 실행"""
    if config_path is None:
        config_path = str(Path(__file__).parent / "config" / "config.yaml")

    agents = {
        "planner": PlannerAgent,
        "prompt": PromptGeneratorAgent,
        "image": ImageGeneratorAgent,
        "overlay": TextOverlayAgent,
        "qa": QualityCheckerAgent,
        "caption": CaptionAgent,
        "publish": PublisherAgent,
    }

    if agent_name not in agents:
        print(f"❌ Unknown agent: {agent_name}")
        return

    agent = agents[agent_name](config_path)
    result = await agent.run({"topic": topic})

    print(f"\n{'='*50}")
    print(f"🔧 {agent_name.upper()} Agent Result")
    print(f"{'='*50}")
    print(f"Success: {result.success}")
    if result.data:
        print(f"Data: {result.data}")
    if result.error:
        print(f"Error: {result.error}")
    print(f"{'='*50}\n")


async def cmd_schedule(args):
    """스케줄 관리 명령"""
    agent = SchedulerAgent()

    if args.schedule_action == "create":
        topics = args.topics.split(",") if args.topics else []
        result = await agent.run({
            "action": "generate_schedule",
            "topics": topics,
            "posts_per_day": args.per_day
        })
        if result.success:
            print(f"\n[스케줄 생성 완료] {result.data['total_posts']}개 포스팅 예약")
            for item in result.data.get("schedule", [])[:7]:
                print(f"  {item['day_of_week']}: {item['topic']} @ {item['scheduled_time'][:16]}")
        else:
            print(f"실패: {result.error}")

    elif args.schedule_action == "status":
        result = await agent.run({"action": "get_status"})
        if result.success:
            data = result.data
            print(f"\n[큐 상태]")
            print(f"  대기: {data['queued']} | 완료: {data['completed']} | 실패: {data['failed']}")

    elif args.schedule_action == "add":
        result = await agent.run({
            "action": "add_to_queue",
            "topic": args.topic_name,
            "category": args.category or "general",
            "priority": args.priority or 5
        })
        if result.success:
            print(f"큐 추가: {result.data['topic']} @ {result.data['scheduled_time'][:16]}")


async def cmd_trend(args):
    """트렌드 분석 명령"""
    agent = TrendAgent()

    if args.trend_action == "seasonal":
        result = await agent.run({"action": "seasonal"})
        if result.success:
            data = result.data
            print(f"\n[{data['season'].upper()} 추천]")
            print(f"  테마: {data['theme']}")
            print(f"  추천 음식: {', '.join(data['recommended_foods'])}")
            print(f"  키워드: {', '.join(data.get('keywords', []))}")

    elif args.trend_action == "events":
        result = await agent.run({"action": "events", "days_ahead": args.days or 14})
        if result.success:
            events = result.data.get("events", [])
            if events:
                print(f"\n[다가오는 이벤트] ({len(events)}개)")
                for event in events:
                    print(f"  {event['date']} ({event['days_until']}일 후) - {event['name']}: {event['theme']}")
            else:
                print("다가오는 이벤트가 없습니다.")

    elif args.trend_action == "recommend":
        # 사용 가능한 주제 목록
        config_dir = Path(__file__).parent / "config"
        topics = [f.stem.replace("_text", "") for f in config_dir.glob("*_text.json")]

        result = await agent.run({
            "action": "recommend",
            "topics": topics,
            "count": args.count or 5
        })
        if result.success:
            print(f"\n[콘텐츠 추천]")
            for i, rec in enumerate(result.data["recommendations"], 1):
                print(f"  {i}. {rec['topic']} (점수: {rec['score']}) - {rec['recommendation']}")

    elif args.trend_action == "plan":
        config_dir = Path(__file__).parent / "config"
        topics = [f.stem.replace("_text", "") for f in config_dir.glob("*_text.json")]

        result = await agent.run({
            "action": "plan",
            "topics": topics,
            "posts_per_week": 7
        })
        if result.success:
            print(f"\n[주간 계획]")
            for day in result.data["weekly_plan"]:
                topic = day["topic"] or "미정"
                reason = day.get("reason", "")
                print(f"  Day {day['day']} ({day['date']}): {topic} - {reason}")

    elif args.trend_action == "hashtags":
        category = args.category or "general"
        result = await agent.run({
            "action": "hashtags",
            "category": category,
            "limit": 10
        })
        if result.success:
            print(f"\n[트렌딩 해시태그 - {category}]")
            for tag in result.data["hashtags"]:
                print(f"  #{tag}")


async def cmd_template(args):
    """템플릿 관리 명령"""
    agent = TemplateAgent()

    if args.template_action == "list":
        result = await agent.run({"action": "list"})
        if result.success:
            data = result.data
            print(f"\n[템플릿 목록]")
            print(f"  카테고리: {', '.join(data['category_variations'])}")
            print(f"  A/B 변형: {', '.join(data['ab_variations'])}")
            print(f"  커스텀: {len(data['custom_templates'])}개")

    elif args.template_action == "validate":
        topic = args.topic_name
        text_file = Path(__file__).parent / "config" / f"{topic}_text.json"

        if not text_file.exists():
            print(f"파일 없음: {text_file}")
            return

        with open(text_file, 'r', encoding='utf-8') as f:
            text_data = json.load(f)

        result = await agent.run({"action": "validate", "text_data": text_data})
        if result.success:
            print(f"\n[검증 결과: {topic}] PASS")
        else:
            print(f"\n[검증 결과: {topic}] FAIL")
            for issue in result.data.get("issues", []):
                print(f"  - {issue}")
        for warning in result.data.get("warnings", []):
            print(f"  (경고) {warning}")

    elif args.template_action == "generate":
        result = await agent.run({
            "action": "generate",
            "topic": args.topic_name,
            "topic_kr": args.topic_kr or args.topic_name,
            "category": args.category or "fruit",
            "is_safe": not args.dangerous
        })
        if result.success:
            print(f"\n[템플릿 생성: {args.topic_name}]")
            for slide in result.data["template"]:
                print(f"  Slide {slide['slide']}: [{slide['type']}] {slide['title_hint']}")


async def cmd_backup(args):
    """백업 관리 명령"""
    from scripts.auto_backup import AutoBackup
    backup = AutoBackup()

    if args.backup_action == "create":
        result = backup.create_backup(description=args.description or "CLI 백업")
        if result["success"]:
            info = result["backup_info"]
            size_mb = info["compressed_size"] / 1024 / 1024
            print(f"\n[백업 생성 완료]")
            print(f"  파일: {info['name']}")
            print(f"  크기: {size_mb:.2f} MB")
            print(f"  파일 수: {result['files_backed_up']}")
        else:
            print(f"백업 실패: {result['error']}")

    elif args.backup_action == "list":
        backups = backup.list_backups()
        if backups:
            print(f"\n[백업 목록] ({len(backups)}개)")
            for b in backups:
                status = "O" if b["exists"] else "X"
                print(f"  [{status}] {b['name']} ({b['size_mb']} MB) - {b['created_at'][:16]}")
        else:
            print("백업이 없습니다.")

    elif args.backup_action == "stats":
        stats = backup.get_statistics()
        print(f"\n[백업 통계]")
        print(f"  총 백업 수: {stats['total_backups']}")
        print(f"  총 용량: {stats['total_size_mb']} MB")
        print(f"  최근 백업: {stats.get('newest_backup', 'N/A')}")


async def cmd_retry(args):
    """재시도 관리 명령"""
    agent = RetryAgent()

    if args.retry_action == "stats":
        result = await agent.run({"action": "stats"})
        if result.success:
            data = result.data
            print(f"\n[재시도 통계]")
            print(f"  총 실패: {data['total_failures']}")
            print(f"  대기 중: {data['pending']}")
            print(f"  복구됨: {data['recovered']}")
            print(f"  복구율: {data['recovery_rate']}%")

    elif args.retry_action == "list":
        result = await agent.run({"action": "list", "status": args.status})
        if result.success:
            tasks = result.data.get("tasks", [])
            print(f"\n[실패 작업 목록] ({len(tasks)}개)")
            for task in tasks[:10]:
                print(f"  [{task['status']}] {task['task_id']} - {task['failure_type']} ({task['retry_count']}회)")

    elif args.retry_action == "process":
        result = await agent.run({"action": "process_all"})
        if result.success:
            data = result.data
            print(f"\n[재시도 처리 결과]")
            print(f"  처리: {data['processed']} | 복구: {data['recovered']} | 실패: {data['failed']}")

    elif args.retry_action == "clear":
        result = await agent.run({"action": "clear"})
        if result.success:
            print(f"정리 완료: {result.data['removed_count']}개 제거")


SUBCOMMANDS = {"schedule", "trend", "template", "backup", "retry", "explore"}


# ============================================================
# 주제 탐색 모드 (v5)
# ============================================================

async def run_topic_exploration():
    """
    주제 탐색 모드 (1~2단계)
    - 기제작 목록 확인
    - 추천 5개안 생성
    - 최검증 주제 검증
    """
    print("\n" + "=" * 60)
    print("✍️ 김작가: 주제 탐색 모드 시작")
    print("=" * 60)

    # 1. 기제작 목록 확인
    images_dir = Path(__file__).parent / "images"
    existing = []

    if images_dir.exists():
        for folder in images_dir.iterdir():
            if folder.is_dir() and not folder.name.startswith('.'):
                # 폴더명에서 주제 추출 (예: 008_banana -> banana)
                name = folder.name
                if '_' in name:
                    name = name.split('_', 1)[1]
                existing.append(name.lower())

    print(f"\n📁 기제작 콘텐츠: {len(existing)}개")
    print(f"   {', '.join(existing[:10])}{'...' if len(existing) > 10 else ''}")

    # 2. 추천 5개안 생성 (topics_expanded.json에서)
    topics_file = Path(__file__).parent / "config" / "topics_expanded.json"
    recommendations = []

    if topics_file.exists():
        with open(topics_file, 'r', encoding='utf-8') as f:
            all_topics = json.load(f)

        # 기제작 제외하고 추천
        available = [t for t in all_topics if t.get("topic_en", "").lower() not in existing]

        # 안전한 음식 우선, 점수 기반 정렬
        safe_topics = [t for t in available if t.get("can_eat") in ["O", "△"]]
        safe_topics.sort(key=lambda x: x.get("interest_score", 50), reverse=True)

        recommendations = safe_topics[:5]

    if not recommendations:
        # 기본 추천 목록
        recommendations = [
            {"topic_en": "sweet_potato", "topic_kr": "고구마", "can_eat": "O", "interest_score": 95},
            {"topic_en": "salmon", "topic_kr": "연어", "can_eat": "O", "interest_score": 88},
            {"topic_en": "chicken", "topic_kr": "닭고기", "can_eat": "O", "interest_score": 85},
            {"topic_en": "blueberry", "topic_kr": "블루베리", "can_eat": "O", "interest_score": 82},
            {"topic_en": "egg", "topic_kr": "계란", "can_eat": "O", "interest_score": 80},
        ]

    print(f"\n📋 추천 5개안:")
    for i, rec in enumerate(recommendations, 1):
        topic_en = rec.get("topic_en", rec.get("topic", "unknown"))
        topic_kr = rec.get("topic_kr", topic_en)
        score = rec.get("interest_score", 50)
        can_eat = rec.get("can_eat", "?")
        print(f"   {i}. {topic_kr} ({topic_en}) - {score}점, 급여: {can_eat}")

    # 3. 사용자 선택
    print("\n" + "-" * 60)
    try:
        choice = input("선택할 번호를 입력하세요 (1-5, 또는 직접 입력): ").strip()

        if choice.isdigit() and 1 <= int(choice) <= len(recommendations):
            selected = recommendations[int(choice) - 1]
            topic = selected.get("topic_en", selected.get("topic"))
        else:
            topic = choice.lower().replace(" ", "_")

        print(f"\n✅ 선정된 주제: {topic}")
        return topic

    except EOFError:
        # 비대화형 모드
        topic = recommendations[0].get("topic_en", recommendations[0].get("topic"))
        print(f"\n✅ 자동 선정: {topic}")
        return topic


async def run_pipeline_cmd(args):
    """파이프라인 명령 실행"""
    import argparse
    parser = argparse.ArgumentParser(description="Pipeline")
    parser.add_argument("topic", nargs="?", default=None, help="콘텐츠 주제 (없으면 탐색 모드)")
    parser.add_argument("--dry-run", action="store_true", help="게시 스킵")
    parser.add_argument("--force", action="store_true", help="중복 게시 강제 진행")
    parser.add_argument("--v5", action="store_true", help="v5 파이프라인 (자동 재작업)")
    parser.add_argument("--skip-approval", action="store_true", help="PD 승인 스킵")
    parser.add_argument("--crewai", "--crew", action="store_true", help="CrewAI 에이전트 대화 모드 활성화")
    parser.add_argument("--step", choices=["planner", "prompt", "image", "overlay", "qa", "caption", "publish"])
    parser.add_argument("--config", help="설정 파일 경로")

    parsed = parser.parse_args(args)

    # 주제가 없으면 탐색 모드
    if parsed.topic is None:
        parsed.topic = await run_topic_exploration()
        parsed.v5 = True  # 탐색 모드는 자동으로 v5

    if parsed.step:
        await run_single_agent(parsed.step, parsed.topic, parsed.config)
    elif parsed.v5 or parsed.crewai:
        # v5 파이프라인 (자동 재작업)
        # --crewai 사용 시 자동으로 v5도 활성화
        pipeline = SunshinePipelineV5(config_path=parsed.config, use_crew=parsed.crewai)
        await pipeline.run(
            parsed.topic,
            skip_publish=parsed.dry_run,
            skip_approval=parsed.skip_approval,
            force=parsed.force,
            use_crew=parsed.crewai
        )
    else:
        # 기존 v3 파이프라인
        pipeline = SunshinePipeline(config_path=parsed.config)
        await pipeline.run(parsed.topic, skip_publish=parsed.dry_run, force=parsed.force)


async def run_subcommand(cmd, args):
    """서브커맨드 실행"""
    import argparse

    if cmd == "schedule":
        parser = argparse.ArgumentParser(description="스케줄 관리")
        parser.add_argument("schedule_action", choices=["create", "status", "add"])
        parser.add_argument("--topics", help="주제 목록 (콤마 구분)")
        parser.add_argument("--per-day", type=int, default=1, help="하루 포스팅 수")
        parser.add_argument("--topic-name", help="주제명 (add용)")
        parser.add_argument("--category", help="카테고리")
        parser.add_argument("--priority", type=int, help="우선순위 (1-10)")
        await cmd_schedule(parser.parse_args(args))

    elif cmd == "trend":
        parser = argparse.ArgumentParser(description="트렌드 분석")
        parser.add_argument("trend_action", choices=["seasonal", "events", "recommend", "plan", "hashtags"])
        parser.add_argument("--days", type=int, help="조회 기간 (일)")
        parser.add_argument("--count", type=int, help="추천 개수")
        parser.add_argument("--category", help="카테고리")
        await cmd_trend(parser.parse_args(args))

    elif cmd == "template":
        parser = argparse.ArgumentParser(description="템플릿 관리")
        parser.add_argument("template_action", choices=["list", "validate", "generate"])
        parser.add_argument("--topic-name", help="주제명")
        parser.add_argument("--topic-kr", help="한글 주제명")
        parser.add_argument("--category", help="카테고리")
        parser.add_argument("--dangerous", action="store_true", help="위험 음식")
        await cmd_template(parser.parse_args(args))

    elif cmd == "backup":
        parser = argparse.ArgumentParser(description="백업 관리")
        parser.add_argument("backup_action", choices=["create", "list", "stats"])
        parser.add_argument("--description", help="백업 설명")
        await cmd_backup(parser.parse_args(args))

    elif cmd == "retry":
        parser = argparse.ArgumentParser(description="재시도 관리")
        parser.add_argument("retry_action", choices=["stats", "list", "process", "clear"])
        parser.add_argument("--status", help="상태 필터")
        await cmd_retry(parser.parse_args(args))


async def main():
    """CLI 메인 함수"""
    args = sys.argv[1:]

    if args and args[0] in ("-h", "--help"):
        print("""Project Sunshine v5.0 - 자동 협업 시스템

🆕 v5 특징:
  - 주제 탐색 모드 (인자 없이 실행)
  - 자동 재작업 루프 (검수 실패 시 최대 3회 재시도)
  - G1/G2/G3 분리 검수 (김감독)
  - PD 승인 요청 시스템

🤖 멀티 페르소나 모드 (--crewai):
  - 에이전트 간 대화 로그 생성
  - 김감독 ↔ 이작가, 박편집 등 협의 과정 출력
  - 규칙 기반 (API 호출 없음, 추가 비용 0원)

사용법:
  python cli.py                                     주제 탐색 모드 (1~2단계)
  python cli.py <topic>                             다이렉트 모드 (v3)
  python cli.py <topic> --v5                        v5 파이프라인 (자동 재작업)
  python cli.py <topic> --v5 --dry-run              v5 + 게시 스킵
  python cli.py <topic> --v5 --skip-approval        v5 + PD승인 스킵
  python cli.py <topic> --crewai                    CrewAI 에이전트 대화 모드
  python cli.py <topic> --crewai --dry-run          CrewAI + 게시 스킵
  python cli.py schedule <action>                   스케줄 관리
  python cli.py trend <action>                      트렌드 분석
  python cli.py template <action>                   템플릿 관리
  python cli.py backup <action>                     백업 관리
  python cli.py retry <action>                      재시도 관리
  python cli.py --history                           게시 이력 보기

예시:
  python cli.py                       # 주제 탐색 → 5개 추천 → 선택 → 실행
  python cli.py cherry --v5           # 체리 v5 파이프라인 (자동 재작업)
  python cli.py cherry --v5 --dry-run # 체리 v5 (게시 스킵)
  python cli.py cherry --crewai       # 체리 + CrewAI 대화 모드
  python cli.py peach --crewai --dry-run  # 복숭아 CrewAI (게시 스킵)
  python cli.py cherry                # 체리 v3 파이프라인 (기존 방식)
  python cli.py trend seasonal        # 계절 추천
  python cli.py trend recommend       # 콘텐츠 추천
  python cli.py schedule create       # 스케줄 생성
  python cli.py backup create         # 즉시 백업
  python cli.py --history             # 게시 이력
""")
        return

    # --history: 게시 이력 보기
    if "--history" in args:
        history = PublishingHistory()
        history.show_history()
        return

    # --add-history: 게시 이력 수동 추가
    if "--add-history" in args:
        idx = args.index("--add-history")
        remaining = args[idx + 1:]
        if not remaining:
            print("사용법: python cli.py --add-history <topic> [url]")
            return
        topic = remaining[0]
        history = PublishingHistory()
        history.add_published(topic=topic)
        print(f"게시 이력 추가 완료: {topic}")
        return

    # 인자 없으면 주제 탐색 모드
    if not args:
        await run_pipeline_cmd([])
        return

    # 첫 번째 인자가 서브커맨드인지 확인
    if args[0] in SUBCOMMANDS:
        await run_subcommand(args[0], args[1:])
    else:
        await run_pipeline_cmd(args)


if __name__ == "__main__":
    asyncio.run(main())
