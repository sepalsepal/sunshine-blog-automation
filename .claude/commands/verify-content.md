# 🔍 콘텐츠 품질 검증

생성된 콘텐츠의 품질을 검증합니다. (검증 루프 적용)

## 검증 항목

### 1. 텍스트 검증
- [ ] 맞춤법/문법 오류 없음
- [ ] 팩트 정확성 (독성 정보 특히 중요)
- [ ] 슬라이드 10장 구성 완료
- [ ] CTA 및 해시태그 적절성

### 2. 이미지 검증
- [ ] 해상도: 1080x1080px
- [ ] 텍스트 가독성
- [ ] 언더라인 길이: 텍스트 너비 + 20px
- [ ] 브랜드 일관성

### 3. 캡션 검증
- [ ] 2200자 이내
- [ ] 해시태그 30개 이내
- [ ] 중복 해시태그 없음
- [ ] CTA 포함

## 실행 명령
```bash
cd /Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine
python -c "
from agents.quality_checker import QualityChecker
checker = QualityChecker()
result = checker.verify('$ARGUMENTS')
print(f'품질 점수: {result.score}/100')
print(f'통과 여부: {\"✅ PASS\" if result.score >= 85 else \"❌ FAIL\"}')
for issue in result.issues:
    print(f'  - {issue}')
"
```

## 완료 기준
- 품질 점수 85점 이상
- 모든 체크리스트 통과
- 이슈 0개

## 검증 실패 시
1. 이슈 목록 확인
2. 해당 에이전트 재실행
3. 다시 검증 실행
4. 3회 실패 시 수동 검토 요청
