import os
import re

KEYWORDS = {
    "tick":       ["clock", "tick", "fps", "framerate", "frame_rate", "cap", "60", "30", "120"],
    "movement":   ["player", "move", "velocity", "speed", "input", "direction", "dx", "dy"],
    "render":     ["draw", "render", "blit", "screen", "display", "surface"],
    "collision":  ["collide", "hitbox", "rect", "overlap", "intersect"],
    "score":      ["score", "point", "count", "total"],
    "audio":      ["sound", "music", "play", "volume", "mixer"],
    "input":      ["event", "keydown", "mousebutton", "keyboard", "mouse", "input"],
    "spawn":      ["spawn", "create", "instantiate", "generate", "enemy", "object"],
    "ui":         ["button", "menu", "label", "text", "font", "hud"],
    "save":       ["save", "load", "file", "json", "pickle", "read", "write"],
    "network":    ["socket", "server", "client", "request", "http", "connect"],
    "camera":     ["camera", "viewport", "scroll", "offset"],
    "animation":  ["animation", "frame", "sprite", "sheet"],
    "physics":    ["gravity", "velocity", "acceleration", "friction", "jump"],
    "shader":     ["shader", "glsl", "hlsl", "material"],
}

SUPPORTED_FILE_TYPE = {
    ".py", ".js", ".ts", ".jsx", ".tsx",
    ".cpp", ".h", ".hpp", ".c",
    ".cs", ".java", ".go", ".rs",
    ".html", ".css", ".json", ".yaml", ".yml",
    ".lua", ".rb", ".php", ".swift", ".kt"
}

SKIP_DIRS = {"__pycache__", "node_modules", ".git", "venv", "env", ".venv", "dist", "build"}


def find_relevant_files(folder, prompt):
    prompt_lower = prompt.lower()

    mentioned_filenames = set(re.findall(r'\b[\w\-]+\.\w+\b', prompt_lower))

    all_files = []
    for root, dirs, files in os.walk(folder):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]

        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext not in SUPPORTED_FILE_TYPE:
                continue
            all_files.append(os.path.join(root, file))

    exact_matches = []
    for path in all_files:
        if os.path.basename(path).lower() in mentioned_filenames:
            exact_matches.append(path)

    if exact_matches:
        return exact_matches[:3]

    scored = []
    for path in all_files:
        filename = os.path.basename(path).lower()

        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read().lower()
        except Exception:
            continue

        score = 0

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

        name_no_ext = os.path.splitext(filename)[0]
        if name_no_ext in prompt_lower:
            score += 5

        if score > 0:
            scored.append((score, path))

    scored.sort(reverse=True)

    return [path for _, path in scored[:3]]