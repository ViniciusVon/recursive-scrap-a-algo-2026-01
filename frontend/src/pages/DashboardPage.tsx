import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  api,
  type RegistroHistorico,
  type Sessao,
} from '../api/client';

const POLL_MS = 3000;

/**
 * Tela 3 — Dashboard de monitoramento.
 * Fase 1: preview do navegador fica como placeholder; Fase 2 implementa
 * streaming de screenshots via WebSocket. Histórico é atualizado por
 * polling a cada 3s.
 */
export default function DashboardPage() {
  const { sessionId = '' } = useParams();
  const navigate = useNavigate();

  const [sessao, setSessao] = useState<Sessao | null>(null);
  const [historico, setHistorico] = useState<RegistroHistorico[]>([]);
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    let ativo = true;

    async function tick() {
      try {
        const [s, h] = await Promise.all([
          api.obterSessao(sessionId),
          api.historico(sessionId),
        ]);
        if (!ativo) return;
        setSessao(s);
        setHistorico(h);
      } catch (e) {
        if (ativo) setErro(String(e));
      }
    }

    tick();
    const id = setInterval(tick, POLL_MS);
    return () => {
      ativo = false;
      clearInterval(id);
    };
  }, [sessionId]);

  async function encerrar() {
    await api.encerrar(sessionId).catch(() => {});
    navigate('/login');
  }

  return (
    <div className="space-y-6">
      <section className="bg-white rounded-lg border border-gray-200 p-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-lg font-medium">Monitoramento ativo</h2>
            <p className="text-sm text-gray-500 break-all">{sessao?.url}</p>
          </div>
          <button
            onClick={encerrar}
            className="px-3 py-1.5 text-sm border border-red-300 text-red-600 rounded hover:bg-red-50"
          >
            Encerrar sessão
          </button>
        </div>

        <dl className="grid grid-cols-3 gap-4 mt-4 text-sm">
          <div>
            <dt className="text-gray-500">Status</dt>
            <dd className="font-mono">{sessao?.status ?? '...'}</dd>
          </div>
          <div>
            <dt className="text-gray-500">Valor atual</dt>
            <dd className="font-mono">{sessao?.valor_atual ?? '...'}</dd>
          </div>
          <div>
            <dt className="text-gray-500">Alterações</dt>
            <dd className="font-mono">{historico.length}</dd>
          </div>
        </dl>
      </section>

      <section className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="font-medium mb-2">Navegador (preview)</h3>
        <div className="h-56 flex items-center justify-center bg-gray-50 border border-dashed border-gray-300 rounded text-gray-400 text-sm">
          Preview ao vivo chega na Fase 2 (WebSocket + screenshots)
        </div>
      </section>

      <section className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="font-medium mb-3">Histórico de alterações</h3>
        {historico.length === 0 ? (
          <p className="text-sm text-gray-500">
            Nenhuma alteração ainda. O monitor atualiza a cada 15s.
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

      {erro && (
        <p className="text-red-600 text-sm">
          Erro ao atualizar: {erro}
        </p>
      )}
    </div>
  );
}
