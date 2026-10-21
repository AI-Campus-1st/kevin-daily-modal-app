'''운행 시간(첫차, 막차) 판단 (rules.md 3.4)

- 노선별 운행 범위 조회 결과를 인자로 받는 순수 함수
- 시각은 그날 0시부터의 초. 자정을 넘는 막차는 86,400초 이상으로 다룸
'''

import re
from dataclasses import dataclass
from datetime import timedelta

from app import config
from app.geo import distance_m
from app.planner.base import step_wait, wait_seconds

DAY = 24 * 3600


@dataclass(frozen=True)
class Window:
    '''노선 하나의 운행 범위. start ~ end(초). end는 86,400 이상일 수 있음'''

    start: int
    end: int


@dataclass(frozen=True)
class Check:
    '''경로 하나의 운행 판단 결과

    - running: 모든 노선이 승차 시각에 운행하거나 운행 범위를 모름
    - unknown_steps: 운행 범위를 모르는 노선이 있는 구간 위치 (rules.md 3.4.4)
    '''

    running: bool
    unknown_steps: frozenset = frozenset()


def expected_total(route):
    '''예상 총 소요 시간 = 카카오 총 소요 시간 + 승차 대기 시간 (3.4.1)'''
    return route.total_time + wait_seconds(route)


def departure(route, arrive_by, now):
    '''경로의 기준 출발 시각 (3.4.1)

    - arrive_by(목표 도착 시각 − 여유 시간)가 없으면 지금 시각
    - 역산한 시각이 지금보다 앞서면 지금 시각
    '''
    if arrive_by is None:
        return now
    return max(arrive_by - timedelta(seconds=expected_total(route)), now)


def origin_walk_estimate(route, origin, destination):
    '''출발 쪽 도보 추정 시간 (3.4.2)

    - 카카오 총 소요 시간 − 구간 시간의 합(빠진 출발, 도착 도보)을
      출발지 → 첫 구간 시작, 마지막 구간 끝 → 도착지의 직선거리 비율로 나눔
    '''
    missing = max(route.total_time - sum(step.seconds for step in route.steps), 0)
    first = route.steps[0].points[0] if route.steps and route.steps[0].points else None
    last = route.steps[-1].points[-1] if route.steps and route.steps[-1].points else None
    head = distance_m(origin, first) if first else 0.0
    tail = distance_m(last, destination) if last else 0.0
    if head + tail == 0:
        return missing // 2
    return round(missing * head / (head + tail))


def boarding_offsets(route, origin, destination):
    '''기준 출발 시각부터 각 버스, 지하철 구간에 오르기까지 걸리는 초. {구간 위치: 초}'''
    elapsed = origin_walk_estimate(route, origin, destination)
    offsets = {}
    for index, step in enumerate(route.steps):
        elapsed += step_wait(step)
        if step.kind in ('bus', 'subway'):
            offsets[index] = elapsed
        elapsed += step.seconds
    return offsets


def runs_at(window, seconds):
    '''운행 범위 안인지. 자정 이후 승차는 전날 운행 범위(24시 이상)로도 확인'''
    return any(window.start <= t <= window.end for t in (seconds, seconds + DAY))


def check_route(boardings):
    '''경로의 운행 판단 (3.4, 3.4.4)

    - boardings: [(구간 위치, 승차 시각 초, (노선마다 Window 또는 None(모름), ...))]
    - 운행 범위 밖인 노선이 하나라도 있으면 running 거짓 (D-36)
    - 노선 목록이 비어 있는 구간도 모름으로 봄
    '''
    unknown = set()
    for index, seconds, windows in boardings:
        if not windows:
            unknown.add(index)
        for window in windows:
            if window is None:
                unknown.add(index)
            elif not runs_at(window, seconds):
                return Check(running=False)
    return Check(running=True, unknown_steps=frozenset(unknown))


def bus_window(first, last, length_m):
    '''버스 운행 범위 = 기점 첫차 ~ 기점 막차 + 노선 전체 운행 시간 (3.4.3, D-37)

    - first, last: 기점 첫차, 막차(초). 막차가 첫차보다 이르면 자정을 넘긴 것으로 봄
    - 노선 전체 운행 시간 = 노선 길이 ÷ BUS_ROUTE_SPEED
    '''
    if last < first:
        last += DAY
    return Window(start=first, end=last + round(length_m / config.BUS_ROUTE_SPEED))


def route_number(name):
    '''버스 노선 번호 조회용 이름. 카카오 이름의 괄호 부분을 뺌

    - 예: 'N13(심야)' → 'N13' (datasource.md C-12)
    '''
    return re.sub(r'\(.*?\)', '', name or '').strip()


def station_key(name):
    '''역 이름 비교용 열쇠. 공백, 괄호 안 글자, 끝의 '역'을 뺌 (3.4.3)'''
    name = re.sub(r'\(.*?\)', '', name or '')
    name = re.sub(r'\s+', '', name)
    if len(name) > 1 and name.endswith('역'):
        name = name[:-1]
    return name


def rail_window(directions, station, next_station):
    '''지하철 승차역의 운행 범위 (3.4.3, D-41)

    - directions: 방향마다 {역 열쇠: (첫차 초, 막차 초)}
    - 첫차가 승차역 다음에 다음 역을 지나는 방향이 하나이면 그 방향의 범위
    - 정하지 못하면 승차역이 있는 방향들 중 이른 첫차 ~ 늦은 막차. 승차역이 없으면 None
    '''
    here_key = station_key(station)
    found = [table[here_key] for table in directions if here_key in table]
    if not found:
        return None
    index = rail_direction(directions, station, next_station)
    if index is not None:
        here = directions[index][here_key]
        return Window(start=here[0], end=here[1])
    return Window(start=min(h[0] for h in found), end=max(h[1] for h in found))


def rail_direction(directions, station, next_station):
    '''첫차가 승차역 다음에 다음 역을 지나는 방향의 위치 (D-41). 하나로 정하지 못하면 None'''
    here_key = station_key(station)
    next_key = station_key(next_station)
    matched = [
        index
        for index, table in enumerate(directions)
        if here_key in table and next_key in table and table[next_key][0] > table[here_key][0]
    ]
    return matched[0] if len(matched) == 1 else None


def day_type(day, holidays):
    '''요일 구분 (3.4.3). 'weekday', 'saturday', 'sunday', 'holiday', 모르면 None

    - holidays: {연도: 평일 공휴일 날짜 집합}. 그 해 목록이 없으면 평일은 None (datasource.md 7.1)
    '''
    if day.weekday() == 5:
        return 'saturday'
    if day.weekday() == 6:
        return 'sunday'
    year = holidays.get(day.year)
    if year is None:
        return None
    return 'holiday' if day in year else 'weekday'
