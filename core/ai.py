import requests
import re
from config import OPENROUTER_API_KEY

FALLBACK_MODELS = [
    "nvidia/nemotron-3-super-120b-a12b:free",
    "qwen/qwen3-coder:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "google/gemma-4-31b-it:free",
    "openai/gpt-oss-120b:free",
    "z-ai/glm-4.5-air:free",
    "openrouter/free",
]

CHANGE_SYSTEM_PROMPT = """You are a code editing assistant. The user wants to make a specific change to their code.

Respond ONLY in this exact format with no other text:
File: <filename>
Line: <line number>
Change: replace `<old code>` with `<new code>`

Output nothing else. No thinking. No explanation. No preamble."""

QUESTION_SYSTEM_PROMPT = """You are DevScope, an expert coding assistant. Answer the user's question directly.

Rules:
- Start your answer immediately. No preamble.
- Never say "The user asks..." or "The user wants..." or "Looking at the code..."
- Never show your thinking or reasoning process
- Be concise and practical
- Speak directly to the developer"""

CHANGE_KEYWORDS = [
    "change", "replace", "fix", "update", "rename", "delete", "remove",
    "add", "insert", "move", "refactor", "modify", "set", "make it",
    "switch", "convert", "rewrite", "edit"
]

def is_change_request(prompt):
    prompt_lower = prompt.lower().strip()

    question_starters = [
        "what", "why", "how", "when", "where", "which", "who",
        "should", "could", "would", "can", "is ", "are ", "does",
        "do i", "tell me", "explain", "describe", "show me"
    ]
    for starter in question_starters:
        if prompt_lower.startswith(starter):
            return False

    for keyword in CHANGE_KEYWORDS:
        if keyword in prompt_lower:
            return True

    return False

def strip_reasoning(text):
    """Remove reasoning leaks from model output."""

    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)

    text = re.sub(r'^(Okay|Alright|Sure|Right|So)[,.]?\s*', '', text, flags=re.IGNORECASE)

    lines = text.split('\n')
    reasoning_line_patterns = [
        r'the user (asks?|wants?|said|needs?|is asking|is)',
        r'we need to',
        r"let me (think|consider|look|check|analyze|formulate)",
        r"i need to",
        r"i (can|will|should|must) ",
        r"i('ll| will) ",
        r"looking at (the )?code",
        r"looking at (the )?file",
        r"since they want",
        r"they want to keep",
        r"they need to",
        r"i (just|only) need",
        r"but to be helpful",
        r"i'll (mention|note|suggest|state)",
        r"i could suggest",
        r"but (we|i) don't have",
        r"however[,] i don't",
    ]

    clean_lines = []
    skip_block = False

    for line in lines:
        line_lower = line.lower().strip()

        is_reasoning = any(re.search(p, line_lower) for p in reasoning_line_patterns)

        if is_reasoning:
            skip_block = True
            continue

        if skip_block:
            if line.strip() and not line_lower.startswith(('```', '#')):
                real_answer_starters = [
                    'file:', 'line:', 'change:', '-', '*', '•',
                    'keep', 'remove', 'you can', 'you should',
                    'recommended', 'suggest', 'here'
                ]
                if any(line_lower.startswith(s) for s in real_answer_starters):
                    skip_block = False

        if not skip_block:
            clean_lines.append(line)

    result = '\n'.join(clean_lines).strip()

    if not result:
        return text.strip()

    return result

def _try_model(model, system_prompt, user_message):
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            "temperature": 0.1,
            "max_tokens": 500,
        },
        timeout=30
    )

    data = response.json()

    if "error" in data:
        return False, data["error"]["message"]

    content = data["choices"][0]["message"]["content"]

    if not content or not content.strip():
        return False, "Empty response"

    return True, content.strip()


def ask_ai(prompt, codebase, project_types, model=None):
    if is_change_request(prompt):
        system_prompt = CHANGE_SYSTEM_PROMPT
        user_message = f"Request: {prompt}\n\nCode:\n{codebase}"
    else:
        system_prompt = QUESTION_SYSTEM_PROMPT
        user_message = f"Question: {prompt}\n\nProject code for context:\n{codebase}"

    models_to_try = []
    if model and model in FALLBACK_MODELS:
        idx = FALLBACK_MODELS.index(model)
        models_to_try = FALLBACK_MODELS[idx:]
    elif model:
        models_to_try = [model] + FALLBACK_MODELS
    else:
        models_to_try = FALLBACK_MODELS

    last_error = "All models failed."

    for m in models_to_try:
        try:
            success, result = _try_model(m, system_prompt, user_message)
            if success:
                clean = strip_reasoning(result)
                return f"[{m}]\n\n{clean}"
            else:
                last_error = f"{m}: {result}"
        except requests.exceptions.Timeout:
            last_error = f"{m}: Timed out"
        except requests.exceptions.ConnectionError:
            return "Error: No internet connection."
        except Exception as e:
            last_error = f"{m}: {str(e)}"

    return f"All models failed. Last error: {last_error}"