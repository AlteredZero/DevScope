import os
import re

KEYWORDS = {
    "tick":       ["clock", "tick", "fps", "framerate", "frame_rate"],
    "movement":   ["player", "move", "velocity", "speed", "input"],
    "render":     ["draw", "render", "blit", "screen", "display"],
    "collision":  ["collide", "hitbox", "rect", "overlap"],
    "score":      ["score", "point", "count", "total"],
    "audio":      ["sound", "music", "play", "volume", "mixer"],
    "input":      ["event", "keydown", "mousebutton", "keyboard", "mouse"],
    "spawn":      ["spawn", "create", "instantiate", "generate", "enemy"],
    "ui":         ["button", "menu", "label", "text", "font", "hud"],
    "save":       ["save", "load", "file", "json", "pickle"],
    "network":    ["socket", "server", "client", "request", "http"],
    "camera":     ["camera", "viewport", "scroll", "offset"],
    "animation":  ["animation", "frame", "sprite", "sheet"],
    "physics":    ["gravity", "velocity", "acceleration", "friction", "jump"],
    "model":      ["model", "fallback", "openrouter", "api", "ai"],
    "config":     ["config", "settings", "key", "api_key", "setup"],
}

SUPPORTED_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx",
    ".cpp", ".h", ".hpp", ".c",
    ".cs", ".java", ".go", ".rs",
    ".html", ".css", ".json", ".yaml", ".yml",
    ".lua", ".rb", ".php", ".swift", ".kt"
}

SKIP_DIR_PATTERNS = {
    "__pycache__", "node_modules", ".git", "venv", "env", ".venv",
    "dist", "build", "site-packages", "lib", "lib64", "bin",
    "devscope-env", ".env", "eggs", ".eggs", "htmlcov", ".tox",
    "migrations", "static", "media"
}

def _is_skipped_path(path):
    """Return True if any part of the path is a known library/env folder."""
    parts = path.replace("\\", "/").split("/")
    for part in parts:
        if part.lower() in SKIP_DIR_PATTERNS:
            return True
    return False

def find_relevant_files(folder, prompt):
    prompt_lower = prompt.lower()
    mentioned_filenames = set(re.findall(r'\b[\w\-]+\.\w+\b', prompt_lower))

    all_files = []
    for root, dirs, files in os.walk(folder):
        dirs[:] = [
            d for d in dirs
            if d.lower() not in SKIP_DIR_PATTERNS and not d.startswith(".")
        ]

        if _is_skipped_path(root):
            continue

        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext not in SUPPORTED_EXTENSIONS:
                continue
            all_files.append(os.path.join(root, file))

    exact_matches = [
        p for p in all_files
        if os.path.basename(p).lower() in mentioned_filenames
    ]
    if exact_matches:
        return exact_matches[:3]

    scored = []
    for path in all_files:
        if _is_skipped_path(path):
            continue

        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read().lower()
        except Exception:
            continue

        score = 0
        filename = os.path.basename(path).lower()
        name_no_ext = os.path.splitext(filename)[0]

        for key, words in KEYWORDS.items():
            if key in prompt_lower:
                for word in words:
                    if word in content:
                        score += 1
                    if word in prompt_lower and word in content:
                        score += 1

        for word in re.findall(r'\b\w{4,}\b', prompt_lower):
            if word in content:
                score += 0.5

        if name_no_ext in prompt_lower:
            score += 5

        if score > 0:
            scored.append((score, path))

    scored.sort(reverse=True)
    return [path for _, path in scored[:3]]