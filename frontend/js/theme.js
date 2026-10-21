// 화면 모드 적용 (DESIGN.md 2.5.5)
// - <html>의 data-theme 속성만 바꿈. 색은 tokens.css의 라이트 블록이 바꿈
// - null(기기 설정 따름)이면 속성을 지워 기기의 밝은 화면 설정(prefers-color-scheme)을 따르게 함

export function applyTheme(theme) {
  const html = document.documentElement;
  if (theme === 'light' || theme === 'dark') {
    html.dataset.theme = theme;
  } else {
    delete html.dataset.theme;
  }
}
