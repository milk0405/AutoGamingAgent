# AutoGamingAgent

**AutoGamingAgent**는 마우스와 키보드를 동시에 사용하는 2D 액션 플랫포머 게임을 유저의 개입 없이 스스로 분석하고 플레이하여 돌파할 수 있도록 설계된 **완전 자율형 비전 AI 에이전트**입니다.

이 프로젝트는 사람의 창의적인 아이디어를 바탕으로 프론티어 AI 모델과 협업하여 생성된 자율 주행 게임 에이전트 시스템입니다.

---

## 📁 파일 트리 (File Tree)

프로젝트 디렉토리 구조는 다음과 같이 구성되어 있습니다.

```text
AutoGamingAgent/
├── README.md              # 프로젝트 설명서 (본 문서)
├── LICENSE                # 라이센스 파일 (MIT)
├── PLAN.md                # 개발 명세서 및 아키텍처 플랜
├── game_agent_autonomous.py # 메인 자율 에이전트 실행 코드
└── .env.example           # 환경 변수 설정 템플릿

```

---

## ⚙️ 핵심 특징 (Key Features)

* **키보드 및 마우스 통합 제어**: 이동, 점프 등의 키보드 입력뿐만 아니라 정밀한 조준, 클릭, 홀드 등의 마우스 인터랙션을 유기적으로 수행합니다.
* **구조화된 플래닝 툴 (Function Calling)**: 화면을 즉각적으로 누르지 않고, `create_plan`과 `update_plan` 툴을 통해 1~3초 분량의 거시적 행동 계획을 먼저 수립하고 실행합니다.
* **정밀한 클라이언트 좌표계 정합성**: `win32gui`를 활용해 멀티 모니터 및 Windows DPI 배율 환경에서도 게임 창 클라이언트 영역의 절대 좌표를 정확하게 추적합니다.
* **자율 복구 및 서킷 브레이커 (Circuit Breaker)**: 데스(Death)나 데드락(정체 상태)이 5초 이상 감지될 경우, 에이전트가 이를 스스로 인지하고 대체 플랜으로 강제 갱신하여 난관을 돌파합니다.
* **토큰 최적화 계층형 메모리**: 방대한 대화 히스토리 대신 단기 프레임 스트림과 글로벌 게임 규칙 메모장(`game_memory`)을 분리 운영하여 API 비용과 지연 시간을 최소화합니다.

---

## 🚀 빠른 시작 (Getting Started)

### 1. 사전 요구 사항 및 패키지 설치

Python 3.8 이상 환경에서 아래 라이브러리들을 설치해주세요.

```bash
pip install mss Pillow pynput openai python-dotenv pywin32

```

### 2. 환경 변수 설정 (`.env`)

`.env.example` 파일을 복사하여 `.env` 파일을 생성하고, 사용하는 API 게이트웨이(예: OmniRoute 또는 OpenAI 호환 엔드포인트) 정보를 입력합니다.

```env
OPENAI_API_KEY=your-api-key-here
OPENAI_BASE_URL=http://localhost:20128/v1
AI_MODEL_NAME=gpt-4o

```

### 3. 에이전트 실행

1. 대상 게임을 창 모드로 실행하고 모니터 한쪽에 배치합니다.
2. `game_agent_autonomous.py` 상단의 설정 파라미터(`TARGET_WINDOW_TITLE`)에 실제 게임 창의 타이틀을 입력합니다.
3. 터미널에서 스크립트를 실행합니다.

```bash
python game_agent_autonomous.py

```

---

## 📄 라이센스 (License)

이 프로젝트는 **MIT License**를 따릅니다. 자세한 내용은 `LICENSE` 파일을 참고하세요.
