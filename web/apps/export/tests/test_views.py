import pytest
from django.urls import reverse

from apps.core.dtos import SiteResult

pytestmark = pytest.mark.django_db

_FAKE_RESULTS = [
    SiteResult(site_name="GitHub", url="https://github.com/john_doe", status="found"),
    SiteResult(site_name="Reddit", url="https://reddit.com/user/john_doe", status="not_found"),
]


def test_export_view_csv_returns_text_csv_content_type(client, mocker):
    """Teste 5: ?format=csv → header Content-Type: text/csv."""
    mocker.patch("apps.export.views.SherlockService.search", return_value=_FAKE_RESULTS)
    response = client.get(reverse("export:export"), {"username": "john_doe", "format": "csv"})
    assert response.status_code == 200
    assert "text/csv" in response["Content-Type"]


def test_export_view_json_returns_application_json(client, mocker):
    """Teste 6: ?format=json → header Content-Type: application/json."""
    mocker.patch("apps.export.views.SherlockService.search", return_value=_FAKE_RESULTS)
    response = client.get(reverse("export:export"), {"username": "john_doe", "format": "json"})
    assert response.status_code == 200
    assert "application/json" in response["Content-Type"]


def test_export_view_unknown_format_returns_400(client):
    """Teste 7: ?format=xml → 400."""
    response = client.get(reverse("export:export"), {"username": "john_doe", "format": "xml"})
    assert response.status_code == 400


def test_export_view_missing_username_returns_400(client):
    """Teste 8: Sem username → 400."""
    response = client.get(reverse("export:export"), {"format": "csv"})
    assert response.status_code == 400
