/**
 * Stack global de toasts.
 *
 * Montado uma única vez em App.tsx. Lê de `useToastStore` e renderiza
 * uma pilha fixa no canto superior direito. Cada toast tem cor/ícone
 * conforme o `tipo` e um botão "×" para dispensa manual (além do
 * auto-dismiss disparado pelo próprio store).
 */

import { useToastStore, type ToastTipo } from '../store/toastStore';

const ESTILOS: Record<ToastTipo, { bg: string; border: string; icon: string; label: string }> = {
  sucesso: {
    bg: 'bg-green-50',
    border: 'border-green-300 text-green-800',
    icon: '✓',
    label: 'Sucesso',
  },
  erro: {
    bg: 'bg-red-50',
    border: 'border-red-300 text-red-800',
    icon: '✕',
    label: 'Erro',
  },
  info: {
    bg: 'bg-blue-50',
    border: 'border-blue-300 text-blue-800',
    icon: 'ℹ',
    label: 'Info',
  },
  aviso: {
    bg: 'bg-amber-50',
    border: 'border-amber-300 text-amber-800',
    icon: '⚠',
    label: 'Aviso',
  },
};

export default function ToastContainer() {
  const toasts = useToastStore((s) => s.toasts);
  const remover = useToastStore((s) => s.remover);

  if (toasts.length === 0) return null;

  return (
    <div
      className="fixed top-4 right-4 z-50 flex flex-col gap-2 w-[min(92vw,22rem)]"
      role="region"
      aria-label="Notificações"
    >
      {toasts.map((t) => {
        const e = ESTILOS[t.tipo];
        return (
          <div
            key={t.id}
            role={t.tipo === 'erro' ? 'alert' : 'status'}
            className={`${e.bg} ${e.border} border rounded-md shadow-sm px-3 py-2 flex items-start gap-2 text-sm animate-[fadeIn_0.15s_ease-out]`}
          >
            <span aria-hidden="true" className="font-semibold leading-5">
              {e.icon}
            </span>
            <div className="flex-1 min-w-0">
              <span className="sr-only">{e.label}: </span>
              <p className="break-words">{t.mensagem}</p>
            </div>
            <button
              type="button"
              onClick={() => remover(t.id)}
              className="text-current/60 hover:text-current leading-5 px-1"
              aria-label="Dispensar notificação"
            >
              ×
            </button>
          </div>
        );
      })}
    </div>
  );
}
