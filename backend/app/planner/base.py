'''기본 경로, 출발 도보와 도착 도보 반영, 총 소요 시간, PM 절감 시간 (rules.md 3, 4장)

- 외부 호출 결과(카카오 경로, 도보 경로)를 인자로 받는 순수 함수
'''

from app import config
from app.geo import line
from app.schemas import BaseRoute, PmSaving, TransitLeg, TransitRoute, Vehicle, WalkLeg


def is_ok(path):
    '''도보, 자전거 경로 조회 결과가 성공인지. 조회하지 않았으면(None) 실패로 봄'''
    return path is not None and path.ok


def step_wait(step):
    '''구간 하나의 승차 대기 시간 (rules.md 3.3). 도보는 0'''
    if step.kind == 'bus':
        return config.BUS_WAIT_SECONDS
    if step.kind == 'subway':
        return config.SUBWAY_WAIT_SECONDS
    return 0


def wait_seconds(route):
    '''경로 전체의 승차 대기 시간'''
    return sum(step_wait(step) for step in route.steps)


def edge_points(route):
    '''(출발 도보의 끝, 도착 도보의 시작) 좌표

    - 출발 도보의 끝은 첫 구간 첫 좌표, 도착 도보의 시작은 마지막 구간 마지막 좌표
    - 좌표가 없으면 None
    '''
    if not route.steps:
        return None, None
    first = route.steps[0].points
    last = route.steps[-1].points
    return (first[0] if first else None), (last[-1] if last else None)


def step_leg(step, unknown=False):
    '''카카오 구간 하나를 응답의 구간으로 바꿈. 도보 구간은 환승 도보(edge 없음)

    - unknown: 운행 시간을 확인하지 못한 노선이 있는 구간 (rules.md 3.4.4)
    '''
    if step.kind == 'walk':
        return WalkLeg(
            seconds=step.seconds, distance=step.distance, edge=None, points=line(step.points)
        )
    return TransitLeg(
        type=step.kind,
        seconds=step.seconds,
        wait_seconds=step_wait(step),
        distance=step.distance,
        stops=list(step.stops),
        vehicles=[Vehicle(type=kind, name=name) for kind, name in step.vehicles],
        service_unknown=unknown,
        points=line(step.points),
    )


def edge_leg(path, edge):
    '''출발 도보 또는 도착 도보 구간'''
    return WalkLeg(
        seconds=path.seconds, distance=path.distance, edge=edge, points=line(path.points)
    )


def transit_fields(route, origin_walk, destination_walk, unknown_steps=frozenset()):
    '''대중교통 경로 형식(api_spec.md 4.3)의 값

    - 출발 도보, 도착 도보 모두 조회에 성공하면 구간 목록 처음과 끝에 넣고 총 소요 시간을 다시 계산
    - 하나라도 실패하면 카카오 총 소요 시간 + 승차 대기 시간, 카카오 총 거리 (rules.md 3.2)
    '''
    wait = wait_seconds(route)
    legs = [step_leg(step, index in unknown_steps) for index, step in enumerate(route.steps)]
    edge_known = is_ok(origin_walk) and is_ok(destination_walk)
    if edge_known:
        legs = [edge_leg(origin_walk, 'origin'), *legs, edge_leg(destination_walk, 'destination')]
        total = (
            origin_walk.seconds
            + sum(step.seconds for step in route.steps)
            + destination_walk.seconds
            + wait
        )
        distance = (
            origin_walk.distance
            + sum(step.distance for step in route.steps)
            + destination_walk.distance
        )
    else:
        total = route.total_time + wait
        distance = route.total_distance
    return {
        'route_index': route.index,
        'type': route.kind,
        'total_seconds': total,
        'total_distance': distance,
        'wait_seconds': wait,
        'edge_walk_known': edge_known,
        'transfers': route.transfers,
        'fare': route.fare,
        'legs': legs,
        'service_unknown': bool(unknown_steps),
    }


def walk_saving(path):
    '''도보 하나를 킥보드 속도로 바꿀 때 줄어드는 시간(초)

    - 음수이면 0, 초 미만은 버림 (rules.md 4장)
    '''
    return max(int(path.seconds - path.distance / config.KICKBOARD_SPEED), 0)


def pm_saving(origin_walk, destination_walk):
    '''기본 경로의 PM 절감 시간. 출발 도보, 도착 도보 중 하나라도 모르면 None'''
    if not (is_ok(origin_walk) and is_ok(destination_walk)):
        return None
    first = walk_saving(origin_walk)
    last = walk_saving(destination_walk)
    return PmSaving(first_seconds=first, last_seconds=last, total_seconds=first + last)


def build_base(route, origin_walk, destination_walk, unknown_steps=frozenset()):
    '''기본 경로 (운행 시간 안인 첫 번째 경로, rules.md 3장)'''
    return BaseRoute(
        **transit_fields(route, origin_walk, destination_walk, unknown_steps),
        pm_saving=pm_saving(origin_walk, destination_walk),
    )


def build_transit(route, origin_walk, destination_walk, unknown_steps=frozenset()):
    '''출발 도보, 도착 도보를 반영한 대중교통 경로 (버스 전용 경로에 사용)'''
    return TransitRoute(**transit_fields(route, origin_walk, destination_walk, unknown_steps))
