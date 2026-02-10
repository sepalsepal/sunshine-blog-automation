# ➕ 새 주제 추가

새로운 강아지 음식 주제를 추가합니다.

## 필요한 정보
- 주제명 (영문): $ARGUMENTS
- 한글명: 입력 필요
- 카테고리: fruit / vegetable / meat / seafood / dairy / other

## 자동 생성 파일
1. `config/{topic}_text.json` - 10장 슬라이드 텍스트
2. `config/image_prompts/{topic}.md` - 이미지 생성 프롬프트
3. `agents/caption.py` 업데이트 - food_database에 추가

## 실행 순서
```bash
cd /Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine

# 1. 텍스트 설정 파일 생성
python scripts/generate_topic_config.py --topic "$ARGUMENTS"

# 2. 이미지 프롬프트 생성
python scripts/generate_image_prompts.py --topic "$ARGUMENTS"

# 3. caption.py food_database 업데이트
python scripts/update_food_database.py --topic "$ARGUMENTS"

# 4. 테스트 실행
python -m pytest tests/test_agents.py -k "$ARGUMENTS" -v

# 5. 드라이런 테스트
python cli.py "$ARGUMENTS" --dry-run
```

## 주제별 템플릿
- **과일 (fruit):** 단맛, 수분, 비타민 강조
- **채소 (vegetable):** 섬유질, 저칼로리 강조
- **육류 (meat):** 단백질, 조리법 주의사항
- **해산물 (seafood):** 오메가3, 알레르기 주의
- **유제품 (dairy):** 유당불내증 주의

## 완료 후 체크리스트
- [ ] config 파일 생성 확인
- [ ] 테스트 통과
- [ ] --dry-run 성공
- [ ] CLAUDE.md에 기록
