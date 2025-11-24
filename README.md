# Wi-Fi 채널 분석기 & 최적화 도구

주변 무선 네트워크를 스캔하여 채널 혼잡도를 분석하고 최적의 채널을 추천하는 크로스 플랫폼 웹 애플리케이션입니다.

## 주요 기능

- **실시간 Wi-Fi 네트워크 스캔** - Windows, macOS, Linux 지원
- **채널 혼잡도 분석** - 2.4GHz 및 5GHz 대역 분석
- **인터랙티브 데이터 시각화** - Chart.js 기반 그래프
- **최적 채널 추천** - AP 분포 기반 알고리즘
- **반응형 웹 UI** - 모바일 및 데스크톱 지원
- **환경 변수 설정** - 유연한 구성 관리
- **Mock 데이터 지원** - 테스트 및 개발용

## 시스템 요구사항

### 필수 요구사항
- **Node.js** 14.x 이상
- **Python 3.x**

### 플랫폼별 요구사항

| 플랫폼 | 권한 요구사항 | 사용 명령어 |
|--------|---------------|-------------|
| **Windows** | 관리자 권한 필수 | `netsh wlan show networks` |
| **macOS** | 일반 사용자 권한 | `airport -s` |
| **Linux** | 일반 사용자 권한 | `nmcli` |

## 빠른 시작

### 1. 저장소 클론

```bash
git clone <repository-url>
cd network_project
```

### 2. 의존성 설치

```bash
cd backend
npm install
```

### 3. 환경 변수 설정 (선택사항)

```bash
# .env 파일 복사
cp .env.example .env

# 필요에 따라 .env 파일 수정
vi .env
```

기본 설정:
```env
PORT=5001
HOST=0.0.0.0
NODE_ENV=development
PYTHON_COMMAND=python3
CORS_ORIGIN=*
SCAN_TIMEOUT=15
WIFI_INTERFACE_NAME=    # 비워두면 자동 감지
USE_MOCK_DATA=false     # 테스트용 Mock 데이터 사용 여부
```

**Mock 데이터 사용 (개발/테스트용):**
실제 Wi-Fi 스캔 없이 미리 정의된 네트워크 목록으로 테스트할 수 있습니다:
```env
USE_MOCK_DATA=true
```

Mock 데이터에는 KT, SK, U+ 등 일반적인 한국 Wi-Fi 네트워크 15개가 포함되어 있습니다.

### 4. 서버 실행

```bash
# 프로덕션 모드
npm start

# 개발 모드 (자동 재시작)
npm run dev
```

### 5. 브라우저에서 접속

```
http://localhost:5001
```

## 프로젝트 구조

```
network_project/
├── backend/                    # 백엔드 서버
│   ├── .env                   # 환경 변수 (git에서 제외)
│   ├── .env.example           # 환경 변수 예제
│   ├── .gitignore             # Git 제외 파일 목록
│   ├── package.json           # Node.js 의존성 및 스크립트
│   └── src/
│       ├── server.js          # Express.js 서버
│       └── wifi_scanner.py    # Python Wi-Fi 스캐너
│
└── frontend/                   # 프론트엔드
    ├── index.html             # 메인 UI
    ├── css/
    │   └── style.css          # 스타일시트
    └── js/
        └── app.js             # 애플리케이션 로직
```

## 아키텍처

### 시스템 설계

```
┌─────────────────┐
│   웹 브라우저    │  Vanilla JavaScript + Chart.js
│   localhost     │
└────────┬────────┘
         │ HTTP REST API
         ▼
┌─────────────────┐
│  Node.js 서버   │  Express.js (포트 5001)
│  backend/src/   │  환경 변수 기반 설정
└────────┬────────┘
         │ child_process.spawn() + 환경 변수 전달
         ▼
┌─────────────────┐
│ Python 스캐너   │  플랫폼별 CLI 명령어 실행
│ wifi_scanner.py │  Wi-Fi 인터페이스 자동 감지 (Windows)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  OS 명령어      │  netsh / airport / nmcli
└─────────────────┘
```

### 주요 개선사항

1. **환경 변수 지원**: 하드코딩 제거, `.env` 파일로 설정 관리
2. **자동 인터페이스 감지**: Windows에서 Wi-Fi 인터페이스 자동 감지
3. **향상된 로깅**: 구조화된 로그 메시지 (`[TAG] message`)
4. **더 나은 오류 처리**: 사용자 친화적인 한국어 오류 메시지
5. **서버 바인딩 개선**: `0.0.0.0`으로 바인딩하여 외부 접속 허용
6. **Graceful Shutdown**: SIGTERM/SIGINT 시그널 처리

## API 엔드포인트

