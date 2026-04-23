/**
 * Página 1 — Wizard unificado de setup.
 *
 * Antes eram 3 rotas (/login, /config, /select/:id). Agora o usuário faz
 * tudo em uma única tela com 3 steps:
 *   1. "usuario" — escolhe ou cadastra o usuário
 *   2. "url"     — informa a URL e o modo do navegador
 *   3. "valor"   — escolhe o valor a monitorar
 *
 * No fim, navega para /monitor/:sessionId (a "página 2").
 */

import { useEffect, useState } from 'react';
import {
  api,
  mensagemDeErro,
  type Sessao,
  type SessaoHistorica,
  type Usuario,
  type ValorEncontrado,
} from '../api/client';
import { toast } from '../store/toastStore';
import { Skeleton, SkeletonList } from '../components/Skeleton';
import {
  primeiraMensagem,
  sessaoInSchema,
  usuarioInSchema,
} from '../api/schemas';

/** Chave do localStorage que lembra a última URL informada, por usuário. */
const lsUltimaUrl = (usuarioId: number) => `monitor.ultimaUrl.${usuarioId}`;

type Step = 'usuario' | 'url' | 'valor';

export default function SetupWizard() {
  const [step, setStep] = useState<Step>('usuario');
  const [usuario, setUsuario] = useState<Usuario | null>(null);
  const [sessao, setSessao] = useState<Sessao | null>(null);

  function iniciarMonitor(s: Sessao) {
    // Abre o monitor ao vivo em nova guia — mantemos o wizard aqui
    // pra o usuário poder iniciar outra sessão sem perder o contexto.
    window.open(`/monitor/${s.id}`, '_blank', 'noopener');
    // Reseta o wizard para o step inicial (mantém o usuário logado).
    setSessao(null);
    setStep('url');
  }

  return (
    <div className="space-y-6">
      <Steps atual={step} />

      {step === 'usuario' && (
        <StepUsuario
          onPronto={(u) => {
            setUsuario(u);
            setStep('url');
          }}
        />
      )}

      {step === 'url' && usuario && (
        <StepUrl
          usuario={usuario}
          onPronto={(s) => {
            setSessao(s);
            setStep('valor');
          }}
          onVoltar={() => setStep('usuario')}
        />
      )}

      {step === 'valor' && sessao && (
        <StepValor
          sessao={sessao}
          onPronto={() => iniciarMonitor(sessao)}
          onVoltar={() => setStep('url')}
        />
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Indicador de steps
// ---------------------------------------------------------------------------

function Steps({ atual }: { atual: Step }) {
  const items: { key: Step; label: string }[] = [
    { key: 'usuario', label: '1. Usuário' },
    { key: 'url', label: '2. Site' },
    { key: 'valor', label: '3. Valor' },
  ];
  const atualIdx = items.findIndex((i) => i.key === atual);

  return (
    <ol className="flex items-center gap-2 text-sm">
      {items.map((it, idx) => {
        const estado =
          idx < atualIdx ? 'feito' : idx === atualIdx ? 'atual' : 'futuro';
        return (
          <li key={it.key} className="flex items-center gap-2">
            <span
              className={
                estado === 'atual'
                  ? 'px-3 py-1 rounded-full bg-indigo-600 text-white'
                  : estado === 'feito'
                    ? 'px-3 py-1 rounded-full bg-indigo-100 text-indigo-700'
                    : 'px-3 py-1 rounded-full bg-gray-100 text-gray-500'
              }
            >
              {it.label}
            </span>
            {idx < items.length - 1 && (
              <span className="text-gray-300">→</span>
            )}
          </li>
        );
      })}
    </ol>
  );
}

// ---------------------------------------------------------------------------
// Step 1 — usuário
// ---------------------------------------------------------------------------

function StepUsuario({ onPronto }: { onPronto: (u: Usuario) => void }) {
  const [usuarios, setUsuarios] = useState<Usuario[]>([]);
  const [carregando, setCarregando] = useState(true);

  const [nome, setNome] = useState('');
  const [email, setEmail] = useState('');
  const [criando, setCriando] = useState(false);

  // Valida o formulário inteiro com Zod; erros específicos aparecem
  // abaixo de cada campo via `safeParse` individual.
  const erroNome = primeiraMensagem(usuarioInSchema.shape.nome, nome);
  const erroEmail = primeiraMensagem(usuarioInSchema.shape.email, email);
  const nomeOk = nome.length > 0 && !erroNome;
  const emailOk = email.length > 0 && !erroEmail;

  useEffect(() => {
    api
      .listarUsuarios()
      .then(setUsuarios)
      .catch((e) => toast.erro(mensagemDeErro(e)))
      .finally(() => setCarregando(false));
  }, []);

  async function cadastrar(e: React.FormEvent) {
    e.preventDefault();
    setCriando(true);
    try {
      const novo = await api.criarUsuario(nome.trim(), email.trim());
      toast.sucesso(`Bem-vindo, ${novo.nome}!`);
      onPronto(novo);
    } catch (e) {
      toast.erro(mensagemDeErro(e));
    } finally {
      setCriando(false);
    }
  }

  return (
    <div className="grid gap-6 md:grid-cols-2">
      <section className="bg-white rounded-lg border border-gray-200 p-6">
        <h2 className="text-lg font-medium mb-4">Usuários cadastrados</h2>
        {carregando && <SkeletonList linhas={3} />}
        {!carregando && usuarios.length === 0 && (
          <p className="text-gray-500">
            Nenhum usuário ainda. Cadastre ao lado.
          </p>
        )}
        <ul className="space-y-2">
          {usuarios.map((u) => (
            <li key={u.id}>
              <button
                onClick={() => onPronto(u)}
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
            {nome.length > 0 && erroNome && (
              <span className="text-xs text-red-600">{erroNome}</span>
            )}
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
            {email.length > 0 && erroEmail && (
              <span className="text-xs text-red-600">{erroEmail}</span>
            )}
          </label>
          <button
            type="submit"
            disabled={criando || !nomeOk || !emailOk}
            className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 disabled:opacity-60"
          >
            {criando ? 'Criando...' : 'Cadastrar e continuar'}
          </button>
        </form>
      </section>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Step 2 — URL + headless
// ---------------------------------------------------------------------------

function StepUrl({
  usuario,
  onPronto,
  onVoltar,
}: {
  usuario: Usuario;
  onPronto: (s: Sessao) => void;
  onVoltar: () => void;
}) {
  // Recupera a última URL usada por este navegador. É apenas um
  // valor inicial — o usuário pode apagar livremente.
  const [url, setUrl] = useState(
    () => localStorage.getItem(lsUltimaUrl(usuario.id)) ?? '',
  );
  const [headless, setHeadless] = useState(true);
  const [iniciando, setIniciando] = useState(false);

  const [historico, setHistorico] = useState<SessaoHistorica[]>([]);
  const [carregandoHist, setCarregandoHist] = useState(true);

  const erroUrl = primeiraMensagem(sessaoInSchema.shape.url, url);
  const urlOk = url.length > 0 && !erroUrl;

  useEffect(() => {
    // Histórico persistente do usuário — permite reusar uma URL antiga
    // num clique. Falha silenciosa: não é crítico.
    api
      .sessoesDoUsuario(usuario.id)
      .then(setHistorico)
      .catch(() => {})
      .finally(() => setCarregandoHist(false));
  }, [usuario.id]);

  async function iniciar(e: React.FormEvent) {
    e.preventDefault();
    if (!urlOk) {
      toast.aviso(erroUrl ?? 'Informe uma URL http(s) válida.');
      return;
    }
    setIniciando(true);
    try {
      const urlLimpa = url.trim();
      const sessao = await api.criarSessao(usuario.id, urlLimpa, headless);
      localStorage.setItem(lsUltimaUrl(usuario.id), urlLimpa);
      onPronto(sessao);
    } catch (e) {
      toast.erro(mensagemDeErro(e));
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
            className={`mt-1 w-full px-3 py-2 border rounded ${
              url.length > 0 && !urlOk
                ? 'border-red-400'
                : 'border-gray-300'
            }`}
          />
          {url.length > 0 && erroUrl && (
            <span className="text-xs text-red-600">{erroUrl}</span>
          )}
        </label>

        <fieldset>
          <legend className="text-sm text-gray-700 mb-1">
            Modo do navegador
          </legend>
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
          {!headless && (
            <p className="text-xs text-gray-500 mt-2">
              A janela do Chrome abre em segundo plano e não rouba foco
              durante o monitoramento.
            </p>
          )}
        </fieldset>

        <div className="flex gap-2">
          <button
            type="button"
            onClick={onVoltar}
            className="px-4 py-2 border border-gray-300 rounded hover:bg-gray-50"
          >
            Voltar
          </button>
          <button
            type="submit"
            disabled={iniciando || !urlOk}
            className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 disabled:opacity-60"
          >
            {iniciando ? 'Abrindo navegador...' : 'Continuar'}
          </button>
        </div>
      </form>

      <SessoesAnteriores
        carregando={carregandoHist}
        historico={historico}
        onReusar={(u) => setUrl(u)}
      />
    </section>
  );
}

// ---------------------------------------------------------------------------
// Widget — sessões anteriores do usuário
// ---------------------------------------------------------------------------

function SessoesAnteriores({
  carregando,
  historico,
  onReusar,
}: {
  carregando: boolean;
  historico: SessaoHistorica[];
  onReusar: (url: string) => void;
}) {
  const [aberto, setAberto] = useState(false);

  if (carregando) return null;
  if (historico.length === 0) return null;

  return (
    <details
      open={aberto}
      onToggle={(e) => setAberto((e.target as HTMLDetailsElement).open)}
      className="mt-6 border-t border-gray-200 pt-4"
    >
      <summary className="cursor-pointer text-sm text-indigo-600 hover:text-indigo-700 select-none">
        {aberto ? '▾' : '▸'} Sessões anteriores ({historico.length})
      </summary>
      <ul className="mt-3 space-y-2">
        {historico.slice(0, 10).map((s) => (
          <li
            key={s.id}
            className="text-sm border border-gray-200 rounded p-2 flex items-center justify-between gap-2"
          >
            <div className="min-w-0">
              <p className="truncate font-mono text-xs">{s.url}</p>
              <p className="text-xs text-gray-500">
                {new Date(s.encerrada_em).toLocaleString('pt-BR')} •{' '}
                {s.total_alteracoes} alterações • final:{' '}
                <span className="font-mono">{s.valor_final ?? '—'}</span>
              </p>
            </div>
            <button
              type="button"
              onClick={() => onReusar(s.url)}
              className="text-xs px-2 py-1 border border-gray-300 rounded hover:bg-indigo-50"
            >
              Reusar URL
            </button>
          </li>
        ))}
      </ul>
    </details>
  );
}

// ---------------------------------------------------------------------------
// Step 3 — seleção do valor
// ---------------------------------------------------------------------------

function StepValor({
  sessao,
  onPronto,
  onVoltar,
}: {
  sessao: Sessao;
  onPronto: () => void;
  onVoltar: () => void;
}) {
  const [valores, setValores] = useState<ValorEncontrado[]>([]);
  const [preview, setPreview] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [selecionando, setSelecionando] = useState<number | null>(null);

  useEffect(() => {
    // Busca valores + screenshot em paralelo. O screenshot é apenas
    // visual (contexto pro usuário), então a falha dele não deve
    // bloquear a listagem.
    let ativo = true;
    Promise.allSettled([
      api.listarValores(sessao.id),
      api.screenshot(sessao.id),
    ]).then((resultados) => {
      if (!ativo) return;
      const [resValores, resScreenshot] = resultados;
      if (resValores.status === 'fulfilled') {
        setValores(resValores.value);
      } else {
        toast.erro(mensagemDeErro(resValores.reason));
      }
      if (resScreenshot.status === 'fulfilled') {
        setPreview(resScreenshot.value.data);
      }
      setCarregando(false);
    });
    return () => {
      ativo = false;
    };
  }, [sessao.id]);

  async function selecionar(v: ValorEncontrado) {
    setSelecionando(v.indice);
    try {
      await api.selecionarValor(sessao.id, v.xpath, v.text);
      toast.sucesso('Monitoramento iniciado! Abrindo painel ao vivo...');
      onPronto();
    } catch (e) {
      toast.erro(mensagemDeErro(e));
      setSelecionando(null);
    }
  }

  return (
    <section className="bg-white rounded-lg border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-medium">Escolha o valor a monitorar</h2>
        <button
          onClick={onVoltar}
          className="text-sm text-gray-500 hover:text-gray-700"
        >
          ← Voltar
        </button>
      </div>

      <p className="text-xs text-gray-500 mb-3 break-all">
        URL atual: <span className="font-mono">{sessao.url}</span>
      </p>

      {/* Preview único da página — ajuda o usuário a confirmar que
          chegou no site certo antes de escolher o valor. */}
      <div className="mb-4 bg-gray-900 rounded border border-gray-300 overflow-hidden aspect-video">
        {preview ? (
          <img
            src={`data:image/png;base64,${preview}`}
            alt="Prévia do site monitorado"
            className="w-full h-full object-contain"
          />
        ) : carregando ? (
          <Skeleton className="w-full h-full !rounded-none" />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-400 text-sm">
            Sem prévia.
          </div>
        )}
      </div>

      {carregando && (
        <div className="grid gap-2 md:grid-cols-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-12" />
          ))}
        </div>
      )}

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
