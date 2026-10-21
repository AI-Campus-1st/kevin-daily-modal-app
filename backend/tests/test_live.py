'''실시간 위치 테스트 (rules.md 11.3, 권장 F-26)

- test_api.py의 가짜 외부 서버와 api 준비 함수(conftest.py로 공유)를 함께 씀
'''

from app import config
from app.planner import live
from tests.samples import offset, raw_route, subway, transit_response
from tests.test_api import (
    BODY,
    BUS_END,
    BUS_STOP,
    SUBWAY_END,
    SUBWAY_START,
    bus_route,
    seoul_bus,
)


def first_position(api):
    return api.post('/api/recommend', json=BODY).json()['base']['legs'][1]['positions'][0]


def seoul_line(rid, api, count=5):
    '''BUS_STOP이 3번째, BUS_END가 마지막인 서울 노선 정류소'''
    api.fake.seoul_stations[rid] = [
        (1, *offset(BUS_STOP, east_m=-3000)),
        (2, *offset(BUS_STOP, east_m=-1500)),
        (3, *BUS_STOP),
        (4, *offset(BUS_STOP, east_m=800)),
        (5, *BUS_END),
    ][:count]


def test_seoul_bus_stops_away_not_in_total(api):
    api.fake.transit = transit_response(bus_route('101'))
    seoul_line('1000101', api)
    api.fake.seoul_positions['1000101'] = [(1, False), (4, False)]  # 4는 이미 지나감
    data = api.post('/api/recommend', json=BODY).json()
    position = data['base']['legs'][1]['positions'][0]
    assert (position['vehicle'], position['status'], position['stopsAway']) == ('101', 'live', 2)
    assert position['observedAt'] == '2026-10-20T07:59:50+09:00'
    # 소요 시간에는 반영하지 않음: 위치가 달라도 같은 값
    api.clock.value += 60
    api.fake.seoul_positions['1000101'] = []
    again = api.post('/api/recommend', json=BODY).json()
    assert again['base']['totalSeconds'] == data['base']['totalSeconds']
    assert again['base']['legs'][1]['positions'][0]['status'] == 'none'


def test_seoul_routes_loaded_once_over_pages(api, monkeypatch):
    # DS-19는 쪽을 나눠 전체를 받고, 같은 날에는 다시 받지 않음
    monkeypatch.setattr(config, 'SEOUL_ROUTE_PAGE_SIZE', 2)
    api.fake.transit = transit_response(bus_route('101'))
    seoul_line('1000101', api)
    api.fake.seoul_positions['1000101'] = [(2, False)]
    assert first_position(api)['stopsAway'] == 1
    api.clock.value += 60
    first_position(api)
    assert api.fake.calls['seoul_routes'] == 3  # 5행을 2행씩


def test_seoul_route_far_from_boarding_is_not_seoul(api):
    # 같은 번호의 서울 노선이 승차 지점에서 멀면 경기 노선에서 찾음
    api.fake.transit = transit_response(bus_route('101'))
    api.fake.seoul_stations['1000101'] = [(1, *offset(BUS_STOP, east_m=5000))]
    near = [offset(BUS_STOP, east_m=30), offset(BUS_END, east_m=30)]
    api.fake.gyeonggi_buses = [({'routeId': 7, 'routeName': 101, 'upFirstTime': '05:00'}, near)]
    api.fake.gyeonggi_positions['7'] = [(1, '1')]  # 승차 정류소에 도착해 있음
    position = first_position(api)
    assert (position['status'], position['stopsAway']) == ('live', 0)
    assert api.fake.calls['gyeonggi_pos'] == 1


def test_seoul_bus_without_times_is_unknown_not_gyeonggi(api):
    # DS-9를 쓰지 못하면 DS-19로 서울 노선인지만 확인. 같은 번호의 경기 노선 시각을 쓰지 않음
    api.fake.fail.add('seoul_bus')
    api.fake.transit = transit_response(bus_route('101'))
    seoul_line('1000101', api)
    near = [offset(BUS_STOP, east_m=30), offset(BUS_END, east_m=30)]
    api.fake.gyeonggi_buses = [
        ({'routeId': 7, 'routeName': 101, 'upFirstTime': '09:30', 'upLastTime': '22:00'}, near)
    ]
    data = api.post('/api/recommend', json=BODY).json()
    assert data['transit']['status'] == 'ok'
    assert data['base']['serviceUnknown'] is True


