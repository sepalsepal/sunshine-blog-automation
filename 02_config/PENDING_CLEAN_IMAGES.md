# 클린 이미지 누락 목록

## 생성일: 2026-02-15
## 상태: 대기 중

---

## 누락 목록 (75개)

| 번호 | 음식명 | 상태 |
|------|--------|------|
| 014 | Pear (배) | ⬜ |
| 032 | Milk (우유) | ⬜ |
| 034 | RedBeanBread (단팥빵) | ⬜ |
| 040 | LotusRoot (연근) | ⬜ |
| 042 | Oatmeal (오트밀) | ⬜ |
| 045 | EggYolk (달걀노른자) | ⬜ |
| 046 | Pomegranate (석류) | ⬜ |
| 047 | Mackerel (고등어) | ⬜ |
| 048 | Tofu (두부) | ⬜ |
| 050 | Plum (자두) | ⬜ |
| 054 | SweetPumpkin (단호박) | ⬜ |
| 056 | Raisin (건포도) | ⬜ |
| 057 | Chocolate (초콜릿) | ⬜ |
| 058 | Kimchi (김치) | ⬜ |
| 059 | QuailEgg (메추리알) | ⬜ |
| 062 | Tteokguk (떡국) | ⬜ |
| 063 | DriedFish (육포) | ⬜ |
| 065 | Bibimbap (비빔밥) | ⬜ |
| 067 | Udon (우동) | ⬜ |
| 070 | Ramen (라면) | ⬜ |
| 073 | Samgyeopsal (삼겹살) | ⬜ |
| 074 | Bulgogi (불고기) | ⬜ |
| 075 | Cake (케이크) | ⬜ |
| 078 | Brownie (브라우니) | ⬜ |
| 079 | Muffin (머핀) | ⬜ |
| 080 | Pancake (팬케이크) | ⬜ |
| 081 | Waffle (와플) | ⬜ |
| 082 | Cereal (시리얼) | ⬜ |
| 083 | Granola (그래놀라) | ⬜ |
| 085 | Dakgangjeong (닭강정) | ⬜ |
| 086 | Meatball (미트볼) | ⬜ |
| 087 | Bacon (베이컨) | ⬜ |
| 089 | CassBeer (카스맥주) | ⬜ |
| 091 | Croissant (크루아상) | ⬜ |
| 092 | Doritos (도리토스) | ⬜ |
| 093 | Fanta (환타) | ⬜ |
| 095 | Lays (레이즈) | ⬜ |
| 096 | Milkis (밀키스) | ⬜ |
| 097 | Perrier (페리에) | ⬜ |
| 099 | Reeses (리세스) | ⬜ |
| 100 | Ritz (리츠) | ⬜ |
| 101 | Skittles (스키틀즈) | ⬜ |
| 102 | Soju (소주) | ⬜ |
| 103 | StarbucksCoffee (스타벅스커피) | ⬜ |
| 104 | Starburst (스타버스트) | ⬜ |
| 105 | Cheese (치즈) | ⬜ |
| 106 | WhiteFish (흰살생선) | ⬜ |
| 107 | Sprite (스프라이트) | ⬜ |
| 108 | ChickenBreast (닭가슴살) | ⬜ |
| 110 | Raspberry (라즈베리) | ⬜ |
| 111 | Coconut (코코넛) | ⬜ |
| 112 | Grapefruit (자몽) | ⬜ |
| 113 | Lemon (레몬) | ⬜ |
| 114 | Cabbage (양배추) | ⬜ |
| 115 | Asparagus (아스파라거스) | ⬜ |
| 116 | Beet (비트) | ⬜ |
| 117 | NapaCabbage (배추) | ⬜ |
| 118 | Lettuce (상추) | ⬜ |
| 121 | GreenBeans (그린빈) | ⬜ |
| 122 | Duck (오리고기) | ⬜ |
| 123 | Tteok (떡) | ⬜ |
| 124 | Peas (완두콩) | ⬜ |
| 125 | DriedPollack (황태) | ⬜ |
| 126 | Mushroom (버섯) | ⬜ |
| 127 | GreenOnion (파) | ⬜ |
| 128 | Squid (오징어) | ⬜ |
| 129 | Anchovy (멸치) | ⬜ |
| 130 | Seaweed (미역) | ⬜ |
| 131 | Pollack (명태) | ⬜ |
| 134 | Bread (식빵) | ⬜ |
| 135 | CoconutOil (코코넛오일) | ⬜ |
| 173 | RoastDuck (오리구이) | ⬜ |
| 175 | Mushroom (버섯) | ⬜ |

---

## 클린 이미지 저장 위치

```
contents/{번호}_{음식명}/00_Clean/{음식명}_Cover_Clean.png
```

---

## 완료 후 실행

```bash
python3 services/scripts/cover_generator.py {번호}
```

또는 전체 재생성:
```bash
for i in $(seq -w 1 175); do python3 services/scripts/cover_generator.py $i 2>&1 | grep -E "(OK|ERROR)"; done
```
