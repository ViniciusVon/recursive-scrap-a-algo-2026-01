"""
Utilitários gerais — WebDriver e validação de URL.
"""

import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# ---------------------------------------------------------------------------
# Utilitários de validação   O(1) por chamada
# ---------------------------------------------------------------------------

def validar_url(url: str) -> bool:
    """Valida se a URL informada possui formato válido. O(1)"""
    padrao = re.compile(
        r"^(https?://)"           # esquema obrigatório
        r"([a-zA-Z0-9\-\.]+)"    # domínio
        r"(\.[a-zA-Z]{2,})"      # TLD
        r"(:\d+)?(/.*)?$"        # porta e caminho opcionais
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

    driver = webdriver.Chrome(options=opcoes)
    return driver
