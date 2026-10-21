'''4종 경로 추천 POST /api/recommend (api_spec.md 4장)

- 외부 호출 순서를 조정하는 유일한 곳 (backend/CLAUDE.md 3.1). 계산은 app/planner/의 순수 함수가 함
- 순서 (tech_stack.md 2.3)
  1. 대중교통 경로, PM 전용 자전거 경로, 따릉이 대여정보를 동시에 조회
  2. 첫차, 막차 확인 (rules.md 3.4). 카카오 응답 순서대로 확인해 운행 중인 첫 경로가 기본 경로,
     버스 경로는 짧은 순으로 확인해 운행 중인 첫 경로가 버스 전용 경로
  3. 기본 경로, 버스 전용 경로의 출발 도보, 도착 도보와 조건 1 판단용 도보를 동시에 조회
  4. First, Last mile 따릉이 구간을 동시에 조회
  5. First, Last mile 대체 경로를 만들지 못했을 때만 전 구간 따릉이 구간 조회
  6. 기본 경로, 버스 전용 경로의 버스, 지하철 실시간 위치 조회 (권장 F-26)
- 좌표는 로그에 남기지 않음
'''

import asyncio
from datetime import timedelta

from fastapi import APIRouter, Request

from app.planner import base as base_planner
from app.planner import bike_route, bus_pm, miles, service
from app.schemas import (
    BikeDataStatus,
    Position,
    RecommendRequest,
    RecommendResponse,
    TransitStatus,
)

router = APIRouter()


async def nothing():
    '''조회하지 않는 자리를 채우는 빈 결과'''
    return None


def walk_or_nothing(kakao, start, end):
    '''두 좌표가 모두 있으면 도보 경로 조회, 아니면 빈 결과'''
    if start is None or end is None:
        return nothing()
    return kakao.walk(start, end)


async def make_segment(kakao, bike_data, mile, start, end, replaced_seconds, known):
    '''대여소를 고르고 카카오 도보, 자전거 경로를 조회해 따릉이 구간을 만듦'''
    if not known:
        return bike_route.Segment(outcome='skipped')
    plan = bike_route.plan_segment(mile, start, end, bike_data.stations, bike_data.stock_known)
    if plan is None:
        return bike_route.Segment(outcome='no_station')
    to_station, ride, from_station = await asyncio.gather(
        kakao.walk(plan.start, plan.rent_point),
        kakao.bicycle(plan.rent_point, plan.return_point),
        kakao.walk(plan.return_point, plan.end),
    )
    return bike_route.build_segment(
        plan, replaced_seconds, to_station, ride, from_station, bike_data.stock_known
    )


async def check_service(timetable, route, origin, destination, arrive_by, now):
    '''경로 하나의 첫차, 막차 확인 (rules.md 3.4). 구간마다 모든 노선의 운행 범위를 동시에 조회'''
    start = service.departure(route, arrive_by, now)
    offsets = service.boarding_offsets(route, origin, destination)

    async def boarding(index):
        step = route.steps[index]
        moment = start + timedelta(seconds=offsets[index])
        day = moment.date()
        seconds = moment.hour * 3600 + moment.minute * 60 + moment.second
        if step.kind == 'bus':
            near = step.points[0] if step.points else None
            lookups = [timetable.bus_window(name, near, day) for _, name in step.vehicles]
        else:
            station = step.stops[0] if step.stops else ''
            next_station = step.stops[1] if len(step.stops) > 1 else ''
            lookups = [
                timetable.rail_window(name, station, next_station, day) for _, name in step.vehicles
            ]
        windows = await asyncio.gather(*lookups)
        return index, seconds, tuple(windows)

    boardings = await asyncio.gather(*(boarding(index) for index in offsets))
    return service.check_route(boardings)


def unique_names(step):
    '''구간 노선 이름. 일반, 급행처럼 같은 이름이 겹치면 한 번만 (datasource.md 7.5)'''
    names = []
    for _, name in step.vehicles:
        if name and name not in names:
            names.append(name)
    return names


async def attach_positions(live, route, built, origin, destination, arrive_by, now):
    '''경로의 버스, 지하철 구간마다 노선별 실시간 위치를 넣음 (rules.md 11.3, 권장 F-26)

    - 소요 시간, 출발 시각에는 반영하지 않음
    - 시간표로 다음 열차를 구할 때 기준은 그 구간의 승차 예상 시각 (rules.md 3.4.2)
    - built의 구간 객체를 고치므로, 같은 구간을 쓰는 따릉이 포함 경로에도 함께 들어감
    '''
    start = service.departure(route, arrive_by, now)
    offsets = service.boarding_offsets(route, origin, destination)
    shift = 1 if built.edge_walk_known else 0

    async def fill(index):
        step = route.steps[index]
        leg = built.legs[index + shift]
        moment = start + timedelta(seconds=offsets[index])
        names = unique_names(step)
        if step.kind == 'bus':
            board = step.points[0] if step.points else None
            alight = step.points[-1] if step.points else None
            board_name = step.stops[0] if step.stops else ''
            alight_name = step.stops[-1] if step.stops else ''
            lookups = [live.bus(name, board, alight, board_name, alight_name) for name in names]
        else:
            station = step.stops[0] if step.stops else ''
            next_station = step.stops[1] if len(step.stops) > 1 else ''
            lookups = [live.subway(name, station, next_station, moment) for name in names]
        results = await asyncio.gather(*lookups)
        leg.positions = [
            Position(
                vehicle=name,
                status=result.status,
                stops_away=result.stops_away,
                next_departure=result.next_departure,
                observed_at=result.observed_at,
            )
            for name, result in zip(names, results, strict=True)
        ]

    await asyncio.gather(*(fill(index) for index in offsets))


