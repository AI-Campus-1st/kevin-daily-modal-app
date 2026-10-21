# 공개 배포 가이드: 홈랩 NAS (Docker, Cloudflare Tunnel)

## 0. 문서 정보
- 작성일: 2026-10-21
- 상태: 초안. NAS, Docker 이미지, Cloudflare의 현재 정책과 화면 메뉴 이름은 외부 확인 전 (12장 `H-` 항목)
- 근거 문서: `docs/tech/tech_stack.md`, `docs/tech/datasource.md`, `docs/tech/deploy-render.md`
- 쓰임: 이 앱을 집의 NAS에서 Docker로 실행하고 Cloudflare Tunnel로 주소를 아는 사람 누구나 접속하게 하는 절차
- 전제
  | 항목 | 값 |
  |---|---|
  | 서버 | NAS. Synology DSM 7.2 이상의 Container Manager 기준. 다른 NAS도 Docker Compose를 쓸 수 있으면 같은 파일로 실행 |
  | 실행 방식 | Docker 컨테이너 2개 (앱, Cloudflare Tunnel 연결) |
  | 외부 접속 | Cloudflare Tunnel. 공유기 포트 개방 없음 |
  | 공개 범위 | 주소를 아는 사람 누구나 |
  | 이미지 | 저장소 root의 `Dockerfile`, `.dockerignore`. Render 배포(`deploy-render.md`)와 같은 파일 (4장) |

## 1. 구조와 원리

### 1.1 구조
| 순서 | 위치 | 동작 |
|---|---|---|
| 1 | 휴대폰 브라우저 | `https://{하위 이름}.{도메인}` 접속 |
| 2 | Cloudflare | HTTPS 인증서로 접속을 받고, 터널을 통해 NAS로 전달 |
| 3 | NAS `tunnel` 컨테이너 | NAS에서 Cloudflare로 먼저 연결해 둔 통로(터널)로 요청을 받아 `app` 컨테이너에 전달 |
| 4 | NAS `app` 컨테이너 | FastAPI 서버가 화면과 `/api/...`를 제공. 외부 API는 NAS의 인터넷 연결로 호출 |

### 1.2 원리
| 개념 | 설명 | 이 앱에서 |
|---|---|---|
| 이미지 | 프로그램 실행에 필요한 운영체제 일부, Python, 라이브러리, 코드를 한 묶음으로 만든 파일. `Dockerfile`이 만드는 순서 | Python 3.14 + `requirements.txt` 라이브러리 + `backend/`, `frontend/` |
| 컨테이너 | 이미지를 실행한 것. NAS 운영체제와 분리된 공간에서 돌아감 | `app`, `tunnel` 2개 |
| Docker Compose | 여러 컨테이너의 설정(이미지, 환경 변수, 재시작 규칙)을 `compose.yaml` 한 파일에 적고 함께 켜고 끄는 방식 | Container Manager의 "프로젝트"가 이 파일을 읽음 |
| 컨테이너 네트워크 | 같은 Compose 프로젝트의 컨테이너끼리는 서비스 이름을 주소처럼 써서 통신 | `tunnel`이 `http://app:8000`으로 앱에 접속 |
| 터널 | NAS가 바깥(Cloudflare)으로 먼저 연결을 열어 두고, 그 연결로 요청을 받는 방식 | 공유기에서 포트를 열지 않으므로 NAS 관리 화면이 인터넷에 드러나지 않음 |

### 1.3 Render와 비교
| 항목 | Render 무료 플랜 (`deploy-render.md`) | 홈랩 NAS |
|---|---|---|
| 잠들기 | 15분 접속 없으면 멈춤 | 없음. 메모리 캐시가 유지되어 외부 호출이 줄어듦 |
| 서버 위치 | 싱가포르 | 한국 가정 인터넷. 공공 API 해외 접속 차단 문제 없음 |
| 주소 | `{이름}.onrender.com` | 본인 도메인 필요 |
| 관리 | Render가 맡음 | NAS 전원, 인터넷, 업데이트를 직접 관리. NAS가 꺼지면 앱도 멈춤 |
| 비용 | 없음 | 도메인 비용, NAS 전기 요금 |

