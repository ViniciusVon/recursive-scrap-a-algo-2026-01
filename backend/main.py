"""
Ponto de entrada da API FastAPI.

Sobe em `localhost:8000` e expõe os recursos:
    - GET/POST/GET-by-id   /usuarios
    - POST/GET/DELETE      /sessoes
    - GET                  /sessoes/{id}/valores
    - POST                 /sessoes/{id}/selecionar
    - GET                  /sessoes/{id}/historico

Para rodar em desenvolvimento:
    uvicorn backend.main:app --reload --port 8000

### Configuração via ambiente (Fase 4)

- `CORS_ORIGINS`: lista separada por vírgulas de origens permitidas.
  Default contempla o Vite dev server em `localhost` e `127.0.0.1`.
  Em produção, defina com o domínio público do frontend.
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.middlewares.rate_limit import RateLimitMiddleware
from backend.routes import sessoes, usuarios, websocket
from src.db import inicializar_banco


def _carregar_origens_cors() -> list[str]:
    """
    Lê `CORS_ORIGINS` do ambiente (separado por vírgulas). Se ausente,
    devolve apenas as origens de dev — seguro por default.
    """
    bruto = os.environ.get("CORS_ORIGINS")
    if not bruto:
        return ["http://localhost:5173", "http://127.0.0.1:5173"]
    return [x.strip() for x in bruto.split(",") if x.strip()]


@asynccontextmanager
async def lifespan(_: FastAPI):
    # `on_event` foi deprecado; lifespan async é o padrão atual.
    inicializar_banco()
    yield


app = FastAPI(
    title="Monitor de Preços API",
    version="1.0.0",
    description="Backend HTTP do assistente de lances.",
    lifespan=lifespan,
)

# CORS restrito: apenas origens conhecidas, métodos usados pela SPA e
# cabeçalhos estritamente necessários. `allow_credentials=False` porque
# não usamos cookies/sessão — só precisaria habilitar se migrássemos
# para auth com cookie.
app.add_middleware(
    CORSMiddleware,
    allow_origins=_carregar_origens_cors(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    max_age=600,
)

# Rate limiting — protege endpoints críticos contra loops acidentais
# do frontend e ataques de força bruta em cadastro/criação de sessão.
# Aplicado via middleware; rotas não-listadas passam sem contagem.
app.add_middleware(RateLimitMiddleware)


@app.get("/health", tags=["infra"])
def health() -> dict:
    return {"status": "ok"}


app.include_router(usuarios.router)
app.include_router(sessoes.router)
app.include_router(websocket.router)
