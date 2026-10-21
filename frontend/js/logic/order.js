// 표시 순서와 기본 경로와의 차이 (rules.md 8장)
// - 입력은 /api/recommend 응답 (api_spec.md 4장)
// - 순서 비교는 분으로 바꾸기 전 초 단위 값으로 함 (rules.md 2장)

import { ceilMinutes } from './departure.js';

// 기본 경로가 아닌 경로의 키. 배열 순서가 총 소요 시간이 같을 때의 순서
const OTHER_KEYS = ['busOnly', 'bikeMix', 'pmOnly'];

// 기본 경로와의 총 소요 시간 차이
// - 카드에 보이는 소요 시간(분 단위 올림)끼리의 차이 (2026-10-20 사용자 결정)
// - 분 단위 차이가 0이거나 기본 경로가 없으면 null
export function compareWithBase(base, route) {
  if (!base) {
    return null;
  }
  const diffMinutes = ceilMinutes(route.totalSeconds) - ceilMinutes(base.totalSeconds);
  if (diffMinutes === 0) {
    return null;
  }
  if (diffMinutes < 0) {
    const minutes = -diffMinutes;
    return { kind: 'faster', minutes, text: `기본 경로보다 ${minutes}분 빠릅니다` };
  }
  return { kind: 'slower', minutes: diffMinutes, text: `기본 경로보다 ${diffMinutes}분 느립니다` };
}

// 화면에 보일 카드 순서
// - 기본 경로가 있으면 맨 위, 나머지는 응답에 있는 것만 총 소요 시간이 짧은 순
// - 반환: [{ key, route, diff }]. 기본 경로의 diff는 null
export function orderRoutes(response) {
  const ordered = [];
  if (response.base) {
    ordered.push({ key: 'base', route: response.base, diff: null });
  }
  const others = OTHER_KEYS
    .filter((key) => response[key])
    .map((key) => ({ key, route: response[key], diff: compareWithBase(response.base, response[key]) }));
  others.sort((a, b) => {
    const bySeconds = a.route.totalSeconds - b.route.totalSeconds;
    if (bySeconds !== 0) {
      return bySeconds;
    }
    return OTHER_KEYS.indexOf(a.key) - OTHER_KEYS.indexOf(b.key);
  });
  return ordered.concat(others);
}
