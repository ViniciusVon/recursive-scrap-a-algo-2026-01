/**
 * Mini-navegador embutido: mostra os screenshots que chegam via WS.
 */

import { useSessionStore } from '../store/sessionStore';

export default function BrowserPreview() {
  const screenshot = useSessionStore((s) => s.screenshot);
  const conn = useSessionStore((s) => s.conn);

  return (
    <div className="relative w-full aspect-video bg-gray-900 rounded border border-gray-300 overflow-hidden">
      {screenshot ? (
        <img
          src={`data:image/png;base64,${screenshot}`}
          alt="Navegador monitorado"
          className="w-full h-full object-contain"
        />
      ) : (
        <div className="absolute inset-0 flex items-center justify-center text-gray-400 text-sm">
          {conn === 'conectando'
            ? 'Conectando ao navegador...'
            : 'Aguardando primeiro screenshot...'}
        </div>
      )}

      <span
        className={`absolute top-2 right-2 px-2 py-0.5 text-xs rounded ${
          conn === 'conectado'
            ? 'bg-emerald-500/80 text-white'
            : conn === 'desconectado' || conn === 'erro'
              ? 'bg-red-500/80 text-white'
              : 'bg-gray-500/80 text-white'
        }`}
      >
        {conn}
      </span>
    </div>
  );
}
