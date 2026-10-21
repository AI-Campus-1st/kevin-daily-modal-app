'''운행 시간(첫차, 막차) 판단 테스트 (rules.md 3.4)

- app/planner/service.py의 순수 함수와 app/clients/timetable.py의 값 정리 함수
'''

from datetime import date, datetime, timedelta, timezone

from app.clients.timetable import clock_seconds, load_holidays, stamp_seconds
from app.planner import service
from tests.samples import DESTINATION, ORIGIN, bus, offset, route, subway

KST = timezone(timedelta(hours=9))
HOUR = 3600


def test_bus_window_adds_route_running_time():
    # 30km ÷ 15km/h = 2시간
    window = service.bus_window(4 * HOUR, 23 * HOUR, 30000)
    assert window == service.Window(start=4 * HOUR, end=25 * HOUR)


def test_bus_window_last_after_midnight():
    # V-19의 N61: 첫차 23:30, 막차 03:50, 30km → 23:30 ~ 05:50 (다음 날)
    window = service.bus_window(23 * HOUR + 1800, 3 * HOUR + 3000, 30000)
    assert window.end == 24 * HOUR + 5 * HOUR + 3000
    assert not service.runs_at(window, 9 * HOUR)
    assert service.runs_at(window, 23 * HOUR + 2000)
    assert service.runs_at(window, 2 * HOUR)  # 자정 이후는 전날 범위로 확인


def test_runs_at_edges():
    window = service.Window(start=5 * HOUR, end=24 * HOUR + 1800)
    assert service.runs_at(window, 5 * HOUR)
    assert service.runs_at(window, 1800)
    assert not service.runs_at(window, 1801)
    assert not service.runs_at(window, 5 * HOUR - 1)


def test_check_route_any_vehicle_out_excludes_route():
    day = service.Window(start=4 * HOUR, end=25 * HOUR)
    night = service.Window(start=23 * HOUR, end=30 * HOUR)
    assert service.check_route([(0, 9 * HOUR, (day, night))]).running is False
    assert service.check_route([(0, 9 * HOUR, (day,))]) == service.Check(running=True)


def test_check_route_unknown_is_running_with_steps():
    day = service.Window(start=4 * HOUR, end=25 * HOUR)
    result = service.check_route([(0, 9 * HOUR, (day,)), (2, 10 * HOUR, (None,)), (3, HOUR, ())])
    assert result == service.Check(running=True, unknown_steps=frozenset({2, 3}))


def test_departure_from_arrive_by_or_now():
    kakao = route(0, 'SUBWAY', [subway(900, offset(ORIGIN, east_m=500), DESTINATION)])
    total = kakao.total_time + 180
    now = datetime(2026, 10, 20, 0, 30, tzinfo=KST)
    arrive_by = datetime(2026, 10, 20, 3, 0, tzinfo=KST)
    assert service.departure(kakao, arrive_by, now) == arrive_by - timedelta(seconds=total)
    assert service.departure(kakao, None, now) == now
    late = datetime(2026, 10, 20, 9, 0, tzinfo=KST)
    assert service.departure(kakao, arrive_by, late) == late


def test_boarding_offsets_split_missing_walk_by_distance():
    first_stop = offset(ORIGIN, east_m=300)
    last_stop = offset(DESTINATION, east_m=-100)
    kakao = route(
        0, 'BUS', [bus(600, first_stop, last_stop)], total_time=1000
    )  # 빠진 도보 400초를 300 : 100으로 나눔
    offsets = service.boarding_offsets(kakao, ORIGIN, DESTINATION)
    assert offsets == {0: 300 + 180}


def test_rail_window_picks_direction_by_next_station():
    up = {'A': (5 * HOUR, 24 * HOUR), 'B': (5 * HOUR + 120, 24 * HOUR + 120)}
    down = {'B': (5 * HOUR + 600, 23 * HOUR), 'A': (5 * HOUR + 720, 23 * HOUR + 120)}
    assert service.rail_window([up, down], 'A역', 'B') == service.Window(5 * HOUR, 24 * HOUR)
    assert service.rail_window([up, down], 'B', 'A') == service.Window(5 * HOUR + 600, 23 * HOUR)


def test_rail_window_undecided_uses_widest():
    up = {'A': (5 * HOUR, 24 * HOUR)}
    down = {'A': (5 * HOUR + 720, 24 * HOUR + 600)}
    assert service.rail_window([up, down], 'A', 'Z') == service.Window(5 * HOUR, 24 * HOUR + 600)
    assert service.rail_window([up, down], 'Q', 'A') is None


def test_station_key():
    assert service.station_key('서울역') == '서울'
    assert service.station_key('총신대입구(이수)역') == '총신대입구'
    assert service.station_key(' 강남 ') == '강남'
    assert service.station_key('역') == '역'


def test_day_type(tmp_path):
    folder = tmp_path / 'holidays'
    folder.mkdir()
    (folder / '2026.csv').write_text('MM-DD,공휴일 이름\r\n12-25,성탄절\r\n', encoding='utf-8-sig')
    holidays = load_holidays(folder)
    assert holidays == {2026: {date(2026, 12, 25)}}
    assert service.day_type(date(2026, 12, 25), holidays) == 'holiday'
    assert service.day_type(date(2026, 12, 24), holidays) == 'weekday'
    assert service.day_type(date(2026, 12, 26), holidays) == 'saturday'
    assert service.day_type(date(2026, 12, 27), holidays) == 'sunday'
    # 2027년 파일이 없으면 평일은 모름, 주말은 요일로 판단
    assert service.day_type(date(2027, 1, 4), holidays) is None
    assert service.day_type(date(2027, 1, 2), holidays) == 'saturday'


def test_project_holiday_files_load():
    from app import config

    holidays = load_holidays(config.DATA_DIR / 'holidays')
    assert date(2026, 10, 9) in holidays[2026]
    assert date(2027, 12, 27) in holidays[2027]


def test_clock_seconds_formats():
    assert clock_seconds('05:30') == 5 * HOUR + 1800
    assert clock_seconds('0530') == 5 * HOUR + 1800
    assert clock_seconds(530) == 5 * HOUR + 1800
    assert clock_seconds('245000') == 24 * HOUR + 3000
    assert clock_seconds('24:05') == 24 * HOUR + 300
    assert clock_seconds('') is None
    assert clock_seconds('ab') is None
    assert clock_seconds(None) is None


def test_stamp_seconds_relative_to_day():
    day = date(2026, 10, 20)
    assert stamp_seconds('20261020233000', day) == 23 * HOUR + 1800
    assert stamp_seconds('20261021035000', day) == 27 * HOUR + 3000
    assert stamp_seconds('', day) is None
