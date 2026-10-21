// 화면 쪽 규칙의 기본값 (rules.md 12장)
// - 값을 바꿀 때는 rules.md 12장 표를 먼저 고친 뒤 이 파일을 맞춤
// - 서버 쪽 기본값(따릉이 조건, 대여소 반경, 승차 대기 시간 등)은 backend/app/config.py

// 출근, 퇴근 전환 기준 시각 (rules.md 9장). 24시간제 'HH:MM'
export const DIRECTION_SWITCH_TIME = '14:00';

// 출발 시각 여유 시간 기본값, 초 단위 (rules.md 11.2). 사용자가 설정에서 바꿈
export const MARGIN_SECONDS = 600;