## 2. 준비
| 항목 | 내용 |
|---|---|
| NAS 모델 | Container Manager를 설치할 수 있는 모델 (x86_64 또는 일부 ARM64). 패키지 센터에서 Container Manager 설치 (H-1) |
| NAS 메모리 | 앱 컨테이너가 DS-19 전체 목록(약 4만 행)을 메모리에 두므로 여유 메모리 확인 |
| 도메인 | Cloudflare에 등록된(네임서버가 Cloudflare인) 본인 도메인. 없으면 Cloudflare Registrar 등에서 구입 후 등록 |
| Cloudflare 계정 | Zero Trust 무료 플랜 사용 등록 (H-2) |
| 로컬 검사 | `deploy-render.md` 4.1의 테스트, 코드 검사, 토큰 일치, 4.2의 로컬 Docker 검사 모두 통과 |

## 3. 폴더 구성
- NAS 안 위치 예: `/volume1/docker/daily-modal/`
  ```
  /volume1/docker/daily-modal/
    compose.yaml          컨테이너 2개의 설정 (6.1)
    app.env               앱 인증키 5개. 저장소에 올리지 않음
    tunnel.env            Cloudflare Tunnel 토큰. 저장소에 올리지 않음
    app/                  저장소에서 옮긴 파일 (6.3)
      Dockerfile
      .dockerignore
      backend/
        requirements.txt
        app/
        data/
      frontend/
        index.html
        css/
        js/
        fonts/
  ```
- `app.env` 형식은 `이름=값` 한 줄씩. 이름은 `backend/.env`와 같고, 값은 `backend/.env`의 따옴표를 뺀 안의 값만 적음. 도구에 따라 따옴표를 값의 일부로 읽는 경우가 있음 (`deploy-render.md` 4.2)
- `tunnel.env` 형식: `TUNNEL_TOKEN=` 뒤에 5장에서 받은 토큰
- 두 `.env` 파일은 File Station에서 권한을 관리자만 읽게 설정

## 4. 이미지 파일
- 저장소 root의 `Dockerfile`, `.dockerignore`를 그대로 씀. Render 배포와 같은 파일
- 줄별 뜻, 실행 명령 풀이, 제외 파일 목록: `deploy-render.md` 3장
- 이 문서와 관련된 부분
  | 항목 | 내용 |
  |---|---|
  | 포트 | 실행 명령이 `--port ${PORT:-8000}`이므로, `PORT`를 넣지 않는 NAS에서는 8000에서 접속을 받음. 5장 `app:8000`, 6.1 `ports`가 이 번호 |
  | 실행 사용자 | `appuser`(관리자 권한 없음). 앱은 파일을 읽기만 하므로 NAS 폴더 권한 설정이 필요 없음 |
  | 로컬 검증 | `deploy-render.md` 4.2, 6.1. PC(linux/amd64)에서 빌드, 실행 확인 (2026-10-21) |

## 5. Cloudflare Tunnel 만들기
| 순서 | 작업 |
|---|---|
| 1 | Cloudflare 대시보드 → Zero Trust → Networks → Tunnels → Create a tunnel (H-2) |
| 2 | 연결 방식 Cloudflared 선택, 터널 이름 입력 (예: `nas-daily-modal`) |
| 3 | 설치 안내 화면의 Docker 명령에서 `--token` 뒤 긴 문자열을 복사해 `tunnel.env`의 `TUNNEL_TOKEN=` 뒤에 붙임. 설치 명령 자체는 실행하지 않음 (6장에서 Compose로 실행) |
| 4 | 공개 주소(Public Hostname, 또는 Published application routes) 추가: 하위 이름 예 `commute`, 도메인 선택, 서비스 종류 `HTTP`, 주소 `app:8000` |
| 5 | 저장. 6장 실행 후 터널 상태가 Healthy로 바뀜 |

- 4번의 `app:8000`은 6.1 `compose.yaml`의 서비스 이름 `app`과 Dockerfile의 포트 8000
- 이 터널에는 앱 주소 하나만 연결. NAS 관리 화면(DSM)은 연결하지 않음
- 토큰은 터널 접속 권한 자체이므로 저장소, 문서, 채팅에 적지 않음. 새어 나갔으면 Cloudflare에서 토큰을 다시 발급

