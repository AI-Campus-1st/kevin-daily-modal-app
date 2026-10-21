# 기술 스택

## 0. 문서 정보
- 작성일: 2026-10-19
- 최종 수정: 2026-10-20
- 상태: 확정 (2026-10-19). 2.2 역할 분담(D-24), 3.1, 4.1 라이브러리 목록(D-25), 3.5 대중교통 경로 캐시(D-29), 7장 환경 변수(D-23) 사용자 확인
- 근거 문서: `docs/product/functions.md`, `docs/product/rules.md`, `docs/tech/datasource.md`, `docs/design/DESIGN.md`
- 쓰임: 백엔드, 프론트엔드의 기술 선택, 역할 분담, 폴더 구조, 저장 방식, 실행 방법의 기준
- 라이브러리 버전은 설치 시점의 최신 안정판으로 고정하고 이 문서에 기록

## 1. 개발 환경
| 항목 | 값 |
|---|---|
| 운영체제 | Windows 11 Pro |
| Python | 3.14.8 (64비트, 2026-10-19 확인) |
| Node.js | 24.21.0 (2026-10-19 확인). 프론트엔드 로직 테스트(`node --test`)에만 사용. 외부 JS 패키지 설치 없음 |
| 가상 환경 | `backend/.venv` (Python 기본 `venv`) |
| 화면 확인 | 데스크톱 브라우저의 휴대폰 너비 화면과 실제 휴대폰 |

## 2. 전체 구조

### 2.1 구성
| 구성 | 역할 |
|---|---|
| FastAPI 서버 1개 | `/api/...` 주소로 주소 검색과 4종 경로 제공, `/` 주소로 `frontend/` 정적 파일 제공 |
| 브라우저 | 화면, 표시 순서, 추천 이유, 출발 시각, 출근 퇴근 전환, 장소와 설정의 기기 내 보관 |
| 외부 데이터 | 카카오 API(DS-1 ~ DS-4), 따릉이 대여정보(DS-5)는 서버만 호출. 카카오 지도 SDK(DS-6)만 브라우저가 직접 받음 (권장 F-16) |

- 화면과 API를 같은 서버, 같은 주소에서 제공하므로 다른 출처 요청 허용 설정(CORS)이 필요 없음

### 2.2 역할 분담
| `rules.md` 장 | 내용 | 위치 | 이유 |
|---|---|---|---|
| 3 ~ 7장 | 기본 경로, PM 절감 시간, 따릉이 포함 경로(대여소 선택, 조건 판단), 버스 전용, PM 전용 경로 만들기 | 서버 | 카카오 REST API 키는 서버에만 둠. 여러 외부 호출을 이어서 해야 하므로 서버에서 한 번에 처리 |
| 10장 (외부 데이터 실패) | 조회 실패 시 경로 처리 | 서버 | 외부 호출 결과를 아는 곳 |
| 8장 | 표시 순서, 기본 경로와의 차이 | 브라우저 | 이후 이동 선호(권장 F-18)처럼 기기에만 있는 설정을 반영해야 함 |
| 9장 | 출근, 퇴근 전환 | 브라우저 | 기기 설정과 지금 시각으로 결정 |
| 11.1 | 추천 이유 | 브라우저 | 화면 문구 |
| 11.2 | 출발 시각 | 브라우저 | 목표 도착 시각, 여유 시간은 기기에만 있음 |

- 서버는 사용자 설정(목표 도착 시각, 모드, 선호)을 받지 않음. 서버가 받는 값은 출발지, 도착지 좌표와 주소 검색어뿐 (`api_spec.md` 6장)

