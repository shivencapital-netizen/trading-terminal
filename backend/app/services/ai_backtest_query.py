import json

import requests

from app.core.config import AI_API_BASE_URL, AI_API_KEY, AI_MODEL


class AIProviderNotConfigured(Exception):
    pass


class AIProviderUnavailable(Exception):
    pass


class AIResponseInvalid(Exception):
    pass


def is_ai_provider_configured() -> bool:
    return bool(AI_API_BASE_URL.strip() and AI_MODEL.strip())


def get_ai_provider_status() -> dict:
    if not is_ai_provider_configured():
        return {
            "status": "not-configured",
            "provider": "Ollama",
            "model": AI_MODEL,
            "message": "Set AI_API_BASE_URL and AI_MODEL in backend/.env.",
        }

    ollama_url = AI_API_BASE_URL.removesuffix("/v1")
    try:
        response = requests.get(f"{ollama_url}/api/tags", timeout=(2, 5))
        response.raise_for_status()
        models = response.json().get("models", [])
    except requests.RequestException:
        return {
            "status": "offline",
            "provider": "Ollama",
            "model": AI_MODEL,
            "message": "Ollama is not responding. Start the Ollama app or run `ollama serve`.",
        }
    except (ValueError, AttributeError):
        return {
            "status": "offline",
            "provider": "Ollama",
            "model": AI_MODEL,
            "message": "Ollama returned an unreadable model list.",
        }

    available_models = {
        model.get("name")
        for model in models
        if isinstance(model, dict) and isinstance(model.get("name"), str)
    }
    model_with_latest = AI_MODEL if ":" in AI_MODEL else f"{AI_MODEL}:latest"
    if AI_MODEL not in available_models and model_with_latest not in available_models:
        return {
            "status": "model-missing",
            "provider": "Ollama",
            "model": AI_MODEL,
            "message": f"Download the selected model with `ollama pull {AI_MODEL}`.",
        }

    return {
        "status": "ready",
        "provider": "Ollama",
        "model": AI_MODEL,
        "message": "Ollama and the selected model are ready.",
    }


def parse_backtest_question(question: str) -> dict:
    if not is_ai_provider_configured():
        raise AIProviderNotConfigured

    response_schema = {
        "supported": "boolean",
        "symbol": "ticker symbol",
        "years": "integer from 1 to 20",
        "threshold_percent": "positive number from 0 to 100",
        "reason": "short explanation when unsupported",
    }
    system_prompt = (
        "Convert the user's market question into a backtest request. "
        "Do not write SQL, code, or a financial recommendation. "
        "Only support counting daily close-to-close percentage moves greater than "
        "a positive threshold or less than the corresponding negative threshold, "
        "for one symbol over a lookback in years. For example, 3% means strictly "
        "greater than +3% and strictly less than -3%. If the user omits the lookback, "
        "use 2 years; if they omit the threshold, use 3%. Set supported=false for "
        "other analysis types or unclear symbols. Return one JSON object matching "
        f"this schema: {json.dumps(response_schema)}."
    )
    try:
        response = requests.post(
            f"{AI_API_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {AI_API_KEY}"},
            json={
                "model": AI_MODEL,
                "temperature": 0,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question},
                ],
            },
            timeout=(5, 180),
        )
        response.raise_for_status()
    except requests.Timeout as error:
        raise AIProviderUnavailable("The local Ollama request timed out.") from error
    except requests.RequestException as error:
        raise AIProviderUnavailable(
            "Could not reach Ollama. Start Ollama and confirm the selected model is downloaded."
        ) from error

    try:
        response_body = response.json()
        content = response_body["choices"][0]["message"]["content"]
        parsed = json.loads(content)
    except (ValueError, KeyError, IndexError, TypeError) as error:
        raise AIResponseInvalid("Ollama returned an invalid response.") from error

    if not isinstance(parsed, dict):
        raise AIResponseInvalid("Ollama returned an invalid response.")
    return parsed
