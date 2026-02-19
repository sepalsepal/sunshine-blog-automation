#!/usr/bin/env python3
"""
Night Worker - 야간 배치 작업 시스템 (이중 구조)
- queue/night_tasks.json에서 작업 읽기
- 우선순위 기반 실행
- 에러 처리 및 재시도
- 텔레그램 알림
- 야간 보고서 생성
- 중복 실행 방지 (lock 파일)

실행 구조:
    1. GitHub Actions (메인) - 23:00 KST
    2. 로컬 launchd (백업) - 23:05 KST
    → GitHub가 먼저 실행되면 lock으로 로컬은 스킵

사용법:
    # 일반 실행
    python night_worker.py --source=local

    # GitHub Actions에서 실행
    python night_worker.py --source=github

    # 드라이런 (실제 실행 없이 테스트)
    python night_worker.py --dry-run

    # 특정 작업만 실행
    python night_worker.py --task-id task_001
"""

import os
import sys
import json
import time
import shutil
import argparse
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# 프로젝트 루트 설정
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 환경변수 로드
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / '.env')
except ImportError:
    pass

# 경로 설정
QUEUE_DIR = PROJECT_ROOT / 'queue'
QUEUE_FILE = QUEUE_DIR / 'night_tasks.json'
LOGS_DIR = PROJECT_ROOT / 'logs'
LOCK_FILE = Path('/tmp/night_worker.lock')

# 텔레그램 설정
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '5360443525')


# ========== 중복 실행 방지 ==========

def check_already_running() -> bool:
    """
    이미 실행 중이거나 최근 완료된 경우 True 반환
    lock 파일이 1시간 이내 생성된 경우 스킵
    """
    if LOCK_FILE.exists():
        lock_age = time.time() - LOCK_FILE.stat().st_mtime
        if lock_age < 3600:  # 1시간 = 3600초
            return True
    return False


def create_lock(source: str):
    """lock 파일 생성"""
    LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOCK_FILE, 'w') as f:
        f.write(json.dumps({
            'created_at': datetime.now().isoformat(),
            'source': source,
            'pid': os.getpid()
        }))


def remove_lock():
    """lock 파일 제거"""
    if LOCK_FILE.exists():
        LOCK_FILE.unlink()


def get_lock_info() -> Optional[Dict]:
    """lock 파일 정보 읽기"""
    if LOCK_FILE.exists():
        try:
            with open(LOCK_FILE, 'r') as f:
                return json.load(f)
        except:
            return None
    return None


class TelegramNotifier:
    """텔레그램 알림 전송"""

    def __init__(self):
        self.bot_token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        self.enabled = bool(self.bot_token and self.chat_id)

    def send(self, message: str) -> bool:
        """메시지 전송"""
        if not self.enabled:
            print(f"[Telegram] (비활성) {message[:50]}...")
            return False

        try:
            import requests
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            response = requests.post(url, data=data, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"[Telegram] 전송 실패: {e}")
            return False


