// 출발 시각, 예상 도착 시각과 분 단위 처리 (rules.md 2장, 11.2)
// - 지금 시각은 인자로 받음. 함수 안에서 시각을 읽지 않음
// - 계산은 초 단위로 하고, 화면에 보이는 값만 분 단위로 바꿈

import { MARGIN_SECONDS } from './defaults.js';

const MINUTE_MS = 60 * 1000;

// 소요 시간을 분으로. 실제보다 빠르게 보이지 않도록 올림
export function ceilMinutes(seconds) {
  return Math.ceil(seconds / 60);
}

// 줄어드는 시간을 분으로. 실제보다 크게 보이지 않도록 버림
export function floorMinutes(seconds) {
  return Math.floor(seconds / 60);
}

// 'HH:MM' 문자열을 시, 분 숫자로. 형식이 틀리면 null
export function parseClock(text) {
  const match = /^(\d{2}):(\d{2})$/.exec(text ?? '');
  if (!match) {
    return null;
  }
  const hours = Number(match[1]);
  const minutes = Number(match[2]);
  if (hours > 23 || minutes > 59) {
    return null;
  }
  return { hours, minutes };
}

// now와 같은 날의 'HH:MM' 시각 (기기 시간대 기준, 0초)
export function clockOnDate(now, text) {
  const clock = parseClock(text);
  if (!clock) {
    return null;
  }
  const date = new Date(now.getTime());
  date.setHours(clock.hours, clock.minutes, 0, 0);
  return date;
}

// 시각을 분 단위로 버림. 초, 밀리초를 0으로 만든 새 Date
export function floorToMinute(date) {
  return new Date(Math.floor(date.getTime() / MINUTE_MS) * MINUTE_MS);
}

// 시각을 분 단위로 올림. 이미 0초이면 같은 시각
export function ceilToMinute(date) {
  return new Date(Math.ceil(date.getTime() / MINUTE_MS) * MINUTE_MS);
}

// Date를 24시간제 'HH:MM' 문자열로
export function formatClock(date) {
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  return `${hours}:${minutes}`;
}

// 지금 출발할 때의 예상 도착 시각 'HH:MM' (분 단위 올림)
export function expectedArrival(now, totalSeconds) {
  const arrival = new Date(now.getTime() + totalSeconds * 1000);
  return formatClock(ceilToMinute(arrival));
}

// 늦어도 출발해야 할 시각 = 목표 도착 시각 - 총 소요 시간 - 여유 시간 (초 단위, 반올림 전)
export function latestDeparture(targetDate, totalSeconds, marginSeconds = MARGIN_SECONDS) {
  return new Date(targetDate.getTime() - (totalSeconds + marginSeconds) * 1000);
}

// 카드의 출발 시각 줄 (rules.md 11.2, screen-today.md 3.1)
// - 목표 도착 시각은 항상 오늘 날짜 기준 (2026-10-20 사용자 결정)
// - 목표가 없거나 출발 시각이 지났으면 '지금 출발하면 HH:MM 도착'
// - 지났는지는 분 단위로 바꾸기 전 초 단위 값으로 판단 (rules.md 2장)
// - 반환: kind('leave_by' 또는 'arrive_if_now'), 앞말, 시각, 뒷말
export function departureLine({ now, targetArrival, totalSeconds, marginSeconds = MARGIN_SECONDS }) {
  const targetDate = clockOnDate(now, targetArrival);
  if (targetDate) {
    const latest = latestDeparture(targetDate, totalSeconds, marginSeconds);
    if (latest.getTime() >= now.getTime()) {
      return {
        kind: 'leave_by',
        prefix: '늦어도',
        time: formatClock(floorToMinute(latest)),
        suffix: '출발',
      };
    }
  }
  return {
    kind: 'arrive_if_now',
    prefix: '지금 출발하면',
    time: expectedArrival(now, totalSeconds),
    suffix: '도착',
  };
}

// 날짜를 기기 시간대 오프셋을 포함한 ISO 8601 문자열로 (예: '2026-10-20T08:50:00+09:00')
export function toOffsetIso(date) {
  const pad = (value) => String(value).padStart(2, '0');
  const offset = -date.getTimezoneOffset();
  const sign = offset >= 0 ? '+' : '-';
  const zone = `${sign}${pad(Math.floor(Math.abs(offset) / 60))}:${pad(Math.abs(offset) % 60)}`;
  return (
    `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}` +
    `T${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}${zone}`
  );
}

// 첫차, 막차 판단의 기준 도착 시각 = 목표 도착 시각 - 여유 시간 (rules.md 3.4.1, api_spec.md 4.1)
// - 목표 도착 시각이 없으면 null (서버로 보내지 않음)
export function arriveBy({ now, targetArrival, marginSeconds = MARGIN_SECONDS }) {
  const targetDate = clockOnDate(now, targetArrival);
  if (!targetDate) {
    return null;
  }
  return toOffsetIso(new Date(targetDate.getTime() - marginSeconds * 1000));
}
