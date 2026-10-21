# 데이터 출처

## 0. 문서 정보
- 작성일: 2026-10-19
- 최종 수정: 2026-10-20
- 상태: 공식 문서 기준 정리. DS-1 ~ DS-5 실제 호출 확인 (2026-10-19, 9장)
- 근거: 카카오 개발자 문서(카카오맵 REST API, 쿼터), 서울 열린데이터광장 안내 페이지
- 확인 표기
  | 표기 | 의미 |
  |---|---|
  | 문서 확인 | 공식 문서에서 확인 |
  | 호출 확인 | 발급받은 인증키로 실제 호출해 확인 |
  | 미확인 | 공식 문서에 없거나 아직 호출해 보지 않음 |
- 인증키 값은 이 문서와 코드에 적지 않음. 환경 변수 이름은 10장

## 1. 데이터 원칙
| 원칙 | 내용 |
|---|---|
| 경로 출처 | 대중교통 경로는 카카오맵 대중교통 경로 API만 사용 |
| PM 경로 | 따릉이 구간과 PM 전용 경로는 카카오 도보, 자전거 경로 API 사용. 킥보드는 외부 데이터를 쓰지 않음 (`rules.md` 4장) |
| 따릉이 재고 | 서울 공공자전거 실시간 대여정보 사용 |
| 실시간 도착 정보 | 소요 시간에는 반영하지 않음. 버스, 지하철 위치는 카드 표시에만 사용 (권장 F-26) |
| 개인정보 | 외부 서비스에 보내는 값은 좌표와 주소, 장소 검색어뿐. 서버는 이 값을 저장하거나 기록에 남기지 않음 |

## 2. 데이터 목록
| ID | 데이터 | 제공처 | 쓰임 | 하루 무료 사용량 | 확인 |
|---|---|---|---|---|---|
| DS-1 | 주소 검색 `/v2/local/search/address` | 카카오 | 주소 → 좌표 (F-01) | 100,000 | 호출 확인 |
| DS-7 | 키워드 장소 검색 `/v2/local/search/keyword` | 카카오 | 주소 검색 결과가 없을 때 장소 이름 → 좌표 (F-01) | 100,000 | 호출 확인 |
| DS-2 | 대중교통 경로 `/v2/routing/publictraffic` | 카카오 | 기본 경로, 버스 전용 경로, 구간별 거리, 시간 (F-03, F-04, F-06) | 1,000 | 호출 확인 |
| DS-3 | 도보 경로 `/v2/routing/walk` | 카카오 | 기본, 버스 전용 경로의 출발 도보, 도착 도보 (F-03, F-04, F-06), 따릉이 구간의 대여소까지, 대여소에서의 도보 시간, 따릉이 조건 1의 첫 역까지, 마지막 역에서의 도보 시간 (F-05) | 1,000 | 호출 확인 |
| DS-4 | 자전거 경로 `/v2/routing/bicycle` | 카카오 | 따릉이 구간의 자전거 이동 시간 (F-05), PM 전용 경로 (F-07) | 1,000 | 호출 확인 |
| DS-5 | 공공자전거 실시간 대여정보 `bikeList` | 서울 열린데이터광장 OA-15493 | 대여소 위치, 대여 가능 대수, 거치대 수 (F-05) | 문서에 없음 | 호출 확인 |
| DS-8 | 평일 공휴일 목록 `backend/data/holidays/{연도}.csv` | 사용자 직접 입력 | 첫차/막차 시간표의 요일 구분 (7.1) | - | 사용자 제공 |
| DS-9 | 서울 버스 노선정보조회 `busRouteInfo/getBusRouteList` | 서울특별시 (data.go.kr 15000193) | 버스 노선 기점 첫차, 막차, 노선 길이 (`rules.md` 3.4) | 1,000 (개발 계정) | 문서 확인 |
| DS-10 | 경기 버스노선 조회 v2 `getBusRouteListv2`, `getBusRouteInfoItemv2`, `getBusRouteStationListv2` | 경기도 (data.go.kr 15080662) | 서울 데이터에 없는 버스 노선의 기점 첫차, 막차, 경유 정류소 | 1,000 (개발 계정) | 문서 확인 |
| DS-11 | 인천 버스노선 조회 `getBusRouteNo` | 인천광역시 (data.go.kr 15058487) | 서울, 경기 데이터에 없는 버스 노선의 기점 첫차, 막차, 노선 길이 | 1,000 (개발 계정) | 문서 확인 |
| DS-12 | 서울 지하철 첫차, 막차 `SearchFirstAndLastTrainbyLineServiceNew` | 서울 열린데이터광장 OA-15492 | 1 ~ 9호선 역별, 방향별, 요일별 첫차, 막차 | 문서에 없음 | 호출 확인 (공개 샘플 키) |
| DS-13 | 지하철 시간표 `backend/data/rail/{노선 이름}.csv` | 사용자 직접 입력 | 1 ~ 9호선 밖 노선의 첫차, 막차 (7.4) | - | 사용자 제공 예정 |
| DS-14 | 서울 버스 위치 `buspos/getBusPosByRtid`, 경유 정류소 `busRouteInfo/getStaionByRoute` | 서울특별시 (data.go.kr 15000332, 15000193) | 버스 실시간 위치 (권장 F-26) | 1,000 (개발 계정) | 문서 확인 |
| DS-15 | 경기 버스 위치 `buslocationservice/v2/getBusLocationListv2` | 경기도 (data.go.kr 15080648) | 버스 실시간 위치 (권장 F-26) | 1,000 (개발 계정) | 문서 확인 |
| DS-16 | 인천 버스 위치 `busLocationService/getBusRouteLocation`, 경유 정류소 `busRouteService/getBusRouteSectionList` | 인천광역시 (data.go.kr 15059206, 15058487) | 버스 실시간 위치 (권장 F-26) | 1,000 (개발 계정) | 문서 확인 |
| DS-17 | 서울 지하철 실시간 도착정보 `realtimeStationArrival` | 서울 열린데이터광장 OA-12764 | 지하철 실시간 위치 (권장 F-26) | 문서에 없음 | 호출 확인 (C-13) |
| DS-18 | 서울 지하철 역별 시간표 `SearchSTNTimeTableByIDService`, 역 코드 `SearchSTNBySubwayLineInfo` | 서울 열린데이터광장 OA-101 | 실시간 정보가 없는 1 ~ 9호선 역의 다음 출발 시각 (권장 F-26) | 문서에 없음 | 호출 확인 (공개 샘플 키) |
| DS-19 | 서울 버스 노선별 경유 정류소 `busRteInfo` | 서울 열린데이터광장 OA-1095 | 서울 버스 노선 번호 → 노선 ID, 경유 정류소 순번과 좌표 (권장 F-26). DS-9를 쓰지 못할 때 서울 노선인지 확인 (`rules.md` 3.4.3) | 문서에 없음 | 호출 확인 (2026-10-21) |
| DS-6 | Kakao Maps JavaScript SDK | 카카오 | 경로 지도 표시 (권장 F-16). 브라우저가 직접 불러옴 | 300,000 | 문서 확인 |

