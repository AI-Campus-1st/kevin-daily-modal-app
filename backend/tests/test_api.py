'''API 테스트 (api_spec.md 3, 4장)

- 엔드포인트마다 정상, no_result, unavailable, 422 응답 형식 확인
- 외부 API는 httpx.MockTransport로 대신하며 실제로 호출하지 않음
- 캐시(tech_stack.md 3.5)와 로그 개인정보 기준(api_spec.md 6장) 확인
'''

import asyncio
import logging
from collections import Counter
from datetime import datetime

import httpx
import pytest
from fastapi.testclient import TestClient

from app import config
from app.cache import TTLCache
from app.clients.bike import BikeClient
from app.clients.kakao import KakaoClient
from app.clients.live import LiveClient
from app.clients.timetable import TimetableClient
from app.geo import distance_m
from app.main import KST, app, now_kst
from tests.samples import (
    DESTINATION,
    ORIGIN,
    bike_page,
    bike_row,
    offset,
    path_response,
    raw_route,
    step,
    subway,
    transit_response,
)

SUBWAY_START = offset(ORIGIN, east_m=1500)
SUBWAY_END = offset(DESTINATION, east_m=-1500)
TEST_KEY = 'test-key-value'
# 테스트의 지금 시각: 2026-10-20(화) 08:00 한국 표준시
NOW = datetime(2026, 10, 20, 8, 0, tzinfo=KST)

BODY = {
    'origin': {'x': ORIGIN[0], 'y': ORIGIN[1]},
    'destination': {'x': DESTINATION[0], 'y': DESTINATION[1]},
}

ADDRESS_OK = {
    'meta': {'total_count': 1, 'pageable_count': 1, 'is_end': True},
    'documents': [
        {
            'address_name': '서울 종로구 세종대로 209',
            'address_type': 'ROAD_ADDR',
            'x': '126.9769',
            'y': '37.5759',
            'address': {'address_name': '서울 종로구 세종로 1-57'},
            'road_address': {
                'address_name': '서울 종로구 세종대로 209',
                'building_name': '정부서울청사',
            },
        }
    ],
}


KEYWORD_EMPTY = {'meta': {'total_count': 0, 'pageable_count': 0, 'is_end': True}, 'documents': []}

# 키워드 장소 검색 응답 (datasource.md 4.1, C-10). 도로명 주소가 빈 장소 포함
KEYWORD_OK = {
    'meta': {'total_count': 50, 'pageable_count': 45, 'is_end': False},
    'documents': [
        {
            'place_name': '정부서울청사 본관',
            'road_address_name': '서울 종로구 세종대로 209',
            'address_name': '서울 종로구 세종로 77-6',
            'x': '126.9752',
            'y': '37.5751',
            'category_group_code': '',
            'distance': '',
        },
        {
            'place_name': '정부서울청사교차로',
            'road_address_name': '',
            'address_name': '서울 종로구 적선동',
            'x': '126.9741',
            'y': '37.5745',
            'category_group_code': '',
            'distance': '',
        },
    ],
}


class Clock:
    '''시간을 직접 옮길 수 있는 시계'''

    def __init__(self):
        self.value = 1000.0

    def __call__(self):
        return self.value


