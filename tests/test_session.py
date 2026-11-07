"""Tests du code de session et de la reserve du technicien (#38)."""

import re
import signal
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from telephonia.web import app as web_app
from telephonia.web.app import create_app
from telephonia.web.session import (
    ATTEMPT_WINDOW_SECONDS,
    COOKIE_NAME,
    MAX_CODE_ATTEMPTS,
    SessionGate,
    is_technician_route,
    new_code,
)

CODE = "ABCD-EFGH"
LAN_URL = "http://192.168.1.50:8000"
LAN_CLIENT = ("192.168.1.20", 50000)

TECHNICIAN_CALLS = [
    ("post", "/api/shutdown", {}),
    ("put", "/api/voice", {"json": {"voice_id": "x"}}),
    ("put", "/api/prefix", {"json": {"prefix": "x"}}),
    ("delete", "/api/music", {}),
    ("delete", "/api/audio/attente", {}),
]


def _lan(app, address=LAN_CLIENT):
    return TestClient(app, base_url=LAN_URL, client=address, follow_redirects=False)


def _local(app, host="127.0.0.1"):
    return TestClient(app, base_url=f"http://{host}", client=("127.0.0.1", 50000))


@pytest.fixture
def app():
    return create_app(SessionGate(CODE))


@pytest.fixture
def paired(app):
    """Machine du reseau du client, appairee avec le code."""
    lan = _lan(app)
    assert lan.get(f"/?code={CODE}").status_code == 303
    return lan


class TestCode:
    def test_format(self):
        assert re.fullmatch(r"[A-Z2-9]{4}-[A-Z2-9]{4}", new_code())

    def test_new_code_at_each_launch(self):
        assert create_app().state.session.code != create_app().state.session.code

    def test_main_shows_the_code_in_the_lan_url(self, capsys):
        with (
            patch.object(web_app, "uvicorn") as uvicorn,
            patch.object(web_app, "_configure_ffmpeg"),
            patch.object(web_app, "find_free_port", return_value=8123),
            patch.object(web_app, "get_lan_ip", return_value="192.168.1.50"),
            patch.dict("os.environ", {"TELEPHONIA_APP_MODE": "1"}),
        ):
            web_app.main()
        code = uvicorn.run.call_args[0][0].state.session.code
        out = capsys.readouterr().out
        assert f"http://192.168.1.50:8123/?code={code}" in out
        assert "PORT:8123" in out


class TestLanWithoutCode:
    @pytest.mark.parametrize("path", ["/api/messages", "/api/voices", "/api/audio/accueil", "/"])
    def test_401(self, app, path):
        assert _lan(app).get(path).status_code == 401

    def test_health_stays_open(self, app):
        assert _lan(app).get("/api/health").status_code == 200

    def test_wrong_code_401(self, app):
        assert _lan(app).get("/?code=ZZZZ-ZZZZ").status_code == 401

    def test_forged_cookie_401(self, app):
        lan = _lan(app)
        lan.cookies.set(COOKIE_NAME, "forge")
        assert lan.get("/api/messages").status_code == 401

    def test_code_as_cookie_401(self, app):
        """Le cookie porte un jeton distinct du code affiche."""
        lan = _lan(app)
        lan.cookies.set(COOKIE_NAME, CODE)
        assert lan.get("/api/messages").status_code == 401

    def test_cookie_of_a_previous_launch_401(self, paired):
        token = paired.cookies[COOKIE_NAME]
        lan = _lan(create_app(SessionGate(CODE)))
        lan.cookies.set(COOKIE_NAME, token)
        assert lan.get("/api/messages").status_code == 401


