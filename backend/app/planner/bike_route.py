'''따릉이 구간 시간, First, Last mile 대체, 전 구간 따릉이, 조건 판단 (rules.md 5.2 ~ 5.5)

- 대여소 선택 결과와 카카오 도보, 자전거 경로 조회 결과를 인자로 받는 순수 함수
- 전 구간 따릉이 경로는 First, Last mile 대체 경로를 만들지 못했을 때만 조회
  (2026-10-20 사용자 결정)
'''

from dataclasses import dataclass

from app import config
from app.geo import line
from app.planner.base import is_ok
from app.planner.miles import alighting_index, boarding_index
from app.planner.stations import select_pair
from app.schemas import BikeLeg, BikeMix, Conditions, Note, RentStation, ReturnStation


@dataclass(frozen=True)
class SegmentPlan:
    '''대여소를 고른 따릉이 구간 (카카오 경로 조회 전)'''

    mile: str  # 'first', 'last', 'full'
    start: tuple
    end: tuple
    rent: object  # stations.Pick
    ret: object  # stations.Pick

    @property
    def rent_point(self):
        return (self.rent.station.x, self.rent.station.y)

    @property
    def return_point(self):
        return (self.ret.station.x, self.ret.station.y)


@dataclass(frozen=True)
class Segment:
    '''따릉이 구간을 만든 결과

    - outcome 'built': leg에 구간이 있음
    - 'no_station': 조건에 맞는 대여소가 없음
    - 'route_failed': 카카오 도보, 자전거 경로 조회 실패
    - 'skipped': 출발 도보 또는 도착 도보를 몰라 만들지 않음 (rules.md 3.2)
    '''

    outcome: str
    leg: BikeLeg | None = None


@dataclass(frozen=True)
class FirstLast:
    '''First, Last mile 대체 경로'''

    total_seconds: int
    transfers: int
    legs: list


def plan_segment(mile, start, end, stations, stock_known):
    '''대여소를 골라 SegmentPlan을 만듦. 대여소가 없으면 None (rules.md 5.1)'''
    pair = select_pair(stations, start, end, stock_known)
    if pair is None:
        return None
    rent, ret = pair
    return SegmentPlan(mile=mile, start=start, end=end, rent=rent, ret=ret)


def build_segment(plan, replaced_seconds, to_station, ride, from_station, stock_known):
    '''따릉이 구간 소요 시간 계산 (rules.md 5.2). 경로 조회 중 하나라도 실패하면 route_failed'''
    if not (is_ok(to_station) and is_ok(ride) and is_ok(from_station)):
        return Segment(outcome='route_failed')
    seconds = (
        to_station.seconds
        + config.BIKE_RENT_SECONDS
        + ride.seconds
        + config.BIKE_RETURN_SECONDS
        + from_station.seconds
    )
    rent = plan.rent.station
    ret = plan.ret.station
    leg = BikeLeg(
        mile=plan.mile,
        seconds=seconds,
        replaced_seconds=replaced_seconds,
        to_station_seconds=to_station.seconds,
        rent_seconds=config.BIKE_RENT_SECONDS,
        ride_seconds=ride.seconds,
        return_seconds=config.BIKE_RETURN_SECONDS,
        from_station_seconds=from_station.seconds,
        rent_station=RentStation(
            id=rent.id,
            name=rent.name,
            available_bikes=rent.bikes if stock_known else None,
            distance=round(plan.rent.distance),
            x=rent.x,
            y=rent.y,
        ),
        return_station=ReturnStation(
            id=ret.id,
            name=ret.name,
            available_racks=ret.racks if stock_known else None,
            distance=round(plan.ret.distance),
            x=ret.x,
            y=ret.y,
        ),
        to_station_points=line(to_station.points),
        ride_points=line(ride.points),
        from_station_points=line(from_station.points),
    )
    return Segment(outcome='built', leg=leg)


