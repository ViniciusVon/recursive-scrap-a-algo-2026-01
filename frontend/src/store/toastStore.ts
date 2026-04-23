/**
 * Store de toasts (notificações efêmeras).
 *
 * Qualquer componente pode disparar `toast.sucesso("...")` e o
 * `<ToastContainer />` montado em App.tsx renderiza automaticamente.
 * Os toasts somem sozinhos após `duracao` ms (default 3.5s).
 */

import { create } from 'zustand';

export type ToastTipo = 'sucesso' | 'erro' | 'info' | 'aviso';

export interface Toast {
  id: string;
  tipo: ToastTipo;
  mensagem: string;
}

interface ToastStore {
  toasts: Toast[];
  emitir: (tipo: ToastTipo, mensagem: string, duracao?: number) => void;
  remover: (id: string) => void;
}

export const useToastStore = create<ToastStore>((set, get) => ({
  toasts: [],
  emitir: (tipo, mensagem, duracao = 3500) => {
    const id = `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
    set((st) => ({ toasts: [...st.toasts, { id, tipo, mensagem }] }));
    window.setTimeout(() => get().remover(id), duracao);
  },
  remover: (id) =>
    set((st) => ({ toasts: st.toasts.filter((t) => t.id !== id) })),
}));

/** API ergonômica para uso fora de componentes React. */
export const toast = {
  sucesso: (m: string) => useToastStore.getState().emitir('sucesso', m),
  erro: (m: string) => useToastStore.getState().emitir('erro', m, 5000),
  info: (m: string) => useToastStore.getState().emitir('info', m),
  aviso: (m: string) => useToastStore.getState().emitir('aviso', m, 4500),
};