- 카카오 사용량 출처: https://developers.kakao.com/docs/ko/getting-started/quota
  - 무료 사용량은 개발자 계정에서 처음 활성화한 앱에만 제공
  - 초과분 요금(문서 기준): 대중교통, 도보, 자전거 경로 건당 10원, 주소 검색 건당 0.5원. 유료 사용 설정 전에는 과금되지 않음 (C-7)

## 3. 카카오 공통
- 인증: 요청 헤더 `Authorization: KakaoAK {REST API 키}` (문서 확인)
- 키 종류: REST API 키. 서버에서만 사용하고 화면에 보내지 않음
- 좌표: 기본 WGS84, 경도가 `x`, 위도가 `y` (문서 확인)
- 초당 호출 제한: 문서에 없음 (C-8)

## 4. DS-1 주소 검색
- 요청: `GET https://dapi.kakao.com/v2/local/search/address.json`
  | 변수 | 내용 |
  |---|---|
  | `query` (필수) | 지번 또는 도로명 주소 검색어 |
  | `analyze_type` | `similar`(기본, 부분 일치 허용) / `exact` |
  | `page` | 1 ~ 45 |
  | `size` | 1 ~ 30, 기본 10 |
- 사용 항목 (`documents`)
  | 항목 | 쓰임 |
  |---|---|
  | `address_name` | 후보 목록 표시 |
  | `address_type` | `REGION`, `ROAD`, `REGION_ADDR`, `ROAD_ADDR` |
  | `road_address.address_name`, `road_address.building_name` | 도로명 주소, 건물 이름 표시 |
  | `address.address_name` | 지번 주소 표시 |
  | `x`, `y` | 저장할 좌표 |
- `meta`: `total_count`, `pageable_count`, `is_end`

### 4.1 DS-7 키워드 장소 검색
- 요청: `GET https://dapi.kakao.com/v2/local/search/keyword.json`
  | 변수 | 내용 |
  |---|---|
  | `query` (필수) | 장소 이름 검색어 |
  | `page` | 1 ~ 45 |
  | `size` | 1 ~ 15, 기본 15. 서버는 10 사용 (주소 검색과 같은 쪽 크기) |
  | `x`, `y`, `radius`, `rect`, `sort`, `category_group_code` | 사용하지 않음 (위치를 보내지 않음) |
- 사용 항목 (`documents`)
  | 항목 | 쓰임 |
  |---|---|
  | `place_name` | 후보 목록 첫 줄, 이름 칸 자동 채우기 |
  | `road_address_name` | 도로명 주소. 빈 문자열이면 없는 것으로 처리 (C-10) |
  | `address_name` | 지번 주소 |
  | `x`, `y` | 저장할 좌표 (문자열) |
- `meta`: `total_count`, `pageable_count`(최대 45), `is_end`

## 5. DS-2 대중교통 경로
- 요청: `GET https://dapi.kakao.com/v2/routing/publictraffic`
  | 변수 | 내용 |
  |---|---|
  | `start_x`, `start_y` (필수) | 출발지 좌표 |
  | `end_x`, `end_y` (필수) | 도착지 좌표 |
  | `s_name`, `e_name` | 출발지, 도착지 명칭. 보내지 않음 (기본값 "출발", "도착") |
