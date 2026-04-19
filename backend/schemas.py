"""
Modelos Pydantic da API.

Separados em dois grupos:
- Inputs (request bodies)  → sufixo `In`
- Outputs (response bodies) → sufixo `Out`
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# ---------------------------------------------------------------------------
# Usuário
# ---------------------------------------------------------------------------

class UsuarioIn(BaseModel):
    nome: str = Field(..., min_length=3, max_length=80)
    email: EmailStr


class UsuarioOut(BaseModel):
    id: int
    nome: str
    email: str


# ---------------------------------------------------------------------------
# Sessão de monitoramento
# ---------------------------------------------------------------------------

class SessaoIn(BaseModel):
    usuario_id: int
    url: str
    headless: bool = True


class SessaoOut(BaseModel):
    id: str
    usuario_id: int
    url: str
    headless: bool
    status: str  # "iniciada" | "monitorando" | "encerrada"
    xpath_monitorado: Optional[str] = None
    valor_atual: Optional[str] = None


class ValorEncontrado(BaseModel):
    indice: int
    text: str
    xpath: str


class SelecaoIn(BaseModel):
    xpath: str
    text: str


class RegistroHistorico(BaseModel):
    ciclo: int
    timestamp: datetime
    valor_antigo: str
    valor_novo: str
