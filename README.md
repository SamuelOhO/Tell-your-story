# Tell Your Story
[![CI](https://github.com/SamuelOhO/Tell-your-story/actions/workflows/ci.yml/badge.svg)](https://github.com/SamuelOhO/Tell-your-story/actions/workflows/ci.yml)

## 현재 상태
- 백엔드/프론트 기본 기능 구현 완료
- 세션 기반 인터뷰, STT/TTS, 자서전 초안 생성, `/health` 지원
- CI(GitHub Actions)에서 `pytest + frontend lint/build` 자동 검증
- 프론트 UI를 최근 버전으로 전면 개편
- 인터뷰 질문을 더 구체적으로 나오도록 서버 프롬프트 규칙 강화

## 로컬에서 내려받아 실행하기 (Windows/Powershell)

### 1. 저장소 클론
```powershell
git clone https://github.com/SamuelOhO/Tell-your-story.git
cd Tell-your-story
```

### 2. 백엔드 준비
```powershell
python -m venv venv
.\venv\Scripts\python -m pip install --upgrade pip
.\venv\Scripts\pip install -r backend\requirements.txt
Copy-Item backend\.env.example backend\.env
```

### 3. 프론트 준비
```powershell
cd frontend
npm install
Copy-Item .env.example .env
cd ..
```

### 4. 한 번에 실행 (권장)
```powershell
.\scripts\dev-all.ps1
```

### 5. 접속 주소
- 프론트: `http://localhost:5173`
- 백엔드: `http://localhost:8000`

## 경로 이슈가 있을 때 (한글 경로/클라우드 동기화 폴더)
프론트 설치/실행이 멈추거나 `vite` 인식 오류가 나면 ASCII 경로 우회 모드를 사용하세요.

```powershell
.\scripts\dev-all.ps1 -UseAsciiFrontend
```

이미 우회 경로에 설치가 끝났다면:
```powershell
.\scripts\dev-all.ps1 -UseAsciiFrontend -SkipFrontendInstall
```

## 개별 실행

### 백엔드
```powershell
.\venv\Scripts\Activate.ps1
uvicorn backend.main:app --reload
```

### 프론트
```powershell
cd frontend
npm run dev
```

## 환경 변수

### 백엔드 `backend/.env` 예시 (DEV)
```env
APP_ENV=dev
LOG_LEVEL=INFO
UPSTAGE_API_KEY=
OPENAI_API_KEY=
OPENAI_BASE_URL=
LLM_MODEL=solar-pro2
ALLOWED_ORIGINS=http://localhost:5173
MAX_HISTORY_TURNS=12
DB_PATH=backend/data/tell_your_story.db
SUMMARY_UPDATE_EVERY=6
```

### 프론트 `frontend/.env` 예시 (DEV)
```env
VITE_APP_ENV=development
VITE_API_BASE_URL=http://localhost:8000
```

## SQLite 운영 스크립트

### DB 상태 점검
```powershell
.\scripts\check-db.ps1
```

### DB 백업
```powershell
.\scripts\backup-db.ps1
```

### DB 복원
```powershell
.\scripts\backup-db.ps1 -RestoreFrom "backups\tell_your_story_YYYYMMDD_HHMMSS.db"
```

PostgreSQL 전환 계획 문서: `docs/DB_MIGRATION_PLAN.md`

## 로컬 검증 (CI와 유사)
```powershell
.\scripts\verify-local.ps1
```

백엔드만:
```powershell
.\scripts\verify-local.ps1 -SkipFrontend
```

## 문제 해결 빠른 체크
- `vite is not recognized`:
  - `frontend\node_modules` 손상 가능성이 큼
  - `.\scripts\dev-all.ps1 -UseAsciiFrontend`로 우선 실행
- `pytest`가 멈춤:
  - `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` 설정 후 실행
- 브라우저 접속:
  - `localhost` 기준으로 접속 권장 (`127.0.0.1` 대신)
