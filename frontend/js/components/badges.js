// 배지 (DESIGN.md 7.4)

import { el } from './dom.js';
import { icon } from './icons.js';

// 경로 종류 ("기본 경로", "따릉이 포함", "버스 전용", "PM 전용")
export function badgeRank(text) {
  return el('span', { class: 'badge-rank t-link-sm', text });
}

// 주의 상태 ("재고 정보가 없습니다"). 색만으로 구분하지 않도록 아이콘과 글자를 함께 둠
export function badgeCaution(text) {
  return el('span', { class: 'badge-caution t-link-sm' }, [icon('caution'), text]);
}

// 정보 상태, 비교 ("기본 경로보다 6분 빠릅니다", "N분 전 정보")
export function badgeNeutral(text, extraClass = '') {
  return el('span', { class: `badge-neutral t-link-sm num ${extraClass}`.trim(), text });
}
