'''첫차, 막차 데이터 조회와 정리 (datasource.md 7.1 ~ 7.4, rules.md 3.4)

- DS-8 평일 공휴일 파일, DS-9 서울 버스, DS-10 경기 버스, DS-11 인천 버스
- DS-12 서울 지하철, DS-13 사용자 지하철 시간표
- DS-19 서울 버스 노선별 경유 정류소 (DS-9를 쓰지 못할 때 서울 노선 확인, 실시간 위치의 승차 정류소)
- 결과는 노선 하나의 운행 범위(service.Window). 알 수 없으면 None (rules.md 3.4.4)
- 캐시 열쇠에 날짜를 넣어 그날 안에서만 다시 씀 (tech_stack.md 3.5)
- 조회에 실패한 결과는 캐시하지 않음
- 로그에는 조회 종류와 결과 상태만 남김. 노선 번호, 역 이름, 좌표, 인증키는 남기지 않음
'''

import asyncio
import csv
import logging
import re
import xml.etree.ElementTree as ElementTree
from datetime import date, datetime

import httpx

from app import config
from app.cache import TTLCache
from app.geo import distance_m
from app.planner import service
from app.planner.live import STOP_MATCH_RADIUS

logger = logging.getLogger('app.timetable')

SUBWAY_LINE = re.compile(r'^(?:수도권\s*)?([1-9])호선$')
# DS-12 요일 값: 1 평일, 2 토요일, 3 휴일
SUBWAY_DOW = {'weekday': '1', 'saturday': '2', 'sunday': '3', 'holiday': '3'}
# DS-13 요일 열 값
RAIL_DAY = {'weekday': '평일', 'saturday': '토요일', 'sunday': '휴일', 'holiday': '휴일'}
# DS-10 요일별 기점 첫차, 막차 항목. 공휴일 값이 없으면 일요일 값
GYEONGGI_TIMES = {
    'weekday': [('upFirstTime', 'upLastTime')],
    'saturday': [('satUpFirstTime', 'satUpLastTime')],
    'sunday': [('sunUpFirstTime', 'sunUpLastTime')],
    'holiday': [('weUpFirstTime', 'weUpLastTime'), ('sunUpFirstTime', 'sunUpLastTime')],
}


class FetchError(Exception):
    '''외부 조회 실패 (연결, 시간 초과, 형식 오류)'''


# 형식이 달라 정리하지 못할 때 생기는 예외
PARSE_ERRORS = (KeyError, TypeError, ValueError, IndexError, AttributeError)


def clock_seconds(value):
    '''시각 값을 0시부터의 초로. 'HH:MM', 'HHMM', 'HHMMSS', 정수(600 → 06:00) 모두 허용

    - 24시 이상(자정을 넘긴 막차)도 그대로 둠. 형식이 다르면 None
    '''
    if value is None:
        return None
    text = str(value).strip().replace(':', '')
    if not text.isdigit() or len(text) > 6:
        return None
    text = text.zfill(4) if len(text) <= 4 else text.zfill(6)
    hours, minutes = int(text[:2]), int(text[2:4])
    seconds = int(text[4:6]) if len(text) == 6 else 0
    if minutes > 59 or seconds > 59 or hours > 30:
        return None
    return hours * 3600 + minutes * 60 + seconds


def stamp_seconds(value, base):
    '''DS-9의 14자리 시각(YYYYMMDDHHMMSS)을 base 날짜 0시부터의 초로. 형식이 다르면 None'''
    try:
        moment = datetime.strptime(str(value), '%Y%m%d%H%M%S')
    except ValueError:
        return None
    return int((moment - datetime.combine(base, datetime.min.time())).total_seconds())


def as_list(value):
    '''응답 목록 항목 정리. 항목이 하나이면 딕셔너리로 오는 경우가 있음'''
    if value is None:
        return []
    if isinstance(value, dict):
        return [value]
    return list(value)


