// 추천 이유 테스트 (rules.md 11.1)

import { test } from 'node:test';
import assert from 'node:assert/strict';

import { routeReason } from '../../js/logic/reason.js';
import { sampleBikeLeg, sampleBusOnly, sampleResponse } from './fixtures.js';

test('기본 경로는 환승 횟수', () => {
  const response = sampleResponse();
  assert.equal(routeReason('base', response.base), '환승이 없습니다');

  response.base.transfers = 1;
  assert.equal(routeReason('base', response.base), '환승 1회');
});

test('버스 전용은 지하철 없이 이동, 환승 횟수', () => {
  assert.equal(routeReason('busOnly', sampleBusOnly(2880)), '지하철 없이 이동합니다, 환승 1회');
});

test('PM 전용은 자전거 길 거리, 100m 단위 반올림', () => {
  const response = sampleResponse();
  assert.equal(routeReason('pmOnly', response.pmOnly), '자전거 길 3.4km');

  assert.equal(routeReason('pmOnly', { totalSeconds: 780, totalDistance: 3450 }), '자전거 길 3.5km');
  assert.equal(routeReason('pmOnly', { totalSeconds: 780, totalDistance: 3449 }), '자전거 길 3.4km');
  assert.equal(routeReason('pmOnly', { totalSeconds: 780, totalDistance: 12000 }), '자전거 길 12.0km');
});

test('전 구간 따릉이는 따릉이로만 N분(올림), 대여소 자전거 대수', () => {
  const response = sampleResponse();
  // 1110초 = 18분 30초 -> 19분
  assert.equal(routeReason('bikeMix', response.bikeMix), '따릉이로만 19분, 대여소 자전거 2대');
});

test('재고를 확인하지 못했으면 재고 정보가 없습니다', () => {
  const response = sampleResponse();
  response.bikeMix.stockKnown = false;
  response.bikeMix.legs[0].rentStation.availableBikes = null;
  assert.equal(routeReason('bikeMix', response.bikeMix), '따릉이로만 19분, 재고 정보가 없습니다');
});

function firstLastMix(bikeLegs) {
  return {
    kind: 'first_last',
    conditions: { first: true, second: true, third: null },
    totalSeconds: 2400,
    transfers: 0,
    stockKnown: true,
    legs: bikeLegs,
  };
}

test('First mile만 바꾸면 바꾼 mile, 대여소 자전거 대수', () => {
  const mix = firstLastMix([
    sampleBikeLeg({ mile: 'first', seconds: 8 * 60, replacedSeconds: 22 * 60 }),
  ]);
  assert.equal(routeReason('bikeMix', mix), '첫 역까지 22분 → 따릉이 8분, 대여소 자전거 3대');
});

test('Last mile만 바꾸면 마지막 역에서 문구, 시간은 분 단위 올림', () => {
  const mix = firstLastMix([
    sampleBikeLeg({ mile: 'last', seconds: 4 * 60 + 1, replacedSeconds: 11 * 60 + 30 }),
  ]);
  assert.equal(routeReason('bikeMix', mix), '마지막 역에서 12분 → 따릉이 5분, 대여소 자전거 3대');
});

test('두 mile을 모두 바꾸면 두 mile 문구만', () => {
  const mix = firstLastMix([
    sampleBikeLeg({ mile: 'first', seconds: 8 * 60, replacedSeconds: 22 * 60 }),
    sampleBikeLeg({ mile: 'last', seconds: 5 * 60, replacedSeconds: 12 * 60 }),
  ]);
  assert.equal(routeReason('bikeMix', mix), '첫 역까지 22분 → 따릉이 8분, 마지막 역에서 12분 → 따릉이 5분');
});
