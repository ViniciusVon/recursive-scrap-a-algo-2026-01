"""
Monitor de Preços via Selenium

"""

import logging
from selenium import webdriver
from selenium.common.exceptions import (
    WebDriverException
)
from src.utils import criar_driver, validar_url
from src.validators import validar_nome_usuario, validar_email
from src.db import inicializar_banco, cadastrar_usuario, listar_usuarios, buscar_usuario_por_id

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

def identificar_usuario() -> dict:
    """
    Solicita a identificação do usuário: cadastra um novo ou seleciona
    um existente no banco. O(n) onde n = quantidade de usuários cadastrados.
    """
    print("\n--- Identificação do Usuário ---\n")

    usuarios = listar_usuarios()

    if usuarios:
        print("Usuários cadastrados:")
        for uid, nome, email in usuarios:
            print(f"  [{uid}] {nome} ({email})")
        print()

        opcao = input("Digite o ID para entrar ou 'n' para novo cadastro: ").strip().lower()

        if opcao != "n":
            try:
                usuario = buscar_usuario_por_id(int(opcao))
                if usuario:
                    logger.info("LOG | Usuário identificado: '%s' (%s)", usuario[1], usuario[2])
                    return {"id": usuario[0], "nome": usuario[1], "email": usuario[2]}
            except ValueError:
                pass
            print("  ID inválido. Vamos cadastrar um novo usuário.\n")

    # Cadastro de novo usuário
    while True:
        nome = input("Seu nome (mínimo 3 letras, apenas caracteres): ").strip()
        if validar_nome_usuario(nome):
            break
        print("  Nome inválido. Use apenas letras, ao menos 3 caracteres.\n")

    while True:
        email = input("Seu e-mail: ").strip()
        if validar_email(email):
            break
        print("  E-mail inválido. Tente novamente.\n")

    usuario_id = cadastrar_usuario(nome, email)
    logger.info("LOG | Novo usuário cadastrado: '%s' (%s) [ID: %d]", nome, email, usuario_id)

    return {"id": usuario_id, "nome": nome, "email": email}


def coletar_entradas() -> dict:
    """
    Solicita ao usuário todas as informações necessárias para o monitoramento.
    Valida cada entrada antes de prosseguir. O(1) por campo.
    """
    print("\n========================================")
    print("  Monitor de Preços via Selenium")
    print("========================================\n")

    usuario = identificar_usuario()

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
        "usuario": usuario,
        "url": url,
        "headless": headless,
    }

# ---------------------------------------------------------------------------
# Ponto de entrada principal
# ---------------------------------------------------------------------------

def main() -> None:
    inicializar_banco()
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
