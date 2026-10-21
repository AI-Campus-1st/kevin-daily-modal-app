'''화면 설정 GET /api/config (api_spec.md 2.1)

- 경로 지도(권장 F-16)에 쓰는 카카오 JavaScript 키만 보냄. REST API 키는 보내지 않음
- 사용자 정보를 받지 않음
'''

from fastapi import APIRouter

from app import config
from app.schemas import ClientConfigResponse

router = APIRouter()


@router.get('/api/config', response_model=ClientConfigResponse)
async def client_config():
    return ClientConfigResponse(kakao_map_key=config.map_js_key())