class FakeExternal:
    '''카카오, 따릉이 서버 대신 응답. 호출 수를 셈'''

    def __init__(self):
        self.calls = Counter()
        self.fail = set()  # 연결 실패로 만들 호출 종류
        self.address = ADDRESS_OK
        self.keyword = KEYWORD_EMPTY
        self.transit = transit_response(
            raw_route('SUBWAY', [subway(900, SUBWAY_START, SUBWAY_END)])
        )
        self.bike_rows = [
            bike_row('ST-O', offset(ORIGIN, east_m=50)),
            bike_row('ST-S1', offset(SUBWAY_START, north_m=60)),
            bike_row('ST-S2', offset(SUBWAY_END, north_m=60)),
            bike_row('ST-D', offset(DESTINATION, east_m=50)),
        ]
        # 첫차, 막차 (datasource.md 7.2, 7.3). 2호선 A역 → B역 방향은 1
        self.subway_rows = {
            '1': [subway_row('A역', '053000', '243000'), subway_row('B역', '053200', '243200')],
            '2': [subway_row('B역', '053000', '243000'), subway_row('A역', '053200', '243200')],
        }
        self.seoul_buses = [seoul_bus('101', '043000', '233000', 20)]
        self.gyeonggi_buses = []  # (노선 정보, 경유 정류소 좌표 목록)
        self.incheon_buses = []
        self.incheon_error = False  # 참이면 인천 API가 data.go.kr 오류 XML(HTTP 200)을 보냄
        # 실시간 위치 (datasource.md 7.5)
        self.seoul_stations = {}  # 노선 ID → [(순번, 경도, 위도)]
        self.seoul_positions = {}  # 노선 ID → [(구간 순번, 정류소 도착 여부)]
        self.gyeonggi_positions = {}  # 노선 ID → [(정류소 순번, 상태 코드)]
        self.incheon_sections = {}  # 노선 ID → [(정류소 순번, 정류소 이름)]
        self.incheon_positions = {}  # 노선 ID → [최근 정류소 순번]
        # 역 이름 → [(subwayId, trainLineNm, ordkey, 있으면 statnId, statnFid, statnTid)]
        self.subway_live = {}
        self.station_codes = []  # [(호선 표기, 역 이름, 역 코드, 있으면 외부 코드)]
        self.station_times = {}  # (역 코드, 요일, 방향) → ['HH:MM:SS']

    def live(self, request):
        '''실시간 위치, 역별 시간표 서버 대신 응답. 호출 종류 이름과 응답, 해당 없으면 None'''
        path = request.url.path
        params = request.url.params
        parts = path.strip('/').split('/')
        if request.url.host == 'swopenapi.seoul.go.kr':
            names = ('subwayId', 'trainLineNm', 'ordkey', 'statnId', 'statnFid', 'statnTid')
            rows = [
                {**dict(zip(names, row, strict=False)), 'recptnDt': '2026-10-20 07:59:30'}
                for row in self.subway_live.get(parts[-1], [])
            ]
            if not rows:
                return 'subway_live', {'status': 500, 'code': 'INFO-200'}
            return 'subway_live', {
                'errorMessage': {'code': 'INFO-000'},
                'realtimeArrivalList': rows,
            }
        if 'busRteInfo' in path:
            # DS-19: seoul_stations의 노선 ID를 seoul_buses의 노선 번호로 이어 한 표로 만듦
            names = {b['busRouteId']: b['busRouteNm'] for b in self.seoul_buses}
            rows = [
                {'ROUTE_ID': rid, 'RTE_NM': names.get(rid, rid), 'SN': str(q), 'XCRD': x, 'YCRD': y}
                for rid, stops in self.seoul_stations.items()
                for q, x, y in stops
            ]
            start, end = int(parts[-2]), int(parts[-1])
            body = {'list_total_count': len(rows), 'row': rows[start - 1 : end]}
            return 'seoul_routes', {'busRteInfo': body}
        if 'SearchSTNBySubwayLineInfo' in path:
            names = ('LINE_NUM', 'STATION_NM', 'STATION_CD', 'FR_CODE')
            rows = [
                dict(zip(names, row, strict=False))
                for row in self.station_codes
                if row[1] == parts[-1]
            ]
            return 'subway_code', {'SearchSTNBySubwayLineInfo': {'row': rows}}
        if 'SearchSTNTimeTableByIDService' in path:
            times = self.station_times.get((parts[-3], parts[-2], parts[-1]), [])
            rows = [{'LEFTTIME': t} for t in times]
            return 'subway_times', {'SearchSTNTimeTableByIDService': {'row': rows}}
        if path.endswith('getStaionByRoute'):
            stops = self.seoul_stations.get(params['busRouteId'], [])
            items = [{'seq': q, 'gpsX': x, 'gpsY': y} for q, x, y in stops]
            return 'seoul_bus', {'msgBody': {'itemList': items}}
        if path.endswith('getBusPosByRtid'):
            items = [
                {'sectOrd': o, 'stopFlag': '1' if f else '0', 'dataTm': '20261020075950'}
                for o, f in self.seoul_positions.get(params['busRouteId'], [])
            ]
            return 'seoul_pos', {'msgBody': {'itemList': items}}
        if path.endswith('getBusLocationListv2'):
            items = [
                {'stationSeq': q, 'stateCd': c}
                for q, c in self.gyeonggi_positions.get(params['routeId'], [])
            ]
            return 'gyeonggi_pos', {'response': {'msgBody': {'busLocationList': items}}}
        if path.endswith('getBusRouteSectionList'):
            items = [
                {'BSTOPSEQ': q, 'BSTOPNM': n}
                for q, n in self.incheon_sections.get(params['routeId'], [])
            ]
            return 'incheon', {'response': {'body': {'items': {'itemList': items}}}}
        if path.endswith('getBusRouteLocation'):
            items = [
                {'LATEST_STOPSEQ': q} for q in self.incheon_positions.get(params['routeId'], [])
            ]
            return 'incheon_pos', {'response': {'body': {'items': {'itemList': items}}}}
        return None

    def timetable(self, request):
        '''첫차, 막차 데이터 서버 대신 응답. 호출 종류 이름과 응답'''
        path = request.url.path
        params = request.url.params
        if request.url.host == 'openapi.seoul.go.kr':
            parts = path.strip('/').split('/')
            self.dows.append(parts[7])
            rows = self.subway_rows.get(parts[6], [])
            return 'subway', {'SearchFirstAndLastTrainbyLineServiceNew': {'row': rows}}
        if request.url.host == 'ws.bus.go.kr':
            if path.endswith('getStaionByRoute'):
                return 'seoul_bus', {'msgBody': {'itemList': []}}
            rows = [b for b in self.seoul_buses if params['strSrch'] in b['busRouteNm']]
            return 'seoul_bus', {'msgHeader': {'headerCd': '0'}, 'msgBody': {'itemList': rows}}
        if '6410000' in path:
            if path.endswith('getBusRouteListv2'):
                rows = [info for info, _ in self.gyeonggi_buses]
                rows = [r for r in rows if params['keyword'] in str(r['routeName'])]
                return 'gyeonggi', {'response': {'msgBody': {'busRouteList': rows}}}
            route = next(
                b for b in self.gyeonggi_buses if str(b[0]['routeId']) == params['routeId']
            )
            if path.endswith('getBusRouteStationListv2'):
                stations = [
                    {'stationSeq': i + 1, 'x': p[0], 'y': p[1]} for i, p in enumerate(route[1])
                ]
                return 'gyeonggi', {'response': {'msgBody': {'busRouteStationList': stations}}}
            return 'gyeonggi', {'response': {'msgBody': {'busRouteInfoItem': route[0]}}}
        rows = [b for b in self.incheon_buses if params['routeNo'] in b['ROUTENO']]
        return 'incheon', {'response': {'body': {'items': {'itemList': rows}}}}

    def handler(self, request):
        found = self.live(request)
        if found is not None:
            name, body = found
            self.calls[name] += 1
            if name in self.fail:
                raise httpx.ConnectError('연결 실패')
            return httpx.Response(200, json=body)
        if request.url.host in ('ws.bus.go.kr', 'apis.data.go.kr') or (
            'SearchFirstAndLastTrainbyLineServiceNew' in request.url.path
        ):
            name, body = self.timetable(request)
            self.calls[name] += 1
            if name in self.fail:
                raise httpx.ConnectError('연결 실패')
            if name == 'incheon' and self.incheon_error:
                return httpx.Response(200, text=GATEWAY_ERROR)
            return httpx.Response(200, json=body)
        if request.url.host == 'openapi.seoul.go.kr':
            name = 'bike'
        else:
            name = {
                '/v2/local/search/address.json': 'address',
                '/v2/local/search/keyword.json': 'keyword',
                '/v2/routing/publictraffic': 'transit',
                '/v2/routing/walk': 'walk',
                '/v2/routing/bicycle': 'bicycle',
            }[request.url.path]
        self.calls[name] += 1
        if name in self.fail:
            raise httpx.ConnectError('연결 실패')
        if name == 'address':
            return httpx.Response(200, json=self.address)
        if name == 'keyword':
            return httpx.Response(200, json=self.keyword)
        if name == 'transit':
            return httpx.Response(200, json=self.transit)
        if name == 'bike':
            parts = request.url.path.strip('/').split('/')
            start, end = int(parts[3]), int(parts[4])
            rows = self.bike_rows[start - 1 : end]
            if not rows:
                return httpx.Response(200, json={'RESULT': {'CODE': 'INFO-200', 'MESSAGE': ''}})
            return httpx.Response(200, json=bike_page(rows))
        # 도보 1.2m/s, 자전거 4m/s로 직선거리에 비례한 값
        params = request.url.params
        start = (float(params['start_x']), float(params['start_y']))
        end = (float(params['end_x']), float(params['end_y']))
        distance = distance_m(start, end)
        speed = 1.2 if name == 'walk' else 4.0
        seconds = int(distance / speed) + 1
        return httpx.Response(
            200, json=path_response(seconds, int(distance) + 1, points=[start, end])
        )


