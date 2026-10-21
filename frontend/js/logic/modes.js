// 수단 색 고르기 (DESIGN.md 2.4)
// - 구간, 노선을 받아 수단 색 토큰 이름과 그 색 위의 글자 토큰 이름을 돌려줌. 화면 요소에는 접근하지 않음
// - 색: { color: 'subway-line2', ink: 'ink-dark' }. 화면은 var(--colors-{이름})으로 씀
// - 글자는 DESIGN.md 2.4 표의 '글자' (on-primary, ink-dark 중 대비가 높은 쪽). on-primary는 두 화면 모드 모두 흰색 (2.5.4)

const INK = {
  'mode-walk': 'on-primary',
  'mode-bike': 'ink-dark',
  'mode-pm': 'ink-dark',
  'subway-line1': 'on-primary',
  'subway-line2': 'ink-dark',
  'subway-line3': 'ink-dark',
  'subway-line4': 'ink-dark',
  'subway-line5': 'ink-dark',
  'subway-line6': 'ink-dark',
  'subway-line7': 'ink-dark',
  'subway-line8': 'ink-dark',
  'subway-line9': 'ink-dark',
  'subway-gyeongui-jungang': 'ink-dark',
  'subway-suin-bundang': 'ink-dark',
  'subway-shinbundang': 'on-primary',
  'subway-airport': 'on-primary',
  'subway-gyeongchun': 'ink-dark',
  'subway-gyeonggang': 'on-primary',
  'subway-seohae': 'ink-dark',
  'subway-ui-sinseol': 'ink-dark',
  'subway-sillim': 'ink-dark',
  'subway-gimpo-goldline': 'ink-dark',
  'subway-incheon1': 'ink-dark',
  'subway-incheon2': 'ink-dark',
  'subway-uijeongbu': 'ink-dark',
  'subway-everline': 'ink-dark',
  'subway-gtx-a': 'on-primary',
  'bus-trunk': 'on-primary',
  'bus-branch': 'ink-dark',
  'bus-village': 'ink-dark',
  'bus-wide': 'on-primary',
  'bus-direct': 'on-primary',
  'bus-rapid': 'on-primary',
  'bus-general': 'ink-dark',
  'bus-seat': 'on-primary',
  'bus-circular': 'ink-dark',
  'bus-airport': 'on-primary',
  'bus-night': 'on-primary',
  primary: 'on-primary',
};

// 카카오 지하철 노선 이름 → 색 토큰 (DESIGN.md 2.4.2)
const SUBWAY = {
  '1호선': 'subway-line1',
  '2호선': 'subway-line2',
  '3호선': 'subway-line3',
  '4호선': 'subway-line4',
  '5호선': 'subway-line5',
  '6호선': 'subway-line6',
  '7호선': 'subway-line7',
  '8호선': 'subway-line8',
  '9호선': 'subway-line9',
  경의중앙선: 'subway-gyeongui-jungang',
  수인분당선: 'subway-suin-bundang',
  신분당선: 'subway-shinbundang',
  공항철도: 'subway-airport',
  경춘선: 'subway-gyeongchun',
  경강선: 'subway-gyeonggang',
  서해선: 'subway-seohae',
  우이신설선: 'subway-ui-sinseol',
  신림선: 'subway-sillim',
  김포골드라인: 'subway-gimpo-goldline',
  인천1호선: 'subway-incheon1',
  인천2호선: 'subway-incheon2',
  의정부경전철: 'subway-uijeongbu',
  에버라인: 'subway-everline',
  용인에버라인: 'subway-everline',
  'GTX-A': 'subway-gtx-a',
};

// 카카오 버스 종류 → 색 토큰 (DESIGN.md 2.4.3)
const BUS = {
  간선: 'bus-trunk',
  지선: 'bus-branch',
  마을: 'bus-village',
  광역: 'bus-wide',
  직행: 'bus-direct',
  급행: 'bus-rapid',
  일반: 'bus-general',
  좌석: 'bus-seat',
  순환: 'bus-circular',
  공항: 'bus-airport',
  심야: 'bus-night',
};

// 표에 없는 노선, 종류의 색
const FALLBACK = 'primary';

function tone(color) {
  return { color, ink: INK[color] };
}

export const WALK_TONE = tone('mode-walk');
export const BIKE_TONE = tone('mode-bike');
export const PM_TONE = tone('mode-pm');

// 노선 하나의 색. legType은 'bus' 또는 'subway', vehicle은 { type, name }
export function vehicleTone(legType, vehicle) {
  const color = legType === 'bus' ? BUS[vehicle?.type] : SUBWAY[vehicle?.name];
  return tone(color ?? FALLBACK);
}

// 구간 하나의 색. 버스, 지하철은 첫 번째 노선의 색 (DESIGN.md 2.4)
export function legTone(leg) {
  if (leg.type === 'walk') {
    return WALK_TONE;
  }
  if (leg.type === 'bike') {
    return BIKE_TONE;
  }
  return vehicleTone(leg.type, leg.vehicles?.[0]);
}

// 이름이 같은 노선의 색 (실시간 위치 행). 구간에 없는 이름이면 구간의 색
export function namedTone(leg, name) {
  const vehicle = leg.vehicles?.find((item) => item.name === name);
  return vehicle ? vehicleTone(leg.type, vehicle) : legTone(leg);
}
