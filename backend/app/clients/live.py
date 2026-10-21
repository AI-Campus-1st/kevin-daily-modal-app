'''버스, 지하철 실시간 위치 조회와 정리 (datasource.md 7.5, rules.md 11.3, 권장 F-26)

- DS-14 서울 버스 위치, DS-15 경기 버스 위치, DS-16 인천 버스 위치, DS-17 서울 지하철 실시간 도착
- 실시간 정보가 없는 지하철은 DS-18 역별 시간표로 다음 출발 예정 시각을 구함
- 노선 번호 → 노선 ID, 경유 정류소 목록은 하루 캐시. 실시간 위치는 LIVE_TTL 동안만 캐시
- 로그에는 조회 종류와 결과 상태만 남김. 노선 번호, 역 이름, 좌표, 인증키는 남기지 않음
'''

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

from app import config
from app.cache import TTLCache
from app.clients.timetable import PARSE_ERRORS, SUBWAY_DOW, SUBWAY_LINE, FetchError, clock_seconds
from app.planner import live, service

logger = logging.getLogger('app.live')

LATE_NIGHT = 3 * 3600  # 이 시각 전의 열차는 전날 운행(24시 이상)으로 봄


@dataclass(frozen=True)
class LivePosition:
    '''구간 노선 하나의 위치 정보 (api_spec.md 4.10)

    - status: 'live'(stops_away에 남은 정류장, 역 수), 'none'(다가오는 차량 없음),
      'timetable'(next_departure에 시간표 다음 출발 시각), 'unknown'(알 수 없음)
    '''

    status: str
    stops_away: int | None = None
    next_departure: datetime | None = None
    observed_at: datetime | None = None


UNKNOWN = LivePosition(status='unknown')


def parse_moment(value, tz):
    ''' '2026-10-20 17:13:28', '20261020171328', '2026-10-20 17:13:28.0' 형식 시각. 아니면 None'''
    text = ''.join(ch for ch in str(value or '') if ch.isdigit())[:14]
    try:
        return datetime.strptime(text, '%Y%m%d%H%M%S').replace(tzinfo=tz)
    except ValueError:
        return None