def test_seoul_bus_at_stop(api):
    api.fake.transit = transit_response(bus_route('101'))
    seoul_line('1000101', api)
    api.fake.seoul_positions['1000101'] = [(3, True)]
    position = first_position(api)
    assert (position['status'], position['stopsAway']) == ('live', 0)


def test_positions_per_route_in_step(api):
    api.fake.transit = transit_response(bus_route('101', '202'))
    api.fake.seoul_buses.append(seoul_bus('202', '043000', '233000', 20))
    for rid, at in (('1000101', 1), ('1000202', 2)):
        seoul_line(rid, api)
        api.fake.seoul_positions[rid] = [(at, False)]
    positions = api.post('/api/recommend', json=BODY).json()['base']['legs'][1]['positions']
    assert [(p['vehicle'], p['stopsAway']) for p in positions] == [('101', 2), ('202', 1)]


def test_gyeonggi_bus_position(api):
    api.fake.transit = transit_response(bus_route('7'))
    stops = [offset(BUS_STOP, east_m=-1000), BUS_STOP, BUS_END]
    api.fake.gyeonggi_buses = [
        ({'routeId': 2, 'routeName': 7, 'upFirstTime': '05:00', 'upLastTime': '23:00'}, stops)
    ]
    api.fake.gyeonggi_positions['2'] = [(1, '2')]
    position = first_position(api)
    assert (position['status'], position['stopsAway']) == ('live', 1)


def test_incheon_bus_position_by_stop_name(api):
    api.fake.transit = transit_response(bus_route('564-1'))
    api.fake.incheon_buses = [
        {
            'ROUTEID': '165000111',
            'ROUTENO': '564-1',
            'ROUTELEN': '15900',
            'FBUS_DEPHMS': '0530',
            'LBUS_DEPHMS': '0015',
        }
    ]
    api.fake.incheon_sections['165000111'] = [(1, '기점'), (2, '중간'), (3, '승차'), (4, '하차')]
    api.fake.incheon_positions['165000111'] = [1]
    position = first_position(api)
    assert (position['status'], position['stopsAway']) == ('live', 2)


def test_subway_live_matches_line_and_direction(api):
    api.fake.subway_live['A'] = [
        ('1002', '성수행 - B방면', '01002성수0'),
        ('1002', '성수행 - C방면', '11001성수0'),  # 반대 방향
        ('1077', '신사행 - B방면', '01000신사0'),  # 다른 노선
    ]
    position = first_position(api)
    assert position['vehicle'] == '2호선'
    assert (position['status'], position['stopsAway']) == ('live', 2)
    assert position['observedAt'] == '2026-10-20T07:59:30+09:00'


def test_subway_express_uses_station_order(api):
    # 급행: 카카오 다음 역 B(외부 코드 213)는 바로 옆 역이 아니라 방면 이름(X, W)과 맞지 않음
    api.fake.subway_live['A'] = [
        ('1002', '성수행 - X방면', '01002성수0', '1002000210', '1002000209', '1002000211'),
        ('1002', '성수행 - W방면', '11001성수0', '1002000210', '1002000211', '1002000209'),
    ]
    api.fake.station_codes = [('02호선', 'A', '0210', '210'), ('02호선', 'B', '0213', '213')]
    position = first_position(api)
    assert (position['status'], position['stopsAway']) == ('live', 2)


def test_subway_adjacent_next_without_matching_train_is_none(api):
    # 다음 역 B가 바로 옆 역(211)이면 역 번호로 다시 찾지 않음
    api.fake.subway_live['A'] = [
        ('1002', '성수행 - W방면', '11001성수0', '1002000210', '1002000211', '1002000209'),
    ]
    api.fake.station_codes = [('02호선', 'A', '0210', '210'), ('02호선', 'B', '0211', '211')]
    assert first_position(api)['status'] == 'none'


def test_subway_without_live_uses_timetable_after_boarding(api):
    api.fake.station_codes = [('02호선', 'A', '0222')]
    api.fake.station_times[('0222', '1', '1')] = ['07:50:00', '08:20:00', '08:40:00']
    position = first_position(api)
    # 08:00 출발에 출발 쪽 도보와 승차 대기를 더한 승차 예상 시각 이후 첫 열차
    assert position['status'] == 'timetable'
    assert position['nextDeparture'] == '2026-10-20T08:20:00+09:00'
    assert api.fake.calls['subway_live'] == 1


