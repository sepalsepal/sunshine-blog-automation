# 클린 이미지 배포 규칙 (CLEAN_IMAGE_DISTRIBUTE_RULE)

> 버전 1.0 | 2026-02-18
> 000_CleanReady 폴더의 클린 이미지 네이밍 및 배포 규칙

---

## 1. 000_CleanReady 폴더 구조

```
01_contents/000_CleanReady/
├── 01_cover/        ← 표지용 클린 이미지 (강아지+음식)
├── 02_food/         ← 음식 사진 클린 이미지 (음식만)
└── 03_DogWithFood/  ← 강아지+음식 브릿지 이미지
```

---

## 2. 이미지 유형별 네이밍 규칙

### 2.1 원본 파일 (업로드 시)

huggingface에서 다운로드 시 자동 생성되는 형식:
```
hf_{날짜}_{시간}_{UUID}.png
```

### 2.2 네이밍된 파일 (배포용)

| 폴더 | 네이밍 패턴 | 예시 |
|------|-------------|------|
| 01_cover | `{번호}_{영문명}_Common_01_Cover_Clean.png` | `017_Peach_Common_01_Cover_Clean.png` |
| 02_food | `{번호}_{영문명}_Common_02_Food.png` | `017_Peach_Common_02_Food.png` |
| 03_DogWithFood | `{번호}_{영문명}_Common_03_DogWithFood_Clean.png` | `017_Peach_Common_03_DogWithFood_Clean.png` |

---

## 3. 배포 절차

### 3.1 배포 작업 순서

```
[1] 이미지 식별 (어떤 음식인지 확인)
[2] 노션 DB에서 번호/영문명 확인
[3] 000_CleanReady 내에서 네이밍 (원본 보존 + 네이밍 복사본 생성)
[4] 대상 콘텐츠 폴더로 복사
[5] (선택) 노션 상태 업데이트
```

### 3.2 배포 대상 폴더

| 소스 폴더 | 배포 대상 | 배포 파일명 |
|----------|----------|-------------|
| 01_cover | `{번호}_{영문명}/` | `{번호}_{영문명}_Common_01_Cover.png` |
| 02_food | `{번호}_{영문명}/` | `{번호}_{영문명}_Common_02_Food.png` |
| 03_DogWithFood | `{번호}_{영문명}/` | `{번호}_{영문명}_Common_03_DogWithFood.png` |

### 3.3 배포 명령어 예시

```bash
# 02_food 배포
cp "000_CleanReady/02_food/017_Peach_Common_02_Food.png" \
   "017_Peach/017_Peach_Common_02_Food.png"

# 01_cover 배포
cp "000_CleanReady/01_cover/017_Peach_Common_01_Cover_Clean.png" \
   "017_Peach/017_Peach_Common_01_Cover.png"

# 03_DogWithFood 배포
cp "000_CleanReady/03_DogWithFood/017_Peach_Common_03_DogWithFood_Clean.png" \
   "017_Peach/017_Peach_Common_03_DogWithFood.png"
```

---

## 4. 영문명 규칙

| 항목 | 규칙 | 예시 |
|-----|------|------|
| 대소문자 | PascalCase | `BananaMilk`, `EggYolk` |
| 공백 | 없음 | `ChickenBreast` (O), `Chicken Breast` (X) |
| 특수문자 | 사용 금지 | `Sweet_Potato` (X) |
| 번호 | 3자리 zero-padding | `017`, `003`, `121` |

---

## 5. 원본 보존 원칙 (🚨 최우선 규칙)

### 5.1 절대 삭제 금지

| 항목 | 규칙 |
|-----|------|
| hf_ 원본 | **절대 삭제 금지** (백업 이미지) |
| 네이밍된 파일 | **절대 삭제 금지** |
| 000_CleanReady 전체 | **PD 승인 2회 없이 삭제 불가** |

### 5.2 삭제 승인 절차

