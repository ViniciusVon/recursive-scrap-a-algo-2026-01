import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { api, type Usuario } from '../api/client';

/**
 * Tela 2 — Configuração do monitoramento.
 * Coleta URL e modo headless, abre a sessão no backend e
 * navega para a seleção de valores.
 */
export default function ConfigPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const usuario = (location.state as { usuario?: Usuario } | null)?.usuario;

  const [url, setUrl] = useState('');
  const [headless, setHeadless] = useState(true);
  const [iniciando, setIniciando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  if (!usuario) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <p>Sessão inválida.</p>
        <button
          onClick={() => navigate('/login')}
          className="mt-3 px-4 py-2 bg-indigo-600 text-white rounded"
        >
          Voltar ao login
        </button>
      </div>
    );
  }

  async function iniciar(e: React.FormEvent) {
    e.preventDefault();
    setErro(null);
    setIniciando(true);
    try {
      const sessao = await api.criarSessao(usuario!.id, url.trim(), headless);
      navigate(`/select/${sessao.id}`, { state: { usuario, sessao } });
    } catch (e) {
      setErro(String(e));
    } finally {
      setIniciando(false);
    }
  }

  return (
    <section className="bg-white rounded-lg border border-gray-200 p-6 max-w-xl">
      <h2 className="text-lg font-medium mb-1">Configurar monitoramento</h2>
      <p className="text-sm text-gray-500 mb-4">
        Logado como <strong>{usuario.nome}</strong> ({usuario.email})
      </p>

      <form onSubmit={iniciar} className="space-y-4">
        <label className="block">
          <span className="text-sm text-gray-700">URL do site</span>
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://site.com/produto"
            required
            className="mt-1 w-full px-3 py-2 border border-gray-300 rounded"
          />
        </label>

        <fieldset>
          <legend className="text-sm text-gray-700 mb-1">Modo do navegador</legend>
          <label className="inline-flex items-center mr-4">
            <input
              type="radio"
              checked={headless}
              onChange={() => setHeadless(true)}
              className="mr-2"
            />
            Headless (invisível)
          </label>
          <label className="inline-flex items-center">
            <input
              type="radio"
              checked={!headless}
              onChange={() => setHeadless(false)}
              className="mr-2"
            />
            Mostrar navegador
          </label>
        </fieldset>

        <button
          type="submit"
          disabled={iniciando}
          className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 disabled:opacity-60"
        >
          {iniciando ? 'Abrindo navegador...' : 'Iniciar monitoramento'}
        </button>
      </form>

      {erro && <p className="text-red-600 text-sm mt-3">{erro}</p>}
    </section>
  );
}
