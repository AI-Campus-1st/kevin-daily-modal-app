'''경로 만들기 테스트 (rules.md 13장 V-1 ~ V-11, V-13, V-17)

- app/planner/의 순수 함수에 예시 응답을 넣어 확인
- run()은 routers/recommend.py의 호출 순서를 외부 호출 없이 그대로 따라 함
'''

from types import SimpleNamespace

from app.planner.base import build_base
from app.planner.bike_route import (
    FirstLast,
    Segment,
    build_segment,
    condition1,
    decide,
    make_first_last,
    plan_segment,
    should_replace,
)
from app.planner.bus_pm import bus_only, pick_bus_route, pm_only
from app.planner.miles import first_mile, last_mile
from app.planner.stations import select_pair
from app.schemas import BikeLeg, RentStation, ReturnStation
from tests.samples import (
    DESTINATION,
    FAILED,
    ORIGIN,
    bus,
    offset,
    route,
    station,
    subway,
    walk,
)

# 가상 지점: 출발지 → 버스 정류장 → 첫 지하철역 → 마지막 지하철역 → 버스 하차 → 도착지
BUS_STOP = offset(ORIGIN, east_m=200)
SUBWAY_START = offset(ORIGIN, east_m=1500)
SUBWAY_END = offset(DESTINATION, east_m=-1500)
BUS_END = offset(DESTINATION, east_m=-200)

# 각 지점 근처 대여소 (서로 500m 넘게 떨어져 있음)
STATIONS = (
    station('ST-O', offset(ORIGIN, east_m=50)),
    station('ST-S1', offset(SUBWAY_START, north_m=60)),
    station('ST-S2', offset(SUBWAY_END, north_m=60)),
    station('ST-D', offset(DESTINATION, east_m=50)),
)

# 따릉이 구간 조회 결과 (대여소까지 도보, 자전거, 대여소에서 도보)
FAST = (walk(60), walk(200), walk(60))  # 60 + 60 + 200 + 30 + 60 = 410초
SLOW = (walk(60), walk(1500), walk(60))  # 1,710초


def run(
    kakao_route,
    origin_walk,
    destination_walk,
    station_walks=(None, None),
    stations=STATIONS,
    stock_known=True,
    first_paths=FAST,
    last_paths=FAST,
    full_paths=SLOW,
):
    '''routers/recommend.py와 같은 순서로 planner 함수를 부름'''
    base = build_base(kakao_route, origin_walk, destination_walk)
    first = first_mile(kakao_route, ORIGIN, origin_walk)
    last = last_mile(kakao_route, DESTINATION, destination_walk)
    cond1_first = condition1(first, station_walks[0])
    cond1_last = condition1(last, station_walks[1])

    def make(mile, start, end, replaced, known, paths):
        if not known:
            return Segment(outcome='skipped')
        plan = plan_segment(mile, start, end, stations, stock_known)
        if plan is None:
            return Segment(outcome='no_station')
        return build_segment(plan, replaced, *paths, stock_known)

    first_seg = make(
        'first', first.start, first.end, first.original_seconds, first.known, first_paths
    )
    last_seg = make('last', last.start, last.end, last.original_seconds, last.known, last_paths)
    first_last = make_first_last(
        kakao_route, base, first, last, first_seg, last_seg, cond1_first, cond1_last
    )
    full_seg = None
    if first_last is None:
        full_seg = make('full', ORIGIN, DESTINATION, base.total_seconds, True, full_paths)
    mix, note = decide(
        base, cond1_first, cond1_last, first_seg, last_seg, first_last, full_seg, stock_known
    )
    return SimpleNamespace(
        base=base,
        first=first,
        last=last,
        cond1_first=cond1_first,
        cond1_last=cond1_last,
        first_seg=first_seg,
        last_seg=last_seg,
        first_last=first_last,
        full_seg=full_seg,
        mix=mix,
        note=note,
    )


def subway_route():
    '''지하철 하나만 타는 기본 경로'''
    return route(0, 'SUBWAY', [subway(900, SUBWAY_START, SUBWAY_END)])


def bike_leg(seconds, mile='full'):
    return BikeLeg(
        mile=mile,
        seconds=seconds,
        replaced_seconds=0,
        to_station_seconds=0,
        rent_seconds=60,
        ride_seconds=seconds - 90,
        return_seconds=30,
        from_station_seconds=0,
        rent_station=RentStation(id='A', name='A', available_bikes=1, distance=0, x=0, y=0),
        return_station=ReturnStation(id='B', name='B', available_racks=1, distance=0, x=0, y=0),
    )


# 기본 경로, 총 소요 시간 (rules.md 3장)


