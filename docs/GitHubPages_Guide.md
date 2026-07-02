# GitHub Desktop으로 GitHub Pages 배포하기

이 문서는 `frontend` 앱을 GitHub Desktop과 GitHub Actions를 이용해 GitHub Pages에 배포하는 절차입니다.

## 1. 현재 프로젝트 상태 확인

현재 프로젝트는 GitHub Pages 배포가 가능한 구조입니다.

- 프론트엔드 위치: `frontend/`
- 빌드 명령어: `npm run build`
- 빌드 결과물: `frontend/dist/`
- 배포 워크플로: `.github/workflows/deploy-frontend-pages.yml`
- GitHub Pages 경로 대응 설정: `frontend/vite.config.ts`

주의할 점:

- GitHub Pages는 정적 사이트만 배포합니다.
- FastAPI 백엔드는 GitHub Pages에 같이 배포되지 않습니다.
- 배포된 페이지에서 실제 파일 분석 API를 사용하려면 별도 백엔드 서버 URL이 필요합니다.

## 2. GitHub Desktop에서 저장소 열기

1. GitHub Desktop을 실행합니다.
2. 상단 메뉴에서 `File > Add local repository...`를 클릭합니다.
3. 프로젝트 폴더를 선택합니다.
   - 예: `C:\Users\admin\Desktop\day4_test`
4. `Add repository`를 클릭합니다.

이미 GitHub Desktop에 저장소가 열려 있다면 이 단계는 건너뜁니다.

## 3. 변경 파일 확인

GitHub Desktop 왼쪽 `Changes` 탭에서 변경된 파일을 확인합니다.

이번 GitHub Pages 배포에 필요한 핵심 파일은 다음입니다.

- `.github/workflows/deploy-frontend-pages.yml`
- `frontend/vite.config.ts`

추가로 현재까지 개발한 프론트엔드/백엔드 변경 파일도 함께 표시될 수 있습니다.

## 4. Commit 만들기

1. GitHub Desktop 왼쪽 아래의 `Summary` 입력란에 커밋 메시지를 작성합니다.
   - 예: `Add GitHub Pages deployment workflow`
2. 필요하면 `Description`에 설명을 작성합니다.
   - 예: `Deploy frontend with GitHub Actions from frontend/dist`
3. `Commit to main` 버튼을 클릭합니다.

브랜치 이름이 `main`이 아니라면 버튼에는 현재 브랜치명이 표시됩니다.

## 5. GitHub에 Push하기

1. GitHub Desktop 상단의 `Push origin` 버튼을 클릭합니다.
2. Push가 끝날 때까지 기다립니다.
3. GitHub 웹사이트에서 해당 저장소 페이지를 엽니다.

처음 GitHub에 올리는 저장소라면:

1. GitHub Desktop 상단의 `Publish repository`를 클릭합니다.
2. 저장소 이름을 확인합니다.
3. 공개 저장소로 배포하려면 `Keep this code private` 체크를 해제합니다.
4. `Publish Repository`를 클릭합니다.

## 6. GitHub Pages 설정

1. GitHub 웹사이트에서 저장소로 이동합니다.
2. 상단 메뉴에서 `Settings`를 클릭합니다.
3. 왼쪽 메뉴에서 `Pages`를 클릭합니다.
4. `Build and deployment` 영역을 찾습니다.
5. `Source`를 `GitHub Actions`로 설정합니다.

이 프로젝트는 GitHub Actions 방식으로 배포하도록 구성되어 있습니다.

## 7. GitHub Actions 실행 확인

1. GitHub 저장소 상단 메뉴에서 `Actions`를 클릭합니다.
2. `Deploy Frontend to GitHub Pages` 워크플로를 선택합니다.
3. 실행 상태가 초록색 체크로 완료되는지 확인합니다.

자동 실행 조건:

- `main` 브랜치에 push하면 자동 실행됩니다.
- 수동 실행도 가능합니다.

수동 실행 방법:

1. `Actions` 탭으로 이동합니다.
2. `Deploy Frontend to GitHub Pages`를 클릭합니다.
3. `Run workflow` 버튼을 클릭합니다.
4. 브랜치를 선택하고 실행합니다.

## 8. 배포 URL 확인

Actions가 성공하면 `Settings > Pages`에서 배포 URL을 확인할 수 있습니다.

일반적인 URL 형식:

```text
https://사용자명.github.io/저장소명/
```

예:

```text
https://my-account.github.io/day4_test/
```

## 9. 백엔드 API 연결이 필요한 경우

GitHub Pages는 프론트엔드만 호스팅합니다.

현재 앱의 데이터 업로드/분석 기능은 FastAPI 백엔드가 필요합니다.
배포된 GitHub Pages에서 실제 분석 기능까지 사용하려면 백엔드를 별도로 배포한 뒤 URL을 GitHub Actions 변수에 등록해야 합니다.

설정 방법:

1. GitHub 저장소에서 `Settings`로 이동합니다.
2. 왼쪽 메뉴에서 `Secrets and variables > Actions`를 클릭합니다.
3. `Variables` 탭을 클릭합니다.
4. `New repository variable`을 클릭합니다.
5. 아래 값을 추가합니다.

```text
Name: VITE_API_BASE_URL
Value: https://배포한-백엔드-주소
```

예:

```text
Name: VITE_API_BASE_URL
Value: https://my-api.example.com
```

이 값을 등록한 뒤 다시 Actions를 실행하면 프론트엔드가 해당 백엔드 주소를 사용합니다.

## 10. 자주 발생하는 문제

### Actions가 실행되지 않는 경우

- `.github/workflows/deploy-frontend-pages.yml` 파일이 push되었는지 확인합니다.
- push한 브랜치가 `main`인지 확인합니다.
- 기본 브랜치가 `master`라면 workflow 파일의 `branches` 값을 수정해야 합니다.

```yaml
on:
  push:
    branches:
      - master
```

### Pages 화면이 빈 화면으로 보이는 경우

- `frontend/vite.config.ts`의 `base` 설정이 필요합니다.
- 현재 workflow는 `VITE_BASE_PATH`를 `/저장소명/`으로 자동 설정합니다.
- 저장소 이름이 바뀌면 다시 Actions를 실행합니다.

### 업로드/분석 API가 작동하지 않는 경우

- GitHub Pages에는 FastAPI 백엔드가 없습니다.
- 별도 백엔드 배포 주소를 `VITE_API_BASE_URL` 변수로 등록해야 합니다.
- 백엔드에서 CORS 설정이 GitHub Pages URL을 허용해야 합니다.

### `npm ci` 단계에서 실패하는 경우

- `frontend/package-lock.json`이 저장소에 포함되어 있는지 확인합니다.
- 로컬에서 다음 명령어가 성공하는지 확인합니다.

```bash
cd frontend
npm ci
npm run build
```

## 11. 최종 체크리스트

- GitHub Desktop에서 변경 파일을 commit 했는가
- `Push origin`을 완료했는가
- GitHub Pages Source를 `GitHub Actions`로 설정했는가
- Actions 실행이 성공했는가
- Pages URL에서 화면이 열리는가
- 분석 API까지 사용할 경우 `VITE_API_BASE_URL`을 등록했는가
