// 입력과 목록 (DESIGN.md 7.5)

import { el } from './dom.js';
import { icon } from './icons.js';

// 목록 행. 첫 줄(body), 둘째 줄부터(link-sm, ink-secondary), 오른쪽 값, 선택 표시
// - subtitle은 문자열 하나 또는 여러 줄의 배열. 빈 값은 뺌
// - onClick이 없으면 누를 수 없는 행(div)
export function listRow({ title, subtitle = null, value = null, selected = false, onClick = null }) {
  const children = [
    el('span', { class: 'row-text' }, [
      el('span', { class: 't-body', text: title }),
      ...[].concat(subtitle ?? []).filter(Boolean).map((text) => el('span', { class: 't-link-sm ink-secondary', text })),
    ]),
    value ? el('span', { class: 'row-value t-body num', text: value }) : null,
    selected ? icon('check') : null,
    selected ? el('span', { class: 'sr-only', text: '선택되었습니다' }) : null,
  ];
  if (!onClick) {
    return el('div', { class: 'list-row' }, children);
  }
  return el('button', { type: 'button', class: 'list-row pressable', onclick: onClick }, children);
}

// 입력 칸
export function textInput(props) {
  return el('input', { type: 'text', class: 'text-input t-body', ...props });
}
