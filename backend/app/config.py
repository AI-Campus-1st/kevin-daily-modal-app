'''환경 변수와 rules.md 12장 기본값 상수

- 인증키는 환경 변수로만 읽음 (tech_stack.md 7장). 개발 중에는 backend/.env를 python-dotenv로 읽음
- 경로 만들기 기본값은 이 파일 한 곳에만 둠 (backend/CLAUDE.md 3장)
'''

import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BACKEND_DIR.parent / 'frontend'
DATA_DIR = BACKEND_DIR / 'data'  # 공휴일, 지하철 시간표 파일 (datasource.md 7.1, 7.4)

load_dotenv(BACKEND_DIR / '.env')


def kakao_key():
    '''카카오 REST API 키. 없으면 빈 문자열'''
    return os.environ.get('KAKAO_REST_API', '')


def seoul_key():
    '''열린데이터광장 일반 인증키. 없으면 빈 문자열'''
    return os.environ.get('DATA_SEOUL_GOKR_GENERIC_API', '')


def gokr_key():
    '''공공데이터포털 일반 인증키 (버스 노선 첫차, 막차). 없으면 빈 문자열'''
    return os.environ.get('DATA_GOKR_GENERIC_API', '')


def subway_key():
    '''열린데이터광장 실시간 지하철 인증키 (권장 F-26). 없으면 빈 문자열'''
    return os.environ.get('DATA_SEOUL_GOKR_SUBWAY_API', '')


def map_js_key():
    '''카카오 JavaScript 키 (권장 F-16). 화면에 보내는 키. 없으면 None'''
    return os.environ.get('KAKAO_JS_API') or None


# rules.md 12장 기본값 (서버가 쓰는 것만)
KICKBOARD_SPEED = 15 * 1000 / 3600  # 15km/h를 m/s로 바꾼 값
BIKE_COND1_WALK = 1200  # 초 (20분)
BIKE_COND2_RATIO = 1.15
BIKE_COND3_TOTAL = 1800  # 초 (30분)
BIKE_STATION_RADIUS = 500  # m
BIKE_RENT_SECONDS = 60
BIKE_RETURN_SECONDS = 30
BUS_WAIT_SECONDS = 180
SUBWAY_WAIT_SECONDS = 180
BUS_ROUTE_SPEED = 15 * 1000 / 3600  # 15km/h를 m/s로 바꾼 값. 버스 노선 전체 운행 시간 계산

# 카카오 도보, 자전거 경로 방식 (rules.md 3.2, 5.2, 7장)
WALK_MODE = 'BROAD_FIRST'
BICYCLE_MODE = 'SHORTEST'

# 메모리 캐시 보관 시간, 초 (tech_stack.md 3.5)
BIKE_LIST_TTL = 30
TRANSIT_TTL = 24 * 3600
PATH_TTL = 24 * 3600
TIMETABLE_TTL = 24 * 3600  # 캐시 열쇠에 날짜를 넣어 그날 안에서만 다시 씀
LIVE_TTL = 20  # 실시간 위치. 한 번의 요청 안에서 같은 조회를 다시 쓰는 정도만 (tech_stack.md 3.5)

# 외부 API
KAKAO_HOST = 'https://dapi.kakao.com'
SEOUL_HOST = 'http://openapi.seoul.go.kr:8088'
SEOUL_BUS_HOST = 'http://ws.bus.go.kr/api/rest'  # DS-9
GYEONGGI_BUS_HOST = 'https://apis.data.go.kr/6410000/busrouteservice/v2'  # DS-10
INCHEON_BUS_HOST = 'https://apis.data.go.kr/6280000/busRouteService'  # DS-11
GYEONGGI_LOCATION_HOST = 'https://apis.data.go.kr/6410000/buslocationservice/v2'  # DS-15
INCHEON_LOCATION_HOST = 'https://apis.data.go.kr/6280000/busLocationService'  # DS-16
SUBWAY_LIVE_HOST = 'http://swopenapi.seoul.go.kr/api/subway'  # DS-17
HTTP_TIMEOUT = 10.0  # 초. 넘으면 조회 실패(unavailable)로 처리
ADDRESS_PAGE_SIZE = 10  # datasource.md 4장 size 기본값
BIKE_PAGE_SIZE = 1000  # datasource.md 7장 1회 최대 건수
BIKE_FIRST_PAGES = 3  # 처음에 동시에 받는 쪽 수 (2,716곳, 2026-10-19)
SEOUL_ROUTE_PAGE_SIZE = 1000  # DS-19 1회 최대 건수 (전체 41,688행, 2026-10-21)
SEOUL_ROUTE_PARALLEL = 8  # DS-19 전체를 받을 때 동시에 보내는 요청 수
