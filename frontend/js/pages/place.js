// SC-03 장소 입력 (screen-place.md)
// - 칸이 비어 있으면 새로 등록, 저장된 장소가 있으면 수정
// - 저장하지 않고 나가면 입력 내용을 버림 (확인 창 없음)
// - 주소로 찾지 못하면 서버가 키워드 장소 검색으로 찾아 줌 (D-32)

import { searchAddress } from '../api.js';
import { buttonCaution, buttonGhost, buttonPrimary } from '../components/buttons.js';
import { el } from '../components/dom.js';
import { topBar } from '../components/frame.js';
import { icon } from '../components/icons.js';
import { listRow, textInput } from '../components/inputs.js';
import { modal, toast } from '../components/overlay.js';
import { deletePlace, loadPlaces, savePlace, SLOTS } from '../storage.js';
import { placeLines } from './settings.js';

const NAME_MAX = 20;
const QUERY_MAX = 100;

let state = null;
let root = null;
let nav = null;

export function render(rootNode, navigator, slot) {
  root = rootNode;
  nav = navigator;
  const safeSlot = SLOTS.includes(slot) ? slot : 'origin';
  const existing = loadPlaces()[safeSlot];
  state = {
    slot: safeSlot,
    existing,
    query: '',
    lastQuery: '',
    error: null,
    searching: false,
    searched: false,
    status: null,
    items: [],
    page: 1,
    isEnd: true,
    source: null, // 첫 쪽 응답의 source. 다음 쪽 요청에 함께 보냄
    selected: null,
    name: existing ? existing.name : '',
  };
  draw();
}

function trimmedName() {
  return state.name.trim();
}

function canSave() {
  const name = trimmedName();
  const hasAddress = state.selected !== null || state.existing !== null;
  return hasAddress && name.length >= 1 && name.length <= NAME_MAX;
}

// 검색어 확인 (api_spec.md 3.1). 맞지 않으면 서버에 보내지 않음
function queryError(query) {
  const trimmed = query.trim();
  if (trimmed.replace(/\s/g, '').length < 2) {
    return '2자 이상 입력해 주십시오';
  }
  if (trimmed.length > QUERY_MAX) {
    return '100자 이하로 입력해 주십시오';
  }
  return null;
}

async function search(page = 1) {
  if (state.searching) {
    return;
  }
  const query = page === 1 ? state.query : state.lastQuery;
  if (page === 1) {
    state.error = queryError(query);
    if (state.error) {
      draw('query');
      return;
    }
    // 새로 검색하면 후보와 선택을 비움
    state.items = [];
    state.selected = null;
    state.status = null;
    state.source = null;
    state.lastQuery = query.trim();
  }
  state.searching = true;
  draw(page === 1 ? 'query' : null);
  const current = state;
  const result = await searchAddress(state.lastQuery, page, page === 1 ? null : state.source);
  if (state !== current) {
    return;
  }
  state.searching = false;
  if (result.status === 'ok') {
    state.items = page === 1 ? result.items : state.items.concat(result.items);
    state.page = page;
    state.isEnd = result.isEnd;
    state.status = 'ok';
    if (page === 1) {
      state.source = result.source;
    }
  } else if (result.status === 'no_result' && page === 1) {
    state.status = 'no_result';
  } else {
    state.status = page === 1 ? null : state.status;
    toast('주소를 검색하지 못했습니다. 다시 시도해 주십시오');
  }
  state.searched = true;
  draw();
}

// 후보 행 (screen-place.md 2장). 장소 후보는 첫 줄 장소 이름, 둘째 줄 도로명 주소(없으면 지번 주소)
function candidateRow(item, index) {
  const isPlace = Boolean(item.placeName);
  const title = isPlace ? item.placeName : (item.roadAddress ?? item.addressName);
  const second = isPlace
    ? (item.roadAddress ?? item.jibunAddress ?? item.addressName)
    : [item.jibunAddress, item.buildingName].filter(Boolean).join(' · ');
  return listRow({
    title,
    subtitle: second || null,
    selected: state.selected === index,
    onClick: () => {
      state.selected = index;
      // 장소 후보를 고를 때 이름 칸이 비어 있으면 장소 이름의 앞 20자로 채움 (D-32)
      if (isPlace && trimmedName() === '') {
        state.name = item.placeName.slice(0, NAME_MAX);
      }
      draw();
    },
  });
}

