---
version: 1
name: 출퇴근 대중교통, PM 경로 추천 서비스 디자인 명세
description: Discord Analysis 토큰(DESIGN-discord.md)을 이 서비스에 맞게 적용한 디자인 기준. 깊은 인디고 바탕, Blurple 강조, 둥근 형태를 유지하되 매일 아침 몇 초 안에 읽고 결정하는 휴대폰 도구에 맞게 표현 강도를 조절
source: docs/design/DESIGN-discord.md (Discord Analysis, version alpha)

colors:
  # 원본 토큰 (값 변경 없음)
  primary: "#5865f2"
  on-primary: "#ffffff"
  green: "#35ed7e"
  magenta: "#ec48bd"
  link: "#00b0f4"
  canvas: "#0a0d3a"
  surface-indigo: "#1e2353"
  surface-onyx: "#23272a"
  surface-black: "#000000"
  ink: "#ffffff"
  ink-dark: "#000000"
  muted: "#333333"
  hairline: "#23272a"
  # 사용자 지정 추가 토큰
  caution: "#ffda33"
  # 사용자 지정 수단 색 (2.4)
  mode-walk: "#262626"
  mode-bike: "#2edb8c"
  mode-pm: "#9c9c9c"
  position-surface: "#262626"
  position-text: "#ff7a7a"
  # 지하철 노선 색 (2.4.2)
  subway-line1: "#0052a4"
  subway-line2: "#00a84d"
  subway-line3: "#ef7c1c"
  subway-line4: "#00a4e3"
  subway-line5: "#996cac"
  subway-line6: "#cd7c2f"
  subway-line7: "#747f00"
  subway-line8: "#e6186c"
  subway-line9: "#bdb092"
  subway-gyeongui-jungang: "#77c4a3"
  subway-suin-bundang: "#f5a200"
  subway-shinbundang: "#d4003b"
  subway-airport: "#0065b3"
  subway-gyeongchun: "#0c8e72"
  subway-gyeonggang: "#003da5"
  subway-seohae: "#8ec31f"
  subway-ui-sinseol: "#b0ce18"
  subway-sillim: "#6789ca"
  subway-gimpo-goldline: "#a17800"
  subway-incheon1: "#7ca8d5"
  subway-incheon2: "#ed8b00"
  subway-uijeongbu: "#fda600"
  subway-everline: "#509f22"
  subway-gtx-a: "#9a6292"
  # 버스 종류 색 (2.4.3)
  bus-trunk: "#0068b7"
  bus-branch: "#53b332"
  bus-village: "#53b332"
  bus-wide: "#e60012"
  bus-direct: "#e60012"
  bus-rapid: "#e60012"
  bus-general: "#33cc99"
  bus-seat: "#0068b7"
  bus-circular: "#f2b70a"
  bus-airport: "#3d5bab"
  bus-night: "#3d5bab"
  # 파생 토큰 (원본 토큰 조합)
  ink-secondary: "rgba(255, 255, 255, 0.7)"
  caution-text: "{colors.caution}"
  pressed-overlay: "rgba(0, 0, 0, 0.2)"
  gradient-brand: "linear-gradient(135deg, {colors.primary} 0%, {colors.magenta} 100%)"

colors-light:
  # 라이트 모드에서 값을 바꾸는 색 (2.5). 이름은 colors와 같고, 여기 없는 색은 colors 값 그대로
  canvas: "#ffffff"
  surface-indigo: "#ebedfd"
  surface-onyx: "#e6e6e6"
  surface-black: "#e6e6e6"
  hairline: "#e6e6e6"
  ink: "#0a0d3a"
  ink-secondary: "rgba(10, 13, 58, 0.7)"
  link: "#006a92"
  caution-text: "#736217"

typography:
  # 글꼴은 모두 Pretendard로 대체. 크기, 굵기, 줄 높이, 자간은 원본 값 유지
  display-md:
    fontFamily: Pretendard
    fontSize: 56px
    fontWeight: 700
    lineHeight: 1.05
    letterSpacing: 0
  heading-lg:
    fontFamily: Pretendard
    fontSize: 48px
    fontWeight: 700
    lineHeight: 1.1
    letterSpacing: 0
  heading-sm:
    fontFamily: Pretendard
    fontSize: 22px
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: 0
  body-lg:
    fontFamily: Pretendard
    fontSize: 20px
    fontWeight: 500
    lineHeight: 1.4
    letterSpacing: 0
  link-lg:
    fontFamily: Pretendard
    fontSize: 18px
    fontWeight: 500
    lineHeight: 1.4
    letterSpacing: 0
  body:
    fontFamily: Pretendard
    fontSize: 16px
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: 0
  link:
    fontFamily: Pretendard
    fontSize: 16px
    fontWeight: 500
    lineHeight: 1.4
    letterSpacing: 0
  link-sm:
    fontFamily: Pretendard
    fontSize: 14px
    fontWeight: 500
    lineHeight: 1.4
    letterSpacing: 0

rounded:
  xs: 6px
  sm: 12px
  md: 14px
  lg: 16px
  xl: 40px
  pill: 50px
  full: 9999px

spacing:
  xxs: 4px
  xs: 8px
  sm: 12px
  md: 16px
  lg: 20px
  xl: 24px
  xxl: 32px
  section: 40px

elevation:
  flat: "none"
  float: "0 3px 68px rgba(69, 42, 124, 0.1)"

layout:
  mobile-max: 767px
  touch-target: 44px
  focus-ring: "2px solid {colors.ink}"