GATEWAY_ERROR = (
    '<?xml version="1.0" encoding="UTF-8"?><OpenAPI_ServiceResponse><cmmMsgHeader>'
    '<errMsg>HTTP_ERROR</errMsg><returnReasonCode>04</returnReasonCode>'
    '</cmmMsgHeader></OpenAPI_ServiceResponse>'
)


def subway_row(station, first, last):
    '''DS-12 응답의 row 하나 (datasource.md 7.3)'''
    return {'STTN': station, 'FSTT_HRM': first, 'LSTTM_HRM': last}


def seoul_bus(name, first, last, length_km, day='20261020'):
    '''DS-9 응답의 itemList 하나. first, last는 HHMMSS. 막차가 이르면 다음 날'''
    last_day = '20261021' if last < first else day
    return {
        'busRouteId': f'1000{name}',
        'busRouteNm': name,
        'length': str(length_km),
        'firstBusTm': f'{day}{first}',
        'lastBusTm': f'{last_day}{last}',
    }


@pytest.fixture
def api(tmp_path):
    fake = FakeExternal()
    fake.dows = []
    clock = Clock()
    holidays = tmp_path / 'holidays'
    holidays.mkdir()
    (holidays / '2026.csv').write_text('MM-DD,공휴일 이름\n12-25,성탄절\n', encoding='utf-8-sig')
    with TestClient(app) as client:
        http = httpx.AsyncClient(transport=httpx.MockTransport(fake.handler))
        app.state.now = lambda: NOW
        app.state.kakao = KakaoClient(http, TEST_KEY, clock=clock)
        app.state.bike = BikeClient(http, TEST_KEY, clock=clock, now=now_kst)
        app.state.timetable = TimetableClient(http, TEST_KEY, TEST_KEY, tmp_path, clock=clock)
        app.state.live = LiveClient(
            app.state.timetable,
            TEST_KEY,
            TEST_KEY,
            TEST_KEY,
            now=lambda: app.state.now(),
            clock=clock,
        )
        client.data_dir = tmp_path
        client.fake = fake
        client.clock = clock
        yield client


# 추천 (api_spec.md 4장)