- 출발 시각, 정렬 기준, 최소 환승 등 선택 변수는 문서에 없음
- 응답
  | 위치 | 항목 | 쓰임 |
  |---|---|---|
  | 최상위 | `status` | `OK`, `STARTNODES_NULL`, `ENDNODES_NULL`, `EQUAL_POINTS`, `INVALID_REQUEST`, `NO_RESULTS` |
  | 최상위 | `properties`의 `total`, `bus`, `subway`, `busAndSubway`(경로 유형별 수), `landingURL` | `landingURL`은 권장 F-19 카카오맵 열기 |
  | `routes[].properties` | `type`(`BUS`, `SUBWAY`, `BUS_AND_SUBWAY`), `totalDistance`(m), `totalTime`(초), `transfers`, `fare`(원. 단일 요금은 `value`, 범위 요금은 `min`, `max`. 서버는 `value`, 없으면 `min` 사용. 9장 C-9) | 기본 경로, 버스 전용 경로 선택 (`rules.md` 3장, 6장) |
  | `routes[].steps[].properties` | `type`(`BUS`, `SUBWAY`, `WALKING`), `guidance`, `distance`(m), `time`(초) | 구간 구성, First, Last mile 판정, PM 절감 시간 |
  | `routes[].steps[].properties.stops[]` | `name` (정류장 이름만). 도보 구간에도 있음 | 화면 표시 |
  | `routes[].steps[].properties.vehicles[]` | `type`(간선, 지선, 일반 등), `name` | 노선 표시. 같은 구간을 다니는 노선을 모두 담으며 심야 노선도 시간대와 관계없이 포함 |
  | `routes[].steps[].path.points` | `[x, y]` 좌표 목록 | 첫 승차 지점, 마지막 하차 지점 좌표 (`rules.md` 3.1), 권장 F-16 지도 선 |
- `steps`에는 출발지 → 첫 승차 정류장, 마지막 하차 정류장 → 도착지의 도보가 들어 있지 않음. 이 두 도보의 시간, 거리는 `totalTime`, `totalDistance`에만 포함 (9장 C-3, C-4)
- 경로 순서는 총 소요 시간 순이 아니며, 첫 번째 경로가 카카오맵 앱의 첫 번째 추천 경로와 같음 (9장 C-2)
- 문서에 없는 것: 정류장 좌표, 정류장, 노선 ID, 실시간 도착 정보, 최대 경로 수, 지원 지역

## 6. DS-3 도보 경로, DS-4 자전거 경로
- 요청: `GET https://dapi.kakao.com/v2/routing/walk`, `GET https://dapi.kakao.com/v2/routing/bicycle`
  | 변수 | 내용 |
  |---|---|
  | `start_x`, `start_y`, `end_x`, `end_y` (필수) | 출발, 도착 좌표 |
  | `via_x`, `via_y` | 경유지 최대 5개. 사용하지 않음 |
  | `route_mode` | 도보: `BROAD_FIRST`(기본), `SHORTEST`, `ACCESSIBLE` / 자전거: `BIKE_ONLY`(기본), `SHORTEST`, `ACCESSIBLE` |
- 사용하는 방식
  | 쓰임 | API | `route_mode` |
  |---|---|---|
  | 기본, 버스 전용 경로의 출발 도보, 도착 도보 (`rules.md` 3.2) | 도보 | 기본값 `BROAD_FIRST` |
  | 따릉이 구간의 도보, 조건 1의 첫 역까지, 마지막 역에서의 도보 | 도보 | 기본값 `BROAD_FIRST` |
  | 따릉이 구간의 자전거 | 자전거 | `SHORTEST` (사용자 결정, `rules.md` 5.2) |
  | PM 전용 경로 | 자전거 | `SHORTEST` (사용자 결정) |
- 응답 (두 API 같은 형식)
  | 위치 | 항목 | 쓰임 |
  |---|---|---|
  | 최상위 | `status` | `OK`, `SAME_POINT`, `START_LINK_NOT_FOUND`, `END_LINK_NOT_FOUND`, `TOO_MANY_SEARCH_LINK`, `TOO_FAR_AWAY`, `ROUTE_RESULT_NOT_FOUND` |
  | `route.properties` | `totalDistance`(m), `totalTime`(초), `landingUrl` | 따릉이 구간 시간 (`rules.md` 5.2), PM 전용 경로 (`rules.md` 7장) |
  | `route.legs[].steps[]` | `distance`, `time`, `guidance`, `path.points` | 권장 F-16 지도 선. `path.points`는 `[x, y]` 좌표 목록이며, 구간 좌표를 순서대로 이어 붙여 사용 (C-11) |
- `OK` 외의 상태는 모두 조회 실패로 처리 (`rules.md` 10장)
- 호출 수 줄이기: 같은 두 좌표 사이의 도보, 자전거 경로는 자주 바뀌지 않으므로 서버가 저장해 두고 다시 씀 (`tech_stack.md` 3.5)

