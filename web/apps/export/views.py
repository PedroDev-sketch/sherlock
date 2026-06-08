from django.http import HttpResponse, HttpResponseBadRequest

from apps.core.dtos import SearchRequest
from apps.core.services import SherlockService
from apps.export.exporters import to_csv, to_json

_ALLOWED_FORMATS = {"csv", "json"}


def export_view(request):
    username = request.GET.get("username", "").strip()
    fmt = request.GET.get("format", "").strip().lower()

    if not username:
        return HttpResponseBadRequest("Parâmetro 'username' é obrigatório.")

    if fmt not in _ALLOWED_FORMATS:
        return HttpResponseBadRequest(f"Formato '{fmt}' não suportado. Use csv ou json.")

    service = SherlockService()
    results = list(service.search(SearchRequest(username=username)))

    if fmt == "csv":
        content = to_csv(results)
        response = HttpResponse(content, content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="{username}.csv"'
    else:
        content = to_json(results, username=username)
        response = HttpResponse(content, content_type="application/json")
        response["Content-Disposition"] = f'attachment; filename="{username}.json"'

    return response
