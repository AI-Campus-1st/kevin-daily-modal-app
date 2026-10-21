// 선 아이콘 (DESIGN.md 9장)
// - 24 x 24 칸에 직접 그린 선 아이콘. 색은 주변 글자 색, 크기는 주변 글자 크기 (base.css .icon)
// - 장식용이므로 화면 낭독기에서 숨기고, 이름은 버튼이나 글자가 맡음

const SVG_NS = 'http://www.w3.org/2000/svg';

// 아이콘별 도형: ['path', d] 또는 ['circle', cx, cy, r] 또는 ['rect', x, y, w, h, rx]
const SHAPES = {
  walk: [
    ['circle', 13, 4, 2],
    ['path', 'M13 7.5 11 13l3 3v5'],
    ['path', 'M11 13l-3 3v5'],
    ['path', 'M8.5 11 12 8l3 3h3'],
  ],
  bus: [
    ['rect', 5, 3, 14, 15, 2],
    ['path', 'M5 11h14'],
    ['path', 'M5 7h14'],
    ['path', 'M8 18v3'],
    ['path', 'M16 18v3'],
    ['path', 'M8 14.5h.01'],
    ['path', 'M16 14.5h.01'],
  ],
  subway: [
    ['rect', 6, 3, 12, 14, 3],
    ['path', 'M6 10h12'],
    ['path', 'M9.5 13.5h.01'],
    ['path', 'M14.5 13.5h.01'],
    ['path', 'M9 17l-2 4'],
    ['path', 'M15 17l2 4'],
  ],
  bike: [
    ['circle', 6, 16, 3.5],
    ['circle', 18, 16, 3.5],
    ['path', 'M6 16l3.5-7h6L18 16'],
    ['path', 'M9.5 9l3 7'],
    ['path', 'M13.5 6h2.5l-0.5 3'],
  ],
  refresh: [
    ['path', 'M20 12a8 8 0 1 1-2.34-5.66'],
    ['path', 'M20 4v4h-4'],
  ],
  settings: [
    ['path', 'M4 6h10'],
    ['path', 'M18 6h2'],
    ['circle', 16, 6, 2],
    ['path', 'M4 12h4'],
    ['path', 'M12 12h8'],
    ['circle', 10, 12, 2],
    ['path', 'M4 18h12'],
    ['path', 'M20 18h0'],
    ['circle', 18, 18, 2],
  ],
  back: [['path', 'M15 5l-7 7 7 7']],
  check: [['path', 'M5 12.5l4.5 4.5L19 7.5']],
  caution: [
    ['path', 'M12 3.5 2.5 20h19Z'],
    ['path', 'M12 10v4.5'],
    ['path', 'M12 17.5h.01'],
  ],
};

export function icon(name) {
  const svg = document.createElementNS(SVG_NS, 'svg');
  svg.setAttribute('class', 'icon');
  svg.setAttribute('viewBox', '0 0 24 24');
  svg.setAttribute('aria-hidden', 'true');
  svg.setAttribute('focusable', 'false');
  for (const [kind, ...args] of SHAPES[name] ?? []) {
    const shape = document.createElementNS(SVG_NS, kind);
    if (kind === 'path') {
      shape.setAttribute('d', args[0]);
    } else if (kind === 'circle') {
      ['cx', 'cy', 'r'].forEach((attr, i) => shape.setAttribute(attr, args[i]));
    } else if (kind === 'rect') {
      ['x', 'y', 'width', 'height', 'rx'].forEach((attr, i) => shape.setAttribute(attr, args[i]));
    }
    svg.append(shape);
  }
  return svg;
}
