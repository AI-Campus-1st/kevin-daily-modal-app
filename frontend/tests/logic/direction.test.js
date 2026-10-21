// 출근, 퇴근 전환 테스트 (rules.md 9장, 13장 V-15)

import { test } from 'node:test';
import assert from 'node:assert/strict';

import {
  autoDirection,
  currentDirection,
  nextBoundary,
  routeEnds,
  switchDirection,
} from '../../js/logic/direction.js';

// 2026-10-20 hh:mm:ss (기기 시간대 기준)
const at = (hours, minutes, seconds = 0, day = 20) => new Date(2026, 9, day, hours, minutes, seconds);

test('V-15 모드 출근/퇴근, 13:59에 열면 출근, 14:00에 열면 퇴근', () => {
  assert.equal(autoDirection(at(13, 59), 'commute_return'), 'commute');
  assert.equal(autoDirection(at(14, 0), 'commute_return'), 'return');
});

test('13:59:59까지는 기준 시각 전', () => {
  assert.equal(autoDirection(at(13, 59, 59), 'commute_return'), 'commute');
});

test('모드 퇴근/출근은 반대', () => {
  assert.equal(autoDirection(at(13, 59), 'return_commute'), 'return');
  assert.equal(autoDirection(at(14, 0), 'return_commute'), 'commute');
});

test('모드 기본값은 출근/퇴근', () => {
  assert.equal(autoDirection(at(8, 0)), 'commute');
});

test('다음 경계는 기준 시각 전이면 오늘 14:00, 이후면 다음 날 자정', () => {
  assert.equal(nextBoundary(at(9, 30)).getTime(), at(14, 0).getTime());
  assert.equal(nextBoundary(at(14, 0)).getTime(), at(0, 0, 0, 21).getTime());
  assert.equal(nextBoundary(at(23, 59)).getTime(), at(0, 0, 0, 21).getTime());
});

test('오전에 퇴근으로 전환하면 14:00 전까지 퇴근 유지', () => {
  const manual = switchDirection({ now: at(8, 0), mode: 'commute_return', manual: null });
  assert.deepEqual(manual, { direction: 'return', until: at(14, 0).toISOString() });

  assert.equal(currentDirection({ now: at(13, 59), mode: 'commute_return', manual }), 'return');
  // 14:00부터는 유지가 끝나고 자동 방향(퇴근)
  assert.equal(currentDirection({ now: at(14, 0), mode: 'commute_return', manual }), 'return');
});

test('오후에 출근으로 전환하면 자정 전까지 출근 유지, 자정 이후 자동 방향', () => {
  const manual = switchDirection({ now: at(18, 0), mode: 'commute_return', manual: null });
  assert.deepEqual(manual, { direction: 'commute', until: at(0, 0, 0, 21).toISOString() });

  assert.equal(currentDirection({ now: at(23, 59), mode: 'commute_return', manual }), 'commute');
  // 다음 날 오전 자동 방향도 출근이므로 결과는 같음
  assert.equal(currentDirection({ now: at(0, 0, 0, 21), mode: 'commute_return', manual }), 'commute');
  // 다음 날 오후에는 자동 방향 퇴근
  assert.equal(currentDirection({ now: at(15, 0, 0, 21), mode: 'commute_return', manual }), 'return');
});

test('유지 종료 시각이 지난 수동 전환은 무시', () => {
  const manual = { direction: 'return', until: at(14, 0, 0, 19).toISOString() };
  assert.equal(currentDirection({ now: at(9, 0), mode: 'commute_return', manual }), 'commute');
});

test('수동 전환 중 다시 전환해 자동 방향으로 돌아오면 수동 전환 상태 없음', () => {
  const manual = switchDirection({ now: at(8, 0), mode: 'commute_return', manual: null });
  const back = switchDirection({ now: at(8, 5), mode: 'commute_return', manual });
  assert.equal(back, null);
  assert.equal(currentDirection({ now: at(8, 5), mode: 'commute_return', manual: back }), 'commute');
});

test('출근은 출발지 -> 도착지, 퇴근은 도착지 -> 출발지', () => {
  const places = { origin: { name: '집' }, destination: { name: '회사' } };
  assert.deepEqual(routeEnds('commute', places), { from: places.origin, to: places.destination });
  assert.deepEqual(routeEnds('return', places), { from: places.destination, to: places.origin });
});
