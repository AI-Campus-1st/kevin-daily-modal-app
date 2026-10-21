// SC-01 오늘의 추천 (screen-today.md)
// - 화면을 열 때, 새로고침, 출근 퇴근 전환 때 조회. 1분마다 시각 표시만 다시 계산
// - 받은 결과는 화면 메모리에만 둠 (rules.md 10장). 방향과 두 장소 좌표별로 마지막 결과를 기억

import { recommend } from '../api.js';
import { badgeNeutral } from '../components/badges.js';
import { bestRouteCard, routeCard } from '../components/cards.js';
import { el } from '../components/dom.js';
import { headerGradient } from '../components/frame.js';
import { emptyState, toast } from '../components/overlay.js';
import { arriveBy, ceilMinutes, departureLine, expectedArrival, floorMinutes } from '../logic/departure.js';
import { legRows, liveBasis } from '../logic/legs.js';
import { BIKE_TONE, PM_TONE, WALK_TONE, legTone } from '../logic/modes.js';
import { currentDirection, routeEnds, switchDirection } from '../logic/direction.js';
import { orderRoutes } from '../logic/order.js';
import { routeReason } from '../logic/reason.js';
import { loadPlaces, loadSettings, saveSettings } from '../storage.js';

const LABELS = { base: '기본 경로', bikeMix: '따릉이 포함', busOnly: '버스 전용', pmOnly: 'PM 전용' };
const MINUTE_MS = 60 * 1000;

const results = new Map(); // 조회 열쇠 → 마지막으로 받은 응답
let view = null; // { key, from, to, direction, loading, response, stale, expanded }
let shown = null; // 마지막으로 화면에 그린 응답과 좌표. SC-04 경로 지도가 씀
let root = null;
let nav = null;
let timer = null;
let requestCount = 0;

// SC-04가 쓸 경로 하나 (screen-map.md 3장). 없으면 null
export function shownRoute(key) {
  const route = shown?.response?.[key];
  if (!route) {
    return null;
  }
  return { route, from: shown.from, to: shown.to };
}

function resultKey(direction, from, to) {
  return `${direction}|${from.x},${from.y}|${to.x},${to.y}`;
}

// 지금 방향. 유지 기간이 지난 수동 전환은 저장소에서 지움
function directionNow(now) {
  const settings = loadSettings();
  const direction = currentDirection({ now, mode: settings.directionMode, manual: settings.manualDirection });
  if (settings.manualDirection && now.getTime() >= new Date(settings.manualDirection.until).getTime()) {
    settings.manualDirection = null;
    saveSettings(settings);
  }
  return { direction, settings };
}

export function render(rootNode, navigator) {
  root = rootNode;
  nav = navigator;
  const places = loadPlaces();
  if (!places.origin || !places.destination) {
    view = null;
    root.replaceChildren(
      el('div', { class: 'page today-page' }, [
        emptyState({
          caption: '출발지와 도착지를 등록하면 오늘의 추천을 보여 드립니다',
          actionLabel: '장소 등록',
          onAction: () => nav.go('#settings'),
        }),
      ]),
    );
    return;
  }
  const now = new Date();
  const { direction } = directionNow(now);
  const { from, to } = routeEnds(direction, places);
  const key = resultKey(direction, from, to);
  const previous = results.get(key) ?? null;
  view = { key, from, to, direction, loading: false, response: previous, stale: false, expanded: new Set() };
  draw();
  scheduleTick();
  load();
}

export function leave() {
  clearTimeout(timer);
  timer = null;
  view = null;
  requestCount += 1; // 떠난 뒤 도착한 응답은 버림
}

