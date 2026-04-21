/**
 * Hook que gerencia a conexão WebSocket de uma sessão.
 *
 * - Conecta ao montar, despacha cada mensagem para o `sessionStore` e
 *   fecha a conexão ao desmontar.
 * - Reconecta com backoff exponencial em caso de queda inesperada.
 * - Pequeno delay antes de conectar evita abrir/fechar uma conexão
 *   zumbi durante o double-effect do React StrictMode em dev.
 * - Códigos definitivos (1000 normal, 4404 sessão inexistente) e
 *   evento `encerrada` vindo do servidor PARAM o loop de reconnect.
 */

import { useEffect } from 'react';
import { useSessionStore } from '../store/sessionStore';

const BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';
const WS_URL = BASE_URL.replace(/^http/, 'ws');

const MOUNT_DELAY_MS = 100;
const MAX_BACKOFF_MS = 10_000;

export function useSessionWS(sessionId: string | undefined): void {
  const aplicarEvento = useSessionStore((s) => s.aplicarEvento);
  const setConn = useSessionStore((s) => s.setConn);
  const reset = useSessionStore((s) => s.reset);

  useEffect(() => {
    if (!sessionId) return;

    reset();
    let ws: WebSocket | null = null;
    let tentativa = 0;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let mountTimer: ReturnType<typeof setTimeout> | null = null;
    let desmontado = false;
    // Quando o servidor sinaliza fim-de-vida da sessão, param os
    // reconnects automáticos.
    let encerrado = false;

    function conectar() {
      if (desmontado || encerrado) return;
      setConn('conectando');
      ws = new WebSocket(`${WS_URL}/ws/sessoes/${sessionId}`);

      ws.onopen = () => {
        tentativa = 0;
        setConn('conectado');
      };

      ws.onmessage = (e) => {
        try {
          const evento = JSON.parse(e.data);
          if (evento?.type === 'encerrada') {
            // Backend avisou que a sessão morreu — não tenta reconectar
            // depois que essa conexão cair.
            encerrado = true;
          }
          aplicarEvento(evento);
        } catch {
          // payload inválido, ignora
        }
      };

      ws.onerror = () => {
        // onerror dispara junto com onclose em vários casos — inclusive
        // quando o servidor fecha a conexão após emitir `encerrada`
        // (alguns navegadores tratam o close remoto como falha). Se já
        // sabemos que a sessão morreu normalmente, não é erro.
        if (encerrado) return;
        if (ws && ws.readyState !== WebSocket.OPEN) {
          setConn('erro', 'Falha na conexão WebSocket.');
        }
      };

      ws.onclose = (ev) => {
        if (desmontado) return;
        // 1000 = fechamento normal; 4404 = sessão não existe no backend
        // (ex.: já encerrada, ou o servidor reiniciou). Em ambos os
        // casos não faz sentido ficar reconectando em loop.
        const codigoDefinitivo = ev.code === 1000 || ev.code === 4404;
        if (encerrado || codigoDefinitivo) {
          setConn('desconectado', 'Sessão encerrada.');
          return;
        }
        setConn('desconectado');
        tentativa += 1;
        const delay = Math.min(1000 * 2 ** tentativa, MAX_BACKOFF_MS);
        reconnectTimer = setTimeout(conectar, delay);
      };
    }

    // Pequeno atraso: no StrictMode dev, o useEffect roda duas vezes
    // em sequência (mount → cleanup → mount). Sem o atraso, abrimos e
    // fechamos uma conexão WS "zumbi" que gera stack trace no backend.
    // Com o atraso + cancelamento no cleanup, só a segunda instância
    // chega a abrir socket.
    mountTimer = setTimeout(conectar, MOUNT_DELAY_MS);

    return () => {
      desmontado = true;
      if (mountTimer) clearTimeout(mountTimer);
      if (reconnectTimer) clearTimeout(reconnectTimer);
      if (ws && ws.readyState <= WebSocket.OPEN) ws.close(1000, 'unmount');
    };
  }, [sessionId, aplicarEvento, setConn, reset]);
}
