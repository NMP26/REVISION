import json
import socket
import unittest
from datetime import date
from decimal import Decimal

from .revisiondesprix_client import (
    RevisionDesPrixApiClient,
    RevisionDesPrixApiError,
    TransportResponse,
)


class FakeTransport:
    def __init__(self, *outcomes):
        self.outcomes = list(outcomes)
        self.calls = []

    def __call__(self, url, timeout):
        self.calls.append((url, timeout))
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


def response(payload, status_code=200, content_type="application/json; charset=utf-8"):
    return TransportResponse(status_code, json.dumps(payload).encode(), content_type)


class RevisionDesPrixApiClientTests(unittest.TestCase):
    def client(self, transport, **kwargs):
        return RevisionDesPrixApiClient(transport=transport, sleep=lambda _: None, **kwargs)

    def test_names_are_normalized_from_observed_string_array(self):
        client = self.client(FakeTransport(response([" BAT3 ", "BAT6"])))
        self.assertEqual([item.code for item in client.get_index_names()], ["BAT3", "BAT6"])

    def test_year_values_use_decimal_and_observed_fields(self):
        payload = [{
            "id": 47135, "date": "2025-11-01", "indexName": "BAT3", "value": 337.8,
            "month": 11, "year": 2025, "revisionNum": 3, "isDefinitif": True,
            "createdAt": "2026-05-06T00:00:00.000Z",
        }]
        value = self.client(FakeTransport(response(payload))).get_indices_for_year(2025)[0]
        self.assertIs(type(value.value), Decimal)
        self.assertEqual(value.value, Decimal("337.8"))
        self.assertEqual(value.date, date(2025, 11, 1))

    def test_evolution_values_use_decimal(self):
        payload = [{"date": "2026-04-01", "value": 348.7, "label": "04/2026"}]
        point = self.client(FakeTransport(response(payload))).get_index_evolution("BAT3")[0]
        self.assertEqual(point.value, Decimal("348.7"))

    def test_empty_evolution_is_valid(self):
        self.assertEqual(self.client(FakeTransport(response([]))).get_index_evolution("UNKNOWN"), [])

    def test_timeout_is_retried_then_structured(self):
        transport = FakeTransport(socket.timeout(), socket.timeout(), socket.timeout())
        with self.assertRaisesRegex(RevisionDesPrixApiError, "Délai dépassé") as context:
            self.client(transport, max_retries=2).get_index_evolution("BAT3")
        self.assertEqual(context.exception.kind, "TIMEOUT")
        self.assertEqual(len(transport.calls), 3)

    def test_transient_http_error_is_retried(self):
        transport = FakeTransport(response({"error": "busy"}, 503), response([]))
        self.assertEqual(self.client(transport).get_index_evolution("BAT3"), [])
        self.assertEqual(len(transport.calls), 2)

    def test_non_transient_http_error_is_not_retried(self):
        transport = FakeTransport(response({"error": "bad request"}, 400), response([]))
        with self.assertRaises(RevisionDesPrixApiError) as context:
            self.client(transport).get_index_evolution("BAT3")
        self.assertEqual(context.exception.kind, "HTTP_ERROR")
        self.assertEqual(len(transport.calls), 1)

    def test_invalid_json_is_structured(self):
        transport = FakeTransport(TransportResponse(200, b"not-json", "application/json"))
        with self.assertRaises(RevisionDesPrixApiError) as context:
            self.client(transport).get_index_names()
        self.assertEqual(context.exception.kind, "INVALID_JSON")

    def test_missing_field_is_rejected(self):
        payload = [{"date": "2026-04-01", "value": 348.7, "label": "04/2026"}]
        with self.assertRaises(RevisionDesPrixApiError) as context:
            self.client(FakeTransport(response(payload))).get_indices_for_year(2026)
        self.assertEqual(context.exception.kind, "MISSING_DATA")

    def test_null_and_non_numeric_values_are_rejected(self):
        base = {"id": 1, "date": "2025-11-01", "indexName": "BAT3", "month": 11, "year": 2025, "revisionNum": 3, "isDefinitif": True, "createdAt": None}
        for value, kind in [(None, "MISSING_DATA"), ("not-a-number", "INVALID_VALUE")]:
            payload = [{**base, "value": value}]
            with self.subTest(value=value), self.assertRaises(RevisionDesPrixApiError) as context:
                self.client(FakeTransport(response(payload))).get_indices_for_year(2025)
            self.assertEqual(context.exception.kind, kind)

    def test_missing_month_and_inconsistent_period_are_rejected(self):
        base = {"id": 1, "date": "2025-11-01", "indexName": "BAT3", "value": 337.8, "year": 2025, "revisionNum": 3, "isDefinitif": True, "createdAt": None}
        with self.assertRaises(RevisionDesPrixApiError) as context:
            self.client(FakeTransport(response([base]))).get_indices_for_year(2025)
        self.assertEqual(context.exception.kind, "MISSING_DATA")
        with self.assertRaises(RevisionDesPrixApiError) as context:
            self.client(FakeTransport(response([{**base, "month": 10}]))).get_indices_for_year(2025)
        self.assertEqual(context.exception.kind, "SCHEMA_ERROR")

    def test_non_json_content_type_is_rejected(self):
        transport = FakeTransport(response([], content_type="text/html"))
        with self.assertRaises(RevisionDesPrixApiError) as context:
            self.client(transport).get_index_names()
        self.assertEqual(context.exception.kind, "INVALID_CONTENT_TYPE")

    def test_unknown_index_is_encoded_and_empty_response_is_returned(self):
        transport = FakeTransport(response([]))
        result = self.client(transport).get_index_evolution("unknown/code")
        self.assertEqual(result, [])
        self.assertIn("unknown%2Fcode", transport.calls[0][0])