## 7. DS-5 공공자전거 실시간 대여정보
- 요청: `GET http://openapi.seoul.go.kr:8088/{KEY}/json/bikeList/{시작}/{끝}/`
- 1회 최대 1,000건. 전체 대여소가 2,716곳(2026-10-19)이라 3번 나누어 받음
- 응답 구조: `rentBikeStatus`의 `list_total_count`(이번 응답에 담긴 건수, 전체 건수가 아님), `RESULT`(`CODE`, `MESSAGE`. 정상은 `INFO-000`), `row`(대여소 목록)
- 모든 값이 문자열이므로 숫자로 바꿔 사용
- 사용 항목
  | 항목 | 의미 | 쓰임 |
  |---|---|---|
  | `stationId` | 대여소 ID | 구분 |
  | `stationName` | 대여소 이름 | 화면 표시 |
  | `stationLatitude`, `stationLongitude` | 대여소 위도, 경도 | 반경 안 대여소 찾기 |
  | `parkingBikeTotCnt` | 세워진 자전거 수 = 대여 가능 대수 | `rules.md` 5.1 |
  | `rackTotCnt` | 거치대 수 | 반납 가능 거치대 수 계산 |
  | `shared` | 거치율(%) = 세워진 자전거 수 ÷ 거치대 수 × 100 | 사용하지 않음 |
- 반납 가능 거치대 수 = `rackTotCnt` − `parkingBikeTotCnt`, 음수이면 0 (거치대보다 많이 세워 둔 대여소가 전체의 약 32%)
- 이 데이터에 대여소 좌표가 있어 별도의 대여소 기준 정보 파일 없이 동작 (C-6)
- 출처: https://data.seoul.go.kr/dataList/OA-15493/A/1/datasetView.do

### 7.1 DS-8 평일 공휴일 목록
- 대중교통 첫차/막차를 판단할 때 그날이 공휴일인지 확인하는 데 사용 (`masterplan.md` D-39)
- 외부 API 대신 사용자가 연도마다 직접 만들어 넣는 파일 (2026-10-20 2026년, 2027년 제공)
- 위치와 이름: `backend/data/holidays/{연도}.csv` (예: `2026.csv`). 다음 해 파일은 같은 폴더에 추가
- 형식
  | 항목 | 내용 |
  |---|---|
  | 인코딩 | UTF-8 (BOM 있음), 줄바꿈 CRLF. 서버는 BOM을 무시하고 읽음 |
  | 첫 줄 | 열 이름 `MM-DD,공휴일 이름` |
  | `MM-DD` | 월-일. 연도는 파일 이름의 연도 |
  | `공휴일 이름` | 예: 신정, 설날, 삼일절 대체공휴일 |
- 평일(월 ~ 금)인 공휴일만 들어 있음. 토요일, 일요일은 요일로 판단
- 그 해 파일이 없으면 공휴일이 없는 것으로 보지 않음. 요일 구분이 필요한 데이터(DS-10, DS-12, DS-13)는 평일이면 운행 시간 정보 없음으로 처리 (`rules.md` 3.4.4)

### 7.2 DS-9 ~ DS-11 버스 노선 첫차, 막차
- 조사일: 2026-10-20. 공식 명세(data.go.kr 상세 기능) 기준. 실제 호출은 인증키 발급 후 확인 (C-12)
- 인증키: data.go.kr 일반 인증키 하나로 세 API 사용. API마다 활용 신청 필요 (자동 승인)
- data.go.kr 중계 서버의 오류 응답(`OpenAPI_ServiceResponse`)은 HTTP 200으로 와도 조회 실패로 처리하고 캐시하지 않음. 노선 없음으로 보지 않음 (예: 인천 `HTTP_ERROR` 04, 2026-10-21)
- 카카오 구간의 노선 이름(`vehicles[].name`)을 노선 번호로 찾음. 서울 → 경기 → 인천 순서로, 노선 번호가 정확히 같은 것만 사용 (`rules.md` 3.4.3)

| ID | 요청 | 사용 항목 | 비고 |
|---|---|---|---|
| DS-9 | `GET http://ws.bus.go.kr/api/rest/busRouteInfo/getBusRouteList?serviceKey=&strSrch={노선 번호}&resultType=json` | `busRouteId`, `busRouteNm`, `routeType`(1 공항, 2 마을, 3 간선, 4 지선, 5 순환, 6 광역, 7 인천, 8 경기, 9 폐지, 0 공용), `length`(km), `firstBusTm`, `lastBusTm`(금일 첫차, 막차, 14자리) | 부분 일치 검색이므로 `busRouteNm`이 같은 행만 사용. 서울을 지나는 인천, 경기 노선도 포함. 요일 구분 없이 그날 값 |
| DS-10 | `GET https://apis.data.go.kr/6410000/busrouteservice/v2/getBusRouteListv2?serviceKey=&keyword={노선 번호}&format=json` | `routeId`, `routeName`, `regionName` | 같은 번호가 여러 시군에 있을 수 있음 |
| DS-10 | `.../getBusRouteInfoItemv2?serviceKey=&routeId=&format=json` | `upFirstTime`, `upLastTime`(평일 기점), `satUp*`(토요일), `sunUp*`(일요일), `weUp*`(공휴일) | 종점(`down*`) 시각은 사용하지 않음 (D-37 기점 기준) |
| DS-10 | `.../getBusRouteStationListv2?serviceKey=&routeId=&format=json` | `stationSeq`, `stationName`, `x`, `y`, `turnYn` | 노선 길이(정류소 사이 직선거리의 합)와 같은 번호 노선 고르기에 사용 |
| DS-11 | `GET https://apis.data.go.kr/6280000/busRouteService/getBusRouteNo?serviceKey=&routeNo={노선 번호}&pageNo=1&numOfRows=10&_type=json` | `ROUTEID`, `ROUTENO`, `ROUTELEN`(m), `FBUS_DEPHMS`, `LBUS_DEPHMS`(기점 첫차, 막차 출발 hhmm) | 요일 구분 없음 |

