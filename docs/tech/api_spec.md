# API 명세서

## 0. 문서 정보
- 작성일: 2026-10-19
- 최종 수정: 2026-10-20
- 상태: 확정 (2026-10-20). 역할 분담(D-24), 출발 도보, 도착 도보와 승차 대기 시간(D-26, D-27) 반영
- 근거 문서: `docs/product/functions.md`, `docs/product/rules.md`, `docs/tech/datasource.md`, `docs/tech/tech_stack.md`
- 범위: 화면(브라우저)과 서버 사이의 API. 서버가 외부 서비스를 부르는 형식은 `datasource.md`

## 1. 공통 규칙

### 1.1 형식
| 항목 | 규칙 |
|---|---|
| 주소 | 같은 서버의 `/api/...` |
| 본문 | JSON, UTF-8 |
| 필드 이름 | 낮은 카멜 표기 (예: `totalSeconds`) |
| 시간 길이 | 초 단위 정수. 서버는 분 단위로 바꾸지 않음 (`rules.md` 2장) |
| 시각 | 한국 표준시 오프셋을 포함한 ISO 8601 (예: `2026-10-20T07:41:05+09:00`) |
| 거리 | 미터 단위 정수 |
| 좌표 | WGS84 경도 `x`, 위도 `y` (숫자) |
| 요청 방식 | 주소 검색어와 좌표는 주소창(URL)에 남지 않도록 모두 `POST` 본문으로 보냄 |

### 1.2 응답 상태
- 외부 서비스 장애, 사용량 초과, 시간 초과는 HTTP 오류로 끝내지 않고 HTTP 200과 본문의 `status`로 알림
  | `status` | 의미 |
  |---|---|
  | `ok` | 정상 |
  | `no_result` | 외부 서비스가 결과 없음으로 응답 (주소 후보 없음, 경로 없음) |
  | `unavailable` | 외부 서비스 조회 실패 |
- HTTP 오류는 요청 자체의 문제와 서버 내부 오류에만 사용
  | 코드 | 상황 |
  |---|---|
  | 422 | 요청 본문 형식 오류, 허용 범위를 벗어난 값 |
  | 500 | 서버 내부 오류 |

## 2. 정적 파일
| 요청 | 응답 |
|---|---|
| `GET /` | `frontend/index.html` |
| `GET /css/...`, `/js/...`, `/fonts/...` | `frontend/` 아래 파일 |

## 2.1 화면 설정 `GET /api/config` (권장 F-16)
| 필드 | 형식 | 내용 |
|---|---|---|
| `kakaoMapKey` | 문자열 또는 `null` | 카카오 JavaScript 키(`KAKAO_JS_API`). 환경 변수가 없으면 `null` |

- 요청 본문 없음. 사용자 정보를 받지 않음
- JavaScript 키는 등록한 도메인에서만 쓸 수 있는 키라 화면에 보냄 (`tech_stack.md` 7장). REST API 키는 보내지 않음

## 3. 주소, 장소 검색 `POST /api/address/search` (F-01)

### 3.1 요청
| 필드 | 형식 | 조건 |
|---|---|---|
| `query` | 문자열 | 공백 제외 2자 이상 100자 이하 |
| `page` | 정수 | 1 ~ 45, 기본 1 |
| `source` | 문자열 | 선택. `address` 또는 `place`. 첫 쪽은 보내지 않고, 다음 쪽(`page` 2 이상)은 첫 응답의 `source`를 그대로 보냄 |

### 3.2 응답
| 필드 | 형식 | 내용 |
|---|---|---|
| `status` | 문자열 | 1.2 |
| `source` | 문자열 | `address`(주소 검색 결과) 또는 `place`(키워드 장소 검색 결과). `status`가 `ok`일 때만 값이 있음 |
| `items` | 배열 | 주소 또는 장소 후보. `status`가 `ok`일 때만 값이 있음 |
| `items[].placeName` | 문자열 또는 `null` | 장소 이름. `source`가 `address`이면 `null` |
| `items[].addressName` | 문자열 | 대표 주소 |
| `items[].roadAddress` | 문자열 또는 `null` | 도로명 주소 |
| `items[].jibunAddress` | 문자열 또는 `null` | 지번 주소 |
| `items[].buildingName` | 문자열 또는 `null` | 건물 이름 |
| `items[].x`, `items[].y` | 숫자 | 좌표 |
| `isEnd` | 참/거짓 | 마지막 쪽 여부 |

- 한 번에 최대 10개 (`datasource.md` 4장 `size` 기본값)
- `source` 없이 요청하면 주소 검색을 먼저 하고, 결과가 0건이면 키워드 장소 검색 결과로 응답 (D-32)
- 주소 검색이 조회 실패이면 키워드 장소 검색으로 넘어가지 않고 `unavailable`
- 장소 후보의 값: `roadAddress`는 `road_address_name`(빈 값이면 `null`), `jibunAddress`는 `address_name`, `addressName`은 도로명 주소(없으면 지번 주소), `buildingName`은 `null`

