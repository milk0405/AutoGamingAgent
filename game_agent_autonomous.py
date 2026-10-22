"""
Autonomous 2D Action Platformer Agent
-------------------------------------
Architecture:
- Utilizes an OpenAI-compatible API (OmniRoute gateway) with multi-modal vision inputs.
- Employs Function Calling for structured planning and execution (Keyboard + Mouse).
- Integrates win32gui client-area coordinate mapping to eliminate multi-monitor DPI offset errors.
- Implements a Circuit Breaker pattern for deadlock/stuck recovery without human intervention.
- Supports dynamic language settings for internal reasoning and prompt direction.
"""

import os
import io
import time
import base64
import json
import mss
from PIL import Image
import pynput
from openai import OpenAI
from dotenv import load_dotenv
import win32gui
import win32api
import win32con
import ctypes

# ==========================================
# [Configuration & Global Parameters Section]
# ==========================================
TARGET_WINDOW_TITLE = "TargetGameWindow"  # Target game window title substring for HWND lookup
DEFAULT_AGENT_LANGUAGE = "en"            # Default language context for reasoning and system prompts ('en', 'ko')
MAX_SHORT_TERM_FRAMES = 2                # Number of recent frames to retain for short-term memory stream
CIRCUIT_BREAKER_TIMEOUT = 5.0            # Inactivity threshold (seconds) to trigger deadlock recovery
SCREEN_THUMBNAIL_SIZE = (800, 450)       # Downscaled resolution for vision API token optimization
JPEG_QUALITY = 80                        # Compression quality for captured screenshot JPEGs (0-100)
TICK_INTERVAL = 0.05                     # Main loop tick delay to prevent excessive CPU consumption

# Force Per-Monitor V2 DPI awareness to prevent coordinate scaling mismatches on Windows High-DPI displays.
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

load_dotenv()

# Initialize OpenAI-compatible client routed through OmniRoute gateway.
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "omniroute-local"),
    base_url=os.getenv("OPENAI_BASE_URL", "http://localhost:20128/v1")
)
MODEL_NAME = os.getenv("AI_MODEL_NAME", "gpt-4o")

# Initialize hardware controllers for low-level OS input synthesis.
keyboard_ctrl = pynput.keyboard.Controller()
mouse_ctrl = pynput.mouse.Controller()

# Global state management variables.
cached_hwnd = None
game_memory = "- Controls: WASD/Arrows (Move), Space (Jump), Mouse (Aim & Click)\n- Rules: Not learned yet"
current_plan = {"goal": "Initialize", "steps": []}
last_action_time = time.time()
stuck_detection_count = 0

# --- Tool Definitions ---

def create_plan(goal_description: str, action_steps: list):
    """
    Establish a short-term tactical goal and sequence of sub-actions.
    Design Choice: Separates high-level planning from reactive low-level frame executions.
    """
    global current_plan
    current_plan = {
        "goal": goal_description,
        "steps": action_steps
    }
    print(f"\n📋 [New Plan Created] Goal: {goal_description}")
    for idx, step in enumerate(action_steps):
        print(f"   {idx+1}. {step}")
    return f"Plan successfully created with {len(action_steps)} steps."

def update_plan(status: str, reason: str, next_steps: list):
    """
    Force-update the active plan upon encountering obstacles or deadlocks.
    Constraint: Enforces a strict 1-5 word limit on 'reason' to optimize token consumption and focus.
    """
    words = reason.strip().split()
    if len(words) < 1:
        reason = "Stuck"
    elif len(words) > 5:
        reason = " ".join(words[:5])

    global current_plan
    current_plan = {
        "goal": f"Recovered/Updated ({status}): {reason}",
        "steps": next_steps
    }
    print(f"\n🔄 [Plan Updated] Status: {status} | Reason: {reason}")
    for idx, step in enumerate(next_steps):
        print(f"   {idx+1}. {step}")
    return "Plan successfully updated."

def key_action(key: str, action_type: str, hold_duration: float = 0.1):
    """
    Map high-level key commands to OS-level inputs via pynput.
    Quirk: Maps string identifiers to pynput SpecialKey objects where necessary.
    """
    print(f"🎮 [Keyboard] {action_type} -> {key} (duration: {hold_duration}s)")
    try:
        target_key = key.lower()
        if target_key == "space":
            target_key = pynput.keyboard.Key.space
        elif target_key == "left":
            target_key = pynput.keyboard.Key.left
        elif target_key == "right":
            target_key = pynput.keyboard.Key.right

        if action_type == "press_key":
            keyboard_ctrl.press(target_key)
            time.sleep(hold_duration)
            keyboard_ctrl.release(target_key)
        elif action_type == "key_down":
            keyboard_ctrl.press(target_key)
        elif action_type == "key_up":
            keyboard_ctrl.release(target_key)
        return f"Success: {action_type} {key}"
    except Exception as e:
        return f"Error: {str(e)}"