```
삭제 요청 시:
[1] PD 1차 승인 요청 → 승인 받음
[2] PD 2차 확인 승인 요청 → 승인 받음
[3] 삭제 실행
```

⚠️ **경고:** 000_CleanReady는 원본 백업 폴더입니다.
- 복구 불가능한 소스 이미지 보관
- 무단 삭제 시 프로젝트 전체에 영향
- **Claude는 PD 승인 2회 없이 절대 삭제 금지**

### 5.3 네이밍 작업 원칙

| 작업 | 방법 |
|-----|------|
| 네이밍 | 원본 **복사(cp)** 후 이름 변경 |
| 배포 | 000_CleanReady에서 대상 폴더로 **복사(cp)** |
| 이동 | **금지** (mv 사용 금지) |
| 삭제 | **금지** (rm 사용 금지) |

---

## 6. 일괄 배포 스크립트

### 6.1 02_food 일괄 배포

```bash
cd "01_contents"
for file in 000_CleanReady/02_food/*_Common_02_Food.png; do
  filename=$(basename "$file")
  num=$(echo "$filename" | cut -d'_' -f1)
  target_dir=$(find . -maxdepth 1 -type d -name "${num}_*" | head -1)

  if [ -n "$target_dir" ] && [ ! -f "${target_dir}/${filename}" ]; then
    cp "$file" "${target_dir}/${filename}"
    echo "OK: ${filename}"
  fi
done
```

---

## 7. 체크리스트

배포 전 확인 사항:

- [ ] 이미지 음식 식별 완료
- [ ] 노션에서 번호/영문명 확인
- [ ] 000_CleanReady 내 네이밍 완료
- [ ] 대상 폴더 존재 확인
- [ ] 파일명 네이밍 규칙 준수
- [ ] 원본 hf_ 파일 보존 확인

---

## 8. 폴더 없는 이미지 처리 프로세스

### 8.1 처리 순서

```
[1] 이미지 식별 (어떤 음식인지 확인)
[2] 기존 폴더 목록에서 비슷한 음식 검색
[3] PD에게 유사 음식 후보 제시 및 컨펌 요청
[4] PD 승인 후 해당 폴더에 배포
```

### 8.2 유사 음식 검색 기준

| 기준 | 예시 |
|-----|------|
| 동일 카테고리 | 버터 → 치즈, 우유 (유제품) |
| 조리 형태 유사 | 매쉬드포테이토 → 감자샐러드 |
| 재료 유사 | 계란프라이 → 삶은계란, 스크램블 |

### 8.3 PD 컨펌 요청 형식

```
⚠️ 폴더 없는 이미지 발견

이미지: hf_20260216_xxxxxx.png
식별된 음식: {음식명}

유사 폴더 후보:
1. {번호}_{영문명} - {한글명} (유사도: 높음/중간)
2. {번호}_{영문명} - {한글명} (유사도: 높음/중간)

어느 폴더에 배포할까요? 또는 신규 폴더 생성하시겠습니까?
```

### 8.4 PD 응답에 따른 처리

| PD 응답 | 처리 |
|--------|------|
| 기존 폴더 지정 | 해당 폴더에 배포 |
| 신규 폴더 생성 | PD가 노션 등록 후 폴더 생성 → 배포 |
| 보류 | hf_ 원본 상태로 유지 |

---

## 9. 금지 사항

| 금지 | 이유 |
|-----|------|
| hf_ 원본 삭제 | 백업 목적 보존 필요 |
| 폴더 없는 음식 임의 생성 | 노션 DB 우선 확인 필요 |
| 기존 파일 덮어쓰기 | 기존 작업물 보호 |
| 네이밍 규칙 무시 | 자동화 스크립트 호환성 |
| PD 컨펌 없이 유사 폴더 배포 | 잘못된 분류 방지 |

---

_마지막 업데이트: 2026-02-18 (v1.1 폴더 없는 이미지 처리 프로세스 추가)_
