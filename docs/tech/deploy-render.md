# 공개 배포 가이드: Render (Docker)

## 0. 문서 정보
- 작성일: 2026-10-21
- 상태: 로컬 Docker 검증 완료 (2026-10-21, 6.1). Render, 카카오의 현재 정책과 화면 메뉴 이름은 외부 확인 전 (10장 `E-` 항목)
- 근거 문서: `docs/tech/tech_stack.md`, `docs/tech/datasource.md`, `docs/tech/api_spec.md`, `docs/masterplan.md`
- 쓰임: 이 앱을 Docker 이미지로 만들어 Render 무료 플랜에 올리고, 주소를 아는 사람 누구나 접속하게 하는 절차
- 전제
  | 항목 | 값 |
  |---|---|
  | 배포 기준 | Docker 이미지. 저장소 root의 `Dockerfile`, `.dockerignore` (3장) |
  | 배포처 | Render 웹 서비스 (Web Service), Language Docker |
  | 빌드 방식 | Render가 GitHub 저장소의 `Dockerfile`로 이미지를 만듦. 별도 이미지 저장소(Docker Hub 등) 없음 |
  | 설정 관리 | Render 대시보드에서 직접 입력. `render.yaml` 쓰지 않음 |
  | 요금 | 무료 플랜 (Free instance) |
  | 공개 범위 | 주소를 아는 사람 누구나 |
- 같은 `Dockerfile`로 홈랩 NAS에서 구동하는 방법: `docs/tech/deploy-homelab.md`

## 1. 배포 구조와 원리

### 1.1 구조
| 순서 | 위치 | 동작 |
|---|---|---|
| 1 | GitHub 비공개 저장소 `kevin110419/daily-modal-app-v2` | `main` 브랜치에 push |
| 2 | Render | 저장소를 내려받아 `Dockerfile` 순서대로 이미지 빌드 |
| 3 | Render | 이미지로 컨테이너 실행. 인증키와 포트 번호는 Render 환경 변수로 컨테이너에 전달 |
| 4 | Render | `https://{서비스 이름}.onrender.com` 주소로 HTTPS 접속을 받아 컨테이너에 전달 |
| 5 | 휴대폰 브라우저 | 위 주소로 화면과 `/api/...`를 함께 받음 |

- 서버 하나가 화면과 API를 같은 주소로 제공하는 구조(`tech_stack.md` 2.1)를 그대로 올리므로 CORS 설정이 필요 없음
- 데이터베이스가 없으므로 따로 만들 저장소가 없음. 사용자 정보는 브라우저 localStorage에만 있음

### 1.2 원리
| 개념 | 설명 | 이 앱에서 |
|---|---|---|
| 이미지 | 프로그램 실행에 필요한 운영체제 일부, Python, 라이브러리, 코드를 한 묶음으로 만든 파일. `Dockerfile`이 만드는 순서 | Debian slim + Python 3.14.8 + `requirements.txt` 라이브러리 + `backend/`, `frontend/` 실행 파일 |
| 컨테이너 | 이미지를 실행한 것. 서버 운영체제와 분리된 공간에서 돌아감 | Render에서 1개 실행 |
| 빌드 캐시 | `Dockerfile`의 각 줄 결과를 저장해 두고, 입력이 그대로면 다시 쓰는 방식 | `requirements.txt`가 그대로면 라이브러리 설치 단계를 건너뜀 |
| PaaS | 서버 컴퓨터 관리(운영체제, 보안 패치, HTTPS 인증서)를 서비스가 맡고, 사용자는 실행할 것만 지정하는 방식 | Render가 Linux 서버, HTTPS를 맡고, 이 앱은 이미지만 지정 |
| 환경 변수 | 프로그램 밖에서 넣어 주는 이름과 값의 쌍. 코드와 이미지에 비밀 값을 넣지 않기 위해 사용 | `config.py`가 `os.environ.get('KAKAO_REST_API')`로 읽음 |
| 포트 | 한 컴퓨터 안에서 프로그램을 구분하는 번호 | Render가 정한 번호를 환경 변수 `PORT`로 알려 줌 (3.1) |
| `0.0.0.0` | "이 컴퓨터의 모든 네트워크 주소에서 접속을 받음"이라는 뜻의 주소 | 컨테이너 밖(Render의 중계 서버)에서 오는 접속을 받기 위해 사용. 로컬 기본값 `127.0.0.1`은 컨테이너 자기 자신에서만 접속 가능 |

