import requests
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

SYSTEM_PROMPT = """You are a code editing assistant. You only do one thing: make the exact change the user asks for.

Your entire response must follow this format and nothing else:
File: <filename>
Line: <line number>
Change: replace `<old code>` with `<new code>`

Do not describe the code. Do not summarize. Do not explain. Do not use bullet points.
Only output the File, Line, and Change. That is all."""

def _try_model(model, prompt, codebase):
    """Try a single model. Returns (success, response_text)."""
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Request: {prompt}\n\nCode:\n{codebase}"}
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
    """
    Try models in fallback order.
    If a specific model is passed (from UI dropdown), try it first,
    then fall back to the list if it fails.
    """
    models_to_try = []

    if model and model not in FALLBACK_MODELS:
        models_to_try.append(model)

    if model and model in FALLBACK_MODELS:
        idx = FALLBACK_MODELS.index(model)
        models_to_try = FALLBACK_MODELS[idx:]
    else:
        models_to_try += FALLBACK_MODELS

    last_error = "All models failed."

    for m in models_to_try:
        try:
            success, result = _try_model(m, prompt, codebase)
            if success:
                return f"[{m}]\n\n{result}"
            else:
                last_error = f"{m}: {result}"
        except requests.exceptions.Timeout:
            last_error = f"{m}: Timed out"
        except requests.exceptions.ConnectionError:
            return "Error: No internet connection."
        except Exception as e:
            last_error = f"{m}: {str(e)}"

    return f"All models failed. Last error: {last_error}"