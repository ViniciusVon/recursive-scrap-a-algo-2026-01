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
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes import sessoes, usuarios, websocket
from src.db import inicializar_banco

app = FastAPI(
    title="Monitor de Preços API",
    version="0.1.0",
    description="Backend HTTP do assistente de lances (Fase 1 — MVP).",
)

# CORS liberado para o Vite dev server. Em prod (Fase 4) restringir.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    inicializar_banco()


@app.get("/health", tags=["infra"])
def health() -> dict:
    return {"status": "ok"}


app.include_router(usuarios.router)
app.include_router(sessoes.router)
app.include_router(websocket.router)
