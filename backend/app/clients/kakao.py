'''카카오 API 호출과 응답 정리 (datasource.md 3 ~ 6장)

- DS-1 주소 검색, DS-2 대중교통 경로, DS-3 도보 경로, DS-4 자전거 경로
- 응답을 경로 만들기(app/planner/)가 쓰는 데이터 클래스로 정리
- 장애, 사용량 초과, 시간 초과는 예외 대신 status 'unavailable'로 돌려줌
- 로그에는 호출 종류와 결과 상태만 남김. 주소, 좌표, 검색어, 인증키는 남기지 않음
'''

import asyncio
import logging
from dataclasses import dataclass

import httpx

from app import config
from app.cache import TTLCache, round_point

logger = logging.getLogger('app.kakao')

# 대중교통 경로에서 '결과 없음'으로 보는 상태 (datasource.md 5장)
TRANSIT_NO_RESULT = {'NO_RESULTS', 'STARTNODES_NULL', 'ENDNODES_NULL', 'EQUAL_POINTS'}
# 도보, 자전거 경로에서 '결과 없음'으로 보는 상태 (datasource.md 6장)
PATH_NO_RESULT = {
    'SAME_POINT',
    'START_LINK_NOT_FOUND',
    'END_LINK_NOT_FOUND',
    'TOO_MANY_SEARCH_LINK',
    'TOO_FAR_AWAY',
    'ROUTE_RESULT_NOT_FOUND',
}

STEP_KINDS = {'WALKING': 'walk', 'BUS': 'bus', 'SUBWAY': 'subway'}
ROUTE_KINDS = {'BUS': 'bus', 'SUBWAY': 'subway', 'BUS_AND_SUBWAY': 'bus_subway'}


class ParseError(Exception):
    '''응답 형식이 datasource.md와 다름'''


# 응답 형식이 달라 정리하지 못할 때 생기는 예외. 모두 조회 실패(unavailable)로 처리
PARSE_ERRORS = (KeyError, TypeError, ValueError, IndexError, AttributeError, ParseError)


@dataclass(frozen=True)
class AddressCandidate:
    address_name: str
    road_address: str | None
    jibun_address: str | None
    building_name: str | None
    x: float
    y: float
    place_name: str | None = None  # 키워드 장소 검색 결과만 (DS-7)


@dataclass(frozen=True)
class AddressResult:
    status: str
    items: tuple = ()
    is_end: bool = True


@dataclass(frozen=True)
class Step:
    '''대중교통 경로의 구간 하나 (카카오 steps 하나)'''

    kind: str  # 'walk', 'bus', 'subway'
    seconds: int
    distance: int
    stops: tuple = ()  # 정류장, 역 이름
    vehicles: tuple = ()  # (종류, 노선 이름)
    points: tuple = ()  # (경도, 위도) 좌표 목록


@dataclass(frozen=True)
class Route:
    '''대중교통 경로 하나'''

    index: int  # 카카오 응답 순서 (0부터)
    kind: str  # 'bus', 'subway', 'bus_subway'
    total_time: int  # 카카오 총 소요 시간 (출발, 도착 도보 포함, 승차 대기 미포함)
    total_distance: int
    transfers: int
    fare: int | None
    steps: tuple


@dataclass(frozen=True)
class TransitResult:
    status: str
    routes: tuple = ()


@dataclass(frozen=True)
class PathResult:
    '''도보 또는 자전거 경로 조회 결과'''

    status: str
    seconds: int = 0
    distance: int = 0
    points: tuple = ()  # (경도, 위도) 좌표 목록. 지도 선에만 사용 (권장 F-16)

    @property
    def ok(self):
        return self.status == 'ok'


def to_int(value):
    '''숫자 또는 숫자 문자열을 반올림한 정수로 바꿈'''
    return int(round(float(value)))


def to_text(value):
    '''문자열 항목 정리. 값이 없거나 null이면 빈 문자열'''
    return '' if value is None else str(value)


def parse_address(data):
    '''DS-1 응답을 AddressResult로 정리'''
    items = []
    for doc in data['documents']:
        road = doc.get('road_address') or {}
        jibun = doc.get('address') or {}
        items.append(
            AddressCandidate(
                address_name=doc['address_name'],
                road_address=road.get('address_name') or None,
                jibun_address=jibun.get('address_name') or None,
                building_name=road.get('building_name') or None,
                x=float(doc['x']),
                y=float(doc['y']),
            )
        )
    is_end = bool((data.get('meta') or {}).get('is_end', True))
    if not items:
        return AddressResult(status='no_result', is_end=True)
    return AddressResult(status='ok', items=tuple(items), is_end=is_end)