class TestLanWithCode:
    def test_cookie_is_set_then_access_is_granted(self, app):
        lan = _lan(app)
        response = lan.get(f"/?code={CODE}")
        assert response.status_code == 303
        cookie = response.headers["set-cookie"]
        assert cookie.startswith(f"{COOKIE_NAME}=")
        assert "HttpOnly" in cookie
        assert "SameSite=strict" in cookie
        assert CODE not in cookie
        assert lan.get("/api/messages").status_code == 200

    def test_code_leaves_the_url(self, app):
        response = _lan(app).get(f"/api/messages?code={CODE}&v=2")
        assert response.headers["location"] == "/api/messages?v=2"

    def test_client_can_read_and_edit_messages(self, paired):
        assert paired.get("/api/messages").status_code == 200
        assert paired.put("/api/messages/attente", json={"text": "Bonjour"}).status_code == 200

    @pytest.mark.parametrize("method,path,kwargs", TECHNICIAN_CALLS)
    def test_technician_routes_403(self, paired, method, path, kwargs):
        with patch("telephonia.web.api.os.kill") as kill:
            response = getattr(paired, method)(path, **kwargs)
        assert response.status_code == 403
        kill.assert_not_called()


class TestBruteForce:
    def test_blocked_after_max_attempts_even_with_the_right_code(self, app):
        lan = _lan(app)
        for _ in range(MAX_CODE_ATTEMPTS):
            assert lan.get("/?code=ZZZZ-ZZZZ").status_code == 401
        assert lan.get(f"/?code={CODE}").status_code == 429

    def test_other_addresses_are_not_blocked(self, app):
        lan = _lan(app)
        for _ in range(MAX_CODE_ATTEMPTS):
            lan.get("/?code=ZZZZ-ZZZZ")
        assert _lan(app, ("192.168.1.21", 50000)).get(f"/?code={CODE}").status_code == 303

    def test_unblocked_after_the_window(self):
        gate = SessionGate(CODE)
        for _ in range(MAX_CODE_ATTEMPTS):
            gate.check_code("10.0.0.1", "ZZZZ-ZZZZ", now=0.0)
        assert gate.is_blocked("10.0.0.1", now=ATTEMPT_WINDOW_SECONDS - 1)
        assert not gate.is_blocked("10.0.0.1", now=ATTEMPT_WINDOW_SECONDS)

    def test_code_compared_in_constant_time(self):
        gate = SessionGate(CODE)
        with patch("telephonia.web.session.secrets.compare_digest", return_value=False) as cmp:
            assert not gate.check_code("10.0.0.1", CODE)
        cmp.assert_called_once()


class TestTechnicianPost:
    def test_full_access_without_code(self, app):
        local = _local(app)
        assert local.get("/api/messages").status_code == 200
        with patch("telephonia.web.api.os.kill") as kill:
            assert local.post("/api/shutdown").status_code == 200
        assert kill.call_args[0][1] == signal.SIGINT

    def test_localhost_host_header(self, app):
        assert _local(app, host="localhost:8000").get("/api/messages").status_code == 200

    def test_foreign_host_header_needs_the_code(self, app):
        """DNS rebinding : une page tierce resolue en 127.0.0.1 n'a pas l'acces local."""
        assert _local(app, host="evil.example").get("/api/messages").status_code == 401

    def test_foreign_origin_refused(self, app):
        with patch("telephonia.web.api.os.kill") as kill:
            response = _local(app).post("/api/shutdown", headers={"Origin": "http://evil.example"})
        assert response.status_code == 403
        kill.assert_not_called()

    def test_same_origin_accepted(self, app):
        with patch("telephonia.web.api.os.kill"):
            response = _local(app).post("/api/shutdown", headers={"Origin": "http://127.0.0.1"})
        assert response.status_code == 200


@pytest.mark.parametrize(
    "method,path,expected",
    [
        ("POST", "/api/shutdown", True),
        ("DELETE", "/api/audio/accueil", True),
        ("GET", "/api/audio/accueil", False),
        ("POST", "/api/audio/accueil/upload", False),
        ("POST", "/api/music", False),
        ("PUT", "/api/messages/accueil", False),
        ("POST", "/api/generate", False),
    ],
)
def test_is_technician_route(method, path, expected):
    assert is_technician_route(method, path) is expected
