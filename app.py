"""
Monitor de Preços via Selenium

"""

import time
import logging
from datetime import datetime
from selenium import webdriver
from selenium.common.exceptions import (
    WebDriverException
)
from src.utils import criar_driver, validar_url
from src.validators import validar_nome_usuario, validar_email
from src.db import inicializar_banco, cadastrar_usuario, listar_usuarios, buscar_usuario_por_id
from src.notifier import enviar_email, carregar_senha_app
from src.form_recorder import abrir_aba_form, registrar_alteracao
from src.value_selector import selecionar_valor, ler_valor_por_xpath
from src.constants import FORM_URL, INTERVALO_SEGUNDOS

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
    usuario: dict,
) -> list:
    """
    Loop de monitoramento do valor selecionado pelo usuário.

    1. Carrega a página e pede ao usuário que selecione o valor a monitorar.
    2. Abre segunda aba com o Google Form de registro.
    3. A cada INTERVALO_SEGUNDOS refresca a página e lê o valor pelo XPath.
    4. Se mudou → registra no Google Form e loga no console.
    5. Retorna o histórico de alterações ao encerrar (Ctrl+C).

    O(1) por ciclo (leitura de um único elemento pelo XPath).
    """
    logger.info("Iniciando monitoramento | URL: %s | Intervalo: %ds", url, INTERVALO_SEGUNDOS)

    try:
        driver.get(url)
    except WebDriverException as exc:
        logger.error("Falha ao carregar URL '%s': %s", url, exc)
        return []

    # Usuário escolhe qual valor monitorar
    selecionado = selecionar_valor(driver)
    if not selecionado:
        logger.error("Nenhum valor selecionado. Encerrando.")
        return []

    xpath_monitorado = selecionado["xpath"]
    valor_anterior = selecionado["text"]
    logger.info("LOG | Valor inicial: '%s'", valor_anterior)
    logger.info("LOG | XPath monitorado: %s", xpath_monitorado)

    # Segunda aba para registro
    aba_monitor = driver.current_window_handle
    aba_form = abrir_aba_form(driver, FORM_URL)

    ciclo = 0
    historico = []

    try:
        while True:
            time.sleep(INTERVALO_SEGUNDOS)
            ciclo += 1

            try:
                driver.switch_to.window(aba_monitor)
                driver.refresh()
                valor_atual = ler_valor_por_xpath(driver, xpath_monitorado)
            except WebDriverException as exc:
                logger.error("Falha ao atualizar página (ciclo %d): %s", ciclo, exc)
                continue

            if not valor_atual:
                logger.warning("LOG | Ciclo %d — valor não encontrado no XPath", ciclo)
                continue

            if valor_atual != valor_anterior:
                logger.info("LOG | ALTERAÇÃO DETECTADA no ciclo %d!", ciclo)
                logger.info("LOG | Antes: '%s'", valor_anterior)
                logger.info("LOG | Depois: '%s'", valor_atual)

                timestamp = datetime.now().isoformat(timespec="seconds")
                registro = {
                    "url": url,
                    "valor_antigo": valor_anterior,
                    "valor_novo": valor_atual,
                    "timestamp": timestamp,
                    "usuario": usuario.get("nome", ""),
                }
                historico.append(registro)

                # Registra na segunda aba (Google Form)
                registrar_alteracao(
                    driver=driver,
                    aba_monitor=aba_monitor,
                    aba_form=aba_form,
                    form_url=FORM_URL,
                    dados=registro,
                )

                valor_anterior = valor_atual
            else:
                logger.info("LOG | Ciclo %d — sem alteração ('%s')", ciclo, valor_atual)
    except KeyboardInterrupt:
        logger.info(
            "LOG | Monitoramento interrompido pelo usuário. %d alteração(ões) registrada(s).",
            len(historico),
        )

    return historico

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
    historico = []
    try:
        driver = criar_driver(headless=parametros["headless"])
        historico = monitorar_preco(
            driver=driver,
            url=parametros["url"],
            usuario=parametros["usuario"],
        )
    except WebDriverException as exc:
        logger.error("Erro crítico no WebDriver: %s", exc)
    finally:
        if driver:
            driver.quit()
            logger.info("WebDriver encerrado.")

    # Envio de e-mail de resumo (extra) — apenas se houver alterações e senha configurada
    if historico and parametros["senha_app"]:
        usuario = parametros["usuario"]
        corpo_linhas = [
            f"Resumo do monitoramento — {len(historico)} alteração(ões) detectada(s).",
            f"URL monitorada: {parametros['url']}",
            "",
        ]
        for i, reg in enumerate(historico, 1):
            corpo_linhas.append(f"[{i}] {reg['timestamp']}")
            corpo_linhas.append(f"    Antes: {reg['valor_antigo']}")
            corpo_linhas.append(f"    Depois: {reg['valor_novo']}")
            corpo_linhas.append("")

        enviar_email(
            destinatario=usuario["email"],
            senha_app=parametros["senha_app"],
            assunto=f"Resumo do monitoramento — {parametros['url']}",
            corpo="\n".join(corpo_linhas),
        )

if __name__ == "__main__":
    main()
