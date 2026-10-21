// 구간 세부 문구와 지도 선 (screen-today.md 6.1, screen-map.md 2장)
// - 서버 응답의 경로 하나를 받아 화면에 보일 값만 만듦. 화면 요소, 지도 SDK에는 접근하지 않음
// - 시간은 분 단위 올림, 거리는 100m 단위 반올림해 소수 첫째 자리 (screens.md 3.3)

import { ceilMinutes, floorToMinute, formatClock } from './departure.js';
import { BIKE_TONE, PM_TONE, WALK_TONE, legTone, namedTone } from './modes.js';

// 거리(m)를 'N.N' km 글자로
export function formatKm(distance) {
  return (Math.round(distance / 100) / 10).toFixed(1);
}

function isTransit(leg) {
  return leg?.type === 'bus' || leg?.type === 'subway';
}

// 도보 앞쪽 끝 이름: 앞 구간의 하차 정류장. 앞 구간이 없으면 fallback
function placeBefore(leg, fallback) {
  if (isTransit(leg)) {
    return leg.stops.at(-1) ?? fallback;
  }
  if (leg?.type === 'bike') {
    return '따릉이 반납 대여소';
  }
  return fallback;
}

// 도보 뒤쪽 끝 이름: 다음 구간의 승차 정류장. 다음 구간이 없으면 fallback
function placeAfter(leg, fallback) {
  if (isTransit(leg)) {
    return leg.stops[0] ?? fallback;
  }
  if (leg?.type === 'bike') {
    return '따릉이 대여 대여소';
  }
  return fallback;
}

function walkRow(leg, prev, next) {
  let start;
  let end;
  if (leg.edge === 'origin') {
    start = '출발지';
    end = placeAfter(next, '도착지');
  } else if (leg.edge === 'destination') {
    start = placeBefore(prev, '출발지');
    end = '도착지';
  } else {
    start = placeBefore(prev, '출발지');
    end = placeAfter(next, '도착지');
  }
  return {
    iconName: 'walk',
    title: '도보',
    tone: WALK_TONE,
    lines: [`${start} → ${end}`, `${ceilMinutes(leg.seconds)}분 · ${formatKm(leg.distance)}km`],
  };
}

// 노선 이름 목록. 같은 이름(일반, 급행 등)은 한 번만
function vehicleNames(leg) {
  return [...new Set(leg.vehicles.map((vehicle) => vehicle.name))];
}

function transitRow(leg) {
  const unit = leg.type === 'bus' ? '정류장' : '역';
  const lines = [];
  if (leg.stops.length) {
    const count = Math.max(leg.stops.length - 1, 0);
    lines.push(`${leg.stops[0]} → ${leg.stops.at(-1)} · ${count}개 ${unit}`);
  }
  lines.push(`${ceilMinutes(leg.seconds)}분 · 승차 대기 ${ceilMinutes(leg.waitSeconds)}분`);
  return {
    iconName: leg.type,
    title: vehicleNames(leg).join(', '),
    tone: legTone(leg),
    lines,
  };
}

function bikeRow(leg) {
  return {
    iconName: 'bike',
    title: `따릉이 ${ceilMinutes(leg.seconds)}분`,
    tone: BIKE_TONE,
    lines: [
      `${leg.rentStation.name} → ${leg.returnStation.name}`,
      `대여소까지 도보 ${ceilMinutes(leg.toStationSeconds)}분, ` +
        `대여·반납 ${ceilMinutes(leg.rentSeconds + leg.returnSeconds)}분, ` +
        `자전거 ${ceilMinutes(leg.rideSeconds)}분, ` +
        `반납 후 도보 ${ceilMinutes(leg.fromStationSeconds)}분`,
    ],
  };
}

// 실시간 위치 문구 (screen-today.md 6.1, 권장 F-26). 행을 만들지 않으면 null
// - timetable: 지금부터 다음 열차까지 분 단위 올림. 이미 지났으면 null
export function positionText(type, position, now) {
  if (position.status === 'live') {
    if (position.stopsAway === 0) {
      return '도착';
    }
    return type === 'bus' ? `${position.stopsAway}정거장 전` : `${position.stopsAway}역 전`;
  }
  if (position.status === 'timetable' && position.nextDeparture) {
    const seconds = (new Date(position.nextDeparture).getTime() - now.getTime()) / 1000;
    return seconds > 0 ? `${ceilMinutes(seconds)}분 후 도착 예정` : null;
  }
  if (position.status === 'none') {
    return '정보 없음';
  }
  return null;
}

// 구간 아래 노선별 위치 행. 아이콘 없이 '{노선 이름}'과 위치 문구 칩 한 줄
// - 행의 색은 안내 대상 노선의 색 (DESIGN.md 2.4)
function positionRows(leg, now) {
  const rows = [];
  for (const position of leg.positions ?? []) {
    const text = positionText(leg.type, position, now);
    if (text) {
      rows.push({
        iconName: null,
        title: position.vehicle,
        position: text,
        tone: namedTone(leg, position.vehicle),
        lines: [],
      });
    }
  }
  return rows;
}

