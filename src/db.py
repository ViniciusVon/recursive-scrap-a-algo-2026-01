"""
Módulo de persistência — SQLite para cadastro de usuários.
"""

from __future__ import annotations

import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "dados.db")


def inicializar_banco() -> None:
    """Cria a tabela de usuários caso não exista. O(1)"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS usuarios (
                id    INTEGER PRIMARY KEY AUTOINCREMENT,
                nome  TEXT NOT NULL,
                email TEXT NOT NULL
            )
            """
        )
        conn.commit()


def cadastrar_usuario(nome: str, email: str) -> int:
    """Insere um novo usuário e retorna o id gerado. O(1)"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            "INSERT INTO usuarios (nome, email) VALUES (?, ?)",
            (nome, email),
        )
        conn.commit()
        return cursor.lastrowid


def listar_usuarios() -> list[tuple[int, str, str]]:
    """Retorna todos os usuários cadastrados (id, nome, email). O(n)"""
    with sqlite3.connect(DB_PATH) as conn:
        return conn.execute("SELECT id, nome, email FROM usuarios").fetchall()


def buscar_usuario_por_id(usuario_id: int) -> tuple[int, str, str] | None:
    """Busca um usuário pelo id. O(1)"""
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT id, nome, email FROM usuarios WHERE id = ?",
            (usuario_id,),
        ).fetchone()
        return row