### `GET /`
프론트엔드 HTML 페이지 제공

### `GET /api/health`
서버 상태 확인

**응답 예시:**
```json
{
  "status": "ok",
  "timestamp": "2025-10-13T08:54:50.986Z",
  "platform": "darwin",
  "nodeVersion": "v22.20.0",
  "environment": "development"
}
```

### `GET /api/scan`
Wi-Fi 네트워크 스캔 및 분석 결과 반환

**응답 예시:**
```json
{
  "networks": [
    {
      "ssid": "MyNetwork",
      "channel": 6,
      "signal": 75
    },
    {
      "ssid": "NeighborWiFi",
      "channel": 6,
      "signal": 45
    }
  ],
  "channel_usage": {
    "1": 1,
    "6": 2,
    "11": 0
  },
  "recommended": 11,
  "predicted": "15%",
  "total_networks": 2,
  "platform": "darwin"
}
```

### `GET /api/debug`
시스템 디버깅 정보 및 환경 설정 반환

**응답 예시:**
```json
{
  "platform": "darwin",
  "nodeVersion": "v22.20.0",
  "cwd": "/Users/kyoe/network_project/backend",
  "pythonScript": "/Users/kyoe/network_project/backend/src/wifi_scanner.py",
  "config": {
    "PORT": "5001",
    "HOST": "0.0.0.0",
    "PYTHON_COMMAND": "python3",
    "CORS_ORIGIN": "*",
    "SCAN_TIMEOUT": 10,
    "NODE_ENV": "development",
    "WIFI_INTERFACE_NAME": "auto-detect"
  }
}
```

## 환경 변수 설명

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `PORT` | `5001` | 서버 포트 번호 |
| `HOST` | `0.0.0.0` | 서버 바인딩 주소 (0.0.0.0은 모든 인터페이스) |
| `NODE_ENV` | `development` | 실행 환경 (development/production) |
| `PYTHON_COMMAND` | `python3` | Python 실행 명령어 (Windows: `python`) |
| `PYTHON_PATH` | `` | Python 실행 파일 절대 경로 (선택) |
| `CORS_ORIGIN` | `*` | CORS 허용 origin (프로덕션에서는 제한 필요) |
| `LOG_LEVEL` | `info` | 로그 레벨 |
| `WIFI_INTERFACE_NAME` | `` | Wi-Fi 인터페이스 이름 (비워두면 자동 감지) |
| `SCAN_TIMEOUT` | `15` | 스캔 타임아웃 (초 단위) |
| `USE_MOCK_DATA` | `false` | Mock 데이터 사용 여부 (true/false) |

## 채널 추천 알고리즘

### 작동 원리

1. **AP 개수 계산**: 각 채널의 액세스 포인트 개수 집계
2. **대역 판별**: 최대 채널이 14 이하면 2.4GHz, 아니면 5GHz
3. **후보 채널 선정**:
   - **2.4GHz**: 1, 6, 11 (비중첩 채널)
   - **5GHz**: 36, 40, 44, 48, 149, 153, 157, 161
4. **최적 채널 반환**: AP 개수가 가장 적은 채널

### 왜 이 채널들인가?

- **2.4GHz 채널 1, 6, 11**: 각각 ~22MHz 대역폭을 사용하여 서로 겹치지 않음
- **5GHz 채널**: DFS(Dynamic Frequency Selection) 제한을 피하는 채널 선택

## 개발 가이드

### Python 스캐너 직접 테스트

```bash
# Python 스캐너 독립 실행
python3 backend/src/wifi_scanner.py

# Windows
python backend/src/wifi_scanner.py

# JSON 유효성 검증
python3 backend/src/wifi_scanner.py | python3 -m json.tool
```

### 백엔드 디버깅

```bash
# 서버 로그 확인
cd backend
npm start
# 콘솔에서 Python stdout/stderr 확인

# API 엔드포인트 수동 테스트
curl http://localhost:5001/api/health
curl http://localhost:5001/api/scan
curl http://localhost:5001/api/debug
```

### 프론트엔드 디버깅

브라우저 콘솔에서 노출된 디버그 함수 사용:

```javascript
// API 엔드포인트 확인
console.log(WifiAnalyzer.API_ENDPOINTS);

// 헬스 체크 실행
WifiAnalyzer.checkHealth();

// 스캔 실행
WifiAnalyzer.scan();
```

## 문제 해결

### 서버 접속이 안 됨

**원인:**
- 서버가 `localhost`에만 바인딩되어 있음
- 방화벽 차단

**해결:**
1. `.env` 파일에서 `HOST=0.0.0.0` 설정 확인
2. 방화벽에서 포트 5001 허용
3. 브라우저에서 `http://localhost:5001` 또는 `http://[서버IP]:5001` 접속

