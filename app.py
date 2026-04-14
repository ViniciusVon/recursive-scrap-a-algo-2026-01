"""
Monitor de Preços via Selenium

"""

import time
import logging
from selenium import webdriver
from selenium.common.exceptions import (
    WebDriverException
)
from src.utils import criar_driver, validar_url
from src.validators import validar_nome_usuario, validar_email
from src.db import inicializar_banco, cadastrar_usuario, listar_usuarios, buscar_usuario_por_id
from src.search_numbers import encontrar_numeros
from src.notifier import enviar_email, montar_corpo_alteracao, carregar_senha_app

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

INTERVALO_SEGUNDOS = 15


def extrair_valores(driver: webdriver.Chrome) -> dict:
    """Extrai todos os valores numéricos da página atual do driver. O(n)"""
    texto = driver.find_element("tag name", "body").text
    numeros = encontrar_numeros(texto)
    return {"numeros": numeros}


def monitorar_preco(
    driver: webdriver.Chrome,
    url: str,
    usuario: dict,
    senha_app: str,
) -> None:
    """
    Loop de monitoramento: a cada 15s extrai valores da página,
    compara com a leitura anterior e notifica por e-mail se houver mudança.
    O(n) por ciclo, onde n = tamanho do texto da página.
    """
    logger.info("Iniciando monitoramento | URL: %s | Intervalo: %ds", url, INTERVALO_SEGUNDOS)

    try:
        driver.get(url)
    except WebDriverException as exc:
        logger.error("Falha ao carregar URL '%s': %s", url, exc)
        return

    valores_anteriores = extrair_valores(driver)
    logger.info("LOG | Leitura inicial: %d valores numéricos encontrados", len(valores_anteriores["numeros"]))
    ciclo = 0

    while True:
        time.sleep(INTERVALO_SEGUNDOS)
        ciclo += 1

        try:
            driver.refresh()
            valores_atuais = extrair_valores(driver)
        except WebDriverException as exc:
            logger.error("Falha ao atualizar página (ciclo %d): %s", ciclo, exc)
            continue

        if valores_atuais["numeros"] != valores_anteriores["numeros"]:
            logger.info("LOG | ALTERAÇÃO DETECTADA no ciclo %d!", ciclo)
            logger.info("LOG | Antes: %s", valores_anteriores["numeros"][:10])
            logger.info("LOG | Depois: %s", valores_atuais["numeros"][:10])

            corpo = montar_corpo_alteracao(url, valores_anteriores, valores_atuais)
            enviar_email(
                destinatario=usuario["email"],
                senha_app=senha_app,
                assunto=f"Alteração detectada — {url}",
                corpo=corpo,
            )
            valores_anteriores = valores_atuais
        else:
            logger.info("LOG | Ciclo %d — sem alterações (%d valores)", ciclo, len(valores_atuais["numeros"]))

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

    # Senha de app do Gmail (carregada do .env)
    senha_app = carregar_senha_app()
    if senha_app:
        logger.info("LOG | Senha de app do Gmail carregada do .env")
    else:
        logger.warning("LOG | Senha de app não encontrada no .env — notificações por e-mail desabilitadas")

    # Modo headless
    headless_str = input("Executar em modo headless? (s/n): ").strip().lower()
    headless = headless_str in ("s", "sim", "y", "yes")
    logger.info("LOG | Modo headless: %s", headless)

    return {
        "usuario": usuario,
        "url": url,
        "senha_app": senha_app,
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
            usuario=parametros["usuario"],
            senha_app=parametros["senha_app"],
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
