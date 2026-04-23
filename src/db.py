"""
Módulo de persistência — SQLite para cadastro de usuários.
"""

from __future__ import annotations

import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "dados.db")


def inicializar_banco() -> None:
    """Cria as tabelas do app caso não existam. O(1)"""
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
        # Histórico de sessões encerradas. Populada pelo DELETE
        # /sessoes/{id}. Guarda o resumo da sessão para o usuário
        # consultar depois, mesmo com o backend reiniciado.
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sessoes_historicas (
                id                TEXT PRIMARY KEY,
                usuario_id        INTEGER NOT NULL,
                url               TEXT NOT NULL,
                xpath_monitorado  TEXT,
                valor_inicial     TEXT,
                valor_final       TEXT,
                total_alteracoes  INTEGER NOT NULL DEFAULT 0,
                iniciada_em       TEXT NOT NULL,
                encerrada_em      TEXT NOT NULL,
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
            )
            """
        )
        # Alterações detectadas durante uma sessão histórica. Chaveada
        # pelo id da sessão (não pelo próprio ciclo) para suportar
        # múltiplas sessões com mesmo ciclo.
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS alteracoes_historicas (
                sessao_id     TEXT NOT NULL,
                ciclo         INTEGER NOT NULL,
                timestamp     TEXT NOT NULL,
                valor_antigo  TEXT NOT NULL,
                valor_novo    TEXT NOT NULL,
                PRIMARY KEY (sessao_id, ciclo),
                FOREIGN KEY (sessao_id) REFERENCES sessoes_historicas(id)
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_sessoes_historicas_usuario "
            "ON sessoes_historicas(usuario_id, encerrada_em DESC)"
        )
        conn.commit()


def cadastrar_usuario(nome: str, email: str) -> int:
    """Insere um novo usuário e retorna o id gerado.

    Complexidade: O(log n) — INSERT no B-tree do SQLite com n linhas.
    """
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
    """Busca um usuário pelo id.

    Complexidade: O(log n) — lookup por chave primária no B-tree do SQLite.
    """
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT id, nome, email FROM usuarios WHERE id = ?",
            (usuario_id,),
        ).fetchone()
        return row


# ---------------------------------------------------------------------------
# Histórico de sessões
# ---------------------------------------------------------------------------


def gravar_sessao_historica(
    sessao_id: str,
    usuario_id: int,
    url: str,
    xpath_monitorado: str | None,
    valor_inicial: str | None,
    valor_final: str | None,
    iniciada_em: str,
    encerrada_em: str,
    alteracoes: list,
) -> None:
    """
    Persiste uma sessão encerrada + suas alterações em uma única
    transação. `alteracoes` é uma lista de objetos com `.ciclo`,
    `.timestamp` (datetime), `.valor_antigo`, `.valor_novo`.

    Complexidade: O(k) onde k é o número de alterações.
    """
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO sessoes_historicas (
                id, usuario_id, url, xpath_monitorado,
                valor_inicial, valor_final, total_alteracoes,
                iniciada_em, encerrada_em
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                sessao_id,
                usuario_id,
                url,
                xpath_monitorado,
                valor_inicial,
                valor_final,
                len(alteracoes),
                iniciada_em,
                encerrada_em,
            ),
        )
        # Limpa alterações antigas dessa sessão (caso de re-gravação)
        conn.execute(
            "DELETE FROM alteracoes_historicas WHERE sessao_id = ?",
            (sessao_id,),
        )
        conn.executemany(
            """
            INSERT INTO alteracoes_historicas (
                sessao_id, ciclo, timestamp, valor_antigo, valor_novo
            ) VALUES (?, ?, ?, ?, ?)
            """,
            [
                (
                    sessao_id,
                    r.ciclo,
                    r.timestamp.isoformat(),
                    r.valor_antigo,
                    r.valor_novo,
                )
                for r in alteracoes
            ],
        )
        conn.commit()


def listar_sessoes_historicas(usuario_id: int) -> list[tuple]:
    """
    Retorna as sessões encerradas de um usuário, mais recentes primeiro.

    Complexidade: O(k log n) — lookup indexado por usuario_id, ordenação
    já usa o índice composto (usuario_id, encerrada_em DESC).
    """
    with sqlite3.connect(DB_PATH) as conn:
        return conn.execute(
            """
            SELECT id, usuario_id, url, xpath_monitorado, valor_inicial,
                   valor_final, total_alteracoes, iniciada_em, encerrada_em
            FROM sessoes_historicas
            WHERE usuario_id = ?
            ORDER BY encerrada_em DESC
            """,
            (usuario_id,),
        ).fetchall()


def obter_sessao_historica(sessao_id: str) -> tuple | None:
    """Busca uma sessão histórica pelo id. O(log n)."""
    with sqlite3.connect(DB_PATH) as conn:
        return conn.execute(
            """
            SELECT id, usuario_id, url, xpath_monitorado, valor_inicial,
                   valor_final, total_alteracoes, iniciada_em, encerrada_em
            FROM sessoes_historicas
            WHERE id = ?
            """,
            (sessao_id,),
        ).fetchone()


def listar_alteracoes_historicas(sessao_id: str) -> list[tuple]:
    """Retorna as alterações de uma sessão histórica, em ordem cronológica."""
    with sqlite3.connect(DB_PATH) as conn:
        return conn.execute(
            """
            SELECT ciclo, timestamp, valor_antigo, valor_novo
            FROM alteracoes_historicas
            WHERE sessao_id = ?
            ORDER BY ciclo ASC
            """,
            (sessao_id,),
        ).fetchall()