- 서울 노선의 `getStaionByRoute`에는 정류소별 구간 거리(`fullSectDist`), 구간 속도(`sectSpd`), 회차지 여부(`transYn`)가 있으나 기점 기준 판단(D-37)에서는 사용하지 않음
- 기타 지역: 국토교통부 TAGO 버스노선정보(data.go.kr 15098529, `startvehicletime`, `endvehicletime`)가 있으나 서울이 없고 요일 구분이 없어 사용하지 않음
- 서울 열린데이터광장의 서울 버스 노선 페이지(OA-1095)에는 2025-09-26 이후 신규 인증키 발급 중단 공지가 있음. data.go.kr 15000193은 자동 승인으로 표시

### 7.3 DS-12 서울 지하철 첫차, 막차
- 요청: `GET http://openapi.seoul.go.kr:8088/{KEY}/json/SearchFirstAndLastTrainbyLineServiceNew/1/1000/{호선 숫자}/{방향}/{요일}/`
  | 변수 | 값 |
  |---|---|
  | 호선 숫자 | 1 ~ 9 |
  | 방향 | 1 상행, 내선 / 2 하행, 외선 |
  | 요일 | 1 평일 / 2 토요일 / 3 휴일 |
  | 역 코드 | 생략하면 그 호선 그 방향 전체 역 (2호선 한 방향 51행) |
- 사용 항목: `STTN`(역 이름, "역" 없음), `FSTT_HRM`(첫차 HHMMSS), `LSTTM_HRM`(막차 HHMMSS, 자정 이후는 24 이상, 예: "245000")
- 인증키: 지금 쓰는 열린데이터광장 일반 인증키 (DS-5와 같음)
- 1 ~ 9호선만 있음. 신분당선, 경의중앙선, 공항철도, 수인분당선, GTX-A 등은 없음 (조사 2026-10-20). 이 노선들은 DS-13

### 7.4 DS-13 사용자 지하철 시간표
- 1 ~ 9호선 밖 노선의 첫차, 막차를 사용자가 직접 만들어 넣는 파일 (D-38)
- 위치와 이름: `backend/data/rail/{노선 이름}.csv`. 노선 이름은 카카오 응답의 노선 이름 그대로 (예: `신분당선.csv`)
- 형식: UTF-8(BOM 있어도 됨), 첫 줄 `역,다음 역,요일,첫차,막차`
  | 열 | 내용 |
  |---|---|
  | 역 | 승차역 이름. "역" 없이 |
  | 다음 역 | 그 방향으로 바로 다음 역 이름. 방향을 정하는 데 사용 |
  | 요일 | `평일`, `토요일`, `휴일`(일요일, 공휴일) |
  | 첫차, 막차 | 그 역 출발 시각 `HH:MM`. 자정을 넘으면 `24:05`처럼 24 이상 |

### 7.5 DS-14 ~ DS-18 실시간 위치 (권장 F-26)
- 조사일: 2026-10-20. 버스는 공식 명세 기준(실제 호출은 키 반영 후, C-13), 지하철은 실제 호출 확인
- 노선 번호 → 노선 ID, 경유 정류소 목록은 하루 캐시. 실시간 위치는 캐시하지 않음(한 요청 안의 중복만 20초 보관)
- 서울 버스의 노선 ID, 경유 정류소는 DS-19로 구함 (2026-10-21 사용자 결정, D-51). DS-14 위치만 data.go.kr 키 사용