def mouse_action(action: str, button: str = "left", x: int = None, y: int = None):
    """
    Control mouse aiming and clicks based on absolute window client coordinates.
    Design Choice: Moves the system cursor directly to target coordinates prior to clicking.
    """
    print(f"🖱️ [Mouse] Action: {action}, Button: {button}, Pos: ({x}, {y})")
    try:
        if x is not None and y is not None:
            win32api.SetCursorPos((x, y))
            time.sleep(0.02) # Brief delay to allow cursor repositioning before click event.

        btn = pynput.mouse.Button.left if button == "left" else pynput.mouse.Button.right
        
        if action == "move":
            pass
        elif action == "click":
            mouse_ctrl.click(btn, 1)
        elif action == "press":
            mouse_ctrl.press(btn)
        elif action == "release":
            mouse_ctrl.release(btn)
        return f"Success: mouse {action}"
    except Exception as e:
        return f"Error: {str(e)}"

def update_game_memory(rule: str):
    """
    Persist newly discovered rules or environment mechanics into the global memory buffer.
    Design Choice: Avoids context window bloat by maintaining a single mutable summary variable instead of full chat history.
    """
    global game_memory
    game_memory = rule
    print(f"\n📝 [Memory Updated]:\n{game_memory}")
    return "Memory successfully updated."

available_tools = {
    "create_plan": create_plan,
    "update_plan": update_plan,
    "key_action": key_action,
    "mouse_action": mouse_action,
    "update_game_memory": update_game_memory
}

# --- OpenAI Function Calling Tool Schemas ---

tools_definition = [
    {
        "type": "function",
        "function": {
            "name": "create_plan",
            "description": "Analyze the current screen frames and establish a short-term tactical goal with a sequential list of action steps.",
            "parameters": {
                "type": "object",
                "properties": {
                    "goal_description": {"type": "string", "description": "The current short-term objective (e.g., 'Move to the upper platform')"},
                    "action_steps": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Sequential list of sub-actions to perform"
                    }
                },
                "required": ["goal_description", "action_steps"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_plan",
            "description": "Discard current plan and update to a recovery plan when dead, blocked, or stuck. The 'reason' field MUST be strictly between 1 to 5 words.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "description": "Current status (e.g., 'DEADLOCK', 'STUCK', 'OBSTACLE')"},
                    "reason": {"type": "string", "description": "Reason for modifying the plan. MUST be concise, strictly between 1 to 5 words."},
                    "next_steps": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "New alternative action step list"
                    }
                },
                "required": ["status", "reason", "next_steps"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "key_action",
            "description": "Control keyboard actions such as movement, jumping, and skill triggers.",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Key to press (e.g., 'space', 'left', 'right', 'a', 'd', 'w', 's')"},
                    "action_type": {"type": "string", "enum": ["press_key", "key_down", "key_up"]},
                    "hold_duration": {"type": "number", "description": "Duration to hold the key in seconds"}
                },
                "required": ["key", "action_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "mouse_action",
            "description": "Control mouse cursor movement, crosshair aiming, clicking, and holding.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["move", "click", "press", "release"]},
                    "button": {"type": "string", "enum": ["left", "right"]},
                    "x": {"type": "integer", "description": "Absolute screen X coordinate if needed"},
                    "y": {"type": "integer", "description": "Absolute screen Y coordinate if needed"}
                },
                "required": ["action"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_game_memory",
            "description": "Record newly discovered aiming mechanics, terrain rules, or strategies into the global game memory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "rule": {"type": "string", "description": "Full updated memory content"}
                },
                "required": ["rule"]
            }
        }
    }
]

# --- Win32 Window Tracking & Client Area Capture ---

def find_window_hwnd(window_title: str):
    """
    Enumerate top-level windows to locate the target game handle matching the title substring.
    """
    results = []
    def enum_windows_callback(hwnd, extra):
        if win32gui.IsWindowVisible(hwnd):
            text = win32gui.GetWindowText(hwnd)
            if window_title in text:
                extra.append(hwnd)
    win32gui.EnumWindows(enum_windows_callback, results)
    return results[0] if results else None

