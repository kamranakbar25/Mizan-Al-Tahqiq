import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from django.conf import settings


OLLAMA_BASE_URL = settings.OLLAMA_BASE_URL
DEFAULT_TIMEOUT = settings.OLLAMA_TIMEOUT


class OllamaError(Exception):
    """Base exception for local Ollama runtime errors."""


class OllamaConnectionError(OllamaError):
    """Ollama is unavailable or unreachable."""


class OllamaTimeoutError(OllamaError):
    """Ollama request exceeded the configured timeout."""


class OllamaModelError(OllamaError):
    """Requested model is unavailable or returned an error."""


def _validate_local_url():
    parsed = urlparse(OLLAMA_BASE_URL)

    if (
        parsed.scheme != "http"
        or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}
        or parsed.port != 11434
        or parsed.username
        or parsed.password
    ):
        raise OllamaConnectionError(
            "Only the local Ollama runtime is permitted."
        )


def _request(endpoint, payload=None, timeout=DEFAULT_TIMEOUT):
    _validate_local_url()

    url = f"{OLLAMA_BASE_URL}{endpoint}"

    headers = {"Content-Type": "application/json"}
    data = None

    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    request = Request(
        url,
        data=data,
        headers=headers,
        method="POST" if data is not None else "GET",
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    except HTTPError as exc:
        try:
            error_body = exc.read().decode("utf-8")
        except Exception:
            error_body = str(exc)

        raise OllamaModelError(
            f"Ollama returned HTTP {exc.code}: {error_body}"
        ) from exc

    except (TimeoutError, OSError) as exc:
        if isinstance(exc, TimeoutError):
            raise OllamaTimeoutError(
                "Ollama request timed out."
            ) from exc

        raise OllamaConnectionError(
            f"Could not connect to local Ollama: {exc}"
        ) from exc

    except URLError as exc:
        if isinstance(exc.reason, TimeoutError):
            raise OllamaTimeoutError(
                "Ollama request timed out."
            ) from exc

        raise OllamaConnectionError(
            f"Could not connect to local Ollama: {exc.reason}"
        ) from exc

    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise OllamaError(
            "Ollama returned an invalid response."
        ) from exc


def check_health():
    """Check whether the local Ollama API is reachable."""
    return _request("/api/tags", timeout=10)


def list_models():
    """Return installed local Ollama models."""
    result = check_health()
    return result.get("models", [])


def generate(
    prompt,
    model="qwen3:4b",
    timeout=DEFAULT_TIMEOUT,
):
    """Generate text using a local Ollama model."""
    if not prompt or not prompt.strip():
        raise ValueError("Prompt cannot be empty.")

    result = _request(
        "/api/chat",
        {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "stream": False,
        },
        timeout=timeout,
    )

    message = result.get("message", {})
    content = message.get("content")

    if not isinstance(content, str):
        raise OllamaModelError(
            "Model did not return valid message content."
        )

    return content


def embed(
    text,
    model="qwen3-embedding:0.6b",
    timeout=DEFAULT_TIMEOUT,
):
    """Generate embeddings using a local Ollama model."""
    if not text:
        raise ValueError("Embedding input cannot be empty.")

    result = _request(
        "/api/embed",
        {
            "model": model,
            "input": text,
        },
        timeout=timeout,
    )

    embeddings = result.get("embeddings")

    if not embeddings or not isinstance(embeddings, list):
        raise OllamaModelError(
            "Model did not return valid embeddings."
        )

    return embeddings