## 6. 실행

### 6.1 compose.yaml
```yaml
# NAS의 /volume1/docker/daily-modal/compose.yaml
services:
  app:
    build: ./app
    image: daily-modal-app:0.3.1   # 이미지 이름과 버전. 버전은 커밋 이름과 맞춤 (9장)
    restart: unless-stopped        # NAS 재시작, 오류 종료 후 자동으로 다시 켬
    env_file: ./app.env            # 인증키 5개
    # NAS 안 네트워크에서 직접 확인할 때만 아래 두 줄의 주석 해제 (8장 1번)
    # ports:
    #   - '8000:8000'

  tunnel:
    image: cloudflare/cloudflared:latest   # 버전 고정 권장 (H-4)
    restart: unless-stopped
    command: tunnel --no-autoupdate run    # 토큰은 tunnel.env의 TUNNEL_TOKEN에서 읽음 (H-4)
    env_file: ./tunnel.env
    depends_on:
      - app
```
- `app`에 `ports`가 없으므로 앱은 NAS 밖에서 직접 접속할 수 없고 터널로만 접속됨
- 서버 수는 1개 유지 (`--workers` 없음). 메모리 캐시가 프로세스 안에 있기 때문

### 6.2 Container Manager에서 실행
| 순서 | 작업 |
|---|---|
| 1 | 3장 폴더 구성대로 파일 배치 (5장 토큰 포함) |
| 2 | Container Manager → 프로젝트 → 생성 |
| 3 | 프로젝트 이름 `daily-modal`, 경로 `/volume1/docker/daily-modal`, 원본 "기존 docker-compose.yml 사용" 선택 (H-5) |
| 4 | 웹 포털 설정은 사용하지 않음. 완료하면 이미지 빌드 후 컨테이너 2개가 켜짐 |
| 5 | 컨테이너 → `app` → 로그에서 Uvicorn 시작 기록 확인 |

- SSH를 쓰면 같은 폴더에서 `sudo docker compose up -d --build`로 같은 작업 가능

### 6.3 파일 옮기기
- PC에서 NAS 공유 폴더(`\\{NAS 이름}\docker\daily-modal\app`)로 3장의 `app/` 아래 파일만 복사
- `backend/.env`, `backend/.venv`, `.git`은 복사하지 않음
- 비공개 저장소이므로 NAS에서 직접 `git clone`하려면 NAS에 GitHub 접근 키를 따로 두어야 함. 이 문서는 파일 복사 방식 기준

## 7. 카카오 개발자 설정
| 대상 | 작업 |
|---|---|
| JavaScript 키 | 사이트 도메인(JavaScript SDK 도메인)에 `https://{하위 이름}.{도메인}` 추가. 개발용 localhost 주소는 유지 |
| REST API 키 | 허용 IP 주소 설정을 쓰고 있다면 집 인터넷의 공인 IP 추가. 가정 인터넷 IP는 바뀔 수 있으므로 설정을 쓰지 않는 쪽이 관리가 쉬움 |

- 메뉴 이름 확인 필요 (`deploy-render.md` E-5)

## 8. 배포 후 확인
| 순서 | 확인 | 방법 |
|---|---|---|
| 1 | 앱 단독 (선택) | 6.1의 `ports` 주석을 풀고 다시 켠 뒤, 같은 집 네트워크의 PC에서 `http://{NAS 주소}:8000` 열기. 확인 후 다시 주석 처리 |
| 2 | 터널 | Cloudflare Tunnels 화면에서 상태 Healthy |
| 3 | 화면, API, 지도, 홈 화면 추가 | `https://{하위 이름}.{도메인}`으로 `deploy-render.md` 6.2의 2 ~ 10번과 같은 항목 확인 |
| 4 | 개인정보 | Container Manager의 `app` 로그에 주소, 좌표, 검색어가 없음 |
| 5 | 화면 파일 갱신 | 앱이 붙이는 `Cache-Control: no-cache` 때문에 Cloudflare가 css, js를 저장해 두지 않고 매번 NAS에 확인하는지 (H-6). 고친 화면이 바로 보이면 정상 |
| 6 | 자동 재시작 | NAS를 다시 켠 뒤 두 컨테이너가 자동으로 켜짐 |