## 4. 추천 `POST /api/recommend` (F-03 ~ F-07, F-11)

### 4.1 요청
| 필드 | 형식 | 조건 |
|---|---|---|
| `origin.x`, `origin.y` | 숫자 | 출발지 좌표. 경도 124 ~ 132, 위도 33 ~ 39 |
| `destination.x`, `destination.y` | 숫자 | 도착지 좌표. 범위는 위와 같음 |
| `arriveBy` | 시각 또는 생략 | 첫차, 막차 판단의 기준 도착 시각 = 목표 도착 시각 − 여유 시간 (`rules.md` 3.4.1). 지금 방향의 목표 도착 시각이 없으면 보내지 않음. 한국 표준시 오프셋 포함 |

- 방향(출근, 퇴근)은 화면이 정하고, 그 방향에 맞게 출발지와 도착지를 바꿔 보냄 (`rules.md` 9장)

### 4.2 응답 최상위
| 필드 | 형식 | 내용 |
|---|---|---|
| `fetchedAt` | 시각 | 서버가 결과를 만든 시각 |
| `transit` | 객체 | 카카오 대중교통 경로 조회 결과. `status`(1.2 또는 `out_of_service`: 경로가 모두 운행 시간 밖, `rules.md` 3.4.5) |
| `bikeData` | 객체 | 따릉이 대여정보 조회 결과. `status`(`ok`, `unavailable`), `fetchedAt`(시각 또는 `null`. `status`가 `unavailable`이면 `null`) |
| `base` | 객체 또는 `null` | 기본 경로 (4.4). `transit.status`가 `ok`일 때만 값이 있음 |
| `bikeMix` | 객체 또는 `null` | 따릉이 포함 경로 (4.5). 표시 조건을 만족하지 않으면 `null` |
| `busOnly` | 객체 또는 `null` | 버스 전용 경로 (4.3 형식). 없거나 기본 경로와 같으면 `null` |
| `pmOnly` | 객체 또는 `null` | PM 전용 경로 (4.6). 조회 실패 시 `null` |
| `notes` | 배열 | 경로를 만들지 않은 이유 (4.7) |

- 표시 순서와 기본 경로와의 차이는 화면이 계산 (`rules.md` 8장)
- `bikeData.status`가 `unavailable`이어도 마지막으로 조회에 성공한 대여소 목록이 있으면 따릉이 구간을 만들 수 있으며, 이때 `stockKnown`은 거짓 (`rules.md` 10장)

### 4.3 대중교통 경로 형식
| 필드 | 형식 | 내용 |
|---|---|---|
| `routeIndex` | 정수 | 카카오 응답 순서 (0부터) |
| `type` | 문자열 | `bus`, `subway`, `bus_subway` |
| `totalSeconds` | 정수 | 승차 대기 시간을 포함한 총 소요 시간 (`rules.md` 3.3). 출발 도보, 도착 도보 조회 실패 시 카카오 총 소요 시간 + 승차 대기 시간 (`rules.md` 3.2) |
| `totalDistance` | 정수 | 총 거리 (`rules.md` 3.3). 출발 도보, 도착 도보 조회 실패 시 카카오 총 거리 |
| `waitSeconds` | 정수 | 승차 대기 시간의 합 |
| `edgeWalkKnown` | 참/거짓 | 출발 도보, 도착 도보 조회 성공 여부. 거짓이면 `legs`에 두 도보가 없음 |
| `transfers` | 정수 | 환승 횟수 |
| `fare` | 정수 또는 `null` | 요금(원) |
| `legs` | 배열 | 구간 목록 (4.8) |
| `serviceUnknown` | 참/거짓 | 구간 중 `serviceUnknown`이 참인 구간이 있는지 (`rules.md` 3.4.4) |

### 4.4 `base` 기본 경로
- 4.3 형식에 아래 필드를 더함. `edgeWalkKnown`이 거짓이면 `pmSaving`은 `null` (`rules.md` 4장)
  | 필드 | 형식 | 내용 |
  |---|---|---|
  | `pmSaving.firstSeconds` | 정수 | 출발 도보를 킥보드 속도로 바꿀 때 줄어드는 시간 |
  | `pmSaving.lastSeconds` | 정수 | 도착 도보의 같은 값 |
  | `pmSaving.totalSeconds` | 정수 | 두 값의 합 (`rules.md` 4장) |

