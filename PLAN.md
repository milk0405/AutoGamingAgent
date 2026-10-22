[Plan Document] 2D 액션 플랫포머(키보드+마우스) 완전 자율형 AI 에이전트 개발 명세서 (Updated)
1. 프로젝트 개요 (Overview)
목표: 마우스와 키보드를 동시에 사용하는 2D 액션 플랫포머 게임에서 유저의 개입 없이, 명시적 플래닝 툴을 활용해 스테이지 구조를 분석하고 스스로 플레이하여 돌파하는 자율형 비전 에이전트 구축.
핵심 특징:
키보드(이동/점프)와 마우스(조준/클릭/홀드)의 유기적 결합
플래닝 전용 툴(Tool Calling)을 통한 구조화된 액션 플랜 수립 및 동적 갱신
유저 질의 기능 배제 및 서킷 브레이커 기반 자율 예외 복구 시스템
2. 세부 개발 페이즈 (Development Phases)
Phase 1: 시각적 컨텍스트 수집 및 절대 좌표계 정합성 확보 (Perception & Coordinate Mapping)
DPI Awareness 및 창 핸들링
Windows OS의 DPI 배율로 인한 마우스 좌표 오차를 원천 차단하기 위해 애플리케이션 레벨에서 DPI 인식 강제 적용.
win32gui를 통해 게임 창의 클라이언트 영역(Client Area) 기준 좌상단 (0, 0) 오프셋을 실시간 동기화.
멀티모달 시각 입력 구성
캡처 화면에 플레이어, 적, 지형뿐만 아니라 마우스 커서의 현재 위치, 조준선(Crosshair), UI 상태(체력, 탄창, 쿨타임 등)가 온전하게 포함되도록 시각적 컨텍스트 파이프라인 구성.
Phase 2: 계층형 메모리 및 전술 플래닝 엔진 (Hierarchical Memory & Planner)
글로벌 게임 규칙 메모장 (Global Game Memory)
대화 히스토리를 배제하고, 시행착오를 통해 획득한 고정 규칙(예: "이 적은 마우스 우클릭으로 원거리 타격해야 함", "붉은 스위치는 마우스 클릭 필요")을 업데이트하는 전역 메모리 구조 구현.
에이전트 주도형 플래닝 메커니즘
화면 변화나 체크포인트 진입 시 즉시 키를 누르지 않고, 플래닝 툴을 호출하여 1~3초 분량의 거시적 행동 계획(Action Plan Sequence)을 먼저 생성한 뒤 실행기로 전달.
Phase 3: 무인 통합 툴 세트 구축 (Autonomous Tool Suite with Planning Tools)
에이전트가 외부 도움 없이 온전히 게임을 제어하고 전략을 수립할 수 있는 툴(Function Calling) 정의 (유저 질의 툴 원천 배제).
플래닝 툴 (Planning Tools) — (New Added)
create_plan(goal_description, action_steps): 현재 화면의 목표(예: "상단 플랫폼으로 이동 후 적 저격")와 순차적인 하위 액션 리스트를 명시적으로 생성.
update_plan(status, reason, next_steps): 실행 중 장애물이나 변수가 생겼을 때 기존 계획을 수정하거나 새로운 대체 플랜으로 갱신.
키보드 조작 툴
key_down(key) / key_up(key) / press_key(key): 이동, 점프, 스킬 등 키 홀드 및 릴리즈 제어.
마우스 제어 툴
move_mouse(x, y): 게임 창 클라이언트 좌표계 기준 마우스 커서 즉시 이동.
click_mouse(button, action): 좌/우 클릭, 누르고 있기(드래그 및 차징 공격) 제어.
메모리 갱신 툴
update_game_memory(rule): 플레이 중 파악한 조준 기믹이나 지형 규칙을 메모장에 반영.
Phase 4: 자율 복구 및 서킷 브레이커 루프 (Autonomous Recovery & Deadlock Handling)
유저의 힌트 없이 에이전트가 난관을 돌파하기 위한 핵심 안전장치 설계.
무한 루프 및 데스 감지 (Deadlock Detection)
동일한 위치에서 반복적으로 데스를 당하거나, 일정 시간(예: 5초 이상) 캐릭터의 전진 없이 화면 변화가 정체될 경우를 감지하는 서킷 브레이커 로직 탑재.
자동 복구 및 플랜 강제 수정 (Dynamic Replanning)
데스 또는 정체 감지 시, 기존 플랜을 실패 처리하고 update_plan을 호출하여 기존과 다른 이동 경로 혹은 반대 방향 조준 등 우회 플랜(Alternative Plan)을 강제 생성한 뒤 재시도.
