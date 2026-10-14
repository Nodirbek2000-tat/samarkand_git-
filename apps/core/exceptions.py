from rest_framework import status
from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    """
    Uniform error shape for the frontend:
    {"detail": "human message", "errors": {"field": ["message", ...]}}
    """
    response = exception_handler(exc, context)
    if response is None:
        return None

    data = response.data
    if isinstance(data, dict) and set(data.keys()) <= {"detail", "code"}:
        response.data = {"detail": str(data.get("detail", ""))}
        return response

    errors = data if isinstance(data, dict) else {"non_field_errors": data}
    first = next(iter(errors.values()), None)
    if isinstance(first, list) and first:
        first = first[0]
    detail = str(first) if first else "So‘rovda xatolik bor."
    if response.status_code == status.HTTP_400_BAD_REQUEST:
        detail = "Ma’lumotlarni tekshiring: " + detail
    response.data = {"detail": detail, "errors": errors}
    return response