// 조회. 실패하면 같은 방향의 이전 결과를 유지하고 "N분 전 정보"를 표시
async function load() {
  if (!view) {
    return;
  }
  requestCount += 1;
  const id = requestCount;
  const { key, from, to, direction } = view;
  view.loading = true;
  view.expanded.clear(); // 새로고침하면 모두 접힘 (screen-today.md 6.1)
  draw();
  const settings = loadSettings();
  const limit = arriveBy({
    now: new Date(),
    targetArrival: settings.targetArrival[direction],
    marginSeconds: settings.marginSeconds,
  });
  const response = await recommend(from, to, limit);
  if (id !== requestCount || !view) {
    return;
  }
  view.loading = false;
  const status = response?.transit?.status;
  if (status === 'ok' || status === 'no_result' || status === 'out_of_service') {
    results.set(key, response);
    view.response = response;
    view.stale = false;
  } else if (results.has(key)) {
    view.response = results.get(key);
    view.stale = true;
    toast('경로를 불러오지 못했습니다');
  } else {
    // 이전 결과 없음: 경로 없음과 같은 표시. PM 전용 경로가 있으면 표시
    view.response = response ?? { transit: { status: 'unavailable' }, base: null, pmOnly: null };
    view.stale = false;
  }
  draw();
}

function onToggle() {
  const now = new Date();
  const settings = loadSettings();
  settings.manualDirection = switchDirection({
    now,
    mode: settings.directionMode,
    manual: settings.manualDirection,
  });
  saveSettings(settings);
  render(root, nav);
}

// 1분마다 시각 표시(출발 시각 줄, 예상 도착, N분 전)만 다시 계산 (screen-today.md 7장)
function scheduleTick() {
  clearTimeout(timer);
  const wait = MINUTE_MS - (Date.now() % MINUTE_MS);
  timer = setTimeout(() => {
    if (view) {
      draw();
      scheduleTick();
    }
  }, wait);
}

// 수단 구성 칩 (screen-today.md 6장). 칩마다 수단 색 (DESIGN.md 2.4)
function chipsFor(key, route) {
  if (key === 'pmOnly') {
    return [{ iconName: 'bike', text: `자전거 ${ceilMinutes(route.totalSeconds)}분`, tone: PM_TONE }];
  }
  const chips = [];
  for (const leg of route.legs) {
    if (leg.type === 'walk') {
      if (leg.edge) {
        chips.push({ iconName: 'walk', text: `도보 ${ceilMinutes(leg.seconds)}분`, tone: WALK_TONE });
      }
    } else if (leg.type === 'bus' || leg.type === 'subway') {
      chips.push({ iconName: leg.type, text: leg.vehicles[0]?.name ?? '', tone: legTone(leg) });
    } else if (leg.type === 'bike') {
      chips.push({ iconName: 'bike', text: `따릉이 ${ceilMinutes(leg.seconds)}분`, tone: BIKE_TONE });
    }
  }
  return chips;
}

// 대여소 행 (screen-today.md 4.1). 따릉이 구간마다 대여, 반납 두 행
function stationsFor(route) {
  const rows = [];
  for (const leg of route.legs.filter((item) => item.type === 'bike')) {
    rows.push({
      kind: 'rent',
      name: leg.rentStation.name,
      walkMinutes: ceilMinutes(leg.toStationSeconds),
      bikes: leg.rentStation.availableBikes ?? null,
    });
    rows.push({ kind: 'return', name: leg.returnStation.name });
  }
  return rows;
}

// 펼치기 (screen-today.md 6.1). 다시 그린 뒤에도 누른 카드에 초점을 둠
function detailFor(key, route) {
  return {
    key,
    label: LABELS[key],
    expanded: view.expanded.has(key),
    rows: legRows(key, route, new Date()),
    basis: liveBasis(key, route, view.response?.fetchedAt),
    onToggle: () => {
      if (view.expanded.has(key)) {
        view.expanded.delete(key);
      } else {
        view.expanded.add(key);
      }
      draw();
      root.querySelector(`.card-toggle[data-key="${key}"]`)?.focus();
    },
    onMap: () => nav.go(`#map/${key}`),
  };
}

function baseCard(route, now, target, marginSeconds) {
  const departure = departureLine({ now, targetArrival: target, totalSeconds: route.totalSeconds, marginSeconds });
  const savingMinutes = route.pmSaving ? floorMinutes(route.pmSaving.totalSeconds) : 0;
  return bestRouteCard({
    departure,
    durationText: `${ceilMinutes(route.totalSeconds)}분`,
    arrivalText: departure.kind === 'arrive_if_now' ? null : `지금 출발하면 ${expectedArrival(now, route.totalSeconds)} 도착`,
    chips: chipsFor('base', route),
    reason: routeReason('base', route),
    savingText: savingMinutes >= 1 ? `PM 탑승 시 ${savingMinutes}분 단축됩니다` : null,
    serviceUnknown: Boolean(route.serviceUnknown),
    detail: detailFor('base', route),
  });
}