### 포트가 이미 사용 중

**증상:** `Error: listen EADDRINUSE: address already in use`

**해결:**
```bash
# 포트 사용 프로세스 확인 및 종료 (macOS/Linux)
lsof -ti:5001 | xargs kill -9

# Windows
netstat -ano | findstr :5001
taskkill /PID [PID번호] /F

# 또는 다른 포트 사용
# .env 파일에서 PORT=5002 로 변경
```

### Python을 찾을 수 없음

**증상:** "Python을 찾을 수 없습니다" 오류

**원인:** Python이 PATH에 없거나 잘못된 명령어 이름

**해결:**
1. Python 설치 확인:
   ```bash
   python3 --version  # macOS/Linux
   python --version   # Windows
   ```

2. `.env` 파일에서 Python 명령어 수정:
   ```env
   # macOS/Linux
   PYTHON_COMMAND=python3

   # Windows
   PYTHON_COMMAND=python

   # 또는 절대 경로 사용
   PYTHON_COMMAND=/usr/local/bin/python3
   ```

### Windows에서 스캔 결과가 비어있음

**증상:** 주변에 네트워크가 있는데 `networks: []` 반환

**원인:** 관리자 권한 없이 서버 실행

**해결:**
1. PowerShell 또는 CMD를 "관리자 권한으로 실행"
2. `cd backend && npm start`

**또는** 자동 인터페이스 감지가 실패한 경우:
```env
# .env 파일에서 인터페이스 이름 지정
WIFI_INTERFACE_NAME=Wi-Fi

# 또는 한글 Windows
WIFI_INTERFACE_NAME=무선 네트워크 연결
```

### 인터페이스 이름 확인 (Windows)

```bash
# 사용 가능한 Wi-Fi 인터페이스 확인
netsh wlan show interfaces

# 출력에서 "Name" 또는 "이름" 항목 확인
```

### 차트가 렌더링되지 않음

**증상:** 차트가 표시되지 않고 콘솔에 Chart.js 오류

**원인:** Chart.js CDN 로드 실패 (오프라인 또는 네트워크 문제)

**해결:**
Chart.js를 로컬에 다운로드:
```bash
cd frontend
mkdir lib
curl -o lib/chart.js https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js
```

`index.html` 수정:
```html
<script src="lib/chart.js"></script>
```

## 코드 스타일

### JavaScript
- ES6+ 문법 (화살표 함수, async/await, 템플릿 리터럴)
- 2칸 들여쓰기
- camelCase 함수 및 변수명
- UPPER_SNAKE_CASE 상수명

### Python
- 4칸 들여쓰기
- snake_case 네이밍
- 모든 함수에 docstring 작성
- 환경 변수는 `os.environ.get()` 사용

### CSS
- CSS 커스텀 속성(변수) 사용
- BEM 스타일 네이밍 (예: `.card-title`)
- 모바일 우선 반응형 디자인

## 프로덕션 배포

### 필수 변경사항

1. **환경 변수 설정**
   ```env
   NODE_ENV=production
   HOST=0.0.0.0
   PORT=80
   CORS_ORIGIN=https://yourdomain.com
   ```

2. **프로세스 관리자 사용**
   ```bash
   npm install pm2 -g
   pm2 start backend/src/server.js --name wifi-analyzer
   pm2 startup
   pm2 save
   ```

3. **HTTPS 적용**
   - Nginx 또는 Apache 리버스 프록시 사용
   - Let's Encrypt 인증서 발급

4. **보안 강화**
   - CORS origin 제한
   - Rate limiting 추가 (express-rate-limit)
   - Helmet.js로 보안 헤더 추가
   - Input validation

5. **모니터링**
   - PM2 모니터링: `pm2 monit`
   - 로그 확인: `pm2 logs wifi-analyzer`
   - Health check 엔드포인트 활용

## 기술 스택

### 백엔드
- **Node.js** - 서버 런타임 환경
- **Express.js** - 웹 프레임워크
- **dotenv** - 환경 변수 관리
- **Python 3** - Wi-Fi 스캐닝 유틸리티
- **child_process** - Python 스크립트 실행

### 프론트엔드
- **Vanilla JavaScript** - 프레임워크 없는 순수 JS
- **HTML5** - 시맨틱 마크업
- **CSS3** - CSS Grid, Flexbox, 커스텀 속성
- **Chart.js** - 데이터 시각화 라이브러리

---

**마지막 업데이트:** 2025-10-13
**버전:** 2.0.0
**아키텍처:** Node.js + Python + Vanilla JavaScript
**UI 언어:** 한국어
