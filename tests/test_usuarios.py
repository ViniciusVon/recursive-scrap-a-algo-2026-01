"""Testes das rotas de usuários — cobrem schema strict e happy path."""

from fastapi.testclient import TestClient


def test_cadastro_e_listagem(client: TestClient) -> None:
    r = client.post("/usuarios", json={"nome": "Gabriel", "email": "g@x.com"})
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["nome"] == "Gabriel"
    assert body["email"] == "g@x.com"
    assert body["id"] >= 1

    r = client.get("/usuarios")
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_strict_rejeita_campo_extra(client: TestClient) -> None:
    # A configuração `extra="forbid"` deve barrar com 422.
    r = client.post(
        "/usuarios",
        json={"nome": "Gabriel", "email": "g@x.com", "admin": True},
    )
    assert r.status_code == 422


def test_strict_trim_whitespace(client: TestClient) -> None:
    r = client.post(
        "/usuarios",
        json={"nome": "   Gabriel   ", "email": "g@x.com"},
    )
    assert r.status_code == 201
    assert r.json()["nome"] == "Gabriel"


def test_email_invalido(client: TestClient) -> None:
    r = client.post("/usuarios", json={"nome": "Gabriel", "email": "nao-eh-email"})
    assert r.status_code == 422


def test_nome_curto(client: TestClient) -> None:
    r = client.post("/usuarios", json={"nome": "Ga", "email": "g@x.com"})
    assert r.status_code == 422


def test_get_usuario_inexistente(client: TestClient) -> None:
    r = client.get("/usuarios/9999")
    assert r.status_code == 404


def test_sessoes_do_usuario_vazio(client: TestClient) -> None:
    r = client.post("/usuarios", json={"nome": "Gabriel", "email": "g@x.com"})
    uid = r.json()["id"]
    r = client.get(f"/usuarios/{uid}/sessoes")
    assert r.status_code == 200
    assert r.json() == []
