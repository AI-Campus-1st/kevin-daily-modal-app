'''주소, 장소 검색 중계 POST /api/address/search (api_spec.md 3장)

- source 없이 요청하면 주소 검색(DS-1)을 먼저 하고,
  결과가 0건이면 키워드 장소 검색(DS-7)으로 찾음 (D-32)
- 다음 쪽은 첫 응답의 source로 같은 검색을 이어 감
- 주소 검색이 조회 실패이면 키워드 장소 검색으로 넘어가지 않음
- 검색어는 카카오에 전달만 하고 저장, 로그 기록, 캐시를 하지 않음
'''

from fastapi import APIRouter, Request

from app.schemas import AddressItem, AddressSearchRequest, AddressSearchResponse

router = APIRouter()


async def find(kakao, body):
    '''(검색 결과, source)'''
    if body.source == 'place':
        return await kakao.search_keyword(body.query, body.page), 'place'
    result = await kakao.search_address(body.query, body.page)
    if body.source is None and result.status == 'no_result':
        return await kakao.search_keyword(body.query, body.page), 'place'
    return result, 'address'


@router.post('/api/address/search', response_model=AddressSearchResponse)
async def search_address(body: AddressSearchRequest, request: Request):
    result, source = await find(request.app.state.kakao, body)
    items = [
        AddressItem(
            address_name=item.address_name,
            road_address=item.road_address,
            jibun_address=item.jibun_address,
            building_name=item.building_name,
            x=item.x,
            y=item.y,
            place_name=item.place_name,
        )
        for item in result.items
    ]
    return AddressSearchResponse(
        status=result.status,
        source=source if result.status == 'ok' else None,
        items=items,
        is_end=result.is_end,
    )
