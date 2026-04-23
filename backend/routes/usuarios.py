"""Rotas de usuários — reusa src/db.py."""

from fastapi import APIRouter, HTTPException

from backend.schemas import SessaoHistoricaOut, UsuarioIn, UsuarioOut
from src.db import (
    buscar_usuario_por_id,
    cadastrar_usuario,
    listar_sessoes_historicas,
    listar_usuarios,
)
from src.validators import validar_nome_usuario

router = APIRouter(prefix="/usuarios", tags=["usuarios"])


@router.get("", response_model=list[UsuarioOut])
def get_usuarios() -> list[UsuarioOut]:
    """Lista todos os usuários cadastrados. O(u)."""
    linhas = listar_usuarios()
    return [UsuarioOut(id=u[0], nome=u[1], email=u[2]) for u in linhas]


@router.post("", response_model=UsuarioOut, status_code=201)
def post_usuario(body: UsuarioIn) -> UsuarioOut:
    """Cadastra um novo usuário. O(log u)."""
    if not validar_nome_usuario(body.nome):
        raise HTTPException(
            status_code=400,
            detail="Nome inválido. Use apenas letras, mínimo 3 caracteres.",
        )
    novo_id = cadastrar_usuario(body.nome, body.email)
    return UsuarioOut(id=novo_id, nome=body.nome, email=body.email)


@router.get("/{usuario_id}", response_model=UsuarioOut)
def get_usuario(usuario_id: int) -> UsuarioOut:
    """Busca usuário por ID. O(log u)."""
    linha = buscar_usuario_por_id(usuario_id)
    if not linha:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    return UsuarioOut(id=linha[0], nome=linha[1], email=linha[2])


@router.get("/{usuario_id}/sessoes", response_model=list[SessaoHistoricaOut])
def get_sessoes_usuario(usuario_id: int) -> list[SessaoHistoricaOut]:
    """
    Lista as sessões encerradas do usuário, mais recentes primeiro.
    Usado pelo wizard para mostrar o "histórico" ao retornar usuário.
    """
    if not buscar_usuario_por_id(usuario_id):
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    rows = listar_sessoes_historicas(usuario_id)
    return [
        SessaoHistoricaOut(
            id=r[0],
            usuario_id=r[1],
            url=r[2],
            xpath_monitorado=r[3],
            valor_inicial=r[4],
            valor_final=r[5],
            total_alteracoes=r[6],
            iniciada_em=r[7],
            encerrada_em=r[8],
        )
        for r in rows
    ]
