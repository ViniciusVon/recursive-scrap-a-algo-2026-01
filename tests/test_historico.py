"""
Testa a persistência do histórico de sessões (sem depender de Selenium).

Gravamos direto via `src.db.gravar_sessao_historica` e validamos os
endpoints REST que expõem os dados.
"""

from dataclasses import dataclass
from datetime import datetime

from fastapi.testclient import TestClient

from src.db import gravar_sessao_historica


@dataclass
class _Alteracao:
    # Duck-typing para `gravar_sessao_historica`: precisa de .ciclo,
    # .timestamp, .valor_antigo, .valor_novo.
    ciclo: int
    timestamp: datetime
    valor_antigo: str
    valor_novo: str


def _criar_usuario(client: TestClient) -> int:
    r = client.post("/usuarios", json={"nome": "Gabriel", "email": "g@x.com"})
    return r.json()["id"]


def test_sessao_historica_round_trip(client: TestClient) -> None:
    uid = _criar_usuario(client)

    gravar_sessao_historica(
        sessao_id="s1",
        usuario_id=uid,
        url="https://example.com",
        xpath_monitorado="//span",
        valor_inicial="R$ 10,00",
        valor_final="R$ 12,00",
        iniciada_em=datetime(2026, 4, 20, 10, 0, 0).isoformat(),
        encerrada_em=datetime(2026, 4, 20, 11, 0, 0).isoformat(),
        alteracoes=[
            _Alteracao(1, datetime(2026, 4, 20, 10, 15), "R$ 10,00", "R$ 11,00"),
            _Alteracao(2, datetime(2026, 4, 20, 10, 45), "R$ 11,00", "R$ 12,00"),
        ],
    )

    r = client.get(f"/usuarios/{uid}/sessoes")
    assert r.status_code == 200
    sessoes = r.json()
    assert len(sessoes) == 1
    assert sessoes[0]["id"] == "s1"
    assert sessoes[0]["total_alteracoes"] == 2

    r = client.get("/sessoes/historicas/s1")
    assert r.status_code == 200
    assert r.json()["valor_final"] == "R$ 12,00"

    r = client.get("/sessoes/historicas/s1/alteracoes")
    assert r.status_code == 200
    alts = r.json()
    assert [a["ciclo"] for a in alts] == [1, 2]
    assert alts[1]["valor_novo"] == "R$ 12,00"


def test_idempotencia_gravar(client: TestClient) -> None:
    uid = _criar_usuario(client)
    args = dict(
        sessao_id="s-idem",
        usuario_id=uid,
        url="https://example.com",
        xpath_monitorado=None,
        valor_inicial="A",
        valor_final="B",
        iniciada_em=datetime(2026, 4, 20, 10, 0).isoformat(),
        encerrada_em=datetime(2026, 4, 20, 11, 0).isoformat(),
        alteracoes=[_Alteracao(1, datetime(2026, 4, 20, 10, 5), "A", "B")],
    )
    gravar_sessao_historica(**args)
    # Re-gravar a mesma sessão deve substituir sem duplicar alterações.
    gravar_sessao_historica(**args)

    r = client.get("/sessoes/historicas/s-idem/alteracoes")
    assert len(r.json()) == 1


def test_historica_inexistente_404(client: TestClient) -> None:
    r = client.get("/sessoes/historicas/nao-existe")
    assert r.status_code == 404
