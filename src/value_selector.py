"""
Módulo de seleção do valor a monitorar.

Varre o DOM da página identificando elementos com números e exibe
uma lista ao usuário. O usuário escolhe qual valor deseja monitorar,
e o sistema armazena o XPath desse elemento para acompanhamento.
"""

import os
import logging
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from selenium.webdriver.common.by import By

logger = logging.getLogger(__name__)

# Caminho do script JS que lista valores numéricos com seus XPaths
JS_LISTAR_VALORES_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "js", "list_values.js"
)


def _carregar_script_js() -> str:
    """Lê o conteúdo do arquivo JS que lista valores. O(1)."""
    with open(JS_LISTAR_VALORES_PATH, encoding="utf-8") as f:
        return f.read()


def listar_valores_com_xpath(driver: webdriver.Chrome) -> list:
    """
    Retorna lista de dicts {text, xpath} com todos os elementos da página
    que contêm dígitos.

    Complexidade: O(n · d) onde n = total de elementos no DOM e
    d = profundidade média da árvore. O custo vem de `getXPath()` no JS,
    que sobe recursivamente até a raiz para cada folha com dígitos.
    A deduplicação em Python é O(k), com k = valores encontrados.
    """
    try:
        script = _carregar_script_js()
        resultados = driver.execute_script(script)
        # Remove duplicatas mantendo ordem
        vistos = set()
        unicos = []
        for r in resultados:
            chave = (r["text"], r["xpath"])
            if chave not in vistos:
                vistos.add(chave)
                unicos.append(r)
        return unicos
    except WebDriverException as exc:
        logger.error("Erro ao listar valores da página: %s", exc)
        return []


def selecionar_valor(driver: webdriver.Chrome) -> dict:
    """
    Exibe os valores numéricos encontrados e pede que o usuário escolha
    qual monitorar. Retorna {text, xpath} do selecionado.

    Complexidade: O(n · d) — dominado pelo `listar_valores_com_xpath`.
    A impressão dos resultados é limitada a 30 itens (O(1)).
    """
    valores = listar_valores_com_xpath(driver)

    if not valores:
        logger.warning("Nenhum valor numérico encontrado na página.")
        return {}

    print("\n--- Valores numéricos encontrados na página ---\n")
    # Mostra os primeiros 30 para não poluir o console
    limite = min(len(valores), 30)
    for i in range(limite):
        texto = valores[i]["text"]
        # Trunca texto longo para visualização
        preview = texto if len(texto) <= 80 else texto[:77] + "..."
        print(f"  [{i}] {preview}")

    if len(valores) > limite:
        print(f"  ... e mais {len(valores) - limite} valores (não exibidos).")
    print()

    while True:
        escolha = input(f"Digite o índice do valor a monitorar (0-{limite - 1}): ").strip()
        try:
            idx = int(escolha)
            if 0 <= idx < limite:
                selecionado = valores[idx]
                logger.info("LOG | Valor selecionado: '%s'", selecionado["text"])
                logger.info("LOG | XPath: %s", selecionado["xpath"])
                return selecionado
        except ValueError:
            pass
        print("  Índice inválido. Tente novamente.")


def ler_valor_por_xpath(driver: webdriver.Chrome, xpath: str) -> str:
    """Lê o texto atual do elemento identificado pelo XPath.

    Complexidade: O(d) no caso médio, O(n) no pior caso, onde d =
    profundidade do XPath absoluto e n = tamanho do DOM. O navegador
    resolve XPaths absolutos descendo nível a nível.
    """
    try:
        elemento = driver.find_element(By.XPATH, xpath)
        return elemento.text.strip()
    except NoSuchElementException:
        logger.warning("Elemento não encontrado no XPath: %s", xpath)
        return ""
    except WebDriverException as exc:
        logger.error("Erro ao ler elemento por XPath: %s", exc)
        return ""
