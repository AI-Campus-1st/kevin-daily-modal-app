'''버스, 지하철 실시간 위치 (rules.md 11.3, 권장 F-26)

- 위치 조회 결과를 인자로 받는 순수 함수
- 소요 시간, 출발 시각에는 반영하지 않음. 화면에 상대 위치만 보여 줌
'''

import re

from app.geo import distance_m
from app.planner.service import station_key

# 카카오 승차 지점과 노선 정류소를 같은 곳으로 보는 최대 직선거리(m)
STOP_MATCH_RADIUS = 300

# 카카오 지하철 노선 이름 → 실시간 도착정보 subwayId (datasource.md 7.5)
SUBWAY_IDS = {
    **{f'{n}호선': str(1000 + n) for n in range(1, 10)},
    '경의중앙선': '1063',
    '공항철도': '1065',
    '경춘선': '1067',
    '수인분당선': '1075',
    '신분당선': '1077',
    '경강선': '1081',
    '우이신설선': '1092',
    '서해선': '1093',
    'GTX-A': '1032',
}

DIRECTION_TEXT = re.compile(r'-\s*(.+?)방면')


def board_seq(stations, board, alight):
    '''노선 정류소 목록에서 승차 정류소 순번 (좌표로 맞춤)

    - stations: [(순번, 경도, 위도)]
    - 승차 지점에 가까운 정류소와 하차 지점에 가까운 정류소를 순번이 앞뒤가 맞게 고름 (방향 구분)
    - 승차 정류소가 STOP_MATCH_RADIUS 밖이면 None
    '''
    if board is None or not stations:
        return None
    best = None
    for seq, x, y in stations:
        to_board = distance_m(board, (x, y))
        if to_board > STOP_MATCH_RADIUS:
            continue
        to_alight = 0.0
        if alight is not None:
            after = [distance_m(alight, (ax, ay)) for aseq, ax, ay in stations if aseq > seq]
            if not after:
                continue
            to_alight = min(after)
        score = to_board + to_alight
        if best is None or score < best[0]:
            best = (score, seq)
    return None if best is None else best[1]


def board_seq_by_name(stations, board_name, alight_name):
    '''정류소 이름으로 승차 정류소 순번 (인천 데이터, rules.md 11.3)

    - stations: [(순번, 정류소 이름)]
    - 승차 정류소 이름이 같은 순번 중, 그 뒤에 하차 정류소 이름이 있는 첫 순번
    '''
    board = station_key(board_name)
    alight = station_key(alight_name)
    for seq, name in sorted(stations):
        if station_key(name) != board:
            continue
        if any(s > seq and station_key(n) == alight for s, n in stations):
            return seq
    return None


def stops_away(board, vehicles):
    '''승차 정류소까지 가장 가까운 차량의 남은 정류장 수

    - vehicles: [(차량의 현재 정류소 순번, 정류소에 도착해 있는지)]
    - 승차 정류소보다 앞에 있는 차량만. 0은 승차 정류소에 도착해 있는 차량
    - 다가오는 차량이 없으면 None
    '''
    found = []
    for seq, at_stop in vehicles:
        away = board - seq
        if away > 0 or (away == 0 and at_stop):
            found.append(away)
    return min(found, default=None)


def subway_away(rows, line, next_station):
    '''실시간 도착정보에서 승차역까지 가장 가까운 열차의 남은 역 수

    - rows: [(subwayId, trainLineNm, ordkey)]
    - 노선(subwayId)과 방면(trainLineNm의 'OO방면'이 다음 역)이 맞는 열차만
    - ordkey의 셋째 ~ 다섯째 글자가 남은 역 수 (000은 승차역 도착, datasource.md 7.5)
    - 결과: (남은 역 수, rows 안의 위치). 맞는 열차가 없으면 None
    '''
    line_id = SUBWAY_IDS.get(line)
    target = station_key(next_station)
    found = []
    for index, (subway_id, line_name, ordkey) in enumerate(rows):
        if line_id is not None and subway_id != line_id:
            continue
        match = DIRECTION_TEXT.search(line_name or '')
        if not match or station_key(match.group(1)) != target:
            continue
        digits = (ordkey or '')[2:5]
        if digits.isdigit():
            found.append((int(digits), index))
    return min(found, default=None)


def station_number(value):
    '''역 번호 숫자. 실시간 역 ID('1009000917')는 끝 여섯 자리, 외부 코드('917')는 그대로

    - 숫자가 아니면(지선 '211-1', 다른 노선 'K243' 등) None
    '''
    text = str(value or '').strip()
    if not text.isdigit():
        return None
    return int(text[-6:]) if len(text) > 6 else int(text)


def subway_away_by_order(rows, line, here_code, next_code):
    '''역 번호로 방향을 정해 승차역까지 가장 가까운 열차의 남은 역 수 (rules.md 11.3)

    - 방면 이름이 다음 역과 맞지 않을 때 사용 (급행처럼 다음 역이 바로 옆 역이 아님)
    - rows: [(subwayId, ordkey, statnId, statnFid, statnTid)]
    - here_code, next_code: 승차역, 다음 역의 외부 코드. 실시간 역 ID 끝 여섯 자리와 같은 번호
    - 열차가 가는 쪽(statnTid − statnId)과 다음 역 쪽(next_code − here_code)의 부호가 같은 열차만
    - 쓰지 않는 경우(None): 역 번호가 숫자가 아님, 실시간 역 ID와 외부 코드가 다른 번호 체계,
      다음 역이 바로 옆 역(방면 이름 비교로 이미 정해짐)
    - 결과: (남은 역 수, rows 안의 위치). 맞는 열차가 없으면 None
    '''
    line_id = SUBWAY_IDS.get(line)
    here = station_number(here_code)
    target = station_number(next_code)
    if line_id is None or here is None or target is None or here == target:
        return None
    mine = [(i, row) for i, row in enumerate(rows) if row[0] == line_id]
    neighbors = {station_number(row[n]) for _, row in mine for n in (3, 4)}
    if target in neighbors:
        return None
    found = []
    for index, (_, ordkey, statn, _, toward) in mine:
        at = station_number(statn)
        step = station_number(toward)
        if at != here:
            return None
        if step is None:
            continue
        digits = (ordkey or '')[2:5]
        if (step - at) * (target - here) > 0 and digits.isdigit():
            found.append((int(digits), index))
    return min(found, default=None)


def next_departure(times, seconds):
    '''시간표에서 seconds 이후 첫 출발(초). 없으면 None

    - times: 그날 0시부터의 출발 초 목록. 자정을 넘긴 열차는 86,400 이상
    '''
    later = [t for t in times if t >= seconds]
    return min(later, default=None)
