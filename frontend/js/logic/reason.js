// 추천 이유 (rules.md 11.1)
// - 카드마다 한 줄. 경로 종류별 문구를 최대 2개까지 쉼표로 이음
// - 기본 경로의 PM 절감 시간은 이유에 넣지 않음 (rules.md 4장, 카드 옆에 따로 표시)

import { ceilMinutes } from './departure.js';

const MAX_PHRASES = 2;

// 환승 횟수 문구
export function transfersText(transfers) {
  return transfers === 0 ? '환승이 없습니다' : `환승 ${transfers}회`;
}

// 따릉이 구간 하나의 바꾼 mile 문구. 원래 mile 시간과 따릉이 구간 시간 모두 소요 시간이므로 분 단위 올림
function mileText(leg) {
  const before = ceilMinutes(leg.replacedSeconds);
  const after = ceilMinutes(leg.seconds);
  if (leg.mile === 'first') {
    return `첫 역까지 ${before}분 → 따릉이 ${after}분`;
  }
  return `마지막 역에서 ${before}분 → 따릉이 ${after}분`;
}

// 대여 가능 대수 문구. 재고를 확인하지 못했으면 '재고 정보가 없습니다' (rules.md 10장)
function stockText(bikeMix, leg) {
  const bikes = leg.rentStation?.availableBikes;
  if (!bikeMix.stockKnown || bikes === null || bikes === undefined) {
    return '재고 정보가 없습니다';
  }
  return `대여소 자전거 ${bikes}대`;
}

// 경로 종류별 문구 목록
export function reasonPhrases(key, route) {
  if (key === 'base') {
    return [transfersText(route.transfers)];
  }
  if (key === 'busOnly') {
    return ['지하철 없이 이동합니다', transfersText(route.transfers)];
  }
  if (key === 'pmOnly') {
    // 100m 단위 반올림 (2026-10-20 사용자 결정)
    const km = (Math.round(route.totalDistance / 100) / 10).toFixed(1);
    return [`자전거 길 ${km}km`];
  }
  if (key === 'bikeMix') {
    const bikeLegs = route.legs.filter((leg) => leg.type === 'bike');
    if (route.kind === 'full') {
      return [`따릉이로만 ${ceilMinutes(route.totalSeconds)}분`, stockText(route, bikeLegs[0])];
    }
    // 두 mile을 모두 바꿨으면 두 mile 문구만 표시 (2026-10-20 사용자 결정)
    const phrases = bikeLegs.map(mileText);
    if (phrases.length < MAX_PHRASES) {
      phrases.push(stockText(route, bikeLegs[0]));
    }
    return phrases;
  }
  return [];
}

// 카드에 보일 한 줄
export function routeReason(key, route) {
  return reasonPhrases(key, route).slice(0, MAX_PHRASES).join(', ');
}
