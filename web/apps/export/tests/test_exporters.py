import json

from apps.core.dtos import SiteResult
from apps.export.exporters import to_csv, to_json


def _make_results():
    return [
        SiteResult(site_name="GitHub", url="https://github.com/john_doe", status="found"),
        SiteResult(site_name="Reddit", url="https://reddit.com/user/john_doe", status="not_found"),
        SiteResult(site_name="Twitter", url="https://twitter.com/john_doe", status="found"),
    ]


def test_to_csv_has_expected_headers():
    """Teste 1: to_csv começa com site_name,url,status."""
    output = to_csv([])
    assert output.startswith("site_name,url,status")


def test_to_csv_writes_one_row_per_result():
    """Teste 2: Lista com 3 resultados → 4 linhas (header + 3)."""
    output = to_csv(_make_results())
    lines = [l for l in output.split("\n") if l]
    assert len(lines) == 4


def test_to_csv_escapes_commas_in_fields():
    """Teste 3: Campo com vírgula é envolvido em aspas."""
    results = [
        SiteResult(site_name="Site, Name", url="https://example.com", status="found"),
    ]
    output = to_csv(results)
    assert '"Site, Name"' in output


def test_to_json_is_valid_and_has_expected_shape():
    """Teste 4: json.loads(to_json(...)) tem chaves username e hits."""
    data = json.loads(to_json(_make_results(), username="john_doe"))
    assert data["username"] == "john_doe"
    assert "hits" in data
    assert len(data["hits"]) == 3
    first = data["hits"][0]
    assert set(first.keys()) == {"site_name", "url", "status"}
