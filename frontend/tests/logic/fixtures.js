// 테스트용 /api/recommend 응답 (api_spec.md 5장 응답 예)
// - 테스트마다 고쳐 쓰므로 부를 때마다 새 객체를 만듦

const SAMPLE = {
  fetchedAt: '2026-10-20T08:20:05+09:00',
  transit: { status: 'ok' },
  bikeData: { status: 'ok', fetchedAt: '2026-10-20T08:20:03+09:00' },
  base: {
    routeIndex: 0,
    type: 'subway',
    totalSeconds: 1560,
    totalDistance: 4000,
    transfers: 0,
    fare: 1550,
    waitSeconds: 180,
    edgeWalkKnown: true,
    legs: [
      { type: 'walk', seconds: 480, distance: 650, edge: 'origin' },
      {
        type: 'subway', seconds: 480, waitSeconds: 180, distance: 2800,
        stops: ['건대입구', '성수', '뚝섬', '한양대'], vehicles: [{ type: '수도권', name: '2호선' }],
      },
      { type: 'walk', seconds: 420, distance: 550, edge: 'destination' },
    ],
    pmSaving: { firstSeconds: 324, lastSeconds: 288, totalSeconds: 612 },
  },
  bikeMix: {
    kind: 'full',
    conditions: { first: false, second: null, third: true },
    totalSeconds: 1110,
    transfers: 0,
    stockKnown: true,
    legs: [
      {
        type: 'bike', mile: 'full', seconds: 1110, replacedSeconds: 1560,
        toStationSeconds: 240, rentSeconds: 60, rideSeconds: 720, returnSeconds: 30, fromStationSeconds: 60,
        rentStation: { id: 'ST-0000', name: '예시 대여소', availableBikes: 2, distance: 260 },
        returnStation: { id: 'ST-0001', name: '예시 반납 대여소', availableRacks: 5, distance: 70 },
      },
    ],
  },
  busOnly: null,
  pmOnly: { totalSeconds: 780, totalDistance: 3400 },
  notes: [{ target: 'busOnly', reason: 'none' }],
};

// 응답 예의 깊은 복사본
export function sampleResponse() {
  return structuredClone(SAMPLE);
}

// 버스 전용 경로 (api_spec.md 4.3 형식, 값은 가상)
export function sampleBusOnly(totalSeconds) {
  return {
    routeIndex: 2,
    type: 'bus',
    totalSeconds,
    totalDistance: 4300,
    transfers: 1,
    fare: 1500,
    waitSeconds: 360,
    edgeWalkKnown: true,
    legs: [
      { type: 'walk', seconds: 300, distance: 400, edge: 'origin' },
      {
        type: 'bus', seconds: 900, waitSeconds: 180, distance: 2500,
        stops: ['가 정류장', '나 정류장'], vehicles: [{ type: '간선', name: '000' }],
      },
      { type: 'walk', seconds: 120, distance: 150, edge: null },
      {
        type: 'bus', seconds: 600, waitSeconds: 180, distance: 1100,
        stops: ['다 정류장', '라 정류장'], vehicles: [{ type: '지선', name: '0000' }],
      },
      { type: 'walk', seconds: 240, distance: 150, edge: 'destination' },
    ],
  };
}

// 따릉이 구간 하나 (api_spec.md 4.8 bike 형식, 값은 가상)
export function sampleBikeLeg({ mile, seconds, replacedSeconds, availableBikes = 3 }) {
  return {
    type: 'bike', mile, seconds, replacedSeconds,
    toStationSeconds: 120, rentSeconds: 60, rideSeconds: seconds - 270, returnSeconds: 30, fromStationSeconds: 60,
    rentStation: { id: 'ST-1000', name: '가상 대여소', availableBikes, distance: 150 },
    returnStation: { id: 'ST-1001', name: '가상 반납 대여소', availableRacks: 4, distance: 90 },
  };
}
