import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { api, type ValorEncontrado } from '../api/client';

/**
 * Tela 4 — Seleção do valor a monitorar.
 * Lista os valores encontrados pelo list_values.js e permite escolher um.
 */
export default function SelectValuePage() {
  const { sessionId = '' } = useParams();
  const navigate = useNavigate();

  const [valores, setValores] = useState<ValorEncontrado[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [selecionando, setSelecionando] = useState<number | null>(null);
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    api
      .listarValores(sessionId)
      .then(setValores)
      .catch((e) => setErro(String(e)))
      .finally(() => setCarregando(false));
  }, [sessionId]);

  async function selecionar(v: ValorEncontrado) {
    setErro(null);
    setSelecionando(v.indice);
    try {
      await api.selecionarValor(sessionId, v.xpath, v.text);
      navigate(`/dashboard/${sessionId}`);
    } catch (e) {
      setErro(String(e));
      setSelecionando(null);
    }
  }

  return (
    <section className="bg-white rounded-lg border border-gray-200 p-6">
      <h2 className="text-lg font-medium mb-4">
        Escolha o valor a monitorar
      </h2>

      {carregando && <p className="text-gray-500">Extraindo valores da página...</p>}
      {erro && <p className="text-red-600 text-sm mb-3">{erro}</p>}

      {!carregando && valores.length === 0 && (
        <p className="text-gray-500">Nenhum valor numérico encontrado.</p>
      )}

      <ul className="grid gap-2 md:grid-cols-2">
        {valores.map((v) => (
          <li key={v.indice}>
            <button
              onClick={() => selecionar(v)}
              disabled={selecionando !== null}
              className="w-full text-left px-4 py-2 rounded border border-gray-200 hover:bg-indigo-50 hover:border-indigo-300 disabled:opacity-50"
            >
              <span className="font-mono text-sm">{v.text}</span>
              <span className="block text-xs text-gray-400 truncate">
                {v.xpath}
              </span>
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}
