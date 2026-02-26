# Tell Your Story 상세 구현 계획서 (2026-02-26)

## 문서 목적
- `CODE_REVIEW_AND_ROADMAP.md`를 실제 개발 작업 단위로 변환한 실행 계획서다.
- 목표는 "안정화 -> 품질 고도화 -> 제품화"를 실제 코드 변경/검증 기준으로 관리하는 것이다.

## 현재 백엔드 동작 점검 결과
- 점검 일시: 2026-02-26
- 점검 방식: `FastAPI TestClient` 스모크 테스트
- 결과:
1. `GET /` -> `200`, `{"message":"Tell Your Story API"}`
2. `POST /interview/start` -> `200`, 첫 질문 반환
3. `POST /interview/chat` 정상 payload -> `200`
4. `POST /interview/chat` 비정상 payload -> `422` (요청 검증 정상 동작)
5. LLM 실제 호출은 현재 API 키 인증 실패 시 fallback 응답으로 처리됨 (`AuthenticationError` 로그)

해석:
- API 라우팅/유효성 검증/기본 fallback 동작은 정상.
- 운영 준비를 위해 "모델 설정 분리 + 키/공급자 검증 + 테스트 자동화"가 다음 핵심 작업.

## 구현 원칙
1. 설정 하드코딩 제거: 모델명/엔드포인트/CORS/히스토리 턴수는 환경변수로 이동.
2. 회귀 방지 우선: 기능 추가 전 테스트 기반 최소 안전망 확보.
3. 단계별 납품: 각 Phase마다 "실행 가능 + 검증 가능" 상태로 마감.
4. 의사결정 분리: STT/TTS는 연결할지 제거할지 초기에 명확히 결정.

## Phase 1: 안정화 (권장 1주)

### 목표
- 로컬/CI에서 동일하게 실행되고, 핵심 API가 자동 검증되는 상태.

### 작업 항목
1. 설정 모듈 도입 (`backend/config.py`)
- 작업:
1. `pydantic-settings` 또는 환경 변수 헬퍼 도입
2. 아래 값을 설정 객체로 통합
  - `UPSTAGE_API_KEY` / `OPENAI_API_KEY`
  - `OPENAI_BASE_URL`
  - `LLM_MODEL` (현재 `solar-pro2`)
  - `ALLOWED_ORIGINS`
  - `MAX_HISTORY_TURNS`
- 변경 대상:
  - `backend/main.py`
  - `backend/services/llm_service.py`
  - `backend/services/stt_service.py`
  - `backend/services/tts_service.py`

2. 백엔드 테스트 도입 (`pytest`)
- 작업:
1. `tests/test_api_health.py`: `/` 및 `/interview/start`
2. `tests/test_interview_chat.py`: 정상/비정상 payload 검증
3. `tests/test_llm_fallback.py`: API 키 미설정 fallback 검증
- 완료 기준:
  - `pytest` 통과
  - 최소 5개 테스트 케이스 통과

3. 프론트 설치 경로 이슈 대응 가이드 강화
- 작업:
1. README 실행 파트에 "권장 경로 전략" 명확화
2. 가능하면 `scripts/dev-frontend.ps1` 추가해 ASCII 경로 복제 실행 자동화
- 완료 기준:
  - 신규 개발자가 문서만 보고 dev 서버 실행 가능

4. 의존성 슬림화
- 작업:
1. 사용하지 않는 패키지 정리 (`langchain`, `langchain-openai`, `chromadb` 검토)
2. 실제 사용 기준으로 `backend/requirements.txt` 최소화
- 완료 기준:
  - `pip install -r backend/requirements.txt` 성공
  - 백엔드 스모크 테스트 성공

### 진행 현황
- [x] `backend/config.py` 도입
- [x] `main.py`, `llm_service.py`, `stt_service.py`, `tts_service.py` 설정 이관
- [x] `LLM_MODEL`, `ALLOWED_ORIGINS`, `MAX_HISTORY_TURNS` 환경 변수 항목 추가 (`backend/.env.example`, `README.md`)
- [x] 백엔드 테스트 추가 (`tests/test_api_health.py`, `tests/test_interview_chat.py`, `tests/test_llm_fallback.py`)
- [x] `requirements.txt` 슬림화 최종 확정 (`langchain*`, `chromadb` 제거)
- [x] 프론트 설치 경로 이슈 대응 스크립트(`scripts/dev-frontend.ps1`) 작성

### 특이사항 및 참고사항
- 2026-02-26: API 스모크 테스트 기준 백엔드 라우팅은 정상 동작 (`/`, `/interview/start`, `/interview/chat`).
- 2026-02-26: 실제 LLM 호출은 키 상태에 따라 `AuthenticationError`가 발생할 수 있으며, 현재 fallback 응답으로 안전 처리됨.
- 2026-02-26: `user_text`/`conversation_history.text`는 공백만 입력 시 422로 차단되도록 검증 강화됨.
- 2026-02-26: 대화 히스토리는 `MAX_HISTORY_TURNS` 기준으로 최근 턴만 LLM에 전달하도록 제한 로직 추가됨.
- 2026-02-26: 테스트 결과 `pytest -q tests` 기준 11개 케이스 통과.
- 2026-02-26: 프론트 경로 이슈 우회용 `scripts/dev-frontend.ps1` 추가.

