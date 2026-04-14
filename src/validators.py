"""
Módulo de validações de entrada do usuário.
"""

import re


def validar_nome_usuario(nome: str) -> bool:
    """
    Valida se o nome de usuário contém ao menos 3 caracteres e é composto
    apenas por letras (permite nomes compostos separados por espaço). O(n)
    """
    nome = nome.strip()
    if len(nome) < 3:
        return False
    partes = nome.split()
    return all(parte.isalpha() for parte in partes)


def validar_email(email: str) -> bool:
    """Valida formato básico de e-mail. O(1)"""
    padrao = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}$")
    return bool(padrao.match(email.strip()))
