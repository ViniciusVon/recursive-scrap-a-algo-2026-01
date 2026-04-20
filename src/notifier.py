"""
Módulo de notificação por e-mail via Gmail SMTP.
"""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from src.constants import SMTP_HOST, SMTP_PORT

logger = logging.getLogger(__name__)


def carregar_senha_app() -> str:
    """Carrega a senha de app do Gmail a partir do arquivo .env. O(1)"""
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for linha in f:
                if linha.startswith("GMAIL_APP_PASSWORD="):
                    return linha.split("=", 1)[1].strip()
    return ""


def enviar_email(destinatario: str, senha_app: str, assunto: str, corpo: str) -> bool:
    """
    Envia um e-mail via Gmail SMTP.
    O remetente é o próprio destinatário (usa a conta do usuário). O(1)
    """
    msg = MIMEMultipart()
    msg["From"] = destinatario
    msg["To"] = destinatario
    msg["Subject"] = assunto
    msg.attach(MIMEText(corpo, "plain", "utf-8"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as servidor:
            servidor.starttls()
            servidor.login(destinatario, senha_app)
            servidor.send_message(msg)
        logger.info("LOG | E-mail enviado para %s", destinatario)
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error("Falha de autenticação SMTP. Verifique a senha de app do Gmail.")
        return False
    except smtplib.SMTPException as exc:
        logger.error("Erro ao enviar e-mail: %s", exc)
        return False


def montar_resumo_sessao(
    url: str,
    valor_final: Optional[str],
    historico: list,
) -> tuple:
    """
    Gera (assunto, corpo) de um e-mail resumindo uma sessão de
    monitoramento que acabou de ser encerrada.

    `historico` é uma lista de objetos com atributos `.ciclo`,
    `.timestamp`, `.valor_antigo`, `.valor_novo` (os `RegistroAlteracao`
    do session_manager).

    Complexidade: O(k), onde k é o número de alterações registradas.
    """
    linhas = [
        "Resumo do monitoramento",
        "-----------------------",
        f"URL: {url}",
        f"Valor final observado: {valor_final or '—'}",
        f"Total de alterações: {len(historico)}",
        "",
    ]

    if historico:
        linhas.append("Histórico:")
        for r in historico:
            quando = r.timestamp.strftime("%d/%m/%Y %H:%M:%S")
            linhas.append(
                f"  [{quando}] ciclo {r.ciclo}: "
                f"{r.valor_antigo} -> {r.valor_novo}"
            )
    else:
        linhas.append("Nenhuma alteração foi registrada durante a sessão.")

    assunto = f"Monitor de Preços — sessão encerrada ({len(historico)} alterações)"
    return assunto, "\n".join(linhas)


def montar_corpo_alteracao(url: str, antes: dict, depois: dict) -> str:
    """Monta o corpo do e-mail com as alterações detectadas.

    Complexidade: O(n log n) — a construção dos sets é O(n), a diferença
    simétrica é O(n), e os `sorted(novos)` / `sorted(removidos)` custam
    O(k log k), dominando o total.
    """
    linhas = [
        "Alterações detectadas no monitoramento!",
        f"\nURL: {url}\n",
    ]

    numeros_antes = set(antes.get("numeros", []))
    numeros_depois = set(depois.get("numeros", []))

    novos = numeros_depois - numeros_antes
    removidos = numeros_antes - numeros_depois

    if novos:
        linhas.append("Valores NOVOS:")
        for v in sorted(novos):
            linhas.append(f"  + {v}")

    if removidos:
        linhas.append("Valores REMOVIDOS:")
        for v in sorted(removidos):
            linhas.append(f"  - {v}")

    if not novos and not removidos:
        linhas.append("Houve alteração na ordem ou frequência dos valores numéricos.")

    linhas.append(f"\nAntes: {len(antes.get('numeros', []))} valores")
    linhas.append(f"Depois: {len(depois.get('numeros', []))} valores")

    return "\n".join(linhas)