### 4.5 `bikeMix` 따릉이 포함 경로
| 필드 | 형식 | 내용 |
|---|---|---|
| `kind` | 문자열 | `first_last` (First, Last mile 대체), `full` (전 구간 따릉이) |
| `conditions.first` | 참/거짓 | 조건 1 만족 여부. First mile 쪽, Last mile 쪽 중 하나라도 해당하면 참 (`rules.md` 5.4) |
| `conditions.second` | 참/거짓 또는 `null` | 조건 2 만족 여부. First, Last mile 대체 경로를 만들지 못했으면 `null` |
| `conditions.third` | 참/거짓 또는 `null` | 조건 3 만족 여부. 전 구간 따릉이 경로를 조회하지 않았거나(First, Last mile 대체 경로를 표시) 만들지 못했으면 `null` |
| `totalSeconds` | 정수 | 총 소요 시간 |
| `transfers` | 정수 | 환승 횟수 (`full`이면 0) |
| `stockKnown` | 참/거짓 | 따릉이 재고를 확인했는지 (`rules.md` 10장) |
| `serviceUnknown` | 참/거짓 | 남은 대중교통 구간 중 `serviceUnknown`이 참인 구간이 있는지 |
| `legs` | 배열 | 구간 목록 (4.8). 바꾼 mile은 `bike` 구간 하나로 들어감 |

### 4.6 `pmOnly` PM 전용 경로
| 필드 | 형식 | 내용 |
|---|---|---|
| `totalSeconds` | 정수 | 카카오 자전거 경로(`SHORTEST`) 총 소요 시간 |
| `totalDistance` | 정수 | 총 거리 |
| `points` | 배열 | 경로 좌표 (4.9) |

### 4.7 `notes[]` 경로를 만들지 않은 이유
| 필드 | 형식 | 내용 |
|---|---|---|
| `target` | 문자열 | `bikeMix`, `busOnly`, `pmOnly` |
| `reason` | 문자열 | 아래 표 |

| `target` | `reason` | 의미 |
|---|---|---|
| `bikeMix` | `no_condition` | 세 조건 모두 만족하지 않음 |
| `bikeMix` | `no_station` | 반경 안에 조건에 맞는 대여소가 없어 따릉이 구간을 만들지 못함 |
| `bikeMix` | `route_failed` | 따릉이 구간의 카카오 도보, 자전거 경로 조회 실패 |
| `busOnly` | `none` | 버스만 타는 경로가 없음 |
| `busOnly` | `same_as_base` | 가장 빠른 버스 경로가 기본 경로와 같음 |
| `pmOnly` | `route_failed` | 카카오 자전거 경로 조회 실패 |

### 4.8 `legs[]` 구간
| `type` | 필드 |
|---|---|
| `walk` | `seconds`, `distance`, `edge`(`origin`: 출발 도보, `destination`: 도착 도보, `null`: 환승 도보) |
| `bus`, `subway` | `seconds`(카카오 구간 시간, 승차 대기 제외), `waitSeconds`(승차 대기 시간), `distance`, `stops`(정류장, 역 이름 목록, 승차부터 하차까지), `vehicles`(`type`, `name`), `serviceUnknown`(운행 시간을 확인하지 못한 노선이 있는지, `rules.md` 3.4.4), `positions`(노선별 실시간 위치, 4.10) |
| `bike` | `mile`(`first`, `last`, `full`), `seconds`(합계), `replacedSeconds`(바꾸기 전 mile 시간), `toStationSeconds`, `rentSeconds`, `rideSeconds`, `returnSeconds`, `fromStationSeconds`, `rentStation`, `returnStation` |

- `rentStation`: `id`, `name`, `availableBikes`(재고를 확인하지 못하면 `null`), `distance`(따릉이 구간 시작에서의 직선거리)
- `returnStation`: `id`, `name`, `availableRacks`(재고를 확인하지 못하면 `null`), `distance`(따릉이 구간 끝까지의 직선거리)
- `rentStation`, `returnStation`에는 대여소 좌표 `x`, `y`도 있음 (권장 F-16)

### 4.9 경로 좌표 (권장 F-16)
| 위치 | 필드 | 내용 |
|---|---|---|
| `walk`, `bus`, `subway` 구간 | `points` | 구간의 좌표 목록 |
| `bike` 구간 | `toStationPoints`, `ridePoints`, `fromStationPoints` | 대여소까지 도보, 대여소 사이 자전거, 반납 대여소에서 도보의 좌표 목록 |
| `pmOnly` | `points` | 자전거 경로 좌표 목록 |

- 좌표 목록은 `[x, y]` 쌍의 배열. 소수 다섯째 자리(약 1m)로 맞춤
- 출처: 대중교통 구간은 카카오 대중교통 응답의 `path.points`, 도보, 자전거는 카카오 도보, 자전거 응답의 구간 좌표 (`datasource.md` 5장, 6장)
- 카카오 응답에 좌표가 없거나 형식이 다르면 빈 배열. 시간, 거리 계산에는 영향 없음
- 따릉이 구간에 들어간 대중교통 구간 좌표는 없음 (바꾼 mile은 `bike` 구간 하나)

