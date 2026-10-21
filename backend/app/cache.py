'''메모리 캐시 (tech_stack.md 3.5)

- 딕셔너리에 (저장 시각, 값)을 두고, 꺼낼 때 보관 시간이 지났으면 지움
- 서버 메모리에만 두며 파일, 데이터베이스, 로그에 쓰지 않음
'''

import time


def round_point(point):
    '''좌표를 소수 다섯째 자리(약 1m)로 맞춤. 캐시 열쇠에 사용'''
    return (round(point[0], 5), round(point[1], 5))


class TTLCache:
    '''보관 시간이 있는 딕셔너리 캐시'''

    def __init__(self, ttl_seconds, clock=time.monotonic):
        self.ttl_seconds = ttl_seconds
        self.clock = clock
        self._items = {}

    def get(self, key):
        '''값이 있고 보관 시간 안이면 값, 아니면 None'''
        item = self._items.get(key)
        if item is None:
            return None
        saved_at, value = item
        if self.clock() - saved_at >= self.ttl_seconds:
            del self._items[key]
            return None
        return value

    def set(self, key, value):
        '''지금 시각과 함께 저장'''
        self._items[key] = (self.clock(), value)

    def clear(self):
        '''모두 지움'''
        self._items.clear()
