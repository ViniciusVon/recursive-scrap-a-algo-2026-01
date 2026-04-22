"""
Verifica o rate limit em /usuarios.

Limite é 5 POSTs por 60s por IP — a 6ª chamada seguida devolve 429
com cabeçalho Retry-After.
"""

from fastapi.testclient import TestClient


def test_rate_limit_usuarios_bloqueia_sexta_chamada(client: TestClient) -> None:
    # `validar_nome_usuario` só aceita letras — nomes sem número.
    nomes = ["Alice", "Bruno", "Carla", "Diego", "Erika"]
    for i, nome in enumerate(nomes):
        r = client.post(
            "/usuarios",
            json={"nome": nome, "email": f"u{i}@x.com"},
        )
        # Os 5 primeiros passam (201 criado).
        assert r.status_code == 201, (i, r.text)

    # A sexta chamada bate no limite.
    r = client.post("/usuarios", json={"nome": "Sexta", "email": "six@x.com"})
    assert r.status_code == 429
    assert "Retry-After" in r.headers
    assert int(r.headers["Retry-After"]) >= 1
    assert "Muitas requisições" in r.json()["detail"]


def test_rate_limit_nao_afeta_get(client: TestClient) -> None:
    # GET /usuarios não é protegido — 10 chamadas devem passar.
    for _ in range(10):
        r = client.get("/usuarios")
        assert r.status_code == 200
