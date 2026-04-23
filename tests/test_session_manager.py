"""Testes para o gerenciador de sessões e controle de filas."""

from unittest.mock import MagicMock, patch
from backend.services.session_manager import SessionManager

@patch("backend.services.session_manager.criar_driver")
def test_criar_e_obter_sessao(mock_criar_driver):
    mock_criar_driver.return_value = MagicMock()
    manager = SessionManager()
    
    sessao = manager.criar(usuario_id=1, url="http://exemplo.com", headless=True)
    
    assert sessao.id is not None
    assert sessao.url == "http://exemplo.com"
    assert sessao.status == "iniciada"
    
    # O lookup deve retornar a mesma instância
    sessao_recuperada = manager.obter(sessao.id)
    assert sessao_recuperada == sessao

@patch("backend.services.session_manager.criar_driver")
def test_encerrar_sessao_limpa_registry_e_fecha_driver(mock_criar_driver):
    mock_driver = MagicMock()
    mock_criar_driver.return_value = mock_driver
    manager = SessionManager()
    
    sessao = manager.criar(usuario_id=1, url="http://teste.com", headless=True)
    sucesso = manager.encerrar(sessao.id)
    
    assert sucesso is True
    assert manager.obter(sessao.id) is None
    assert sessao.status == "encerrada"
    mock_driver.quit.assert_called_once()

@patch("backend.services.session_manager.criar_driver")
def test_pub_sub_inscricao_e_envio_mensagens(mock_criar_driver):
    mock_criar_driver.return_value = MagicMock()
    manager = SessionManager()
    sessao = manager.criar(usuario_id=1, url="http://teste.com", headless=True)
    
    # Simula dois clientes WebSocket se inscrevendo na mesma sessão
    fila_cliente1 = manager.subscribe(sessao.id)
    fila_cliente2 = manager.subscribe(sessao.id)
    
    # Emite um evento falso
    manager._emit(sessao, {"type": "teste", "mensagem": "ola"})
    
    # Verifica se ambas as filas receberam o evento
    assert fila_cliente1.get_nowait() == {"type": "teste", "mensagem": "ola"}
    assert fila_cliente2.get_nowait() == {"type": "teste", "mensagem": "ola"}
    
    # Cliente 1 sai, não deve mais receber eventos
    manager.unsubscribe(sessao.id, fila_cliente1)
    manager._emit(sessao, {"type": "teste2"})
    
    assert fila_cliente1.empty() is True
    assert fila_cliente2.get_nowait() == {"type": "teste2"}