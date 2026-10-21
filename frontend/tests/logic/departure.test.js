// 출발 시각, 분 단위 처리 테스트 (rules.md 2장, 11.2, 13장 V-14)
// - 시각은 기기 시간대 기준으로 만들어 어느 시간대에서 실행해도 같은 결과

import { test } from 'node:test';
import assert from 'node:assert/strict';

import {
  arriveBy,
  ceilMinutes,
  departureLine,
  expectedArrival,
  floorMinutes,
  parseClock,
} from '../../js/logic/departure.js';
import { MARGIN_SECONDS } from '../../js/logic/defaults.js';

// 2026-10-20 hh:mm:ss (월은 0부터이므로 10월은 9)
const at = (hours, minutes, seconds = 0) => new Date(2026, 9, 20, hours, minutes, seconds);

test('V-14 목표 09:00, 총 소요 52분 10초, 여유 10분이면 늦어도 07:57 출발', () => {
  const line = departureLine({
    now: at(7, 0),
    targetArrival: '09:00',
    totalSeconds: 52 * 60 + 10,
  });
  // 09:00:00 - 52:10 - 10:00 = 07:57:50 -> 분 단위 버림
  assert.deepEqual(line, { kind: 'leave_by', prefix: '늦어도', time: '07:57', suffix: '출발' });
});

test('여유 시간 기본값은 600초', () => {
  assert.equal(MARGIN_SECONDS, 600);
});

test('사용자가 바꾼 여유 시간 반영', () => {
  const line = departureLine({
    now: at(7, 0),
    targetArrival: '09:00',
    totalSeconds: 52 * 60 + 10,
    marginSeconds: 0,
  });
  // 09:00:00 - 52:10 = 08:07:50
  assert.equal(line.time, '08:07');
});

test('출발 시각과 지금이 같은 초이면 아직 지나지 않음', () => {
  const line = departureLine({ now: at(7, 57, 50), targetArrival: '09:00', totalSeconds: 3130 });
  assert.equal(line.kind, 'leave_by');
  assert.equal(line.time, '07:57');
});

test('출발 시각이 1초라도 지났으면 지금 출발하면 도착 시각', () => {
  const line = departureLine({ now: at(7, 57, 51), targetArrival: '09:00', totalSeconds: 3130 });
  // 07:57:51 + 52:10 = 08:50:01 -> 분 단위 올림
  assert.deepEqual(line, { kind: 'arrive_if_now', prefix: '지금 출발하면', time: '08:51', suffix: '도착' });
});

test('목표 도착 시각이 없으면 지금 출발하면 도착 시각', () => {
  const line = departureLine({ now: at(7, 52, 0), targetArrival: null, totalSeconds: 58 * 60 });
  assert.deepEqual(line, { kind: 'arrive_if_now', prefix: '지금 출발하면', time: '08:50', suffix: '도착' });
});

test('목표 도착 시각은 항상 오늘 기준. 이미 지난 목표는 다음 날로 넘기지 않음', () => {
  const line = departureLine({ now: at(22, 0), targetArrival: '09:00', totalSeconds: 3130 });
  assert.equal(line.kind, 'arrive_if_now');
  assert.equal(line.time, '22:53');
});

test('예상 도착 시각은 분 단위 올림, 0초이면 그 분', () => {
  assert.equal(expectedArrival(at(8, 0), 30 * 60), '08:30');
  assert.equal(expectedArrival(at(8, 0), 30 * 60 + 1), '08:31');
  assert.equal(expectedArrival(at(23, 50), 20 * 60), '00:10');
});

test('소요 시간은 분 단위 올림, 줄어드는 시간은 분 단위 버림', () => {
  assert.equal(ceilMinutes(3130), 53);
  assert.equal(ceilMinutes(3120), 52);
  assert.equal(floorMinutes(778), 12);
  assert.equal(floorMinutes(59), 0);
});

test('HH:MM 형식이 아니면 null', () => {
  assert.deepEqual(parseClock('09:05'), { hours: 9, minutes: 5 });
  assert.equal(parseClock('9:05'), null);
  assert.equal(parseClock('24:00'), null);
  assert.equal(parseClock(null), null);
});

test('기준 도착 시각은 목표 도착 시각 - 여유 시간, 기기 시간대 오프셋 포함', () => {
  const now = new Date(2026, 9, 20, 7, 30, 0);
  const text = arriveBy({ now, targetArrival: '09:00', marginSeconds: 600 });
  assert.match(text, /^2026-10-20T08:50:00[+-]\d{2}:\d{2}$/);
  assert.equal(new Date(text).getTime(), new Date(2026, 9, 20, 8, 50, 0).getTime());
});

test('목표 도착 시각이 없으면 기준 도착 시각도 없음', () => {
  assert.equal(arriveBy({ now: new Date(2026, 9, 20, 7, 30), targetArrival: null, marginSeconds: 600 }), null);
});
