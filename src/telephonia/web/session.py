"""Code de session : l'interface web ouverte au reseau du client (#38).

Le serveur ecoute sur 0.0.0.0 pour que le client recupere ses messages
depuis sa machine. Ce reseau est celui du client, que personne ne maitrise :

- le poste du technicien (adresse de bouclage, en-tete Host local) a tout ;
- une machine du reseau doit presenter le code tire au lancement
  (``?code=XXXX-XXXX``), echange contre un cookie de session ;
- les gestes du technicien (arret, suppressions, voix, prefixe) restent
  reserves a son poste, meme avec le cookie.

Le code et le cookie meurent avec le serveur : rien a stocker ni a revoquer.
"""

import ipaddress
import secrets
import time
from collections import defaultdict, deque
from urllib.parse import urlencode, urlsplit

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, PlainTextResponse, RedirectResponse

COOKIE_NAME = "telephonia_session"

# Sans 0/O ni 1/I/L : le code se recopie a la main depuis l'ecran du technicien
_CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
_CODE_HALF = 4

MAX_CODE_ATTEMPTS = 5
ATTEMPT_WINDOW_SECONDS = 60.0

_OPEN_PATHS = {"/api/health"}
_LOCAL_HOSTNAMES = {"localhost", "127.0.0.1", "::1"}
_SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}

TECHNICIAN_ROUTES = {
    ("POST", "/api/shutdown"),
    ("PUT", "/api/voice"),
    ("PUT", "/api/prefix"),
    ("DELETE", "/api/music"),
}
_TECHNICIAN_DELETE_PREFIX = "/api/audio/"

_UNAUTHENTICATED = "Code de session requis : ouvrez le lien affiche sur le poste du technicien"
_TECHNICIAN_ONLY = "Reserve au poste du technicien"
_FOREIGN_ORIGIN = "Requete d'une autre origine refusee"
_TOO_MANY_ATTEMPTS = "Trop d'essais de code : reessayez dans une minute"


def new_code() -> str:
    """Code aleatoire ``XXXX-XXXX``, nouveau a chaque lancement."""
    chars = [secrets.choice(_CODE_ALPHABET) for _ in range(2 * _CODE_HALF)]
    return "".join(chars[:_CODE_HALF]) + "-" + "".join(chars[_CODE_HALF:])


def is_technician_route(method: str, path: str) -> bool:
    """Arret, suppressions, voix et prefixe : reserves au poste du technicien."""
    if (method, path) in TECHNICIAN_ROUTES:
        return True
    return method == "DELETE" and path.startswith(_TECHNICIAN_DELETE_PREFIX)


def _hostname(host_header: str) -> str:
    """Nom d'hote d'un en-tete Host, sans le port (``[::1]:8000`` → ``::1``)."""
    if host_header.startswith("["):
        return host_header[1 : host_header.find("]")]
    return host_header.split(":", 1)[0]


def _is_loopback(address: str) -> bool:
    try:
        return ipaddress.ip_address(address).is_loopback
    except ValueError:
        return False


class SessionGate:
    """Le code et le jeton de cookie d'un lancement, et les essais par adresse."""

    def __init__(self, code: str | None = None):
        self.code = code or new_code()
        # Le cookie porte un jeton distinct : le code affiche ne sert qu'une fois par appareil
        self.cookie_token = secrets.token_urlsafe(32)
        self._failures: dict[str, deque[float]] = defaultdict(deque)

    def is_blocked(self, address: str, now: float | None = None) -> bool:
        """Vrai apres MAX_CODE_ATTEMPTS codes faux dans la derniere minute."""
        now = time.monotonic() if now is None else now
        failures = self._failures[address]
        while failures and now - failures[0] >= ATTEMPT_WINDOW_SECONDS:
            failures.popleft()
        if not failures:
            del self._failures[address]
            return False
        return len(failures) >= MAX_CODE_ATTEMPTS

    def check_code(self, address: str, code: str, now: float | None = None) -> bool:
        """Compare en temps constant ; un code faux compte un essai pour l'adresse."""
        if secrets.compare_digest(code.encode(), self.code.encode()):
            return True
        self._failures[address].append(time.monotonic() if now is None else now)
        return False

    def check_cookie(self, value: str | None) -> bool:
        return value is not None and secrets.compare_digest(
            value.encode(), self.cookie_token.encode()
        )


def _refuse(path: str, status: int, detail: str):
    if path.startswith("/api/"):
        return JSONResponse({"detail": detail}, status_code=status)
    return PlainTextResponse(detail, status_code=status)


class SessionMiddleware(BaseHTTPMiddleware):
    """Applique le code de session et la reserve du technicien a chaque requete."""

    def __init__(self, app, gate: SessionGate):
        super().__init__(app)
        self.gate = gate

    async def dispatch(self, request, call_next):
        path = request.url.path
        method = request.method
        address = request.client.host if request.client else ""
        host = request.headers.get("host", "")
        # L'en-tete Host local ferme la porte au DNS rebinding depuis le navigateur du technicien
        local = _is_loopback(address) and _hostname(host) in _LOCAL_HOSTNAMES

        if local:
            # Sans cookie sur ce poste, l'origine est la seule garde contre une page tierce
            origin = request.headers.get("origin")
            if method not in _SAFE_METHODS and origin and urlsplit(origin).netloc != host:
                return _refuse(path, 403, _FOREIGN_ORIGIN)
            return await call_next(request)

        if path in _OPEN_PATHS:
            return await call_next(request)

        code = request.query_params.get("code")
        if code is not None:
            if self.gate.is_blocked(address):
                return _refuse(path, 429, _TOO_MANY_ATTEMPTS)
            if not self.gate.check_code(address, code):
                return _refuse(path, 401, _UNAUTHENTICATED)
            # Le code quitte l'URL (historique, favoris) une fois le cookie pose
            rest = [(k, v) for k, v in request.query_params.multi_items() if k != "code"]
            target = path + ("?" + urlencode(rest) if rest else "")
            response = RedirectResponse(target, status_code=303)
            response.set_cookie(
                COOKIE_NAME, self.gate.cookie_token, httponly=True, samesite="strict", path="/"
            )
            return response

        if not self.gate.check_cookie(request.cookies.get(COOKIE_NAME)):
            return _refuse(path, 401, _UNAUTHENTICATED)
        if is_technician_route(method, path):
            return _refuse(path, 403, _TECHNICIAN_ONLY)
        return await call_next(request)
