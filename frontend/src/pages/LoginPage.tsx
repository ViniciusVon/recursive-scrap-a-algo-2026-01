import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, type Usuario } from '../api/client';

/**
 * Tela 1 — Identificação do usuário.
 * Lista os usuários cadastrados e permite criar um novo.
 */
export default function LoginPage() {
  const navigate = useNavigate();
  const [usuarios, setUsuarios] = useState<Usuario[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);

  const [nome, setNome] = useState('');
  const [email, setEmail] = useState('');
  const [criando, setCriando] = useState(false);

  useEffect(() => {
    api
      .listarUsuarios()
      .then(setUsuarios)
      .catch((e) => setErro(String(e)))
      .finally(() => setCarregando(false));
  }, []);

  function entrar(u: Usuario) {
    navigate('/config', { state: { usuario: u } });
  }

  async function cadastrar(e: React.FormEvent) {
    e.preventDefault();
    setErro(null);
    setCriando(true);
    try {
      const novo = await api.criarUsuario(nome.trim(), email.trim());
      entrar(novo);
    } catch (e) {
      setErro(String(e));
    } finally {
      setCriando(false);
    }
  }

  return (
    <div className="grid gap-6 md:grid-cols-2">
      <section className="bg-white rounded-lg border border-gray-200 p-6">
        <h2 className="text-lg font-medium mb-4">Usuários cadastrados</h2>
        {carregando && <p className="text-gray-500">Carregando...</p>}
        {!carregando && usuarios.length === 0 && (
          <p className="text-gray-500">Nenhum usuário ainda. Cadastre ao lado.</p>
        )}
        <ul className="space-y-2">
          {usuarios.map((u) => (
            <li key={u.id}>
              <button
                onClick={() => entrar(u)}
                className="w-full text-left px-4 py-2 rounded border border-gray-200 hover:bg-indigo-50 hover:border-indigo-300"
              >
                <span className="font-medium">{u.nome}</span>
                <span className="block text-sm text-gray-500">{u.email}</span>
              </button>
            </li>
          ))}
        </ul>
      </section>

      <section className="bg-white rounded-lg border border-gray-200 p-6">
        <h2 className="text-lg font-medium mb-4">Novo cadastro</h2>
        <form onSubmit={cadastrar} className="space-y-3">
          <label className="block">
            <span className="text-sm text-gray-700">Nome</span>
            <input
              value={nome}
              onChange={(e) => setNome(e.target.value)}
              required
              minLength={3}
              className="mt-1 w-full px-3 py-2 border border-gray-300 rounded"
            />
          </label>
          <label className="block">
            <span className="text-sm text-gray-700">E-mail</span>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="mt-1 w-full px-3 py-2 border border-gray-300 rounded"
            />
          </label>
          <button
            type="submit"
            disabled={criando}
            className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 disabled:opacity-60"
          >
            {criando ? 'Criando...' : 'Cadastrar e entrar'}
          </button>
        </form>
        {erro && <p className="text-red-600 text-sm mt-3">{erro}</p>}
      </section>
    </div>
  );
}