// 펼친 구간 맨 아래의 위치 기준 시각 'HH:MM' (fetchedAt 분 단위 버림). 버스, 지하철 구간이 없으면 null
export function liveBasis(key, route, fetchedAt) {
  if (key === 'pmOnly' || !fetchedAt || !route.legs.some(isTransit)) {
    return null;
  }
  return formatClock(floorToMinute(new Date(fetchedAt)));
}

// 구간 행 목록. key는 'base', 'bikeMix', 'busOnly', 'pmOnly'
// 행: { iconName, title, tone, lines: [글자...] }. 위치 행은 position(위치 문구)이 더 있음
// - tone: 수단 색 { color, ink } (DESIGN.md 2.4)
// - now가 있으면 버스, 지하철 구간 아래에 노선별 실시간 위치 행을 더함 (권장 F-26)
export function legRows(key, route, now = null) {
  if (key === 'pmOnly') {
    return [
      {
        iconName: 'bike',
        title: `자전거 ${ceilMinutes(route.totalSeconds)}분`,
        tone: PM_TONE,
        lines: [`${formatKm(route.totalDistance)}km · 자전거 길 기준`],
      },
    ];
  }
  return route.legs.flatMap((leg, index) => {
    if (leg.type === 'walk') {
      return [walkRow(leg, route.legs[index - 1], route.legs[index + 1])];
    }
    if (leg.type === 'bike') {
      return [bikeRow(leg)];
    }
    return [transitRow(leg), ...(now ? positionRows(leg, now) : [])];
  });
}

// 지도의 한 토막: 같은 수단으로 이어지는 선 하나
// - start: 토막이 시작되는 지점. 없으면 points의 첫 좌표
function segment(tone, dash, points, start = null) {
  return { tone, dash, points: points ?? [], start };
}

function segmentsOf(key, route) {
  if (key === 'pmOnly') {
    return [segment(PM_TONE, 'solid', route.points)];
  }
  const segments = [];
  for (const leg of route.legs) {
    if (leg.type === 'walk') {
      segments.push(segment(WALK_TONE, 'shortdash', leg.points));
    } else if (isTransit(leg)) {
      segments.push(segment(legTone(leg), 'solid', leg.points));
    } else if (leg.type === 'bike') {
      const rent = [leg.rentStation.x, leg.rentStation.y];
      const back = [leg.returnStation.x, leg.returnStation.y];
      segments.push(segment(WALK_TONE, 'shortdash', leg.toStationPoints));
      segments.push(segment(BIKE_TONE, 'solid', leg.ridePoints, rent));
      segments.push(segment(WALK_TONE, 'shortdash', leg.fromStationPoints, back));
    }
  }
  return segments;
}

function startOf(item) {
  return item.start ?? item.points[0] ?? null;
}

// 환승 지점: 두 번째 토막부터 각 토막의 시작 지점. 출발지(첫 토막의 시작)는 빼고, 좌표를 모르면 건너뜀
// - 토막에 좌표가 없으면 앞 토막의 마지막 좌표를 씀
function transferPoints(segments) {
  const points = [];
  for (let index = 1; index < segments.length; index += 1) {
    const point = startOf(segments[index]) ?? segments[index - 1].points.at(-1) ?? null;
    if (point) {
      points.push({ x: point[0], y: point[1], tone: segments[index].tone });
    }
  }
  return points;
}

// 지도에 그릴 선과 표시 (screen-map.md 2장)
// - 선: { tone, dash: 'solid' | 'shortdash', points: [[x, y], ...] }. 좌표가 2개 미만인 구간은 그리지 않음
// - 표시: { kind: 'origin' | 'destination' | 'rent' | 'return', x, y }
// - 환승 지점: { x, y, tone }. tone은 환승 뒤 수단의 색
export function mapShapes(key, route, from, to) {
  const markers = [
    { kind: 'origin', x: from.x, y: from.y },
    { kind: 'destination', x: to.x, y: to.y },
  ];
  if (key !== 'pmOnly') {
    for (const leg of route.legs.filter((item) => item.type === 'bike')) {
      markers.push({ kind: 'rent', x: leg.rentStation.x, y: leg.rentStation.y });
      markers.push({ kind: 'return', x: leg.returnStation.x, y: leg.returnStation.y });
    }
  }
  const segments = segmentsOf(key, route);
  const lines = segments
    .filter((item) => item.points.length >= 2)
    .map(({ tone, dash, points }) => ({ tone, dash, points }));
  return { lines, markers, transfers: transferPoints(segments) };
}
