// 수단 색 고르기 테스트 (DESIGN.md 2.4)

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

import { BIKE_TONE, PM_TONE, WALK_TONE, legTone, namedTone, vehicleTone } from '../../js/logic/modes.js';

test('지하철은 노선 이름으로 고름', () => {
  assert.deepEqual(vehicleTone('subway', { type: '일반', name: '2호선' }), { color: 'subway-line2', ink: 'ink-dark' });
  assert.deepEqual(vehicleTone('subway', { type: '급행', name: '신분당선' }), { color: 'subway-shinbundang', ink: 'on-primary' });
  assert.equal(vehicleTone('subway', { type: '일반', name: 'GTX-A' }).color, 'subway-gtx-a');
});

test('버스는 카카오 종류로 고름', () => {
  assert.equal(vehicleTone('bus', { type: '간선', name: '101' }).color, 'bus-trunk');
  assert.equal(vehicleTone('bus', { type: '마을', name: '구로09' }).color, 'bus-village');
  assert.equal(vehicleTone('bus', { type: '직행', name: '1101' }).color, 'bus-direct');
  assert.equal(vehicleTone('bus', { type: '급행', name: '급행95' }).color, 'bus-rapid');
});

test('표에 없는 노선, 종류는 primary', () => {
  assert.deepEqual(vehicleTone('subway', { type: '일반', name: '없는선' }), { color: 'primary', ink: 'on-primary' });
  assert.deepEqual(vehicleTone('bus', { type: '시외', name: '8800' }), { color: 'primary', ink: 'on-primary' });
  assert.deepEqual(vehicleTone('bus', undefined), { color: 'primary', ink: 'on-primary' });
});

test('구간의 색: 도보, 따릉이, 버스와 지하철은 첫 번째 노선', () => {
  assert.deepEqual(legTone({ type: 'walk' }), WALK_TONE);
  assert.deepEqual(legTone({ type: 'bike' }), BIKE_TONE);
  const leg = { type: 'bus', vehicles: [{ type: '지선', name: '2014' }, { type: '간선', name: '101' }] };
  assert.equal(legTone(leg).color, 'bus-branch');
  assert.equal(namedTone(leg, '101').color, 'bus-trunk');
  assert.equal(namedTone(leg, '없음').color, 'bus-branch');
});

// tokens.css의 값으로 글자 토큰이 on-primary, ink-dark 중 대비가 높은 쪽인지 확인 (DESIGN.md 2.3, 2.4)
function luminance(hex) {
  const channels = [1, 3, 5].map((index) => parseInt(hex.slice(index, index + 2), 16) / 255);
  const [r, g, b] = channels.map((c) => (c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4));
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

function contrast(a, b) {
  const [high, low] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (high + 0.05) / (low + 0.05);
}

const TOKENS = readFileSync(new URL('../../css/tokens.css', import.meta.url), 'utf8');

function tokenHex(name) {
  const match = TOKENS.match(new RegExp(`--colors-${name}: (#[0-9a-f]{6});`));
  assert.ok(match, `tokens.css에 --colors-${name} 없음`);
  return match[1];
}

test('수단 색의 글자는 대비가 높은 쪽이고 4.5:1 이상', () => {
  const tones = [
    WALK_TONE,
    BIKE_TONE,
    PM_TONE,
    ...['1호선', '2호선', '3호선', '4호선', '5호선', '6호선', '7호선', '8호선', '9호선', '경의중앙선',
      '수인분당선', '신분당선', '공항철도', '경춘선', '경강선', '서해선', '우이신설선', '신림선',
      '김포골드라인', '인천1호선', '인천2호선', '의정부경전철', '에버라인', 'GTX-A', '없는선']
      .map((name) => vehicleTone('subway', { name })),
    ...['간선', '지선', '마을', '광역', '직행', '급행', '일반', '좌석', '순환', '공항', '심야']
      .map((type) => vehicleTone('bus', { type })),
  ];
  for (const tone of tones) {
    const color = tokenHex(tone.color);
    const white = contrast(color, tokenHex('on-primary'));
    const black = contrast(color, tokenHex('ink-dark'));
    assert.equal(tone.ink, white >= black ? 'on-primary' : 'ink-dark', tone.color);
    assert.ok(Math.max(white, black) >= 4.5, tone.color);
  }
});
