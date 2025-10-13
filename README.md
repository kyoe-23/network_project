# Wi-Fi 채널 분석기 & 최적화 도구

주변 무선 네트워크를 스캔하여 채널 혼잡도를 분석하고 최적의 채널을 추천하는 크로스 플랫폼 웹 애플리케이션입니다.

## 주요 기능

- **실시간 Wi-Fi 네트워크 스캔** - Windows, macOS, Linux 지원
- **채널 혼잡도 분석** - 2.4GHz 및 5GHz 대역 분석
- **인터랙티브 데이터 시각화** - Chart.js 기반 그래프
- **최적 채널 추천** - AP 분포 기반 알고리즘
- **반응형 웹 UI** - 모바일 및 데스크톱 지원

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

### 3. 서버 실행

```bash
# 프로덕션 모드
npm start

# 개발 모드 (자동 재시작)
npm run dev
```

### 4. 브라우저에서 접속

```
http://localhost:5000
```

## 프로젝트 구조

```
network_project/
├── backend/                    # 백엔드 서버
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
│  Node.js 서버   │  Express.js (포트 5000)
│  backend/src/   │
└────────┬────────┘
         │ child_process.spawn()
         ▼
┌─────────────────┐
│ Python 스캐너   │  플랫폼별 CLI 명령어 실행
│ wifi_scanner.py │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  OS 명령어      │  netsh / airport / nmcli
└─────────────────┘
```

### 데이터 흐름

1. 사용자가 브라우저에서 스캔 버튼 클릭
2. 프론트엔드가 `/api/scan` 호출
3. Express 서버가 Python 서브프로세스 실행
4. Python이 플랫폼별 시스템 명령어 실행
5. Python이 출력 파싱 후 JSON 반환
6. Node.js가 JSON을 프론트엔드로 전달
7. 프론트엔드가 차트와 테이블 렌더링

## API 엔드포인트

### `GET /`
프론트엔드 HTML 페이지 제공

### `GET /api/health`
서버 상태 확인

**응답 예시:**
```json
{
  "status": "ok",
  "timestamp": "2025-10-13T05:25:00.000Z",
  "platform": "darwin"
}
```

### `GET /api/scan`
Wi-Fi 네트워크 스캔 및 분석 결과 반환

**응답 예시:**
```json
{
  "networks": [
    {"ssid": "MyNetwork", "channel": 6, "signal": 75},
    {"ssid": "NeighborWiFi", "channel": 6, "signal": 45}
  ],
  "channel_usage": {"1": 1, "6": 2, "11": 0},
  "recommended": 11,
  "predicted": "15%"
}
```

**필드 설명:**
- `networks`: 발견된 네트워크 목록
  - `ssid`: 네트워크 이름
  - `channel`: 채널 번호
  - `signal`: 신호 강도 (0-100%)
- `channel_usage`: 채널별 AP 개수
- `recommended`: 추천 채널 번호
- `predicted`: 추천 채널의 예상 혼잡도

### `GET /api/debug`
시스템 디버깅 정보 반환

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
curl http://localhost:5000/api/health
curl http://localhost:5000/api/scan
curl http://localhost:5000/api/debug
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

### Python을 찾을 수 없음

**증상:** "Failed to start Python process" 또는 "ENOENT" 오류

**원인:** Python이 PATH에 없거나 잘못된 명령어 이름

**해결:**
`server.js:39`의 Python 명령어 수정:
```javascript
const pythonCommand = process.platform === 'win32' ? 'python' : 'python3';
```

필요시 절대 경로 사용:
```javascript
const pythonCommand = '/usr/local/bin/python3';
```

### Windows에서 스캔 결과가 비어있음

**증상:** 주변에 네트워크가 있는데 `networks: []` 반환

**원인:** 관리자 권한 없이 서버 실행

**해결:**
1. PowerShell 또는 CMD를 "관리자 권한으로 실행"
2. `cd backend && npm start`

### 차트가 렌더링되지 않음

**증상:** 차트가 표시되지 않고 콘솔에 Chart.js 오류

**원인:** Chart.js CDN 로드 실패 (오프라인 또는 네트워크 문제)

**해결:**
Chart.js를 로컬에 다운로드하여 사용:
```bash
cd frontend
mkdir lib
curl -o lib/chart.js https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js
```