async def first_running(candidates, check):
    '''후보를 순서대로 확인해 운행 중인 첫 경로. 없으면 None'''
    for candidate in candidates:
        if (await check(candidate)).running:
            return candidate
    return None


async def plan_transit(
    kakao, timetable, live, bike_task, routes, origin, destination, arrive_by, now
):
    '''대중교통 경로 조회에 성공했을 때 기본, 따릉이 포함, 버스 전용 경로를 만듦

    - 운행 중인 경로가 없으면 None (rules.md 3.4.5)
    '''
    checks = {}

    async def check(candidate):
        if candidate.index not in checks:
            checks[candidate.index] = await check_service(
                timetable, candidate, origin, destination, arrive_by, now
            )
        return checks[candidate.index]

    route = await first_running(routes, check)
    if route is None:
        return None
    bus_route = await first_running(bus_pm.bus_candidates(routes), check)
    need_bus_walks = bus_route is not None and bus_route.index != route.index

    # 3. 출발 도보, 도착 도보, 조건 1 판단용 도보
    base_start, base_end = base_planner.edge_points(route)
    bus_start, bus_end = base_planner.edge_points(bus_route) if need_bus_walks else (None, None)
    first_point = miles.boarding_point(route)
    last_point = miles.alighting_point(route)
    first_has_bus = miles.first_mile(route, origin, None).has_bus
    last_has_bus = miles.last_mile(route, destination, None).has_bus
    (
        origin_walk,
        destination_walk,
        bus_origin_walk,
        bus_destination_walk,
        first_station_walk,
        last_station_walk,
    ) = await asyncio.gather(
        walk_or_nothing(kakao, origin, base_start),
        walk_or_nothing(kakao, base_end, destination),
        walk_or_nothing(kakao, origin, bus_start),
        walk_or_nothing(kakao, bus_end, destination),
        walk_or_nothing(kakao, origin, first_point) if first_has_bus else nothing(),
        walk_or_nothing(kakao, last_point, destination) if last_has_bus else nothing(),
    )

    base = base_planner.build_base(
        route, origin_walk, destination_walk, checks[route.index].unknown_steps
    )
    bus_unknown = checks[bus_route.index].unknown_steps if bus_route is not None else frozenset()
    bus, bus_note = bus_pm.bus_only(
        bus_route, route.index, bus_origin_walk, bus_destination_walk, bus_unknown
    )
    first = miles.first_mile(route, origin, origin_walk)
    last = miles.last_mile(route, destination, destination_walk)
    cond1_first = bike_route.condition1(first, first_station_walk)
    cond1_last = bike_route.condition1(last, last_station_walk)

    # 4. First, Last mile 따릉이 구간
    bike_data = await bike_task
    first_seg, last_seg = await asyncio.gather(
        make_segment(
            kakao, bike_data, 'first', first.start, first.end, first.original_seconds, first.known
        ),
        make_segment(
            kakao, bike_data, 'last', last.start, last.end, last.original_seconds, last.known
        ),
    )
    first_last = bike_route.make_first_last(
        route, base, first, last, first_seg, last_seg, cond1_first, cond1_last
    )

    # 5. 전 구간 따릉이 (필요할 때만)
    full_seg = None
    if first_last is None:
        full_seg = await make_segment(
            kakao, bike_data, 'full', origin, destination, base.total_seconds, True
        )

    bike_mix, bike_note = bike_route.decide(
        base,
        cond1_first,
        cond1_last,
        first_seg,
        last_seg,
        first_last,
        full_seg,
        bike_data.stock_known,
    )
    # 6. 실시간 위치 (권장 F-26)
    await asyncio.gather(
        attach_positions(live, route, base, origin, destination, arrive_by, now),
        attach_positions(live, bus_route, bus, origin, destination, arrive_by, now)
        if bus is not None
        else nothing(),
    )
    notes = [note for note in (bike_note, bus_note) if note is not None]
    return base, bike_mix, bus, notes


@router.post('/api/recommend', response_model=RecommendResponse)
async def recommend(body: RecommendRequest, request: Request):
    state = request.app.state
    origin = body.origin.as_tuple()
    destination = body.destination.as_tuple()

    # 1. 대중교통 경로, PM 전용 자전거 경로, 따릉이 대여정보
    bike_task = asyncio.create_task(state.bike.stations())
    transit, bicycle = await asyncio.gather(
        state.kakao.transit(origin, destination),
        state.kakao.bicycle(origin, destination),
    )

    base = bike_mix = bus = None
    notes = []
    transit_status = transit.status
    if transit.status == 'ok':
        now = state.now()
        arrive_by = body.arrive_by.astimezone(now.tzinfo) if body.arrive_by else None
        planned = await plan_transit(
            state.kakao,
            state.timetable,
            state.live,
            bike_task,
            transit.routes,
            origin,
            destination,
            arrive_by,
            now,
        )
        if planned is None:
            transit_status = 'out_of_service'
        else:
            base, bike_mix, bus, notes = planned
    bike_data = await bike_task
    pm, pm_note = bus_pm.pm_only(bicycle)
    if pm_note is not None:
        notes.append(pm_note)

    return RecommendResponse(
        fetched_at=state.now().replace(microsecond=0),
        transit=TransitStatus(status=transit_status),
        bike_data=BikeDataStatus(status=bike_data.status, fetched_at=bike_data.fetched_at),
        base=base,
        bike_mix=bike_mix,
        bus_only=bus,
        pm_only=pm,
        notes=notes,
    )