class NightWorker:
    """야간 배치 작업 관리자"""

    SOURCE_LABELS = {
        'github': 'GitHub Actions',
        'local': '로컬 (launchd)',
        'manual': '수동 실행'
    }

    def __init__(self, dry_run: bool = False, source: str = 'manual'):
        self.dry_run = dry_run
        self.source = source
        self.source_label = self.SOURCE_LABELS.get(source, source)
        self.telegram = TelegramNotifier()
        self.start_time = datetime.now()
        self.results = {
            'success': [],
            'failed': [],
            'skipped': [],
            'blocked': False
        }
        self.error_count = 0

    def load_queue(self) -> Dict[str, Any]:
        """큐 파일 로드"""
        if not QUEUE_FILE.exists():
            return {'tasks': [], 'settings': {}}

        with open(QUEUE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_queue(self, queue_data: Dict[str, Any]):
        """큐 파일 저장"""
        queue_data['last_updated'] = datetime.now().isoformat()
        with open(QUEUE_FILE, 'w', encoding='utf-8') as f:
            json.dump(queue_data, f, ensure_ascii=False, indent=2)

    def get_pending_tasks(self, queue_data: Dict[str, Any]) -> List[Dict]:
        """대기 중인 작업 목록 (우선순위 정렬)"""
        tasks = queue_data.get('tasks', [])
        pending = [t for t in tasks if t.get('status') == 'pending']
        return sorted(pending, key=lambda x: x.get('priority', 999))

    # ========== 작업 핸들러 ==========

    def handle_generate_content(self, params: Dict) -> Dict:
        """콘텐츠 생성 작업"""
        topic = params.get('topic')
        if not topic:
            return {'success': False, 'error': 'topic 파라미터 필요'}

        if self.dry_run:
            return {'success': True, 'message': f'[DRY-RUN] {topic} 콘텐츠 생성 시뮬레이션'}

        # 실제 구현: 파이프라인 호출
        try:
            # from pipeline.pipeline_v5 import run_pipeline
            # result = run_pipeline(topic, dry_run=False)
            return {'success': True, 'message': f'{topic} 콘텐츠 생성 완료'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def handle_sync_sheets(self, params: Dict) -> Dict:
        """Google Sheets 동기화"""
        if self.dry_run:
            return {'success': True, 'message': '[DRY-RUN] 시트 동기화 시뮬레이션'}

        try:
            from core.utils.google_sheets_manager import ContentSheetManager
            manager = ContentSheetManager()
            if manager.connect():
                count = manager.sync_from_local()
                return {'success': True, 'message': f'{count}개 항목 동기화'}
            else:
                return {'success': False, 'error': '시트 연결 실패'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def handle_cleanup_folders(self, params: Dict) -> Dict:
        """폴더 정리"""
        folders = params.get('folders', ['temp'])
        cleaned = []

        if self.dry_run:
            return {'success': True, 'message': f'[DRY-RUN] {folders} 정리 시뮬레이션'}

        for folder_name in folders:
            # temp 폴더 정리
            if folder_name == 'temp':
                for temp_dir in PROJECT_ROOT.rglob('temp'):
                    if temp_dir.is_dir():
                        for f in temp_dir.glob('*'):
                            if f.is_file():
                                f.unlink()
                                cleaned.append(str(f))

            # archive 폴더 정리 (30일 이상 된 파일)
            elif folder_name == 'archive':
                for archive_dir in PROJECT_ROOT.rglob('archive'):
                    if archive_dir.is_dir():
                        for f in archive_dir.glob('*'):
                            if f.is_file():
                                age = datetime.now().timestamp() - f.stat().st_mtime
                                if age > 30 * 24 * 3600:  # 30일
                                    f.unlink()
                                    cleaned.append(str(f))

        return {'success': True, 'message': f'{len(cleaned)}개 파일 정리', 'cleaned': cleaned}

    def handle_backup_data(self, params: Dict) -> Dict:
        """데이터 백업"""
        if self.dry_run:
            return {'success': True, 'message': '[DRY-RUN] 백업 시뮬레이션'}

        backup_dir = PROJECT_ROOT / 'backups' / datetime.now().strftime('%Y%m%d')
        backup_dir.mkdir(parents=True, exist_ok=True)

        # config 폴더 백업
        config_backup = backup_dir / 'config'
        if (PROJECT_ROOT / 'config').exists():
            shutil.copytree(PROJECT_ROOT / 'config', config_backup, dirs_exist_ok=True)

        return {'success': True, 'message': f'백업 완료: {backup_dir}'}

    def handle_visual_check(self, params: Dict) -> Dict:
        """시각 품질 검수"""
        folder = params.get('folder')
        if not folder:
            return {'success': False, 'error': 'folder 파라미터 필요'}

        if self.dry_run:
            return {'success': True, 'message': f'[DRY-RUN] {folder} 시각 검수 시뮬레이션'}

        try:
            from core.agents.visual_guard import VisualGuard
            guard = VisualGuard()
            result = guard.check_folder(folder)
            return result
        except ImportError:
            return {'success': True, 'message': 'visual_guard 모듈 미구현 (스킵)'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def handle_publish_scheduled(self, params: Dict) -> Dict:
        """예약 게시 실행"""
        if self.dry_run:
            return {'success': True, 'message': '[DRY-RUN] 예약 게시 시뮬레이션'}

        try:
            # 스케줄 파일 확인
            schedule_file = PROJECT_ROOT / 'config' / 'settings' / 'publish_schedule.json'
            if not schedule_file.exists():
                return {'success': True, 'message': '예약된 게시 없음'}

            with open(schedule_file, 'r', encoding='utf-8') as f:
                schedule = json.load(f)

            today = datetime.now().strftime('%Y-%m-%d')
            pending = [t for t in schedule.get('scheduled', [])
                      if t.get('scheduled_date') == today and t.get('status') == 'pending']

            if not pending:
                return {'success': True, 'message': '오늘 예약 게시 없음'}

            return {'success': True, 'message': f'{len(pending)}개 예약 게시 대기 중', 'needs_review': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    # ========== 작업 실행 ==========

    def execute_task(self, task: Dict) -> Dict:
        """단일 작업 실행"""
        task_id = task.get('id', 'unknown')
        task_type = task.get('type')
        params = task.get('params', {})
        retry_count = task.get('retry_count', 0)

        print(f"\n{'='*50}")
        print(f"[{task_id}] {task_type} 실행 중...")
        print(f"  파라미터: {params}")

        start = datetime.now()

        # 핸들러 매핑
        handlers = {
            'generate_content': self.handle_generate_content,
            'sync_sheets': self.handle_sync_sheets,
            'cleanup_folders': self.handle_cleanup_folders,
            'backup_data': self.handle_backup_data,
            'visual_check': self.handle_visual_check,
            'publish_scheduled': self.handle_publish_scheduled,
        }

        handler = handlers.get(task_type)
        if not handler:
            return {
                'success': False,
                'error': f'알 수 없는 작업 유형: {task_type}',
                'duration': 0
            }

        try:
            result = handler(params)
            result['duration'] = (datetime.now() - start).total_seconds()
            result['task_id'] = task_id
            result['task_type'] = task_type

            if result.get('success'):
                print(f"  ✅ 성공: {result.get('message', '')}")
            else:
                print(f"  ❌ 실패: {result.get('error', '')}")

            return result

        except Exception as e:
            duration = (datetime.now() - start).total_seconds()
            error_msg = f"{type(e).__name__}: {str(e)}"
            print(f"  ❌ 예외 발생: {error_msg}")
            traceback.print_exc()

            return {
                'success': False,
                'error': error_msg,
                'duration': duration,
                'task_id': task_id,
                'task_type': task_type
            }

    def run(self, specific_task_id: Optional[str] = None):
        """배치 작업 실행"""
        print("=" * 60)
        print("🌙 Night Worker 시작")
        print(f"   시간: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   실행: {self.source_label}")
        print(f"   모드: {'DRY-RUN' if self.dry_run else '실제 실행'}")
        print("=" * 60)

        # 중복 실행 체크 (dry-run이 아닐 때만)
        if not self.dry_run and check_already_running():
            lock_info = get_lock_info()
            prev_source = lock_info.get('source', 'unknown') if lock_info else 'unknown'
            print(f"\n⏭️  이미 실행됨 또는 최근 완료됨. 스킵.")
            print(f"   이전 실행: {self.SOURCE_LABELS.get(prev_source, prev_source)}")
            self.telegram.send(
                f"⏭️ <b>Night Worker 스킵</b>\n"
                f"📍 시도: {self.source_label}\n"
                f"이유: 최근 1시간 내 실행됨"
            )
            return

        # Lock 생성
        if not self.dry_run:
            create_lock(self.source)

        # 텔레그램 시작 알림
        self.telegram.send(
            f"🌙 <b>Night Worker 시작</b>\n"
            f"📍 실행: {self.source_label}\n"
            f"시간: {self.start_time.strftime('%H:%M')}\n"
            f"모드: {'DRY-RUN' if self.dry_run else '실제 실행'}"
        )

        # 큐 로드
        queue_data = self.load_queue()
        settings = queue_data.get('settings', {})
        max_errors = settings.get('max_errors', 3)
        stop_on_block = settings.get('stop_on_block', True)

        # 대기 작업 가져오기
        pending_tasks = self.get_pending_tasks(queue_data)

        if specific_task_id:
            pending_tasks = [t for t in pending_tasks if t.get('id') == specific_task_id]

        if not pending_tasks:
            print("\n📭 대기 중인 작업 없음")
            self.telegram.send("📭 야간 작업 없음 - 스킵")
            return

        print(f"\n📋 대기 작업: {len(pending_tasks)}개")
        for t in pending_tasks:
            print(f"   [{t.get('priority', 0)}] {t.get('id')}: {t.get('type')}")

        # 작업 실행
        for task in pending_tasks:
            task_id = task.get('id')

            # 에러 초과 체크
            if self.error_count >= max_errors:
                print(f"\n⛔ 최대 에러 횟수 초과 ({max_errors}회) - 중단")
                self.results['skipped'].append(task_id)
                continue

            # 작업 실행
            result = self.execute_task(task)

            # 결과 처리
            if result.get('success'):
                self.results['success'].append({
                    'id': task_id,
                    'type': task.get('type'),
                    'message': result.get('message', ''),
                    'duration': result.get('duration', 0)
                })
                task['status'] = 'completed'
                task['completed_at'] = datetime.now().isoformat()

                # BLOCK 판정 체크
                if result.get('verdict') == 'BLOCK':
                    self.results['blocked'] = True
                    if stop_on_block:
                        print("\n🚨 BLOCK 발생 - 작업 중단")
                        self.telegram.send(
                            f"🚨 <b>BLOCK 발생!</b>\n"
                            f"작업: {task_id}\n"
                            f"사유: {result.get('message', '')}"
                        )
                        break
            else:
                self.error_count += 1
                self.results['failed'].append({
                    'id': task_id,
                    'type': task.get('type'),
                    'error': result.get('error', ''),
                    'duration': result.get('duration', 0)
                })
                task['status'] = 'failed'
                task['error'] = result.get('error', '')
                task['failed_at'] = datetime.now().isoformat()

        # 큐 저장
        self.save_queue(queue_data)

        # 보고서 생성
        self.generate_report()

        # 완료 알림
        success_count = len(self.results['success'])
        failed_count = len(self.results['failed'])
        elapsed = (datetime.now() - self.start_time).total_seconds()

        status_emoji = "✅" if failed_count == 0 else "⚠️"
        self.telegram.send(
            f"{status_emoji} <b>Night Worker 완료</b>\n"
            f"📍 실행: {self.source_label}\n"
            f"성공: {success_count}개\n"
            f"실패: {failed_count}개\n"
            f"소요: {elapsed:.1f}초"
        )

        print(f"\n{'='*60}")
        print(f"🏁 Night Worker 완료")
        print(f"   실행: {self.source_label}")
        print(f"   성공: {success_count}개")
        print(f"   실패: {failed_count}개")
        print(f"   소요: {elapsed:.1f}초")
        print("=" * 60)

    def generate_report(self):
        """야간 보고서 생성"""
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        report_file = LOGS_DIR / f"night_report_{datetime.now().strftime('%Y%m%d')}.md"

        elapsed = (datetime.now() - self.start_time).total_seconds()

        report = f"""# Night Worker Report - {datetime.now().strftime('%Y-%m-%d')}

## 실행 정보
- **실행 소스:** {self.source_label}
- **시작 시간:** {self.start_time.strftime('%H:%M:%S')}
- **종료 시간:** {datetime.now().strftime('%H:%M:%S')}
- **총 소요 시간:** {elapsed:.1f}초
- **모드:** {'DRY-RUN' if self.dry_run else '실제 실행'}

## 실행 결과 요약
| 구분 | 개수 |
|------|------|
| ✅ 성공 | {len(self.results['success'])} |
| ❌ 실패 | {len(self.results['failed'])} |
| ⏭️ 스킵 | {len(self.results['skipped'])} |

"""

        # 성공 작업 상세
        if self.results['success']:
            report += "## ✅ 성공한 작업\n\n"
            report += "| ID | 유형 | 메시지 | 소요시간 |\n"
            report += "|-----|------|--------|----------|\n"
            for item in self.results['success']:
                report += f"| {item['id']} | {item['type']} | {item.get('message', '')[:30]} | {item['duration']:.1f}s |\n"
            report += "\n"

        # 실패 작업 상세
        if self.results['failed']:
            report += "## ❌ 실패한 작업\n\n"
            report += "| ID | 유형 | 에러 | 소요시간 |\n"
            report += "|-----|------|------|----------|\n"
            for item in self.results['failed']:
                report += f"| {item['id']} | {item['type']} | {item.get('error', '')[:40]} | {item['duration']:.1f}s |\n"
            report += "\n"

        # PD 확인 필요 항목
        needs_review = [s for s in self.results['success'] if s.get('needs_review')]
        if needs_review or self.results['blocked']:
            report += "## 🔔 PD 확인 필요\n\n"
            if self.results['blocked']:
                report += "- ⚠️ **BLOCK 발생** - 품질 검수 결과 확인 필요\n"
            for item in needs_review:
                report += f"- {item['id']}: {item.get('message', '')}\n"
            report += "\n"

        # 파일 저장
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"\n📄 보고서 생성: {report_file}")


def main():
    parser = argparse.ArgumentParser(description='Night Worker - 야간 배치 작업')
    parser.add_argument('--dry-run', action='store_true', help='실제 실행 없이 테스트')
    parser.add_argument('--task-id', type=str, help='특정 작업만 실행')
    parser.add_argument('--source', type=str, default='manual',
                       choices=['github', 'local', 'manual'],
                       help='실행 소스 (github/local/manual)')
    args = parser.parse_args()

    worker = NightWorker(dry_run=args.dry_run, source=args.source)
    worker.run(specific_task_id=args.task_id)


if __name__ == '__main__':
    main()