def test_base_total_includes_edge_walks_and_wait():
    result = run(subway_route(), walk(300, 350), walk(240, 280))
    base = result.base
    assert base.edge_walk_known is True
    assert base.wait_seconds == 180
    assert base.total_seconds == 300 + 900 + 240 + 180
    assert base.total_distance == 350 + 9000 + 280
    assert [leg.type for leg in base.legs] == ['walk', 'subway', 'walk']
    assert [base.legs[0].edge, base.legs[-1].edge] == ['origin', 'destination']
    assert base.legs[1].wait_seconds == 180


def test_edge_walk_failure_uses_kakao_total():
    kakao_route = subway_route()
    result = run(kakao_route, walk(300), FAILED)
    base = result.base
    assert base.edge_walk_known is False
    assert base.total_seconds == kakao_route.total_time + 180
    assert base.total_distance == kakao_route.total_distance
    assert [leg.type for leg in base.legs] == ['subway']
    assert base.pm_saving is None
    # 실패한 쪽 mile은 바꾸지 않고 조건 1도 만족하지 않음 (rules.md 3.2)
    assert result.last_seg.outcome == 'skipped'
    assert result.cond1_last is False


def test_v1_pm_saving():
    result = run(subway_route(), walk(720, 840), walk(360, 420))
    saving = result.base.pm_saving
    assert saving.first_seconds == 518  # 720 - 840 / 4.1667 = 518.4, 초 미만 버림
    assert saving.last_seconds == 259
    assert saving.total_seconds == saving.first_seconds + saving.last_seconds
    assert abs(saving.total_seconds - 778) <= 1
    assert saving.total_seconds // 60 == 12  # "12분 단축"


def test_pm_saving_never_negative():
    result = run(subway_route(), walk(60, 600), walk(360, 420))
    assert result.base.pm_saving.first_seconds == 0


# 따릉이 포함 경로 (rules.md 5장)


def test_v2_first_mile_with_bus_replaced_by_condition1():
    kakao_route = route(
        0,
        'BUS_AND_SUBWAY',
        [bus(600, BUS_STOP, SUBWAY_START), subway(900, SUBWAY_START, SUBWAY_END)],
        transfers=1,
    )
    result = run(
        kakao_route,
        walk(300),
        walk(240),
        station_walks=(walk(1380), None),  # 출발지 → 첫 지하철역 도보 23분
        first_paths=SLOW,  # 원래 First mile(18분)보다 느려도 조건 1이면 바꿈
    )
    assert result.cond1_first is True
    assert result.first.original_seconds == 300 + 600 + 180
    mix = result.mix
    assert mix.kind == 'first_last'
    assert mix.conditions.first is True
    assert [leg.type for leg in mix.legs] == ['bike', 'subway', 'walk']
    assert mix.legs[0].mile == 'first'
    assert mix.legs[0].seconds == 1710
    assert mix.legs[0].replaced_seconds == 1080
    assert mix.total_seconds == result.base.total_seconds - 1080 + 1710
    assert mix.transfers == 0


def test_v3_condition2_only():
    base = SimpleNamespace(total_seconds=2000)
    first_last = FirstLast(total_seconds=2240, transfers=0, legs=[])  # 112%
    built = Segment(outcome='built', leg=bike_leg(400, 'first'))
    mix, note = decide(base, False, False, built, built, first_last, None, True)
    assert note is None
    assert mix.kind == 'first_last'
    assert mix.conditions.first is False
    assert mix.conditions.second is True
    assert mix.conditions.third is None


def test_v4_condition3_only():
    base = SimpleNamespace(total_seconds=2000)
    first_last = FirstLast(total_seconds=2400, transfers=0, legs=[])  # 120%
    built = Segment(outcome='built', leg=bike_leg(400, 'first'))
    full = Segment(outcome='built', leg=bike_leg(1560))  # 26분
    mix, note = decide(base, False, False, built, built, first_last, full, True)
    assert note is None
    assert mix.kind == 'full'
    assert mix.conditions.second is False
    assert mix.conditions.third is True
    assert mix.transfers == 0
    assert mix.total_seconds == 1560


def test_v4_full_route_when_miles_not_replaced():
    full_27 = (walk(60), walk(1410), walk(60))  # 60 + 60 + 1410 + 30 + 60 = 1,620초 (30분 미만)
    result = run(
        subway_route(), walk(300), walk(240), first_paths=SLOW, last_paths=SLOW, full_paths=full_27
    )
    assert result.first_last is None
    assert result.mix.kind == 'full'
    assert result.mix.conditions.first is False
    assert result.mix.conditions.second is None
    assert result.mix.conditions.third is True
    assert result.mix.legs[0].mile == 'full'
    assert result.mix.legs[0].replaced_seconds == result.base.total_seconds