def parse_keyword(data):
    '''DS-7 키워드 장소 검색 응답을 AddressResult로 정리 (datasource.md 4.1)

    - 도로명 주소가 빈 문자열인 장소가 있어 None으로 바꿈 (C-10)
    - 대표 주소는 도로명 주소, 없으면 지번 주소. 둘 다 없는 장소는 뺌
    '''
    items = []
    for doc in data['documents']:
        road = to_text(doc.get('road_address_name')).strip() or None
        jibun = to_text(doc.get('address_name')).strip() or None
        if not (road or jibun):
            continue
        items.append(
            AddressCandidate(
                address_name=road or jibun,
                road_address=road,
                jibun_address=jibun,
                building_name=None,
                x=float(doc['x']),
                y=float(doc['y']),
                place_name=to_text(doc.get('place_name')).strip() or None,
            )
        )
    is_end = bool((data.get('meta') or {}).get('is_end', True))
    if not items:
        return AddressResult(status='no_result', is_end=True)
    return AddressResult(status='ok', items=tuple(items), is_end=is_end)


def parse_step(raw):
    '''steps 하나를 Step으로 정리'''
    props = raw['properties']
    kind = STEP_KINDS.get(props['type'])
    if kind is None:
        raise ParseError('알 수 없는 구간 종류')
    points = tuple((float(p[0]), float(p[1])) for p in (raw.get('path') or {}).get('points') or [])
    return Step(
        kind=kind,
        seconds=to_int(props['time']),
        distance=to_int(props['distance']),
        stops=tuple(to_text(s.get('name')) for s in props.get('stops') or []),
        vehicles=tuple(
            (to_text(v.get('type')), to_text(v.get('name'))) for v in props.get('vehicles') or []
        ),
        points=points,
    )


def parse_route(index, raw):
    '''routes 하나를 Route로 정리'''
    props = raw['properties']
    kind = ROUTE_KINDS.get(props['type'])
    if kind is None:
        raise ParseError('알 수 없는 경로 유형')
    # 요금은 {'value': 값} 또는 {'min': 값, 'max': 값} 형식 (2026-10-20 실제 호출 확인)
    # 범위이면 min 사용
    fare_info = props.get('fare') or {}
    fare = fare_info.get('value', fare_info.get('min'))
    return Route(
        index=index,
        kind=kind,
        total_time=to_int(props['totalTime']),
        total_distance=to_int(props['totalDistance']),
        transfers=int(props.get('transfers') or 0),
        fare=None if fare is None else to_int(fare),
        steps=tuple(parse_step(step) for step in raw['steps']),
    )


def parse_transit(data):
    '''DS-2 응답을 TransitResult로 정리'''
    status = data.get('status')
    if status in TRANSIT_NO_RESULT:
        return TransitResult(status='no_result')
    if status != 'OK':
        return TransitResult(status='unavailable')
    routes = tuple(parse_route(i, raw) for i, raw in enumerate(data.get('routes') or []))
    if not routes:
        return TransitResult(status='no_result')
    return TransitResult(status='ok', routes=routes)


def path_points(route):
    '''도보, 자전거 경로의 좌표 목록 (datasource.md 6장 route.legs[].steps[].path.points)

    - 구간 좌표를 순서대로 이어 붙이고, 앞 구간 끝과 같은 좌표는 한 번만 넣음
    - 형식이 다르면 빈 튜플. 좌표는 지도 선에만 쓰므로 시간, 거리 결과는 그대로 둠
    '''
    try:
        points = []
        for leg in route.get('legs') or []:
            for step in leg.get('steps') or []:
                for raw in (step.get('path') or {}).get('points') or []:
                    point = (float(raw[0]), float(raw[1]))
                    if not points or points[-1] != point:
                        points.append(point)
        return tuple(points)
    except PARSE_ERRORS:
        return ()


def parse_path(data):
    '''DS-3, DS-4 응답을 PathResult로 정리'''
    status = data.get('status')
    if status in PATH_NO_RESULT:
        return PathResult(status='no_result')
    if status != 'OK':
        return PathResult(status='unavailable')
    route = data['route']
    props = route['properties']
    return PathResult(
        status='ok',
        seconds=to_int(props['totalTime']),
        distance=to_int(props['totalDistance']),
        points=path_points(route),
    )


