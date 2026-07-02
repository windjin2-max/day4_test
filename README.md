# 데이터 분석 자동화 프로그램

데이터 탐색, 전처리, EDA, 시각화, 인사이트 도출을 자동화하는 프로젝트입니다.

## 기술 스택
- FE: TypeScript, Vite, React
- BE: Python, FastAPI, uv
- DB: SQLite

## 프로젝트 구조
```text
day4_test/
├─ backend/
├─ frontend/
└─ docs/
```

## 실행 환경
- Node.js 18 이상
- uv
- Python 3.12 권장
- SQLite는 별도 설치 없이 사용 가능

## 1. 백엔드 실행

### 1-1. 의존성 설치
```bash
cd backend
uv sync
```

### 1-2. 서버 실행
```bash
cd backend
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 1-3. 확인 API
- `GET /api/health`
- `GET /api/db/health`
- `POST /api/explore`

## 2. 프론트엔드 실행

### 2-1. 의존성 설치
```bash
cd frontend
npm install
```

### 2-2. 개발 서버 실행
```bash
cd frontend
npm run dev
```

기본 접속 주소:
- `http://localhost:5173`

프론트는 백엔드의 다음 API를 호출합니다.
- `/api/health`
- `/api/db/health`
- `/api/explore`

Vite 프록시는 `frontend/vite.config.ts`에 설정되어 있습니다.

## 3. Colab 실행

데이터 탐색 셀 코드가 준비되어 있습니다.

- 노트북 파일: `docs/colab_data_exploration.ipynb`
- 파이썬 스크립트: `docs/colab_data_exploration.py`

### 실행 순서
1. Google Colab을 연다.
2. `docs/colab_data_exploration.ipynb`를 업로드한다.
3. 첫 번째 설치 셀을 실행한다.
4. `csv`, `xls`, `xlsx` 파일을 업로드한다.
5. 나머지 셀을 순서대로 실행한다.

### 생성 결과
- 데이터 기본 개요
- 컬럼 프로파일
- 결측치/중복/상수형 컬럼 점검
- JSON 리포트
- Markdown 리포트

## 4. 데이터 탐색 결과 다운로드

프론트의 데이터 탐색 페이지에서 분석이 끝나면 다음 파일을 받을 수 있습니다.
- Markdown 리포트
- JSON 요약

## 5. 자주 발생하는 문제

### 5-1. 백엔드가 실행되지 않음
- `backend` 폴더에서 `uv sync`를 먼저 실행했는지 확인한다.
- `uv run uvicorn app.main:app ...` 명령을 `backend` 디렉터리에서 실행한다.

### 5-2. 프론트에서 API 호출이 실패함
- 백엔드 서버가 `http://localhost:8000`에서 실행 중인지 확인한다.
- `frontend/vite.config.ts`의 proxy 설정을 확인한다.

### 5-3. Excel 파일을 읽지 못함
- `.xlsx`는 `openpyxl`, `.xls`는 `xlrd`를 사용한다.
- Colab에서는 첫 설치 셀을 먼저 실행해야 한다.

### 5-4. CSV 인코딩 오류
- `utf-8-sig`, `utf-8`, `cp949`, `euc-kr` 순서로 읽기를 시도한다.
- 파일 원본 인코딩이 다르면 저장 형식을 바꿔서 다시 시도한다.

## 6. 개발 참고
- SQLite DB 파일은 `backend/data/app.db`에 생성된다.
- 프론트와 백엔드는 분리 실행하는 구조다.
- 문서화 파일은 `docs/` 폴더에 있다.