def test_recommend_ok(api):
    response = api.post('/api/recommend', json=BODY)
    assert response.status_code == 200
    data = response.json()
    assert set(data) == {
        'fetchedAt',
        'transit',
        'bikeData',
        'base',
        'bikeMix',
        'busOnly',
        'pmOnly',
        'notes',
    }
    assert data['fetchedAt'].endswith('+09:00')
    assert data['transit'] == {'status': 'ok'}
    assert data['bikeData']['status'] == 'ok'
    assert data['bikeData']['fetchedAt'].endswith('+09:00')

    base = data['base']
    assert base['routeIndex'] == 0
    assert base['type'] == 'subway'
    assert base['edgeWalkKnown'] is True
    assert base['waitSeconds'] == 180
    assert base['fare'] == 1550
    assert [leg['type'] for leg in base['legs']] == ['walk', 'subway', 'walk']
    assert base['legs'][1]['vehicles'] == [{'type': '수도권', 'name': '2호선'}]
    assert set(base['pmSaving']) == {'firstSeconds', 'lastSeconds', 'totalSeconds'}

    # 출발지 → 첫 지하철역 도보가 20분 이상이라 First mile을 따릉이로 바꿈
    mix = data['bikeMix']
    assert mix['kind'] == 'first_last'
    assert mix['conditions']['first'] is True
    assert mix['stockKnown'] is True
    bike = mix['legs'][0]
    assert bike['type'] == 'bike'
    assert bike['mile'] == 'first'
    assert bike['rentStation']['id'] == 'ST-O'
    assert bike['rentStation']['availableBikes'] == 5
    assert bike['returnStation']['id'] == 'ST-S1'
    assert bike['returnStation']['availableRacks'] == 5

    assert data['busOnly'] is None
    assert data['pmOnly']['totalSeconds'] > 0
    assert data['notes'] == [{'target': 'busOnly', 'reason': 'none'}]

    # 지도 선 좌표 (api_spec.md 4.9)
    def near(point, target):
        return distance_m(point, target) < 2

    origin_walk, ride, destination_walk = base['legs']
    assert near(origin_walk['points'][0], ORIGIN)
    assert near(origin_walk['points'][-1], SUBWAY_START)
    assert near(ride['points'][0], SUBWAY_START)
    assert near(ride['points'][-1], SUBWAY_END)
    assert near(destination_walk['points'][-1], DESTINATION)
    station = (bike['rentStation']['x'], bike['rentStation']['y'])
    assert near(station, offset(ORIGIN, east_m=50))
    assert near(bike['toStationPoints'][-1], station)
    assert near(bike['ridePoints'][0], station)
    assert near(bike['fromStationPoints'][-1], SUBWAY_START)
    assert near(data['pmOnly']['points'][0], ORIGIN)
    assert near(data['pmOnly']['points'][-1], DESTINATION)


def test_recommend_no_result(api):
    api.fake.transit = transit_response(status='NO_RESULTS')
    data = api.post('/api/recommend', json=BODY).json()
    assert data['transit'] == {'status': 'no_result'}
    assert data['base'] is None
    assert data['bikeMix'] is None
    assert data['busOnly'] is None
    assert data['pmOnly'] is not None  # PM 전용 경로는 조회되면 표시 (rules.md 10장)


def test_v13_recommend_transit_unavailable(api):
    api.fake.fail.add('transit')
    response = api.post('/api/recommend', json=BODY)
    assert response.status_code == 200
    data = response.json()
    assert data['transit'] == {'status': 'unavailable'}
    assert data['base'] is None
    assert data['pmOnly'] is not None


def test_recommend_quota_exceeded_is_unavailable(api):
    api.fake.transit = {'code': -10, 'msg': 'API limit has been exceeded.'}
    data = api.post('/api/recommend', json=BODY).json()
    assert data['transit'] == {'status': 'unavailable'}


def test_recommend_pm_failure(api):
    api.fake.fail.add('bicycle')
    data = api.post('/api/recommend', json=BODY).json()
    assert data['pmOnly'] is None
    assert {'target': 'pmOnly', 'reason': 'route_failed'} in data['notes']
    assert data['bikeMix'] is None  # 따릉이 구간도 자전거 경로를 쓰므로 만들지 못함
    assert {'target': 'bikeMix', 'reason': 'route_failed'} in data['notes']


def test_recommend_bike_data_never_fetched(api):
    api.fake.fail.add('bike')
    data = api.post('/api/recommend', json=BODY).json()
    assert data['bikeData'] == {'status': 'unavailable', 'fetchedAt': None}
    assert data['bikeMix'] is None
    assert {'target': 'bikeMix', 'reason': 'no_station'} in data['notes']


def test_v9_recommend_bike_data_failure_uses_last_list(api):
    api.post('/api/recommend', json=BODY)
    api.clock.value += 31  # 따릉이 목록 캐시(30초)가 지남
    api.fake.fail.add('bike')
    data = api.post('/api/recommend', json=BODY).json()
    assert data['bikeData'] == {'status': 'unavailable', 'fetchedAt': None}
    mix = data['bikeMix']
    assert mix['stockKnown'] is False
    assert mix['legs'][0]['rentStation']['availableBikes'] is None
    assert mix['legs'][0]['returnStation']['availableRacks'] is None


@pytest.mark.parametrize(
    'body',
    [
        {'origin': {'x': 200, 'y': 37.5}, 'destination': BODY['destination']},
        {'origin': {'x': 127.0, 'y': 10}, 'destination': BODY['destination']},
        {'origin': BODY['origin']},
        {'origin': {'x': 'abc', 'y': 37.5}, 'destination': BODY['destination']},
        {**BODY, 'name': '집'},
    ],
)
def test_recommend_422(api, body):
    assert api.post('/api/recommend', json=body).status_code == 422
    assert sum(api.fake.calls.values()) == 0


