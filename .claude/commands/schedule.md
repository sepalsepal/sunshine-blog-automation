# 📅 게시 스케줄 관리

콘텐츠 게시 일정을 확인하고 관리합니다.

## 기능
- 이번 주/다음 주 게시 일정 확인
- 최적 게시 시간 추천
- 중복 주제 확인

## 실행 명령
```bash
cd /Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine

# 스케줄 확인
python -c "
from agents.scheduler import SchedulerAgent

scheduler = SchedulerAgent()

# 이번 주 일정
print('📅 이번 주 게시 일정:')
for item in scheduler.get_weekly_schedule():
    print(f'  {item.date} - {item.topic} ({item.status})')

# 최적 게시 시간
print('\n⏰ 오늘 최적 게시 시간:')
optimal = scheduler.get_optimal_time()
print(f'  {optimal} (한국시간)')

# 다음 추천 주제
print('\n💡 다음 추천 주제:')
for topic in scheduler.recommend_next_topics(3):
    print(f'  - {topic.name} (마지막 게시: {topic.last_posted})')
"
```

## 게시 시간 규칙
- **최적 시간:** 오후 6-9시 (한국시간)
- **평일:** 저녁 7-8시 권장
- **주말:** 오후 5-6시 권장

## 중복 방지 규칙
- 같은 주제: 최소 30일 간격
- 같은 카테고리: 최소 7일 간격
- 연속 게시: 최소 24시간 간격
