"""
Monitor de Preços via Selenium

"""

import logging
from selenium import webdriver
from selenium.common.exceptions import (
    WebDriverException
)
from utils import criar_driver, validar_url

# ---------------------------------------------------------------------------
# Configuração de logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def validar_nome_usuario(nome: str) -> bool:
    """
    Valida se o nome de usuário contém ao menos 3 caracteres e é composto
    apenas por letras (permite nomes compostos separados por espaço). O(n)
    """
    nome = nome.strip()
    if len(nome) < 3:
        return False
    # Remove espaços entre palavras e verifica se tudo são letras
    partes = nome.split()
    return all(parte.isalpha() for parte in partes)

# ---------------------------------------------------------------------------
# Funções de monitoramento
# ---------------------------------------------------------------------------

def monitorar_preco(
    driver: webdriver.Chrome,
    url: str,
) -> None:
    logger.info("Iniciando monitoramento | URL: %s", url)
    try:
        driver.get(url)
    except WebDriverException as exc:
        logger.error("Falha ao carregar URL '%s': %s", url, exc)

    logger.info("Monitoramento encerrado.")

# ---------------------------------------------------------------------------
# Entrada do usuário via console
# ---------------------------------------------------------------------------

def coletar_entradas() -> dict:
    """
    Solicita ao usuário todas as informações necessárias para o monitoramento.
    Valida cada entrada antes de prosseguir. O(1) por campo.
    """
    print("\n========================================")
    print("  Monitor de Preços via Selenium")
    print("========================================\n")

    # Nome do usuário
    while True:
        nome = input("Seu nome (mínimo 3 letras, apenas caracteres): ").strip()
        if validar_nome_usuario(nome):
            logger.info("LOG | Usuário identificado: '%s'", nome)
            break
        print("  Nome inválido. Use apenas letras, ao menos 3 caracteres.\n")

    # URL a monitorar
    while True:
        url = input("URL do site a monitorar (ex: https://site.com/produto): ").strip()
        if validar_url(url):
            logger.info("LOG | URL informada: %s", url)
            break
        print("  URL inválida. Certifique-se de incluir http:// ou https://\n")

    # Modo headless
    headless_str = input("Executar em modo headless? (s/n): ").strip().lower()
    headless = headless_str in ("s", "sim", "y", "yes")
    logger.info("LOG | Modo headless: %s", headless)

    return {
        "nome_usuario": nome,
        "url": url,
        "headless": headless,
    }

# ---------------------------------------------------------------------------
# Ponto de entrada principal
# ---------------------------------------------------------------------------

def main() -> None:
    parametros = coletar_entradas()

    driver = None
    try:
        driver = criar_driver(headless=parametros["headless"])
        monitorar_preco(
            driver=driver,
            url=parametros["url"],
        )
    except KeyboardInterrupt:
        logger.info("Monitoramento interrompido pelo usuário.")
    except WebDriverException as exc:
        logger.error("Erro crítico no WebDriver: %s", exc)
    finally:
        if driver:
            driver.quit()
            logger.info("WebDriver encerrado.")

if __name__ == "__main__":
    main()