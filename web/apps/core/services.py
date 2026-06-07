"""
Service layer que encapsula a chamada ao sherlock_project.

Dia 2 — Dupla 1: implementação mínima GREEN.
O método search() delega ao sherlock() da CLI e converte os resultados
em SiteResult DTOs com mapeamento de status (Anexo A do PLANO_TDD.md).
"""

import logging
import re
from typing import Iterator

import requests
from sherlock_project.result import QueryStatus
from sherlock_project.notify import QueryNotify
from sherlock_project.sites import SitesInformation
from sherlock_project.sherlock import sherlock

from .dtos import SearchRequest, SiteResult
from .exceptions import InvalidUsernameError, ServiceTimeoutError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Mapeamento QueryStatus → status do DTO (Anexo A)
# ---------------------------------------------------------------------------
_STATUS_MAP: dict[QueryStatus, str] = {
    QueryStatus.CLAIMED: "found",
    QueryStatus.AVAILABLE: "not_found",
    QueryStatus.UNKNOWN: "error",
    QueryStatus.WAF: "error",
    QueryStatus.ILLEGAL: "error",
}


def _map_status(query_status: QueryStatus) -> str:
    """Converte um QueryStatus da CLI para o literal de status do DTO."""
    return _STATUS_MAP.get(query_status, "error")


class _SilentNotify(QueryNotify):
    """QueryNotify que não produz saída — usado no contexto web."""

    def start(self, message: str = "") -> None:
        pass

    def update(self, result: object = None) -> None:
        pass

    def finish(self, message: str = "") -> None:
        pass


class SherlockService:
    """Fachada para buscar usernames via sherlock_project."""

    def search(self, req: SearchRequest) -> Iterator[SiteResult]:
        """Executa a busca e devolve SiteResults.

        Raises:
            InvalidUsernameError: se o username for vazio.
        """
        # --- Validação de entrada ---
        if not req.username or not req.username.strip():
            raise InvalidUsernameError("Username não pode ser vazio.")
        if not re.match(r'^[a-zA-Z0-9_.-]+$', req.username):
            raise InvalidUsernameError(f"Username contém caracteres inválidos: {req.username!r}")

        # --- Carrega dados de sites ---
        sites_info = SitesInformation(data_file_path=None)
        site_data = {site.name: site.information for site in sites_info}
        if req.sites:
            site_data = {name: info for name, info in site_data.items() if name in req.sites}

        # --- Dispara a busca via sherlock() ---
        try:
            results = sherlock(
                username=req.username,
                site_data=site_data,
                query_notify=_SilentNotify(),
                timeout=int(req.timeout),
            )
        except requests.exceptions.Timeout as exc:
            raise ServiceTimeoutError("Busca expirou.") from exc

        # --- Converte resultados para DTOs ---
        for site_name, site_info in results.items():
            query_result = site_info.get("status")
            if query_result is None:
                continue

            status = _map_status(query_result.status)
            url = site_info.get("url_user", "")
            response_time_ms = None
            if query_result.query_time is not None:
                response_time_ms = int(query_result.query_time * 1000)

            yield SiteResult(
                site_name=site_name,
                url=url,
                status=status,
                response_time_ms=response_time_ms,
            )