- `config.py`의 `load_dotenv(BACKEND_DIR / '.env')`는 파일이 없으면 아무것도 하지 않음. `.env`는 git과 이미지에서 모두 제외되므로(3.2) Render에서는 환경 변수만 쓰임
- Python 버전은 `Dockerfile`의 기준 이미지 이름(`python:3.14.8-slim`)으로 정해짐. Render의 Python 설정(`PYTHON_VERSION`)은 쓰지 않음

## 2. 무료 플랜의 동작
| 항목 | 내용 | 이 앱에 주는 영향 |
|---|---|---|
| 잠들기 | 15분 동안 접속이 없으면 서버가 멈춤. 다음 접속 때 다시 켜지는 데 1분 안팎 (E-1) | 아침에 처음 앱을 열면 첫 화면, 첫 추천이 늦게 나옴. 화면의 `fetch`에는 시간 제한이 없으므로 실패하지 않고 기다림 |
| 메모리 캐시 초기화 | 잠들거나 다시 배포하면 컨테이너가 새로 켜져 메모리가 비워짐 | `tech_stack.md` 3.5의 24시간 캐시(대중교통, 도보, 자전거 경로, 노선 정보)가 사라짐. 깨어난 뒤 첫 추천은 외부 호출이 모두 다시 일어나고, 서울 버스 노선 전체(DS-19)도 다시 받음 |
| 월 사용 시간 | 계정당 무료 인스턴스 시간 750시간 (E-1) | 서비스 1개면 한 달 내내 켜져 있어도 넘지 않음 |
| 성능 | 메모리 512MB, CPU 일부 (E-1) | 로컬 컨테이너에서 DS-19 전체 목록을 받은 뒤 메모리 약 95MiB (6.1). 여유 있음 |
| 서버 수 | 1개 | 캐시가 프로세스 메모리에 있으므로 Uvicorn worker는 1개 유지. `Dockerfile` 실행 명령에 `--workers`를 붙이지 않음 |

- 잠들기를 줄이는 방법
  | 방법 | 내용 | 비고 |
  |---|---|---|
  | 외부 주기 호출 | 외부 모니터링 서비스가 14분마다 `/api/config`를 호출해 잠들지 않게 함 | 외부 API를 부르지 않는 주소라 호출량에 영향 없음. Render 무료 플랜 약관상 허용 여부 확인 필요 (E-2) |
  | 유료 인스턴스 | 대시보드에서 인스턴스 종류 변경 | 잠들기 없음 |

## 3. 이미지 구성

### 3.1 Dockerfile
- 위치: 저장소 root `Dockerfile`
  | 줄 | 뜻 |
  |---|---|
  | `FROM python:3.14.8-slim` | 시작점이 되는 이미지. Python 3.14.8이 설치된 작은 Linux(Debian slim). `tech_stack.md` 1장의 개발 환경 버전과 같음 |
  | `ENV PYTHONDONTWRITEBYTECODE=1`, `PYTHONUNBUFFERED=1` | `.pyc` 파일을 만들지 않고, 로그를 모아 두지 않고 바로 출력. Render Logs에 기록이 늦지 않게 나옴 |
  | `WORKDIR /srv` | 이후 명령의 기준 폴더. 컨테이너 안에서 `/srv/backend`, `/srv/frontend`가 되어 `config.py`의 `BACKEND_DIR`, `FRONTEND_DIR` 계산(`backend/`의 상위 폴더에 `frontend/`)이 그대로 맞음 |
  | `COPY backend/requirements.txt` → `RUN pip install` | 라이브러리를 코드보다 먼저 설치. 코드만 바뀐 배포에서는 이 단계를 빌드 캐시로 건너뜀 |
  | `COPY backend/app`, `backend/data`, `frontend/...` | 서버 실행에 필요한 파일만 복사. `.env`, 테스트, 문서는 넣지 않음 |
  | `RUN useradd`, `USER appuser` | 관리자(root) 권한이 없는 사용자로 서버 실행. 앱은 파일을 읽기만 하므로 쓰기 권한이 필요 없음 |
  | `EXPOSE 8000` | 이 이미지가 접속을 받는 기본 포트를 적어 두는 표시. 실제 포트는 아래 `CMD`가 정함 |
  | `CMD [...]` | 컨테이너를 켤 때 실행할 명령 (3.3) |

