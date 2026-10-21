'''직선거리 계산'''

import math

EARTH_RADIUS = 6371000  # m


def distance_m(a, b):
    '''두 좌표 (x 경도, y 위도) 사이의 직선거리(m). 하버사인 공식'''
    lon1, lat1, lon2, lat2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = (
        math.sin((lat2 - lat1) / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    )
    return 2 * EARTH_RADIUS * math.asin(math.sqrt(h))


def line(points):
    '''지도 선 좌표 목록 (api_spec.md 4.9). 소수 다섯째 자리(약 1m)로 맞춘 (경도, 위도) 목록'''
    return [(round(x, 5), round(y, 5)) for x, y in points]
