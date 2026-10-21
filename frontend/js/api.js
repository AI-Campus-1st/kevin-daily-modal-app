// 서버 API 호출 (api_spec.md 3, 4장)
// - 주소 검색어와 좌표는 주소창에 남지 않도록 POST 본문으로만 보냄
// - 서버에 연결하지 못하거나 HTTP 오류이면 null

async function post(path, body) {
  try {
    const response = await fetch(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      return null;
    }
    return await response.json();
  } catch {
    return null;
  }
}

// 주소, 장소 검색. 연결 실패도 status 'unavailable'로 돌려줌
// - 다음 쪽은 첫 응답의 source('address', 'place')를 함께 보냄 (api_spec.md 3.1)
export async function searchAddress(query, page = 1, source = null) {
  const body = source ? { query, page, source } : { query, page };
  const data = await post('/api/address/search', body);
  return data ?? { status: 'unavailable', source: null, items: [], isEnd: true };
}

// 4종 경로 추천. from, to는 좌표(x, y)가 있는 장소. 연결 실패이면 null
// - arriveBy: 기준 도착 시각(목표 도착 시각 - 여유 시간). 없으면 보내지 않음 (api_spec.md 4.1)
export async function recommend(from, to, arriveBy = null) {
  const body = {
    origin: { x: from.x, y: from.y },
    destination: { x: to.x, y: to.y },
  };
  if (arriveBy) {
    body.arriveBy = arriveBy;
  }
  return post('/api/recommend', body);
}

// 화면 설정 (api_spec.md 2.1). 지도 키가 없거나 연결 실패이면 null
export async function mapKey() {
  try {
    const response = await fetch('/api/config');
    if (!response.ok) {
      return null;
    }
    const data = await response.json();
    return data.kakaoMapKey ?? null;
  } catch {
    return null;
  }
}
