"""
Modelos Pydantic da API.

Separados em dois grupos:
- Inputs (request bodies)  → sufixo `In`
- Outputs (response bodies) → sufixo `Out`
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


# Configuração strict aplicada a TODOS os *In*:
#   - `extra="forbid"`         → rejeita campos desconhecidos (pega typo
#                                 no cliente: {"nomee": "..."} vira 422).
#   - `str_strip_whitespace`   → trim automático em strings.
#   - `str_min_length=1`       → strings vazias já reprovam sem validator.
STRICT_IN = ConfigDict(
    extra="forbid",
    str_strip_whitespace=True,
    str_min_length=1,
)


# ---------------------------------------------------------------------------
# Usuário
# ---------------------------------------------------------------------------

class UsuarioIn(BaseModel):
    model_config = STRICT_IN

    nome: str = Field(..., min_length=3, max_length=80)
    email: EmailStr

    @field_validator("nome")
    @classmethod
    def _nome_nao_vazio(cls, v: str) -> str:
        # Após o strip, o campo precisa continuar tendo algo visível.
        # Strings de só espaço virariam "" e já seriam barradas pelo
        # `min_length=3`, mas o erro fica mais claro aqui.
        if not v.strip():
            raise ValueError("nome não pode ser vazio")
        return v


class UsuarioOut(BaseModel):
    id: int
    nome: str
    email: str


# ---------------------------------------------------------------------------
# Sessão de monitoramento
# ---------------------------------------------------------------------------

class SessaoIn(BaseModel):
    model_config = STRICT_IN

    usuario_id: int = Field(..., gt=0)
    url: str = Field(..., min_length=8, max_length=2048)
    headless: bool = True

    @field_validator("url")
    @classmethod
    def _url_protocolo(cls, v: str) -> str:
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("URL precisa começar com http:// ou https://")
        return v


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
    model_config = STRICT_IN

    xpath: str = Field(..., min_length=1, max_length=4096)
    text: str = Field(..., min_length=1, max_length=512)


class RegistroHistorico(BaseModel):
    ciclo: int
    timestamp: datetime
    valor_antigo: str
    valor_novo: str


# ---------------------------------------------------------------------------
# Histórico persistente de sessões encerradas
# ---------------------------------------------------------------------------


class SessaoHistoricaOut(BaseModel):
    id: str
    usuario_id: int
    url: str
    xpath_monitorado: Optional[str] = None
    valor_inicial: Optional[str] = None
    valor_final: Optional[str] = None
    total_alteracoes: int
    iniciada_em: datetime
    encerrada_em: datetime