### 2.3 데이터 흐름
| 순서 | 위치 | 동작 |
|---|---|---|
| 1 | 브라우저 | 지금 시각과 설정으로 방향(출근, 퇴근)을 정하고, 기기에 저장된 두 장소의 좌표를 그 방향 순서로 고름 |
| 2 | 브라우저 → 서버 | 출발지, 도착지 좌표로 추천 API 한 번 요청 |
| 3 | 서버 | 카카오 대중교통 경로 조회와 PM 전용 자전거 경로 조회를 동시에 시작 → 기본 경로, 버스 전용 경로 선택 → 두 경로의 출발 도보, 도착 도보 조회 → 승차 대기 시간을 포함한 총 소요 시간, PM 절감 시간 계산 → First, Last mile 판정 → 따릉이 대여정보에서 대여소 선택 → 카카오 도보, 자전거 경로 조회 → 따릉이 조건 판단 |
| 4 | 서버 → 브라우저 | 4종 경로(구간 구성, 총 소요 시간, 대여소, 실패 정보) 응답 |
| 5 | 브라우저 | 표시 순서, 이유, 출발 시각 계산 후 화면 표시 |

## 3. 백엔드

### 3.1 라이브러리
| 구분 | 라이브러리 | 버전 | 쓰임 |
|---|---|---|---|
| 실행 | FastAPI | 0.150.0 | API 주소 연결, 요청 검증, 정적 파일 제공 |
| 실행 | Uvicorn | 0.54.0 | FastAPI 앱 실행 서버 |
| 실행 | Pydantic | 2.14.1 | 요청, 응답 모델과 값 검증 (FastAPI에 포함) |
| 실행 | httpx | 0.28.1 | 외부 API 비동기 호출. FastAPI `TestClient`도 사용 |
| 실행 | python-dotenv | 1.2.4 | 개발 중 `backend/.env`의 인증키를 환경 변수로 읽음 |
| 개발 | PyYAML | 6.0.3 | `DESIGN.md` 머리말을 읽어 `tokens.css` 생성 (5장) |
| 개발 | pytest | 9.1.1 | 테스트 |
| 개발 | Ruff | 0.17.1 | 코드 검사, 서식 정리 |

- 설치일 2026-10-20. 고정 버전은 `requirements.txt`, `requirements-dev.txt`와 같음
- 위 라이브러리를 설치할 때 함께 설치되는 패키지(Starlette 등)는 버전을 고정하지 않음

- Python 기본 기능으로 처리하는 것
  | 기능 | 기본 기능 |
  |---|---|
  | 메모리 캐시 | 딕셔너리와 저장 시각 비교 |
  | 직선거리 계산 | `math` (하버사인 공식) |
  | 로그 | `logging` |

### 3.2 설치 파일
| 파일 | 내용 |
|---|---|
| `requirements.txt` | 실행 라이브러리와 고정 버전 |
| `requirements-dev.txt` | `-r requirements.txt`와 개발 라이브러리 |
| `pyproject.toml` | Ruff, pytest 설정 |
| `.env.example` | 환경 변수 이름만 적은 예시 파일 (값 없음) |

### 3.3 Ruff, pytest 설정
```toml
[tool.ruff]
target-version = 'py314'
line-length = 100

[tool.ruff.lint]
select = ['E', 'F', 'I', 'B', 'UP', 'Q']

[tool.ruff.lint.flake8-quotes]
inline-quotes = 'single'
multiline-quotes = 'single'
docstring-quotes = 'single'

[tool.ruff.format]
quote-style = 'preserve'

[tool.pytest.ini_options]
testpaths = ['tests']
pythonpath = ['.']
```
- 작은따옴표 규칙(최상위 `CLAUDE.md` 5장)은 검사의 `Q` 규칙이 확인. 서식 정리는 따옴표를 바꾸지 않도록 `preserve`