class LiveClient:
    '''실시간 위치 조회. 노선 하나의 위치 정보(LivePosition)를 돌려줌'''

    def __init__(self, timetable, gokr_key, seoul_key, subway_key, now, clock=None):
        self.t = timetable  # 요청, 응답 정리, 하루 캐시, 요일 구분을 함께 씀
        self.gokr_key = gokr_key
        self.seoul_key = seoul_key
        self.subway_key = subway_key
        self.now = now
        cache_args = {} if clock is None else {'clock': clock}
        self.cache = TTLCache(config.LIVE_TTL, **cache_args)
        self.inflight = {}

    async def _live_once(self, key, factory):
        '''실시간 조회를 짧게 캐시하고 같은 조회를 함께 씀. factory는 값을 돌려주는 코루틴 함수'''
        cached = self.cache.get(key)
        if cached is not None:
            return cached[0]
        task = self.inflight.get(key)
        if task is None:

            async def run():
                value = await factory()
                self.cache.set(key, (value,))
                return value

            task = asyncio.ensure_future(run())
            self.inflight[key] = task
            task.add_done_callback(lambda _: self.inflight.pop(key, None))
        return await asyncio.shield(task)

    async def _daily(self, key, factory):
        '''하루 캐시 (노선 ID, 경유 정류소). 실패는 캐시하지 않음'''

        async def wrapped():
            try:
                return await factory(), True
            except (FetchError, *PARSE_ERRORS):
                return None, False

        return await self.t.once(('live', *key, self.now().date().isoformat()), wrapped)

    # 버스 (DS-14 ~ DS-16)

    async def bus(self, name, board, alight, board_name, alight_name):
        '''버스 노선 하나의 위치. 서울 → 경기 → 인천 순서로 노선 번호를 찾음 (rules.md 11.3)'''
        name = service.route_number(name)
        if not self.gokr_key or not name:
            return UNKNOWN
        for source in (self._seoul_bus, self._gyeonggi_bus, self._incheon_bus):
            try:
                found, position = await source(name, board, alight, board_name, alight_name)
            except (FetchError, *PARSE_ERRORS):
                continue
            if found:
                logger.info('live bus %s', position.status)
                return position
        logger.info('live bus unknown')
        return UNKNOWN

    async def _seoul_bus(self, name, board, alight, board_name, alight_name):
        '''서울 버스. 노선 ID와 경유 정류소는 DS-19, 차량 위치는 DS-14

        - 같은 번호여도 승차 정류소를 맞추지 못하면 서울 노선이 아닌 것으로 보고 경기, 인천에서 찾음
        '''
        routes = await self.t.seoul_routes(name, self.now().date())
        if routes is None:
            raise FetchError
        for route_id, stops in routes.items():
            seq = live.board_seq(stops, board, alight)
            if seq is None:
                continue

            async def positions(route_id=route_id):
                data = await self.t.get(
                    f'{config.SEOUL_BUS_HOST}/buspos/getBusPosByRtid',
                    {'serviceKey': self.gokr_key, 'busRouteId': route_id, 'resultType': 'json'},
                )
                return self.t.items(data, 'itemList')

            rows = await self._live_once(('seoul-pos', route_id), positions)
            vehicles = [(int(r['sectOrd']), str(r.get('stopFlag')) == '1') for r in rows]
            moments = [parse_moment(r.get('dataTm'), self.now().tzinfo) for r in rows]
            observed = max((m for m in moments if m is not None), default=self.now())
            return True, self._bus_position(seq, vehicles, observed)
        return False, None

    async def _gyeonggi_bus(self, name, board, alight, board_name, alight_name):
        base = config.GYEONGGI_BUS_HOST

        async def route_ids():
            data = await self.t.get(
                f'{base}/getBusRouteListv2',
                {'serviceKey': self.gokr_key, 'keyword': name, 'format': 'json'},
            )
            rows = self.t.items(data, 'busRouteList')
            return [str(r['routeId']) for r in rows if str(r.get('routeName')) == name]

        ids = await self._daily(('gyeonggi-routes', name), route_ids)
        if ids is None:
            raise FetchError
        if not ids:
            return False, None
        for route_id in ids:

            async def stations(route_id=route_id):
                data = await self.t.get(
                    f'{base}/getBusRouteStationListv2',
                    {'serviceKey': self.gokr_key, 'routeId': route_id, 'format': 'json'},
                )
                return [
                    (int(s['stationSeq']), float(s['x']), float(s['y']))
                    for s in self.t.items(data, 'busRouteStationList')
                ]

            stops = await self._daily(('gyeonggi-stations', route_id), stations)
            seq = live.board_seq(stops or [], board, alight)
            if seq is None:
                continue

            async def positions(route_id=route_id):
                data = await self.t.get(
                    f'{config.GYEONGGI_LOCATION_HOST}/getBusLocationListv2',
                    {'serviceKey': self.gokr_key, 'routeId': route_id, 'format': 'json'},
                )
                return self.t.items(data, 'busLocationList')

            rows = await self._live_once(('gyeonggi-pos', route_id), positions)
            vehicles = [(int(r['stationSeq']), str(r.get('stateCd')) == '1') for r in rows]
            return True, self._bus_position(seq, vehicles, self.now())
        return True, UNKNOWN

    async def _incheon_bus(self, name, board, alight, board_name, alight_name):
        async def route_ids():
            data = await self.t.get(
                f'{config.INCHEON_BUS_HOST}/getBusRouteNo',
                {
                    'serviceKey': self.gokr_key,
                    'routeNo': name,
                    'pageNo': 1,
                    'numOfRows': 50,
                    '_type': 'json',
                },
            )
            rows = self.t.items(data, 'itemList')
            return [str(r['ROUTEID']) for r in rows if str(r.get('ROUTENO')) == name]

        ids = await self._daily(('incheon-routes', name), route_ids)
        if ids is None:
            raise FetchError
        if not ids:
            return False, None
        for route_id in ids:

            async def stations(route_id=route_id):
                data = await self.t.get(
                    f'{config.INCHEON_BUS_HOST}/getBusRouteSectionList',
                    {
                        'serviceKey': self.gokr_key,
                        'routeId': route_id,
                        'pageNo': 1,
                        'numOfRows': 1000,
                        '_type': 'json',
                    },
                )
                return [
                    (int(s['BSTOPSEQ']), str(s['BSTOPNM'])) for s in self.t.items(data, 'itemList')
                ]

            stops = await self._daily(('incheon-stations', route_id), stations)
            seq = live.board_seq_by_name(stops or [], board_name, alight_name)
            if seq is None:
                continue

            async def positions(route_id=route_id):
                data = await self.t.get(
                    f'{config.INCHEON_LOCATION_HOST}/getBusRouteLocation',
                    {
                        'serviceKey': self.gokr_key,
                        'routeId': route_id,
                        'pageNo': 1,
                        'numOfRows': 100,
                        '_type': 'json',
                    },
                )
                return self.t.items(data, 'itemList')

            rows = await self._live_once(('incheon-pos', route_id), positions)
            # 최근 정류소 순번만 있으므로 같은 순번이면 도착해 있는 것으로 봄
            vehicles = [(int(r['LATEST_STOPSEQ']), True) for r in rows]
            return True, self._bus_position(seq, vehicles, self.now())
        return True, UNKNOWN

    @staticmethod
    def _bus_position(seq, vehicles, observed):
        away = live.stops_away(seq, vehicles)
        if away is None:
            return LivePosition(status='none', observed_at=observed)
        return LivePosition(status='live', stops_away=away, observed_at=observed)

    # 지하철 (DS-17, DS-18)

    async def subway(self, line, station, next_station, moment):
        '''지하철 노선 하나의 위치 (rules.md 11.3)

        - 실시간 도착정보에 그 역, 그 노선이 있으면 남은 역 수. 방향이 맞는 열차가 없으면 'none'
        - 방면 이름이 다음 역과 맞는 열차가 없으면 역 번호로 방향을 정해 다시 찾음 (급행 구간)
        - 실시간 정보가 없으면 moment(그 구간의 승차 예상 시각) 이후 시간표 첫 열차
        '''
        rows = await self._subway_rows(station)
        line_id = live.SUBWAY_IDS.get(line)
        if rows:
            found = live.subway_away([(r[0], r[1], r[2]) for r in rows], line, next_station)
            if found is None:
                found = await self._subway_by_order(rows, line, station, next_station)
            if found is not None:
                away, index = found
                logger.info('live subway live')
                return LivePosition(status='live', stops_away=away, observed_at=rows[index][3])
            if line_id is None or any(r[0] == line_id for r in rows):
                logger.info('live subway none')
                return LivePosition(status='none', observed_at=self.now())
        position = await self._subway_timetable(line, station, next_station, moment)
        logger.info('live subway %s', position.status)
        return position

    async def _subway_by_order(self, rows, line, station, next_station):
        '''역 번호로 방향을 정한 열차 (rules.md 11.3). 1 ~ 9호선만. (남은 역 수, 위치) 또는 None

        - 승차역, 다음 역의 외부 코드는 DS-18 역 정보로 구함 (하루 캐시)
        '''
        match = SUBWAY_LINE.match(line or '')
        if not match or not next_station:
            return None
        number = match.group(1)
        here = await self._station_info(number, station)
        after = await self._station_info(number, next_station)
        if not here or not after:
            return None
        found = live.subway_away_by_order(
            [(r[0], r[2], r[4], r[5], r[6]) for r in rows], line, here[1], after[1]
        )
        if found is not None:
            logger.info('live subway order')
        return found

    async def _subway_rows(self, station):
        '''DS-17 승차역의 실시간 도착 열차

        - 결과: [(subwayId, trainLineNm, ordkey, 생성 시각, statnId, statnFid, statnTid)]
        - 없으면 None
        '''
        name = service.station_key(station)
        if not self.subway_key or not name:
            return None

        async def fetch():
            url = (
                f'{config.SUBWAY_LIVE_HOST}/{self.subway_key}/json/realtimeStationArrival'
                f'/0/50/{name}'
            )
            try:
                data = await self.t.get(url, {})
            except FetchError:
                return None
            rows = data.get('realtimeArrivalList') if isinstance(data, dict) else None
            if not rows:
                return None
            tz = self.now().tzinfo
            return [
                (
                    str(r.get('subwayId')),
                    str(r.get('trainLineNm')),
                    str(r.get('ordkey')),
                    parse_moment(r.get('recptnDt'), tz),
                    str(r.get('statnId') or ''),
                    str(r.get('statnFid') or ''),
                    str(r.get('statnTid') or ''),
                )
                for r in rows
            ]

        return await self._live_once(('subway', name), fetch)

    async def _subway_timetable(self, line, station, next_station, moment):
        '''DS-18 서울 1 ~ 9호선 역별 시간표로 moment 이후 첫 열차. 1 ~ 9호선 밖이면 'unknown'''
        match = SUBWAY_LINE.match(line or '')
        if not match or moment is None:
            return UNKNOWN
        number = match.group(1)
        seconds = moment.hour * 3600 + moment.minute * 60 + moment.second
        day = moment.date()
        if seconds < LATE_NIGHT:
            # 자정 이후 새벽은 전날 시간표의 24시 이후 열차로 봄
            day -= timedelta(days=1)
            seconds += service.DAY
        kind = self.t.day_type(day)
        if kind is None:
            return UNKNOWN
        directions = await self.t.subway_directions(number, kind, day)
        index = service.rail_direction(directions, station, next_station) if directions else None
        tags = ['1', '2'] if index is None else [str(index + 1)]
        info = await self._station_info(number, station)
        if not info:
            return UNKNOWN
        code = info[0]
        times = []
        for tag in tags:
            week = SUBWAY_DOW[kind]
            found = await self._daily(
                ('stn-times', code, week, tag),
                lambda tag=tag, week=week: self._station_times(code, week, tag),
            )
            times.extend(found or [])
        departure = live.next_departure(times, seconds)
        if departure is None:
            return LivePosition(status='none', observed_at=self.now())
        midnight = datetime.combine(day, datetime.min.time(), tzinfo=moment.tzinfo)
        return LivePosition(
            status='timetable', next_departure=midnight + timedelta(seconds=departure)
        )

    async def _station_info(self, number, station):
        '''역 이름, 호선으로 (역 코드, 외부 코드). 찾지 못하거나 조회에 실패하면 None (하루 캐시)'''
        name = service.station_key(station)
        if not name:
            return None
        return await self._daily(
            ('stn-info', number, name), lambda: self._fetch_station_info(number, name)
        )

    async def _fetch_station_info(self, number, name):
        '''SearchSTNBySubwayLineInfo (datasource.md 7.5). 찾지 못하면 None'''
        url = (
            f'{config.SEOUL_HOST}/{self.seoul_key}/json/SearchSTNBySubwayLineInfo/1/50/%20/{name}/'
        )
        data = await self.t.get(url, {})
        for row in self.t.items(data, 'row'):
            same_line = row.get('LINE_NUM') == f'0{number}호선'
            if same_line and service.station_key(row.get('STATION_NM')) == name:
                return str(row['STATION_CD']), str(row.get('FR_CODE') or '')
        return None

    async def _station_times(self, code, week, inout):
        '''역 코드, 요일, 방향의 출발 시각 목록(초). 새벽 0 ~ 3시 출발은 24시 이후로 바꿈'''
        url = (
            f'{config.SEOUL_HOST}/{self.seoul_key}/json/SearchSTNTimeTableByIDService'
            f'/1/1000/{code}/{week}/{inout}/'
        )
        data = await self.t.get(url, {})
        times = []
        for row in self.t.items(data, 'row'):
            value = clock_seconds(row.get('LEFTTIME'))
            if value is None or value == 0:
                continue
            times.append(value + service.DAY if value < LATE_NIGHT else value)
        return times