def test_full_route_not_fetched_when_first_last_shown():
    result = run(subway_route(), walk(900), walk(240))  # First mile 15분 → 따릉이 410초가 빠름
    assert result.mix.kind == 'first_last'
    assert result.full_seg is None
    assert result.mix.conditions.third is None


def test_v5_no_condition():
    full_35 = (walk(60), walk(1950), walk(60))  # 2,160초
    result = run(
        subway_route(), walk(300), walk(240), first_paths=SLOW, last_paths=SLOW, full_paths=full_35
    )
    assert result.mix is None
    assert result.note.target == 'bikeMix'
    assert result.note.reason == 'no_condition'


def test_v6_bus_only_base_uses_first_bus_stop():
    kakao_route = route(0, 'BUS', [bus(900, BUS_STOP, BUS_END)])
    result = run(
        kakao_route,
        walk(1260),
        walk(120),
        stations=(
            station('ST-O', offset(ORIGIN, east_m=50)),
            station('ST-B', offset(BUS_STOP, north_m=-50)),
            station('ST-D', offset(DESTINATION, east_m=50)),
        ),
    )
    assert result.first.steps == ()
    assert result.first.has_bus is False
    assert result.first.end == BUS_STOP
    assert result.cond1_first is True  # 첫 버스 정류장까지 도보 21분
    assert result.mix.kind == 'first_last'
    assert result.mix.legs[0].mile == 'first'


def test_v7_no_bike_at_first_station():
    stations = (
        station('ST-O', offset(ORIGIN, east_m=50), bikes=0),
        *STATIONS[1:],
    )
    result = run(subway_route(), walk(900), walk(900), stations=stations)
    assert result.first_seg.outcome == 'no_station'
    assert result.last_seg.outcome == 'built'
    mix = result.mix
    assert mix.kind == 'first_last'
    assert [leg.type for leg in mix.legs] == ['walk', 'subway', 'bike']
    assert mix.legs[0].edge == 'origin'
    assert mix.legs[-1].mile == 'last'
    assert mix.total_seconds == result.base.total_seconds - 900 + 410
    assert mix.conditions.second is True


def test_v8_short_last_mile_not_replaced():
    six_minutes = (walk(60), walk(150), walk(60))  # 360초
    result = run(subway_route(), walk(240), walk(180), last_paths=six_minutes)
    assert result.last_seg.leg.seconds == 360
    assert should_replace(result.last, result.last_seg, result.cond1_last) is False
    assert result.first_last is None


def test_v9_stock_unknown_uses_nearest_station():
    stations = (
        station('ST-O', offset(ORIGIN, east_m=50), bikes=0),
        station('ST-S1', offset(SUBWAY_START, north_m=60), racks=0),
        *STATIONS[2:],
    )
    result = run(subway_route(), walk(1300), walk(240), stations=stations, stock_known=False)
    mix = result.mix
    assert mix.stock_known is False
    leg = mix.legs[0]
    assert leg.rent_station.id == 'ST-O'
    assert leg.rent_station.available_bikes is None
    assert leg.return_station.id == 'ST-S1'
    assert leg.return_station.available_racks is None


def test_v17_last_mile_with_bus_replaced_by_condition1():
    kakao_route = route(
        0,
        'BUS_AND_SUBWAY',
        [subway(900, SUBWAY_START, SUBWAY_END), bus(480, SUBWAY_END, BUS_END)],
        transfers=1,
    )
    result = run(
        kakao_route,
        walk(360),  # 첫 역까지 도보 6분
        walk(240),  # 버스 하차 후 도보 4분
        station_walks=(None, walk(1260)),  # 마지막 하차역 → 도착지 도보 21분
        last_paths=SLOW,
    )
    assert result.cond1_first is False
    assert result.cond1_last is True
    assert result.last.original_seconds == 480 + 180 + 240
    mix = result.mix
    assert mix.kind == 'first_last'
    assert [leg.type for leg in mix.legs] == ['walk', 'subway', 'bike']
    assert mix.legs[-1].mile == 'last'
    assert mix.total_seconds == result.base.total_seconds - 900 + 1710


def test_condition1_walk_failure_means_not_satisfied():
    kakao_route = route(
        0,
        'BUS_AND_SUBWAY',
        [bus(600, BUS_STOP, SUBWAY_START), subway(900, SUBWAY_START, SUBWAY_END)],
    )
    result = run(kakao_route, walk(300), walk(240), station_walks=(FAILED, None))
    assert result.cond1_first is False


