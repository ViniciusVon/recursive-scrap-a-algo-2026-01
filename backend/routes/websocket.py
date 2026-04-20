"""
WebSocket endpoint para streaming de eventos da sessão.

Eventos emitidos pelo backend (JSON):
    - {"type": "inicial", ...}     -> snapshot ao conectar
    - {"type": "ciclo", ...}       -> a cada ciclo de monitoramento (~15s)
    - {"type": "alteracao", ...}   -> quando o valor mudou
    - {"type": "screenshot", ...}  -> a cada 2s, base64 PNG
    - {"type": "encerrada"}        -> sessão foi encerrada via DELETE
"""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.services.session_manager import manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


def _snapshot_inicial(estado) -> dict:
    """Serializa o estado atual para enviar assim que o cliente conecta."""
    return {
        "type": "inicial",
        "sessao": {
            "id": estado.id,
            "usuario_id": estado.usuario_id,
            "url": estado.url,
            "headless": estado.headless,
            "status": estado.status,
            "xpath_monitorado": estado.xpath_monitorado,
            "valor_atual": estado.valor_atual,
            "ciclo": estado.ciclo,
        },
        "historico": [
            {
                "ciclo": r.ciclo,
                "timestamp": r.timestamp.isoformat(),
                "valor_antigo": r.valor_antigo,
                "valor_novo": r.valor_novo,
            }
            for r in estado.historico
        ],
    }


async def _send_json_safe(ws: WebSocket, payload: dict) -> bool:
    """
    Envia JSON tratando desconexões abruptas como "perdeu cliente"
    silenciosamente — sem gerar stack trace no log. Retorna False se a
    conexão caiu.
    """
    try:
        await ws.send_json(payload)
        return True
    except WebSocketDisconnect:
        return False
    except Exception as exc:  # noqa: BLE001
        # Cliente pode fechar o socket a qualquer momento (ex.: o
        # double-effect do React StrictMode em dev reabre a conexão).
        # Logamos em nível debug pra não poluir o terminal.
        logger.debug("WebSocket envio falhou: %s", exc)
        return False


@router.websocket("/ws/sessoes/{session_id}")
async def ws_sessao(ws: WebSocket, session_id: str) -> None:
    """
    Conexão WebSocket para uma sessão. Envia um snapshot inicial e depois
    retransmite cada evento emitido pelo monitor enquanto o cliente estiver
    conectado.

    Complexidade por mensagem: O(1) para leitura da fila + O(tamanho-do-
    evento) para serialização JSON. Screenshots dominam (base64 PNG ~50KB).
    """
    await ws.accept()

    estado = manager.obter(session_id)
    if not estado:
        await _send_json_safe(
            ws, {"type": "erro", "mensagem": "Sessão não encontrada."}
        )
        await ws.close(code=4404)
        return

    # Enviamos o snapshot inicial; se o cliente sumiu nesse meio tempo
    # (caso clássico do double-effect do StrictMode), apenas saímos.
    if not await _send_json_safe(ws, _snapshot_inicial(estado)):
        return

    q = manager.subscribe(session_id)
    if q is None:
        await ws.close(code=4404)
        return

    try:
        while True:
            try:
                evento = await asyncio.wait_for(
                    asyncio.to_thread(q.get, True, 5), timeout=30
                )
            except (asyncio.TimeoutError, Exception):
                # Ping de keepalive caso a fila esteja vazia por muito tempo
                if not await _send_json_safe(ws, {"type": "ping"}):
                    break
                continue

            if not await _send_json_safe(ws, evento):
                break

            if evento.get("type") == "encerrada":
                break
    except WebSocketDisconnect:
        pass
    finally:
        manager.unsubscribe(session_id, q)
