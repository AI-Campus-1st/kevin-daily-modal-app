'''첫 승차 지점, 마지막 하차 지점, First, Last mile 구간 (rules.md 1장, 3.1)

- 첫 승차 지점: 첫 지하철 구간의 첫 좌표. 지하철이 없으면 첫 버스 구간의 첫 좌표
- 마지막 하차 지점: 마지막 지하철 구간의 마지막 좌표. 지하철이 없으면 마지막 버스 구간의 마지막 좌표
'''

from dataclasses import dataclass

from app.planner.base import is_ok, step_wait


@dataclass(frozen=True)
class Mile:
    '''First mile 또는 Last mile 하나'''

    side: str  # 'first', 'last'
    start: tuple | None  # 따릉이 구간 시작 좌표
    end: tuple | None  # 따릉이 구간 끝 좌표
    steps: tuple  # mile 안의 카카오 구간 (출발 도보, 도착 도보 제외)
    known: bool  # 출발 도보(Last mile은 도착 도보) 조회에 성공하고 좌표가 있음
    original_seconds: int  # 바꾸기 전 mile 시간. known이 거짓이면 0

    @property
    def has_bus(self):
        return any(step.kind == 'bus' for step in self.steps)


def boarding_index(route):
    '''첫 승차 구간의 위치. 지하철 우선, 없으면 버스. 둘 다 없으면 None'''
    for kind in ('subway', 'bus'):
        for index, step in enumerate(route.steps):
            if step.kind == kind:
                return index
    return None


def alighting_index(route):
    '''마지막 하차 구간의 위치. 지하철 우선, 없으면 버스. 둘 다 없으면 None'''
    for kind in ('subway', 'bus'):
        for index in range(len(route.steps) - 1, -1, -1):
            if route.steps[index].kind == kind:
                return index
    return None


def boarding_point(route):
    '''첫 승차 지점 좌표. 없으면 None'''
    index = boarding_index(route)
    if index is None or not route.steps[index].points:
        return None
    return route.steps[index].points[0]


def alighting_point(route):
    '''마지막 하차 지점 좌표. 없으면 None'''
    index = alighting_index(route)
    if index is None or not route.steps[index].points:
        return None
    return route.steps[index].points[-1]


def mile_seconds(edge_walk, steps):
    '''원래 mile 시간 (rules.md 5.3)

    - 출발(도착) 도보 시간 + 구간 시간의 합 + mile 안 버스 구간의 승차 대기 시간
    '''
    return edge_walk.seconds + sum(step.seconds + step_wait(step) for step in steps)


def first_mile(route, origin, origin_walk):
    '''출발지 → 첫 승차 지점'''
    index = boarding_index(route)
    point = boarding_point(route)
    steps = route.steps[:index] if index is not None else ()
    known = is_ok(origin_walk) and point is not None
    return Mile(
        side='first',
        start=origin,
        end=point,
        steps=tuple(steps),
        known=known,
        original_seconds=mile_seconds(origin_walk, steps) if known else 0,
    )


def last_mile(route, destination, destination_walk):
    '''마지막 하차 지점 → 도착지'''
    index = alighting_index(route)
    point = alighting_point(route)
    steps = route.steps[index + 1 :] if index is not None else ()
    known = is_ok(destination_walk) and point is not None
    return Mile(
        side='last',
        start=point,
        end=destination,
        steps=tuple(steps),
        known=known,
        original_seconds=mile_seconds(destination_walk, steps) if known else 0,
    )
