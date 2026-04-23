"""Testes para o módulo de busca de números na web."""

from unittest.mock import MagicMock, patch
from src.search_numbers import encontrar_numeros, buscar_numeros_na_pagina

def test_encontrar_numeros_simples():
    texto = "Temos 10 laranjas e 5.5 maçãs."
    resultado = encontrar_numeros(texto)
    assert "10" in resultado
    assert "5.5" in resultado

def test_encontrar_formatos_complexos():
    texto = "Data: 01/01/2026, Hora: 12:30:45, Valor: 1.500,99"
    resultado = encontrar_numeros(texto)
    assert "01/01/2026" in resultado
    assert "12:30:45" in resultado
    assert "1.500,99" in resultado

def test_encontrar_numeros_texto_vazio():
    assert encontrar_numeros("Apenas texto sem digitos") == []
    assert encontrar_numeros("") == []

@patch("src.search_numbers.criar_driver")
@patch("src.search_numbers.validar_url")
def test_buscar_numeros_na_pagina_sucesso(mock_validar_url, mock_criar_driver):
    mock_validar_url.return_value = True
    
    # Simula o driver do Selenium e a busca do elemento body
    mock_driver = MagicMock()
    mock_element = MagicMock()
    mock_element.text = "Preço atual: 250,00"
    mock_driver.find_element.return_value = mock_element
    mock_criar_driver.return_value = mock_driver

    resultado = buscar_numeros_na_pagina("http://exemplo.com")
    
    assert "numeros" in resultado
    assert resultado["numeros"] == ["250,00"]
    # Verifica se o Selenium fechou o browser no finally
    mock_driver.quit.assert_called_once()

@patch("src.search_numbers.validar_url")
def test_buscar_numeros_na_pagina_url_invalida(mock_validar_url):
    mock_validar_url.return_value = False
    resultado = buscar_numeros_na_pagina("url-ruim")
    assert "erro" in resultado
    assert resultado["erro"] == "URL inválida."