### 3.2 .dockerignore
- 위치: 저장소 root `.dockerignore`
- 이미지를 만들 때 Docker에 보내지 않을 파일 목록: `.git`, `.claude`, 모든 `.env` 파일, `.venv`, 캐시 폴더, `node_modules`, `docs`, `tools`
- `Dockerfile`이 필요한 파일만 복사하지만, 이 파일이 있으면 인증키 파일과 큰 폴더가 빌드 과정에 아예 전달되지 않음

### 3.3 실행 명령 풀이
```dockerfile
CMD ["sh", "-c", "exec uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port ${PORT:-8000}"]
```
| 부분 | 뜻 |
|---|---|
| `["sh", "-c", "..."]` | 셸(`sh`)이 문자열을 해석한 뒤 실행. 대괄호 안에 명령을 바로 적는 방식(exec form)은 셸을 거치지 않아 `$PORT` 같은 변수가 숫자로 바뀌지 않으므로 셸을 거침 |
| `exec` | 셸이 자기 자리를 uvicorn에 넘김. uvicorn이 컨테이너의 첫 프로세스(PID 1)가 되어, Render가 서버를 끌 때 보내는 종료 신호(SIGTERM)를 직접 받고 정상 종료 |
| `uvicorn app.main:app` | `app/main.py` 파일 안의 `app` 변수(FastAPI 객체)를 실행 |
| `--app-dir backend` | `app` 패키지를 `backend/` 폴더에서 찾음. `.claude/launch.json`의 로컬 실행과 같은 방식 |
| `--host 0.0.0.0` | 컨테이너 밖에서 오는 접속을 받음 |
| `--port ${PORT:-8000}` | 환경 변수 `PORT`가 있으면 그 값, 없으면 8000. Render에서는 Render가 넣어 준 값, 홈랩 NAS에서는 8000 |

- 로컬 개발 명령의 `--reload`(파일이 바뀌면 자동 재시작)는 개발용이므로 넣지 않음

### 3.4 저장소에 있어야 하는 파일
| 파일 | 이유 |
|---|---|
| `Dockerfile`, `.dockerignore` | Render가 이미지를 만드는 기준 |
| `frontend/css/tokens.css` | 이미지 빌드 중 `build_tokens.py`를 실행하지 않음. 생성된 파일이 저장소에 있어야 화면 색, 글자 크기가 적용됨 |
| `frontend/fonts/*.woff2` | Pretendard 글꼴 |
| `backend/data/holidays/*.csv` | 평일 공휴일 판단 (`datasource.md` 7.1) |
| `backend/requirements.txt` | 이미지 빌드 중 라이브러리 설치에 쓰임 |

- `backend/.env`가 저장소에 없는지 확인 (`.gitignore`에서 제외 중)

## 4. 배포 전 준비

