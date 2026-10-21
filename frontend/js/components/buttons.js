// 버튼 (DESIGN.md 7.3)
// - 글자는 행동을 그대로 씀. 비활성은 disabled 속성으로 표시하고 색은 button-disabled

import { el } from './dom.js';
import { icon } from './icons.js';

function button(kind, typography, { label, onClick, disabled = false, block = false, type = 'button' }) {
  const classes = [kind, typography, 'pressable', block ? 'button-block' : ''].filter(Boolean).join(' ');
  return el('button', { type, class: classes, onclick: onClick, disabled, text: label });
}

// 화면의 주요 행동 (저장, 확인, 다시 시도)
export function buttonPrimary(options) {
  return button('button-primary', 't-link-lg', options);
}

// 보조 행동 (취소, 장소 삭제, 검색)
export function buttonGhost(options) {
  return button('button-ghost', 't-link', options);
}

// 카드 안의 작은 행동 (지도 보기)
export function buttonGhostSmall(options) {
  return button('button-ghost-sm', 't-link-sm', options);
}

// 되돌릴 수 없는 작업의 마지막 확인
export function buttonCaution(options) {
  return button('button-caution', 't-link-lg', options);
}

// 아이콘만 있는 원형 버튼. name은 화면 낭독기용 이름 (screens.md 3.4)
export function iconButton({ iconName, name, onClick, disabled = false }) {
  return el(
    'button',
    { type: 'button', class: 'icon-button pressable', 'aria-label': name, title: name, onclick: onClick, disabled },
    [icon(iconName)],
  );
}
