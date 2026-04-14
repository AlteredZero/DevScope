import os
import json
from datetime import datetime

MAX_HISTORY = 25
HISTORY_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "history")


def _ensure_history_dir():
    os.makedirs(HISTORY_DIR, exist_ok=True)


def save_exchange(folder, prompt, response):
    """Save a single prompt/response exchange to history."""
    _ensure_history_dir()

    entry = {
        "timestamp": datetime.now().isoformat(),
        "project": folder,
        "prompt": prompt,
        "response": response,
    }

    history = load_history()

    history.insert(0, entry)

    history = history[:MAX_HISTORY]

    history_file = os.path.join(HISTORY_DIR, "history.json")
    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)


def load_history():
    """Load all saved history entries. Returns list of dicts."""
    history_file = os.path.join(HISTORY_DIR, "history.json")
    if not os.path.exists(history_file):
        return []
    try:
        with open(history_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def format_history_entry(entry):
    """Format a history entry for display."""
    ts = entry.get("timestamp", "")[:19].replace("T", " ")
    project = os.path.basename(entry.get("project", "Unknown"))
    prompt = entry.get("prompt", "")
    response = entry.get("response", "")
    return (
        f"[{ts}] Project: {project}\n"
        f"Prompt: {prompt}\n"
        f"Response:\n{response}"
    )