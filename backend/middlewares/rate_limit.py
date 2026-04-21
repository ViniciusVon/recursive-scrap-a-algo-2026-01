"""
Rate limiting in-memory com token bucket simplificado.

Por que um middleware caseiro em vez de `slowapi`:
    - zero dep nova
    - só protegemos 3 endpoints — não justifica trazer Redis + lib
    - os limites são leves o suficiente para caber num dicionário

Escopo:
    - Chave = (IP do cliente, rota protegida).
    - Cada chave tem uma janela deslizante (fifo de timestamps).
    - Quando o número de chamadas dentro da janela >= limite, devolve
      HTTP 429 com `Retry-After` em segundos.

Limitações (documentadas):
    - Memória local: se subir em mais de 1 processo, cada worker tem seu
      próprio contador. Para o escopo deste projeto (entrega acadêmica,
      1 processo) é aceitável.
    - Não persiste entre reinícios — intencional, é rate limit, não
      auditoria.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp


@dataclass(frozen=True)
class Regra:
    """Descreve `max` chamadas a cada `janela` segundos."""

    max: int
    janela: int  # segundos


# Endpoints protegidos. (método, prefixo-exato) → regra.
#
# Prefixos exatos porque nossas rotas críticas não têm parâmetros de
# caminho no meio que compliquem o match. Para `/sessoes/{id}/selecionar`
# usamos `startswith` + `.endswith("/selecionar")` abaixo.
REGRAS: dict[tuple[str, str], Regra] = {
    ("POST", "/usuarios"): Regra(max=5, janela=60),
    ("POST", "/sessoes"): Regra(max=10, janela=60),
    # (`/selecionar` tratado no `_regra_para`)
}

# Regra aplicada a qualquer `POST /sessoes/*/selecionar`.
REGRA_SELECIONAR = Regra(max=15, janela=60)


def _regra_para(metodo: str, caminho: str) -> Regra | None:
    """Resolve a regra que se aplica à requisição, ou None."""
    chave = (metodo, caminho)
    if chave in REGRAS:
        return REGRAS[chave]
    if (
        metodo == "POST"
        and caminho.startswith("/sessoes/")
        and caminho.endswith("/selecionar")
    ):
        return REGRA_SELECIONAR
    return None


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Token-bucket por (IP, rota-protegida). Ver docstring do módulo."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        # defaultdict(deque) evita checar existência em cada chamada.
        self._hits: dict[tuple[str, str, str], Deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        regra = _regra_para(request.method, request.url.path)
        if regra is None:
            return await call_next(request)

        ip = request.client.host if request.client else "unknown"
        chave = (ip, request.method, request.url.path)
        agora = time.monotonic()

        historico = self._hits[chave]
        # Janela deslizante: descarta timestamps fora do intervalo.
        limite_janela = agora - regra.janela
        while historico and historico[0] < limite_janela:
            historico.popleft()

        if len(historico) >= regra.max:
            # Quantos segundos até a entrada mais antiga sair da janela?
            retry_em = max(1, int(regra.janela - (agora - historico[0])))
            return JSONResponse(
                status_code=429,
                content={
                    "detail": (
                        "Muitas requisições. Aguarde alguns instantes "
                        "antes de tentar novamente."
                    )
                },
                headers={"Retry-After": str(retry_em)},
            )

        historico.append(agora)
        return await call_next(request)
