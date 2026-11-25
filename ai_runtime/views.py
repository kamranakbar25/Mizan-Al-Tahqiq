from django.http import JsonResponse
from django.views.decorators.http import require_GET

from ai_runtime.services import ollama


@require_GET
def health_check(request):
    """
    Return the health status of the local AI runtime.
    """

    required_models = {
        "llm": "qwen3:4b",
        "embedding": "qwen3-embedding:0.6b",
    }

    try:
        installed_models = ollama.list_models()

        installed_names = {
            model.get("name")
            for model in installed_models
        }

        model_status = {
            key: {
                "model": model_name,
                "available": model_name in installed_names,
            }
            for key, model_name in required_models.items()
        }

        all_models_available = all(
            item["available"]
            for item in model_status.values()
        )

        return JsonResponse(
            {
                "status": (
                    "healthy"
                    if all_models_available
                    else "degraded"
                ),
                "runtime": "ollama",
                "mode": "local_only",
                "connection": "connected",
                "models": model_status,
            },
            status=200 if all_models_available else 503,
        )

    except ollama.OllamaError as exc:
        return JsonResponse(
            {
                "status": "unavailable",
                "runtime": "ollama",
                "mode": "local_only",
                "connection": "failed",
                "error": str(exc),
            },
            status=503,
        )
