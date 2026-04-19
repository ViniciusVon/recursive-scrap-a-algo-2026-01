"""Rotas de sessões de monitoramento."""

from fastapi import APIRouter, HTTPException

from backend.schemas import (
    RegistroHistorico,
    SelecaoIn,
    SessaoIn,
    SessaoOut,
    ValorEncontrado,
)
from backend.services.session_manager import manager
from src.db import buscar_usuario_por_id
from src.utils import validar_url
from src.value_selector import listar_valores_com_xpath

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
    ok = manager.encerrar(session_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Sessão não encontrada.")