def find_items(data, name):
    '''JSON 응답 어딘가에 있는 name 목록을 찾음 (msgBody, response 감싸기 차이 흡수)'''
    if isinstance(data, dict):
        for key, value in data.items():
            if key == name:
                return as_list(value)
            found = find_items(value, name)
            if found:
                return found
    return []


def xml_items(text, name):
    '''XML 응답의 name 요소들을 {항목: 값} 목록으로'''
    root = ElementTree.fromstring(text)
    return [{child.tag: (child.text or '') for child in item} for item in root.iter(name)]


def load_holidays(folder):
    '''DS-8 평일 공휴일 파일들 → {연도: 날짜 집합} (datasource.md 7.1)'''
    holidays = {}
    for path in sorted(folder.glob('*.csv')) if folder.is_dir() else []:
        if not path.stem.isdigit():
            continue
        year = int(path.stem)
        days = set()
        with path.open(encoding='utf-8-sig', newline='') as file:
            for row in list(csv.reader(file))[1:]:
                if row and re.fullmatch(r'\d{2}-\d{2}', row[0].strip()):
                    month, day = map(int, row[0].strip().split('-'))
                    days.add(date(year, month, day))
        holidays[year] = days
    return holidays


def load_rail(path):
    '''DS-13 사용자 지하철 시간표 (datasource.md 7.4)

    - 결과: {요일: [(역 열쇠, 다음 역 열쇠, 첫차 초, 막차 초)]}
    '''
    table = {}
    with path.open(encoding='utf-8-sig', newline='') as file:
        for row in list(csv.reader(file))[1:]:
            if len(row) < 5:
                continue
            first, last = clock_seconds(row[3]), clock_seconds(row[4])
            if first is None or last is None:
                continue
            item = (service.station_key(row[0]), service.station_key(row[1]), first, last)
            table.setdefault(row[2].strip(), []).append(item)
    return table


def rail_file_window(table, day, station, next_station):
    '''DS-13 시간표에서 운행 범위. 다음 역까지 같은 줄이 있으면 그 방향, 없으면 그 역의 모든 방향'''
    rows = table.get(RAIL_DAY[day], [])
    here = service.station_key(station)
    after = service.station_key(next_station)
    exact = [row for row in rows if row[0] == here and row[1] == after]
    pool = exact or [row for row in rows if row[0] == here]
    if not pool:
        return None
    return service.Window(start=min(r[2] for r in pool), end=max(r[3] for r in pool))


def route_length(stations):
    '''정류소 좌표 목록을 순서대로 이은 직선거리의 합(m)'''
    return sum(distance_m(a, b) for a, b in zip(stations, stations[1:], strict=False))


def nearest_distance(stations, point):
    '''point에서 가장 가까운 정류소까지의 직선거리(m). 정류소가 없으면 무한대'''
    return min((distance_m(point, s) for s in stations), default=float('inf'))