### 4.10 `positions[]` 실시간 위치 (권장 F-26)
| 필드 | 형식 | 내용 |
|---|---|---|
| `vehicle` | 문자열 | 노선 이름 (`vehicles[].name`, 겹치는 이름은 한 번) |
| `status` | 문자열 | `live`(실시간 위치 있음), `none`(다가오는 차량 없음), `timetable`(시간표로 구한 다음 출발), `unknown`(알 수 없음) |
| `stopsAway` | 정수 또는 `null` | `live`일 때 승차 정류장, 역까지 남은 정류장, 역 수. 0은 도착해 있음 |
| `nextDeparture` | 시각 또는 `null` | `timetable`일 때 승차 예상 시각 이후 첫 열차의 출발 시각 |
| `observedAt` | 시각 또는 `null` | 위치 정보가 만들어진 시각 (`live`, `none`) |

- 기본 경로, 버스 전용 경로와 따릉이 포함 경로의 남은 대중교통 구간에 들어감
- 소요 시간 값(`totalSeconds` 등)에는 반영하지 않음 (`rules.md` 11.3)

## 5. 응답 예 (요약)
```json
{
  "fetchedAt": "2026-10-20T08:20:05+09:00",
  "transit": { "status": "ok" },
  "bikeData": { "status": "ok", "fetchedAt": "2026-10-20T08:20:03+09:00" },
  "base": {
    "routeIndex": 0,
    "type": "subway",
    "totalSeconds": 1560,
    "totalDistance": 4000,
    "transfers": 0,
    "fare": 1550,
    "waitSeconds": 180,
    "edgeWalkKnown": true,
    "legs": [
      { "type": "walk", "seconds": 480, "distance": 650, "edge": "origin" },
      { "type": "subway", "seconds": 480, "waitSeconds": 180, "distance": 2800, "stops": ["건대입구", "성수", "뚝섬", "한양대"], "vehicles": [{ "type": "수도권", "name": "2호선" }] },
      { "type": "walk", "seconds": 420, "distance": 550, "edge": "destination" }
    ],
    "pmSaving": { "firstSeconds": 324, "lastSeconds": 288, "totalSeconds": 612 }
  },
  "bikeMix": {
    "kind": "full",
    "conditions": { "first": false, "second": null, "third": true },
    "totalSeconds": 1110,
    "transfers": 0,
    "stockKnown": true,
    "legs": [
      {
        "type": "bike", "mile": "full", "seconds": 1110, "replacedSeconds": 1560,
        "toStationSeconds": 240, "rentSeconds": 60, "rideSeconds": 720, "returnSeconds": 30, "fromStationSeconds": 60,
        "rentStation": { "id": "ST-0000", "name": "예시 대여소", "availableBikes": 2, "distance": 260 },
        "returnStation": { "id": "ST-0001", "name": "예시 반납 대여소", "availableRacks": 5, "distance": 70 }
      }
    ]
  },
  "busOnly": null,
  "pmOnly": { "totalSeconds": 780, "totalDistance": 3400 },
  "notes": [ { "target": "busOnly", "reason": "none" } ]
}
```
- 값은 예시. 대여소 ID, 이름은 가상 값

## 6. 개인정보 기준
| 값 | 받는 곳 | 처리 |
|---|---|---|
| 주소, 장소 검색어 | `/api/address/search` | 카카오 주소 검색, 키워드 장소 검색에 전달만 함. 저장, 로그 기록 없음 |
| 출발지, 도착지 좌표 | `/api/recommend` | 카카오 경로 조회와 대여소 선택에만 사용. 메모리 캐시(`tech_stack.md` 3.5) 외에 저장하지 않고 로그에 남기지 않음 |
| 기준 도착 시각(`arriveBy`) | `/api/recommend` | 첫차, 막차 판단에만 사용. 저장, 로그 기록 없음 (2026-10-20 사용자 결정, D-35) |

- 위 표 외의 값(장소 이름, 설정)은 서버로 보내지 않음. 목표 도착 시각과 여유 시간은 따로 보내지 않고 둘을 뺀 기준 도착 시각만 보냄
- 경로 지도(권장 F-16)는 브라우저가 카카오 지도 SDK와 지도 그림을 직접 받음. 이때 카카오는 지도에 보이는 지역을 알 수 있음. 서버를 거치지 않는 유일한 외부 호출 (2026-10-20 사용자 허용, `frontend/CLAUDE.md` 1장)
- 쿠키, 세션, 사용자 식별 값을 만들지 않음
- 서버 로그에는 요청 주소(`/api/recommend` 등), 응답 코드, 처리 시간, 외부 호출 결과 상태만 기록
