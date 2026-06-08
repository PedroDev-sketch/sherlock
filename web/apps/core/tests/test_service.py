"""
Testes — Dupla 1 (SherlockService).

Técnica: TDD (ciclo Red → Green → Refactor).

Testes deste arquivo:
  #1  test_search_returns_results_for_known_user        — GREEN (Dia 2)
  #1b test_search_result_has_correct_url                — GREEN (Dia 2)
  #2  test_search_rejects_empty_username                — GREEN (Dia 2)
  #2b test_search_rejects_empty_username_without_...    — GREEN (Dia 2)
  #3  test_search_rejects_username_with_invalid_chars   — GREEN (Dia 3)
  #5  test_search_filters_by_sites                      — GREEN (Dia 3)
  #6  test_site_result_mapping_status_found             — GREEN (Dia 2)
  #7  test_site_result_mapping_status_not_found         — GREEN (Dia 2)
"""


from unittest.mock import patch

import pytest
import requests
import responses as responses_lib
from sherlock_project.result import QueryResult, QueryStatus

from apps.core.dtos import SearchRequest, SiteResult
from apps.core.exceptions import InvalidUsernameError, ServiceTimeoutError
from apps.core.services import SherlockService


def _make_query_result(username: str, site: str, url: str, status: QueryStatus) -> dict:
    """Monta a estrutura de retorno que sherlock() produz para um único site."""
    return {
        "url_main": f"https://{site.lower()}.com",
        "url_user": url,
        "status": QueryResult(
            username=username,
            site_name=site,
            site_url_user=url,
            status=status,
            query_time=0.5,
        ),
    }


@pytest.fixture
def service():
    return SherlockService()


@pytest.fixture
def two_found_results():
    """Resposta mockada de sherlock() com 2 sites encontrados."""
    return {
        "GitHub": _make_query_result(
            "torvalds", "GitHub", "https://github.com/torvalds", QueryStatus.CLAIMED
        ),
        "Twitter": _make_query_result(
            "torvalds", "Twitter", "https://twitter.com/torvalds", QueryStatus.CLAIMED
        ),
    }


# ---------------------------------------------------------------------------
# Teste #1 — serviço entrega SiteResult para cada hit retornado pelo mock
# ---------------------------------------------------------------------------

class TestSearchReturnsResults:

    def test_search_returns_results_for_known_user(self, service, two_found_results):
        """
        Dado: mock de sherlock() devolvendo 2 sites com status CLAIMED.
        Quando: SherlockService.search() é chamado com username válido.
        Então: retorna 2 SiteResult com status "found" e URLs corretas.

        """
        req = SearchRequest(username="torvalds")

        with patch("apps.core.services.sherlock", return_value=two_found_results):
            with patch("apps.core.services.SitesInformation"):
                results = list(service.search(req))

        assert len(results) == 2
        assert all(isinstance(r, SiteResult) for r in results)
        assert all(r.status == "found" for r in results)

        site_names = {r.site_name for r in results}
        assert site_names == {"GitHub", "Twitter"}

    def test_search_result_has_correct_url(self, service, two_found_results):
        """
        Complementar ao #1: cada SiteResult deve carregar a URL do perfil.

        """
        req = SearchRequest(username="torvalds")

        with patch("apps.core.services.sherlock", return_value=two_found_results):
            with patch("apps.core.services.SitesInformation"):
                results = list(service.search(req))

        urls = {r.url for r in results}
        assert "https://github.com/torvalds" in urls
        assert "https://twitter.com/torvalds" in urls


# ---------------------------------------------------------------------------
# Teste #2 — username vazio levanta InvalidUsernameError
# ---------------------------------------------------------------------------

class TestSearchValidatesUsername:

    def test_search_rejects_username_with_invalid_chars(self, service):
        """
        Dado: SearchRequest com username contendo caracteres inválidos (espaço, barra).
        Quando: SherlockService.search() é chamado.
        Então: levanta InvalidUsernameError sem realizar chamada de rede.
        """
        for bad in ("jo hn", "user/name", "a@b", "foo bar"):
            req = SearchRequest(username=bad)
            with patch("apps.core.services.sherlock") as mock_sherlock:
                with pytest.raises(InvalidUsernameError):
                    list(service.search(req))
                mock_sherlock.assert_not_called()

    def test_search_rejects_empty_username(self, service):
        """
        Dado: SearchRequest com username vazio.
        Quando: SherlockService.search() é chamado.
        Então: levanta InvalidUsernameError antes de qualquer chamada de rede.
        """
        req = SearchRequest(username="")

        with pytest.raises(InvalidUsernameError):
            list(service.search(req))

    def test_search_rejects_empty_username_without_network_call(self, service):
        """
        Complementar ao #2: a validação deve ocorrer ANTES de chamar sherlock(),
        portanto nenhuma chamada de rede deve ser feita.
        """
        req = SearchRequest(username="")

        with patch("apps.core.services.sherlock") as mock_sherlock:
            with pytest.raises(InvalidUsernameError):
                list(service.search(req))

            mock_sherlock.assert_not_called()