| ID | 요청 | 사용 항목 |
|---|---|---|
| DS-14 | `GET http://ws.bus.go.kr/api/rest/buspos/getBusPosByRtid?serviceKey=&busRouteId=&resultType=json` | `sectOrd`(구간 순번), `stopFlag`(1 도착, 0 운행 중), `dataTm`(제공 시각) |
| DS-19 | `GET http://openapi.seoul.go.kr:8088/{KEY}/json/busRteInfo/{시작}/{끝}/` | `ROUTE_ID`(DS-14 노선 ID와 같은 체계), `RTE_NM`(노선 번호), `SN`(정류소 순번), `XCRD`, `YCRD`(경위도) |
| DS-15 | `GET https://apis.data.go.kr/6410000/buslocationservice/v2/getBusLocationListv2?serviceKey=&routeId=&format=json` | `stationSeq`(정류소 순번), `stateCd`(0 교차로 통과, 1 정류소 도착, 2 정류소 출발) |
| DS-16 | `GET https://apis.data.go.kr/6280000/busLocationService/getBusRouteLocation?serviceKey=&routeId=&pageNo=1&numOfRows=100` | `LATEST_STOPSEQ`(최근 정류소 순번), `DIRCD` |
| DS-16 | `.../busRouteService/getBusRouteSectionList?routeId=` | `BSTOPSEQ`, `BSTOPNM` (좌표가 TM 좌표계라 정류소 이름으로 맞춤) |
| DS-17 | `GET http://swopenapi.seoul.go.kr/api/subway/{KEY}/json/realtimeStationArrival/0/50/{역 이름}` | `subwayId`(노선 ID), `trainLineNm`("성수행 - 역삼방면"), `ordkey`(셋째 ~ 다섯째 글자가 남은 역 수, 000은 도착), `arvlMsg2`("[3]번째 전역 (OO)", "전역 도착" 등), `recptnDt`(생성 시각), `statnId`(승차역 ID), `statnFid`, `statnTid`(열차 진행 방향의 이전, 다음 역 ID) |
| DS-18 | `GET http://openapi.seoul.go.kr:8088/{KEY}/json/SearchSTNBySubwayLineInfo/1/50/%20/{역 이름}/` | `STATION_CD`, `LINE_NUM`("02호선"), `FR_CODE`(외부 코드, 예: 9호선 노량진 "917") |
| DS-18 | `.../SearchSTNTimeTableByIDService/1/1000/{역 코드}/{요일 1 ~ 3}/{방향 1 ~ 2}/` | `LEFTTIME`(출발 시각 HH:MM:SS) |

- DS-17 인증키: 열린데이터광장 실시간 지하철 인증키(일반 인증키와 별도). 샘플 키는 '서울'역만 조회됨
- DS-17 범위: 서울 안의 역만. 서울 밖 노선(경의중앙선, 공항철도, 신분당선 등)도 서울 안 역에서는 나옴. 광명, 서동탄, 춘천 등 서울 밖 역은 없음 (OA-12764 안내)
- DS-17 역 ID는 노선 ID + 외부 코드 여섯 자리(예: 9호선 노량진 `1009000917`, 1호선 시청 `1001000132`). 2026-10-21 실제 호출로 확인
- DS-17 노선 ID: 1001 ~ 1009(1 ~ 9호선), 1063 경의중앙선, 1065 공항철도, 1077 신분당선은 호출 확인. 1067 경춘선, 1075 수인분당선, 1081 경강선, 1092 우이신설선, 1093 서해선, 1032 GTX-A는 미확인
- 카카오 지하철 구간의 노선 목록에는 같은 노선이 일반, 급행으로 겹쳐 들어 있음 (예: 수인분당선 일반, 급행)
- 버스 노선 번호 조회(DS-10, DS-11)는 첫차, 막차와 실시간 위치가 따로 하루 캐시하므로 노선 번호마다 하루 2건
- DS-19 키: 열린데이터광장 일반 인증키(DS-5와 같음). 인코딩 키 구분 없음
- DS-19 범위: 전체 41,688행(2026-10-21). 노선 번호, 노선 ID로 거르는 요청이 없어(주소 끝에 붙여도 무시됨) 하루 한 번 전체를 1,000행씩 42쪽으로 나눠 받음. 실제 0.7초
- DS-19에는 첫차, 막차, 노선 길이가 없음. DS-9를 쓰지 못하면 서울 버스는 운행 시간 정보 없음 (`rules.md` 3.4.4)
- DS-14 `sectOrd`는 차량이 마지막으로 지난 정류소의 DS-19 `SN`과 같은 기준. 606번 차량 6대의 좌표가 모두 `SN` = `sectOrd` 정류소와 다음 정류소 사이에 있음 (2026-10-21 실제 호출)

## 8. 하루 호출량 추정 (사용자 1명)
- 가정: 앱 열기와 새로고침 하루 20회, 한 번에 따릉이 구간을 최대 3개(First mile, Last mile, 전 구간) 만듦
  | 데이터 | 1회 최대 호출 | 하루 최대 (저장 재사용 없음) | 무료 사용량 |
  |---|---|---|---|
  | DS-2 대중교통 경로 | 1 | 20 | 1,000 |
  | DS-3 도보 경로 | 12 (출발, 도착 도보 2 × 경로 2 + 따릉이 구간 3 × 도보 2 + 조건 1 판단 2) | 240 | 1,000 |
  | DS-4 자전거 경로 | 4 (따릉이 구간 3 + PM 전용 1) | 80 | 1,000 |
  | DS-5 따릉이 | 3 (전체 목록) | 60 | 문서에 없음 |
  | DS-1 주소 검색 | 등록할 때만 | 수 회 | 100,000 |
  | DS-7 키워드 장소 검색 | 등록할 때 주소 검색 결과가 없을 때만 | 수 회 | 100,000 |
