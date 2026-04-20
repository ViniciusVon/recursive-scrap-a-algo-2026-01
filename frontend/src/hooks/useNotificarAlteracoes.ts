/**
 * Notifica o usuário quando o store de sessão recebe uma nova alteração.
 *
 * Dispara em dois canais:
 *   1. `toast.info(...)` — aparece in-app (sempre).
 *   2. Browser Notification API — só se o usuário tiver concedido
 *      permissão (pedida sob demanda no primeiro uso).
 *
 * O hook observa o comprimento do `historico` e o registro mais recente;
 * assim evitamos notificar retroativamente os registros carregados no
 * evento `inicial`.
 */

import { useEffect, useRef } from 'react';
import { useSessionStore } from '../store/sessionStore';
import { toast } from '../store/toastStore';

export function useNotificarAlteracoes(): void {
  const historico = useSessionStore((s) => s.historico);
  const sessao = useSessionStore((s) => s.sessao);

  // Guarda o tamanho visto na última renderização. No primeiro mount, o
  // "estado anterior" = "estado atual" → nada notifica até chegar algo
  // novo via WebSocket.
  const contagemAnterior = useRef<number | null>(null);

  useEffect(() => {
    if (contagemAnterior.current === null) {
      contagemAnterior.current = historico.length;
      return;
    }
    if (historico.length <= contagemAnterior.current) {
      contagemAnterior.current = historico.length;
      return;
    }

    const novos = historico.slice(contagemAnterior.current);
    contagemAnterior.current = historico.length;

    for (const reg of novos) {
      const msg = `Valor mudou: ${reg.valor_antigo} → ${reg.valor_novo}`;
      toast.info(msg);
      dispararNotificacaoNavegador('Monitor de preços', msg, sessao?.url);
    }
  }, [historico, sessao?.url]);
}

/**
 * Envia uma Notification do navegador de forma best-effort.
 *
 * - Se o suporte não existir (Safari muito antigo, webview), não faz nada.
 * - Se a permissão for `default`, pede uma vez por clique prévio. Navegadores
 *   modernos exigem gesto do usuário — caso o pedido falhe, a função
 *   silencia e confiamos no toast in-app.
 */
function dispararNotificacaoNavegador(
  titulo: string,
  corpo: string,
  tag?: string,
): void {
  if (typeof window === 'undefined' || !('Notification' in window)) return;

  const permissao = Notification.permission;
  if (permissao === 'granted') {
    try {
      new Notification(titulo, { body: corpo, tag });
    } catch {
      // alguns browsers bloqueiam Notification fora de secure contexts
    }
    return;
  }
  if (permissao === 'default') {
    // Pede permissão silenciosamente — se negar, na próxima alteração
    // já sai desse ramo e fica só no toast.
    Notification.requestPermission().catch(() => {});
  }
}

/** Solicita permissão de notificação; usado por um botão explícito. */
export async function pedirPermissaoNotificacao(): Promise<NotificationPermission> {
  if (typeof window === 'undefined' || !('Notification' in window)) {
    return 'denied';
  }
  if (Notification.permission !== 'default') return Notification.permission;
  try {
    return await Notification.requestPermission();
  } catch {
    return 'denied';
  }
}