### 3.4 폴더 구조
```
backend/
  CLAUDE.md                 backend 하위 규칙
  requirements.txt
  requirements-dev.txt
  pyproject.toml
  .env.example
  .env                      실제 인증키 (git 제외)
  data/
    holidays/               평일 공휴일 목록. 연도마다 {연도}.csv (datasource.md 7.1)
    rail/                   1 ~ 9호선 밖 지하철 시간표. 노선마다 {노선 이름}.csv (datasource.md 7.4)
  app/
    main.py                 FastAPI 앱, 라우터 연결, frontend/ 정적 파일 연결
    config.py               환경 변수, rules.md 12장 기본값 상수
    schemas.py              요청, 응답 Pydantic 모델
    cache.py                메모리 캐시 (3.5)
    geo.py                  직선거리 계산
    routers/
      address.py            주소 검색 중계
      recommend.py          4종 경로 (외부 호출 순서 조정)
    clients/
      kakao.py              DS-1 ~ DS-4 호출과 응답 정리
      bike.py               DS-5 호출(3번 나누어)과 응답 정리
      timetable.py          DS-8 ~ DS-13 첫차, 막차 조회와 정리
      live.py               DS-14 ~ DS-18 실시간 위치 조회와 정리 (권장 F-26)
    planner/                rules.md 3 ~ 7장, 10장의 순수 함수 (외부 호출 결과를 인자로 받음)
      base.py               기본 경로 선택, 출발 도보, 도착 도보 반영, 총 소요 시간, PM 절감 시간 (3, 4장)
      miles.py              첫 승차 지점, 마지막 하차 지점, First, Last mile 구간 (1, 3.1장)
      stations.py           대여소 선택 (5.1)
      bike_route.py         따릉이 구간 시간, First, Last mile 대체, 전 구간 따릉이, 조건 판단 (5.2 ~ 5.5)
      bus_pm.py             버스 전용, PM 전용 경로 (6, 7장)
      service.py            운행 시간(첫차, 막차) 판단 (3.4)
      live.py               실시간 상대 위치 계산 (11.3)
  tests/
```
- `planner/`의 함수는 외부 호출을 하지 않고 호출 결과를 인자로 받는 순수 함수. 같은 입력에 같은 결과를 내므로 예시 응답만으로 테스트 가능 (`rules.md` 13장)

### 3.5 메모리 캐시
| 대상 | 보관 시간 | 이유 |
|---|---|---|
| 따릉이 전체 목록 (DS-5) | 30초 | 재고는 자주 바뀜 |
| 대중교통 경로 (DS-2) | 24시간 | 조회 시각에 따라 결과가 달라지지 않음(`datasource.md` C-4). 매일 같은 출발지, 도착지를 조회하므로 하루 무료 사용량(1,000건) 절약 |
| 버스 노선 첫차, 막차 (DS-9 ~ DS-11), 지하철 첫차, 막차 (DS-12) | 같은 날짜 안에서만 (캐시 열쇠에 날짜 포함, 24시간) | 서울 버스는 그날 값만 줌. 노선, 시간표는 하루 안에 거의 바뀌지 않음 |
| 버스 노선 ID, 경유 정류소, 지하철 역 코드, 역별 시간표 (DS-15, DS-16, DS-18) | 같은 날짜 안에서만 (24시간) | 노선 구성과 시간표는 하루 안에 거의 바뀌지 않음 |
| 서울 버스 노선별 경유 정류소 전체 (DS-19) | 같은 날짜 안에서만 (24시간) | 노선 번호로 거르는 요청이 없어 전체(약 4만 행)를 하루 한 번 받음. 첫차, 막차 확인과 실시간 위치가 함께 씀 |
| 버스, 지하철 실시간 위치 (DS-14 ~ DS-17) | 20초 | 실시간 값이므로 한 요청 안에서 같은 조회를 다시 쓰는 정도만 |
| 도보, 자전거 경로 (DS-3, DS-4) | 24시간 | 같은 두 지점, 같은 방식(`route_mode`) 사이의 길은 거의 바뀌지 않으며, 하루 무료 사용량(각 1,000건) 절약 |

- 캐시는 서버 메모리에만 두고 파일, 데이터베이스, 로그에 쓰지 않음. 보관 시간이 지나거나 서버를 다시 켜면 사라짐
- 좌표는 소수 다섯째 자리(약 1m)로 맞춘 값을 캐시 열쇠로 사용

## 4. 프론트엔드

