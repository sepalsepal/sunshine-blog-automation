# Cloudinary 업로드 규칙

## 버전: 1.0
## 최종 수정: 2026-02-14

---

## 목적

Cloudinary 이미지 업로드 시 준수해야 할 규칙을 정의한다.

---

## 규칙

### 1. 기본 설정

```python
cloudinary.uploader.upload(
    file_path,
    public_id="{폴더}/{파일명}",    # PascalCase
    overwrite=False,                 # 🔴 반드시 False
    resource_type="image"
)
```

---

### 2. public_id 규칙

| 항목 | 규칙 |
|------|------|
| 형식 | sunshine/{Food}_{Type}_{Number}_{Name} |
| 케이스 | PascalCase |
| 폴더 | sunshine/ 고정 |

**예시:**
```
sunshine/Pumpkin_Common_01_Cover
sunshine/Carrot_Blog_03_Nutrition
sunshine/SweetPotato_Safe_Insta_Caption
```

---

### 3. overwrite 정책

**overwrite=False 고정**

- 동일 public_id 존재 시: 기존 자산 반환 (덮어쓰기 안 함)
- 새 버전 업로드 시: 새 public_id 사용 또는 기존 삭제 후 업로드

---

### 4. 중복 업로드 금지

업로드 전 기존 URL 확인:

```python
# 기존 URL이 있는 경우 재업로드 금지
existing_url = get_existing_cloudinary_url(public_id)
if existing_url:
    return existing_url  # 기존 URL 반환
else:
    # 새 업로드 진행
```

---

### 5. 대소문자 구분

Cloudinary는 public_id 대소문자를 **구분**한다.

```
sunshine/Pumpkin_Cover  ≠  sunshine/pumpkin_cover
```

PascalCase 통일 필수.

---

### 6. 태그 사용

```python
tags=["cover", "v2.1", "SAFE"]
```

| 태그 | 용도 |
|------|------|
| cover/blog/insta | 이미지 유형 |
| v2.1 | 버전 |
| SAFE/CAUTION/DANGER/FORBIDDEN | 안전도 |

---

## 금지 사항

| 금지 | 이유 |
|------|------|
| overwrite=True | 기존 자산 손실 위험 |
| snake_case public_id | 네이밍 불일치 |
| 중복 업로드 | 스토리지 낭비 |
| 기존 폴더 삭제 | 참조 링크 깨짐 |

---

## 위반 사례

| 위반 | 사례 |
|------|------|
| overwrite=True 사용 | 기존 이미지 덮어씀 |
| 소문자 public_id | sunshine/pumpkin_cover |
| URL 확인 없이 업로드 | 중복 파일 생성 |

---

## Validator 체크리스트

```
□ overwrite=False 사용
□ public_id PascalCase
□ sunshine/ 폴더 사용
□ 기존 URL 확인 후 업로드
□ 태그 포함
□ 업로드 성공 시 URL 접근 가능
```
