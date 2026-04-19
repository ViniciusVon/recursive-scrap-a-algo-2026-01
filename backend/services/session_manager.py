"""
Gerenciador de sessões de monitoramento.

Mantém em memória um registry { session_id → SessionState }. Cada sessão
carrega seu próprio WebDriver, o XPath selecionado, o valor atual e um
histórico de alterações. Cada sessão também roda uma thread daemon que
refresca a página a cada INTERVALO_SEGUNDOS e detecta mudanças.

Complexidade:
    - Criação de sessão: O(1) para o dict + custo I/O do driver.get.
    - Leitura de sessão: O(1) (lookup em dict).
    - Loop de monitoramento (por ciclo): O(d) — leitura por XPath absoluto.

Observação: por ser in-memory, reiniciar o servidor derruba as sessões.
A persistência de sessões fica para a Fase 4 (se fizer sentido).
"""

from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from selenium.common.exceptions import WebDriverException

from src.constants import INTERVALO_SEGUNDOS
from src.utils import criar_driver
from src.value_selector import ler_valor_por_xpath


@dataclass
class RegistroAlteracao:
    ciclo: int
    timestamp: datetime
    valor_antigo: str
    valor_novo: str


@dataclass
class SessionState:
    id: str
    usuario_id: int
    url: str
    headless: bool
    driver: any = None  # webdriver.Chrome
    status: str = "iniciada"
    xpath_monitorado: Optional[str] = None
    valor_atual: Optional[str] = None
    valores_encontrados: List[dict] = field(default_factory=list)
    historico: List[RegistroAlteracao] = field(default_factory=list)
    ciclo: int = 0
    thread: Optional[threading.Thread] = None
    _parar: threading.Event = field(default_factory=threading.Event)


class SessionManager:
    """Registry in-memory de sessões. Thread-safe por lock simples."""

    def __init__(self) -> None:
        self._sessoes: Dict[str, SessionState] = {}
        self._lock = threading.Lock()

    # -- CRUD básico ---------------------------------------------------------

    def criar(self, usuario_id: int, url: str, headless: bool) -> SessionState:
        """Cria sessão, inicia driver e carrega a URL. O(1) + I/O."""
        session_id = uuid.uuid4().hex[:12]
        driver = criar_driver(headless=headless)
        driver.get(url)

        estado = SessionState(
            id=session_id,
            usuario_id=usuario_id,
            url=url,
            headless=headless,
            driver=driver,
            status="iniciada",
        )
        with self._lock:
            self._sessoes[session_id] = estado
        return estado

    def obter(self, session_id: str) -> Optional[SessionState]:
        """Lookup O(1)."""
        with self._lock:
            return self._sessoes.get(session_id)

    def listar(self) -> List[SessionState]:
        with self._lock:
            return list(self._sessoes.values())

    def encerrar(self, session_id: str) -> bool:
        """Para a thread e encerra o driver. Remove do registry."""
        with self._lock:
            estado = self._sessoes.pop(session_id, None)
        if not estado:
            return False
        estado._parar.set()
        if estado.thread and estado.thread.is_alive():
            estado.thread.join(timeout=2)
        try:
            estado.driver.quit()
        except WebDriverException:
            pass
        estado.status = "encerrada"
        return True

    # -- Monitoramento -------------------------------------------------------

    def iniciar_monitoramento(self, session_id: str, xpath: str, valor_inicial: str) -> bool:
        """
        Grava o XPath selecionado e dispara a thread de polling.
        Retorna False se a sessão não existe ou já está monitorando.
        """
        estado = self.obter(session_id)
        if not estado or estado.status == "monitorando":
            return False

        estado.xpath_monitorado = xpath
        estado.valor_atual = valor_inicial
        estado.status = "monitorando"

        thread = threading.Thread(
            target=self._loop_monitor,
            args=(estado,),
            daemon=True,
            name=f"monitor-{session_id}",
        )
        estado.thread = thread
        thread.start()
        return True

    def _loop_monitor(self, estado: SessionState) -> None:
        """Loop de polling. Roda em thread daemon até _parar ser sinalizado."""
        while not estado._parar.is_set():
            if estado._parar.wait(INTERVALO_SEGUNDOS):
                break

            estado.ciclo += 1
            try:
                estado.driver.refresh()
                valor_novo = ler_valor_por_xpath(estado.driver, estado.xpath_monitorado)
            except WebDriverException:
                continue

            if not valor_novo:
                continue

            if valor_novo != estado.valor_atual:
                estado.historico.append(
                    RegistroAlteracao(
                        ciclo=estado.ciclo,
                        timestamp=datetime.now(),
                        valor_antigo=estado.valor_atual or "",
                        valor_novo=valor_novo,
                    )
                )
                estado.valor_atual = valor_novo


# Instância global (singleton de módulo) usada pelas rotas
manager = SessionManager()