components:
  top-bar:
    base: nav-bar
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    typography: "{typography.heading-sm}"
    padding: "{spacing.md}"
  header-gradient:
    base: hero
    background: "{colors.gradient-brand}"
    textColor: "{colors.on-primary}"
    typography: "{typography.heading-sm}"
    padding: "{spacing.xl} {spacing.md}"
  direction-toggle:
    base: button-ghost-sm
    backgroundColor: "{colors.surface-indigo}"
    selectedBackgroundColor: "{colors.primary}"
    textColor: "{colors.ink}"
    selectedTextColor: "{colors.on-primary}"
    typography: "{typography.link}"
    rounded: "{rounded.pill}"
    padding: "{spacing.xs} {spacing.md}"
  best-route-card:
    base: stat-card
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    timeTypography: "{typography.display-md}"
    titleTypography: "{typography.heading-sm}"
    rounded: "{rounded.xl}"
    padding: "{spacing.xl}"
  route-card:
    base: feature-card-dark, game-rank-row
    backgroundColor: "{colors.surface-indigo}"
    textColor: "{colors.ink}"
    titleTypography: "{typography.link}"
    timeTypography: "{typography.body-lg}"
    rounded: "{rounded.lg}"
    padding: "{spacing.md}"
  mode-chain:
    base: badge
    backgroundColor: "수단 색 (2.4)"
    textColor: "수단 색의 글자 (2.4)"
    typography: "{typography.link-sm}"
    rounded: "{rounded.lg}"
    padding: "{spacing.xxs} {spacing.sm}"
  station-row:
    base: game-rank-row
    backgroundColor: "{colors.surface-onyx}"
    textColor: "{colors.ink}"
    typography: "{typography.link-sm}"
    rounded: "{rounded.md}"
    padding: "{spacing.xs} {spacing.sm}"
  leg-row:
    base: game-rank-row
    backgroundColor: "수단 색 (2.4)"
    textColor: "수단 색의 글자 (2.4)"
    subTextColor: "수단 색의 글자 (2.4)"
    typography: "{typography.link-sm}"
    rounded: "{rounded.md}"
    padding: "{spacing.xs} {spacing.sm}"
  position-chip:
    base: badge
    backgroundColor: "{colors.position-surface}"
    textColor: "{colors.position-text}"
    typography: "{typography.link-sm}"
    rounded: "{rounded.lg}"
    padding: "{spacing.xxs} {spacing.sm}"
  map-frame:
    backgroundColor: "{colors.surface-black}"
    rounded: "{rounded.lg}"
    padding: "{spacing.xxs}"
    lineColor: "수단 색 (2.4)"
  transfer-point:
    backgroundColor: "{colors.on-primary}"
    borderColor: "환승 뒤 수단 색 (2.4)"
    rounded: "{rounded.full}"
    size: "{spacing.md}"
    borderWidth: "{spacing.xxs}"
  button-primary:
    base: button-primary
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.link-lg}"
    rounded: "{rounded.sm}"
    padding: "{spacing.lg} {spacing.xl}"
  button-record:
    base: button-green
    backgroundColor: "{colors.green}"
    textColor: "{colors.ink-dark}"
    typography: "{typography.link-lg}"
    rounded: "{rounded.sm}"
    padding: "{spacing.lg} {spacing.xl}"
  button-ghost:
    base: button-ghost
    backgroundColor: "{colors.surface-indigo}"
    textColor: "{colors.ink}"
    typography: "{typography.link}"
    rounded: "{rounded.lg}"
    padding: "{spacing.md}"
  button-ghost-sm:
    base: button-ghost-sm
    backgroundColor: "{colors.surface-indigo}"
    textColor: "{colors.ink}"
    typography: "{typography.link-sm}"
    rounded: "{rounded.xs}"
    padding: "{spacing.sm} {spacing.md}"
  button-caution:
    base: button-primary
    backgroundColor: "{colors.caution}"
    textColor: "{colors.ink-dark}"
    typography: "{typography.link-lg}"
    rounded: "{rounded.sm}"
    padding: "{spacing.lg} {spacing.xl}"
  button-disabled:
    backgroundColor: "{colors.surface-onyx}"
    textColor: "{colors.ink-secondary}"
  icon-button:
    base: button-ghost-sm
    backgroundColor: "{colors.surface-indigo}"
    textColor: "{colors.ink}"
    rounded: "{rounded.full}"
    size: "{layout.touch-target}"
  badge-rank:
    base: badge
    backgroundColor: "{colors.magenta}"
    textColor: "{colors.ink-dark}"
    typography: "{typography.link-sm}"
    rounded: "{rounded.lg}"
    padding: "{spacing.xxs} {spacing.sm}"
  badge-caution:
    base: badge
    backgroundColor: "{colors.caution}"
    textColor: "{colors.ink-dark}"
    typography: "{typography.link-sm}"
    rounded: "{rounded.lg}"
    padding: "{spacing.xxs} {spacing.sm}"
  badge-neutral:
    base: badge
    backgroundColor: "{colors.surface-onyx}"
    textColor: "{colors.ink}"
    typography: "{typography.link-sm}"
    rounded: "{rounded.lg}"
    padding: "{spacing.xxs} {spacing.sm}"
  list-row:
    base: game-rank-row
    backgroundColor: "{colors.surface-indigo}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.md}"
    padding: "{spacing.sm} {spacing.md}"
  text-input:
    base: ex-auth-form-card
    backgroundColor: "{colors.surface-indigo}"
    textColor: "{colors.ink}"
    placeholderColor: "{colors.ink-secondary}"
    typography: "{typography.body}"
    rounded: "{rounded.lg}"
    padding: "{spacing.md}"
  modal:
    base: ex-modal-card
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    rounded: "{rounded.lg}"
    padding: "{spacing.xl}"
    shadow: "{elevation.float}"
  toast:
    base: ex-toast
    backgroundColor: "{colors.surface-indigo}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.lg}"
    padding: "{spacing.sm} {spacing.md}"
    shadow: "{elevation.float}"
  empty-state:
    base: ex-empty-state-card
    backgroundColor: "{colors.surface-indigo}"
    textColor: "{colors.ink}"
    captionTypography: "{typography.body}"
    rounded: "{rounded.xl}"
    padding: "{spacing.section} {spacing.xl}"
---

# 디자인 명세서

## 0. 문서 정보
| 항목 | 내용 |
|---|---|
| 상태 | 디자인 기준. 화면 목록과 화면별 명세는 `docs/masterplan.md`의 화면 설계 단계에서 작성 |
| 작성일 | 2026-10-19 |
| 토큰 원본 | `docs/design/DESIGN-discord.md` (Discord Analysis, version alpha). 수정하지 않고 보관 |
| 적용 범위 | 이 서비스의 모든 화면, 컴포넌트, 프론트엔드 코드 |
| 문서 구성 | 머리말(`---` 사이)은 실제 사용하는 토큰과 컴포넌트 값, 본문은 사용 규칙 |

- 사용 가능한 값은 이 문서 머리말에 있는 토큰뿐임. 원본 토큰 중 머리말에 없는 값은 사용하지 않음
- 원본과 이 문서가 다르면 이 문서를 따름. 원본과 달리 적용한 항목은 1.2에 기록
- 토큰, 컴포넌트를 추가하거나 바꿀 때는 사용자 확인 후 이 문서를 먼저 고치고 코드에 반영 (최상위 `CLAUDE.md` 6장)

### 0.1 토큰 구분
| 구분 | 내용 | 예 |
|---|---|---|
| 원본 토큰 | 원본 파일의 값을 그대로 사용 | `primary`, `spacing.md` |
| 사용자 지정 토큰 | 사용자가 직접 지정해 추가한 토큰 | `caution`, 수단 색(`mode-bike`, `subway-line2`, `bus-trunk` 등) |
| 파생 토큰 | 원본 토큰을 투명도, 조합으로 바꾼 토큰. 새로운 색은 만들지 않음 | `ink-secondary`, `caution-text`, `gradient-brand` |
| 라이트 토큰 | 라이트 모드에서 `colors`의 같은 이름 토큰 값을 바꾸는 색 (머리말 `colors-light`). 원본 토큰의 값이나 조합만 사용 | `colors-light.canvas`, `colors-light.ink` |

## 1. 개요

### 1.1 디자인 방향
- 원본의 바탕(깊은 인디고 `canvas`), 대표색(Blurple `primary`), 둥근 형태를 서비스의 시각 정체성으로 사용
- 원본은 큰 글자와 화려한 그라디언트로 분위기를 만드는 마케팅 페이지이고, 이 서비스는 출근 준비 중 몇 초 안에 읽고 결정하는 휴대폰 도구임
- 따라서 화면마다 가장 큰 요소는 장식이 아닌 "결정에 필요한 숫자"(늦어도 출발해야 할 시각, 예상 도착 시각)로 둠
- 수단(도보, 따릉이, PM, 지하철 노선, 버스 종류)마다 색을 하나씩 정해 지도 선, 수단 칩, 구간 행에서 같은 색으로 표시 (2.4)
- 기본 경로를 맨 위의 큰 카드로 두고, 다른 경로는 기본 경로와의 차이로 읽히게 함
- 강조색마다 의미를 하나씩 고정해, 색만 보고도 상태를 알 수 있게 함 (2.2)
- 화면 모드는 다크(기본)와 라이트 두 가지. 라이트 모드는 바탕, 면, 글자 색만 바꾸고 강조색, 수단 색, 형태, 배치는 다크와 같음 (2.5)