def condition1(mile, station_walk):
    '''한쪽 mile의 조건 1 (rules.md 5.4)

    - mile에 버스가 있으면 출발지 → 첫 지하철역(마지막 지하철역 → 도착지)의 카카오 도보 경로 시간
    - 버스가 없으면 mile 전체가 도보이므로 원래 mile 시간
    - 출발 도보(도착 도보)를 모르거나 도보 경로 조회에 실패하면 만족하지 않음
    '''
    if not mile.known:
        return False
    if mile.has_bus:
        return is_ok(station_walk) and station_walk.seconds >= config.BIKE_COND1_WALK
    return mile.original_seconds >= config.BIKE_COND1_WALK


def should_replace(mile, segment, cond1):
    '''mile을 따릉이 구간으로 바꿀지 (rules.md 5.3)'''
    if not mile.known or segment.outcome != 'built':
        return False
    return cond1 or segment.leg.seconds < mile.original_seconds


def make_first_last(
    route, base, first_mile, last_mile, first_seg, last_seg, cond1_first, cond1_last
):
    '''First, Last mile 대체 경로. 어느 쪽도 바꾸지 않으면 None (rules.md 5.3)'''
    replace_first = should_replace(first_mile, first_seg, cond1_first)
    replace_last = should_replace(last_mile, last_seg, cond1_last)
    if not (replace_first or replace_last):
        return None

    board = boarding_index(route)
    alight = alighting_index(route)
    if base.edge_walk_known:
        origin_edge, step_legs, destination_edge = [base.legs[0]], base.legs[1:-1], [base.legs[-1]]
    else:
        origin_edge, step_legs, destination_edge = [], list(base.legs), []

    head = [first_seg.leg] if replace_first else origin_edge + step_legs[:board]
    middle = step_legs[board : alight + 1]
    tail = [last_seg.leg] if replace_last else step_legs[alight + 1 :] + destination_edge
    legs = head + middle + tail

    total = base.total_seconds
    if replace_first:
        total += first_seg.leg.seconds - first_mile.original_seconds
    if replace_last:
        total += last_seg.leg.seconds - last_mile.original_seconds
    rides = sum(1 for leg in legs if leg.type in ('bus', 'subway'))
    return FirstLast(total_seconds=total, transfers=max(rides - 1, 0), legs=legs)


def failure_reason(segments):
    '''만들지 못한 따릉이 구간들의 이유. 경로 조회 실패가 있으면 route_failed, 아니면 no_station'''
    outcomes = {segment.outcome for segment in segments if segment is not None}
    return 'route_failed' if 'route_failed' in outcomes else 'no_station'


def decide(base, cond1_first, cond1_last, first_seg, last_seg, first_last, full_seg, stock_known):
    '''표시 조건 판단 (rules.md 5.4)

    - 결과: (따릉이 포함 경로 또는 None, 경로를 만들지 않은 이유 또는 None)
    '''
    cond1 = cond1_first or cond1_last
    cond2 = None
    if first_last is not None:
        cond2 = first_last.total_seconds < base.total_seconds * config.BIKE_COND2_RATIO
    cond3 = None
    if full_seg is not None and full_seg.outcome == 'built':
        cond3 = full_seg.leg.seconds < config.BIKE_COND3_TOTAL
    conditions = Conditions(first=cond1, second=cond2, third=cond3)

    if first_last is not None and (cond1 or cond2):
        mix = BikeMix(
            kind='first_last',
            conditions=conditions,
            total_seconds=first_last.total_seconds,
            transfers=first_last.transfers,
            stock_known=stock_known,
            legs=first_last.legs,
            service_unknown=any(getattr(leg, 'service_unknown', False) for leg in first_last.legs),
        )
        return mix, None
    if cond3:
        mix = BikeMix(
            kind='full',
            conditions=conditions,
            total_seconds=full_seg.leg.seconds,
            transfers=0,
            stock_known=stock_known,
            legs=[full_seg.leg],
        )
        return mix, None

    # 경로를 만들지 않은 이유
    if cond1:
        # 조건 1을 만족했지만 First, Last mile 대체 경로를 만들지 못함
        reason = failure_reason([s for s in (first_seg, last_seg) if s.outcome != 'built'])
    elif any(s is not None and s.outcome == 'built' for s in (first_seg, last_seg, full_seg)):
        reason = 'no_condition'
    else:
        reason = failure_reason([first_seg, last_seg, full_seg])
    return None, Note(target='bikeMix', reason=reason)