### 4.1 기술
| 구분 | 기술 | 쓰임 |
|---|---|---|
| 화면 | HTML, CSS, JavaScript (ES 모듈) | 프레임워크, 빌드 도구 없음 |
| 글꼴 | Pretendard (프로젝트에 파일 포함) | `DESIGN.md` 3장 |
| 기기 저장 | localStorage | 장소, 설정 (6장) |
| 로직 테스트 | Node.js 기본 테스트 기능 (`node --test`) | `js/logic/` 순수 함수 테스트. 외부 패키지 없음 |
| 지도 (권장 F-16) | Kakao Maps JavaScript SDK | `dapi.kakao.com`에서 받는 `<script>`. npm 패키지가 아님. 지도 화면을 처음 열 때만 불러옴(`autoload=false`). 2026-10-20 사용자 확인 후 도입 |
| 권장 기능용 | Chart.js, Notification API, 웹 앱 매니페스트 | F-23 주간 리포트, F-20 알림, F-25 홈 화면 추가. 해당 기능 추가 시 사용자 확인 후 도입 |

### 4.2 폴더 구조
```
frontend/
  CLAUDE.md                 frontend 하위 규칙
  package.json              ES 모듈 지정과 테스트 명령만 기록. 의존 패키지 없음
  index.html                단일 페이지. 화면은 주소의 # 뒤 이름으로 전환
  css/
    tokens.css              DESIGN.md 머리말에서 생성 (직접 수정 금지)
    fonts.css               Pretendard 글꼴 등록
    base.css                바탕, 글꼴, 단일 열 배치
    components.css          DESIGN.md 7장 컴포넌트
    pages.css               화면별 배치
  fonts/
    Pretendard-Regular.woff2
    Pretendard-Medium.woff2
    Pretendard-Bold.woff2
    LICENSE.txt             SIL Open Font License 1.1
  js/
    app.js                  화면 이동, 앱 상태
    api.js                  서버 API 호출
    map-sdk.js              카카오 지도 SDK 불러오기 (권장 F-16)
    storage.js              localStorage 읽기, 쓰기
    logic/                  rules.md 8, 9, 11장의 순수 함수 (지금 시각을 인자로 받음)
      order.js              표시 순서, 기본 경로와의 차이
      direction.js          출근, 퇴근 전환
      reason.js             추천 이유
      departure.js          출발 시각, 분 단위 처리
      legs.js               구간 세부 문구 (권장 F-15, F-16)
    components/             DESIGN.md 7장 컴포넌트를 만드는 함수
    pages/                  화면별 그리기 함수 (화면 명세 기준)
  tests/
    logic/                  js/logic/ 테스트
```

### 4.3 Pretendard 글꼴
- 굵기 400, 500, 700 세 개의 woff2 파일만 포함 (`DESIGN.md` 3.1)
- 출처: Pretendard 공식 GitHub 저장소(orioncactus/pretendard)의 배포 파일. 내려받을 때 버전을 이 문서에 기록
- 내려받은 버전: v1.3.9 (2023-11-05 릴리스, 2026-10-20 내려받음). 저장소의 `packages/pretendard/dist/web/static/woff2/`
- 사용 조건: SIL Open Font License 1.1. 라이선스 파일을 함께 둠
- 내려받기는 프론트엔드 단계 시작 시 사용자 확인 후 진행

### 4.4 화면 이동
- 주소의 `#` 뒤 이름으로 화면을 바꿈 (`hashchange` 이벤트). 페이지를 새로 받지 않고, 기기 뒤로 가기가 그대로 동작
- 화면 목록과 주소는 화면 명세에서 확정

## 5. 디자인 토큰 생성
- 도구: `tools/build_tokens.py` (프로젝트 root의 `tools/`)
- 동작: `docs/design/DESIGN.md` 머리말(`---` 사이)을 PyYAML로 읽어 `frontend/css/tokens.css` 생성
  | 머리말 | CSS 변수 예 |
  |---|---|
  | `colors.primary` | `--colors-primary: #5865f2;` |
  | `typography.body.fontSize` | `--typography-body-font-size: 16px;` |
  | `rounded.lg` | `--rounded-lg: 16px;` |
  | `spacing.md` | `--spacing-md: 16px;` |
  | `{colors.primary}` 참조 | `var(--colors-primary)` |
