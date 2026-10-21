// 추천 카드 (DESIGN.md 7.2, screen-today.md 3, 4, 6장)
// - 카드 함수는 화면에 보일 값만 받음. 분 단위 계산과 문구 선택은 화면(pages/today.js)이 함

import { badgeCaution, badgeNeutral, badgeRank } from './badges.js';
import { buttonGhostSmall } from './buttons.js';
import { el, uid } from './dom.js';
import { icon } from './icons.js';

// 수단 색을 CSS 변수로 넘기는 style 값 (DESIGN.md 2.4). tone: { color, ink }
export function toneStyle(tone) {
  return `--mode-color: var(--colors-${tone.color}); --mode-ink: var(--colors-${tone.ink})`;
}

// 수단 구성. chips: [{ iconName, text, tone }]. 칩 사이에 '→'
export function modeChain(chips) {
  const items = [];
  chips.forEach((chip, index) => {
    if (index > 0) {
      items.push(el('li', { class: 't-link-sm', 'aria-hidden': 'true', text: '→' }));
    }
    items.push(
      el('li', { class: 'chip t-link-sm num', style: toneStyle(chip.tone) }, [icon(chip.iconName), chip.text]),
    );
  });
  return el('ol', { class: 'mode-chain' }, items);
}

// 대여소 행. kind 'rent'이면 도보 분, 자전거 대수(있을 때만)를 함께 표시
export function stationRow({ kind, name, walkMinutes = null, bikes = null }) {
  const label = kind === 'rent' ? '대여' : '반납';
  return el('div', { class: 'station-row t-link-sm num' }, [
    el('span', { class: 'station-name', text: `${label} · ${name}` }),
    walkMinutes === null ? null : el('span', { text: `도보 ${walkMinutes}분` }),
    bikes === null ? null : el('span', { text: `자전거 ${bikes}대` }),
  ]);
}

// 위치 문구 칩 (DESIGN.md 7.2, 권장 F-26)
export function positionChip(text) {
  return el('span', { class: 'position-chip t-link-sm num', text });
}

// 구간 하나의 세부 (권장 F-15, F-16 범례). row: { iconName, title, tone, lines, position }
// - 행 전체를 수단 색으로 칠함 (DESIGN.md 2.4, 7.2)
// - position이 있으면 위치 행: 노선 이름 옆에 위치 문구 칩
export function legRow({ iconName, title, tone, lines, position = null }) {
  const mark = iconName ? icon(iconName) : null;
  const head = el('span', { class: 'leg-title t-link-sm num' }, [
    mark,
    title,
    position ? positionChip(position) : null,
  ]);
  return el('li', { class: 'leg-row t-link-sm num', style: toneStyle(tone) }, [
    head,
    ...lines.map((text) => el('span', { class: 'leg-line', text })),
  ]);
}

export function legList(rows) {
  return el('ol', { class: 'leg-list' }, rows.map(legRow));
}

// 펼치기 (screen-today.md 6.1)
// - 카드 전체를 덮는 투명 버튼이 펼침, 접힘을 맡아 카드 아무 곳이나 누르면 동작함
// - 펼친 영역의 '지도 보기' 버튼은 투명 버튼 위에 있어 눌러도 접히지 않음
// detail: { key, label, expanded, rows, basis, onToggle, onMap }
// - basis: 실시간 위치 기준 시각 'HH:MM'. 있으면 구간 목록 아래 '위치는 HH:MM 기준' (권장 F-26)
function expandable(card, detail) {
  if (!detail) {
    return card;
  }
  const regionId = uid('legs');
  card.classList.add('expandable');
  card.prepend(
    el('button', {
      type: 'button',
      class: 'card-toggle pressable',
      'data-key': detail.key,
      'aria-label': detail.label,
      'aria-expanded': detail.expanded ? 'true' : 'false',
      'aria-controls': detail.expanded ? regionId : null,
      onclick: detail.onToggle,
    }),
  );
  if (detail.expanded) {
    card.append(
      el('div', { class: 'card-detail', id: regionId }, [
        legList(detail.rows),
        detail.basis
          ? el('p', { class: 't-link-sm ink-secondary num', text: `위치는 ${detail.basis} 기준` })
          : null,
        buttonGhostSmall({ label: '지도 보기', onClick: detail.onMap }),
      ]),
    );
  }
  return card;
}

// 출발 시각 줄: 앞말(body) + 숫자(display-md) + 뒷말(body)
function departureLine(departure) {
  return el('p', { class: 'departure-line' }, [
    el('span', { class: 't-body', text: departure.prefix }),
    el('span', { class: 't-display-md num', text: departure.time }),
    el('span', { class: 't-body', text: departure.suffix }),
  ]);
}

function cardProps(baseClass, skeleton) {
  return {
    class: `${baseClass}${skeleton ? ' skeleton' : ''}`,
    'aria-hidden': skeleton ? 'true' : null,
  };
}

// 기본 경로 카드. arrivalText가 null이면 예상 도착을 생략
export function bestRouteCard({
  departure,
  durationText,
  arrivalText,
  chips,
  reason,
  savingText,
  serviceUnknown = false,
  detail = null,
  skeleton = false,
}) {
  const card = el('article', cardProps('best-route-card', skeleton), [
    badgeRank('기본 경로'),
    departureLine(departure),
    el('p', { class: 'duration-line' }, [
      el('span', { class: 't-heading-sm num', text: durationText }),
      arrivalText ? el('span', { class: 't-body-lg num', text: arrivalText }) : null,
    ]),
    modeChain(chips),
    el('p', { class: 't-body', text: reason }),
    savingText ? badgeNeutral(savingText) : null,
    serviceUnknown ? badgeCaution('운행 시간 정보가 없습니다') : null,
  ]);
  return expandable(card, detail);
}

// 다른 경로 카드
export function routeCard({
  label,
  durationText,
  diffText,
  departureText,
  chips,
  reason,
  stations = [],
  stockUnknown = false,
  pmNote = false,
  serviceUnknown = false,
  detail = null,
  skeleton = false,
}) {
  const card = el('article', cardProps('route-card', skeleton), [
    badgeRank(label),
    el('p', { class: 'duration-line' }, [
      el('span', { class: 't-body-lg num', text: durationText }),
      diffText ? badgeNeutral(diffText) : null,
    ]),
    el('p', { class: 't-link num', text: departureText }),
    modeChain(chips),
    reason ? el('p', { class: 't-link-sm ink-secondary', text: reason }) : null,
    stations.length ? el('div', { class: 'station-list' }, stations.map(stationRow)) : null,
    stockUnknown ? badgeCaution('재고 정보가 없습니다') : null,
    pmNote ? el('p', { class: 't-link-sm ink-secondary', text: '대여, 반납 시간과 재고는 반영하지 않았습니다' }) : null,
    serviceUnknown ? badgeCaution('운행 시간 정보가 없습니다') : null,
  ]);
  return expandable(card, detail);
}