def test_recommend_cache(api):
    api.post('/api/recommend', json=BODY)
    first = Counter(api.fake.calls)
    api.post('/api/recommend', json=BODY)
    assert api.fake.calls == first  # 외부 호출 수가 늘지 않음

    api.clock.value += 31  # 따릉이 목록만 다시 받음
    api.post('/api/recommend', json=BODY)
    assert api.fake.calls['bike'] > first['bike']
    for name in ('transit', 'walk', 'bicycle'):
        assert api.fake.calls[name] == first[name]

    api.clock.value += 24 * 3600  # 경로 캐시(24시간)가 지남
    api.post('/api/recommend', json=BODY)
    assert api.fake.calls['transit'] == first['transit'] + 1


def test_recommend_failure_not_cached(api):
    api.fake.fail.add('transit')
    api.post('/api/recommend', json=BODY)
    api.fake.fail.clear()
    data = api.post('/api/recommend', json=BODY).json()
    assert data['transit'] == {'status': 'ok'}
    assert api.fake.calls['transit'] == 2


# 주소 검색 (api_spec.md 3장)


def test_address_ok(api):
    response = api.post('/api/address/search', json={'query': '세종대로 209'})
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'ok'
    assert data['isEnd'] is True
    assert data['items'] == [
        {
            'addressName': '서울 종로구 세종대로 209',
            'roadAddress': '서울 종로구 세종대로 209',
            'jibunAddress': '서울 종로구 세종로 1-57',
            'buildingName': '정부서울청사',
            'x': 126.9769,
            'y': 37.5759,
            'placeName': None,
        }
    ]
    assert data['source'] == 'address'
    assert api.fake.calls['keyword'] == 0  # 주소 결과가 있으면 키워드 검색을 하지 않음


def test_address_no_result(api):
    api.fake.address = {'meta': {'is_end': True}, 'documents': []}
    data = api.post('/api/address/search', json={'query': '없는 주소'}).json()
    assert data == {'status': 'no_result', 'source': None, 'items': [], 'isEnd': True}
    assert api.fake.calls['keyword'] == 1  # 주소 0건이면 키워드 검색까지 해 봄


def test_address_unavailable(api):
    api.fake.fail.add('address')
    data = api.post('/api/address/search', json={'query': '세종대로'}).json()
    assert data == {'status': 'unavailable', 'source': None, 'items': [], 'isEnd': True}
    assert api.fake.calls['keyword'] == 0  # 주소 검색 실패이면 키워드로 넘어가지 않음


def test_address_error_response_is_unavailable(api):
    api.fake.address = {'errorType': 'AccessDeniedError', 'message': 'cannot find appKey'}
    data = api.post('/api/address/search', json={'query': '세종대로'}).json()
    assert data['status'] == 'unavailable'


def test_address_is_not_cached(api):
    api.post('/api/address/search', json={'query': '세종대로'})
    api.post('/api/address/search', json={'query': '세종대로'})
    assert api.fake.calls['address'] == 2


@pytest.mark.parametrize(
    'body',
    [
        {'query': ' 가 '},
        {'query': '가' * 101},
        {'query': '세종대로', 'page': 0},
        {'query': '세종대로', 'page': 46},
        {},
        {'query': '세종대로', 'name': '회사'},
        {'query': '세종대로', 'source': 'map'},
    ],
)
def test_address_422(api, body):
    assert api.post('/api/address/search', json=body).status_code == 422
    assert api.fake.calls['address'] == 0


# 키워드 장소 검색으로 넘어가기 (D-32)


def test_keyword_fallback_when_address_empty(api):
    api.fake.address = {'meta': {'is_end': True}, 'documents': []}
    api.fake.keyword = KEYWORD_OK
    data = api.post('/api/address/search', json={'query': '정부서울청사'}).json()
    assert data['status'] == 'ok'
    assert data['source'] == 'place'
    assert data['isEnd'] is False
    assert data['items'] == [
        {
            'addressName': '서울 종로구 세종대로 209',
            'roadAddress': '서울 종로구 세종대로 209',
            'jibunAddress': '서울 종로구 세종로 77-6',
            'buildingName': None,
            'x': 126.9752,
            'y': 37.5751,
            'placeName': '정부서울청사 본관',
        },
        {
            'addressName': '서울 종로구 적선동',
            'roadAddress': None,
            'jibunAddress': '서울 종로구 적선동',
            'buildingName': None,
            'x': 126.9741,
            'y': 37.5745,
            'placeName': '정부서울청사교차로',
        },
    ]
    assert (api.fake.calls['address'], api.fake.calls['keyword']) == (1, 1)


def test_next_page_keeps_place_source(api):
    api.fake.keyword = KEYWORD_OK
    body = {'query': '정부서울청사', 'page': 2, 'source': 'place'}
    data = api.post('/api/address/search', json=body).json()
    assert data['source'] == 'place'
    assert (api.fake.calls['address'], api.fake.calls['keyword']) == (0, 1)


def test_next_page_with_address_source_does_not_fall_back(api):
    api.fake.address = {'meta': {'is_end': True}, 'documents': []}
    body = {'query': '세종대로', 'page': 2, 'source': 'address'}
    data = api.post('/api/address/search', json=body).json()
    assert data['status'] == 'no_result'
    assert api.fake.calls['keyword'] == 0


