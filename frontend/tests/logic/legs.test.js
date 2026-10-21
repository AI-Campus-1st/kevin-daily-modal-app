// 구간 세부 문구, 지도 선 테스트 (screen-today.md 6.1, screen-map.md 2장)

import { test } from 'node:test';
import assert from 'node:assert/strict';

import { formatKm, legRows, liveBasis, mapShapes, positionText } from '../../js/logic/legs.js';
import { BIKE_TONE, PM_TONE, WALK_TONE } from '../../js/logic/modes.js';
import { sampleResponse } from './fixtures.js';

const FROM = { x: 127.0, y: 37.5 };
const TO = { x: 127.05, y: 37.53 };

test('거리는 100m 단위 반올림해 소수 첫째 자리', () => {
  assert.equal(formatKm(650), '0.7');
  assert.equal(formatKm(3449), '3.4');
  assert.equal(formatKm(3450), '3.5');
});

test('기본 경로: 도보의 시작, 끝은 이웃 구간의 정류장', () => {
  const rows = legRows('base', sampleResponse().base);
  assert.deepEqual(rows[0], {
    iconName: 'walk',
    title: '도보',
    tone: WALK_TONE,
    lines: ['출발지 → 건대입구', '8분 · 0.7km'],
  });
  assert.deepEqual(rows[1], {
    iconName: 'subway',
    title: '2호선',
    tone: { color: 'subway-line2', ink: 'ink-dark' },
    lines: ['건대입구 → 한양대 · 3개 역', '8분 · 승차 대기 3분'],
  });
  assert.deepEqual(rows[2].lines, ['한양대 → 도착지', '7분 · 0.6km']);
});

test('버스 구간은 노선 이름을 모두 쉼표로 잇고 정류장 수를 셈', () => {
  const route = sampleResponse().base;
  route.legs[1] = {
    type: 'bus', seconds: 600, waitSeconds: 180, distance: 2500,
    stops: ['가', '나', '다'], vehicles: [{ type: '간선', name: '606' }, { type: '간선', name: '643' }],
  };
  const row = legRows('base', route)[1];
  assert.equal(row.title, '606, 643');
  assert.deepEqual(row.lines, ['가 → 다 · 2개 정류장', '10분 · 승차 대기 3분']);
});

test('같은 노선 이름(일반, 급행)은 한 번만', () => {
  const route = sampleResponse().base;
  route.legs[1] = {
    type: 'subway', seconds: 720, waitSeconds: 180, distance: 6000,
    stops: ['시청', '서울역', '남영'],
    vehicles: [{ type: '수도권1호선', name: '1호선' }, { type: '수도권1호선', name: '1호선' }, { type: '수도권4호선', name: '4호선' }],
  };
  assert.equal(legRows('base', route)[1].title, '1호선, 4호선');
});

test('환승 도보는 앞 하차 정류장 → 다음 승차 정류장', () => {
  const route = sampleResponse().base;
  route.legs.splice(2, 0, { type: 'walk', seconds: 130, distance: 120, edge: null }, {
    type: 'bus', seconds: 300, waitSeconds: 180, distance: 1000,
    stops: ['한양대앞', '왕십리'], vehicles: [{ type: '지선', name: '2012' }],
  });
  assert.deepEqual(legRows('base', route)[2].lines, ['한양대 → 한양대앞', '3분 · 0.1km']);
});

test('따릉이 구간은 따릉이 색, 대여소와 세부 시간', () => {
  const [row] = legRows('bikeMix', sampleResponse().bikeMix);
  assert.deepEqual(row.tone, BIKE_TONE);
  assert.equal(row.title, '따릉이 19분');
  assert.deepEqual(row.lines, [
    '예시 대여소 → 예시 반납 대여소',
    '대여소까지 도보 4분, 대여·반납 2분, 자전거 12분, 반납 후 도보 1분',
  ]);
});

test('PM 전용은 한 행', () => {
  assert.deepEqual(legRows('pmOnly', sampleResponse().pmOnly), [
    { iconName: 'bike', title: '자전거 13분', tone: PM_TONE, lines: ['3.4km · 자전거 길 기준'] },
  ]);
});

test('출발, 도착 도보를 모르는 기본 경로는 도보 행이 없음', () => {
  const route = sampleResponse().base;
  route.edgeWalkKnown = false;
  route.legs = [route.legs[1]];
  assert.deepEqual(legRows('base', route).map((row) => row.iconName), ['subway']);
});

test('지도 선: 구간 종류별 모양, 좌표가 2개 미만이면 그리지 않음', () => {
  const route = sampleResponse().base;
  route.legs[0].points = [[127.0, 37.5], [127.01, 37.5]];
  route.legs[1].points = [[127.01, 37.5], [127.04, 37.52]];
  route.legs[2].points = [];
  const shapes = mapShapes('base', route, FROM, TO);
  assert.deepEqual(shapes.lines.map((line) => [line.tone.color, line.dash]), [
    ['mode-walk', 'shortdash'],
    ['subway-line2', 'solid'],
  ]);
  assert.deepEqual(shapes.markers, [
    { kind: 'origin', x: 127.0, y: 37.5 },
    { kind: 'destination', x: 127.05, y: 37.53 },
  ]);
});

