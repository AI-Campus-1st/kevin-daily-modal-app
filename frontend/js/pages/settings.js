// SC-02 설정 (screen-settings.md)
// - 모달에서 고른 값은 화면 값(draft)만 바꾸고, 화면 아래 "저장"으로 한꺼번에 기기에 저장
// - 장소 입력 화면에 다녀와도 저장하지 않은 값은 화면 메모리에 남음. 오늘의 추천으로 나가면 버림

import { buttonCaution, buttonGhost, buttonPrimary } from '../components/buttons.js';
import { el } from '../components/dom.js';
import { topBar } from '../components/frame.js';
import { listRow, textInput } from '../components/inputs.js';
import { modal, toast } from '../components/overlay.js';
import { DIRECTION_SWITCH_TIME } from '../logic/defaults.js';
import { clearAll, loadPlaces, loadSettings, saveSettings } from '../storage.js';

const MARGIN_CHOICES = [0, 5, 10, 15, 20, 30]; // 분 (screen-settings.md 3.2)

let draft = null;
let root = null;
let nav = null;

// 저장 버튼 대상 4가지만 뽑음 (screen-settings.md 4장)
function editable(settings) {
  return {
    commute: settings.targetArrival.commute,
    return: settings.targetArrival.return,
    marginSeconds: settings.marginSeconds,
    directionMode: settings.directionMode,
  };
}

function isDirty() {
  if (!draft) {
    return false;
  }
  const saved = editable(loadSettings());
  return Object.keys(saved).some((key) => saved[key] !== draft[key]);
}

export function render(rootNode, navigator) {
  root = rootNode;
  nav = navigator;
  if (!draft) {
    draft = editable(loadSettings());
  }
  nav.setGuard((from, to) => (to === '#today' && isDirty() ? openLeaveModal : null));
  draw();
}

// 오늘의 추천으로 나가면 저장하지 않은 값을 버림. 장소 입력 화면으로 가면 유지
export function leave(to) {
  if (!to.startsWith('#place/')) {
    draft = null;
  }
}

function goBack() {
  if (isDirty()) {
    openLeaveModal();
  } else {
    nav.up('#today');
  }
}

// 장소 행의 둘째 줄부터. 키워드로 고른 장소이면 장소 이름, 그 아래 도로명 주소
// - 장소 이름이 사용자가 정한 이름과 같으면 같은 글자가 두 번 보이므로 뺌
export function placeLines(place) {
  const address = place.roadAddress ?? place.jibunAddress ?? place.addressName;
  const placeName = place.placeName && place.placeName !== place.name ? place.placeName : null;
  return [placeName, address];
}

function placeSubtitle(place) {
  if (!place) {
    return '도로명 또는 지번 주소로 등록합니다';
  }
  return placeLines(place);
}

function section(title, rows) {
  return el('section', { class: 'settings-section' }, [
    el('h2', { class: 't-link-sm ink-secondary', text: title }),
    el('div', { class: 'row-list' }, rows),
  ]);
}

function modeText(mode) {
  return mode === 'return_commute' ? `${DIRECTION_SWITCH_TIME} 전 퇴근` : `${DIRECTION_SWITCH_TIME} 전 출근`;
}

function draw() {
  const places = loadPlaces();
  const { origin, destination } = places;
  const hasPlaces = origin && destination;
  const forward = hasPlaces ? `${origin.name} → ${destination.name}` : '출발지 → 도착지';
  const backward = hasPlaces ? `${destination.name} → ${origin.name}` : '도착지 → 출발지';

  const content = [
    topBar({ title: '설정', onBack: goBack }),
    el('div', { class: 'settings-body' }, [
      section('장소', [
        listRow({
          title: origin ? origin.name : '출발지 등록',
          subtitle: placeSubtitle(origin),
          onClick: () => nav.go('#place/origin'),
        }),
        listRow({
          title: destination ? destination.name : '도착지 등록',
          subtitle: placeSubtitle(destination),
          onClick: () => nav.go('#place/destination'),
        }),
      ]),
      section('도착 목표', [
        listRow({
          title: '출근 목표 도착 시각',
          subtitle: forward,
          value: draft.commute ?? '설정하지 않았습니다',
          onClick: () => openTimeModal('commute'),
        }),
        listRow({
          title: '퇴근 목표 도착 시각',
          subtitle: backward,
          value: draft.return ?? '설정하지 않았습니다',
          onClick: () => openTimeModal('return'),
        }),
        listRow({
          title: '여유 시간',
          subtitle: '출발 시각을 이만큼 앞당겨 알려 드립니다',
          value: `${Math.round(draft.marginSeconds / 60)}분`,
          onClick: openMarginModal,
        }),
      ]),
      section('방향', [
        listRow({
          title: '출근 퇴근 전환',
          subtitle: '앱을 연 시각에 따라 방향을 정합니다',
          value: modeText(draft.directionMode),
          onClick: openModeModal,
        }),
      ]),
      buttonGhost({ label: '저장 정보 모두 지우기', onClick: openClearModal, block: true }),
    ]),
    el('div', { class: 'bottom-actions' }, [
      buttonPrimary({ label: '저장', onClick: save, disabled: !isDirty(), block: true }),
    ]),
  ];
  root.replaceChildren(el('div', { class: 'page settings-page' }, content));
}

