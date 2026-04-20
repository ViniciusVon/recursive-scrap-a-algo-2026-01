/**
 * Store global da sessão de monitoramento ativa.
 *
 * Alimentado por eventos do WebSocket do backend:
 *   - "inicial"    -> popula snapshot completo
 *   - "ciclo"      -> atualiza valor_atual e ciclo
 *   - "alteracao"  -> anexa registro ao histórico
 *   - "screenshot" -> atualiza imagem do mini-navegador
 *   - "encerrada"  -> marca sessão como encerrada
 *   - "ping"       -> ignorado (keepalive)
 *   - "erro"       -> grava mensagem de erro
 */

import { create } from 'zustand';
import type { RegistroHistorico, Sessao } from '../api/client';

type ConnState = 'idle' | 'conectando' | 'conectado' | 'desconectado' | 'erro';

interface SessionStore {
  sessao: Sessao | null;
  historico: RegistroHistorico[];
  screenshot: string | null; // base64 sem prefixo data:
  ultimoCiclo: number;
  conn: ConnState;
  mensagem: string | null;

  aplicarEvento: (evento: unknown) => void;
  setConn: (c: ConnState, msg?: string) => void;
  reset: () => void;
}

export const useSessionStore = create<SessionStore>((set) => ({
  sessao: null,
  historico: [],
  screenshot: null,
  ultimoCiclo: 0,
  conn: 'idle',
  mensagem: null,

  setConn: (c, msg) => set({ conn: c, mensagem: msg ?? null }),

  reset: () =>
    set({
      sessao: null,
      historico: [],
      screenshot: null,
      ultimoCiclo: 0,
      conn: 'idle',
      mensagem: null,
    }),

  aplicarEvento: (evento) => {
    const ev = evento as { type?: string; [k: string]: unknown };
    switch (ev.type) {
      case 'inicial': {
        // Backend manda `ciclo` dentro de `sessao`; separamos para manter
        // `Sessao` alinhado com os tipos REST.
        const raw = ev.sessao as Sessao & { ciclo?: number };
        const { ciclo, ...sessao } = raw;
        const historico = (ev.historico as RegistroHistorico[]) ?? [];
        set({
          sessao: sessao as Sessao,
          historico,
          ultimoCiclo: ciclo ?? 0,
        });
        break;
      }
      case 'ciclo': {
        set((st) => ({
          ultimoCiclo: ev.ciclo as number,
          sessao: st.sessao
            ? { ...st.sessao, valor_atual: ev.valor_atual as string }
            : st.sessao,
        }));
        break;
      }
      case 'alteracao': {
        const reg = ev.registro as RegistroHistorico;
        set((st) => ({ historico: [...st.historico, reg] }));
        break;
      }
      case 'screenshot': {
        set({ screenshot: ev.data as string });
        break;
      }
      case 'encerrada': {
        set((st) => ({
          sessao: st.sessao ? { ...st.sessao, status: 'encerrada' } : null,
        }));
        break;
      }
      case 'erro': {
        set({ mensagem: (ev.mensagem as string) ?? 'Erro desconhecido' });
        break;
      }
      // ping é ignorado
    }
  },
}));