### 4.1 로컬 검사
- 모두 통과한 상태로 배포 (`tech_stack.md` 8장)
  | 대상 | 명령 | 실행 위치 |
  |---|---|---|
  | 백엔드 테스트 | `.venv\Scripts\python -m pytest` | `backend/` |
  | 프론트엔드 로직 테스트 | `npm test` | `frontend/` |
  | 코드 검사 | `.venv\Scripts\python -m ruff check .`, `.venv\Scripts\python -m ruff format --check .` | `backend/` |
  | 토큰 일치 | `.venv\Scripts\python ..\tools\build_tokens.py --check` | `backend/` |

### 4.2 로컬 Docker 검사
- Docker Desktop을 켠 뒤 저장소 root에서 실행
  | 순서 | 명령 | 확인 |
  |---|---|---|
  | 1 | `docker build -t daily-modal-app:{버전} .` | 빌드 성공. `{버전}`은 커밋 이름(예: `0.3.1`)과 맞춤 |
  | 2 | `docker run -d --name daily-modal-test -p 8002:10000 -e PORT=10000 -e KAKAO_REST_API -e KAKAO_JS_API -e DATA_SEOUL_GOKR_GENERIC_API -e DATA_GOKR_GENERIC_API -e DATA_SEOUL_GOKR_SUBWAY_API daily-modal-app:{버전}` | Render처럼 `PORT`를 8000이 아닌 값으로 줘도 `http://localhost:8002`에서 화면이 열림 |
  | 3 | `docker logs daily-modal-test` | `Uvicorn running on http://0.0.0.0:10000`, 요청 기록에 주소, 좌표, 검색어 없음 |
  | 4 | 추천 몇 번 실행 후 `docker stats --no-stream daily-modal-test` | 메모리가 512MB보다 충분히 낮음 |
  | 5 | `docker stop daily-modal-test`, `docker rm daily-modal-test` | 로그 끝에 `Application shutdown complete`. 종료 신호를 uvicorn이 받았다는 뜻 |
- 2번 명령의 원리
  | 부분 | 뜻 |
  |---|---|
  | `-p 8002:10000` | PC의 8002번으로 들어온 접속을 컨테이너 안 10000번으로 넘김. 로컬 개발 서버(8000)와 겹치지 않게 8002 사용 |
  | `-e PORT=10000` | 컨테이너에 환경 변수 `PORT` 값을 넣음 |
  | `-e KAKAO_REST_API` (값 없이 이름만) | 명령을 실행하는 셸에 있는 같은 이름의 값을 그대로 넘김. 키 값이 명령 기록에 남지 않음 |
- 인증키를 셸에 넣는 방법: `backend/.env`의 값은 따옴표로 감싸여 있음. `docker run --env-file backend/.env`는 따옴표를 값의 일부로 넘기므로 쓰지 않음. 셸에 넣을 때는 python-dotenv로 읽어 따옴표를 뺀 값을 씀

## 5. Render 웹 서비스 만들기

### 5.1 계정
- Render 가입: GitHub 계정으로 가입하면 저장소 연결이 쉬움
- 비공개 저장소이므로 GitHub 연결 화면에서 Render에 `daily-modal-app-v2` 저장소 접근만 허용 ("Only select repositories")

### 5.2 기본 설정
- 대시보드에서 New → Web Service → 저장소 선택 후 아래 값 입력 (항목 이름은 E-8)
  | 항목 | 값 | 이유 |
  |---|---|---|
  | Name | 예: `commute-route` | 주소 `https://{Name}.onrender.com`에 쓰임. 서비스 이름 미정(Q-5)이므로 임시 이름. 이미 쓰는 이름이면 뒤에 문자가 붙음 |
  | Language | Docker | 저장소의 `Dockerfile`로 이미지를 만들어 실행 |
  | Branch | `main` | |
  | Region | Singapore | 한국에서 가장 가까운 지역. 만든 뒤 바꿀 수 없음 (E-4) |
  | Root Directory | 비워 둠 | 저장소 전체 기준 |
  | Dockerfile Path | `./Dockerfile` | 저장소 root의 `Dockerfile` |
  | Docker Build Context Directory | `.` | `COPY backend/...`, `COPY frontend/...`가 저장소 root 기준이므로 root를 빌드 재료 폴더로 지정 |
  | Docker Command | 비워 둠 | `Dockerfile`의 `CMD`를 그대로 씀. 값을 넣으면 `CMD` 대신 실행됨 |
  | Instance Type | Free | |