`index.html` 수정:
```html
<script src="lib/chart.js"></script>
```

### 한글 Windows에서 인코딩 오류

**증상:** UnicodeDecodeError 또는 깨진 텍스트

**원인:** cp949 인코딩 처리 실패

**현재 구현:** Python 스캐너가 자동으로 cp949 → UTF-8 폴백 처리
```python
output.decode('cp949', errors='ignore')
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

### CSS
- CSS 커스텀 속성(변수) 사용
- BEM 스타일 네이밍 (예: `.card-title`)
- 모바일 우선 반응형 디자인

## 기능 확장

### 새로운 플랫폼 추가

`wifi_scanner.py`에 새 플랫폼 지원 추가:

1. `detect_platform()`에 플랫폼 감지 추가
2. `scan_networks_<platform>()` 함수 구현
3. `(ssid, channel, signal)` 튜플 리스트 반환
4. `scan_networks()` 디스패처에 추가

### 새 API 엔드포인트 추가

1. `server.js`에 `app.get()` 또는 `app.post()` 라우트 추가
2. 적절한 HTTP 상태 코드와 함께 JSON 반환
3. `frontend/js/app.js`의 `API_ENDPOINTS`에 추가
4. 프론트엔드 핸들러 함수 구현

### 채널 추천 로직 수정

`wifi_scanner.py`의 `recommend_channel()` 함수 수정.

**개선 아이디어:**
- 신호 강도 가중치 적용
- 채널 중첩 계산
- 과거 혼잡도 데이터 활용
- DFS 채널 회피 강화

## 알려진 제한사항

1. **관리자 권한 요구 (Windows)**: OS 보안 요구사항으로 우회 불가
2. **단일 동시 스캔**: 한 번에 하나의 스캔만 실행 가능 (큐 메커니즘 없음)
3. **CDN 의존성**: Chart.js를 CDN에서 로드 - 인터넷 연결 필요
4. **데이터 미저장**: 스캔 결과가 메모리에만 존재 (영속성 없음)
5. **고정 인터페이스 이름**: Windows 버전이 "Wi-Fi" 인터페이스 이름 하드코딩

## 프로덕션 배포

**현재 상태로 프로덕션 사용 금지.** 다음 보안 강화가 필요합니다:

### 필수 변경사항

1. **프로덕션 서버 사용**
   ```bash
   npm install pm2 -g
   pm2 start backend/src/server.js --name wifi-analyzer
   ```

2. **CORS 제한**
   ```javascript
   app.use(cors({
     origin: 'https://yourdomain.com'
   }));
   ```

3. **Rate Limiting 추가**
   ```bash
   npm install express-rate-limit
   ```

4. **HTTPS 사용**
   - SSL/TLS 인증서 적용
   - HTTP → HTTPS 리다이렉션

5. **로깅 시스템**
   ```bash
   npm install winston
   ```

6. **환경 변수 관리**
   ```bash
   # .env 파일 생성
   PORT=5000
   NODE_ENV=production
   ```

7. **요청 검증**
   - Input validation
   - Request sanitization

8. **모니터링 및 알림**
   - Health check 엔드포인트 활용
   - 에러 추적 시스템

## 기술 스택

### 백엔드
- **Node.js** - 서버 런타임 환경
- **Express.js** - 웹 프레임워크
- **Python 3** - Wi-Fi 스캐닝 유틸리티
- **child_process** - Python 스크립트 실행

### 프론트엔드
- **Vanilla JavaScript** - 프레임워크 없는 순수 JS
- **HTML5** - 시맨틱 마크업
- **CSS3** - CSS Grid, Flexbox, 커스텀 속성
- **Chart.js** - 데이터 시각화 라이브러리

## 라이선스

MIT License

## 기여

버그 리포트 및 기능 제안은 이슈 트래커를 통해 제출해 주세요.

자세한 개발 가이드는 [CLAUDE.md](CLAUDE.md)를 참조하세요.

## 문의

프로젝트 관련 문의사항은 GitHub 이슈를 이용해 주세요.

---

**마지막 업데이트:** 2025-10-13
**버전:** 1.0.0
**아키텍처:** Node.js + Python + Vanilla JavaScript
**UI 언어:** 한국어
