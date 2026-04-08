"""
Modulo de busca de dados em paginas web.

Utiliza Selenium para acessar a pagina e Regex para extrair:
- Valores monetarios (ex: R$ 1.234,56)
- Datas com barras (ex: 01/01/2026)
"""

import re
from app import criar_driver, validar_url


def encontrar_monetarios(texto: str) -> list:
    """Extrai valores monetários do texto usando regex (ex: R$ 1.234,56 / $ 99.90)."""
    padrao = r'R?\$\s?\d{1,3}(?:\.\d{3})*,\d{2}|\d{1,3}(?:\.\d{3})*,\d{2}'
    return re.findall(padrao, texto)


def encontrar_datas(texto: str) -> list:
    """Extrai datas no formato dd/mm/aaaa ou dd/mm/aa do texto usando regex."""
    padrao = r'\d{1,2}/\d{1,2}/\d{2,4}'
    return re.findall(padrao, texto)


def buscar_numeros_na_pagina(url: str, headless: bool = True) -> dict:
    """Acessa uma URL via Selenium e retorna monetários e datas encontrados."""
    if not validar_url(url):
        return {"erro": "URL inválida.", "monetarios": [], "datas": []}

    driver = criar_driver(headless=headless)
    try:
        driver.get(url)
        texto = driver.find_element("tag name", "body").text
        monetarios = encontrar_monetarios(texto)
        datas = encontrar_datas(texto)
        return {"texto": texto[:500], "monetarios": monetarios, "datas": datas}
    except Exception as e:
        return {"erro": str(e), "monetarios": [], "datas": []}
    finally:
        driver.quit()