## Phase 2: 인터뷰 품질 고도화 (권장 1~2주)

### 목표
- 긴 대화에서도 응답 품질과 지연/비용을 제어.

### 작업 항목
1. 히스토리 윈도우 전략
- 작업:
1. 최근 `N`턴만 LLM에 전달 (`MAX_HISTORY_TURNS`)
2. 프론트/백엔드 동시 제한 적용
- 완료 기준:
  - 30턴 이상 대화 시에도 응답시간 급증 없음

2. 세션 요약 메모리
- 작업:
1. 일정 턴마다 핵심 요약 생성
2. 다음 질문 생성 시 요약 + 최근 N턴 조합
- 완료 기준:
  - 주제 일관성 향상(수동 QA 기준)

3. 에러 UX 개선
- 작업:
1. 에러 타입별 사용자 메시지 분리(네트워크/검증/LLM 실패)
2. 재시도 시 중복 요청 방지 토큰 고려
- 완료 기준:
  - 같은 실패 상황에서 사용자 행동 경로가 명확

### 진행 현황
- [x] 히스토리 윈도우 전략 고도화(최근 턴 제한 + 세션 요약 컨텍스트 결합)
- [x] 세션 요약 메모리 도입(`SUMMARY_UPDATE_EVERY` 주기 갱신)
- [x] 에러 UX 타입 분리(네트워크/검증/인증/서버/요청)

### 특이사항 및 참고사항
- 2026-02-26: `llm_service`에서 대화 요약을 프롬프트 컨텍스트로 사용하도록 반영.
- 2026-02-26: 세션 메시지 수 기준으로 요약 자동 갱신 로직 적용.
- 2026-02-26: 프론트에서 상태코드 기반 오류 타입 메시지 분기 처리.
- 2026-02-26: 프론트에 Enter 전송/재시도/오류타입 안내와 함께 음성 전사 흐름을 결합.

## Phase 3: 제품화 (권장 2주+)

### 목표
- 실제 사용 가능한 인터뷰 서비스 형태로 확장.

### 작업 항목
1. STT/TTS 의사결정 및 구현
- 결정 A: 유지
  - `/interview/stt`, `/interview/tts` 라우트 추가
  - 프론트 `Microphone` 연동
- 결정 B: 보류/제거
  - 관련 서비스 파일 제거 및 문서 정리

2. 데이터 저장
- 작업:
1. 인터뷰 세션 테이블 설계(예: SQLite/PostgreSQL)
2. 대화 로그 저장/조회 API 추가

3. 결과물 생성 파이프라인
- 작업:
1. 인터뷰 -> 챕터 초안 생성
2. 최종 자서전 편집 흐름 기획

### 진행 현황
- [x] STT/TTS API 라우트 구현 (`/interview/stt`, `/interview/tts`)
- [x] 인터뷰 세션 저장소 설계 및 구현(SQLite 기반 `session_store`)
- [x] 결과물 생성 파이프라인 구현 (`/interview/draft`, `/interview/draft/latest/{session_id}`)

### 특이사항 및 참고사항
- 2026-02-26: 세션/메시지/초안 저장을 SQLite로 구현, 앱 startup 시 DB 초기화.
- 2026-02-26: 프론트에 마이크 녹음 -> STT 입력 연동, 질문 TTS 재생, 초안 생성 UI 반영.
- 2026-02-26: `C:\tmp` 검증 경로 기준 `npm run lint` / `npm run build` 통과.

## 작업 우선순위 백로그
1. `backend/config.py` 도입 및 하드코딩 제거
2. `pytest` 테스트 5개 이상 추가
3. 히스토리 N턴 제한
4. `requirements.txt` 정리
5. STT/TTS 연결 여부 확정
6. 세션 저장 설계

## 브랜치/PR 전략
1. `feature/config-and-tests`
2. `feature/history-window`
3. `feature/stt-tts-decision`
4. `feature/session-storage`

규칙:
1. PR당 책임 1개
2. PR 템플릿에 "변경 범위 / 테스트 결과 / 롤백 방법" 필수
3. `main` 병합 전 백엔드 스모크 + 프론트 lint/build 결과 첨부

## 완료 기준 (전체)
1. 백엔드 테스트 자동화 구축 (`pytest`) 및 통과
2. 프론트 lint/build 안정화
3. 설정 하드코딩 제거
4. 대화 품질 개선(히스토리 전략 반영)
5. README 기준 온보딩 30분 이내

## 구현 완료 후 다음 고도화 후보
1. SQLite -> PostgreSQL 마이그레이션 및 Alembic 스키마 관리
2. 세션 요약 품질 평가 지표 도입(질문 일관성/주제 유지율)
3. 초안 생성 결과 편집 UI(단락별 수정/저장) 추가
