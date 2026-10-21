# 작업 규칙 (frontend)

- `frontend/` 폴더 안의 작업에만 적용되는 하위 규칙
- 최상위 `CLAUDE.md`의 전역 규칙과 함께 적용. 충돌하면 최상위 규칙이 우선

## 1. 작업 범위
- 화면(HTML, CSS, JS), 화면 쪽 규칙 로직(`js/logic/`), 기기 저장, 로직 테스트만 다룸
- 결과물은 `frontend/` 안에만 저장. 예외: `css/tokens.css`는 `tools/build_tokens.py`가 만드는 생성물
- `backend/`, `docs/` 수정이 필요하면 직접 고치지 않고 필요한 변경 내용을 사용자에게 알림
- 외부 API를 화면에서 직접 호출하지 않음. 모든 데이터는 서버 API로 받음
  - 예외: 경로 지도(권장 F-16)의 Kakao Maps JavaScript SDK와 지도 그림은 브라우저가 직접 받음 (2026-10-20 사용자 허용). 지도 키는 서버 `GET /api/config`로 받음

## 2. 기준 문서
| 문서 | 쓰임 |
|---|---|
| `docs/product/rules.md` | 8, 9, 11장 화면 쪽 규칙, 12장 기본값 |
| `docs/tech/api_spec.md` | 서버 API의 요청, 응답, 개인정보 기준 |
| `docs/design/DESIGN.md` | 토큰, 색 의미, 컴포넌트, 상태별 표현 |
| `docs/design/` 화면 명세 | 화면별 구성, 상태, 문구 |
| `docs/product/functions.md` | 기능 범위 (필수 F-01 ~ F-12, 탑재한 권장 F-15, F-16, F-26) |
| `docs/tech/tech_stack.md` | 폴더 구조, 실행 방법, 테스트 방법 |

- 문서와 코드가 다르면 문서를 기준으로 하고, 문서 변경이 필요하면 사용자에게 먼저 확인
- 명세에 없는 화면, 컴포넌트, 문구는 만들지 않고 사용자에게 확인

## 3. 기술 규칙
- HTML, CSS, JavaScript(ES 모듈)만 사용. 프레임워크, 빌드 도구, npm 의존 패키지 없음 (`tech_stack.md` 4.1)
  - `package.json`에는 ES 모듈 지정과 테스트 명령만 둠
  - 권장 기능용 라이브러리(Chart.js 등)는 해당 기능을 추가할 때 사용자 확인 후 도입
  - Kakao Maps JavaScript SDK는 도입함 (권장 F-16, `tech_stack.md` 4.1). `js/map-sdk.js`만 불러옴
- JS 주석은 '~음' 또는 명사로 끝냄 (최상위 `CLAUDE.md` 2장)

### 3.1 로직 (`js/logic/`)
- `rules.md`의 화면 쪽 규칙을 순수 함수로 작성. 지금 시각, 서버 응답, 저장 값을 모두 인자로 받고, 함수 안에서 시각을 읽거나 저장소, 서버에 접근하지 않음
- 계산은 초 단위로 하고, 화면에 보이는 값만 분 단위로 바꿈. 소요 시간, 도착 시각은 올림, 줄어드는 시간과 출발 시각은 버림 (`rules.md` 2장)
- 기본값은 `rules.md` 12장의 값을 한 파일에 상수로 모아 둠

### 3.2 디자인
- 색, 글자, 간격, 모서리, 그림자 값은 `css/tokens.css`의 CSS 변수로만 사용. 값을 직접 적지 않음 (최상위 `CLAUDE.md` 6장)
- `css/tokens.css`는 직접 고치지 않음. 토큰 변경은 `DESIGN.md` 수정 후 다시 생성
- 컴포넌트는 `DESIGN.md` 7장 이름과 같은 CSS 클래스, 같은 이름의 함수(`js/components/`)로 만들고 모든 화면이 공유
- 상태 표현은 `DESIGN.md` 8장을 따름. 수단은 항상 `DESIGN.md` 2.4의 수단 색 (색 고르기는 `js/logic/modes.js`)

## 4. 기기 저장 규칙
- 저장 위치는 localStorage. 객체는 JSON 문자열로 바꿔 저장 (`tech_stack.md` 6장)
- 읽기, 쓰기는 `js/storage.js`만 함. 다른 파일은 localStorage를 직접 쓰지 않음

### 4.1 저장 키
| 키 | 내용 |
|---|---|
| `dmpm.v1.places` | 장소 2개 |
| `dmpm.v1.settings` | 목표 도착 시각, 여유 시간, 출근 퇴근 모드, 수동 전환 상태, 화면 모드 |

- 키 이름의 `v1`은 저장 형식 버전. 형식이 바뀌면 새 버전 키를 만들고, 앱을 열 때 이전 키를 읽어 옮긴 뒤 이전 키를 지움
- 읽을 때 없으면 `null`로 두는 선택 항목을 더하는 것은 형식 변경으로 보지 않아 같은 버전 키를 씀 (2026-10-20 사용자 결정)
- 시간 길이는 초 단위 정수, 시각은 ISO 8601 문자열로 저장

### 4.2 장소 (`dmpm.v1.places`)
- `origin`(출발지, 예: 집), `destination`(도착지, 예: 회사) 두 칸
- 칸마다 `name`, `addressName`, `roadAddress`, `jibunAddress`, `placeName`, `x`, `y`. `placeName`은 키워드 장소 검색으로 고른 장소의 이름이며 선택 항목(없으면 `null`)

### 4.3 설정 (`dmpm.v1.settings`)
- `targetArrival`(`commute`, `return` 각각 `HH:MM` 또는 `null`)
- `marginSeconds`(기본값 `rules.md` 12장)
- `directionMode`(`commute_return` 출근/퇴근, `return_commute` 퇴근/출근)
- `manualDirection`(수동 전환한 방향과 유지 종료 시각, 없으면 `null`)
- `theme`(화면 모드. `light` 라이트, `dark` 다크, `null` 기기 설정 따름). 선택 항목이며 없으면 `null` (`DESIGN.md` 2.5.5, `screen-settings.md` 3.6)

### 4.4 지우기
- 저장 정보 모두 지우기(F-12)는 위 키를 모두 지움. 확인 절차 후 실행 (`DESIGN.md` 7.3 `button-caution`)

## 5. 개인정보
- 서버로 보내는 값은 `api_spec.md` 6장의 표에 있는 것뿐 (주소, 장소 검색어, 좌표, 기준 도착 시각). 장소 이름, 설정을 서버로 보내지 않음
  - 기준 도착 시각은 목표 도착 시각 − 여유 시간 하나만 보내고, 두 설정 값을 따로 보내지 않음 (2026-10-20 사용자 결정, `rules.md` 3.4.1)
- 주소, 장소 검색어와 좌표는 주소창(URL)에 넣지 않음
- 실시간 위치(Geolocation)를 쓰지 않음

## 6. 테스트
- 로직 테스트는 Node.js 기본 테스트 기능(`node --test`)으로 `tests/logic/`에 작성하고 `frontend/` 폴더에서 실행
- `rules.md` 13장 검증 기준 중 화면 쪽 상황(V-12, V-14 ~ V-16)을 테스트로 작성
- 테스트 입력의 서버 응답은 `api_spec.md` 4장 형식을 따름
- 화면 확인은 휴대폰 너비에서 직접 진행하고 `docs/design/` 화면 명세와 대조
