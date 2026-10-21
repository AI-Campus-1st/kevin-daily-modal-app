'''대여소 선택 (rules.md 5.1)

- 따릉이 구간 시작 좌표에서 가장 가까운 대여 대여소, 끝 좌표에서 가장 가까운 반납 대여소
- 재고를 모르면(대여정보 조회 실패) 재고 조건 없이 가장 가까운 대여소 (rules.md 10장)
'''

from dataclasses import dataclass

from app import config
from app.geo import distance_m


@dataclass(frozen=True)
class Pick:
    '''고른 대여소와 기준 좌표까지의 직선거리(m)'''

    station: object
    distance: float


def nearest(stations, point, has_stock):
    '''반경 BIKE_STATION_RADIUS 안에서 has_stock을 만족하는 가장 가까운 대여소. 없으면 None'''
    best = None
    for station in stations:
        if not has_stock(station):
            continue
        distance = distance_m(point, (station.x, station.y))
        if distance > config.BIKE_STATION_RADIUS:
            continue
        if best is None or distance < best.distance:
            best = Pick(station=station, distance=distance)
    return best


def select_rent(stations, point, stock_known):
    '''대여 대여소. 재고를 알면 대여 가능 대수 1대 이상'''
    return nearest(stations, point, lambda s: not stock_known or s.bikes >= 1)


def select_return(stations, point, stock_known):
    '''반납 대여소. 재고를 알면 반납 가능 거치대 1개 이상'''
    return nearest(stations, point, lambda s: not stock_known or s.racks >= 1)


def select_pair(stations, start, end, stock_known):
    '''(대여 대여소, 반납 대여소). 하나라도 없거나 두 대여소가 같으면 None'''
    rent = select_rent(stations, start, stock_known)
    if rent is None:
        return None
    ret = select_return(stations, end, stock_known)
    if ret is None or ret.station.id == rent.station.id:
        return None
    return rent, ret
