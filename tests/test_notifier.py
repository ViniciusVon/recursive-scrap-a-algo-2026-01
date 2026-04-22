"""Testes para o módulo de notificações por e-mail."""

import smtplib
from unittest.mock import patch, MagicMock
from src.notifier import enviar_email, montar_corpo_alteracao
from datetime import datetime

@patch("src.notifier.smtplib.SMTP")
def test_enviar_email_sucesso(mock_smtp_class):
    mock_server = MagicMock()
    mock_smtp_class.return_value.__enter__.return_value = mock_server
    
    sucesso = enviar_email(
        destinatario="alvo@teste.com",
        senha_app="senha123",
        assunto="Teste",
        corpo="Corpo do teste",
        remetente="remetente@teste.com"
    )
    
    assert sucesso is True
    mock_server.starttls.assert_called_once()
    mock_server.login.assert_called_once_with("remetente@teste.com", "senha123")
    mock_server.send_message.assert_called_once()

@patch("src.notifier.smtplib.SMTP")
def test_enviar_email_falha_autenticacao(mock_smtp_class):
    mock_server = MagicMock()
    # Simula erro de autenticação do Gmail
    mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, b"Auth failed")
    mock_smtp_class.return_value.__enter__.return_value = mock_server
    
    sucesso = enviar_email("a@a.com", "errada", "A", "C", "r@r.com")
    assert sucesso is False

def test_montar_corpo_alteracao():
    antes = {"numeros": ["10", "20"]}
    depois = {"numeros": ["20", "30"]}
    
    corpo = montar_corpo_alteracao("http://teste.com", antes, depois)
    
    assert "URL: http://teste.com" in corpo
    assert "+ 30" in corpo # Valor adicionado
    assert "- 10" in corpo # Valor removido
    assert "Antes: 2 valores" in corpo