### 5.3 환경 변수
- 같은 화면의 Environment Variables(또는 만든 뒤 Environment 메뉴)에 입력
  | 이름 | 값 |
  |---|---|
  | `KAKAO_REST_API` | `backend/.env`의 값 |
  | `KAKAO_JS_API` | `backend/.env`의 값 |
  | `DATA_SEOUL_GOKR_GENERIC_API` | `backend/.env`의 값 |
  | `DATA_GOKR_GENERIC_API` | `backend/.env`의 값 |
  | `DATA_SEOUL_GOKR_SUBWAY_API` | `backend/.env`의 값 |
- `backend/.env`의 값을 감싼 따옴표는 빼고 안의 값만 입력. Render는 입력한 글자를 그대로 넘기므로 따옴표가 들어가면 모든 외부 호출이 인증 실패로 끝남
- `PORT`는 입력하지 않음. Render가 직접 넣어 줌 (E-3)
- 값은 Render 화면에만 입력하고 저장소, 문서, 채팅에 적지 않음
- 값을 바꾸면 Render가 컨테이너를 다시 켬

### 5.4 추가 설정
| 항목 | 값 | 이유 |
|---|---|---|
| Health Check Path (Advanced) | `/api/config` | Render가 이 주소의 응답으로 서버가 정상인지 판단. 외부 API를 부르지 않는 가벼운 주소 (E-7) |
| Auto-Deploy | On Commit (기본값) | `main`에 push하면 자동으로 이미지를 다시 만들고 배포 |

## 6. 확인

### 6.1 로컬 Docker 검증 결과 (2026-10-21, 커밋 `0.3.1` 위 작업 트리)
| 항목 | 결과 |
|---|---|
| 기준 이미지 | `python:3.14.8-slim` 받아짐 (linux/amd64) |
| 이미지 크기 | 212MB |
| 이미지 내용 | `/srv/backend/app`, `/srv/backend/data/holidays`, `/srv/frontend`의 `index.html`, `css`, `js`, `fonts`만 있음. `.env` 파일 없음. 실행 사용자 `appuser` |
| 포트 | `PORT=10000`을 주면 `0.0.0.0:10000`에서 시작. 서버 프로세스 번호 1 |
| 화면 | 375px 너비에서 첫 화면, 글꼴, 색 적용. 콘솔 오류 없음 |
| 설정 API | `GET /api/config`의 `kakaoMapKey` 값 있음 |
| 주소 검색 | `POST /api/address/search` 200, 결과 10건 |
| 추천 | 공개 장소 4쌍 모두 200. 대중교통 `ok`, 따릉이 `ok`. 서울 버스 노선 전체(`seoul_routes ok`), 버스, 지하철 실시간 위치 조회 기록 확인 |
| 메모리 | 위 조회 후 약 95MiB |
| 개인정보 | 로그에 주소, 좌표, 검색어 없음 |
| 종료 | `docker stop` 후 1초 안에 `Application shutdown complete` |

- 컨테이너 안 시간대는 UTC이므로 앱 로그의 시각은 한국 시각보다 9시간 이른 값으로 찍힘. 경로 판단은 코드가 한국 표준시를 직접 쓰므로(`main.py`의 `now_kst`) 영향 없음