function otherCard({ key, route, diff }, now, target, marginSeconds) {
  const departure = departureLine({ now, targetArrival: target, totalSeconds: route.totalSeconds, marginSeconds });
  return routeCard({
    label: LABELS[key],
    durationText: `${ceilMinutes(route.totalSeconds)}분`,
    diffText: diff ? diff.text : null,
    departureText: `${departure.prefix} ${departure.time} ${departure.suffix}`,
    chips: chipsFor(key, route),
    reason: routeReason(key, route),
    stations: key === 'bikeMix' ? stationsFor(route) : [],
    stockUnknown: key === 'bikeMix' && !route.stockKnown,
    pmNote: key === 'pmOnly',
    serviceUnknown: Boolean(route.serviceUnknown),
    detail: detailFor(key, route),
  });
}

// 처음 불러오는 중: 기본 경로 카드 자리와 다른 경로 카드 자리 2개 (screen-today.md 5장)
function skeletonCards() {
  const departure = { prefix: '늦어도', time: '00:00', suffix: '출발' };
  const chips = [{ iconName: 'walk', text: '도보 0분', tone: WALK_TONE }];
  const other = {
    label: 'PM 전용',
    durationText: '00분',
    departureText: '늦어도 00:00 출발',
    chips,
    reason: '환승이 없습니다',
    skeleton: true,
  };
  return [
    bestRouteCard({ departure, durationText: '00분', arrivalText: '지금 출발하면 00:00 도착', chips, reason: '환승이 없습니다', skeleton: true }),
    routeCard(other),
    routeCard(other),
  ];
}

function cardsFor(response, now, target, marginSeconds) {
  if (response.transit.status === 'ok' && response.base) {
    return orderRoutes(response).map((item) =>
      item.key === 'base' ? baseCard(item.route, now, target, marginSeconds) : otherCard(item, now, target, marginSeconds),
    );
  }
  // 경로 없음, 운행 중인 대중교통 없음(rules.md 3.4.5), 불러오기 실패(이전 결과 없음)
  const caption =
    response.transit.status === 'out_of_service' ? '운행 중인 대중교통이 없습니다' : '경로를 찾지 못했습니다';
  const cards = [emptyState({ caption, actionLabel: '다시 시도', onAction: () => load() })];
  if (response.pmOnly) {
    cards.push(otherCard({ key: 'pmOnly', route: response.pmOnly, diff: null }, now, target, marginSeconds));
  }
  return cards;
}

function draw() {
  if (!view || !root) {
    return;
  }
  const now = new Date();
  const settings = loadSettings();
  const target = settings.targetArrival[view.direction];
  const header = headerGradient({
    title: `${view.from.name} → ${view.to.name}`,
    direction: view.direction,
    targetText: target ? `${target} 도착 목표` : '목표 도착 시각이 없습니다',
    loading: view.loading,
    onRefresh: () => load(),
    onSettings: () => nav.go('#settings'),
    onToggle,
  });

  let cards;
  if (!view.response) {
    cards = skeletonCards();
  } else {
    shown = { response: view.response, from: view.from, to: view.to };
    cards = cardsFor(view.response, now, target, settings.marginSeconds);
  }
  const content = [];
  if (view.response && view.stale) {
    const minutes = floorMinutes((now.getTime() - new Date(view.response.fetchedAt).getTime()) / 1000);
    content.push(badgeNeutral(`${Math.max(minutes, 0)}분 전 정보`, 'stale-badge'));
  }
  content.push(el('div', { class: 'card-list', 'aria-busy': view.loading ? 'true' : 'false' }, cards));
  root.replaceChildren(el('div', { class: 'page today-page' }, [header, el('div', { class: 'today-content' }, content)]));
}