def test_keyword_unavailable(api):
    api.fake.address = {'meta': {'is_end': True}, 'documents': []}
    api.fake.fail.add('keyword')
    data = api.post('/api/address/search', json={'query': '정부서울청사'}).json()
    assert data == {'status': 'unavailable', 'source': None, 'items': [], 'isEnd': True}


def test_keyword_malformed_is_unavailable(api):
    api.fake.address = {'meta': {'is_end': True}, 'documents': []}
    api.fake.keyword = {
        'documents': [{'place_name': 'a', 'road_address_name': 'b', 'x': 'x', 'y': '1'}]
    }
    data = api.post('/api/address/search', json={'query': '정부서울청사'}).json()
    assert data['status'] == 'unavailable'


# 정적 파일, 개인정보


def test_index_served(api, tmp_path, monkeypatch):
    (tmp_path / 'index.html').write_text('<!doctype html>', encoding='utf-8')
    monkeypatch.setattr(config, 'FRONTEND_DIR', tmp_path)
    response = api.get('/')
    assert response.status_code == 200
    assert response.text == '<!doctype html>'
    assert response.headers['cache-control'] == 'no-cache'


def test_frontend_files_revalidated(api):
    '''화면 파일은 매번 바뀌었는지 확인하고, 바뀌지 않았으면 304'''
    first = api.get('/js/app.js')
    assert first.status_code == 200
    assert first.headers['cache-control'] == 'no-cache'
    again = api.get('/js/app.js', headers={'If-None-Match': first.headers['etag']})
    assert again.status_code == 304
    assert again.headers['cache-control'] == 'no-cache'


def test_frontend_rules_file_not_served(api):
    assert api.get('/CLAUDE.md').status_code == 404
    assert api.get('/package.json').status_code == 404


def test_no_cookie(api):
    response = api.post('/api/recommend', json=BODY)
    assert 'set-cookie' not in response.headers


def test_logs_have_no_address_coordinates_or_key(api):
    records = []

    class Collect(logging.Handler):
        def emit(self, record):
            records.append(record.getMessage())

    handler = Collect()
    loggers = [logging.getLogger(), logging.getLogger('app')]
    for logger in loggers:
        logger.addHandler(handler)
    try:
        api.post('/api/recommend', json=BODY)
        api.post('/api/address/search', json={'query': '세종대로 209'})
        api.post('/api/recommend', json={**BODY, 'name': '집'})
    finally:
        for logger in loggers:
            logger.removeHandler(handler)

    text = '\n'.join(records)
    assert 'POST /api/recommend 200' in text
    assert 'kakao transit ok' in text
    for secret in ('127.0', '37.5', '세종대로', TEST_KEY, '집'):
        assert secret not in text


def test_ttl_cache_expires():
    clock = Clock()
    cache = TTLCache(30, clock=clock)
    cache.set('a', 1)
    clock.value += 29
    assert cache.get('a') == 1
    clock.value += 1
    assert cache.get('a') is None


# 외부 응답 형식이 datasource.md와 다를 때 (500이 아니라 status로 응답)


def test_malformed_transit_is_unavailable(api):
    route = raw_route('SUBWAY', [subway(900, SUBWAY_START, SUBWAY_END)])
    route['properties']['fare'] = 1550  # 객체가 아닌 값
    api.fake.transit = transit_response(route)
    response = api.post('/api/recommend', json=BODY)
    assert response.status_code == 200
    data = response.json()
    assert data['transit'] == {'status': 'unavailable'}
    assert data['pmOnly'] is not None


def test_null_stop_and_vehicle_names_become_empty(api):
    step = subway(900, SUBWAY_START, SUBWAY_END)
    step['properties']['stops'] = [{'name': None}]
    step['properties']['vehicles'] = [{'type': None, 'name': '2호선'}]
    api.fake.transit = transit_response(raw_route('SUBWAY', [step]))
    response = api.post('/api/recommend', json=BODY)
    assert response.status_code == 200
    leg = response.json()['base']['legs'][1]
    assert leg['stops'] == ['']
    assert leg['vehicles'] == [{'type': '', 'name': '2호선'}]


def test_malformed_address_is_unavailable(api):
    api.fake.address = {
        'meta': 'x',
        'documents': [{'address_name': 'a', 'x': '1', 'y': '2', 'road_address': 'x'}],
    }
    response = api.post('/api/address/search', json={'query': '세종대로'})
    assert response.status_code == 200
    assert response.json()['status'] == 'unavailable'


def test_malformed_bike_list_is_unavailable(api):
    original = api.fake.handler

    def handler(request):
        if request.url.host == 'openapi.seoul.go.kr':
            return httpx.Response(200, json={'rentBikeStatus': {'RESULT': 'ERROR', 'row': []}})
        return original(request)

    api.fake.handler = handler
    http = httpx.AsyncClient(transport=httpx.MockTransport(lambda r: api.fake.handler(r)))
    app.state.bike = BikeClient(http, TEST_KEY, clock=api.clock, now=now_kst)
    response = api.post('/api/recommend', json=BODY)
    assert response.status_code == 200
    assert response.json()['bikeData'] == {'status': 'unavailable', 'fetchedAt': None}


def test_same_path_in_flight_is_requested_once():
    fake = FakeExternal()
    http = httpx.AsyncClient(transport=httpx.MockTransport(fake.handler))
    kakao = KakaoClient(http, TEST_KEY)

    async def both():
        return await asyncio.gather(
            kakao.walk(ORIGIN, SUBWAY_START), kakao.walk(ORIGIN, SUBWAY_START)
        )

    first, second = asyncio.run(both())
    assert first == second
    assert fake.calls['walk'] == 1
    assert kakao.path_inflight == {}