def test_other_line_without_live_is_unknown_and_names_deduped(api):
    route = raw_route('SUBWAY', [subway(900, SUBWAY_START, SUBWAY_END)])
    route['steps'][0]['properties']['vehicles'] = [
        {'type': '일반', 'name': '신분당선'},
        {'type': '급행', 'name': '신분당선'},
    ]
    api.fake.transit = transit_response(route)
    positions = api.post('/api/recommend', json=BODY).json()['base']['legs'][1]['positions']
    assert [(p['vehicle'], p['status']) for p in positions] == [('신분당선', 'unknown')]


def test_bike_mix_shares_positions(api):
    api.fake.subway_live['A'] = [('1002', '성수행 - B방면', '01003성수0')]
    data = api.post('/api/recommend', json=BODY).json()
    subway_leg = next(leg for leg in data['bikeMix']['legs'] if leg['type'] == 'subway')
    assert subway_leg['positions'][0]['stopsAway'] == 3


def test_live_failure_is_unknown(api):
    api.fake.fail.update({'subway_live', 'subway_code'})
    data = api.post('/api/recommend', json=BODY).json()
    assert data['transit']['status'] == 'ok'
    assert data['base']['legs'][1]['positions'][0]['status'] == 'unknown'


# 순수 함수


def test_board_seq_uses_direction():
    a = (127.0, 37.5)
    b = (127.01, 37.5)
    # 같은 이름 정류소가 양방향(순번 2, 6)에 있으면 하차 지점이 뒤에 오는 쪽
    stations = [(1, 126.99, 37.5), (2, *a), (3, *b), (5, 127.011, 37.5001), (6, 127.0001, 37.5001)]
    assert live.board_seq(stations, a, b) == 2
    assert live.board_seq(stations, (127.2, 37.5), b) is None


def test_stops_away_and_next_departure():
    assert live.stops_away(5, [(1, False), (3, False), (6, False)]) == 2
    assert live.stops_away(5, [(5, True)]) == 0
    assert live.stops_away(5, [(5, False), (7, False)]) is None
    assert live.next_departure([100, 200, 300], 150) == 200
    assert live.next_departure([100], 150) is None


def test_subway_away_parses_ordkey():
    rows = [
        ('1002', '성수행 - 역삼방면', '02005성수0'),
        ('1002', '성수행 - 역삼방면', '01001성수0'),
    ]
    assert live.subway_away(rows, '2호선', '역삼') == (1, 1)
    assert live.subway_away(rows, '2호선', '교대') is None


def test_subway_away_by_order():
    # 9호선 노량진(917) → 동작(920) 급행. 노들(918)방면 열차만
    rows = [
        ('1009', '01000김포공항1', '1009000917', '1009000918', '1009000916'),
        ('1009', '12002중앙보훈병원0', '1009000917', '1009000916', '1009000918'),
        ('1009', '11004중앙보훈병원1', '1009000917', '1009000916', '1009000918'),
        ('1001', '01000광운대0', '1001000136', '1001000135', '1001000137'),  # 다른 노선
    ]
    assert live.subway_away_by_order(rows, '9호선', '917', '920') == (2, 1)
    assert live.subway_away_by_order(rows, '9호선', '917', '910') == (0, 0)
    # 바로 옆 역, 숫자가 아닌 코드, 번호 체계가 다르면 쓰지 않음
    assert live.subway_away_by_order(rows, '9호선', '917', '918') is None
    assert live.subway_away_by_order(rows, '9호선', '917', 'K243') is None
    assert live.subway_away_by_order(rows, '9호선', '4117', '4120') is None


def test_route_number_strips_suffix():
    from app.planner.service import route_number

    assert route_number('N13(심야)') == 'N13'
    assert route_number('1101N') == '1101N'
    assert route_number('') == ''


def test_night_bus_suffix_is_looked_up_without_suffix(api):
    api.fake.transit = transit_response(bus_route('101(심야)'))
    seoul_line('1000101', api)
    api.fake.seoul_positions['1000101'] = [(2, False)]
    data = api.post('/api/recommend', json=BODY).json()
    assert data['base']['serviceUnknown'] is False
    position = data['base']['legs'][1]['positions'][0]
    assert (position['vehicle'], position['stopsAway']) == ('101(심야)', 1)
