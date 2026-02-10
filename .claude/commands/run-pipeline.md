# 🚀 전체 파이프라인 실행

햇살이 Instagram 콘텐츠 파이프라인을 실행합니다.

## 실행 순서
1. 김차장 → 주제 기획 및 구조 설계
2. 최검증 → 팩트 체크 (독성 여부 확인)
3. 김작가 → 슬라이드 텍스트 작성
4. 이작가 → AI 이미지 생성
5. 박편집 → 이미지 편집 및 텍스트 오버레이
6. 박과장 → 품질 검수 (85점 이상 통과)
7. 이카피 → 캡션 및 해시태그 생성
8. 김대리 → Instagram 게시
9. 정분석 → 성과 분석

## 사용 예시
```
/run-pipeline cherry
/run-pipeline banana --dry-run
/run-pipeline grape --start-from 이작가
```

## 실행 명령
```bash
cd /Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine
python cli.py $ARGUMENTS
```

## 완료 기준
- 모든 에이전트 정상 실행
- 박과장 검수 점수 85점 이상
- --dry-run이 아닌 경우 Instagram 게시 완료

## 주의사항
- 실제 게시 전 반드시 --dry-run으로 테스트
- 게시 시간은 한국시간 오후 6-9시 권장
- 중복 주제는 최소 30일 간격 유지