def test_fare_value_or_min(api):
    single = raw_route('SUBWAY', [subway(900, SUBWAY_START, SUBWAY_END)])
    single['properties']['fare'] = {'value': 1500}
    api.fake.transit = transit_response(single)
    assert api.post('/api/recommend', json=BODY).json()['base']['fare'] == 1500


# 화면 설정 (api_spec.md 2.1)


def test_config_returns_map_key(api, monkeypatch):
    monkeypatch.setenv('KAKAO_JS_API', 'js-key')
    response = api.get('/api/config')
    assert response.status_code == 200
    assert response.json() == {'kakaoMapKey': 'js-key'}


def test_config_without_map_key(api, monkeypatch):
    monkeypatch.delenv('KAKAO_JS_API', raising=False)
    assert api.get('/api/config').json() == {'kakaoMapKey': None}


def test_config_never_sends_rest_key(api, monkeypatch):
    monkeypatch.setenv('KAKAO_REST_API', 'rest-key-value')
    monkeypatch.delenv('KAKAO_JS_API', raising=False)
    assert 'rest-key-value' not in api.get('/api/config').text


# 첫차, 막차 (rules.md 3.4, V-18 ~ V-21)

BUS_STOP = offset(ORIGIN, east_m=200)
BUS_END = offset(DESTINATION, east_m=-200)


def bus_route(*names, seconds=1800):
    '''노선 목록이 names인 버스 한 구간 경로 (카카오 응답 형식)'''
    return raw_route(
        'BUS',
        [
            step(
                'BUS',
                seconds,
                seconds * 4,
                [BUS_STOP, BUS_END],
                ['승차', '하차'],
                [('간선', n) for n in names],
            )
        ],
    )


def subway_route_raw():
    return raw_route('SUBWAY', [subway(900, SUBWAY_START, SUBWAY_END)])


def with_arrive_by(text):
    return {**BODY, 'arriveBy': text}


def set_now(hour, minute):
    '''테스트의 지금 시각을 2026-10-20 hour:minute로 바꿈'''
    app.state.now = lambda: datetime(2026, 10, 20, hour, minute, tzinfo=KST)


def test_recommend_ok_checks_subway_service(api):
    data = api.post('/api/recommend', json=BODY).json()
    assert data['base']['serviceUnknown'] is False
    assert data['base']['legs'][1]['serviceUnknown'] is False
    assert api.fake.calls['subway'] == 2  # 2호선 두 방향
    assert api.fake.dows == ['1', '1']  # 화요일, 평일


def test_v18_no_subway_at_three(api):
    set_now(0, 30)
    api.fake.transit = transit_response(subway_route_raw(), bus_route('N61'))
    api.fake.seoul_buses.append(seoul_bus('N61', '233000', '035000', 30))
    data = api.post('/api/recommend', json=with_arrive_by('2026-10-20T03:00:00+09:00')).json()
    assert data['transit']['status'] == 'ok'
    assert data['base']['routeIndex'] == 1
    assert [leg['type'] for leg in data['base']['legs']] == ['walk', 'bus', 'walk']


def test_v19_no_night_bus_at_nine(api):
    api.fake.transit = transit_response(bus_route('643', 'N61'), subway_route_raw())
    api.fake.seoul_buses += [
        seoul_bus('643', '043000', '233000', 30),
        seoul_bus('N61', '233000', '035000', 30),
    ]
    data = api.post('/api/recommend', json=with_arrive_by('2026-10-20T09:00:00+09:00')).json()
    assert data['base']['routeIndex'] == 1
    assert data['base']['type'] == 'subway'
    # 같은 경로 하나가 유일한 버스 경로였으므로 버스 전용 경로 없음
    assert data['busOnly'] is None


def test_night_bus_runs_after_midnight(api):
    set_now(0, 30)
    api.fake.transit = transit_response(subway_route_raw(), bus_route('N61'))
    api.fake.seoul_buses.append(seoul_bus('N61', '233000', '035000', 30))
    data = api.post('/api/recommend', json=with_arrive_by('2026-10-20T01:30:00+09:00')).json()
    assert data['base']['routeIndex'] == 1


def test_v20_unknown_bus_is_running_with_flag(api):
    api.fake.transit = transit_response(bus_route('9999'))
    data = api.post('/api/recommend', json=BODY).json()
    assert data['base']['routeIndex'] == 0
    assert data['base']['serviceUnknown'] is True
    assert data['base']['legs'][1]['serviceUnknown'] is True
    # 서울: 첫차, 막차는 DS-9, 실시간 위치는 DS-19 전체 표. 경기, 인천은 두 쪽이 한 번씩 찾음
    assert api.fake.calls['seoul_bus'] == 1
    assert api.fake.calls['seoul_routes'] == 1
    assert api.fake.calls['gyeonggi'] == 2
    assert api.fake.calls['incheon'] == 2
    assert data['base']['legs'][1]['positions'][0]['status'] == 'unknown'


