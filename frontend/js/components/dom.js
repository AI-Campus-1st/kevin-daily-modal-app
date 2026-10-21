// 화면 요소를 만드는 작은 도구
// - 글자는 항상 textContent로 넣어 장소 이름 같은 입력값이 HTML로 해석되지 않게 함

// el('button', { class: 'x', onclick: fn, text: '저장' }, [자식...])
// - 값이 null, undefined, false인 속성은 넣지 않음. true이면 값 없는 속성
export function el(tag, props = {}, children = []) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(props)) {
    if (value === null || value === undefined || value === false) {
      continue;
    }
    if (key === 'class') {
      node.className = value;
    } else if (key === 'text') {
      node.textContent = value;
    } else if (key.startsWith('on') && typeof value === 'function') {
      node.addEventListener(key.slice(2), value);
    } else if (value === true) {
      node.setAttribute(key, '');
    } else {
      node.setAttribute(key, String(value));
    }
  }
  append(node, children);
  return node;
}

// 자식 목록을 붙임. null, false는 건너뜀
export function append(node, children) {
  for (const child of [].concat(children)) {
    if (child === null || child === undefined || child === false) {
      continue;
    }
    node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  return node;
}

let idCount = 0;

// 화면 안에서 겹치지 않는 id
export function uid(prefix) {
  idCount += 1;
  return `${prefix}-${idCount}`;
}
