"""
Modulo de busca de dados em paginas web.

Utiliza Selenium para acessar a pagina e Regex para extrair:
- Qualquer sequência numérica (inteiros, decimais, monetários, horários, datas, etc.)
"""

import re
import logging
from selenium.common.exceptions import WebDriverException
from src.utils import criar_driver, validar_url


def encontrar_numeros(texto: str) -> list:
    """
    Extrai qualquer sequência que contenha dígitos do texto.
    Captura: inteiros, decimais, monetários, horários (12:30:45),
    datas (01/01/2026), porcentagens, etc.

    Complexidade: O(n) onde n = len(texto). `re.findall` percorre
    a string uma única vez com regex sem backtracking catastrófico.
    """
    padrao = r'[\d]+(?:[/:.,\-]\d+)*'
    return re.findall(padrao, texto)


def buscar_numeros_na_pagina(url: str, headless: bool = True) -> dict:
    """Acessa uma URL via Selenium e retorna monetários e datas encontrados."""
    if not validar_url(url):
        return {"erro": "URL inválida.", "monetarios": [], "datas": []}

    driver = criar_driver(headless=headless)
    try:
        driver.get(url)
        texto = driver.find_element("tag name", "body").text
        numeros = encontrar_numeros(texto)
        logger = logging.getLogger(__name__)
        logger.info("Números encontrados: %d valores", len(numeros))
        return {"numeros": numeros}
    except WebDriverException as e:
        return {"erro": f"Falha no navegador: {e}", "numeros": []}
    except Exception as e:
        return {"erro": f"Erro inesperado: {e}", "numeros": []}
    finally:
        driver.quit()
