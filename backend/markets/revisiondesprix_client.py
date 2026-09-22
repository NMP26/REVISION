"""Read-only client for the public revisiondesprix.ma index API.

This module deliberately has no Django or ORM dependency.  It only performs
transport, response validation and normalization.  Staging, validation and
runtime index storage belong to later layers.
"""

from __future__ import annotations

import json
import logging
import socket
import time
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Callable, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


logger = logging.getLogger(__name__)


class RevisionDesPrixApiError(Exception):
    """Structured, safe-to-log error raised by the external client."""

    def __init__(
        self,
        kind: str,
        message: str,
        *,
        endpoint: str,
        status_code: int | None = None,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        self.kind = kind
        self.endpoint = endpoint
        self.status_code = status_code
        self.details = dict(details or {})
        super().__init__(message)


@dataclass(frozen=True)
class TransportResponse:
    status_code: int
    body: bytes
    content_type: str = ""


@dataclass(frozen=True)
class ExternalIndexName:
    code: str


@dataclass(frozen=True)
class ExternalIndexValue:
    external_id: int
    date: date
    index_name: str
    value: Decimal
    month: int
    year: int
    revision_num: int
    is_definitive: bool
    created_at: datetime | None


@dataclass(frozen=True)
class ExternalIndexEvolutionPoint:
    date: date
    value: Decimal
    label: str


Transport = Callable[[str, float], TransportResponse]
Sleep = Callable[[float], None]


def _default_transport(url: str, timeout: float) -> TransportResponse:
    request = Request(url, headers={"Accept": "application/json"}, method="GET")
    with urlopen(request, timeout=timeout) as response:  # noqa: S310 - fixed HTTPS base URL
        return TransportResponse(
            status_code=response.status,
            body=response.read(),
            content_type=response.headers.get("Content-Type", ""),
        )


class RevisionDesPrixApiClient:
    """Read-only client for the three publicly observed index endpoints."""

    DEFAULT_BASE_URL = "https://revisiondesprix.ma/api"

    def __init__(
        self,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 10.0,
        max_retries: int = 2,
        transport: Transport | None = None,
        sleep: Sleep = time.sleep,
    ) -> None:
        if timeout <= 0:
            raise ValueError("timeout doit être strictement positif")
        if max_retries < 0:
            raise ValueError("max_retries ne peut pas être négatif")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self._transport = transport or _default_transport
        self._sleep = sleep

    def get_index_names(self) -> list[ExternalIndexName]:
        endpoint = "/indices/names"
        payload = self._get_json(endpoint)
        if not isinstance(payload, list):
            raise self._schema_error(endpoint, "la réponse doit être une liste")
        names = []
        for position, item in enumerate(payload):
            if not isinstance(item, str) or not item.strip():
                raise self._schema_error(endpoint, f"code invalide à la position {position}")
            names.append(ExternalIndexName(code=item.strip()))
        return names

    def get_indices_for_year(self, year: int) -> list[ExternalIndexValue]:
        if not isinstance(year, int) or isinstance(year, bool) or not 1 <= year <= 9999:
            raise ValueError("year doit être un entier compris entre 1 et 9999")
        endpoint = f"/indices?year={year}"
        payload = self._get_json(endpoint)
        if not isinstance(payload, list):
            raise self._schema_error(endpoint, "la réponse doit être une liste")
        return [self._normalize_year_item(item, endpoint, position) for position, item in enumerate(payload)]

    def get_index_evolution(self, code: str) -> list[ExternalIndexEvolutionPoint]:
        if not isinstance(code, str) or not code.strip():
            raise ValueError("code doit être une chaîne non vide")
        endpoint = f"/indices/{quote(code.strip(), safe='')}/evolution"
        payload = self._get_json(endpoint)
        if not isinstance(payload, list):
            raise self._schema_error(endpoint, "la réponse doit être une liste")
        return [self._normalize_evolution_item(item, endpoint, position) for position, item in enumerate(payload)]

    def _get_json(self, endpoint: str) -> Any:
        url = f"{self.base_url}{endpoint}"
        response = self._request(url, endpoint)
        if response.content_type and "json" not in response.content_type.lower():
            raise RevisionDesPrixApiError(
                "INVALID_CONTENT_TYPE",
                "La réponse externe n'est pas annoncée comme JSON.",
                endpoint=endpoint,
                status_code=response.status_code,
                details={"content_type": response.content_type},
            )
        try:
            return json.loads(response.body.decode("utf-8"), parse_float=Decimal, parse_int=int)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RevisionDesPrixApiError(
                "INVALID_JSON",
                "La réponse externe ne contient pas un JSON valide.",
                endpoint=endpoint,
                status_code=response.status_code,
            ) from exc

    def _request(self, url: str, endpoint: str) -> TransportResponse:
        attempts = self.max_retries + 1
        for attempt in range(attempts):
            try:
                response = self._transport(url, self.timeout)
            except (TimeoutError, socket.timeout) as exc:
                if attempt + 1 < attempts:
                    self._wait(attempt, endpoint, "timeout")
                    continue
                raise RevisionDesPrixApiError("TIMEOUT", "Délai dépassé lors de l'appel externe.", endpoint=endpoint) from exc
            except HTTPError as exc:
                response = TransportResponse(exc.code, exc.read(), exc.headers.get("Content-Type", ""))
            except (URLError, OSError) as exc:
                if attempt + 1 < attempts:
                    self._wait(attempt, endpoint, "network")
                    continue
                raise RevisionDesPrixApiError("NETWORK_ERROR", "API externe indisponible.", endpoint=endpoint) from exc

            if 200 <= response.status_code < 300:
                return response
            if response.status_code in {408, 429} or response.status_code >= 500:
                if attempt + 1 < attempts:
                    self._wait(attempt, endpoint, f"http_{response.status_code}")
                    continue
            raise RevisionDesPrixApiError(
                "HTTP_ERROR",
                "L'API externe a retourné une réponse HTTP non valide.",
                endpoint=endpoint,
                status_code=response.status_code,
                details={"content_type": response.content_type},
            )
        raise AssertionError("boucle de transport inatteignable")

    def _wait(self, attempt: int, endpoint: str, reason: str) -> None:
        delay = min(2**attempt, 8)
        logger.warning("Retry API revisiondesprix: endpoint=%s reason=%s attempt=%s", endpoint, reason, attempt + 1)
        self._sleep(delay)

    @staticmethod
    def _schema_error(endpoint: str, message: str) -> RevisionDesPrixApiError:
        return RevisionDesPrixApiError("SCHEMA_ERROR", message, endpoint=endpoint)

    @classmethod
    def _normalize_year_item(cls, item: Any, endpoint: str, position: int) -> ExternalIndexValue:
        if not isinstance(item, dict):
            raise cls._schema_error(endpoint, f"objet attendu à la position {position}")
        required = {"id", "date", "indexName", "value", "month", "year", "revisionNum", "isDefinitif", "createdAt"}
        missing = sorted(required - item.keys())
        if missing:
            raise RevisionDesPrixApiError("MISSING_DATA", "Champ(s) obligatoire(s) absent(s).", endpoint=endpoint, details={"fields": missing, "position": position})
        if item["value"] is None:
            raise RevisionDesPrixApiError("MISSING_DATA", "Une valeur d'index est NULL.", endpoint=endpoint, details={"position": position})
        value = cls._decimal(item["value"], endpoint, position)
        try:
            external_id = cls._int(item["id"], "id", endpoint, position)
            month = cls._int(item["month"], "month", endpoint, position)
            item_year = cls._int(item["year"], "year", endpoint, position)
            revision_num = cls._int(item["revisionNum"], "revisionNum", endpoint, position)
            item_date = date.fromisoformat(item["date"])
        except (TypeError, ValueError) as exc:
            raise cls._schema_error(endpoint, f"valeur structurée invalide à la position {position}") from exc
        if not 1 <= month <= 12:
            raise cls._schema_error(endpoint, f"mois hors intervalle à la position {position}")
        if item_year != int(item.get("year")) or item_date.year != item_year or item_date.month != month:
            raise cls._schema_error(endpoint, f"période incohérente à la position {position}")
        if not isinstance(item["indexName"], str) or not item["indexName"].strip():
            raise cls._schema_error(endpoint, f"indexName invalide à la position {position}")
        if not isinstance(item["isDefinitif"], bool):
            raise cls._schema_error(endpoint, f"isDefinitif invalide à la position {position}")
        created_at = cls._datetime(item["createdAt"], endpoint, position)
        return ExternalIndexValue(external_id, item_date, item["indexName"].strip(), value, month, item_year, revision_num, item["isDefinitif"], created_at)

    @classmethod
    def _normalize_evolution_item(cls, item: Any, endpoint: str, position: int) -> ExternalIndexEvolutionPoint:
        if not isinstance(item, dict):
            raise cls._schema_error(endpoint, f"objet attendu à la position {position}")
        required = {"date", "value", "label"}
        missing = sorted(required - item.keys())
        if missing:
            raise RevisionDesPrixApiError("MISSING_DATA", "Champ(s) obligatoire(s) absent(s).", endpoint=endpoint, details={"fields": missing, "position": position})
        if item["value"] is None:
            raise RevisionDesPrixApiError("MISSING_DATA", "Une valeur d'évolution est NULL.", endpoint=endpoint, details={"position": position})
        try:
            point_date = date.fromisoformat(item["date"])
        except (TypeError, ValueError) as exc:
            raise cls._schema_error(endpoint, f"date invalide à la position {position}") from exc
        if not isinstance(item["label"], str):
            raise cls._schema_error(endpoint, f"label invalide à la position {position}")
        return ExternalIndexEvolutionPoint(point_date, cls._decimal(item["value"], endpoint, position), item["label"])

    @staticmethod
    def _decimal(value: Any, endpoint: str, position: int) -> Decimal:
        if isinstance(value, bool) or not isinstance(value, (Decimal, int, str)):
            raise RevisionDesPrixApiError("INVALID_VALUE", "Valeur d'index non numérique.", endpoint=endpoint, details={"position": position})
        try:
            decimal_value = value if isinstance(value, Decimal) else Decimal(str(value))
        except (InvalidOperation, ValueError) as exc:
            raise RevisionDesPrixApiError("INVALID_VALUE", "Valeur d'index non numérique.", endpoint=endpoint, details={"position": position}) from exc
        if not decimal_value.is_finite():
            raise RevisionDesPrixApiError("INVALID_VALUE", "Valeur d'index non finie.", endpoint=endpoint, details={"position": position})
        return decimal_value

    @staticmethod
    def _int(value: Any, field: str, endpoint: str, position: int) -> int:
        if isinstance(value, bool) or not isinstance(value, int):
            raise RevisionDesPrixApiError("SCHEMA_ERROR", f"{field} invalide.", endpoint=endpoint, details={"position": position})
        return value

    @staticmethod
    def _datetime(value: Any, endpoint: str, position: int) -> datetime | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise RevisionDesPrixApiError("SCHEMA_ERROR", "createdAt invalide.", endpoint=endpoint, details={"position": position})
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise RevisionDesPrixApiError("SCHEMA_ERROR", "createdAt invalide.", endpoint=endpoint, details={"position": position}) from exc
