import re

import httpx

SUPPORTED_PROVIDERS = {
    "openai": {
        "label": "OpenAI",
        "key_format": re.compile(r"^sk-[A-Za-z0-9]{20,}$"),
        "validate_url": "https://api.openai.com/v1/models",
        "auth_header": "Authorization",
        "auth_scheme": "Bearer",
    },
    "anthropic": {
        "label": "Anthropic",
        "key_format": re.compile(r"^sk-ant-[A-Za-z0-9]{20,}$"),
        "validate_url": "https://api.anthropic.com/v1/messages",
        "auth_header": "x-api-key",
        "auth_scheme": None,
    },
    "google": {
        "label": "Google Gemini",
        "key_format": re.compile(r"^AIza[A-Za-z0-9_-]{10,}$"),
        "validate_url": None,
        "auth_header": None,
        "auth_scheme": None,
    },
    "openrouter": {
        "label": "OpenRouter",
        "key_format": re.compile(r"^sk-or-[A-Za-z0-9]{20,}$"),
        "validate_url": "https://openrouter.ai/api/v1/auth/key",
        "auth_header": "Authorization",
        "auth_scheme": "Bearer",
    },
    "groq": {
        "label": "Groq",
        "key_format": re.compile(r"^gsk_[A-Za-z0-9]{20,}$"),
        "validate_url": "https://api.groq.com/openai/v1/models",
        "auth_header": "Authorization",
        "auth_scheme": "Bearer",
    },
    "ollama": {
        "label": "Ollama",
        "key_format": None,
        "validate_url": None,
        "auth_header": None,
        "auth_scheme": None,
    },
}


def validate_key_format(provider: str, key: str) -> tuple[bool, str]:
    info = SUPPORTED_PROVIDERS.get(provider)
    if not info:
        return False, f"Unknown provider: {provider}"

    if info["key_format"] is None:
        return True, "No key required"

    if not key or not key.strip():
        return False, "Key is required"

    if info["key_format"].match(key.strip()):
        return True, "Format valid"
    return False, f"Invalid key format for {info['label']}"


async def validate_key_live(provider: str, key: str) -> tuple[bool, str]:
    info = SUPPORTED_PROVIDERS.get(provider)
    if not info:
        return False, f"Unknown provider: {provider}"

    if info["validate_url"] is None:
        return True, "No live validation available"

    headers = {}
    if info["auth_header"] and info["auth_scheme"]:
        headers[info["auth_header"]] = f"{info['auth_scheme']} {key.strip()}"
    elif info["auth_header"]:
        headers[info["auth_header"]] = key.strip()

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            if provider == "google":
                resp = await client.get(
                    f"https://generativelanguage.googleapis.com/v1/models?key={key.strip()}"
                )
            else:
                resp = await client.get(info["validate_url"], headers=headers)

            if resp.status_code == 200:
                return True, "Key validated successfully"
            elif resp.status_code == 401:
                return False, "Invalid or revoked API key"
            elif resp.status_code == 403:
                return False, "API key lacks required permissions"
            else:
                return False, f"Validation failed (HTTP {resp.status_code})"
    except httpx.TimeoutException:
        return False, "Validation request timed out"
    except httpx.RequestError as e:
        return False, f"Connection error: {e}"


def get_provider_info() -> dict:
    return {
        name: {"label": info["label"]}
        for name, info in SUPPORTED_PROVIDERS.items()
    }
