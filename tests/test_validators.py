"""Testes para o módulo de validação."""

import pytest
from src.validators import validar_nome_usuario, validar_email

def test_validar_nome_usuario_valido():
    # Caminho feliz: Nomes com letras e com mais de 3 caracteres
    assert validar_nome_usuario("Gabriel") is True
    assert validar_nome_usuario("Maria Silva") is True
    # O strip() deve limpar os espaços no início e no fim
    assert validar_nome_usuario("  João   ") is True

def test_validar_nome_usuario_invalido():
    # Menos de 3 caracteres
    assert validar_nome_usuario("Zé") is False
    assert validar_nome_usuario("A") is False
    # Contém números
    assert validar_nome_usuario("Gabriel123") is False
    # Contém caracteres especiais/pontuação
    assert validar_nome_usuario("João_Silva") is False
    assert validar_nome_usuario("Maria@") is False

def test_validar_email_valido():
    # Caminho feliz
    assert validar_email("teste@exemplo.com") is True
    assert validar_email("usuario.nome+filtro@dominio.com.br") is True
    # O strip() deve permitir e-mails com espaços acidentais
    assert validar_email("  teste@exemplo.com  ") is True

def test_validar_email_invalido():
    # Falta o símbolo @ ou domínio incompleto
    assert validar_email("emailinvalido") is False
    assert validar_email("teste@.com") is False
    assert validar_email("@dominio.com") is False
    assert validar_email("teste@dominio") is False