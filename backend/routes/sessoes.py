"""Rotas de sessões de monitoramento."""

from fastapi import APIRouter, HTTPException
from selenium.common.exceptions import WebDriverException

from backend.schemas import (
    RegistroHistorico,
    SelecaoIn,
    SessaoIn,
    SessaoOut,
    ValorEncontrado,
)
from backend.services.session_manager import manager
from src.db import buscar_usuario_por_id
from src.notifier import carregar_senha_app, enviar_email, montar_resumo_sessao
from src.utils import validar_url
from src.value_selector import listar_valores_com_xpath

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sessoes", tags=["sessoes"])


def _to_out(estado) -> SessaoOut:
    return SessaoOut(
        id=estado.id,
        usuario_id=estado.usuario_id,
        url=estado.url,
        headless=estado.headless,
        status=estado.status,
        xpath_monitorado=estado.xpath_monitorado,
        valor_atual=estado.valor_atual,
    )


@router.post("", response_model=SessaoOut, status_code=201)
def post_sessao(body: SessaoIn) -> SessaoOut:
    """Cria uma nova sessão, abre o driver e carrega a URL."""
    if not buscar_usuario_por_id(body.usuario_id):
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    if not validar_url(body.url):
        raise HTTPException(status_code=400, detail="URL inválida.")

    estado = manager.criar(
        usuario_id=body.usuario_id,
        url=body.url,
        headless=body.headless,
    )
    return _to_out(estado)


@router.get("/{session_id}", response_model=SessaoOut)
def get_sessao(session_id: str) -> SessaoOut:
    estado = manager.obter(session_id)
    if not estado:
        raise HTTPException(status_code=404, detail="Sessão não encontrada.")
    return _to_out(estado)


@router.get("/{session_id}/valores", response_model=list[ValorEncontrado])
def get_valores(session_id: str) -> list[ValorEncontrado]:
    """
    Executa o list_values.js na página da sessão e retorna os valores
    numéricos encontrados com seus XPaths. O(n · d).
    """
    estado = manager.obter(session_id)
    if not estado:
        raise HTTPException(status_code=404, detail="Sessão não encontrada.")

    valores = listar_valores_com_xpath(estado.driver)
    estado.valores_encontrados = valores
    return [
        ValorEncontrado(indice=i, text=v["text"], xpath=v["xpath"])
        for i, v in enumerate(valores)
    ]


@router.get("/{session_id}/screenshot")
def get_screenshot(session_id: str) -> dict:
    """
    Retorna um screenshot único da página atual, em base64 PNG.

    Usado pelo wizard de setup para o usuário ter uma prévia visual da
    URL antes de escolher qual valor monitorar. Capturamos via CDP
    (`Page.captureScreenshot`) para não trazer a janela do Chrome ao
    primeiro plano.
    """
    estado = manager.obter(session_id)
    if not estado:
        raise HTTPException(status_code=404, detail="Sessão não encontrada.")
    try:
        resultado = estado.driver.execute_cdp_cmd(
            "Page.captureScreenshot",
            {"format": "png", "captureBeyondViewport": False},
        )
    except WebDriverException as e:
        raise HTTPException(
            status_code=502, detail=f"Falha ao capturar screenshot: {e}"
        ) from e
    return {"data": resultado["data"]}


@router.post("/{session_id}/selecionar", response_model=SessaoOut)
def post_selecionar(session_id: str, body: SelecaoIn) -> SessaoOut:
    """Grava o XPath escolhido e inicia a thread de monitoramento."""
    estado = manager.obter(session_id)
    if not estado:
        raise HTTPException(status_code=404, detail="Sessão não encontrada.")

    ok = manager.iniciar_monitoramento(session_id, body.xpath, body.text)
    if not ok:
        raise HTTPException(
            status_code=409,
            detail="Sessão já está em monitoramento ou inválida.",
        )
    return _to_out(estado)


@router.get("/{session_id}/historico", response_model=list[RegistroHistorico])
def get_historico(session_id: str) -> list[RegistroHistorico]:
    estado = manager.obter(session_id)
    if not estado:
        raise HTTPException(status_code=404, detail="Sessão não encontrada.")
    return [
        RegistroHistorico(
            ciclo=r.ciclo,
            timestamp=r.timestamp,
            valor_antigo=r.valor_antigo,
            valor_novo=r.valor_novo,
        )
        for r in estado.historico
    ]


@router.delete("/{session_id}", status_code=204)
def delete_sessao(session_id: str) -> None:
    """
    Encerra a sessão e dispara um e-mail com o resumo (histórico de
    alterações) para o usuário dono da sessão. Se o e-mail falhar, a
    sessão ainda é encerrada — o envio é best-effort.
    """
    estado = manager.obter(session_id)
    if not estado:
        raise HTTPException(status_code=404, detail="Sessão não encontrada.")

    # Snapshot antes do encerramento: o manager limpa o driver e os
    # recursos, mas os dados que vamos enviar por e-mail ficam aqui.
    url = estado.url
    valor_final = estado.valor_atual
    historico = list(estado.historico)
    usuario_row = buscar_usuario_por_id(estado.usuario_id)

    ok = manager.encerrar(session_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Sessão não encontrada.")

    # Best-effort: falha de e-mail não deve derrubar o endpoint.
    try:
        if usuario_row:
            _, _, email = usuario_row
            senha = carregar_senha_app()
            if senha:
                assunto, corpo = montar_resumo_sessao(url, valor_final, historico)
                enviar_email(email, senha, assunto, corpo)
            else:
                logger.warning(
                    "GMAIL_APP_PASSWORD não configurada; "
                    "pulando envio de resumo para %s",
                    email,
                )
    except Exception:  # noqa: BLE001
        logger.exception("Falha ao enviar e-mail de resumo da sessão %s", session_id)
