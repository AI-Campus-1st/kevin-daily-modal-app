'''요청, 응답 Pydantic 모델 (api_spec.md)

- Python 코드는 밑줄 표기, 응답 필드는 별칭(낮은 카멜 표기)으로 바꿈
- 시간 길이는 초 단위 정수, 거리는 미터 단위 정수
'''

from datetime import datetime
from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel

Status = Literal['ok', 'no_result', 'unavailable']

# 지도 선 좌표 목록. [경도, 위도] 쌍의 배열 (api_spec.md 4.9)
Line = list[tuple[float, float]]


class CamelModel(BaseModel):
    '''필드 이름을 낮은 카멜 표기 별칭으로 내보내는 공통 모델'''

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class RequestModel(CamelModel):
    '''요청 모델. api_spec.md 6장의 값 외에는 받지 않으므로 정의하지 않은 필드는 422'''

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra='forbid')


# 주소, 장소 검색 (api_spec.md 3장)

SearchSource = Literal['address', 'place']


class AddressSearchRequest(RequestModel):
    query: str
    page: int = Field(default=1, ge=1, le=45)
    source: SearchSource | None = None  # 다음 쪽 요청 때 첫 응답의 source

    @field_validator('query')
    @classmethod
    def check_query(cls, value):
        '''앞뒤 공백을 지운 뒤 100자 이하, 공백을 뺀 글자 2자 이상'''
        value = value.strip()
        if len(value) > 100:
            raise ValueError('100자 이하')
        if len(''.join(value.split())) < 2:
            raise ValueError('공백 제외 2자 이상')
        return value


class AddressItem(CamelModel):
    address_name: str
    road_address: str | None
    jibun_address: str | None
    building_name: str | None
    x: float
    y: float
    place_name: str | None = None


class AddressSearchResponse(CamelModel):
    status: Status
    source: SearchSource | None
    items: list[AddressItem]
    is_end: bool


# 추천 (api_spec.md 4장)


class Point(RequestModel):
    x: float = Field(ge=124, le=132)
    y: float = Field(ge=33, le=39)

    def as_tuple(self):
        '''(경도, 위도) 튜플'''
        return (self.x, self.y)


class RecommendRequest(RequestModel):
    origin: Point
    destination: Point
    arrive_by: AwareDatetime | None = None  # 목표 도착 시각 − 여유 시간 (rules.md 3.4.1)


class WalkLeg(CamelModel):
    type: Literal['walk'] = 'walk'
    seconds: int
    distance: int
    edge: Literal['origin', 'destination'] | None
    points: Line = []


class Vehicle(CamelModel):
    type: str
    name: str


class Position(CamelModel):
    '''구간 노선 하나의 실시간 위치 (api_spec.md 4.10, 권장 F-26)'''

    vehicle: str
    status: Literal['live', 'none', 'timetable', 'unknown']
    stops_away: int | None = None
    next_departure: datetime | None = None
    observed_at: datetime | None = None


class TransitLeg(CamelModel):
    type: Literal['bus', 'subway']
    seconds: int
    wait_seconds: int
    distance: int
    stops: list[str]
    vehicles: list[Vehicle]
    service_unknown: bool = False
    positions: list[Position] = []
    points: Line = []


class RentStation(CamelModel):
    id: str
    name: str
    available_bikes: int | None
    distance: int
    x: float
    y: float


class ReturnStation(CamelModel):
    id: str
    name: str
    available_racks: int | None
    distance: int
    x: float
    y: float


class BikeLeg(CamelModel):
    type: Literal['bike'] = 'bike'
    mile: Literal['first', 'last', 'full']
    seconds: int
    replaced_seconds: int
    to_station_seconds: int
    rent_seconds: int
    ride_seconds: int
    return_seconds: int
    from_station_seconds: int
    rent_station: RentStation
    return_station: ReturnStation
    to_station_points: Line = []
    ride_points: Line = []
    from_station_points: Line = []


Leg = Annotated[WalkLeg | TransitLeg | BikeLeg, Field(discriminator='type')]


class TransitRoute(CamelModel):
    route_index: int
    type: Literal['bus', 'subway', 'bus_subway']
    total_seconds: int
    total_distance: int
    wait_seconds: int
    edge_walk_known: bool
    transfers: int
    fare: int | None
    legs: list[Leg]
    service_unknown: bool = False


class PmSaving(CamelModel):
    first_seconds: int
    last_seconds: int
    total_seconds: int


class BaseRoute(TransitRoute):
    pm_saving: PmSaving | None


class Conditions(CamelModel):
    first: bool
    second: bool | None
    third: bool | None


class BikeMix(CamelModel):
    kind: Literal['first_last', 'full']
    conditions: Conditions
    total_seconds: int
    transfers: int
    stock_known: bool
    legs: list[Leg]
    service_unknown: bool = False


class PmOnly(CamelModel):
    total_seconds: int
    total_distance: int
    points: Line = []


class Note(CamelModel):
    target: Literal['bikeMix', 'busOnly', 'pmOnly']
    reason: Literal['no_condition', 'no_station', 'route_failed', 'none', 'same_as_base']


class TransitStatus(CamelModel):
    status: Literal['ok', 'no_result', 'unavailable', 'out_of_service']


class BikeDataStatus(CamelModel):
    status: Literal['ok', 'unavailable']
    fetched_at: datetime | None


class ClientConfigResponse(CamelModel):
    kakao_map_key: str | None


class RecommendResponse(CamelModel):
    fetched_at: datetime
    transit: TransitStatus
    bike_data: BikeDataStatus
    base: BaseRoute | None
    bike_mix: BikeMix | None
    bus_only: TransitRoute | None
    pm_only: PmOnly | None
    notes: list[Note]