def test_same_rent_and_return_station_is_not_used():
    near = offset(ORIGIN, east_m=100)
    assert select_pair(STATIONS, ORIGIN, near, True) is None


def test_route_failure_note():
    result = run(
        subway_route(),
        walk(1300),
        walk(240),
        first_paths=(walk(60), FAILED, walk(60)),
        full_paths=(FAILED, walk(1000), walk(60)),
    )
    assert result.first_seg.outcome == 'route_failed'
    assert result.mix is None
    assert result.note.reason == 'route_failed'


def test_no_station_note():
    result = run(subway_route(), walk(300), walk(240), stations=())
    assert result.mix is None
    assert result.note.reason == 'no_station'


# 버스 전용, PM 전용 경로 (rules.md 6, 7장)


def test_v10_fastest_bus_route():
    routes = [
        route(0, 'SUBWAY', [subway(2000, SUBWAY_START, SUBWAY_END)], total_time=52 * 60 - 180),
        route(1, 'BUS', [bus(2000, BUS_STOP, BUS_END)], total_time=55 * 60 - 180),
        route(2, 'BUS', [bus(1800, BUS_STOP, BUS_END)], total_time=48 * 60 - 180),
    ]
    picked = pick_bus_route(routes)
    assert picked.index == 2
    result, note = bus_only(picked, 0, walk(300), walk(200))
    assert note is None
    assert result.route_index == 2
    assert result.type == 'bus'
    assert result.total_seconds == 300 + 1800 + 200 + 180


def test_bus_route_tie_uses_earlier_route():
    routes = [
        route(0, 'SUBWAY', [subway(2000, SUBWAY_START, SUBWAY_END)]),
        route(1, 'BUS', [bus(1800, BUS_STOP, BUS_END)], total_time=3000),
        route(2, 'BUS', [bus(1800, BUS_STOP, BUS_END)], total_time=3000),
    ]
    assert pick_bus_route(routes).index == 1


def test_bus_wait_counts_in_bus_route_choice():
    routes = [
        route(0, 'SUBWAY', [subway(2000, SUBWAY_START, SUBWAY_END)]),
        route(
            1, 'BUS', [bus(900, BUS_STOP, BUS_END), bus(900, BUS_END, DESTINATION)], total_time=2900
        ),  # 대기 포함 3,260초
        route(2, 'BUS', [bus(1800, BUS_STOP, BUS_END)], total_time=3000),  # 대기 포함 3,180초
    ]
    assert pick_bus_route(routes).index == 2


def test_v11_only_bus_route_is_base():
    routes = [
        route(0, 'BUS', [bus(1800, BUS_STOP, BUS_END)]),
        route(1, 'SUBWAY', [subway(2000, SUBWAY_START, SUBWAY_END)]),
    ]
    picked = pick_bus_route(routes)
    result, note = bus_only(picked, 0, None, None)
    assert result is None
    assert note.reason == 'same_as_base'


def test_no_bus_route():
    result, note = bus_only(pick_bus_route([subway_route()]), 0, None, None)
    assert result is None
    assert note.reason == 'none'


def test_v13_pm_only():
    result, note = pm_only(walk(780, 3400))
    assert note is None
    assert (result.total_seconds, result.total_distance) == (780, 3400)
    result, note = pm_only(FAILED)
    assert result is None
    assert (note.target, note.reason) == ('pmOnly', 'route_failed')


# 지도 선 좌표 (api_spec.md 4.9)


def test_path_points_joined_without_duplicates():
    from app.clients.kakao import parse_path
    from tests.samples import path_response

    points = [ORIGIN, BUS_STOP, SUBWAY_START]
    result = parse_path(path_response(100, 200, points=points))
    assert result.points == tuple(points)


def test_malformed_path_points_keep_time():
    from app.clients.kakao import parse_path

    data = {
        'status': 'OK',
        'route': {
            'properties': {'totalTime': 100, 'totalDistance': 200},
            'legs': [{'steps': [{'path': {'points': [['x']]}}]}],
        },
    }
    result = parse_path(data)
    assert (result.status, result.seconds, result.points) == ('ok', 100, ())


def test_transit_and_edge_legs_carry_points():
    from app.clients.kakao import PathResult

    origin_walk = PathResult(status='ok', seconds=60, distance=60, points=(ORIGIN, SUBWAY_START))
    base = build_base(subway_route(), origin_walk, walk(60))
    first, ride, last = base.legs
    assert first.points == [(round(ORIGIN[0], 5), round(ORIGIN[1], 5)), first.points[1]]
    assert len(ride.points) == 2
    assert last.points == []
