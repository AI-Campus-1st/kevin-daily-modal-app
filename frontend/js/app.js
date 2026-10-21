// 화면 이동과 앱 상태 (tech_stack.md 4.4, screens.md 2, 3.1장)
// - 주소의 # 뒤 이름으로 화면을 바꿈 (hashchange). 페이지를 새로 받지 않음
// - 이 앱 안에서 지나온 화면 목록(stack)을 함께 기억해, 위 화면으로 돌아갈 때 기기의 뒤로 가기와 같은 기록이 되게 함

import * as mapPage from './pages/map.js';
import * as placePage from './pages/place.js';
import * as settingsPage from './pages/settings.js';
import * as todayPage from './pages/today.js';
import { loadSettings } from './storage.js';
import { applyTheme } from './theme.js';

const root = document.getElementById('app');

const stack = [];
let replacing = false;
let guard = null;
let afterReturn = null;
let leaveCurrent = null;

const HASHES = new Set([
  '#today',
  '#settings',
  '#place/origin',
  '#place/destination',
  '#map/base',
  '#map/bikeMix',
  '#map/busOnly',
  '#map/pmOnly',
]);

// 화면 주소 정리. 목록에 없는 주소, 빈 주소는 #today
function normalize(hash) {
  return HASHES.has(hash) ? hash : '#today';
}

export const nav = {
  // 아래 화면으로 이동 (기록에 한 칸 추가)
  go(hash) {
    location.hash = hash;
  },
  // 위 화면으로 돌아감. 바로 앞 화면이 그 화면이면 뒤로 가기, 아니면 지금 칸을 바꿈
  up(hash) {
    if (stack.length >= 2 && stack[stack.length - 2] === hash) {
      history.back();
    } else {
      replacing = true;
      location.replace(hash);
    }
  },
  // 기기의 뒤로 가기로 화면을 떠나려 할 때 확인할 함수. (떠나는 화면, 갈 화면) → 막으면 돌아온 뒤 실행할 함수
  setGuard(fn) {
    guard = fn;
  },
};

function render(hash) {
  if (leaveCurrent) {
    leaveCurrent(hash);
    leaveCurrent = null;
  }
  guard = null;
  window.scrollTo(0, 0);
  if (hash === '#settings') {
    settingsPage.render(root, nav);
    leaveCurrent = settingsPage.leave;
  } else if (hash.startsWith('#place/')) {
    placePage.render(root, nav, hash.slice('#place/'.length));
  } else if (hash.startsWith('#map/')) {
    mapPage.render(root, nav, hash.slice('#map/'.length));
    leaveCurrent = mapPage.leave;
  } else {
    todayPage.render(root, nav);
    leaveCurrent = todayPage.leave;
  }
}

function onRoute() {
  const raw = location.hash;
  const hash = normalize(raw);
  if (hash !== raw) {
    replacing = true;
    location.replace(hash);
    return;
  }
  const from = stack[stack.length - 1];
  if (from === hash) {
    // 막았던 뒤로 가기에서 돌아옴
    if (afterReturn) {
      const fn = afterReturn;
      afterReturn = null;
      fn();
    }
    return;
  }
  if (guard && from && !replacing) {
    const blocked = guard(from, hash);
    if (blocked) {
      afterReturn = blocked;
      history.forward();
      return;
    }
  }
  if (replacing && stack.length) {
    stack[stack.length - 1] = hash;
  } else if (stack.length >= 2 && stack[stack.length - 2] === hash) {
    stack.pop();
  } else {
    stack.push(hash);
  }
  replacing = false;
  render(hash);
}

// 저장된 화면 모드를 첫 화면을 그리기 전에 적용 (DESIGN.md 2.5.5)
applyTheme(loadSettings().theme);

window.addEventListener('hashchange', onRoute);
onRoute();