function save() {
  const settings = loadSettings();
  settings.targetArrival = { commute: draft.commute, return: draft.return };
  settings.marginSeconds = draft.marginSeconds;
  settings.directionMode = draft.directionMode;
  saveSettings(settings);
  toast('저장했습니다');
  draw();
}

// 3.1 목표 도착 시각. 휴대폰의 시각 고르기 창(input type=time) 사용
function openTimeModal(direction) {
  const title = direction === 'commute' ? '출근 목표 도착 시각' : '퇴근 목표 도착 시각';
  const input = textInput({ type: 'time', value: draft[direction] ?? '', class: 'text-input t-body num', 'aria-label': title });
  const confirm = buttonPrimary({
    label: '확인',
    block: true,
    disabled: !draft[direction],
    onClick: () => {
      const value = input.value.slice(0, 5);
      handle.close(() => {
        draft[direction] = value;
        draw();
      });
    },
  });
  input.addEventListener('input', () => {
    confirm.disabled = !input.value;
  });
  const handle = modal({
    title,
    content: [
      input,
      el('div', { class: 'modal-actions' }, [
        confirm,
        buttonGhost({
          label: '설정하지 않기',
          block: true,
          onClick: () =>
            handle.close(() => {
              draft[direction] = null;
              draw();
            }),
        }),
      ]),
    ],
  });
}

// 3.2 여유 시간
function openMarginModal() {
  const rows = MARGIN_CHOICES.map((minutes) =>
    listRow({
      title: `${minutes}분`,
      selected: draft.marginSeconds === minutes * 60,
      onClick: () =>
        handle.close(() => {
          draft.marginSeconds = minutes * 60;
          draw();
        }),
    }),
  );
  const handle = modal({ title: '여유 시간', content: [el('div', { class: 'modal-list' }, rows)] });
}

// 3.3 출근 퇴근 전환 기준
function openModeModal() {
  const choices = [
    ['commute_return', `${DIRECTION_SWITCH_TIME} 전 출근`, `${DIRECTION_SWITCH_TIME} 이후 퇴근`],
    ['return_commute', `${DIRECTION_SWITCH_TIME} 전 퇴근`, `${DIRECTION_SWITCH_TIME} 이후 출근`],
  ];
  const rows = choices.map(([mode, title, subtitle]) =>
    listRow({
      title,
      subtitle,
      selected: draft.directionMode === mode,
      onClick: () =>
        handle.close(() => {
          draft.directionMode = mode;
          draw();
        }),
    }),
  );
  const handle = modal({ title: '출근 퇴근 전환', content: [el('div', { class: 'modal-list' }, rows)] });
}

// 3.4 저장 정보 모두 지우기 (F-12)
function openClearModal() {
  const handle = modal({
    title: '저장 정보를 모두 지웁니다',
    content: [
      el('p', { class: 't-body', text: '장소와 설정이 이 기기에서 지워지며 되돌릴 수 없습니다' }),
      el('div', { class: 'modal-actions' }, [
        buttonGhost({ label: '취소', block: true, onClick: () => handle.close() }),
        buttonCaution({
          label: '모두 지우기',
          block: true,
          onClick: () => {
            clearAll();
            draft = null;
            handle.close(() => nav.up('#today'));
          },
        }),
      ]),
    ],
  });
}

// 3.5 저장하지 않고 나가기
function openLeaveModal() {
  const handle = modal({
    title: '저장하지 않은 변경 사항이 있습니다',
    content: [
      el('div', { class: 'modal-actions' }, [
        buttonPrimary({ label: '계속 수정', block: true, onClick: () => handle.close() }),
        buttonGhost({
          label: '저장하지 않고 나가기',
          block: true,
          onClick: () => {
            draft = null;
            handle.close(() => nav.up('#today'));
          },
        }),
      ]),
    ],
  });
}
