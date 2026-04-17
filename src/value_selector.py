"""
Módulo de seleção do valor a monitorar.

Varre o DOM da página identificando elementos com números e exibe
uma lista ao usuário. O usuário escolhe qual valor deseja monitorar,
e o sistema armazena o XPath desse elemento para acompanhamento.
"""

import logging
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from selenium.webdriver.common.by import By

logger = logging.getLogger(__name__)

# Script JS: percorre o DOM, pega elementos folha (sem filhos) com texto que
# contém dígitos, e devolve [{text, xpath}, ...]
JS_LISTAR_VALORES = """
function getXPath(el) {
    if (el === document.body) return '/html/body';
    var ix = 0;
    var siblings = el.parentNode ? el.parentNode.childNodes : [];
    for (var i = 0; i < siblings.length; i++) {
        var sib = siblings[i];
        if (sib === el) {
            return getXPath(el.parentNode) + '/' + el.tagName.toLowerCase() + '[' + (ix + 1) + ']';
        }
        if (sib.nodeType === 1 && sib.tagName === el.tagName) ix++;
    }
    return '';
}

var resultados = [];
var todos = document.body.getElementsByTagName('*');
var regex = /\\d/;
for (var i = 0; i < todos.length; i++) {
    var el = todos[i];
    if (el.children.length > 0) continue;
    var tag = el.tagName.toLowerCase();
    if (tag === 'script' || tag === 'style' || tag === 'noscript') continue;
    var texto = (el.innerText || el.textContent || '').trim();
    if (!texto || !regex.test(texto)) continue;
    if (texto.length > 200) continue;
    resultados.push({text: texto, xpath: getXPath(el)});
}
return resultados;
"""


def listar_valores_com_xpath(driver: webdriver.Chrome) -> list:
    """
    Retorna lista de dicts {text, xpath} com todos os elementos da página
    que contêm dígitos. O(n) onde n = número de elementos no DOM.
    """
    try:
        resultados = driver.execute_script(JS_LISTAR_VALORES)
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
    qual monitorar. Retorna {text, xpath} do selecionado. O(n).
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
    """Lê o texto atual do elemento identificado pelo XPath. O(1)."""
    try:
        elemento = driver.find_element(By.XPATH, xpath)
        return elemento.text.strip()
    except NoSuchElementException:
        logger.warning("Elemento não encontrado no XPath: %s", xpath)
        return ""
    except WebDriverException as exc:
        logger.error("Erro ao ler elemento por XPath: %s", exc)
        return ""
