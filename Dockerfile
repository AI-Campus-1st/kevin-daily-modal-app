# 앱 이미지. 저장소 root 기준
# - Render, 홈랩 NAS가 같은 파일을 씀 (docs/tech/deploy-render.md, deploy-homelab.md)
# - Python 버전은 tech_stack.md 1장과 같게 맞춤
FROM python:3.14.8-slim

# .pyc 파일을 만들지 않고, 로그를 바로 출력
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /srv

# 라이브러리 먼저 설치. requirements.txt가 그대로면 다음 빌드에서 이 단계를 다시 쓰므로 빌드가 빨라짐
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# 서버 실행에 필요한 파일만 복사. .env, 테스트, 문서는 넣지 않음
COPY backend/app backend/app
COPY backend/data backend/data
COPY frontend/index.html frontend/index.html
COPY frontend/css frontend/css
COPY frontend/js frontend/js
COPY frontend/fonts frontend/fonts

# 관리자 권한이 없는 사용자로 실행
RUN useradd --create-home appuser
USER appuser

# 포트는 환경 변수 PORT로 받음. Render는 PORT를 넣어 주고, 없으면 8000
# - sh -c: 셸이 ${PORT:-8000}을 실제 숫자로 바꾼 뒤 실행
# - exec: 셸 대신 uvicorn이 첫 프로세스가 되어 종료 신호(SIGTERM)를 직접 받음
# - worker 1개 유지. 메모리 캐시가 프로세스 안에 있음 (tech_stack.md 3.5)
EXPOSE 8000
CMD ["sh", "-c", "exec uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port ${PORT:-8000}"]