- 대상: `colors`, `typography`, `rounded`, `spacing`, `elevation`, `layout`. `components`는 CSS 변수로 만들지 않고 `components.css`가 위 변수로 작성
- 검사 모드: `--check`로 실행하면 파일을 쓰지 않고 현재 `tokens.css`가 머리말과 같은지만 확인. 다르면 오류로 끝남
- `tokens.css`는 생성물이므로 직접 고치지 않음 (최상위 `CLAUDE.md` 6장)

## 6. 저장 방식
| 위치 | 저장 대상 | 방식 |
|---|---|---|
| 브라우저 | 장소 2개 (이름, 주소, 좌표) | localStorage |
| 브라우저 | 설정 (목표 도착 시각, 여유 시간, 출근 퇴근 모드, 수동 전환 상태) | localStorage |
| 브라우저 | 마지막으로 받은 추천 결과와 받은 시각 | 메모리 (화면을 닫으면 사라짐, `rules.md` 10장) |
| 서버 | 외부 API 응답 | 메모리 캐시 (3.5) |

- 서버에는 사용자 정보를 저장하는 곳이 없음
- localStorage는 문자열만 저장하므로 객체는 JSON 문자열로 바꿔 저장. 저장 형식에 버전 번호를 붙임
- 저장 키와 형식의 세부는 `frontend/CLAUDE.md` 4장

## 7. 환경 변수
| 이름 | 값 | 사용처 |
|---|---|---|
| `KAKAO_REST_API` | 카카오 REST API 키 | DS-1 ~ DS-4. 서버에서만 사용 |
| `DATA_SEOUL_GOKR_GENERIC_API` | 열린데이터광장 일반 인증키 | DS-5, DS-12 |
| `DATA_GOKR_GENERIC_API` | 공공데이터포털 일반 인증키 | DS-9 ~ DS-11 (버스 노선 첫차, 막차), DS-14 ~ DS-16 (버스 위치) |
| `DATA_SEOUL_GOKR_SUBWAY_API` | 열린데이터광장 실시간 지하철 인증키 | DS-17 (지하철 실시간 도착, 권장 F-26) |
| `KAKAO_JS_API` | 카카오 JavaScript 키 | DS-6. 서버가 `GET /api/config`로 화면에 전달 (`api_spec.md` 2.1) |

- 개발 중에는 `backend/.env`에 적고 python-dotenv로 읽음. `.env`는 git에서 제외
- 카카오 REST API 키는 화면에 보내지 않음. JavaScript 키는 도메인 등록으로만 사용이 제한되는 키라 화면에 보내도 되지만 저장소에는 적지 않음

## 8. 실행 방법
```powershell
cd backend
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements-dev.txt
.venv\Scripts\python ..\tools\build_tokens.py
.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
```
- 브라우저에서 `http://localhost:8000` 열기
- 테스트
  | 대상 | 명령 (실행 위치) |
  |---|---|
  | 백엔드 | `.venv\Scripts\python -m pytest` (`backend/`) |
  | 프론트엔드 로직 | `npm test` (`frontend/`). `package.json`의 `node --test "tests/**/*.test.js"` 실행 |
  | 코드 검사 | `.venv\Scripts\python -m ruff check .`, `ruff format --check .` (`backend/`) |
  | 토큰 일치 | `.venv\Scripts\python ..\tools\build_tokens.py --check` (`backend/`) |

## 9. git 관리 파일
- `.gitignore` (프로젝트 root)
  | 제외 | 이유 |
  |---|---|
  | `.env`, `.env.*` (`.env.example` 제외) | 인증키 |
  | `.venv/` | 가상 환경 |
  | `__pycache__/`, `*.pyc`, `.pytest_cache/`, `.ruff_cache/` | 실행 중 생기는 캐시 |
- 현재 `.gitignore`의 `backend/data/raw/` 줄은 이 프로젝트에서 쓰지 않음. 정리 여부는 사용자 확인
- `.gitattributes`: 줄바꿈을 LF로 통일 (작성 예정)