| DS-6 지도 SDK | 지도 화면을 열 때 1 | 수 회 | 300,000 |
| DS-9 서울 버스 노선 | 처음 보는 버스 노선 번호마다 1 | 수 ~ 수십 (같은 날 같은 번호는 캐시) | 1,000 |
| DS-10 경기 버스 노선 | 서울에서 찾지 못한 번호마다 목록 1 + 같은 번호 노선마다 2 | 수 ~ 수십 | 1,000 |
| DS-11 인천 버스 노선 | 서울, 경기에서 찾지 못한 번호마다 1 | 수 회 | 1,000 |
| DS-12 서울 지하철 첫차, 막차 | 처음 보는 호선, 요일마다 2 (방향 2개) | 2 ~ 10 | 문서에 없음 |
| DS-14 ~ DS-16 버스 위치 | 열 때마다 구간 노선마다 1 (+ 처음 보는 경기, 인천 노선의 경유 정류소 1) | 20회 × 노선 수 (예: 노선 3개면 60) | 1,000 (지역별) |
| DS-19 서울 버스 노선별 경유 정류소 | 그날 처음 서울 버스를 찾을 때 42 (전체) | 42 | 문서에 없음 |
| DS-17 지하철 실시간 도착 | 열 때마다 승차역마다 1 | 20회 × 승차역 수 (예: 2개면 40) | 문서에 없음 |
| DS-18 지하철 역별 시간표 | 실시간 정보가 없을 때만. 역마다 역 코드 1 + 방향 1 ~ 2 (하루 캐시) | 수 회 | 문서에 없음 |
- 집, 회사와 그 주변 대여소는 매일 같으므로 도보, 자전거 경로를 저장해 다시 쓰면 실제 호출은 크게 줄어듦
- 따릉이 목록은 30초 동안 서버 메모리에 두고 다시 씀
- 첫차, 막차 확인은 카카오 응답 순서대로 경로를 검사하다가 쓸 수 있는 경로를 찾으면 멈춤 (`rules.md` 3.4). 노선 정보는 하루 동안 캐시

## 9. 확인 사항
- 확인일: 2026-10-19 17:37 ~ 17:39 (월요일), C-4 재조회 2026-10-20 09:00 (화요일), C-9 2026-10-20 10:30 (화요일), C-10 2026-10-20, C-11 2026-10-20 15:05 (화요일)
- 확인 조합 (지역 안의 공개 건물): 서울 강서구 → 서울 종로구, 경기 성남시 분당구 → 서울 강남구, 경기 용인시 기흥구 → 경기 수원시 권선구
- 확인 도구: `tools/check_api.py` (git 제외)