# ---------------------------------------------------------------------------
# Teste #6 — QueryStatus.CLAIMED mapeia para "found"
# ---------------------------------------------------------------------------

class TestSiteResultStatusMapping:

    def test_site_result_mapping_status_found(self, service):
        """
        Dado: mock de sherlock() devolvendo 1 site com status CLAIMED.
        Quando: SherlockService.search() é chamado.
        Então: o SiteResult resultante tem status "found".
        """
        mock_results = {
            "GitHub": _make_query_result(
                "torvalds", "GitHub", "https://github.com/torvalds", QueryStatus.CLAIMED
            ),
        }
        req = SearchRequest(username="torvalds")

        with patch("apps.core.services.sherlock", return_value=mock_results):
            with patch("apps.core.services.SitesInformation"):
                results = list(service.search(req))

        assert len(results) == 1
        assert results[0].status == "found"

    # -----------------------------------------------------------------------
    # Teste #7 — QueryStatus.AVAILABLE mapeia para "not_found"
    # -----------------------------------------------------------------------

    def test_site_result_mapping_status_not_found(self, service):
        """
        Dado: mock de sherlock() devolvendo 1 site com status AVAILABLE.
        Quando: SherlockService.search() é chamado.
        Então: o SiteResult resultante tem status "not_found".
        """
        mock_results = {
            "GitHub": _make_query_result(
                "nonexistent_user_xyz", "GitHub",
                "https://github.com/nonexistent_user_xyz", QueryStatus.AVAILABLE
            ),
        }
        req = SearchRequest(username="nonexistent_user_xyz")

        with patch("apps.core.services.sherlock", return_value=mock_results):
            with patch("apps.core.services.SitesInformation"):
                results = list(service.search(req))

        assert len(results) == 1
        assert results[0].status == "not_found"


# ---------------------------------------------------------------------------
# Teste #5 — req.sites filtra quais sites são consultados
# ---------------------------------------------------------------------------

class TestSearchFiltersBySites:

    def test_search_filters_by_sites(self, service):
        """
        Dado: SitesInformation retorna GitHub, Reddit e Twitter no mock.
        Quando: SearchRequest(username="x", sites=["GitHub"]) é passado.
        Então: sherlock() recebe site_data contendo APENAS a chave "GitHub".
        """
        github_site = _make_query_result(
            "x", "GitHub", "https://github.com/x", QueryStatus.CLAIMED
        )

        mock_site = type("MockSite", (), {})()
        mock_site.name = "GitHub"
        mock_site.information = {"urlMain": "https://github.com"}

        mock_site_reddit = type("MockSite", (), {})()
        mock_site_reddit.name = "Reddit"
        mock_site_reddit.information = {"urlMain": "https://reddit.com"}

        mock_site_twitter = type("MockSite", (), {})()
        mock_site_twitter.name = "Twitter"
        mock_site_twitter.information = {"urlMain": "https://twitter.com"}

        req = SearchRequest(username="x", sites=["GitHub"])

        with patch("apps.core.services.SitesInformation") as mock_sites_cls:
            mock_sites_cls.return_value = [
                mock_site, mock_site_reddit, mock_site_twitter
            ]
            with patch(
                "apps.core.services.sherlock",
                return_value={"GitHub": github_site},
            ) as mock_sherlock:
                list(service.search(req))

        args = mock_sherlock.call_args
        called_site_data = args.kwargs.get(
            "site_data", args[0][1] if args[0] else {}
        )
        assert set(called_site_data.keys()) == {"GitHub"}


# ---------------------------------------------------------------------------
# Teste #4 — timeout do upstream é propagado como ServiceTimeoutError
# ---------------------------------------------------------------------------

class TestSearchPropagatesTimeout:

    def test_search_propagates_timeout(self, service):
        """
        Dado: sherlock() levanta requests.exceptions.Timeout.
        Quando: SherlockService.search() é chamado.
        Então: levanta ServiceTimeoutError (sem vazar o requests.Timeout cru).
        """
        req = SearchRequest(username="torvalds")

        with patch("apps.core.services.SitesInformation"):
            with patch(
                "apps.core.services.sherlock",
                side_effect=requests.exceptions.Timeout("upstream timed out"),
            ):
                with pytest.raises(ServiceTimeoutError):
                    list(service.search(req))


# ---------------------------------------------------------------------------
# Teste #8 — sem mock o serviço tenta rede real (protege a suíte de flakes)
# ---------------------------------------------------------------------------

class TestServiceDoesNotPerformRealNetwork:

    @responses_lib.activate
    def test_service_does_not_perform_real_network_in_tests(self, service):
        """
        Confirma que SherlockService faz chamadas HTTP quando não há mock.
        responses.activate bloqueia toda rede real — qualquer tentativa levanta
        ConnectionError, provando que os outros testes DEVEM mockar SitesInformation
        e sherlock() para não depender de rede.
        """
        req = SearchRequest(username="torvalds")

        with pytest.raises(Exception):
            list(service.search(req))