test('지도 선: 따릉이 구간은 도보, 자전거, 도보와 대여소 표시', () => {
  const route = sampleResponse().bikeMix;
  const leg = route.legs[0];
  leg.toStationPoints = [[127.0, 37.5], [127.001, 37.5]];
  leg.ridePoints = [[127.001, 37.5], [127.049, 37.53]];
  leg.fromStationPoints = [[127.049, 37.53], [127.05, 37.53]];
  leg.rentStation.x = 127.001;
  leg.rentStation.y = 37.5;
  leg.returnStation.x = 127.049;
  leg.returnStation.y = 37.53;
  const shapes = mapShapes('bikeMix', route, FROM, TO);
  assert.deepEqual(shapes.lines.map((line) => line.tone.color), ['mode-walk', 'mode-bike', 'mode-walk']);
  assert.deepEqual(shapes.markers.map((marker) => marker.kind), ['origin', 'destination', 'rent', 'return']);
});

test('지도 선: PM 전용은 자전거 선 하나', () => {
  const route = sampleResponse().pmOnly;
  route.points = [[127.0, 37.5], [127.05, 37.53]];
  const shapes = mapShapes('pmOnly', route, FROM, TO);
  assert.deepEqual(shapes.lines, [{ tone: PM_TONE, dash: 'solid', points: route.points }]);
  assert.deepEqual(shapes.transfers, []);
});

test('환승 지점: 수단이 바뀌는 곳마다, 출발지는 빼고 환승 뒤 수단 색', () => {
  const route = sampleResponse().base;
  route.legs[0].points = [[127.0, 37.5], [127.01, 37.5]];
  route.legs[1].points = [[127.01, 37.5], [127.04, 37.52]];
  route.legs[2].points = [];
  const { transfers } = mapShapes('base', route, FROM, TO);
  assert.deepEqual(transfers, [
    { x: 127.01, y: 37.5, tone: { color: 'subway-line2', ink: 'ink-dark' } },
    { x: 127.04, y: 37.52, tone: WALK_TONE },
  ]);
});

test('환승 지점: 따릉이 구간은 대여소, 반납 대여소에서도 바뀜', () => {
  const route = sampleResponse().bikeMix;
  const leg = route.legs[0];
  leg.toStationPoints = [[127.0, 37.5], [127.001, 37.5]];
  leg.ridePoints = [];
  leg.fromStationPoints = [];
  leg.rentStation.x = 127.001;
  leg.rentStation.y = 37.5;
  leg.returnStation.x = 127.049;
  leg.returnStation.y = 37.53;
  const { transfers } = mapShapes('bikeMix', route, FROM, TO);
  assert.deepEqual(transfers.map((point) => [point.x, point.tone.color]), [
    [127.001, 'mode-bike'],
    [127.049, 'mode-walk'],
  ]);
});

// 실시간 위치 (권장 F-26, screen-today.md 6.1)

const NOW = new Date('2026-10-20T08:00:00+09:00');

test('위치 문구: 정거장, 역, 도착, 정보 없음, 알 수 없음', () => {
  assert.equal(positionText('bus', { status: 'live', stopsAway: 3 }, NOW), '3정거장 전');
  assert.equal(positionText('subway', { status: 'live', stopsAway: 2 }, NOW), '2역 전');
  assert.equal(positionText('bus', { status: 'live', stopsAway: 0 }, NOW), '도착');
  assert.equal(positionText('subway', { status: 'live', stopsAway: 0 }, NOW), '도착');
  assert.equal(positionText('bus', { status: 'none' }, NOW), '정보 없음');
  assert.equal(positionText('subway', { status: 'unknown' }, NOW), null);
});

test('시간표 위치는 지금부터 분 단위 올림, 지났으면 행 없음', () => {
  const at = (text) => ({ status: 'timetable', nextDeparture: text });
  assert.equal(positionText('subway', at('2026-10-20T08:04:10+09:00'), NOW), '5분 후 도착 예정');
  assert.equal(positionText('subway', at('2026-10-20T08:04:00+09:00'), NOW), '4분 후 도착 예정');
  assert.equal(positionText('subway', at('2026-10-20T07:59:00+09:00'), NOW), null);
});

test('구간 아래 노선별 위치 행, now가 없으면 위치 행 없음', () => {
  const route = sampleResponse().base;
  route.legs[1].positions = [
    { vehicle: '2호선', status: 'live', stopsAway: 2 },
    { vehicle: '2호선 급행', status: 'unknown' },
  ];
  const rows = legRows('base', route, NOW);
  assert.deepEqual(rows.map((row) => row.title), ['도보', '2호선', '2호선', '도보']);
  assert.deepEqual(rows[2], {
    iconName: null,
    title: '2호선',
    position: '2역 전',
    tone: { color: 'subway-line2', ink: 'ink-dark' },
    lines: [],
  });
  assert.equal(legRows('base', route).length, 3);
});

test('위치 기준 시각은 버스, 지하철 구간이 있을 때만', () => {
  const response = sampleResponse();
  assert.equal(liveBasis('base', response.base, '2026-10-20T08:20:59+09:00').length, 5);
  assert.equal(liveBasis('pmOnly', response.pmOnly, '2026-10-20T08:20:59+09:00'), null);
  assert.equal(liveBasis('bikeMix', response.bikeMix, '2026-10-20T08:20:59+09:00'), null);
});