### 1.2 원본과 다르게 적용한 항목
| 항목 | 원본 | 이 서비스 | 이유 |
|---|---|---|---|
| 글꼴 | ABC Ginto Nord, ABC Ginto, ggsans | 모두 Pretendard | 원본 글꼴은 유료이고 대체 제안 글꼴에는 한글이 없음 (사용자 결정) |
| 대문자 표기 | 큰 제목은 모두 대문자 | 적용하지 않음 | 한글에는 대소문자가 없음 |
| 큰 제목 크기 | `display-xl` 82px, `display-lg` 62px 사용 | 사용하지 않음. 가장 큰 글자는 `display-md` 56px | 휴대폰 화면 너비에 맞지 않음 |
| 강조색 수 | Blurple, green, magenta 세 가지만, 네 번째 강조색 금지 | `caution`(#ffda33) 추가 | 주의 표현이 필요 (사용자 결정) |
| 수단 색 | 없음 | 도보, 따릉이, PM, 지하철 노선, 버스 종류별 색 추가 (2.4). 강조색이 아닌 수단 구분 전용 | 실제 노선 색과 같은 색으로 수단을 알아보게 함 (사용자 결정) |
| 화면 모드 | 다크 하나 (라이트용 바탕, 면, 글자 토큰 없음) | 다크, 라이트 두 가지. 라이트 색은 원본 토큰의 값이나 조합으로 만듦 (2.5) | 밝은 곳에서 읽기, 기기의 밝은 화면 설정에 맞춤 (사용자 결정) |
| 그라디언트 | 바탕 전체에 계속 움직이는 그라디언트 | 오늘의 추천 화면 머리 영역에만 움직이지 않는 그라디언트 | 매일 반복해서 보는 화면의 읽기 방해 최소화 |
| magenta 위 글자색 | 흰색 (`ink`) | 검정 (`ink-dark`) | 흰 글자는 magenta 위에서 대비 3.4:1로 작은 글자 기준(4.5:1) 미달. 검정은 6.2:1 |
| 큰 카드 안쪽 여백 | `stat-card` `spacing.xxl` 32px | `spacing.xl` 24px | 휴대폰 너비에서 내용 영역 확보 |
| 3D 캐릭터, 장식 소품 | 카드 밖으로 걸치는 3D 그림 | 사용하지 않음 | 정보 위주 도구 화면 |
| 원본 마케팅 컴포넌트 | `pricing-table`, `marquee-band`, `footer` 등 | 사용하지 않음 | 이 서비스에 해당 화면이 없음 |

## 2. 색

### 2.1 토큰과 역할
| 토큰 | 값 | 역할 |
|---|---|---|
| `canvas` | #0a0d3a | 모든 화면의 바탕 |
| `surface-indigo` | #1e2353 | 바탕 위 한 단계 올라온 면. 일반 경로 카드, 입력 칸, 목록 행, 보조 버튼 |
| `surface-onyx` | #23272a | 카드 안의 낮은 면. 대여소 행, 중립 배지, 비활성 버튼 |
| `surface-black` | #000000 | 지도를 담는 면 (`map-frame`, 권장 F-16) |
| `primary` | #5865f2 | 대표색. 기본 경로 카드, 주요 버튼, 선택 상태 |
| `on-primary` | #ffffff | `primary`, `gradient-brand`, 수단 색 위의 흰 글자, 지도 환승 지점 원. 두 화면 모드 모두 흰색 (2.5.4) |
| `green` | #35ed7e | 기록 버튼 전용 (권장 F-13 탑재 후 사용) |
| `magenta` | #ec48bd | 경로 종류 배지, 지도의 대여소 표시, 머리 영역 그라디언트 |
| `caution` | #ffda33 | 주의 전용. 재고 정보 없음, 입력 오류, 되돌릴 수 없는 작업의 확인. 배지, 버튼처럼 칠하는 면에 사용 |
| `caution-text` | 다크 `caution`과 같음 | 주의 글자와 아이콘. 바탕 위에 `caution`을 글자색으로 칠하지 않고 이 토큰을 씀 (라이트 값 2.5.2) |
| `link` | #00b0f4 | 본문 안의 글자 링크 |
| `ink` | #ffffff | 기본 글자 |
| `ink-secondary` | 흰색 70% | 보조 글자 (추천 이유, 안내 문구, 입력 칸 예시 문구) |
| `ink-dark` | #000000 | 밝은 면(`green`, `caution`, `magenta`, 밝은 수단 색) 위의 글자 |
| `muted` | #333333 | 흰 면 위의 보조 글자. 흰 면을 쓰는 경우에만 |
| `hairline` | #23272a | 구분선 |
| `pressed-overlay` | 검정 20% | 눌림 상태에서 면 위에 덮는 색 |
| `gradient-brand` | `primary` → `magenta` | 오늘의 추천 화면 머리 영역 배경 전용 |

### 2.2 강조색의 의미 고정
| 색 | 의미 | 쓰지 않는 곳 |
|---|---|---|
| `primary` | "서비스가 추천함", "지금 선택됨" | 경고, 오류 |
| `magenta` | "분류 표시" | 버튼, 경고, 수단 구분 |
| `caution` | "주의가 필요함" | 장식, 일반 강조, 큰 면의 배경 |
| `green` | "지금 누를 기록 행동" | 장식, 상태 표시, 기록 외 버튼. 첫 버전에는 쓰지 않음 |

- `caution`은 작은 면(배지, 버튼)에만, `caution-text`는 아이콘과 글자에만 사용. 카드 전체를 노랗게 칠하지 않음
- `green` 버튼은 기록 기능(권장 F-13) 탑재 후 한 화면에 하나만 둠

### 2.3 대비 기준
| 조합 | 대비 | 허용 |
|---|---|---|
| `ink` / `canvas` | 18.6:1 | 모든 글자 |
| `ink` / `surface-indigo` | 14.8:1 | 모든 글자 |
| `ink` / `surface-onyx` | 15.1:1 | 모든 글자 |
| `on-primary` / `primary` | 4.6:1 | 모든 글자 |
| `ink-dark` / `magenta` | 6.2:1 | 모든 글자 |
| `ink-dark` / `caution` | 15.3:1 | 모든 글자 |
| `ink-dark` / `green` | 13.6:1 | 모든 글자 |
| `on-primary` / `magenta` | 3.4:1 | 18px 이상 굵은 글자만 (머리 영역 그라디언트 위 제목) |
| `caution-text` / `canvas` | 13.6:1 | 주의 글자, 아이콘 |
| `position-text` / `position-surface` | 6.0:1 | 모든 글자 |
| 수단 색 / 그 색의 글자 (2.4) | 4.6:1 이상 | 모든 글자 |

- 글자는 4.5:1 이상, 18px 이상 굵은 글자(`heading-sm` 이상)는 3:1 이상
- 대비 값은 WCAG 대비 계산식 기준
- 위 표는 다크 모드 기준. 라이트 모드 대비는 2.5.3

### 2.4 수단 색
- 수단을 알아보게 하는 전용 색. 2.2의 강조색과 별개이며 수단 구분 외에는 쓰지 않음
- 쓰는 곳: 지도 경로 선, 수단 칩(`mode-chain`), 구간 행(`leg-row`) 바탕, 실시간 위치 행 바탕, 지도 환승 지점(`transfer-point`) 테두리
- 수단 색 위 글자는 `on-primary`(흰색), `ink-dark` 중 대비가 높은 쪽 (아래 표의 '글자'). 구간 행 둘째 줄부터도 같은 글자색이며 투명도를 주지 않음 (`ink-secondary`, 검정 70%는 여러 수단 색 위에서 4.5:1 미달)
- 표에 없는 노선, 종류는 `primary`, 글자는 `on-primary`
- 한 구간에 노선이 여러 개면 첫 번째 노선(`vehicles[0]`)의 색. 실시간 위치 행은 그 노선 자신의 색

#### 2.4.1 도보, 따릉이, PM, 위치 문구
| 토큰 | 값 | 쓰임 | 글자 | 대비 |
|---|---|---|---|---|
| `mode-walk` | #262626 | 도보 구간 | `on-primary` | 15.1:1 |
| `mode-bike` | #2edb8c | 따릉이 포함 경로의 따릉이 구간 | `ink-dark` | 11.6:1 |
| `mode-pm` | #9c9c9c | PM 전용 경로 | `ink-dark` | 7.7:1 |
| `position-surface` | #262626 | 위치 문구 칩(`position-chip`) 바탕 | - | - |
| `position-text` | #ff7a7a | 위치 문구 칩 글자 ("N역 전", "N정거장 전", "도착", "N분 후 도착 예정", "정보 없음") | - | 6.0:1 (`position-surface` 위) |

#### 2.4.2 지하철 노선
- 카카오 응답의 노선 이름(`vehicles[].name`)으로 고름. 카카오 `type`(일반, 급행)은 노선을 나타내지 않아 쓰지 않음
- 출처: IT 위키 '틀:한국 철도 노선색'(한국철도공사 철도 사인류 설치 기준 매뉴얼의 색 기준이라고 표기, https://www.itwiki.kr/w/틀:한국_철도_노선색/설명문서). 2026-10-21 확인
- '이름 확인'은 2026-10-21 카카오 대중교통 조회에서 그 노선 이름이 실제로 온 노선

| 토큰 | 값 | 노선 이름 | 글자 | 대비 | 이름 확인 |
|---|---|---|---|---|---|
| `subway-line1` | #0052a4 | 1호선 | `on-primary` | 7.7:1 | 확인 |
| `subway-line2` | #00a84d | 2호선 | `ink-dark` | 6.7:1 | 확인 |
| `subway-line3` | #ef7c1c | 3호선 | `ink-dark` | 7.6:1 | 확인 |
| `subway-line4` | #00a4e3 | 4호선 | `ink-dark` | 7.4:1 | 확인 |
| `subway-line5` | #996cac | 5호선 | `ink-dark` | 5.1:1 | 확인 |
| `subway-line6` | #cd7c2f | 6호선 | `ink-dark` | 6.5:1 | 미확인 |
| `subway-line7` | #747f00 | 7호선 | `ink-dark` | 4.8:1 | 확인 |
| `subway-line8` | #e6186c | 8호선 | `ink-dark` | 4.7:1 | 미확인 |
| `subway-line9` | #bdb092 | 9호선 | `ink-dark` | 9.8:1 | 확인 |
| `subway-gyeongui-jungang` | #77c4a3 | 경의중앙선 | `ink-dark` | 10.2:1 | 확인 |
| `subway-suin-bundang` | #f5a200 | 수인분당선 | `ink-dark` | 10.1:1 | 확인 |
| `subway-shinbundang` | #d4003b | 신분당선 | `on-primary` | 5.4:1 | 확인 |
| `subway-airport` | #0065b3 | 공항철도 | `on-primary` | 6.0:1 | 확인 |
| `subway-gyeongchun` | #0c8e72 | 경춘선 | `ink-dark` | 5.1:1 | 미확인 |
| `subway-gyeonggang` | #003da5 | 경강선 | `on-primary` | 9.5:1 | 확인 |
| `subway-seohae` | #8ec31f | 서해선 | `ink-dark` | 10.0:1 | 미확인 |
| `subway-ui-sinseol` | #b0ce18 | 우이신설선 | `ink-dark` | 11.7:1 | 미확인 |
| `subway-sillim` | #6789ca | 신림선 | `ink-dark` | 6.0:1 | 미확인 |
| `subway-gimpo-goldline` | #a17800 | 김포골드라인 | `ink-dark` | 5.2:1 | 미확인 |
| `subway-incheon1` | #7ca8d5 | 인천1호선 | `ink-dark` | 8.4:1 | 확인 |
| `subway-incheon2` | #ed8b00 | 인천2호선 | `ink-dark` | 8.3:1 | 확인 |
| `subway-uijeongbu` | #fda600 | 의정부경전철 | `ink-dark` | 10.6:1 | 미확인 |
| `subway-everline` | #509f22 | 에버라인, 용인에버라인 | `ink-dark` | 6.3:1 | 미확인 |
| `subway-gtx-a` | #9a6292 | GTX-A | `on-primary` | 4.6:1 | 확인 |

- 서해선은 출처 안에서 #8ec31f(기본값)와 #81a914(노선 기호 예시) 두 값이 있어 기본값 사용

#### 2.4.3 버스 종류
- 카카오 응답의 버스 종류(`vehicles[].type`)로 고름. 응답에 노선의 지역(서울, 경기, 인천)이 없어 지역은 구분하지 않음 (2026-10-21 사용자 결정)
- 출처: 리브레 위키 '틀:버스 노선색'(https://librewiki.net/wiki/틀:버스_노선색). 2026-10-21 확인
- 지역별 색 (출처 기준)
  | 지역 | 종류와 색 |
  |---|---|
  | 서울 | 간선 #0068b7, 지선 #53b332, 광역 #e60012, 순환 #f2b70a, 마을 #53b332, 심야 #3d5bab |
  | 경기 | 시내일반 #33cc99, 일반좌석 #0068b7, 직행좌석 #e60012, 경기순환 #e60012, 마을 #ffc600 |
  | 인천 | 간선 #0068b7, 지선 #53b332, 광역 #e60012, 급행간선 #5112ab, 시내좌석 #3d5bab, 공항좌석 #3d5bab |
- 카카오 종류 값별 색. '값 확인'은 2026-10-21 서울, 경기, 인천 10개 구간 카카오 대중교통 조회에서 실제로 온 값

| 토큰 | 값 | 카카오 종류 | 근거 | 글자 | 대비 | 값 확인 |
|---|---|---|---|---|---|---|
| `bus-trunk` | #0068b7 | 간선 | 서울, 인천 간선 (같은 색) | `on-primary` | 5.7:1 | 확인 |
| `bus-branch` | #53b332 | 지선 | 서울, 인천 지선 (같은 색) | `ink-dark` | 7.9:1 | 확인 |
| `bus-village` | #53b332 | 마을 | 서울 마을. 경기 마을(#ffc600)과 구분하지 않음 (사용자 결정) | `ink-dark` | 7.9:1 | 확인 |
| `bus-wide` | #e60012 | 광역 | 서울, 인천 광역 | `on-primary` | 4.8:1 | 확인 |
| `bus-direct` | #e60012 | 직행 | 경기 직행좌석 | `on-primary` | 4.8:1 | 확인 |
| `bus-rapid` | #e60012 | 급행 | 광역, 직행과 같은 색 (사용자 결정) | `on-primary` | 4.8:1 | 확인 |
| `bus-general` | #33cc99 | 일반 | 경기 시내일반 | `ink-dark` | 10.2:1 | 확인 |
| `bus-seat` | #0068b7 | 좌석 | 경기 일반좌석. 인천 시내좌석(#3d5bab)과 구분하지 않음 | `on-primary` | 5.7:1 | 확인 |
| `bus-circular` | #f2b70a | 순환 | 서울 순환 | `ink-dark` | 11.6:1 | 미확인 |
| `bus-airport` | #3d5bab | 공항 | 인천 공항좌석 | `on-primary` | 6.4:1 | 미확인 |
| `bus-night` | #3d5bab | 심야 | 서울 심야 | `on-primary` | 6.4:1 | 미확인 |

### 2.5 라이트 모드

#### 2.5.1 화면 모드 정하기
| 설정 값 | 적용하는 모드 |
|---|---|
| 기기 설정 따름 (기본) | 기기가 밝은 화면 설정이면 라이트, 그 외에는 다크 |
| 라이트 | 라이트 |
| 다크 | 다크 |

- 설정 화면(SC-02)의 "화면 모드"에서 고름 (`screen-settings.md` 3.6). 저장 형식은 `frontend/CLAUDE.md` 4.3 `theme`
- 기기 설정 따름 상태에서 앱을 연 채 기기 설정이 바뀌면 화면도 바로 따라 바뀜
- 기기가 밝기 설정을 알려 주지 않으면 다크
- 라이트 모드는 색만 바꿈. 글자, 간격, 모서리, 그림자, 컴포넌트 구성, 배치는 두 모드가 같음

#### 2.5.2 라이트 토큰
- 머리말 `colors-light`의 값. 라이트 모드에서 `colors`의 같은 이름 토큰 값을 이 값으로 바꿈

| 토큰 | 다크 값 | 라이트 값 | 만든 방법 | 역할 (2.1과 같음) |
|---|---|---|---|---|
| `canvas` | #0a0d3a | #ffffff | 원본 흰색 (`on-primary` 값) | 모든 화면의 바탕 |
| `surface-indigo` | #1e2353 | #ebedfd | `primary` 12% + 흰색 | 바탕 위 한 단계 올라온 면 |
| `surface-onyx` | #23272a | #e6e6e6 | `ink-dark` 10% + 흰색 | 카드 안의 낮은 면, 비활성 버튼 |
| `surface-black` | #000000 | #e6e6e6 | 라이트 `surface-onyx`와 같은 값 | 지도를 담는 면 |
| `hairline` | #23272a | #e6e6e6 | 다크와 같은 방식 (`hairline` = `surface-onyx`) | 구분선 |
| `ink` | #ffffff | #0a0d3a | 다크 `canvas` 값 | 기본 글자 |
| `ink-secondary` | 흰색 70% | #0a0d3a 70% | 다크와 같은 방식 (`ink` 70%) | 보조 글자 |
| `link` | #00b0f4 | #006a92 | `link` 60% + `ink-dark` | 본문 안의 글자 링크 |
| `caution-text` | #ffda33 | #736217 | `caution` 45% + `ink-dark` | 주의 글자, 아이콘 |

- 표에 없는 색은 두 모드에서 같은 값
  - 강조색: `primary`, `magenta`, `green`, `caution`
  - 글자: `on-primary`, `ink-dark`, `muted`
  - 수단 색 전체 (2.4). 수단 칩, 구간 행은 수단 색을 칠한 면이고 글자색도 그 면 위에서 정하므로 바탕이 바뀌어도 대비가 같음
  - `position-surface`, `position-text`, `pressed-overlay`, `gradient-brand`
- 깊이 표현(6.1)은 라이트에서도 면의 색으로 함. `canvas`(흰색) → `surface-indigo`(옅은 인디고) → `primary` 순서
- 라이트 모드의 보조 글자도 `ink-secondary`. `muted`의 쓰임은 바꾸지 않음

#### 2.5.3 라이트 모드 대비
| 조합 | 대비 | 허용 |
|---|---|---|
| `ink` / `canvas` | 18.6:1 | 모든 글자 |
| `ink` / `surface-indigo` | 16.0:1 | 모든 글자 |
| `ink` / `surface-onyx` | 14.9:1 | 모든 글자 |
| `ink-secondary` / `canvas` | 7.1:1 | 모든 글자 |
| `ink-secondary` / `surface-indigo` | 6.6:1 | 모든 글자 |
| `ink-secondary` / `surface-onyx` | 6.4:1 | 모든 글자 (비활성 버튼 글자 포함) |
| `link` / `canvas` | 6.0:1 | 모든 글자 |
| `link` / `surface-indigo` | 5.2:1 | 모든 글자 |
| `link` / `surface-onyx` | 4.8:1 | 모든 글자 |
| `caution-text` / `canvas` | 6.0:1 | 주의 글자, 아이콘 |
| `caution-text` / `surface-indigo` | 5.2:1 | 주의 글자, 아이콘 |
| `caution-text` / `surface-onyx` | 4.8:1 | 주의 글자, 아이콘 |
| `ink` / `pressed-overlay`를 덮은 `surface-indigo` | 10.0:1 | 모든 글자 |
| 라이트 `ink` / `primary` | 4.0:1 | 사용하지 않음. `primary` 위 글자는 항상 `on-primary` |
| `caution` / `canvas` | 1.3:1 | 사용하지 않음. 주의 글자는 `caution-text` |

- `primary`, `magenta`, `caution`, `green`, 수단 색 위 글자의 대비는 2.3, 2.4와 같음 (두 모드에서 값이 같음)
- 초점 표시(`layout.focus-ring`)는 라이트에서 `ink`(#0a0d3a)가 되며, `canvas`, `surface-indigo`, `primary` 모두에서 3:1 이상

#### 2.5.4 두 모드에서 흰색으로 두는 곳
- `ink`는 라이트에서 어두운 색이 되므로, 바탕과 관계없이 흰색이어야 하는 곳은 `ink` 대신 `on-primary`를 씀

| 위치 | 토큰 | 이유 |
|---|---|---|
| `primary` 면 위 글자 (기본 경로 카드, `button-primary`, 선택된 `direction-toggle` 칸) | `on-primary` | 라이트 `ink`는 `primary` 위에서 4.0:1 |
| 머리 영역 그라디언트(`header-gradient`) 위 글자 | `on-primary` | 그라디언트 위에는 흰 글자만 둠 (6.2) |
| 수단 색 위 흰 글자 (2.4 표의 '글자'가 `on-primary`인 수단) | `on-primary` | 수단 색은 두 모드에서 같으므로 글자도 같아야 함 |
| 지도 환승 지점(`transfer-point`) 원 | `on-primary` | 카카오 지도 그림은 화면 모드와 관계없이 밝음 |

- 다크에서는 `ink`와 `on-primary`가 모두 #ffffff이므로 이 표를 적용해도 다크 화면은 달라지지 않음

#### 2.5.5 구현 기준
- `tools/build_tokens.py`가 `colors-light`를 읽어 `frontend/css/tokens.css`에 아래 세 블록을 만듦 (`tech_stack.md` 5장)

  | 블록 | 내용 | 적용 조건 |
  |---|---|---|
  | `:root` | 지금과 같은 모든 토큰(다크 값) + `color-scheme: dark` | 항상 |
  | `@media (prefers-color-scheme: light)` 안의 `:root:not([data-theme='dark'])` | `colors-light` 토큰 + `color-scheme: light` | 기기가 밝은 화면 설정이고 다크를 직접 고르지 않았을 때 |
  | `:root[data-theme='light']` | `colors-light` 토큰 + `color-scheme: light` | 라이트를 직접 골랐을 때 |

  - 라이트 블록의 변수 이름은 `colors`와 같음 (예: `colors-light.canvas` → `--colors-canvas`). `colors`에 없는 이름이 `colors-light`에 있으면 오류로 끝남
  - `color-scheme`은 시각 고르기 창 등 휴대폰 기본 입력 창의 밝기를 화면 모드에 맞추는 CSS 속성. 토큰이 아니며 이 세 블록에만 둠
- 화면 쪽은 `<html>`의 `data-theme` 속성만 바꿈
  | 저장 값 (`theme`) | `data-theme` |
  |---|---|
  | `null` (기기 설정 따름) | 붙이지 않음 |
  | `light` | `light` |
  | `dark` | `dark` |
- 컴포넌트 CSS는 지금처럼 `var(--colors-...)`만 쓰고 화면 모드별 CSS를 따로 두지 않음
- 앱을 열 때 저장 값을 읽어 `data-theme`을 붙이기 전까지 기기 설정의 모드로 잠깐 보일 수 있으며, 이를 허용함 (2026-10-21 사용자 결정)
- 카카오 지도 그림은 화면 모드에 따라 바꾸지 않음. 지도 선 색(수단 색)과 환승 지점(2.5.4)도 두 모드가 같음

## 3. 글자

### 3.1 글꼴
- 한글, 영문, 숫자 모두 Pretendard 하나만 사용
- 굵기는 토큰 값(700, 500, 400)만 사용
- 시각, 분 등 숫자는 고정폭 숫자로 표시해 시각이 바뀌어도 글자 위치가 흔들리지 않게 함

### 3.2 크기와 용도
| 토큰 | 크기, 굵기 | 이 서비스의 용도 |
|---|---|---|
| `display-md` | 56px, 700 | 기본 경로 카드의 "늦어도 출발해야 할 시각" 숫자. 화면에서 가장 큰 글자는 이것 하나 |
| `heading-lg` | 48px, 700 | 사용 예약 (기록 기능 탑재 후 이동 중 표시) |
| `heading-sm` | 22px, 700 | 화면 제목, 기본 경로 카드의 총 소요 시간, 모달 제목 |
| `body-lg` | 20px, 500 | 다른 경로 카드의 총 소요 시간, 기본 경로 카드의 예상 도착 시각 |
| `link-lg` | 18px, 500 | 큰 버튼 글자 (저장, 확인, 다시 시도) |
| `body` | 16px, 400 | 본문, 추천 이유, 목록 행, 입력 칸 |
| `link` | 16px, 500 | 일반 버튼 글자, 출근 퇴근 전환 |
| `link-sm` | 14px, 500 | 수단 칩, 배지, 대여소 행, 보조 안내 |

- 원본의 `display-xl`(82px), `display-lg`(62px)는 사용하지 않음
- 14px(`link-sm`)보다 작은 글자는 사용하지 않음

### 3.3 위계 원칙
- 한 카드 안에서 시각, 소요 시간 > 수단 구성 > 추천 이유 순으로 크기 차이를 둠
- 큰 숫자와 본문의 굵기 차이(700 → 400)를 크게 두어 숫자가 먼저 읽히게 함

## 4. 간격과 배치

### 4.1 간격 용도
| 토큰 | 값 | 용도 |
|---|---|---|
| `spacing.xxs` | 4px | 배지, 칩 위아래 안쪽 여백, 아이콘과 글자 사이 |
| `spacing.xs` | 8px | 같은 카드 안 줄 사이, 수단 칩 사이 |
| `spacing.sm` | 12px | 카드와 카드 사이, 목록 행 위아래 여백 |
| `spacing.md` | 16px | 화면 좌우 여백, 일반 카드 안쪽 여백 |
| `spacing.lg` | 20px | 큰 버튼 위아래 안쪽 여백 |
| `spacing.xl` | 24px | 기본 경로 카드, 모달 안쪽 여백, 큰 버튼 좌우 안쪽 여백 |
| `spacing.xxl` | 32px | 화면 안 구역과 구역 사이 |
| `spacing.section` | 40px | 빈 상태 화면 위아래 여백 |

### 4.2 화면 배치
- 휴대폰 세로 화면 기준 단일 열
- 화면 좌우 여백은 `spacing.md`
- 화면 너비가 `layout.mobile-max`(767px)를 넘으면 콘텐츠 열의 너비를 767px로 고정하고 가운데 정렬. 바깥은 `canvas`
- 주요 행동 버튼은 엄지가 닿는 화면 아래쪽에 둠

### 4.3 터치 영역
- 누를 수 있는 모든 요소는 가로, 세로 `layout.touch-target`(44px) 이상
- 버튼끼리는 `spacing.xs` 이상 떨어뜨림

## 5. 모양
| 토큰 | 값 | 용도 |
|---|---|---|
| `rounded.xs` | 6px | 작은 보조 버튼 (`button-ghost-sm`) |
| `rounded.sm` | 12px | 큰 버튼 (`button-primary`, `button-caution`) |
| `rounded.md` | 14px | 목록 행, 대여소 행 |
| `rounded.lg` | 16px | 일반 카드, 입력 칸, 배지, 수단 칩, 모달, 알림 띠 |
| `rounded.xl` | 40px | 기본 경로 카드, 빈 상태 |
| `rounded.pill` | 50px | 출근 퇴근 전환 |
| `rounded.full` | 9999px | 원형 아이콘 버튼 |

- 각진 모서리는 사용하지 않음 (원본 규칙 유지)

## 6. 깊이와 움직임

### 6.1 깊이
| 단계 | 값 | 사용처 |
|---|---|---|
| 평면 | `elevation.flat` | 모든 카드, 행, 버튼 |
| 떠 있음 | `elevation.float` | 모달, 알림 띠처럼 다른 내용 위에 겹치는 면만 |

- 깊이는 그림자보다 면의 색(`canvas` → `surface-indigo` → `primary`)으로 표현 (원본 규칙 유지)

### 6.2 그라디언트
- `gradient-brand`는 오늘의 추천 화면 머리 영역(`header-gradient`) 배경에만 사용
- 움직이지 않음
- 그라디언트 위에는 `heading-sm` 이상 굵은 흰 글자(`on-primary`)만 둠 (2.3 대비 기준, 2.5.4)

### 6.3 움직임
- 화면 전환, 카드 순서 변경 등 상태 변화를 알리는 짧은 움직임만 사용
- 기기의 움직임 줄이기 설정이 켜져 있으면 움직임 없이 바로 바뀜
- 장식용으로 계속 움직이는 요소는 사용하지 않음

## 7. 컴포넌트
- 각 컴포넌트의 값은 머리말 `components` 참조. `base`는 바탕이 된 원본 컴포넌트
- 상태: 기본, 눌림(`pressed-overlay`를 덮음), 비활성(`button-disabled`), 초점(`layout.focus-ring`, 바깥쪽 2px 띄움)

### 7.1 화면 틀
| 컴포넌트 | 원본 | 내용 | 사용 규칙 |
|---|---|---|---|
| `top-bar` | `nav-bar` | 화면 제목, 뒤로 가기, 오른쪽 아이콘 버튼 | 오늘의 추천 외 모든 화면 |
| `header-gradient` | `hero` | 오늘의 추천 화면 머리 영역. 방향(예: "집 → 회사"), 출근 퇴근 전환, 목표 도착 시각 | 오늘의 추천 화면에만 사용 |
| `direction-toggle` | `button-ghost-sm` | 출근, 퇴근 두 칸 전환. 선택된 칸만 `primary` | 오늘의 추천 머리 영역 (F-02) |

### 7.2 추천 카드
| 컴포넌트 | 원본 | 내용 | 사용 규칙 |
|---|---|---|---|
| `best-route-card` | `stat-card` | 기본 경로 전용. `badge-rank`("기본 경로"), 늦어도 출발 시각(`display-md`), 총 소요 시간(`heading-sm`), 예상 도착 시각(`body-lg`), `mode-chain`, 추천 이유(`body`), PM 절감 시간 `badge-neutral`("공유 모빌리티 탑승 시 N분 단축됩니다") | 항상 맨 위에 하나 |
| `route-card` | `feature-card-dark`, `game-rank-row` | `badge-rank`(경로 종류: "따릉이 포함", "버스 전용", "PM 전용"), 총 소요 시간(`body-lg`), 기본 경로와의 차이 `badge-neutral`, 늦어도 출발 시각(`link`), `mode-chain`, 추천 이유 한 줄(`link-sm`, `ink-secondary`), 따릉이 구간이 있으면 `station-row` | 기본 경로 아래, 총 소요 시간이 짧은 순 (`rules.md` 8장) |
| `mode-chain` | `badge` | 수단 칩을 화살표로 이은 줄 (예: [따릉이 8분] → [2호선] → [도보 5분]). 칩마다 수단 색 바탕에 그 색의 글자 (2.4) | 모든 추천 카드 |
| `station-row` | `game-rank-row` | 대여 대여소 이름, 대여소까지 도보 분, 대여 가능 대수 / 반납 대여소 이름 | 따릉이 포함 경로 카드 (`scenario.md` R-2) |
| `leg-row` | `game-rank-row` | 구간 하나의 세부. 행 전체를 수단 색으로 칠하고 글자는 그 색의 글자 (2.4). 첫 줄은 구간 종류 아이콘과 수단 이름, 둘째 줄부터 정류장, 시간, 거리 | 펼친 추천 카드(권장 F-15), 경로 지도 화면의 범례(권장 F-16) |
| `position-chip` | `badge` | 실시간 위치 행(`leg-row`) 안의 위치 문구 ('3역 전' 등). `position-surface` 바탕에 `position-text` 글자. 위치 행 바탕은 안내 대상 노선의 수단 색 | 버스, 지하철 구간 아래 위치 행 (권장 F-26) |

- PM 전용 경로 카드의 추천 이유에는 대여, 반납, 재고를 반영하지 않은 자전거 길 기준임을 밝힘 (`scenario.md` R-1)
- 수단 칩에는 구간 종류 아이콘과 글자(노선 이름, 분)를 함께 둠. 색만으로 구분하지 않음
- 추천 카드는 누르면 아래로 펼쳐져 `leg-row` 목록과 `button-ghost-sm`("지도 보기")을 보여 줌 (권장 F-15). 펼침 여부는 화면 낭독기에 알림

### 7.3 버튼
| 컴포넌트 | 원본 | 용도 |
|---|---|---|
| `button-primary` | `button-primary` | 저장, 확인, 다시 시도 등 화면의 주요 행동 |
| `button-ghost` | `button-ghost` | 취소, 장소 수정 등 보조 행동 |
| `button-ghost-sm` | `button-ghost-sm` | 카드 안의 작은 행동 |
| `icon-button` | `button-ghost-sm` | 아이콘만 있는 원형 버튼. 새로고침, 설정, 뒤로 가기. 화면 낭독기용 이름 필수 (9장) |
| `button-caution` | 사용자 지정 | 되돌릴 수 없는 작업의 마지막 확인 버튼 (저장 정보 모두 지우기 F-12, 장소 삭제) |
| `button-record` | `button-green` | 기록 버튼 전용. 권장 F-13 탑재 후 사용 |

- 버튼 글자는 행동을 그대로 씀 (예: "저장", "모두 지우기")
- 되돌릴 수 없는 작업은 첫 버튼을 `button-ghost`로 두고, 확인 모달 안의 마지막 버튼만 `button-caution`

### 7.4 배지
| 컴포넌트 | 용도 | 예 |
|---|---|---|
| `badge-rank` | 경로 종류 | "기본 경로", "따릉이 포함", "버스 전용", "PM 전용" |
| `badge-caution` | 주의 상태 | "재고 정보가 없습니다", "운행 시간 정보가 없습니다" |
| `badge-neutral` | 정보 상태, 비교 | "공유 모빌리티 탑승 시 7분 단축됩니다", "기본 경로보다 6분 빠릅니다", "N분 전 정보" |

### 7.5 입력과 목록
| 컴포넌트 | 원본 | 용도 |
|---|---|---|
| `text-input` | `ex-auth-form-card` | 주소 검색어, 장소 이름 |
| `list-row` | `game-rank-row` | 주소 검색 후보, 설정 항목 |

- 주소 후보 행에는 도로명 주소를 첫 줄(`body`), 지번 주소와 건물 이름을 둘째 줄(`link-sm`, `ink-secondary`)에 둠
- 입력 칸 아래 안내 문구는 `link-sm`, `ink-secondary`. 입력 오류는 `caution-text` 아이콘과 `caution-text` 글자

### 7.6 겹치는 면과 빈 상태
| 컴포넌트 | 원본 | 용도 |
|---|---|---|
| `modal` | `ex-modal-card` | 확인 창, 선택 목록(바텀 시트) |
| `toast` | `ex-toast` | "불러오지 못함, 다시 시도" 등 짧은 알림. 화면 아래쪽, 몇 초 뒤 사라짐 |
| `empty-state` | `ex-empty-state-card` | 장소가 등록되지 않았을 때 오늘의 추천 화면. 안내 문구와 `button-primary`("장소 등록") |

### 7.7 지도 (권장 F-16)
| 컴포넌트 | 원본 | 용도 |
|---|---|---|
| `map-frame` | 사용자 지정 | 카카오 지도를 담는 면. `surface-black` 바탕, `rounded.lg`, 안쪽 여백 `spacing.xxs` |

- 지도 위 선 색은 수단 색 (2.4)
  | 구간 | 선 |
  |---|---|
  | 버스, 지하철 | 노선의 수단 색 실선 |
  | 따릉이 | `mode-bike` 실선 |
  | PM 전용 경로 | `mode-pm` 실선 |
  | 도보 | `mode-walk` 점선 |
- 지도 위 표시: 출발지, 도착지는 `badge-neutral`("출발", "도착"), 따릉이 대여소는 `badge-rank`("대여", "반납")
- 선 색은 토큰의 CSS 변수 값을 읽어 지도에 넘김
- 수단이 바뀌는 지점(환승 지점)마다 `transfer-point`: `on-primary`(흰색) 바탕 원에 환승 뒤 수단 색 테두리. 두 화면 모드에서 같음. 출발지, 도착지에는 두지 않음
- 선 굵기와 지도 영역의 가로세로 비율은 토큰 범주(색, 글자, 간격, 모서리, 그림자) 밖의 값으로 화면 명세(`screen-map.md`)에서 정함

## 8. 서비스 상태별 표현
| 상태 | 표현 | 관련 기능 |
|---|---|---|
| 기본 경로 | `best-route-card` | F-03, F-08 |
| PM 절감 시간 | 기본 경로 카드의 `badge-neutral`("공유 모빌리티 탑승 시 N분 단축됩니다"). 1분 미만이면 표시하지 않음 | F-04 |
| 따릉이 포함, 버스 전용, PM 전용 경로 | `route-card` + 경로 종류 `badge-rank` | F-05 ~ F-08 |
| 수단 구분 | `mode-chain` 칩, `leg-row`, 지도 선의 수단 색 (2.4) | F-03 ~ F-08, F-15, F-16 |
| 따릉이 대여소 | `station-row` | F-05 |
| 따릉이 포함, 버스 전용 경로가 없음 | 카드를 만들지 않음. 빈 자리 안내 없음 | F-05, F-06 |
| 재고 정보 없음 | 따릉이 포함 카드에 `badge-caution`("재고 정보가 없습니다") | F-11 |
| 운행 시간 정보 없음 | 해당 카드에 `badge-caution`("운행 시간 정보가 없습니다") | F-03, F-06 |
| 운행 중인 대중교통 없음 | 기본 경로 자리에 `empty-state` 모양으로 "운행 중인 대중교통이 없습니다"와 `button-primary`("다시 시도"). PM 전용 경로가 있으면 그 아래 표시 | F-03, F-11 |
| 출발 시각이 지남 | 늦어도 출발 시각 자리에 "지금 출발하면 HH:MM 도착". 주의 배지 없음 | F-10 |
| 목표 시각 미설정 | 늦어도 출발 시각 자리에 "지금 출발하면 HH:MM 도착" | F-10 |
| 불러오는 중 | 카드 자리에 같은 모양의 `surface-indigo` 면을 먼저 표시하고 내용만 나중에 채움 | F-03 |
| 불러오기 실패 (이전 결과 있음) | 이전 결과 유지 + `badge-neutral`("N분 전 정보") + `toast` | F-11 |
| 대중교통 경로 없음, 불러오기 실패 (이전 결과 없음) | 기본 경로 자리에 `empty-state` 모양으로 "경로를 찾지 못했습니다" 안내와 `button-primary`("다시 시도"). PM 전용 경로가 있으면 그 아래 표시 | F-11 |
| 장소 미등록 | `empty-state` | F-01 |
| 경로 구간 세부 | 펼친 추천 카드의 `leg-row` 목록 | F-15 |
| 경로 지도 | `map-frame`. 지도를 불러오지 못하면 지도 자리에 안내 문구와 `leg-row` 목록만 표시 | F-16 |
| 되돌릴 수 없는 작업 확인 | `modal` + `button-caution` | F-12 |

- 상태는 색만으로 구분하지 않고 항상 글자(배지 문구)를 함께 둠

## 9. 아이콘
- 아이콘은 선 아이콘 한 종류로 통일하고 색은 주변 글자 색을 따름
- 구간 종류 아이콘 5개(도보, 버스, 지하철, 따릉이, 킥보드)는 모든 화면에서 같은 모양 사용
- 아이콘만 있는 버튼은 `rounded.full`, 터치 영역 44px 이상, 화면 낭독기용 이름을 붙임
- 지하철 호선, 버스 종류는 수단 색(2.4)과 함께 노선 이름을 글자로 표시. 색만으로 구분하지 않음

## 10. 문구 원칙
- 짧고 바로 행동할 수 있게 씀. 원본처럼 소리치는 표현은 쓰지 않음
- 시각은 24시간제 "07:45", 시간 길이는 "52분"
- 추천 이유는 사실을 먼저 씀 (예: "첫 구간 도보 14분 → 따릉이 5분", "대여소 자전거 3대")
- 버튼 글자는 동사 하나 또는 짧은 구 (예: "저장", "다시 시도", "장소 등록")

## 11. 지켜야 할 것과 하지 말 것

### 11.1 지켜야 할 것
- 모든 화면의 바탕은 `canvas`
- 화면에서 가장 큰 글자는 결정에 필요한 숫자 하나
- 강조색은 2.2의 의미로만 사용
- 수단은 어느 화면에서든 같은 수단 색(2.4)으로 표시
- 상태는 색과 글자를 함께 써서 표시
- 바탕과 관계없이 흰색이어야 하는 글자, 원은 `on-primary` (2.5.4)
- 누를 수 있는 요소는 44px 이상

### 11.2 하지 말 것
- 머리말에 없는 색, 크기, 간격, 모서리, 그림자 값을 사용하지 않음
- 바탕을 회색이나 검정으로 바꾸지 않음
- `magenta`를 분류 표시 외에 쓰지 않음
- 수단 색을 수단 구분 외에 쓰지 않음
- `caution`을 넓은 면이나 장식에 쓰지 않음
- `caution`을 글자색으로 쓰지 않음. 주의 글자, 아이콘은 `caution-text`
- 화면 모드별로 컴포넌트 CSS를 따로 만들지 않음. 화면 모드에 따른 차이는 라이트 토큰(2.5.2)으로만 표현
- 강조색을 추가하지 않음 (Blurple, green, magenta, caution 네 가지로 끝. 수단 색은 강조색이 아님)
- 각진 모서리를 쓰지 않음
- 계속 움직이는 장식을 쓰지 않음

## 12. 결정 이력
| 날짜 | 결정 | 근거 |
|---|---|---|
| 2026-10-19 | 외부 디자인 토큰은 `DESIGN-discord.md` 하나만 사용 | 사용자 지정 |
| 2026-10-19 | 글꼴은 Pretendard 단일 | 사용자 결정 |
| 2026-10-19 | 주의 색 `caution` #ffda33 추가 | 사용자 결정. 원본의 강조색 추가 금지 규칙에 대한 예외 |
| 2026-10-19 | 그라디언트는 오늘의 추천 화면 머리 영역에만, 움직이지 않음 | 매일 반복해서 보는 화면의 읽기 방해 최소화 |
| 2026-10-19 | PM 구간 표시는 `magenta` 칩 | 이 서비스의 차별점을 모든 카드에서 같은 방식으로 구분 |
| 2026-10-20 | PM 절감 시간 문구 "공유 모빌리티 탑승 시 N분 단축됩니다" | 사용자 결정 (`scenario.md` R-6) |
| 2026-10-20 | `icon-button` 컴포넌트 추가 | 사용자 확인. 화면 명세(`screens.md` 4장)에서 필요 |
| 2026-10-20 | 출발 시각이 지나도 늦는 시간을 표시하지 않고 "지금 출발하면 HH:MM 도착"만 표시 | 사용자 결정. 지난 일에 대한 부정적인 문구 제외 |
| 2026-10-20 | `leg-row`, `map-frame` 컴포넌트와 지도 선 색 규칙 추가 | 사용자 확인. 권장 F-15, F-16 |
| 2026-10-21 | 수단 색 추가 (2.4): 지하철 노선별, 버스 종류별, 따릉이 #2edb8c, PM #9c9c9c, 도보 #262626. 지도 선, 수단 칩, 구간 행에 적용하고 PM 구간의 `magenta` 칩은 수단 색으로 대체 | 사용자 결정 |
| 2026-10-21 | 버스 색은 카카오 버스 종류 값으로만 고르고 지역은 구분하지 않음. 마을은 서울 마을 색, 급행은 광역, 직행과 같은 색 | 사용자 결정. 응답에 노선 지역이 없음 |
| 2026-10-21 | 수단 색 위 글자는 `ink`, `ink-dark` 중 대비가 높은 쪽 | 사용자 결정 |
| 2026-10-21 | 표에 없는 노선, 버스 종류는 `primary` | 사용자 결정 |
| 2026-10-21 | 실시간 위치 행 바탕은 안내 대상 노선의 수단 색, 위치 문구는 `position-chip`(#262626 바탕, #ff7a7a 글자) | 사용자 결정 |
| 2026-10-21 | 지도 환승 지점에 `transfer-point` 원 표시 | 사용자 결정 |
| 2026-10-21 | 라이트 모드 추가. 기본은 기기 설정 따름, 설정 화면에서 라이트, 다크 직접 선택 가능 | 사용자 결정 |
| 2026-10-21 | 라이트 토큰(`colors-light`)은 원본 토큰의 값이나 조합으로 만든 2.5.2의 값. 수단 색은 두 모드에서 같음 | 사용자 확인 |
| 2026-10-21 | 주의 글자, 아이콘용 `caution-text` 추가 (다크 `caution`과 같음, 라이트 #736217) | 사용자 확인. 흰 바탕 위 `caution` 글자는 1.3:1 |
| 2026-10-21 | 흰색이어야 하는 곳(`primary`, 그라디언트, 수단 색 위 흰 글자, 환승 지점 원)은 `ink` 대신 `on-primary` | 사용자 확인. 라이트 `ink`는 어두운 색 |
| 2026-10-21 | 앱을 열 때 기기 설정 모드로 잠깐 보이는 깜빡임을 막지 않음 | 사용자 결정. localStorage는 `storage.js`만 읽는 규칙 유지 |