class KakaoClient:
    '''카카오 API 호출. 대중교통, 도보, 자전거 경로는 메모리 캐시에 보관 (tech_stack.md 3.5)'''

    def __init__(self, http, key, clock=None):
        self.http = http
        self.key = key
        cache_args = {} if clock is None else {'clock': clock}
        self.transit_cache = TTLCache(config.TRANSIT_TTL, **cache_args)
        self.path_cache = TTLCache(config.PATH_TTL, **cache_args)
        self.path_inflight = {}  # 응답을 기다리는 중인 도보, 자전거 경로 조회

    async def _get(self, path, params):
        '''GET 요청 후 JSON 본문. 연결 실패, 시간 초과, JSON이 아니면 None'''
        try:
            response = await self.http.get(
                f'{config.KAKAO_HOST}{path}',
                params=params,
                headers={'Authorization': f'KakaoAK {self.key}'},
                timeout=config.HTTP_TIMEOUT,
            )
            return response.json()
        except httpx.HTTPError, ValueError:
            return None

    async def search_address(self, query, page):
        '''DS-1 주소 검색. 검색어는 캐시하지 않음'''
        data = await self._get(
            '/v2/local/search/address.json',
            {'query': query, 'page': page, 'size': config.ADDRESS_PAGE_SIZE},
        )
        result = AddressResult(status='unavailable')
        if isinstance(data, dict) and 'documents' in data:
            try:
                result = parse_address(data)
            except PARSE_ERRORS:
                result = AddressResult(status='unavailable')
        logger.info('kakao address %s', result.status)
        return result

    async def search_keyword(self, query, page):
        '''DS-7 키워드 장소 검색. 위치는 보내지 않고, 검색어는 캐시하지 않음'''
        data = await self._get(
            '/v2/local/search/keyword.json',
            {'query': query, 'page': page, 'size': config.ADDRESS_PAGE_SIZE},
        )
        result = AddressResult(status='unavailable')
        if isinstance(data, dict) and 'documents' in data:
            try:
                result = parse_keyword(data)
            except PARSE_ERRORS:
                result = AddressResult(status='unavailable')
        logger.info('kakao keyword %s', result.status)
        return result

    async def transit(self, origin, destination):
        '''DS-2 대중교통 경로'''
        key = (round_point(origin), round_point(destination))
        cached = self.transit_cache.get(key)
        if cached is not None:
            logger.info('kakao transit %s (cache)', cached.status)
            return cached
        data = await self._get(
            '/v2/routing/publictraffic',
            {
                'start_x': origin[0],
                'start_y': origin[1],
                'end_x': destination[0],
                'end_y': destination[1],
            },
        )
        result = TransitResult(status='unavailable')
        if isinstance(data, dict):
            try:
                result = parse_transit(data)
            except PARSE_ERRORS:
                result = TransitResult(status='unavailable')
        if result.status != 'unavailable':
            self.transit_cache.set(key, result)
        logger.info('kakao transit %s', result.status)
        return result

    async def _path(self, name, path, start, end, mode):
        '''도보, 자전거 경로 공통

        - 같은 두 지점, 같은 방식이면 캐시 사용
        - 같은 조회가 이미 응답을 기다리는 중이면 새로 호출하지 않고 그 결과를 함께 씀
        '''
        key = (name, mode, round_point(start), round_point(end))
        cached = self.path_cache.get(key)
        if cached is not None:
            logger.info('kakao %s %s (cache)', name, cached.status)
            return cached
        task = self.path_inflight.get(key)
        if task is None:
            task = asyncio.ensure_future(self._fetch_path(key, name, path, start, end, mode))
            self.path_inflight[key] = task
            task.add_done_callback(lambda _: self.path_inflight.pop(key, None))
        return await asyncio.shield(task)

    async def _fetch_path(self, key, name, path, start, end, mode):
        '''도보, 자전거 경로 호출과 캐시 저장'''
        data = await self._get(
            path,
            {
                'start_x': start[0],
                'start_y': start[1],
                'end_x': end[0],
                'end_y': end[1],
                'route_mode': mode,
            },
        )
        result = PathResult(status='unavailable')
        if isinstance(data, dict):
            try:
                result = parse_path(data)
            except PARSE_ERRORS:
                result = PathResult(status='unavailable')
        if result.status != 'unavailable':
            self.path_cache.set(key, result)
        logger.info('kakao %s %s', name, result.status)
        return result

    async def walk(self, start, end):
        '''DS-3 도보 경로 (BROAD_FIRST)'''
        return await self._path('walk', '/v2/routing/walk', start, end, config.WALK_MODE)

    async def bicycle(self, start, end):
        '''DS-4 자전거 경로 (SHORTEST)'''
        return await self._path('bicycle', '/v2/routing/bicycle', start, end, config.BICYCLE_MODE)
