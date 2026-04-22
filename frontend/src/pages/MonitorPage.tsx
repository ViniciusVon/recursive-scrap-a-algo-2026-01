import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { api, mensagemDeErro } from '../api/client';
import BrowserPreview from '../components/BrowserPreview';
import { useSessionWS } from '../hooks/useSessionWS';
import {
  pedirPermissaoNotificacao,
  useNotificarAlteracoes,
} from '../hooks/useNotificarAlteracoes';
import { useSessionStore } from '../store/sessionStore';
import { toast } from '../store/toastStore';

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
  // Observa novas alterações e dispara toast + Notification nativa.
  useNotificarAlteracoes();

  const sessao = useSessionStore((s) => s.sessao);
  const historico = useSessionStore((s) => s.historico);
  const ultimoCiclo = useSessionStore((s) => s.ultimoCiclo);
  const conn = useSessionStore((s) => s.conn);
  const mensagem = useSessionStore((s) => s.mensagem);

  const [encerrando, setEncerrando] = useState(false);
  const [encerrada, setEncerrada] = useState(false);
  const [permNotif, setPermNotif] = useState<NotificationPermission>(
    typeof Notification !== 'undefined' ? Notification.permission : 'denied',
  );

  // Surface WS errors as toasts. Mantemos também o texto fixo embaixo
  // pra ficar visível mesmo depois que o toast some.
  useEffect(() => {
    if (conn === 'erro' && mensagem) toast.erro(mensagem);
  }, [conn, mensagem]);

  async function encerrar() {
    if (encerrando) return;
    setEncerrando(true);
    try {
      // Espera o backend confirmar: o DELETE é quem dispara o e-mail de
      // resumo. Se der erro, ainda assim seguimos para o estado
      // "encerrada" pra não travar a UI.
      await api.encerrar(sessionId);
      toast.sucesso('Sessão encerrada. E-mail de resumo a caminho.');
    } catch (e) {
      toast.aviso(mensagemDeErro(e));
    }
    setEncerrada(true);
    // Se essa aba foi aberta como popup pelo wizard, `window.close()`
    // funciona. Caso contrário (usuário colou a URL manualmente),
    // voltamos pra home.
    setTimeout(() => {
      window.close();
      navigate('/');
    }, 1500);
  }

  async function ativarNotificacoes() {
    const resultado = await pedirPermissaoNotificacao();
    setPermNotif(resultado);
    if (resultado === 'granted') {
      toast.sucesso('Notificações ativadas.');
    } else if (resultado === 'denied') {
      toast.aviso(
        'Notificações bloqueadas. Você ainda verá os alertas dentro da página.',
      );
    }
  }

  return (
    <div className="space-y-6">
      <section className="bg-white rounded-lg border border-gray-200 p-4 sm:p-6">
        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
          <div className="min-w-0">
            <h2 className="text-lg font-medium">Monitoramento ativo</h2>
            <p className="text-sm text-gray-500 break-all">
              {sessao?.url ?? 'Carregando sessão...'}
            </p>
            <p className="text-xs text-gray-400 mt-1">
              Ao encerrar, você receberá um e-mail com o resumo da sessão.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            {permNotif === 'default' && (
              <button
                onClick={ativarNotificacoes}
                className="px-3 py-1.5 text-sm border border-indigo-300 text-indigo-700 rounded hover:bg-indigo-50"
              >
                Ativar notificações
              </button>
            )}
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
        </div>

        <dl className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4 text-sm">
          <div>
            <dt className="text-gray-500">Status</dt>
            <dd className="font-mono">{sessao?.status ?? '...'}</dd>
          </div>
          <div>
            <dt className="text-gray-500">Valor atual</dt>
            <dd className="font-mono break-all">
              {sessao?.valor_atual ?? '...'}
            </dd>
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

      <section className="bg-white rounded-lg border border-gray-200 p-4 sm:p-6">
        <h3 className="font-medium mb-2">Navegador (preview)</h3>
        <BrowserPreview />
      </section>

      <section className="bg-white rounded-lg border border-gray-200 p-4 sm:p-6">
        <h3 className="font-medium mb-3">Histórico de alterações</h3>
        {historico.length === 0 ? (
          <p className="text-sm text-gray-500">
            Nenhuma alteração ainda. O monitor compara o valor a cada 15s.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm min-w-[480px]">
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
                    <td className="font-mono text-indigo-700">
                      {r.valor_novo}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {(conn === 'erro' || conn === 'desconectado') && mensagem && (
        <p className="text-red-600 text-sm">{mensagem}</p>
      )}
    </div>
  );
}