### 6.2 Render 배포 후 확인
| 순서 | 확인 | 방법 | 실패 시 |
|---|---|---|---|
| 1 | 빌드, 실행 | Render Logs에 이미지 빌드 완료와 `Uvicorn running on http://0.0.0.0:{포트}` 기록 | 빌드 실패면 5.2의 Dockerfile Path, Build Context. 실행 후 접속이 안 되면 로그의 포트 번호와 E-3 |
| 2 | 화면 | 휴대폰에서 `https://{Name}.onrender.com` 열기. 글꼴, 색 적용 | 색이 없으면 `tokens.css` 저장소 포함 여부 |
| 3 | 설정 API | `https://{Name}.onrender.com/api/config`의 `kakaoMapKey` 값이 비어 있지 않음 | 환경 변수 `KAKAO_JS_API` |
| 4 | 주소 검색 (DS-1) | 장소 화면에서 주소 등록 | `KAKAO_REST_API` 값의 따옴표(5.3), 카카오 허용 IP(7장) |
| 5 | 4종 경로 | 오늘 화면에서 추천 받기. Logs에서 외부 호출 결과 상태 확인 | 특정 데이터만 실패하면 E-6 (해외 접속 차단 여부) |
| 6 | 따릉이 (DS-5) | 서울 안 장소 쌍에서 따릉이 포함 경로 | `DATA_SEOUL_GOKR_GENERIC_API` |
| 7 | 첫차, 막차, 실시간 위치 | 버스, 지하철 구간 표시 | 공공데이터포털 키, E-6 |
| 8 | 지도 | 지도 화면 열기 | 7장 도메인 등록 |
| 9 | 홈 화면 추가 | 휴대폰 브라우저 메뉴에서 홈 화면에 추가 | HTTPS 주소인지 확인 |
| 10 | 개인정보 | Logs에 주소, 좌표, 검색어가 없음 (`masterplan.md` 5단계) | 주소, 좌표는 POST 본문으로만 오가므로(`api.js`) 주소창, 접속 기록에 남지 않음 |
| 11 | 메모리 | Metrics의 메모리 사용량이 512MB에 여유가 있음 | 넘으면 Render가 컨테이너를 다시 켬 |
| 12 | 잠들기 후 첫 응답 | 15분 이상 지난 뒤 앱을 열어 첫 추천까지 걸리는 시간 | 2장 방법 검토 |

## 7. 카카오 개발자 설정
| 대상 | 작업 | 이유 |
|---|---|---|
| JavaScript 키 | 사이트 도메인(JavaScript SDK 도메인) 목록에 `https://{Name}.onrender.com` 추가. 개발용 `http://localhost:8000`, `http://localhost:8001`은 유지 | 등록한 도메인에서만 지도 SDK가 동작 (`api_spec.md` 2.1). 등록하지 않으면 지도 화면만 실패 상태로 표시됨 |
| REST API 키 | 허용 IP 주소 설정을 쓰고 있다면 해제하거나 Render의 나가는 IP 목록(대시보드 Connect → Outbound) 추가 | Render 서버에서 나가는 호출이 막히지 않게 함 |

- 로컬 Docker 검사에서 `localhost:8002`로 지도 화면을 볼 때는 JavaScript 키 도메인에 `http://localhost:8002`도 필요. 지도 외 화면은 등록 없이 동작
- 콘솔 메뉴 이름은 개편이 잦으므로 확인 필요 (E-5)

## 8. 공개 접속과 호출량

### 8.1 문제
- 서버는 접속자를 구분하지 않으므로 모든 접속자가 같은 인증키의 하루 무료 사용량을 함께 씀
- 하루 무료 사용량을 넘기면 그날 남은 시간 동안 본인을 포함한 모든 접속자의 해당 조회가 실패함. 유료 사용 설정을 하지 않았으므로 과금은 없음 (`datasource.md` C-7)
- 추천 1회당 최대 호출 수와 버틸 수 있는 횟수 (`datasource.md` 8장, 캐시 재사용 없음 기준)
  | 데이터 | 1회 최대 | 무료 사용량 | 하루 추천 가능 횟수 |
  |---|---|---|---|
  | DS-3 도보 경로 | 12 | 1,000 | 약 83회 |
  | DS-4 자전거 경로 | 4 | 1,000 | 250회 |
  | DS-2 대중교통 경로 | 1 | 1,000 | 1,000회 |
  | DS-14 ~ DS-16 버스 위치 | 구간 노선 수 (예: 3) | 지역별 1,000 | 약 333회 |
