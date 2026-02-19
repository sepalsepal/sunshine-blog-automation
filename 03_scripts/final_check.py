#!/usr/bin/env python3
"""
최종 검증 스크립트 (Final Check)
AgentStop hook과 연동되어 작업 완료 전 자동 실행됩니다.

Boris Cherny의 "모델이 스스로 틀렸다는 걸 알아차릴 수 있는 환경" 구현
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict


@dataclass
class CheckResult:
    """검증 결과"""
    category: str
    item: str
    passed: bool
    message: str
    severity: str = "info"  # info, warning, error


@dataclass
class FinalCheckReport:
    """최종 검증 리포트"""
    timestamp: str
    topic: str
    total_checks: int
    passed_checks: int
    failed_checks: int
    warnings: int
    score: float
    results: List[Dict]
    recommendation: str


class FinalChecker:
    """최종 검증기"""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root or os.getcwd())
        self.results: List[CheckResult] = []
        
    def check_text_content(self, topic: str) -> List[CheckResult]:
        """텍스트 콘텐츠 검증"""
        results = []
        config_path = self.project_root / f"config/{topic}_text.json"
        
        if not config_path.exists():
            results.append(CheckResult(
                category="텍스트",
                item="설정 파일",
                passed=False,
                message=f"config/{topic}_text.json 파일이 없습니다",
                severity="error"
            ))
            return results
            
        with open(config_path, 'r', encoding='utf-8') as f:
            content = json.load(f)
            
        # 슬라이드 개수 확인
        slides = content.get('slides', [])
        results.append(CheckResult(
            category="텍스트",
            item="슬라이드 개수",
            passed=len(slides) == 10,
            message=f"슬라이드 {len(slides)}개 (기준: 10개)",
            severity="error" if len(slides) != 10 else "info"
        ))
        
        # 표지 존재 확인
        if slides:
            has_cover = slides[0].get('type') == 'cover'
            results.append(CheckResult(
                category="텍스트",
                item="표지",
                passed=has_cover,
                message="표지 슬라이드 존재" if has_cover else "표지 슬라이드 없음",
                severity="warning" if not has_cover else "info"
            ))
            
        # 글자 수 확인 (각 슬라이드 50자 이하 권장)
        long_slides = [i+1 for i, s in enumerate(slides) if len(s.get('text', '')) > 50]
        results.append(CheckResult(
            category="텍스트",
            item="글자 수",
            passed=len(long_slides) == 0,
            message=f"긴 슬라이드: {long_slides}" if long_slides else "모든 슬라이드 적정 길이",
            severity="warning" if long_slides else "info"
        ))
        
        return results
        
    def check_images(self, topic: str) -> List[CheckResult]:
        """이미지 검증"""
        results = []
        output_dir = self.project_root / f"outputs/{topic}"
        
        if not output_dir.exists():
            results.append(CheckResult(
                category="이미지",
                item="출력 폴더",
                passed=False,
                message=f"outputs/{topic} 폴더가 없습니다",
                severity="error"
            ))
            return results
            
        images = list(output_dir.glob("*.png")) + list(output_dir.glob("*.jpg"))
        
        # 이미지 개수 확인
        results.append(CheckResult(
            category="이미지",
            item="이미지 개수",
            passed=len(images) == 10,
            message=f"이미지 {len(images)}개 (기준: 10개)",
            severity="error" if len(images) != 10 else "info"
        ))
        
        # 이미지 크기 확인 (PIL 필요)
        try:
            from PIL import Image
            for img_path in images[:3]:  # 처음 3개만 샘플 확인
                with Image.open(img_path) as img:
                    w, h = img.size
                    correct_size = (w == 1080 and h == 1080)
                    results.append(CheckResult(
                        category="이미지",
                        item=f"크기 ({img_path.name})",
                        passed=correct_size,
                        message=f"{w}x{h} (기준: 1080x1080)",
                        severity="error" if not correct_size else "info"
                    ))
        except ImportError:
            results.append(CheckResult(
                category="이미지",
                item="크기 검증",
                passed=True,
                message="PIL 없음 - 크기 검증 스킵",
                severity="warning"
            ))
            
        return results
        
    def check_caption(self, topic: str) -> List[CheckResult]:
        """캡션 검증"""
        results = []
        caption_path = self.project_root / f"outputs/{topic}/caption.txt"
        
        if not caption_path.exists():
            results.append(CheckResult(
                category="캡션",
                item="캡션 파일",
                passed=False,
                message="caption.txt 파일이 없습니다",
                severity="error"
            ))
            return results
            
        with open(caption_path, 'r', encoding='utf-8') as f:
            caption = f.read()
            
        # 길이 확인 (Instagram 제한: 2200자)
        results.append(CheckResult(
            category="캡션",
            item="길이",
            passed=len(caption) <= 2200,
            message=f"{len(caption)}자 (제한: 2200자)",
            severity="error" if len(caption) > 2200 else "info"
        ))
        
        # 해시태그 개수 확인 (Instagram 제한: 30개)
        hashtags = [w for w in caption.split() if w.startswith('#')]
        results.append(CheckResult(
            category="캡션",
            item="해시태그 개수",
            passed=len(hashtags) <= 30,
            message=f"{len(hashtags)}개 (제한: 30개)",
            severity="error" if len(hashtags) > 30 else "info"
        ))
        
        # 해시태그 중복 확인
        unique_hashtags = set(hashtags)
        has_duplicates = len(hashtags) != len(unique_hashtags)
        results.append(CheckResult(
            category="캡션",
            item="해시태그 중복",
            passed=not has_duplicates,
            message="중복 없음" if not has_duplicates else f"중복 {len(hashtags) - len(unique_hashtags)}개",
            severity="warning" if has_duplicates else "info"
        ))
        
        return results
        
    def check_quality_score(self, topic: str) -> List[CheckResult]:
        """품질 점수 확인"""
        results = []
        score_path = self.project_root / f"outputs/{topic}/quality_score.json"
        
        if not score_path.exists():
            results.append(CheckResult(
                category="품질",
                item="품질 점수 파일",
                passed=False,
                message="quality_score.json 파일이 없습니다",
                severity="warning"
            ))
            return results
            
        with open(score_path, 'r', encoding='utf-8') as f:
            score_data = json.load(f)
            
        score = score_data.get('score', 0)
        results.append(CheckResult(
            category="품질",
            item="박과장 검수 점수",
            passed=score >= 85,
            message=f"{score}점 (기준: 85점)",
            severity="error" if score < 85 else "info"
        ))
        
        return results
        
    def run_all_checks(self, topic: str) -> FinalCheckReport:
        """모든 검증 실행"""
        self.results = []
        
        # 각 카테고리 검증
        self.results.extend(self.check_text_content(topic))
        self.results.extend(self.check_images(topic))
        self.results.extend(self.check_caption(topic))
        self.results.extend(self.check_quality_score(topic))
        
        # 결과 집계
        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed and r.severity == 'error')
        warnings = sum(1 for r in self.results if not r.passed and r.severity == 'warning')
        total = len(self.results)
        score = (passed / total * 100) if total > 0 else 0
        
        # 권장사항 결정
        if failed > 0:
            recommendation = "❌ FAIL - 에러 수정 후 재실행 필요"
        elif warnings > 2:
            recommendation = "⚠️ WARNING - 경고 확인 후 진행 권장"
        elif score >= 90:
            recommendation = "✅ PASS - 게시 가능"
        else:
            recommendation = "🔄 REVIEW - 수동 검토 권장"
            
        return FinalCheckReport(
            timestamp=datetime.now().isoformat(),
            topic=topic,
            total_checks=total,
            passed_checks=passed,
            failed_checks=failed,
            warnings=warnings,
            score=score,
            results=[asdict(r) for r in self.results],
            recommendation=recommendation
        )
        
    def print_report(self, report: FinalCheckReport):
        """리포트 출력"""
        print("\n" + "="*60)
        print(f"🔍 최종 검증 리포트 - {report.topic}")
        print("="*60)
        print(f"시간: {report.timestamp}")
        print(f"점수: {report.score:.1f}% ({report.passed_checks}/{report.total_checks})")
        print(f"에러: {report.failed_checks}개 | 경고: {report.warnings}개")
        print("-"*60)
        
        # 카테고리별 결과
        categories = {}
        for r in self.results:
            if r.category not in categories:
                categories[r.category] = []
            categories[r.category].append(r)
            
        for cat, items in categories.items():
            print(f"\n📂 {cat}")
            for item in items:
                status = "✅" if item.passed else ("⚠️" if item.severity == "warning" else "❌")
                print(f"  {status} {item.item}: {item.message}")
                
        print("\n" + "="*60)
        print(f"📋 권장사항: {report.recommendation}")
        print("="*60 + "\n")
        
    def save_report(self, report: FinalCheckReport, output_dir: Path = None):
        """리포트 저장"""
        output_dir = output_dir or self.project_root / "logs"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"final_check_{report.topic}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_dir / filename, 'w', encoding='utf-8') as f:
            json.dump(asdict(report), f, ensure_ascii=False, indent=2)
            
        print(f"📁 리포트 저장: {output_dir / filename}")


def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='최종 검증 스크립트')
    parser.add_argument('topic', nargs='?', default=None, help='검증할 주제')
    parser.add_argument('--project-root', default=None, help='프로젝트 루트 경로')
    parser.add_argument('--save', action='store_true', help='리포트 저장')
    parser.add_argument('--strict', action='store_true', help='에러 시 종료 코드 1 반환')
    
    args = parser.parse_args()
    
    # 주제가 없으면 최근 작업 확인
    if not args.topic:
        # outputs 폴더에서 가장 최근 폴더 찾기
        project_root = Path(args.project_root or os.getcwd())
        outputs = project_root / "outputs"
        if outputs.exists():
            folders = [f for f in outputs.iterdir() if f.is_dir()]
            if folders:
                latest = max(folders, key=lambda f: f.stat().st_mtime)
                args.topic = latest.name
                print(f"📌 자동 감지된 주제: {args.topic}")
            else:
                print("❌ outputs 폴더에 주제 폴더가 없습니다.")
                sys.exit(1)
        else:
            print("❌ outputs 폴더가 없습니다.")
            sys.exit(1)
    
    # 검증 실행
    checker = FinalChecker(args.project_root)
    report = checker.run_all_checks(args.topic)
    
    # 리포트 출력
    checker.print_report(report)
    
    # 리포트 저장
    if args.save:
        checker.save_report(report)
    
    # strict 모드에서 실패 시 종료 코드 1
    if args.strict and report.failed_checks > 0:
        sys.exit(1)
        
    # DONE 또는 FAIL 출력 (Ralph Wiggum 연동)
    if report.recommendation.startswith("✅"):
        print("DONE")
    else:
        print("RETRY")


if __name__ == "__main__":
    main()
