'''버스 전용, PM 전용 경로 (rules.md 6, 7장)'''

from app.geo import line
from app.planner.base import build_transit, is_ok, wait_seconds
from app.schemas import Note, PmOnly


def bus_candidates(routes):
    '''경로 유형이 버스인 경로를 카카오 총 소요 시간 + 승차 대기 시간이 짧은 순으로

    - 동점이면 카카오 응답 순서가 앞선 경로 (rules.md 6장)
    '''
    buses = [route for route in routes if route.kind == 'bus']
    return sorted(buses, key=lambda route: (route.total_time + wait_seconds(route), route.index))


def pick_bus_route(routes):
    '''버스 전용 경로 후보 중 첫 번째. 버스 경로가 없으면 None'''
    candidates = bus_candidates(routes)
    return candidates[0] if candidates else None


def bus_only(bus_route, base_index, origin_walk, destination_walk, unknown_steps=frozenset()):
    '''버스 전용 경로. (경로 또는 None, 경로를 만들지 않은 이유 또는 None)'''
    if bus_route is None:
        return None, Note(target='busOnly', reason='none')
    if bus_route.index == base_index:
        return None, Note(target='busOnly', reason='same_as_base')
    return build_transit(bus_route, origin_walk, destination_walk, unknown_steps), None


def pm_only(bicycle):
    '''PM 전용 경로 (카카오 자전거 경로 SHORTEST 값 그대로). 조회에 실패하면 None'''
    if not is_ok(bicycle):
        return None, Note(target='pmOnly', reason='route_failed')
    pm = PmOnly(
        total_seconds=bicycle.seconds,
        total_distance=bicycle.distance,
        points=line(bicycle.points),
    )
    return pm, None
