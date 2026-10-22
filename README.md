# AutoGamingAgent

AutoGamingAgent is a system designed to let a 2D action platformer game be played autonomously without human intervention by analyzing the game screen and controlling both the keyboard and mouse simultaneously.

This project is an autonomous game-agent system created through collaboration between human creative ideas and frontier AI models. It is designed to interpret the game state, plan actions, and execute them continuously in real time.

---

## 📁 Project Structure

```text
AutoGamingAgent/
├── README.md              # Main project documentation
├── README-ko.md           # Korean version of the project documentation
├── LICENSE                # MIT license
├── PLAN.md                # Development specification and architecture plan
├── game_agent_autonomous.py # Main autonomous agent execution code
├── .env.example           # Environment variable template
└── .gitignore             # Git ignore rules
```

---

## ⚙️ Key Features

- Keyboard and mouse combined control: Performs not only movement and jumping but also precise aiming, clicking, and hold interactions through coordinated keyboard and mouse operations.
- Structured planning with function calling: Instead of reacting frame-by-frame, the agent first creates a short-term macro plan using tools such as `create_plan` and `update_plan` to decide the next 1–3 seconds of behavior.
- Precise client-coordinate matching: Uses `win32gui` to compute the absolute client coordinates of the game window even in multi-monitor and Windows DPI scaling environments.
- Autonomous recovery and circuit breaker: Detects deaths or deadlocks lasting longer than 5 seconds, recognizes the failure state, and switches to a fallback plan.
- Token-efficient layered memory: Keeps a short-term frame stream and a global gameplay rules memory (`game_memory`) separate to reduce API cost and manage long-running sessions more efficiently.

---

## 🚀 Getting Started

### 1. Requirements and installation

Use Python 3.8 or later and install the required dependencies:

```bash
pip install mss Pillow pynput openai python-dotenv pywin32
```

### 2. Environment configuration (`.env`)

Copy `.env.example` to `.env` and fill in the information for the API gateway you are using, such as OmniRoute or any OpenAI-compatible endpoint.

```env
OPENAI_API_KEY=your-api-key-here
OPENAI_BASE_URL=http://localhost:20128/v1
AI_MODEL_NAME=gpt-4o
```

### 3. Run the agent

1. Launch the target game in windowed mode and place it on one side of the monitor.
2. Update `TARGET_WINDOW_TITLE` in `game_agent_autonomous.py` to match the actual game window title.
3. Run the script from the terminal:

```bash
python game_agent_autonomous.py
```

---

## 🧠 How it works

The agent continuously monitors the game window, extracts visual context, evaluates the current state, and decides the next action using structured planning. It can navigate the environment, react to hazards, and recover from failed states without needing manual input.

The system is built around a loop of:

- screen capture
- state analysis
- plan creation/update
- direct control execution
- error detection and recovery

---

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for details.
