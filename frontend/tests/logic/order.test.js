// 표시 순서, 기본 경로와의 차이 테스트 (rules.md 8장, 13장 V-12, V-16)

import { test } from 'node:test';
import assert from 'node:assert/strict';

import { compareWithBase, orderRoutes } from '../../js/logic/order.js';
import { sampleBusOnly, sampleResponse } from './fixtures.js';

const keys = (ordered) => ordered.map((item) => item.key);

test('V-12 따릉이 포함 50분, 버스 전용 48분, PM 전용 61분이면 기본, 버스 전용, 따릉이 포함, PM 전용', () => {
  const response = sampleResponse();
  response.bikeMix.totalSeconds = 50 * 60;
  response.busOnly = sampleBusOnly(48 * 60);
  response.pmOnly.totalSeconds = 61 * 60;

  assert.deepEqual(keys(orderRoutes(response)), ['base', 'busOnly', 'bikeMix', 'pmOnly']);
});

test('V-16 세 경로 모두 50분이면 버스 전용, 따릉이 포함, PM 전용 순', () => {
  const response = sampleResponse();
  response.bikeMix.totalSeconds = 50 * 60;
  response.busOnly = sampleBusOnly(50 * 60);
  response.pmOnly.totalSeconds = 50 * 60;

  assert.deepEqual(keys(orderRoutes(response)), ['base', 'busOnly', 'bikeMix', 'pmOnly']);
});

test('기본 경로는 다른 경로보다 느려도 맨 위', () => {
  const response = sampleResponse();
  // 응답 예: 기본 1560초, 따릉이 포함 1110초, PM 전용 780초
  assert.deepEqual(keys(orderRoutes(response)), ['base', 'pmOnly', 'bikeMix']);
});

test('순서는 분이 아닌 초 단위로 비교', () => {
  const response = sampleResponse();
  // 둘 다 화면에는 50분이지만 PM 전용이 1초 빠름
  response.bikeMix.totalSeconds = 49 * 60 + 2;
  response.pmOnly.totalSeconds = 49 * 60 + 1;

  assert.deepEqual(keys(orderRoutes(response)), ['base', 'pmOnly', 'bikeMix']);
});

test('응답에 없는 경로(null)는 카드에서 빠짐', () => {
  const response = sampleResponse();
  response.bikeMix = null;

  assert.deepEqual(keys(orderRoutes(response)), ['base', 'pmOnly']);
});

test('기본 경로가 없으면 차이 없이 PM 전용만', () => {
  const response = sampleResponse();
  response.transit.status = 'no_result';
  response.base = null;
  response.bikeMix = null;

  const ordered = orderRoutes(response);
  assert.deepEqual(keys(ordered), ['pmOnly']);
  assert.equal(ordered[0].diff, null);
});

test('차이는 카드에 보이는 분(올림)끼리 계산: 빠름', () => {
  // 1560초 -> 26분, 1110초 -> 19분
  const diff = compareWithBase({ totalSeconds: 1560 }, { totalSeconds: 1110 });
  assert.deepEqual(diff, { kind: 'faster', minutes: 7, text: '기본 경로보다 7분 빠릅니다' });
});

test('차이는 카드에 보이는 분(올림)끼리 계산: 느림', () => {
  // 1560초 -> 26분, 1700초 -> 29분
  const diff = compareWithBase({ totalSeconds: 1560 }, { totalSeconds: 1700 });
  assert.deepEqual(diff, { kind: 'slower', minutes: 3, text: '기본 경로보다 3분 느립니다' });
});

test('카드에 같은 분으로 보이면 초 단위로 달라도 표시하지 않음', () => {
  assert.equal(compareWithBase({ totalSeconds: 1560 }, { totalSeconds: 1560 }), null);
  // 1561초, 1562초 -> 둘 다 27분
  assert.equal(compareWithBase({ totalSeconds: 1561 }, { totalSeconds: 1562 }), null);
  // 1560초 -> 26분, 1501초 -> 26분
  assert.equal(compareWithBase({ totalSeconds: 1560 }, { totalSeconds: 1501 }), null);
});

test('보이는 분의 차이를 그대로 표시', () => {
  // 1561초 -> 27분, 1500초 -> 25분: 2분 빠름
  const diff = compareWithBase({ totalSeconds: 1561 }, { totalSeconds: 1500 });
  assert.equal(diff.text, '기본 경로보다 2분 빠릅니다');
});

test('카드마다 기본 경로와의 차이를 붙임', () => {
  const response = sampleResponse();
  const ordered = orderRoutes(response);

  assert.equal(ordered[0].diff, null);
  assert.equal(ordered[1].diff.text, '기본 경로보다 13분 빠릅니다');
  assert.equal(ordered[2].diff.text, '기본 경로보다 7분 빠릅니다');
});
