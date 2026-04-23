"""Testes para utilitários gerais."""

from unittest.mock import patch, MagicMock
from src.utils import validar_url, criar_driver

def test_validar_url_sucesso():
    assert validar_url("http://exemplo.com") is True
    assert validar_url("https://meu-dominio.com.br/caminho?query=1") is True
    assert validar_url("https://localhost:8000") is True

def test_validar_url_falha():
    assert validar_url("exemplo.com") is False
    assert validar_url("ftp://exemplo.com") is False
    assert validar_url("texto aleatorio") is False

@patch("src.utils.webdriver.Chrome")
def test_criar_driver_headless(mock_chrome):
    driver = criar_driver(headless=True)
    
    # Verifica se a classe Chrome foi instanciada
    mock_chrome.assert_called_once()
    
    # Recupera os kwargs passados na instanciação
    kwargs = mock_chrome.call_args.kwargs
    options = kwargs.get("options")
    
    assert options is not None
    assert "--headless" in options.arguments
    assert "--disable-gpu" in options.arguments