| 번호 | 사항 | 관련 | 결과 |
|---|---|---|---|
| C-1 | 카카오 REST API 키 발급과 대중교통, 도보, 자전거 경로 API 사용 설정 | 10장 | 완료. 주소 검색, 대중교통, 도보, 자전거 경로 모두 `OK` 응답 |
| C-2 | 대중교통 경로 응답의 실제 형식, 한 번에 오는 경로 수, 첫 번째 경로가 카카오맵 앱의 추천 경로와 같은지 | 5장, `rules.md` 3장 | 형식은 5장에 반영. 경로 수 14 ~ 15개. 경로 순서는 총 소요 시간 순이 아님(분당구 → 강남구 0번 42분, 1번 40분, 강서구 → 종로구 0번 52분, 1번 51분). 첫 번째 경로는 세 조합 모두 카카오맵 앱의 첫 번째 추천 경로와 같음 (2026-10-20 사용자 확인) |
| C-3 | 구간 좌표 목록(`path.points`)에 구간의 시작점, 끝점이 들어 있는지 | `rules.md` 3.1 | 들어 있음. 앞 구간 끝 좌표와 다음 구간 첫 좌표의 거리 0 ~ 4m. 단 첫 구간은 출발지에서 123 ~ 241m 떨어진 정류장에서 시작하고, 마지막 구간은 도착지에서 72 ~ 365m 떨어진 곳에서 끝남. 출발지, 도착지 쪽 도보는 `steps`에 없음 |
| C-4 | 대중교통 `totalTime`에 배차 대기 시간이 들어 있는지, 같은 출발지, 도착지라도 조회 시각에 따라 결과가 달라지는지 | `rules.md` 11.2, 출발 시각 신뢰도, 경로 저장 재사용 여부 | `totalTime` − 구간 시간 합 = 289 ~ 2,997초. 첫 승차, 마지막 하차 정류장이 같은 경로끼리는 노선이 달라도 같은 값(기흥구 → 권선구 9개 경로 467초). `totalDistance` − 구간 거리 합과 거의 비례(약 1초/m). 따라서 이 차이는 빠진 출발지, 도착지 쪽 도보이며 배차 대기 시간은 들어 있지 않은 것으로 판단. 버스 구간 평균 속도 약 15km/h. 2026-10-20 09:00 재조회 결과가 2026-10-19 17:37 결과와 같음(사용자 확인). 조회 시각에 따라 결과가 달라지지 않는 것으로 판단 |
| C-5 | 대중교통 경로의 지원 지역 | `product.md` 6장 | 서울 → 서울, 경기 → 서울, 경기 → 경기 모두 조회됨. 수도권 밖은 미확인 |
| C-6 | `bikeList`의 대여소 이름, 좌표 항목 | 7장 | 7장 항목 이름 그대로 확인. 값은 모두 문자열. 2,716곳 모두 좌표가 서울 범위 안. 대여소 ID 중복 없음 |
| C-7 | 무료 사용량을 넘겼을 때 자동 과금 여부 (유료 API 설정을 하지 않은 경우 차단되는지) | 2장 | 문서 확인: 비즈월렛 생성, 자동 결제 카드 등록, 앱 연결, 유료 사용 설정 "사용 중"을 모두 거친 경우에만 과금. 설정하지 않으면 무료 사용량 초과 후 호출이 오류(`-10`, HTTP 400, 허용된 요청 횟수 초과)로 끝나는 것으로 판단. 개발자 콘솔의 유료 사용 설정은 "사용 안 함" (2026-10-20 사용자 확인) |
| C-8 | 카카오 경로 API의 초당 호출 제한 | 한 번에 동시 호출하는 수 | 문서에 없음. 미확인 |
| C-9 | 대중교통 경로 `fare` 형식 | 5장 | `{value}` 또는 `{min, max}` 두 형식. 강서구 → 종로구 첫 6개 경로 중 4개 `value`, 2개 `min`, `max` |
| C-10 | 키워드 장소 검색 응답 형식 | 4.1 | 문서의 항목 그대로. 좌표는 문자열. `road_address_name`이 빈 문자열인 장소가 있음(강남역 10건 중 1건, 정부서울청사 10건 중 1건). 위치를 보내지 않아도 `distance` 항목은 있음 |
| C-11 | 도보, 자전거 경로 응답의 좌표 형식 (`route.legs[].steps[].path.points`) | 6장, 권장 F-16 | 문서의 형식 그대로. `path.points`는 `[x, y]` 숫자 쌍의 목록. 서울 종로구 → 서울 강서구 확인에서 출발 도보 24개, 도착 도보 11개, 자전거 경로 354개 좌표. 출발 도보의 끝 좌표와 버스 구간의 첫 좌표가 거의 같은 지점(약 1m 차이)으로 이어짐 |
| C-12 | 카카오 구간의 노선 이름과 DS-9 ~ DS-11의 노선 번호 표기가 같은지, DS-10 시각 값 형식, DS-12 역 이름과 카카오 역 이름 | 7.2, 7.3 | 경기 DS-10은 2026-10-21 실제 호출로 노선 번호 표기 일치, 첫차, 막차 판단 동작 확인(성남 311, 3000, 수원 13-4, 720-2, 11-1). DS-9는 활용 신청 미반영(등록되지 않은 서비스키), DS-11은 키는 통과하나 제공 기관 연결 오류(`HTTP_ERROR` 04)로 미확인 |
| C-13 | 버스 위치 API(DS-14 ~ DS-16)의 순번 의미(`sectOrd`, `stationSeq`, `LATEST_STOPSEQ`가 승차 정류장 순번과 같은 기준인지), 지하철 실시간 도착정보 형식 | 7.5 | 지하철 DS-17은 2026-10-20 실제 호출로 7.5 형식 확인(강남역). 서울 DS-14 `sectOrd`는 7.5대로 확인, 경기 DS-15는 실제 호출로 위치 표시 확인(2026-10-21). 인천 DS-16은 제공 기관 연결 오류로 미확인 |

## 10. 인증키
| 키 | 환경 변수 | 발급처 | 쓰는 데이터 | 상태 |
|---|---|---|---|---|
| 카카오 REST API 키 | `KAKAO_REST_API` | developers.kakao.com 앱 설정 | DS-1 ~ DS-4, DS-7 | 발급 완료 (C-1) |
| 열린데이터광장 일반 인증키 | `DATA_SEOUL_GOKR_GENERIC_API` | data.seoul.go.kr | DS-5, DS-12, DS-18, DS-19 | 발급 완료 |
| 공공데이터포털 일반 인증키 | `DATA_GOKR_GENERIC_API` | data.go.kr 활용 신청 (API마다) | DS-9 ~ DS-11, DS-14 ~ DS-16 | 발급 완료 (2026-10-20). 2026-10-21 호출 결과: DS-10, DS-14, DS-15 정상. DS-9 등록되지 않은 서비스키. DS-11, DS-16 제공 기관 연결 오류 |
| 열린데이터광장 실시간 지하철 인증키 | `DATA_SEOUL_GOKR_SUBWAY_API` | data.seoul.go.kr 실시간 지하철 인증키 신청 | DS-17 | 발급 완료 (2026-10-20) |
| 카카오 JavaScript 키 | `KAKAO_JS_API` | developers.kakao.com 앱 설정, 도메인 등록 | DS-6 (권장 F-16) | 발급 완료 (2026-10-20). 도메인 등록은 사용자 관리 |

- 인증키는 `backend/.env`에 적고 환경 변수로 읽음. `.env`는 git에 올리지 않음
- 환경 변수 이름은 2026-10-19 사용자 확인으로 확정
