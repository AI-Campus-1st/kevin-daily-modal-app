// 겹치는 면과 빈 상태 (DESIGN.md 7.6)
// - 모달을 열면 기록(history)에 한 칸을 더해, 기기의 뒤로 가기가 화면 이동 대신 모달을 닫게 함
// - 버튼으로 닫을 때도 그 칸을 되돌린 뒤(history.back) 다음 동작(after)을 실행

import { buttonPrimary } from './buttons.js';
import { el, uid } from './dom.js';

const TOAST_MS = 3000;

let current = null;
let toastTimer = null;

function finishClose() {
  if (!current) {
    return;
  }
  const { scrim, after, previousFocus, onKey } = current;
  current = null;
  document.removeEventListener('keydown', onKey);
  scrim.remove();
  if (previousFocus && document.contains(previousFocus)) {
    previousFocus.focus();
  }
  if (after) {
    after();
  }
}

window.addEventListener('popstate', () => {
  if (current) {
    finishClose();
  }
});

export function isModalOpen() {
  return current !== null;
}

// 화면 아래쪽에서 올라오는 모달. 반환값의 close(after)로 닫음
export function modal({ title, content = [] }) {
  if (current) {
    current.scrim.remove();
    current = null;
  }
  const titleId = uid('modal-title');
  const box = el('div', { class: 'modal', role: 'dialog', 'aria-modal': 'true', 'aria-labelledby': titleId }, [
    el('h2', { class: 't-heading-sm', id: titleId, text: title }),
    ...content,
  ]);
  const handle = {
    close(after = null) {
      if (!current || current.box !== box) {
        return;
      }
      current.after = after;
      history.back();
    },
  };
  const scrim = el(
    'div',
    {
      class: 'modal-scrim',
      onclick: (event) => {
        if (event.target === scrim) {
          handle.close();
        }
      },
    },
    [box],
  );
  const onKey = (event) => {
    if (event.key === 'Escape') {
      handle.close();
    }
  };
  current = { scrim, box, after: null, previousFocus: document.activeElement, onKey };
  document.addEventListener('keydown', onKey);
  history.pushState({ modal: true }, '');
  document.getElementById('modal-region').append(scrim);
  const first = box.querySelector('button, input');
  if (first) {
    first.focus();
  }
  return handle;
}

// 짧은 알림. 화면 아래쪽에 나타나고 몇 초 뒤 사라짐
export function toast(text) {
  const region = document.getElementById('toast-region');
  region.replaceChildren(el('div', { class: 'toast t-body', text }));
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => region.replaceChildren(), TOAST_MS);
}

// 빈 상태. 안내 문구와 주요 행동 버튼. actionLabel이 없으면 안내 문구만
export function emptyState({ caption, actionLabel = null, onAction = null }) {
  return el('section', { class: 'empty-state' }, [
    el('p', { class: 't-body', text: caption }),
    actionLabel ? buttonPrimary({ label: actionLabel, onClick: onAction }) : null,
  ]);
}
