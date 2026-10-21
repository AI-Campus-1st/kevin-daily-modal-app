'''따릉이 실시간 대여정보 호출과 응답 정리 (datasource.md 7장)

- DS-5 bikeList를 1,000건씩 나누어 받음
  - 처음 3쪽은 동시에 받고, 마지막 쪽이 꽉 차 있으면 다음 쪽을 더 받음
- 전체 목록은 30초 동안 메모리 캐시에 보관 (tech_stack.md 3.5)
- 마지막으로 성공한 목록은 서버 메모리에 계속 두고, 조회 실패 시 대여소 위치로만 사용 (재고는 모름)
- 호출 주소에 인증키가 들어 있으므로 주소를 로그, 오류 메시지에 남기지 않음
'''

import asyncio
import logging
import time
from dataclasses import dataclass
from datetime import datetime

import httpx

from app import config
from app.cache import TTLCache

logger = logging.getLogger('app.bike')

CODE_OK = 'INFO-000'
CODE_NO_DATA = 'INFO-200'  # 요청한 범위에 데이터가 없음


class FetchError(Exception):
    '''한 쪽이라도 받지 못함'''


@dataclass(frozen=True)
class Station:
    '''따릉이 대여소 하나'''

    id: str
    name: str
    x: float  # 경도
    y: float  # 위도
    bikes: int  # 대여 가능 대수 = 세워진 자전거 수
    racks: int  # 반납 가능 거치대 = 거치대 수 - 세워진 자전거 수, 음수이면 0


@dataclass(frozen=True)
class BikeData:
    '''따릉이 대여정보 조회 결과

    - status 'ok': stations의 재고가 이번 조회 값
    - status 'unavailable': stations는 마지막으로 성공한 목록(없으면 빈 목록)이며 재고를 쓰지 않음
    '''

    status: str
    fetched_at: datetime | None
    stations: tuple

    @property
    def stock_known(self):
        return self.status == 'ok'


def parse_station(row):
    '''대여소 한 줄을 Station으로 정리. 값이 숫자가 아니면 None'''
    try:
        bikes = int(float(row['parkingBikeTotCnt']))
        rack_total = int(float(row['rackTotCnt']))
        return Station(
            id=str(row['stationId']),
            name=str(row['stationName']),
            x=float(row['stationLongitude']),
            y=float(row['stationLatitude']),
            bikes=max(bikes, 0),
            racks=max(rack_total - bikes, 0),
        )
    except KeyError, TypeError, ValueError:
        return None


def parse_page(data):
    '''한 쪽의 응답을 대여소 줄 목록으로 정리. 오류 응답이면 FetchError'''
    if not isinstance(data, dict):
        raise FetchError
    body = data.get('rentBikeStatus')
    if isinstance(body, dict):
        code = (body.get('RESULT') or {}).get('CODE')
        if code == CODE_OK:
            return body.get('row') or []
        if code == CODE_NO_DATA:
            return []
        raise FetchError
    code = (data.get('RESULT') or {}).get('CODE')
    if code == CODE_NO_DATA:
        return []
    raise FetchError


class BikeClient:
    '''따릉이 대여정보 호출'''

    def __init__(self, http, key, clock=time.monotonic, now=datetime.now):
        self.http = http
        self.key = key
        self.now = now  # 한국 표준시 시각을 돌려주는 함수
        self.cache = TTLCache(config.BIKE_LIST_TTL, clock=clock)
        self.last_success = None  # 마지막으로 성공한 BikeData

    async def _page(self, number):
        '''number번째 쪽(1부터)의 대여소 줄 목록'''
        start = (number - 1) * config.BIKE_PAGE_SIZE + 1
        end = number * config.BIKE_PAGE_SIZE
        url = f'{config.SEOUL_HOST}/{self.key}/json/bikeList/{start}/{end}/'
        try:
            response = await self.http.get(url, timeout=config.HTTP_TIMEOUT)
            data = response.json()
        except (httpx.HTTPError, ValueError) as error:
            raise FetchError from error
        try:
            return parse_page(data)
        except (AttributeError, TypeError) as error:
            # RESULT, row 등의 형식이 datasource.md와 다름
            raise FetchError from error

    async def _fetch_all(self):
        '''전체 대여소 줄 목록'''
        numbers = range(1, config.BIKE_FIRST_PAGES + 1)
        pages = await asyncio.gather(*(self._page(n) for n in numbers))
        rows = [row for page in pages for row in page]
        number = config.BIKE_FIRST_PAGES
        while len(pages[-1]) >= config.BIKE_PAGE_SIZE:
            number += 1
            pages = [await self._page(number)]
            rows.extend(pages[-1])
        return rows

    async def stations(self):
        '''대여소 목록과 재고'''
        cached = self.cache.get('all')
        if cached is not None:
            logger.info('bike list ok (cache)')
            return cached
        try:
            rows = await self._fetch_all()
        except FetchError:
            rows = None
        stations = tuple(s for s in (parse_station(r) for r in rows or []) if s is not None)
        if not stations:
            logger.info('bike list unavailable')
            previous = self.last_success.stations if self.last_success else ()
            return BikeData(status='unavailable', fetched_at=None, stations=previous)
        result = BikeData(
            status='ok', fetched_at=self.now().replace(microsecond=0), stations=stations
        )
        self.cache.set('all', result)
        self.last_success = result
        logger.info('bike list ok')
        return result
