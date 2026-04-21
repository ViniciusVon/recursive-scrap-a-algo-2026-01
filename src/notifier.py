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


def _ler_env(chave: str) -> str:
    """Leitor simples de chave=valor em `.env` (O(n) nas linhas do arquivo)."""
    env_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", ".env"
    )
    if not os.path.exists(env_path):
        return ""
    prefixo = f"{chave}="
    with open(env_path) as f:
        for linha in f:
            if linha.startswith(prefixo):
                return linha.split("=", 1)[1].strip()
    return ""


def carregar_senha_app() -> str:
    """Carrega `GMAIL_APP_PASSWORD` do `.env`. O(1) amortizado."""
    return _ler_env("GMAIL_APP_PASSWORD")


def carregar_remetente() -> str:
    """
    Email da conta que autentica no SMTP.

    Tenta `GMAIL_USER`; se não existir, tenta `GMAIL_FROM`. Vazio
    se não estiver configurado — nesse caso o caller deve decidir
    se pula o envio.
    """
    return _ler_env("GMAIL_USER") or _ler_env("GMAIL_FROM")


def enviar_email(
    destinatario: str,
    senha_app: str,
    assunto: str,
    corpo: str,
    remetente: Optional[str] = None,
) -> bool:
    """
    Envia um e-mail via Gmail SMTP.

    A autenticação é feita com `remetente` + `senha_app` — essa é a
    conta dona da senha de app do `.env`. O e-mail sai **do** remetente
    e é entregue **ao** `destinatario`, que pode ser qualquer endereço.

    Se `remetente` não for passado, cai pro `GMAIL_USER` do `.env`; se
    mesmo assim estiver vazio, usa o próprio destinatário (comportamento
    antigo, que só funciona quando o destinatário é o dono da senha).

    O(1).
    """
    if not remetente:
        remetente = carregar_remetente() or destinatario

    msg = MIMEMultipart()
    msg["From"] = remetente
    msg["To"] = destinatario
    msg["Subject"] = assunto
    msg.attach(MIMEText(corpo, "plain", "utf-8"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as servidor:
            servidor.starttls()
            servidor.login(remetente, senha_app)
            servidor.send_message(msg)
        logger.info(
            "LOG | E-mail enviado de %s para %s", remetente, destinatario
        )
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error(
            "Falha de autenticação SMTP para %s. "
            "Verifique GMAIL_USER e GMAIL_APP_PASSWORD no .env.",
            remetente,
        )
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