## 9. 갱신과 되돌리기
| 작업 | 방법 |
|---|---|
| 갱신 | 로컬 검사 통과 → 바뀐 파일을 NAS `app/`에 다시 복사 → `compose.yaml`의 `image` 버전을 새 버전(예: `0.3.2`)으로 변경 → Container Manager 프로젝트에서 빌드 후 다시 시작 |
| 되돌리기 | `image` 버전을 이전 값으로 되돌리고 다시 시작. 이전 버전 이미지가 NAS에 남아 있으므로 다시 빌드하지 않음 |
| 정리 | 오래된 버전 이미지는 Container Manager → 이미지에서 삭제 |
| 인증키 변경 | `app.env` 수정 후 프로젝트 다시 시작 |

- 이미지 버전을 커밋 이름(`0.3.1` 등)과 맞추면 NAS에서 실행 중인 코드가 어느 커밋인지 바로 알 수 있음
- 다시 시작하면 메모리 캐시가 비워짐

## 10. 공개 접속과 호출량
- 호출량 문제와 앱 쪽 대응 방법은 `deploy-render.md` 8장과 같음. 다만 잠들기가 없어 캐시가 유지되므로 같은 장소 쌍의 반복 조회는 Render보다 적게 호출함
- Cloudflare에서 할 수 있는 대응 (코드 수정 없음, 사용자 결정 필요)
  | 방법 | 내용 |
  |---|---|
  | 요청 수 제한 규칙 | Cloudflare WAF의 Rate limiting rule로 `/api/recommend`에 같은 접속 주소의 분당 요청 수 제한. 무료 플랜 제공 범위 확인 필요 (H-7) |
- 앱 안에서 접속자별 제한을 만들 경우, 터널 뒤에서는 모든 요청이 `tunnel` 컨테이너에서 오는 것으로 보이므로 실제 접속 주소는 `CF-Connecting-IP` 머리글로 읽어야 함

## 11. 운영 시 주의
| 항목 | 내용 |
|---|---|
| NAS 보안 | DSM, 패키지 업데이트 유지. 터널은 앱 주소만 연결 (5장) |
| 정전, 인터넷 끊김 | 그동안 앱 접속 불가. 다시 연결되면 컨테이너와 터널이 자동으로 복구 |
| 베이스 이미지 업데이트 | Python 보안 패치 반영을 위해 주기적으로 다시 빌드 |
| 백업 | 서버에 사용자 데이터가 없으므로 백업 대상은 `compose.yaml`, 두 `.env` 파일뿐 |

## 12. 확인 필요 (외부 정보)
| ID | 항목 | 이 문서의 위치 |
|---|---|---|
| H-1 | Synology Container Manager 지원 모델(CPU 종류), DSM 최소 버전 | 2장 |
| H-2 | Cloudflare Zero Trust 무료 플랜 가입 조건(결제 수단 등록 여부), Tunnels 메뉴와 공개 주소 설정 화면의 현재 이름 | 2장, 5장 |
| H-3 | 공식 Python 이미지 `3.14.8-slim`의 ARM64 제공 여부. 태그와 amd64 제공은 로컬 빌드로 확인 (2026-10-21) | 4장 |
| H-4 | `cloudflare/cloudflared` 이미지의 현재 안정 버전, `TUNNEL_TOKEN` 환경 변수로 토큰을 읽는 방식이 유지되는지 | 6.1 |
| H-5 | Container Manager 프로젝트 생성 화면의 현재 항목 이름, `compose.yaml` 파일 이름 인식 여부 | 6.2 |
| H-6 | Cloudflare가 원본 응답의 `Cache-Control: no-cache`를 따라 css, js, woff2를 캐시하지 않는지 | 8장 |
| H-7 | Cloudflare 무료 플랜의 Rate limiting rule 개수, 기간, 조건 제한 | 10장 |
