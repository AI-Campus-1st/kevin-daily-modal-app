'''FastAPI 앱, 라우터 연결, frontend/ 정적 파일 연결

- 로그에는 요청 주소(경로 부분), 응답 코드, 처리 시간, 외부 호출 결과 상태만 남김 (api_spec.md 6장)
  - httpx의 요청 로그는 주소에 좌표, 인증키가 들어 있으므로 끔
  - Uvicorn 접속 로그는 접속한 곳의 주소가 들어 있으므로 끄고 아래 미들웨어가 대신 기록
'''

import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app import config
from app.clients.bike import BikeClient
from app.clients.kakao import KakaoClient
from app.clients.live import LiveClient
from app.clients.timetable import TimetableClient
from app.routers import address, client_config, recommend

KST = timezone(timedelta(hours=9))

logger = logging.getLogger('app')
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(name)s %(message)s'))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)
logger.propagate = False
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('uvicorn.access').disabled = True


def now_kst():
    '''한국 표준시 지금 시각'''
    return datetime.now(KST)


@asynccontextmanager
async def lifespan(app):
    '''서버를 켤 때 외부 호출용 클라이언트를 만들고, 끌 때 닫음'''
    async with httpx.AsyncClient() as http:
        app.state.now = now_kst
        app.state.kakao = KakaoClient(http, config.kakao_key())
        app.state.bike = BikeClient(http, config.seoul_key(), now=now_kst)
        app.state.timetable = TimetableClient(
            http, config.gokr_key(), config.seoul_key(), config.DATA_DIR
        )
        app.state.live = LiveClient(
            app.state.timetable,
            config.gokr_key(),
            config.seoul_key(),
            config.subway_key(),
            now=lambda: app.state.now(),
        )
        yield


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)


@app.middleware('http')
async def log_request(request, call_next):
    '''요청마다 경로, 응답 코드, 처리 시간을 기록

    - 처리 중 오류는 종류 이름만 기록하고 500으로 응답
    '''
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception as error:
        logger.error('%s %s error %s', request.method, request.url.path, type(error).__name__)
        response = JSONResponse({'detail': 'Internal Server Error'}, status_code=500)
    elapsed = (time.perf_counter() - started) * 1000
    logger.info('%s %s %d %.0fms', request.method, request.url.path, response.status_code, elapsed)
    return response


app.include_router(address.router)
app.include_router(recommend.router)
app.include_router(client_config.router)

# 브라우저가 저장해 둔 파일을 쓰기 전에 매번 바뀌었는지 서버에 확인하게 하는 값
# 바뀌지 않았으면 서버가 본문 없이 304로 답하므로, 고친 화면 파일이 바로 반영됨
NO_CACHE = {'Cache-Control': 'no-cache'}


class FrontendFiles(StaticFiles):
    '''화면 파일 제공. 응답마다 NO_CACHE 머리글을 붙임'''

    def file_response(self, *args, **kwargs):
        response = super().file_response(*args, **kwargs)
        response.headers.update(NO_CACHE)
        return response


# 정적 파일 (api_spec.md 2장). frontend/ 전체가 아니라 화면에 필요한 폴더만 제공
# 서버를 켤 때 있는 폴더만 연결하므로, 폴더를 새로 만들면 서버를 다시 켜야 함
for folder in ('css', 'js', 'fonts'):
    if (config.FRONTEND_DIR / folder).is_dir():
        app.mount(f'/{folder}', FrontendFiles(directory=config.FRONTEND_DIR / folder), name=folder)


@app.get('/', include_in_schema=False)
async def index():
    '''frontend/index.html'''
    path = config.FRONTEND_DIR / 'index.html'
    if not path.is_file():
        return JSONResponse({'detail': 'Not Found'}, status_code=404)
    return FileResponse(path, headers=NO_CACHE)