function candidatesArea() {
  if (state.searching && state.items.length === 0) {
    return el('p', { class: 't-link-sm ink-secondary', text: '검색하고 있습니다' });
  }
  if (state.status === 'no_result') {
    return el('p', { class: 't-body ink-secondary', text: '주소나 장소를 찾지 못했습니다. 검색어를 확인해 주십시오' });
  }
  if (state.items.length === 0) {
    return null;
  }
  return el('div', { class: 'row-list' }, [
    ...state.items.map(candidateRow),
    state.isEnd
      ? null
      : buttonGhost({ label: '더 보기', block: true, disabled: state.searching, onClick: () => search(state.page + 1) }),
  ]);
}

function save() {
  if (!canSave()) {
    return;
  }
  const source = state.selected !== null ? state.items[state.selected] : state.existing;
  savePlace(state.slot, {
    name: trimmedName(),
    addressName: source.addressName,
    roadAddress: source.roadAddress ?? null,
    jibunAddress: source.jibunAddress ?? null,
    placeName: source.placeName ?? null,
    x: source.x,
    y: source.y,
  });
  nav.up('#settings');
}

function openDeleteModal() {
  const handle = modal({
    title: '장소를 삭제합니다',
    content: [
      el('p', { class: 't-body', text: `${state.existing.name} 장소가 이 기기에서 지워집니다` }),
      el('div', { class: 'modal-actions' }, [
        buttonGhost({ label: '취소', block: true, onClick: () => handle.close() }),
        buttonCaution({
          label: '삭제',
          block: true,
          onClick: () => {
            deletePlace(state.slot);
            handle.close(() => nav.up('#settings'));
          },
        }),
      ]),
    ],
  });
}

// focusTarget: 다시 그린 뒤 초점을 둘 입력 칸 ('query', 'name')
function draw(focusTarget = null) {
  const isOrigin = state.slot === 'origin';
  const queryInput = textInput({
    id: 'place-query',
    value: state.query,
    placeholder: '주소 또는 장소 이름',
    enterkeyhint: 'search',
    autocomplete: 'off',
    'aria-label': '주소 또는 장소 이름',
    'aria-describedby': 'place-query-help',
    'aria-invalid': state.error ? 'true' : null,
    oninput: (event) => {
      state.query = event.target.value;
    },
  });
  const saveButton = buttonPrimary({ label: '저장', block: true, disabled: !canSave(), onClick: save });
  const nameInput = textInput({
    id: 'place-name',
    value: state.name,
    placeholder: isOrigin ? '예: 집' : '예: 회사',
    autocomplete: 'off',
    oninput: (event) => {
      state.name = event.target.value;
      saveButton.disabled = !canSave();
    },
  });

  const searchForm = el(
    'form',
    {
      class: 'search-form',
      role: 'search',
      onsubmit: (event) => {
        event.preventDefault();
        search(1);
      },
    },
    [
      el('div', { class: 'search-row' }, [
        queryInput,
        buttonGhost({ label: '검색', type: 'submit', disabled: state.searching }),
      ]),
      el('p', { class: 't-link-sm ink-secondary', id: 'place-query-help', text: '예: 테헤란로 152, 강남역, 정부서울청사' }),
      state.error
        ? el('p', { class: 'input-error t-link-sm', role: 'alert' }, [icon('caution'), state.error])
        : null,
    ],
  );

  const existing = state.existing;
  root.replaceChildren(
    el('div', { class: 'page place-page' }, [
      topBar({ title: isOrigin ? '출발지' : '도착지', onBack: () => nav.up('#settings') }),
      el('div', { class: 'place-body' }, [
        existing
          ? listRow({
              title: existing.name,
              subtitle: placeLines(existing),
            })
          : null,
        el('section', { class: 'place-search' }, [searchForm, candidatesArea()]),
        el('div', { class: 'name-field' }, [
          el('label', { class: 't-link-sm ink-secondary', for: 'place-name', text: '이름' }),
          nameInput,
        ]),
      ]),
      el('div', { class: 'bottom-actions' }, [
        saveButton,
        existing ? buttonGhost({ label: '장소 삭제', block: true, onClick: openDeleteModal }) : null,
      ]),
    ]),
  );
  if (focusTarget === 'query') {
    queryInput.focus();
  } else if (focusTarget === 'name') {
    nameInput.focus();
  }
}