class TimetableClient:
    '''첫차, 막차 조회. 노선 하나의 운행 범위를 돌려줌'''

    def __init__(self, http, gokr_key, seoul_key, data_dir, clock=None):
        self.http = http
        self.gokr_key = gokr_key
        self.seoul_key = seoul_key
        self.rail_dir = data_dir / 'rail'
        self.holidays = load_holidays(data_dir / 'holidays')
        cache_args = {} if clock is None else {'clock': clock}
        self.cache = TTLCache(config.TIMETABLE_TTL, **cache_args)
        self.inflight = {}

    def day_type(self, day):
        '''요일 구분. 그 해 공휴일 파일이 없으면 평일은 None'''
        return service.day_type(day, self.holidays)

    async def get(self, url, params):
        '''GET 요청. JSON이면 딕셔너리, XML이면 문자열. 실패하면 FetchError'''
        try:
            response = await self.http.get(url, params=params, timeout=config.HTTP_TIMEOUT)
        except httpx.HTTPError as error:
            raise FetchError from error
        text = response.text.strip()
        if response.status_code != 200 or not text:
            raise FetchError
        # data.go.kr 중계 서버의 오류 응답. HTTP 200으로 와도 '노선 없음'이 아닌 조회 실패로 봄
        if 'OpenAPI_ServiceResponse' in text[:200]:
            raise FetchError
        if text.startswith('<'):
            return text
        try:
            return response.json()
        except ValueError as error:
            raise FetchError from error

    def items(self, data, name):
        '''JSON, XML 응답에서 name 목록'''
        try:
            return xml_items(data, name) if isinstance(data, str) else find_items(data, name)
        except ElementTree.ParseError as error:
            raise FetchError from error

    async def once(self, key, factory):
        '''같은 열쇠는 캐시나 응답을 기다리는 중인 조회를 함께 씀

        - factory는 (값, 캐시할지)를 돌려주는 코루틴 함수
        '''
        cached = self.cache.get(key)
        if cached is not None:
            return cached[0]
        task = self.inflight.get(key)
        if task is None:

            async def run():
                value, keep = await factory()
                if keep:
                    self.cache.set(key, (value,))
                return value

            task = asyncio.ensure_future(run())
            self.inflight[key] = task
            task.add_done_callback(lambda _: self.inflight.pop(key, None))
        return await asyncio.shield(task)

    # 버스 (DS-9 ~ DS-11)

    async def bus_window(self, name, near, day):
        '''버스 노선의 운행 범위 (rules.md 3.4.3). 서울 → 경기 → 인천 순서. 모르면 None'''
        name = service.route_number(name)
        near_key = None if near is None else (round(near[0], 2), round(near[1], 2))
        key = ('bus', name, near_key, day.isoformat())
        return await self.once(key, lambda: self._bus_window(name, near, day))

    async def _bus_window(self, name, near, day):
        failed = False
        for source in (self._seoul_bus, self._gyeonggi_bus, self._incheon_bus):
            try:
                found, window = await source(name, near, day)
            except (FetchError, *PARSE_ERRORS):
                failed = True
                continue
            if found:
                logger.info('timetable bus %s', 'ok' if window else 'unknown')
                return window, window is not None or not failed
        logger.info('timetable bus %s', 'unavailable' if failed else 'not_found')
        return None, not failed

    async def _seoul_bus(self, name, near, day):
        '''서울 버스. (찾았는지, Window 또는 None)

        - DS-9로 첫차, 막차를 구함
        - DS-9를 쓰지 못하면 DS-19로 서울 노선인지만 확인하고 운행 범위는 모름 (rules.md 3.4.3)
        - 같은 번호여도 승차 지점 STOP_MATCH_RADIUS 안에 정류소가 없으면 서울 노선이 아닌 것으로 봄
        '''
        try:
            return await self._seoul_bus_times(name, near, day)
        except (FetchError, *PARSE_ERRORS):
            pass
        routes = await self.seoul_routes(name, day)
        if routes is None:
            raise FetchError
        stops = [(x, y) for route in routes.values() for _, x, y in route]
        if not stops or (near is not None and nearest_distance(stops, near) > STOP_MATCH_RADIUS):
            return False, None
        return True, None

    async def _seoul_bus_times(self, name, near, day):
        '''DS-9 서울 버스. (찾았는지, Window 또는 None)'''
        if not self.gokr_key:
            raise FetchError
        data = await self.get(
            f'{config.SEOUL_BUS_HOST}/busRouteInfo/getBusRouteList',
            {'serviceKey': self.gokr_key, 'strSrch': name, 'resultType': 'json'},
        )
        rows = [r for r in self.items(data, 'itemList') if str(r.get('busRouteNm')) == name]
        if not rows:
            return False, None
        row = rows[0]
        if len(rows) > 1 and near is not None:
            row = await self._nearest_seoul(rows, near)
        first = stamp_seconds(row.get('firstBusTm'), day)
        last = stamp_seconds(row.get('lastBusTm'), day)
        if first is None or last is None:
            return True, None
        # 금일 값이므로 첫차 날짜 기준으로 맞춤
        base = first // service.DAY * service.DAY
        length = float(row.get('length') or 0) * 1000
        return True, service.bus_window(first - base, last - base, length)

    async def _nearest_seoul(self, rows, near):
        '''같은 번호의 서울 노선 중 승차 지점에서 가장 가까운 정류소가 있는 노선'''

        async def stations(row):
            data = await self.get(
                f'{config.SEOUL_BUS_HOST}/busRouteInfo/getStaionByRoute',
                {
                    'serviceKey': self.gokr_key,
                    'busRouteId': row['busRouteId'],
                    'resultType': 'json',
                },
            )
            items = self.items(data, 'itemList')
            return [(float(s['gpsX']), float(s['gpsY'])) for s in items]

        lists = await asyncio.gather(*(stations(row) for row in rows))
        index = min(range(len(rows)), key=lambda i: nearest_distance(lists[i], near))
        return rows[index]

    async def seoul_routes(self, name, day):
        '''서울 노선 번호의 노선별 경유 정류소. {노선 ID: [(순번, 경도, 위도)]}, 조회 실패는 None

        - DS-19는 번호로 거르는 요청이 없어 전체를 하루 한 번 받아 메모리에 둠 (datasource.md 7.5)
        - 첫차, 막차 확인과 실시간 위치(clients/live.py)가 함께 씀
        '''
        table = await self.once(('seoul-routes', day.isoformat()), self._fetch_seoul_routes)
        if table is None:
            return None
        return table.get(service.route_number(name), {})

    async def _fetch_seoul_routes(self):
        '''DS-19 전체. ({노선 번호: {노선 ID: [(순번, 경도, 위도)]}}, 캐시할지)'''
        if not self.seoul_key:
            return None, False
        size = config.SEOUL_ROUTE_PAGE_SIZE
        limit = asyncio.Semaphore(config.SEOUL_ROUTE_PARALLEL)

        async def page(start):
            async with limit:
                url = (
                    f'{config.SEOUL_HOST}/{self.seoul_key}/json/busRteInfo'
                    f'/{start}/{start + size - 1}/'
                )
                data = await self.get(url, {})
            if not isinstance(data, dict) or 'busRteInfo' not in data:
                raise FetchError
            return data['busRteInfo']

        table = {}
        try:
            first = await page(1)
            total = int(first['list_total_count'])
            rest = await asyncio.gather(*(page(s) for s in range(1 + size, total + 1, size)))
            for body in (first, *rest):
                for row in as_list(body.get('row')):
                    routes = table.setdefault(str(row['RTE_NM']), {})
                    stops = routes.setdefault(str(row['ROUTE_ID']), [])
                    stops.append((int(row['SN']), float(row['XCRD']), float(row['YCRD'])))
        except (FetchError, *PARSE_ERRORS):
            logger.info('timetable seoul_routes unavailable')
            return None, False
        for routes in table.values():
            for stops in routes.values():
                stops.sort()
        logger.info('timetable seoul_routes ok')
        return table, True

    async def _gyeonggi_bus(self, name, near, day):
        '''DS-10 경기 버스. 기점(up) 시각만 사용 (D-37)'''
        if not self.gokr_key:
            raise FetchError
        base = config.GYEONGGI_BUS_HOST
        data = await self.get(
            f'{base}/getBusRouteListv2',
            {'serviceKey': self.gokr_key, 'keyword': name, 'format': 'json'},
        )
        rows = [r for r in self.items(data, 'busRouteList') if str(r.get('routeName')) == name]
        if not rows:
            return False, None

        async def stations(row):
            data = await self.get(
                f'{base}/getBusRouteStationListv2',
                {'serviceKey': self.gokr_key, 'routeId': row['routeId'], 'format': 'json'},
            )
            items = sorted(
                self.items(data, 'busRouteStationList'), key=lambda s: int(s['stationSeq'])
            )
            return [(float(s['x']), float(s['y'])) for s in items]

        lists = await asyncio.gather(*(stations(row) for row in rows))
        index = 0
        if near is not None:
            index = min(range(len(rows)), key=lambda i: nearest_distance(lists[i], near))
            # 가장 가까운 노선도 승차 지점에서 멀면 다른 지역의 같은 번호 노선 (rules.md 3.4.3)
            if nearest_distance(lists[index], near) > STOP_MATCH_RADIUS:
                return False, None
        kind = self.day_type(day)
        if kind is None:
            return True, None
        data = await self.get(
            f'{base}/getBusRouteInfoItemv2',
            {'serviceKey': self.gokr_key, 'routeId': rows[index]['routeId'], 'format': 'json'},
        )
        info = self.items(data, 'busRouteInfoItem')
        if not info:
            return True, None
        for first_key, last_key in GYEONGGI_TIMES[kind]:
            first = clock_seconds(info[0].get(first_key))
            last = clock_seconds(info[0].get(last_key))
            if first is not None and last is not None:
                return True, service.bus_window(first, last, route_length(lists[index]))
        return True, None

    async def _incheon_bus(self, name, near, day):
        '''DS-11 인천 버스. 같은 번호가 여럿이면 첫 번째 (rules.md 3.4.3)'''
        if not self.gokr_key:
            raise FetchError
        data = await self.get(
            f'{config.INCHEON_BUS_HOST}/getBusRouteNo',
            {
                'serviceKey': self.gokr_key,
                'routeNo': name,
                'pageNo': 1,
                'numOfRows': 50,
                '_type': 'json',
            },
        )
        rows = [r for r in self.items(data, 'itemList') if str(r.get('ROUTENO')) == name]
        if not rows:
            return False, None
        first = clock_seconds(rows[0].get('FBUS_DEPHMS'))
        last = clock_seconds(rows[0].get('LBUS_DEPHMS'))
        if first is None or last is None:
            return True, None
        return True, service.bus_window(first, last, float(rows[0].get('ROUTELEN') or 0))

    # 지하철 (DS-12, DS-13)

    async def rail_window(self, line, station, next_station, day):
        '''지하철 승차역의 운행 범위 (rules.md 3.4.3). 모르면 None'''
        kind = self.day_type(day)
        if kind is None:
            logger.info('timetable rail unknown')
            return None
        match = SUBWAY_LINE.match(line or '')
        if match:
            directions = await self.subway_directions(match.group(1), kind, day)
            if directions is None:
                return None
            return service.rail_window(directions, station, next_station)
        path = self.rail_dir / f'{line}.csv'
        if not line or not path.is_file():
            logger.info('timetable rail not_found')
            return None
        try:
            table = load_rail(path)
        except OSError, UnicodeDecodeError, csv.Error:
            logger.info('timetable rail unavailable')
            return None
        return rail_file_window(table, kind, station, next_station)

    async def subway_directions(self, number, kind, day):
        '''DS-12 한 호선, 한 요일의 두 방향 시간표. [{역 열쇠: (첫차, 막차)}, ...] 또는 None'''
        key = ('subway', number, SUBWAY_DOW[kind], day.isoformat())
        return await self.once(key, lambda: self._fetch_subway(number, kind))

    async def _fetch_subway(self, number, kind):
        async def direction(updown):
            url = (
                f'{config.SEOUL_HOST}/{self.seoul_key}/json/SearchFirstAndLastTrainbyLineServiceNew'
                f'/1/1000/{number}/{updown}/{SUBWAY_DOW[kind]}/'
            )
            data = await self.get(url, {})
            table = {}
            for row in self.items(data, 'row'):
                first = clock_seconds(row.get('FSTT_HRM'))
                last = clock_seconds(row.get('LSTTM_HRM'))
                if first is not None and last is not None:
                    table[service.station_key(row.get('STTN'))] = (first, last)
            return table

        try:
            directions = await asyncio.gather(direction('1'), direction('2'))
        except (FetchError, *PARSE_ERRORS):
            logger.info('timetable subway unavailable')
            return None, False
        logger.info('timetable subway ok')
        return list(directions), True
