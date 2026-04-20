import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { api } from '../api/client';
import BrowserPreview from '../components/BrowserPreview';
import { useSessionWS } from '../hooks/useSessionWS';
import { useSessionStore } from '../store/sessionStore';

/**
 * Página 2 — Monitor ao vivo.
 *
 * Conecta via WebSocket e o estado (sessão, histórico, screenshots) é
 * populado por eventos push. Sem polling. É a página dedicada para
 * onde "salvam" as alterações conforme acontecem durante o
 * monitoramento.
 */
export default function MonitorPage() {
  const { sessionId = '' } = useParams();
  const navigate = useNavigate();

  // Abre/fecha a conexão WS e alimenta o store.
  useSessionWS(sessionId);

  const sessao = useSessionStore((s) => s.sessao);
  const historico = useSessionStore((s) => s.historico);
  const ultimoCiclo = useSessionStore((s) => s.ultimoCiclo);
  const conn = useSessionStore((s) => s.conn);
  const mensagem = useSessionStore((s) => s.mensagem);

  const [encerrando, setEncerrando] = useState(false);
  const [encerrada, setEncerrada] = useState(false);

  async function encerrar() {
    if (encerrando) return;
    setEncerrando(true);
    // Espera o backend confirmar: o DELETE é quem dispara o e-mail de
    // resumo. Se der erro, ainda assim seguimos para o estado
    // "encerrada" pra não travar a UI.
    await api.encerrar(sessionId).catch(() => {});
    setEncerrada(true);
    // Se essa aba foi aberta como popup pelo wizard, `window.close()`
    // funciona. Caso contrário (usuário colou a URL manualmente),
    // voltamos pra home.
    setTimeout(() => {
      window.close();
      navigate('/');
    }, 1500);
  }

  return (
    <div className="space-y-6">
      <section className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-lg font-medium">Monitoramento ativo</h2>
            <p className="text-sm text-gray-500 break-all">
              {sessao?.url ?? 'Carregando sessão...'}
            </p>
            <p className="text-xs text-gray-400 mt-1">
              Ao encerrar, você receberá um e-mail com o resumo da sessão.
            </p>
          </div>
          <button
            onClick={encerrar}
            disabled={encerrando}
            className="px-3 py-1.5 text-sm border border-red-300 text-red-600 rounded hover:bg-red-50 disabled:opacity-60"
          >
            {encerrada
              ? 'Sessão encerrada ✓'
              : encerrando
                ? 'Encerrando e enviando e-mail...'
                : 'Encerrar sessão'}
          </button>
        </div>

        <dl className="grid grid-cols-4 gap-4 mt-4 text-sm">
          <div>
            <dt className="text-gray-500">Status</dt>
            <dd className="font-mono">{sessao?.status ?? '...'}</dd>
          </div>
          <div>
            <dt className="text-gray-500">Valor atual</dt>
            <dd className="font-mono">{sessao?.valor_atual ?? '...'}</dd>
          </div>
          <div>
            <dt className="text-gray-500">Ciclo</dt>
            <dd className="font-mono">{ultimoCiclo}</dd>
          </div>
          <div>
            <dt className="text-gray-500">Alterações</dt>
            <dd className="font-mono">{historico.length}</dd>
          </div>
        </dl>
      </section>

      <section className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="font-medium mb-2">Navegador (preview)</h3>
        <BrowserPreview />
        <p className="text-xs text-gray-400 mt-2">
          Screenshots atualizam a cada 2s enquanto a sessão estiver ativa.
        </p>
      </section>

      <section className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="font-medium mb-3">Histórico de alterações</h3>
        {historico.length === 0 ? (
          <p className="text-sm text-gray-500">
            Nenhuma alteração ainda. O monitor compara o valor a cada 15s.
          </p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500 border-b">
                <th className="py-2">Ciclo</th>
                <th>Horário</th>
                <th>De</th>
                <th>Para</th>
              </tr>
            </thead>
            <tbody>
              {historico.map((r) => (
                <tr key={r.ciclo} className="border-b last:border-b-0">
                  <td className="py-2 font-mono">{r.ciclo}</td>
                  <td className="font-mono">
                    {new Date(r.timestamp).toLocaleTimeString('pt-BR')}
                  </td>
                  <td className="font-mono">{r.valor_antigo}</td>
                  <td className="font-mono text-indigo-700">{r.valor_novo}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      {(conn === 'erro' || conn === 'desconectado') && mensagem && (
        <p className="text-red-600 text-sm">
          {mensagem}
        </p>
      )}
    </div>
  );
}
