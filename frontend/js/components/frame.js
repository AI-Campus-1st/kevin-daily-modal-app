// 화면 틀 (DESIGN.md 7.1)

import { iconButton } from './buttons.js';
import { el } from './dom.js';

// 오늘의 추천 외 화면의 머리. 뒤로 가기 버튼과 화면 제목
export function topBar({ title, onBack }) {
  return el('header', { class: 'top-bar' }, [
    iconButton({ iconName: 'back', name: '뒤로 가기', onClick: onBack }),
    el('h1', { class: 't-heading-sm', text: title }),
  ]);
}

// 출근, 퇴근 두 칸 전환. 지금 방향만 선택 표시 (primary)
export function directionToggle({ direction, onSelect }) {
  const choices = [
    ['commute', '출근'],
    ['return', '퇴근'],
  ];
  return el(
    'div',
    { class: 'direction-toggle' },
    choices.map(([value, label]) =>
      el('button', {
        type: 'button',
        class: 't-link pressable',
        'aria-pressed': value === direction ? 'true' : 'false',
        text: label,
        onclick: () => {
          if (value !== direction) {
            onSelect(value);
          }
        },
      }),
    ),
  );
}

// 오늘의 추천 머리 영역 (screen-today.md 2장)
export function headerGradient({ title, direction, targetText, loading, onRefresh, onSettings, onToggle }) {
  return el('header', { class: 'header-gradient' }, [
    el('div', { class: 'header-row' }, [
      el('h1', { class: 't-heading-sm header-title', text: title }),
      iconButton({ iconName: 'refresh', name: '새로고침', onClick: onRefresh, disabled: loading }),
      iconButton({ iconName: 'settings', name: '설정', onClick: onSettings }),
    ]),
    directionToggle({ direction, onSelect: onToggle }),
    el('p', { class: 't-heading-sm num', text: targetText }),
  ]);
}
