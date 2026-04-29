from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import webbrowser
from dotenv import load_dotenv
from typing import List, Dict, Any

# --- Optional imports ---
try:
    import pywhatkit
except ImportError:
    pywhatkit = None

try:
    import wikipediaapi
except ImportError:
    wikipediaapi = None

# --- AI core ---
try:
    from app.core.perplexity_ai import ask_perplexity
except ImportError:
    def ask_perplexity(prompt, mode, history):
        return "AI module not found."

# ================= INIT =================
load_dotenv()

app = FastAPI(title="NOVA Web API", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================= WIKI =================
wiki = None
if wikipediaapi:
    wiki = wikipediaapi.Wikipedia(
        user_agent="NOVA-Assistant/1.0",
        language="en"
    )

# ================= SCHEMA =================
class AskRequest(BaseModel):
    prompt: str = ""
    tab: str = "chat"
    mode: str = "focus"
    memory: List[Dict[str, Any]] = []

class AskResponse(BaseModel):
    answer: str

# ================= MODE PROMPT =================
def build_mode_prompt(prompt: str, mode: str) -> str:
    mode = mode.upper()

    if mode == "FOCUS":
        return f"Give a short and direct answer:\n{prompt}"

    elif mode == "STUDY":
        return f"Explain in a detailed and educational way with examples:\n{prompt}"

    elif mode == "BUILD":
        return f"Give a technical or coding-focused structured answer:\n{prompt}"

    elif mode == "ACTION":
        return f"Give practical step-by-step actionable guidance:\n{prompt}"

    elif mode == "RESEARCH":
        return f"Provide a deep, analytical explanation with insights:\n{prompt}"

    return prompt

# ================= MODE OUTPUT =================
def apply_mode_behavior(answer: str, mode: str) -> str:
    mode = mode.upper()

    if mode == "FOCUS":
        return answer.split(".")[0] + "."

    elif mode == "STUDY":
        return f"📘 Detailed Explanation:\n{answer}"

    elif mode == "BUILD":
        return f"🛠 Developer Mode:\n{answer}"

    elif mode == "ACTION":
        return f"⚡ Action Steps:\n{answer}"

    elif mode == "RESEARCH":
        return f"🔬 Deep Research:\n{answer}"

    return answer

# ================= LOCAL COMMANDS =================
def handle_local_commands(prompt: str) -> str | None:
    c = prompt.lower().strip()
    now = datetime.now()

    if "date" in c or "day" in c or "time" in c:
        parts = []

        if "day" in c:
            parts.append(f"Today is {now.strftime('%A')}")

        if "date" in c:
            parts.append(f"Today's date is {now.strftime('%B %d, %Y')}")

        if "time" in c:
            parts.append(f"The time is {now.strftime('%I:%M %p')}")

        return " · ".join(parts)

    if c.startswith(("open ", "go to ")):
        site = c.replace("open", "").replace("go to", "").strip()
        if "." not in site:
            site += ".com"
        webbrowser.open("https://" + site)
        return f"Opening {site}..."

    if c.startswith(("play ", "play song", "play music")):
        if not pywhatkit:
            return "PyWhatKit not installed."

        song = c.replace("play song", "").replace("play music", "").replace("play", "").strip()
        pywhatkit.playonyt(song)
        return f"Playing {song} on YouTube 🎵"

    return None

# ================= WIKIPEDIA =================
def get_wikipedia_summary(topic: str) -> str:
    if not wiki:
        return "Wikipedia not available."

    try:
        page = wiki.page(topic)
        if not page.exists():
            return f"No Wikipedia page found for '{topic}'."
        return page.summary[:2000] + "..."
    except:
        return "Error fetching Wikipedia data."

# ================= MAIN ENDPOINT =================
@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    prompt = (req.prompt or "").strip()

    if not prompt:
        return {"answer": "Please ask something."}

    print("MODE RECEIVED:", req.mode)

    # ---------- LOCAL ----------
    local = handle_local_commands(prompt)
    if local:
        final = apply_mode_behavior(local, req.mode)
        return {"answer": final}

    # ---------- WIKIPEDIA → AI (FIXED) ----------
    if prompt.lower().startswith(("who is", "what is", "tell me about")):
        topic = (
            prompt.lower()
            .replace("who is", "")
            .replace("what is", "")
            .replace("tell me about", "")
            .strip()
        )

        if topic:
            wiki_data = get_wikipedia_summary(topic)

            enhanced_prompt = build_mode_prompt(
                f"Using this information, answer properly:\n{wiki_data}",
                req.mode
            )

            result = ask_perplexity(
                prompt=enhanced_prompt,
                mode=req.mode.upper(),
                history=req.memory
            )

            final = apply_mode_behavior(str(result), req.mode)
            return {"answer": final}

    # ---------- AI ----------
    try:
        enhanced_prompt = build_mode_prompt(prompt, req.mode)

        result = ask_perplexity(
            prompt=enhanced_prompt,
            mode=req.mode.upper(),
            history=req.memory
        )

        final = apply_mode_behavior(str(result), req.mode)
        return {"answer": final}

    except Exception:
        return {"answer": "AI service is currently unavailable."}