# Tell Your Story

## 🚀 빠른 실행 가이드 (Quick Start)

가장 자주 사용하는 실행 명령어입니다. 터미널 2개를 열어서 진행하세요.

### 1. 터미널 A: 백엔드(BE) 실행
프로젝트 최상위 폴더(루트)에서 실행합니다.
```powershell
# 1. 가상환경 활성화
.\venv\Scripts\Activate.ps1

# 2. 백엔드 서버 실행
uvicorn backend.main:app --reload
```
*서버 주소: http://localhost:8000*

### 2. 터미널 B: 프론트엔드(FE) 실행
```powershell
# 1. 프론트엔드 폴더로 이동
cd frontend

# 2. 개발 서버 실행
npm run dev
```
*접속 주소: http://localhost:5173*

---

## 🛠️ 초기 설정 (최초 1회만 진행)

### 1. 백엔드 설정 (Backend)
```powershell
# 1. 가상환경 생성
python -m venv venv

# 2. 패키지 설치
.\venv\Scripts\python -m pip install --upgrade pip
.\venv\Scripts\pip install -r backend\requirements.txt

# 3. 환경 변수 설정 (.env)
Copy-Item backend\.env.example backend\.env
# backend\.env 파일에서 API 키를 설정하세요.
# - UPSTAGE_API_KEY: LLM 인터뷰 생성용
# - OPENAI_API_KEY: STT/TTS 사용 시
# - OPENAI_BASE_URL: (선택) OpenAI 호환 API 사용 시
```

### 2. 프론트엔드 설정 (Frontend)
```powershell
cd frontend
npm install
# (선택) API 주소 커스텀 시
Copy-Item .env.example .env
# VITE_API_BASE_URL=http://localhost:8000
# 참고: 클라우드 동기화/한글 경로에서 npm install 이 오래 멈추면, 로컬 ASCII 경로(예: C:\tmp)에 복사 후 설치하세요.
```
