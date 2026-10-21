// 카카오 지도 SDK 불러오기 (권장 F-16, tech_stack.md 4.1)
// - 지도 화면을 처음 열 때 한 번만 불러옴. autoload=false로 받은 뒤 kakao.maps.load로 준비
// - 서버를 거치지 않는 유일한 외부 호출 (frontend/CLAUDE.md 1장 예외)
// - 지도 키가 없거나 불러오지 못하면 null

import { mapKey } from './api.js';

const SDK_URL = 'https://dapi.kakao.com/v2/maps/sdk.js';

let loading = null;

function addScript(key) {
  return new Promise((resolve) => {
    const script = document.createElement('script');
    script.src = `${SDK_URL}?appkey=${encodeURIComponent(key)}&autoload=false`;
    script.onload = () => {
      if (window.kakao?.maps?.load) {
        window.kakao.maps.load(() => resolve(window.kakao.maps));
      } else {
        resolve(null);
      }
    };
    script.onerror = () => {
      script.remove();
      resolve(null);
    };
    document.head.append(script);
  });
}

export function loadMapSdk() {
  if (!loading) {
    loading = (async () => {
      const key = await mapKey();
      return key ? addScript(key) : null;
    })();
    // 실패하면 다음에 다시 시도
    loading.then((maps) => {
      if (!maps) {
        loading = null;
      }
    });
  }
  return loading;
}
