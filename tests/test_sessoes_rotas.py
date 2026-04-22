"""Testes de integração para as rotas da API de sessões."""

from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from backend.main import app # Certifique-se de que o caminho de importação da sua app FastAPI está correto

client = TestClient(app)

@patch("backend.routes.sessoes.buscar_usuario_por_id")
@patch("backend.routes.sessoes.validar_url")
@patch("backend.routes.sessoes.manager")
def test_post_sessao_sucesso(mock_manager, mock_validar_url, mock_buscar_usuario):
    # Simula validações passando com sucesso
    mock_buscar_usuario.return_value = (1, "Nome", "email@teste.com")
    mock_validar_url.return_value = True
    
    # Simula o estado retornado pelo manager.criar
    mock_estado = MagicMock()
    mock_estado.id = "abc12345"
    mock_estado.usuario_id = 1
    mock_estado.url = "http://exemplo.com"
    mock_estado.headless = True
    mock_estado.status = "iniciada"
    mock_estado.xpath_monitorado = None
    mock_estado.valor_atual = None
    mock_manager.criar.return_value = mock_estado

    response = client.post(
        "/sessoes",
        json={"usuario_id": 1, "url": "http://exemplo.com", "headless": True}
    )
    
    assert response.status_code == 201
    body = response.json()
    assert body["id"] == "abc12345"
    assert body["status"] == "iniciada"

@patch("backend.routes.sessoes.buscar_usuario_por_id")
def test_post_sessao_usuario_nao_encontrado(mock_buscar_usuario):
    # Simula usuário não existindo no DB
    mock_buscar_usuario.return_value = None
    
    response = client.post(
        "/sessoes",
        json={"usuario_id": 999, "url": "http://exemplo.com", "headless": True}
    )
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Usuário não encontrado."

@patch("backend.routes.sessoes.manager")
def test_get_sessao_inexistente(mock_manager):
    # Simula o lookup do manager não encontrando a sessão
    mock_manager.obter.return_value = None
    
    response = client.get("/sessoes/nao-existe")
    assert response.status_code == 404