"""
Utilitários gerais — WebDriver e validação de URL.
"""

import os
import re

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# ---------------------------------------------------------------------------
# Utilitários de validação   O(1) por chamada
# ---------------------------------------------------------------------------

def validar_url(url: str) -> bool:
    """Valida se a URL informada possui formato válido.

    Complexidade: O(L) onde L = len(url). Na prática, L é limitado
    (URLs raramente passam de ~2000 chars), então é tratado como O(1).
    """
    padrao = re.compile(
        r"^(https?://)"                                 # esquema obrigatório (http ou https)
        r"(localhost|([a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}))" # domínio: aceita 'localhost' OU 'dominio.tld'
        r"(:\d+)?(/.*)?$"                               # porta e caminho opcionais
    )
    return bool(padrao.match(url.strip()))

# ---------------------------------------------------------------------------
# Configuração do WebDriver   O(1)
# ---------------------------------------------------------------------------

def criar_driver(headless: bool = False) -> webdriver.Chrome:
    """Instancia o ChromeDriver com opções básicas. O(1)"""
    opcoes = Options()
    if headless:
        opcoes.add_argument("--headless")
    opcoes.add_argument("--disable-gpu")
    opcoes.add_argument("--no-sandbox")
    opcoes.add_argument("--disable-dev-shm-usage")
    opcoes.add_argument("--window-size=1920,1080")
    # Evita que o Chrome "pause" a aba quando a janela fica atrás de
    # outras no macOS/Windows — sem isso os screenshots CDP podem sair
    # congelados quando o usuário sai do foco da janela.
    opcoes.add_argument(
        "--disable-features=CalculateNativeWinOcclusion"
    )
    # Inicia minimizado para não roubar foco no instante em que abre.
    # O usuário pode trazer pra frente manualmente se quiser.
    if not headless:
        opcoes.add_argument("--window-position=0,0")

    # Em containers ARM64 (Docker Desktop no Apple Silicon), o Selenium
    # Manager não tem binário compatível e falha com
    # "Unsupported platform/architecture combination: linux/aarch64".
    # As variáveis `CHROME_BIN` / `CHROMEDRIVER_BIN` são setadas no
    # Dockerfile.backend e apontam para os binários instalados via apt;
    # passamos explicitamente pra pular a descoberta automática.
    # Fora do container, ambas ficam ausentes e caímos no fluxo normal
    # do Selenium Manager (que já funciona em macOS/Windows/x86_64).
    chrome_bin = os.environ.get("CHROME_BIN")
    driver_bin = os.environ.get("CHROMEDRIVER_BIN")
    if chrome_bin:
        opcoes.binary_location = chrome_bin
    service = Service(executable_path=driver_bin) if driver_bin else None

    driver = webdriver.Chrome(options=opcoes, service=service)
    return driver