def test_v21_all_routes_out_of_service(api):
    set_now(0, 30)
    api.fake.transit = transit_response(subway_route_raw())
    data = api.post('/api/recommend', json=with_arrive_by('2026-10-20T03:00:00+09:00')).json()
    assert data['transit'] == {'status': 'out_of_service'}
    assert (data['base'], data['bikeMix'], data['busOnly']) == (None, None, None)
    assert data['pmOnly']['totalSeconds'] > 0


def test_arrive_by_already_passed_uses_now(api):
    # 목표 07:00은 이미 지났으므로 지금(08:00) 출발로 판단. 08:00대 지하철은 운행
    data = api.post('/api/recommend', json=with_arrive_by('2026-10-20T07:00:00+09:00')).json()
    assert data['base']['type'] == 'subway'


def test_gyeonggi_bus_nearest_route_and_weekday_times(api):
    api.fake.transit = transit_response(bus_route('7'))
    far = [offset(ORIGIN, east_m=20000), offset(ORIGIN, east_m=21000)]
    near = [offset(BUS_STOP, east_m=30), offset(BUS_END, east_m=30)]
    api.fake.gyeonggi_buses = [
        ({'routeId': 1, 'routeName': 7, 'upFirstTime': '05:00', 'upLastTime': '23:00'}, far),
        ({'routeId': 2, 'routeName': 7, 'upFirstTime': '09:30', 'upLastTime': '22:00'}, near),
    ]
    # 가까운 노선(2)은 09:30부터라 08:00대에는 운행하지 않음
    data = api.post('/api/recommend', json=BODY).json()
    assert data['transit']['status'] == 'out_of_service'


def test_far_gyeonggi_route_with_same_number_is_not_used(api):
    # 경기 노선이 같은 번호여도 승차 지점에서 멀면 그 운행 시간을 쓰지 않고 인천에서 찾음
    api.fake.transit = transit_response(bus_route('103'))
    far = [offset(ORIGIN, east_m=20000), offset(ORIGIN, east_m=21000)]
    api.fake.gyeonggi_buses = [
        ({'routeId': 1, 'routeName': 103, 'upFirstTime': '09:30', 'upLastTime': '22:00'}, far)
    ]
    api.fake.incheon_buses = [
        {'ROUTENO': '103', 'ROUTELEN': '15900', 'FBUS_DEPHMS': '0530', 'LBUS_DEPHMS': '2300'}
    ]
    data = api.post('/api/recommend', json=BODY).json()
    assert data['transit']['status'] == 'ok'
    assert data['base']['serviceUnknown'] is False


def test_incheon_bus_used_when_not_in_seoul_or_gyeonggi(api):
    api.fake.transit = transit_response(bus_route('564-1'))
    api.fake.incheon_buses = [
        {'ROUTENO': '564-1', 'ROUTELEN': '15900', 'FBUS_DEPHMS': '0530', 'LBUS_DEPHMS': '0015'}
    ]
    data = api.post('/api/recommend', json=BODY).json()
    assert data['base']['serviceUnknown'] is False


def test_gateway_error_is_not_cached_as_not_found(api):
    # 인천 API가 HTTP 200으로 data.go.kr 오류 XML을 보내면 조회 실패. 복구되면 다시 찾음
    api.fake.transit = transit_response(bus_route('564-1'))
    api.fake.incheon_error = True
    data = api.post('/api/recommend', json=BODY).json()
    assert data['base']['serviceUnknown'] is True
    api.fake.incheon_error = False
    api.fake.incheon_buses = [
        {'ROUTENO': '564-1', 'ROUTELEN': '15900', 'FBUS_DEPHMS': '0530', 'LBUS_DEPHMS': '0015'}
    ]
    data = api.post('/api/recommend', json=BODY).json()
    assert data['base']['serviceUnknown'] is False


def test_holiday_uses_holiday_timetable(api):
    app.state.now = lambda: datetime(2026, 12, 25, 8, 0, tzinfo=KST)
    api.post('/api/recommend', json=BODY)
    assert api.fake.dows == ['3', '3']


def test_timetable_failure_is_unknown_and_not_cached(api):
    api.fake.fail.add('subway')
    data = api.post('/api/recommend', json=BODY).json()
    assert data['base']['serviceUnknown'] is True
    api.fake.fail.clear()
    data = api.post('/api/recommend', json=BODY).json()
    assert data['base']['serviceUnknown'] is False


def test_timetable_cached_within_day(api):
    api.post('/api/recommend', json=BODY)
    api.post('/api/recommend', json=BODY)
    assert api.fake.calls['subway'] == 2


def test_rail_file_for_other_lines(api):
    rail = api.data_dir / 'rail'
    rail.mkdir()
    (rail / '신분당선.csv').write_text(
        '역,다음 역,요일,첫차,막차\nA,B,평일,09:00,23:00\n', encoding='utf-8'
    )
    api.app.state.timetable = TimetableClient(
        api.app.state.timetable.http, TEST_KEY, TEST_KEY, api.data_dir
    )
    route = raw_route('SUBWAY', [subway(900, SUBWAY_START, SUBWAY_END)])
    route['steps'][0]['properties']['vehicles'] = [{'type': '수도권', 'name': '신분당선'}]
    api.fake.transit = transit_response(route)
    data = api.post('/api/recommend', json=BODY).json()
    assert data['transit']['status'] == 'out_of_service'  # 09:00부터 운행


def test_recommend_arrive_by_without_offset_is_422(api):
    assert api.post('/api/recommend', json=with_arrive_by('2026-10-20T09:00:00')).status_code == 422
