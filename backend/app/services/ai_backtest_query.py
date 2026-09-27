import json
import re

import requests

from app.core.config import AI_API_BASE_URL, AI_MODEL


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

    simple_interpretation = _parse_simple_backtest_question(question)
    if simple_interpretation:
        return simple_interpretation

    response_schema = {
        "supported": "boolean",
        "symbol": "ticker symbol",
        "years": "integer from 1 to 20 when period is years, otherwise null",
        "lookback_trading_days": "integer from 1 to 10000 when specified, otherwise null",
        "timeframe": "day or week",
        "threshold_percent": "number from 0 to 100; use 0 when the user asks for all gains/losses without a threshold",
        "reason": "short explanation when unsupported",
    }
    system_prompt = (
        "Convert the user's market question into a backtest request. "
        "Do not write SQL, code, or a financial recommendation. "
        "Only support counting daily or weekly close-to-close percentage moves greater than "
        "a non-negative threshold or less than the corresponding negative threshold, "
        "for one symbol over a lookback in years or trading days. Weekly means one "
        "close on the last trading day of each week compared with the previous week's "
        "last trading day close. For example, 3% means strictly greater than +3% and "
        "strictly less than -3%. If the user asks for gains/losses or moves without "
        "a threshold, use 0% so every positive gain and negative loss is included. "
        "If the user omits the lookback, use 2 years; if they omit the threshold, use 0%; "
        "if they omit the timeframe, use day. Set "
        "supported=false for other analysis types or unclear symbols. Return one JSON "
        f"object matching this schema: {json.dumps(response_schema)}."
    )
    ollama_url = AI_API_BASE_URL.removesuffix("/v1")
    try:
        response = requests.post(
            f"{ollama_url}/api/chat",
            json={
                "model": AI_MODEL,
                "stream": False,
                "think": False,
                "format": "json",
                "options": {"temperature": 0, "num_predict": 128},
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question},
                ],
            },
            timeout=(5, 90),
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
        content = response_body["message"]["content"]
        parsed = json.loads(content)
    except (ValueError, KeyError, IndexError, TypeError) as error:
        raise AIResponseInvalid("Ollama returned an invalid response.") from error

    if not isinstance(parsed, dict):
        raise AIResponseInvalid("Ollama returned an invalid response.")
    return parsed


def _parse_simple_backtest_question(question: str) -> dict | None:
    ticker_match = re.search(
        r"\b([A-Z][A-Z0-9.-]{0,14})\s+(?=(?:closed?|moves?|moved|returns?|gained|fell|dropped)\b)",
        question,
    )
    threshold_match = re.search(r"(\d+(?:\.\d+)?)\s*%", question)
    trading_days_match = re.search(r"\b(\d+)\s+trading\s+days?\b", question, re.IGNORECASE)
    years_match = re.search(r"\blast\s+(\d+)\s+years?\b", question, re.IGNORECASE)
    week_match = re.search(r"\b(?:weekly|weeks?|per\s+week)\b", question, re.IGNORECASE)

    if not ticker_match or not threshold_match:
        return None
    if not trading_days_match and not years_match:
        return None

    lookback_trading_days = int(trading_days_match.group(1)) if trading_days_match else None
    years = int(years_match.group(1)) if years_match else None
    if (lookback_trading_days is not None and not 1 <= lookback_trading_days <= 10000) or (
        years is not None and not 1 <= years <= 20
    ):
        return None
    threshold = float(threshold_match.group(1))
    if not 0 < threshold <= 100:
        return None

    return {
        "supported": True,
        "symbol": ticker_match.group(1),
        "years": years,
        "lookback_trading_days": lookback_trading_days,
        "timeframe": "week" if week_match else "day",
        "threshold_percent": threshold,
    }