def capture_game_client_area(window_title: str):
    """
    Capture only the client area of the target game window using win32gui and mss.
    Design Choice: Caches the HWND globally to avoid expensive EnumWindows overhead per frame.
    """
    global cached_hwnd
    try:
        if not cached_hwnd or not win32gui.IsWindow(cached_hwnd):
            cached_hwnd = find_window_hwnd(window_title)
            if not cached_hwnd:
                return None

        # Convert window-relative client rect coordinates to absolute screen coordinates.
        client_rect = win32gui.GetClientRect(cached_hwnd)
        left_top = win32gui.ClientToScreen(cached_hwnd, (client_rect[0], client_rect[1]))
        right_bottom = win32gui.ClientToScreen(cached_hwnd, (client_rect[2], client_rect[3]))

        left, top = left_top
        right, bottom = right_bottom
        width = right - left
        height = bottom - top

        if width <= 0 or height <= 0:
            return None

        capture_area = {"top": top, "left": left, "width": width, "height": height}

        # Grab screenshot via mss, resize for token optimization, and encode to base64 JPEG.
        with mss.mss() as sct:
            sct_img = sct.grab(capture_area)
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            img.thumbnail(SCREEN_THUMBNAIL_SIZE)
            
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=JPEG_QUALITY)
            return base64.b64encode(buffer.getvalue()).decode("utf-8")
    except Exception as e:
        cached_hwnd = None
        return None

# --- Main Autonomous Agent Loop ---

def autonomous_agent_loop(window_title: str = TARGET_WINDOW_TITLE, language: str = DEFAULT_AGENT_LANGUAGE):
    """
    Main event loop handling visual observation, LLM reasoning via Tool Calling, and Circuit Breaker logic.
    Param window_title: Target game window title string.
    Param language: Sets the language context for internal reasoning and system instructions (e.g., 'en', 'ko').
    """
    global last_action_time, stuck_detection_count, current_plan
    
    frame_history = []
    max_frames = MAX_SHORT_TERM_FRAMES

    print(f"🚀 [Autonomous Agent Started] Target Window: '{window_title}' | Language: {language}")
    
    try:
        while True:
            img_b64 = capture_game_client_area(window_title)
            if not img_b64:
                time.sleep(0.5)
                continue

            frame_history.append(img_b64)
            if len(frame_history) > max_frames:
                frame_history.pop(0)

            # Circuit Breaker Pattern: Forces recovery planning if screen state or actions remain stagnant beyond timeout.
            current_time = time.time()
            if current_time - last_action_time > CIRCUIT_BREAKER_TIMEOUT:
                stuck_detection_count += 1
                print(f"⚠️ [Circuit Breaker] Deadlock/Stuck suspected! Count: {stuck_detection_count}")
                current_plan = {"goal": "RECOVERY_MODE", "steps": ["Press R or Jump to escape stuck position", "Change movement direction"]}
                last_action_time = current_time

            # Dynamic language instruction injected into system prompt based on user parameter.
            lang_instruction = f"All reasoning, plan goals, and plan steps must be written in '{language}' language." if language != "en" else "All reasoning must be in English."

            system_prompt = f"""
            You are an autonomous AI agent playing a 2D action platformer game using both keyboard and mouse.
            Analyze the sequence of game screens, check the [Global Memory] and [Current Plan], and execute tools.
            You must use 'create_plan' or 'update_plan' to structure your tactical actions. No human help is available; you must recover from deaths or obstacles by yourself.
            {lang_instruction}
            
            [Global Game Memory]
            {game_memory}
            
            [Current Plan State]
            Goal: {current_plan.get('goal')}
            Steps: {json.dumps(current_plan.get('steps'))}
            """

            user_content = []
            for b64 in frame_history:
                user_content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
                })
            user_content.append({"type": "text", "text": "Analyze the gameplay frames. Execute tools to plan and control keyboard/mouse."})

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ]

            # Invoke the OmniRoute / OpenAI compatible LLM endpoint.
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                tools=tools_definition,
                tool_choice="auto",
                max_tokens=300
            )

            response_message = response.choices[0].message

            if response_message.tool_calls:
                last_action_time = time.time() # Reset inactivity timer upon valid action execution.
                for tool_call in response_message.tool_calls:
                    fn_name = tool_call.function.name
                    fn_args = json.loads(tool_call.function.arguments)
                    
                    if fn_name in available_tools:
                        result = available_tools[fn_name](**fn_args)
                        print(f"   └ [Tool Result]: {result}")
            else:
                if response_message.content:
                    print(f"\n💬 [AI Reasoning]: {response_message.content}")

            time.sleep(TICK_INTERVAL)

            # NOTE: Loop delay is kept low to ensure responsive frame-by-frame monitoring.

    except KeyboardInterrupt:
        print("\n🛑 Autonomous Agent stopped by user.")

if __name__ == "__main__":
    # Execute the autonomous agent loop with parameters defined at the top.
    autonomous_agent_loop()