- 같은 출발지, 도착지의 반복 조회는 24시간 캐시로 줄지만, 다른 사람의 장소는 캐시를 함께 쓰지 못함. 무료 플랜은 잠들 때 캐시도 사라짐 (2장)

### 8.2 확인 방법
- 카카오 개발자 콘솔의 API별 사용량 통계 (E-5)
- Render Logs의 `POST /api/recommend` 기록 수

### 8.3 대응 방법 (배포 후 사용자 결정)
| 방법 | 내용 | 코드 수정 |
|---|---|---|
| 주소 공유 범위 조절 | 수업 발표 등 필요한 때에만 주소를 알림 | 없음 |
| 접속자별 요청 수 제한 | 같은 접속 주소의 추천 요청을 분당, 하루 횟수로 제한. 접속 주소는 서버 메모리에서만 세고 로그에 쓰지 않음 | 있음 (`main.py` 미들웨어) |
| 서버 전체 하루 상한 | 하루 추천 요청이 정한 수를 넘으면 외부 호출 없이 실패 응답 | 있음 |

## 9. 갱신 배포와 되돌리기
| 작업 | 방법 |
|---|---|
| 갱신 | 로컬 검사(4.1, 4.2) 통과 후 `main`에 push (사용자 진행 또는 허락 후). Auto-Deploy가 이미지를 다시 만들고 컨테이너를 바꿈 |
| 수동 배포 | 대시보드 Manual Deploy → Deploy latest commit |
| 되돌리기 | 대시보드 Events에서 이전 배포의 Rollback 선택 (E-7) |
| 일시 중지 | 대시보드 Settings의 Suspend. 다시 켤 때 Resume |
| 기준 이미지 보안 패치 | `python:3.14.8-slim`이 갱신되어도 빌드 캐시 때문에 반영되지 않을 수 있음. 대시보드 Manual Deploy의 빌드 캐시 비우기 선택지로 다시 배포 (E-8) |

- 배포할 때마다 컨테이너가 새로 켜지므로 메모리 캐시가 비워짐

## 10. 확인 필요 (외부 정보)
| ID | 항목 | 이 문서의 위치 |
|---|---|---|
| E-1 | Render 무료 플랜의 잠들기 기준 시간, 다시 켜지는 시간, 월 무료 시간, 메모리, CPU | 2장 |
| E-2 | 외부 주기 호출로 무료 서버를 깨워 두는 것이 Render 약관상 허용되는지 | 2장 |
| E-3 | Render가 Docker 웹 서비스에 환경 변수 `PORT`를 넣어 주는지, 기본값, 앱이 다른 포트에서 접속을 받을 때의 동작 | 3.3, 5.3, 6.2 |
| E-4 | Render 지역 목록, 만든 뒤 지역 변경 가능 여부 | 5.2 |
| E-5 | 카카오 개발자 콘솔의 JavaScript 키 도메인 등록, REST API 키 허용 IP, 사용량 통계 메뉴의 현재 이름과 위치 | 7장, 8.2 |
| E-6 | 공공데이터포털(data.go.kr), 서울 열린데이터광장(openapi.seoul.go.kr:8088, swopenapi.seoul.go.kr), 서울 버스(ws.bus.go.kr)가 해외(싱가포르) 서버의 호출을 막는지 | 6.2 |
| E-7 | Render 무료 플랜에서 Rollback, Health Check Path를 쓸 수 있는지 | 5.4, 9장 |
| E-8 | Render 무료 플랜의 Docker 빌드 지원과 제한(월 빌드 시간, 빌드 제한 시간, 이미지 크기), Docker 설정 항목의 현재 이름(Dockerfile Path, Docker Build Context Directory, Docker Command), 빌드 캐시 비우기 방법 | 5.2, 9장 |
