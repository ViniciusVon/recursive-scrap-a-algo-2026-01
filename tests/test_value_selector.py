"""Testes para o seletor numérico no DOM."""

from unittest.mock import MagicMock, patch
from selenium.common.exceptions import WebDriverException
from src.value_selector import listar_valores_com_xpath, ler_valor_por_xpath

@patch("src.value_selector._carregar_script_js")
def test_listar_valores_deduplicacao(mock_carregar_js):
    mock_carregar_js.return_value = "return []"
    
    mock_driver = MagicMock()
    # Simula o JS retornando elementos com XPaths e textos (com um duplicado intencional)
    mock_driver.execute_script.return_value = [
        {"text": "100", "xpath": "/div[1]"},
        {"text": "200", "xpath": "/div[2]"},
        {"text": "100", "xpath": "/div[1]"} # Duplicata
    ]
    
    resultados = listar_valores_com_xpath(mock_driver)
    
    assert len(resultados) == 2
    assert resultados[0]["text"] == "100"

def test_listar_valores_erro_driver():
    mock_driver = MagicMock()
    mock_driver.execute_script.side_effect = WebDriverException("Erro JS")
    
    resultados = listar_valores_com_xpath(mock_driver)
    assert resultados == [] # Deve retornar lista vazia graciosamente

def test_ler_valor_por_xpath_sucesso():
    mock_driver = MagicMock()
    mock_elemento = MagicMock()
    mock_elemento.text = " 350,00 "
    mock_driver.find_element.return_value = mock_elemento
    
    valor = ler_valor_por_xpath(mock_driver, "/html/body/p")
    assert valor == "350,00" # O strip() deve limpar espaços