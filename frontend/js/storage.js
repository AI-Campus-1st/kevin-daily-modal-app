// 기기 저장 (frontend/CLAUDE.md 4장)
// - localStorage 읽기, 쓰기는 이 파일만 함
// - 객체는 JSON 문자열로 바꿔 저장. 키 이름의 v1은 저장 형식 버전

import { MARGIN_SECONDS } from './logic/defaults.js';
import { parseClock } from './logic/departure.js';

const PLACES_KEY = 'dmpm.v1.places';
const SETTINGS_KEY = 'dmpm.v1.settings';

export const SLOTS = ['origin', 'destination'];
const MODES = ['commute_return', 'return_commute'];
const THEMES = ['light', 'dark'];

function read(key) {
  try {
    const text = localStorage.getItem(key);
    return text ? JSON.parse(text) : null;
  } catch {
    return null;
  }
}

function write(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
    return true;
  } catch {
    return false;
  }
}

// 장소 한 칸의 형식 확인. 형식이 다르면 null
function validPlace(place) {
  if (!place || typeof place !== 'object') {
    return null;
  }
  const { name, addressName, roadAddress, jibunAddress, placeName, x, y } = place;
  if (typeof name !== 'string' || typeof addressName !== 'string') {
    return null;
  }
  if (!Number.isFinite(x) || !Number.isFinite(y)) {
    return null;
  }
  return {
    name,
    addressName,
    roadAddress: typeof roadAddress === 'string' ? roadAddress : null,
    jibunAddress: typeof jibunAddress === 'string' ? jibunAddress : null,
    // 키워드 장소 검색으로 고른 장소의 이름. 선택 항목이라 없으면 null (같은 v1 형식)
    placeName: typeof placeName === 'string' && placeName ? placeName : null,
    x,
    y,
  };
}

// 저장된 장소 2칸. 없는 칸은 null
export function loadPlaces() {
  const stored = read(PLACES_KEY) ?? {};
  return {
    origin: validPlace(stored.origin),
    destination: validPlace(stored.destination),
  };
}

export function savePlace(slot, place) {
  const places = loadPlaces();
  places[slot] = validPlace(place);
  return write(PLACES_KEY, places);
}

export function deletePlace(slot) {
  const places = loadPlaces();
  places[slot] = null;
  return write(PLACES_KEY, places);
}

// 설정 기본값 (rules.md 12장)
export function defaultSettings() {
  return {
    targetArrival: { commute: null, return: null },
    marginSeconds: MARGIN_SECONDS,
    directionMode: 'commute_return',
    manualDirection: null,
    // 화면 모드. null이면 기기 설정 따름 (DESIGN.md 2.5.1). 선택 항목이라 없으면 null (같은 v1 형식)
    theme: null,
  };
}

function validClock(value) {
  return typeof value === 'string' && parseClock(value) ? value : null;
}

function validManual(value) {
  if (!value || !['commute', 'return'].includes(value.direction)) {
    return null;
  }
  return Number.isNaN(new Date(value.until).getTime()) ? null : { direction: value.direction, until: value.until };
}

// 저장된 설정. 형식이 다른 항목은 기본값
export function loadSettings() {
  const stored = read(SETTINGS_KEY) ?? {};
  const settings = defaultSettings();
  const target = stored.targetArrival ?? {};
  settings.targetArrival = {
    commute: validClock(target.commute),
    return: validClock(target.return),
  };
  if (Number.isInteger(stored.marginSeconds) && stored.marginSeconds >= 0) {
    settings.marginSeconds = stored.marginSeconds;
  }
  if (MODES.includes(stored.directionMode)) {
    settings.directionMode = stored.directionMode;
  }
  settings.manualDirection = validManual(stored.manualDirection);
  settings.theme = THEMES.includes(stored.theme) ? stored.theme : null;
  return settings;
}

export function saveSettings(settings) {
  return write(SETTINGS_KEY, settings);
}

// 화면 모드만 바꿔 저장 (screen-settings.md 3.6)
// - 저장된 설정을 읽어 theme만 바꿈. 설정 화면에서 저장하지 않은 다른 값은 함께 저장하지 않음
export function saveTheme(theme) {
  const settings = loadSettings();
  settings.theme = THEMES.includes(theme) ? theme : null;
  return write(SETTINGS_KEY, settings);
}

// 저장 정보 모두 지우기 (F-12, frontend/CLAUDE.md 4.4)
export function clearAll() {
  try {
    localStorage.removeItem(PLACES_KEY);
    localStorage.removeItem(SETTINGS_KEY);
  } catch {
    // 저장소를 쓸 수 없는 환경이면 지울 것도 없음
  }
}
