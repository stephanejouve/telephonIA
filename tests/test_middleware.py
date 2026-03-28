"""Tests pour le middleware de logging HTTP."""

import logging

import pytest
from fastapi.testclient import TestClient

from telephonia.web.app import create_app


@pytest.fixture
def client():
    """Client de test FastAPI."""
    app = create_app()
    return TestClient(app)


class TestLoggingMiddleware:
    """Tests pour LoggingMiddleware."""

    def test_logs_get_request(self, client, caplog):
        """GET /api/messages → log INFO avec method + path."""
        with caplog.at_level(logging.INFO, logger="telephonia.web.middleware"):
            client.get("/api/messages")
        assert any("GET" in r.message and "/api/messages" in r.message for r in caplog.records)

    def test_logs_404_as_warning(self, client, caplog):
        """404 → WARNING."""
        with caplog.at_level(logging.WARNING, logger="telephonia.web.middleware"):
            client.get("/api/audio/inexistant")
        warning_records = [
            r for r in caplog.records if r.levelno == logging.WARNING and "404" in r.message
        ]
        assert len(warning_records) >= 1

    def test_health_not_logged(self, client, caplog):
        """GET /api/health → aucun log middleware."""
        with caplog.at_level(logging.DEBUG, logger="telephonia.web.middleware"):
            client.get("/api/health")
        middleware_records = [r for r in caplog.records if r.name == "telephonia.web.middleware"]
        assert len(middleware_records) == 0

    def test_log_contains_duration(self, client, caplog):
        """Le log contient 'ms'."""
        with caplog.at_level(logging.INFO, logger="telephonia.web.middleware"):
            client.get("/api/messages")
        assert any("ms" in r.message for r in caplog.records)

    def test_log_contains_status_code(self, client, caplog):
        """Le log contient le code HTTP."""
        with caplog.at_level(logging.INFO, logger="telephonia.web.middleware"):
            client.get("/api/messages")
        assert any("200" in r.message for r in caplog.records)
