// 출근, 퇴근 전환 (rules.md 9장)
// - 방향: 'commute'(출근, 출발지 -> 도착지), 'return'(퇴근, 도착지 -> 출발지)
// - 모드: 'commute_return'(기준 시각 전 출근, 이후 퇴근), 'return_commute'(그 반대)
// - 수동 전환 상태(manualDirection): { direction, until }. until은 유지 종료 시각의 ISO 8601 문자열
// - 지금 시각, 저장 값은 모두 인자로 받음

import { DIRECTION_SWITCH_TIME } from './defaults.js';
import { clockOnDate } from './departure.js';

const MODE_DIRECTIONS = {
  commute_return: { before: 'commute', after: 'return' },
  return_commute: { before: 'return', after: 'commute' },
};

// 반대 방향
export function oppositeDirection(direction) {
  return direction === 'commute' ? 'return' : 'commute';
}

// 지금 시각과 모드로 정한 방향. 기준 시각 정각부터 뒤 방향 (V-15)
export function autoDirection(now, mode = 'commute_return', switchTime = DIRECTION_SWITCH_TIME) {
  const directions = MODE_DIRECTIONS[mode] ?? MODE_DIRECTIONS.commute_return;
  const switchDate = clockOnDate(now, switchTime);
  return now.getTime() < switchDate.getTime() ? directions.before : directions.after;
}

// 지금 이후 처음 오는 기준 시각 경계 (오늘 기준 시각 또는 다음 날 자정)
export function nextBoundary(now, switchTime = DIRECTION_SWITCH_TIME) {
  const switchDate = clockOnDate(now, switchTime);
  if (now.getTime() < switchDate.getTime()) {
    return switchDate;
  }
  const midnight = new Date(now.getTime());
  midnight.setHours(24, 0, 0, 0);
  return midnight;
}

// 지금 보여 줄 방향. 수동 전환이 유지 중이면 그 방향, 아니면 자동 방향
export function currentDirection({ now, mode, manual = null, switchTime = DIRECTION_SWITCH_TIME }) {
  if (manual && now.getTime() < new Date(manual.until).getTime()) {
    return manual.direction;
  }
  return autoDirection(now, mode, switchTime);
}

// 반대 방향으로 전환했을 때 저장할 수동 전환 상태
// - 다음 기준 시각 경계까지 유지
// - 전환한 방향이 자동 방향과 같으면 수동 전환이 필요 없으므로 null
export function switchDirection({ now, mode, manual = null, switchTime = DIRECTION_SWITCH_TIME }) {
  const next = oppositeDirection(currentDirection({ now, mode, manual, switchTime }));
  if (next === autoDirection(now, mode, switchTime)) {
    return null;
  }
  return { direction: next, until: nextBoundary(now, switchTime).toISOString() };
}

// 방향에 맞춘 출발 장소, 도착 장소 (api_spec.md 4.1 요청 순서, screen-today.md 2장 머리 영역)
export function routeEnds(direction, places) {
  if (direction === 'return') {
    return { from: places.destination, to: places.origin };
  }
  return { from: places.origin, to: places.destination };
}
