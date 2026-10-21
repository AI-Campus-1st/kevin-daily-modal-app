// SC-04 경로 지도 (screen-map.md, 권장 F-16)
// - 새로 조회하지 않고 SC-01이 마지막으로 보여 준 응답에서 경로를 꺼냄
// - 받은 응답이 없거나 그 경로가 없으면 #today로 바꿈

import { badgeNeutral, badgeRank } from '../components/badges.js';
import { legList, toneStyle } from '../components/cards.js';
import { el } from '../components/dom.js';
import { topBar } from '../components/frame.js';
import { emptyState } from '../components/overlay.js';
import { legRows, mapShapes } from '../logic/legs.js';
import { loadMapSdk } from '../map-sdk.js';
import { shownRoute } from './today.js';

const TITLES = { base: '기본 경로', bikeMix: '따릉이 포함', busOnly: '버스 전용', pmOnly: 'PM 전용' };
const MARKER_TEXT = { origin: '출발', destination: '도착', rent: '대여', return: '반납' };
const LINE_WEIGHT = 5; // 카카오 지도 단위 px (screen-map.md 2장)

let renderCount = 0;

// 선 색은 수단 색 토큰의 CSS 변수 값을 읽어 씀 (DESIGN.md 2.4, 7.7)
function tokenColor(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(`--colors-${name}`).trim();
}

// 환승 지점 원 (DESIGN.md 7.7). 테두리는 환승 뒤 수단 색
function transferPoint(tone) {
  return el('div', { class: 'transfer-point', style: toneStyle(tone) });
}

function markerContent(kind) {
  const text = MARKER_TEXT[kind];
  return kind === 'origin' || kind === 'destination' ? badgeNeutral(text) : badgeRank(text);
}

function drawMap(maps, canvas, shapes) {
  const first = shapes.markers[0];
  const map = new maps.Map(canvas, { center: new maps.LatLng(first.y, first.x), level: 5 });
  const bounds = new maps.LatLngBounds();
  for (const line of shapes.lines) {
    const path = line.points.map(([x, y]) => new maps.LatLng(y, x));
    path.forEach((point) => bounds.extend(point));
    new maps.Polyline({
      map,
      path,
      strokeWeight: LINE_WEIGHT,
      strokeColor: tokenColor(line.tone.color),
      strokeOpacity: 1,
      strokeStyle: line.dash,
    });
  }
  // 환승 지점은 선 위, 출발, 도착, 대여소 표시 아래
  for (const point of shapes.transfers) {
    const position = new maps.LatLng(point.y, point.x);
    new maps.CustomOverlay({ map, position, content: transferPoint(point.tone), zIndex: 1 });
  }
  for (const marker of shapes.markers) {
    const position = new maps.LatLng(marker.y, marker.x);
    bounds.extend(position);
    new maps.CustomOverlay({ map, position, content: markerContent(marker.kind), yAnchor: 1, zIndex: 2 });
  }
  map.setBounds(bounds);
}

export function render(root, nav, key) {
  renderCount += 1;
  const id = renderCount;
  const shown = shownRoute(key);
  if (!shown) {
    nav.up('#today');
    return;
  }
  const { route, from, to } = shown;
  const frame = el('div', { class: 'map-frame' }, [el('div', { class: 'map-canvas', 'aria-hidden': 'true' })]);
  const slot = el('div', { class: 'map-slot' }, [frame]);
  root.replaceChildren(
    el('div', { class: 'page map-page' }, [
      topBar({ title: TITLES[key], onBack: () => nav.up('#today') }),
      el('div', { class: 'map-content' }, [slot, legList(legRows(key, route, new Date()))]),
    ]),
  );

  loadMapSdk().then((maps) => {
    if (id !== renderCount) {
      return;
    }
    if (!maps) {
      slot.replaceChildren(emptyState({ caption: '지도를 불러오지 못했습니다' }));
      return;
    }
    drawMap(maps, frame.firstChild, mapShapes(key, route, from, to));
  });
}

export function leave() {
  renderCount += 1; // 떠난 뒤 불러온 지도는 그리지 않음
}
