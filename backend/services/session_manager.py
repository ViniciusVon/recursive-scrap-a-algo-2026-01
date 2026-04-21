"""
Gerenciador de sessões de monitoramento.

Mantém em memória um registry { session_id → SessionState }. Cada sessão
carrega seu próprio WebDriver, o XPath selecionado, o valor atual e um
histórico de alterações. A thread daemon do monitor:
    - A cada 2s captura um screenshot e emite para todos os subscribers.
    - A cada INTERVALO_SEGUNDOS (15s) refresca a página, relê o valor
      pelo XPath e emite `ciclo` (e `alteracao` se o valor mudou).

Os subscribers são filas `queue.Queue` por conexão WebSocket. Isso
permite múltiplas abas espiarem a mesma sessão sem disputa.

Complexidade:
    - Criação de sessão: O(1) para o dict + I/O do driver.get.
    - Leitura de sessão: O(1) (lookup em dict).
    - Loop de monitoramento (por tick de 2s): O(d) para ler XPath +
      tamanho do screenshot (custo de I/O do Selenium).
"""

from __future__ import annotations

import queue
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from selenium.common.exceptions import WebDriverException

from src.constants import INTERVALO_SEGUNDOS
from src.utils import criar_driver
from src.value_selector import ler_valor_por_xpath


# Intervalo curto entre screenshots (segundos)
INTERVALO_SCREENSHOT = 2


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
    driver: Any = None  # webdriver.Chrome
    status: str = "iniciada"
    xpath_monitorado: Optional[str] = None
    valor_atual: Optional[str] = None
    valor_inicial: Optional[str] = None
    iniciada_em: datetime = field(default_factory=datetime.now)
    valores_encontrados: List[dict] = field(default_factory=list)
    historico: List[RegistroAlteracao] = field(default_factory=list)
    ciclo: int = 0
    thread: Optional[threading.Thread] = None
    _parar: threading.Event = field(default_factory=threading.Event)
    _subscribers: List["queue.Queue[dict]"] = field(default_factory=list)
    _sub_lock: threading.Lock = field(default_factory=threading.Lock)


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
        # Avisa subscribers para fecharem suas conexões
        self._emit(estado, {"type": "encerrada"})
        return True

    # -- Monitoramento -------------------------------------------------------

    def iniciar_monitoramento(
        self, session_id: str, xpath: str, valor_inicial: str
    ) -> bool:
        """
        Grava o XPath selecionado e dispara a thread daemon do monitor.
        Retorna False se a sessão não existe ou já está monitorando.
        """
        estado = self.obter(session_id)
        if not estado or estado.status == "monitorando":
            return False

        estado.xpath_monitorado = xpath
        estado.valor_atual = valor_inicial
        estado.valor_inicial = valor_inicial
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
        """
        Loop da thread daemon. A cada INTERVALO_SCREENSHOT segundos tira
        screenshot e emite. A cada N ticks (N = INTERVALO_SEGUNDOS //
        INTERVALO_SCREENSHOT) também refresca a página e checa o valor.
        """
        ticks = 0
        ciclos_por_check = max(1, INTERVALO_SEGUNDOS // INTERVALO_SCREENSHOT)

        while not estado._parar.is_set():
            if estado._parar.wait(INTERVALO_SCREENSHOT):
                break
            ticks += 1

            # Monitoramento propriamente dito (a cada ~15s)
            if ticks % ciclos_por_check == 0:
                estado.ciclo += 1
                try:
                    estado.driver.refresh()
                    valor_novo = ler_valor_por_xpath(
                        estado.driver, estado.xpath_monitorado
                    )
                except WebDriverException:
                    valor_novo = None

                if valor_novo and valor_novo != estado.valor_atual:
                    registro = RegistroAlteracao(
                        ciclo=estado.ciclo,
                        timestamp=datetime.now(),
                        valor_antigo=estado.valor_atual or "",
                        valor_novo=valor_novo,
                    )
                    estado.historico.append(registro)
                    estado.valor_atual = valor_novo
                    self._emit(
                        estado,
                        {
                            "type": "alteracao",
                            "registro": {
                                "ciclo": registro.ciclo,
                                "timestamp": registro.timestamp.isoformat(),
                                "valor_antigo": registro.valor_antigo,
                                "valor_novo": registro.valor_novo,
                            },
                        },
                    )

                self._emit(
                    estado,
                    {
                        "type": "ciclo",
                        "ciclo": estado.ciclo,
                        "valor_atual": estado.valor_atual,
                        "timestamp": datetime.now().isoformat(),
                    },
                )

            # Screenshot em todo tick (2s).
            #
            # Usamos CDP `Page.captureScreenshot` em vez de
            # `get_screenshot_as_base64()`: o CDP captura diretamente do
            # compositor do Chrome, o que significa que NÃO precisa da
            # janela em primeiro plano. Isso evita o "roubo de foco" a
            # cada 2s quando o usuário escolhe headless=False — a janela
            # pode ficar atrás de outras sem problema.
            try:
                resultado = estado.driver.execute_cdp_cmd(
                    "Page.captureScreenshot",
                    {"format": "png", "captureBeyondViewport": False},
                )
                self._emit(
                    estado, {"type": "screenshot", "data": resultado["data"]}
                )
            except WebDriverException:
                pass

    # -- Pub/Sub -------------------------------------------------------------

    def subscribe(self, session_id: str) -> Optional["queue.Queue[dict]"]:
        """
        Cria uma fila nova e a registra como subscriber da sessão.
        Retorna None se a sessão não existe.
        """
        estado = self.obter(session_id)
        if not estado:
            return None
        q: "queue.Queue[dict]" = queue.Queue(maxsize=200)
        with estado._sub_lock:
            estado._subscribers.append(q)
        return q

    def unsubscribe(self, session_id: str, q: "queue.Queue[dict]") -> None:
        estado = self.obter(session_id)
        if not estado:
            return
        with estado._sub_lock:
            try:
                estado._subscribers.remove(q)
            except ValueError:
                pass

    def _emit(self, estado: SessionState, event: dict) -> None:
        """Broadcast não-bloqueante para todos os subscribers."""
        with estado._sub_lock:
            mortos: List["queue.Queue[dict]"] = []
            for q in estado._subscribers:
                try:
                    q.put_nowait(event)
                except queue.Full:
                    # Subscriber lento — descarta o evento em vez de travar
                    mortos.append(q)
            for q in mortos:
                try:
                    estado._subscribers.remove(q)
                except ValueError:
                    pass


# Instância global (singleton de módulo) usada pelas rotas
manager = SessionManager()
