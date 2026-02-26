# Next Execution Plan (Completed)

## 목적
- 현재 구현된 기능을 운영 가능한 상태로 정리한다.
- 범위: 환경 분리, DB 운영 준비, CI/CD 검증 파이프라인, 문서/운영 체크리스트.
- 원칙: 이 문서에서 승인된 항목만 순서대로 진행.

## 현재 기준점
- 브랜치: `main`
- 최신 커밋: `cdce8fc`
- 상태: Phase 1~3 기능 구현 완료, 테스트 통과(11 passed), 원격 반영 완료.

## 실행 결과 요약 (2026-02-26)
- 승인 문구: `승인: 현재안(SQLite 운영 안정화)으로 A->B->C->D 진행`
- 실제 실행 순서: `A -> B -> C -> D -> B-2`
- 결과:
  - [x] A 완료
  - [x] B-1 완료
  - [x] C 완료
  - [x] D 완료
  - [x] B-2 완료
- 검증:
  - [x] `python -m pytest -q tests` 통과 (`17 passed`)
  - [x] 프론트 `npm ci`, `npm run lint`, `npm run build` 통과 (ASCII 임시 경로 검증)

## Git 브랜치 전략 (실행 기준)
1. `main` 직접 커밋 금지, 작업은 Phase/항목 단위 feature 브랜치에서 진행.
2. 브랜치 네이밍:
- `feature/a-env-hardening`
- `feature/b-sqlite-ops`
- `feature/c-ci-pipeline`
- `feature/d-observability`
3. 병합 순서:
- `A -> B -> C -> D` 순서로 `main`에 병합.
4. 커밋 규칙:
- 작업 항목 1개 = 커밋 1개 원칙(롤백 단위 확보).
- 커밋 메시지 예시: `feat(b): add sqlite backup/check scripts`
5. 검증 규칙:
- 병합 전 `pytest -q tests` + 프론트 `npm run lint`, `npm run build` 결과 첨부.

## 실행 전 공통 규칙
1. 각 작업 완료 후 `git diff` + 검증 결과를 기록.
2. 실패 시 즉시 중단하고 롤백 방법 먼저 공유.
3. 문서(`README.md`, `IMPLEMENTATION_DETAILED_PLAN.md`)를 코드 변경과 함께 동기화.

## 작업 백로그 (승인 필요)

### A. 환경/설정 운영화
1. 환경 파일 분리
- 목표: 개발/운영 구분.
- 변경:
  - `backend/.env.example` 보강
  - `frontend/.env.example` 보강
  - `README.md`에 DEV/PROD 설정 예시 추가
- 산출물:
  - 운영 설정 키 표(필수/선택/기본값)
- 검증:
  - 설정 누락 시 부팅 실패 메시지 확인

2. 설정 검증 로직 강화
- 목표: 잘못된 환경값 조기 실패.
- 변경:
  - `backend/config.py`에 유효성 검증(필수값/정수 범위)
- 검증:
  - 잘못된 값 입력 시 명확한 오류 메시지

### B. DB 운영 준비
운영 방식 명확화:
- 현재 B 범위는 `SQLite 운영 안정화`이며, 즉시 PostgreSQL 운영 전환이 아님.
- 따라서 B-1은 Docker/PostgreSQL 설치 작업이 아니라 `기존 SQLite 파일 운영 체크/백업 자동화`가 목적.
- PostgreSQL은 B-2 문서화 단계에서 전환 절차만 정의.

1. SQLite 운영 체크 스크립트
- 목표: DB 파일 경로/권한/백업 가능 여부 확인.
- 변경:
  - `scripts/check-db.ps1` 추가
  - `scripts/backup-db.ps1` 추가
- 검증:
  - 백업 파일 생성 성공
  - 복원 테스트(샘플 DB)

2. 마이그레이션 초안 문서
- 목표: PostgreSQL 전환 준비.
- 변경:
  - `docs/DB_MIGRATION_PLAN.md` 추가
- 포함:
  - 테이블 매핑
  - 이행 순서
  - 다운타임/롤백 전략
  - 전환 방식 권고:
    - 개발/스테이징: Docker Compose PostgreSQL
    - 운영: 관리형 PostgreSQL(RDS/Cloud SQL/Supabase 등) 우선 검토

### C. CI 파이프라인
1. GitHub Actions 기본 워크플로우
- 목표: Push/PR 시 자동 검증.
- 변경:
  - `.github/workflows/ci.yml` 추가
- 단계:
  - Python setup
  - `pip install -r backend/requirements.txt`
  - `pytest -q tests`
  - Node setup (frontend)
  - `npm ci` / `npm run lint` / `npm run build` (ASCII 경로 이슈 회피 전략 포함)

2. 배지/실패 가이드 문서
- 목표: 실패 시 대응 경로 명확화.
- 변경:
  - `README.md` CI 배지/트러블슈팅 섹션 추가

### D. 운영 관측성
1. 로깅 표준화
- 목표: 장애 원인 추적 가능.
- 변경:
  - API 요청/응답 핵심 로그 포맷 통일
  - 에러 유형 로깅(`validation/auth/provider/db`)
- 검증:
  - 대표 실패 케이스 로그 샘플 확인

2. 헬스체크 확장
- 목표: 서비스 상태 점검.
- 변경:
  - `/health`(앱/DB 상태) 추가
- 검증:
  - DB 끊김 시 degraded 응답 확인

## 실행 순서 (제안)
1. A-1, A-2
2. B-1
3. C-1, C-2
4. D-1, D-2
5. B-2

## 리스크/주의
1. CI에서 프론트 설치는 경로 이슈 재발 가능.
2. 로깅 변경 시 민감정보 출력 방지 필요.
3. DB 백업 스크립트는 경로/권한 환경 차이 점검 필요.

## 롤백 전략
1. 작업 단위별 커밋 분리(항목별 1커밋 원칙).
2. 문제 발생 시 해당 커밋만 `revert`.
3. CI 도입 실패 시 워크플로우 파일만 비활성화.

## 승인 섹션
- 진행 범위 선택:
  - [x] 전체(A+B+C+D) 진행
  - [ ] A만 진행
  - [ ] A+B만 진행
  - [ ] A+B+C만 진행
- 승인 문구(예시): "NEXT_DEPLOYMENT_EXECUTION_PLAN.md 기준으로 전체 진행 승인"
