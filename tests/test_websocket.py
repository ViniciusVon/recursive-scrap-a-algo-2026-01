"""Testes da rota de WebSocket FastAPI."""

from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from backend.main import app # Certifique-se de que a importação do app está correta
import queue

client = TestClient(app)

@patch("backend.routes.websocket.manager")
def test_ws_sessao_nao_encontrada(mock_manager):
    # Se o manager não encontra a sessão, deve fechar a conexão
    mock_manager.obter.return_value = None
    
    with client.websocket_connect("/ws/sessoes/nao-existe") as websocket:
        dados = websocket.receive_json()
        assert dados["type"] == "erro"
        # O FastAPI TestClient lança uma exceção (WebSocketDisconnect) quando o socket fecha
        # ou encerra a interação. O código interno no app usa `ws.close(code=4404)`.

@patch("backend.routes.websocket.manager")
def test_ws_fluxo_inicial_e_eventos(mock_manager):
    mock_estado = MagicMock()
    mock_estado.id = "s1"
    mock_estado.usuario_id = 1
    mock_estado.url = "http://teste"
    mock_estado.headless = True
    mock_estado.status = "monitorando"
    mock_estado.xpath_monitorado = "//p"
    mock_estado.valor_atual = "10"
    mock_estado.ciclo = 1
    mock_estado.historico = []
    
    mock_manager.obter.return_value = mock_estado
    
    # Simula a fila de eventos do manager.subscribe
    mock_fila = MagicMock()
    mock_manager.subscribe.return_value = mock_fila
    
    # Prepara a fila para devolver um evento de ciclo, e depois levantar Timeout
    # para não bloquear o teste para sempre.
    mock_fila.get.side_effect = [
        {"type": "ciclo", "valor_atual": "15"},
        {"type": "encerrada"} # Encerra o loop do while no endpoint
    ]
    
    with client.websocket_connect("/ws/sessoes/s1") as websocket:
        # Recebe o snapshot inicial da conexão
        snapshot = websocket.receive_json()
        assert snapshot["type"] == "inicial"
        assert snapshot["sessao"]["valor_atual"] == "10"
        
        # Recebe o evento da fila injetado
        evento_ciclo = websocket.receive_json()
        assert evento_ciclo["type"] == "ciclo"
        assert evento_ciclo["valor_atual"] == "15"
        
        # O loop terminará devido à mensagem "encerrada" injetada na sequência
        mock_manager.unsubscribe.assert_called_once_with("s1", mock_fila)