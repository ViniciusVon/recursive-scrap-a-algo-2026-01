"""
Módulo de registro em Google Forms via Selenium.

Abre o formulário em uma segunda aba, preenche os campos com os dados
da alteração detectada e clica no botão de enviar.
"""

import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    WebDriverException,
    TimeoutException,
    NoSuchElementException,
)

from src.constants import TIMEOUT_SEGUNDOS

logger = logging.getLogger(__name__)


def abrir_aba_form(driver: webdriver.Chrome, form_url: str) -> str:
    """
    Abre o Google Form em uma segunda aba e retorna o handle dela.
    Mantém a aba original como a ativa. O(1)
    """
    driver.execute_script(f"window.open('{form_url}', '_blank');")
    handles = driver.window_handles
    aba_form = handles[-1]
    logger.info("LOG | Segunda aba aberta com Google Form: %s", form_url)
    return aba_form


def registrar_alteracao(
    driver: webdriver.Chrome,
    aba_monitor: str,
    aba_form: str,
    form_url: str,
    dados: dict,
) -> bool:
    """
    Troca para a aba do Google Form, preenche os campos e clica em Enviar.
    Retorna True se registrou com sucesso.

    Complexidade: O(m) onde m = tamanho do DOM do formulário. A busca
    de `find_elements` é linear no DOM; o preenchimento dos k campos e
    a varredura dos botões até achar "Enviar" são O(k) e O(b), ambos
    dominados por O(m). I/O de rede (reload do form) é custo externo.

    Campos esperados (na ordem do form):
      1. URL monitorada
      2. Valor antigo
      3. Valor novo
      4. Timestamp
      5. Usuário
    """
    valores = [
        dados.get("url", ""),
        dados.get("valor_antigo", ""),
        dados.get("valor_novo", ""),
        dados.get("timestamp", ""),
        dados.get("usuario", ""),
    ]

    try:
        driver.switch_to.window(aba_form)
        # Recarrega o form para limpar respostas anteriores
        driver.get(form_url)

        wait = WebDriverWait(driver, TIMEOUT_SEGUNDOS)

        # Google Forms usa <input type="text"> para resposta curta
        # e <textarea> para resposta longa
        wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'input[type="text"], textarea')
            )
        )
        campos = driver.find_elements(
            By.CSS_SELECTOR, 'input[type="text"], textarea'
        )

        if not campos:
            logger.error("LOG | Nenhum campo de texto encontrado no form.")
            return False

        logger.info("LOG | %d campo(s) encontrado(s) no form", len(campos))

        # Preenche cada campo na ordem (ignora campos extras)
        for campo, valor in zip(campos, valores):
            campo.clear()
            campo.send_keys(str(valor))

        # Localiza botão de envio (Google Forms: role="button" com texto "Enviar" ou "Submit")
        botoes = driver.find_elements(By.CSS_SELECTOR, 'div[role="button"]')
        botao_enviar = None
        for botao in botoes:
            texto = botao.text.strip().lower()
            if texto in ("enviar", "submit", "send"):
                botao_enviar = botao
                break

        if not botao_enviar:
            logger.error("LOG | Botão de envio não encontrado no form.")
            return False

        botao_enviar.click()
        logger.info("LOG | Formulário enviado — alteração registrada!")

        # Aguarda página de confirmação
        wait.until(
            EC.any_of(
                EC.url_contains("formResponse"),
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div.vHW8K')),
            )
        )
        return True

    except TimeoutException:
        logger.error("LOG | Timeout ao aguardar elementos do form.")
        return False
    except NoSuchElementException as exc:
        logger.error("LOG | Elemento não encontrado no form: %s", exc)
        return False
    except WebDriverException as exc:
        logger.error("LOG | Erro no WebDriver ao registrar no form: %s", exc)
        return False
    finally:
        # Volta para a aba de monitoramento
        try:
            driver.switch_to.window(aba_monitor)
        except WebDriverException:
            pass
