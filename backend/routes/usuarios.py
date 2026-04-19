"""Rotas de usuários — reusa src/db.py."""

from fastapi import APIRouter, HTTPException

from backend.schemas import UsuarioIn, UsuarioOut
from src.db import (
    buscar_usuario_por_id,
    cadastrar_usuario,
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
