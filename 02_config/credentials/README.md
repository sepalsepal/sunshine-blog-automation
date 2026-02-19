# Credentials 폴더

> 이 폴더는 인증/보안 관련 파일을 통합 관리합니다.
> **Git에 커밋하지 마세요!**

## 파일 목록

| 파일명 | 용도 | 원본명 |
|--------|------|--------|
| google_oauth.json | Google OAuth 클라이언트 인증 | client_secret.json |
| firebase.json | Firebase 서비스 인증 | firebase_key.json |
| google_service.json | Google 서비스 계정 키 | service-account-key.json |
| google_token.pickle | Google API 액세스 토큰 | token.pickle |
| telegram.txt | Telegram Bot Chat ID | chat_id.txt |

## 환경변수

민감한 API 키는 `.env` 파일에서 관리합니다.
`.env` 파일은 프로젝트 루트에 위치합니다.

## 보안 주의사항

- 이 폴더의 파일들은 절대 Git에 커밋하지 마세요
- `.gitignore`에 `config/credentials/` 추가됨
- 토큰 만료 시 `google_token.pickle` 재생성 필요

---
_마지막 업데이트: 2026-02-19_
