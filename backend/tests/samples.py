'''테스트용 예시 응답 (datasource.md 형식)

- 실제 외부 API를 호출하지 않고, 카카오, 따릉이 응답 형식대로 만든 값을 사용
- 좌표는 서울 안의 가상 지점
'''

from app.clients.bike import Station
from app.clients.kakao import PathResult, parse_route

ORIGIN = (127.0000, 37.5000)
DESTINATION = (127.0500, 37.5300)


def offset(point, east_m=0.0, north_m=0.0):
    '''point에서 동쪽, 북쪽으로 미터만큼 옮긴 좌표 (위도 37.5 부근 근사)'''
    return (point[0] + east_m / 88200, point[1] + north_m / 111000)


def step(kind, seconds, distance, points, stops=None, vehicles=None):
    '''카카오 대중교통 응답의 steps 하나'''
    return {
        'properties': {
            'type': kind,
            'guidance': '',
            'distance': distance,
            'time': seconds,
            'stops': [{'name': name} for name in (stops or [])],
            'vehicles': [{'type': t, 'name': n} for t, n in (vehicles or [])],
        },
        'path': {'points': [list(p) for p in points]},
    }


def bus(seconds, start, end, distance=None):
    return step(
        'BUS', seconds, distance or seconds * 4, [start, end], ['승차', '하차'], [('간선', '101')]
    )


def subway(seconds, start, end, distance=None):
    return step(
        'SUBWAY',
        seconds,
        distance or seconds * 10,
        [start, end],
        ['A역', 'B역'],
        [('수도권', '2호선')],
    )


def raw_route(kind, steps, total_time=None, total_distance=None, transfers=0, fare=1550):
    '''카카오 대중교통 응답의 routes 하나. totalTime을 주지 않으면 구간 합 + 600초(빠진 도보)'''
    step_time = sum(s['properties']['time'] for s in steps)
    step_distance = sum(s['properties']['distance'] for s in steps)
    return {
        'properties': {
            'type': kind,
            'totalDistance': total_distance or step_distance + 600,
            'totalTime': total_time or step_time + 600,
            'transfers': transfers,
            'fare': {'min': fare, 'max': fare + 100},
        },
        'steps': steps,
    }


def route(index, kind, steps, **kwargs):
    '''정리된 Route (app.clients.kakao.parse_route 결과)'''
    return parse_route(index, raw_route(kind, steps, **kwargs))


def transit_response(*routes, status='OK'):
    '''카카오 대중교통 응답 전체'''
    return {
        'status': status,
        'properties': {'total': len(routes)},
        'routes': list(routes),
    }


def path_response(seconds, distance, status='OK', points=None):
    '''카카오 도보, 자전거 응답. points를 주면 구간 두 개로 나눠 route.legs[].steps[]에 넣음'''
    if status != 'OK':
        return {'status': status}
    route = {'properties': {'totalTime': seconds, 'totalDistance': distance}}
    if points:
        middle = len(points) // 2
        halves = (points[: middle + 1], points[middle:])
        steps = [
            {'distance': 0, 'time': 0, 'path': {'points': [list(p) for p in half]}}
            for half in halves
        ]
        route['legs'] = [{'steps': steps}]
    return {'status': 'OK', 'route': route}


def walk(seconds, distance=None):
    '''조회에 성공한 도보, 자전거 경로'''
    return PathResult(status='ok', seconds=seconds, distance=distance or seconds)


FAILED = PathResult(status='unavailable')


def station(sid, point, bikes=5, racks=5):
    return Station(id=sid, name=f'{sid} 대여소', x=point[0], y=point[1], bikes=bikes, racks=racks)


def bike_row(sid, point, bikes=5, rack_total=10):
    '''따릉이 bikeList 응답의 row 하나 (값은 모두 문자열)'''
    return {
        'rackTotCnt': str(rack_total),
        'stationName': f'{sid} 대여소',
        'parkingBikeTotCnt': str(bikes),
        'shared': '50',
        'stationLatitude': str(point[1]),
        'stationLongitude': str(point[0]),
        'stationId': sid,
    }


def bike_page(rows, code='INFO-000'):
    '''따릉이 bikeList 응답 한 쪽'''
    return {
        'rentBikeStatus': {
            'list_total_count': len(rows),
            'RESULT': {'CODE': code, 'MESSAGE': ''},
            'row': rows,
        }
    }
