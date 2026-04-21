/**
 * Cliente HTTP centralizado para a API FastAPI.
 *
 * `ApiError` carrega `status` + `detail` legível. Consumidores podem
 * fazer `instanceof ApiError` e usar `.detail` direto no toast.
 */

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

export class ApiError extends Error {
  // Atributos declarados explicitamente (sem parameter properties) para
  // satisfazer `erasableSyntaxOnly` do tsconfig — o build falha se o TS
  // tiver de gerar código para inicializá-los.
  readonly status: number;
  readonly detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${BASE_URL}${path}`, {
      headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
      ...init,
    });
  } catch {
    // Falha de rede (servidor desligado, CORS, offline...).
    throw new ApiError(0, 'Não consegui falar com o servidor. Verifique se o backend está rodando.');
  }
  if (!res.ok) {
    // FastAPI devolve { detail: "..." } em erros. Tenta extrair; se
    // não for JSON, usa o texto cru.
    const raw = await res.text();
    let detalhe = raw;
    try {
      const body = JSON.parse(raw);
      if (typeof body?.detail === 'string') detalhe = body.detail;
      else if (Array.isArray(body?.detail) && body.detail[0]?.msg) {
        // Erros de validação do Pydantic vêm como array.
        detalhe = body.detail[0].msg;
      }
    } catch {
      // payload não era JSON — mantém texto.
    }
    throw new ApiError(res.status, detalhe || `Erro HTTP ${res.status}`);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

/** Extrai uma mensagem amigável de qualquer erro de chamada. */
export function mensagemDeErro(e: unknown): string {
  if (e instanceof ApiError) return e.detail;
  if (e instanceof Error) return e.message;
  return 'Erro inesperado.';
}

// --- Tipos (espelham backend/schemas.py) -----------------------------------

export interface Usuario {
  id: number;
  nome: string;
  email: string;
}

export interface Sessao {
  id: string;
  usuario_id: number;
  url: string;
  headless: boolean;
  status: 'iniciada' | 'monitorando' | 'encerrada';
  xpath_monitorado: string | null;
  valor_atual: string | null;
}

export interface ValorEncontrado {
  indice: number;
  text: string;
  xpath: string;
}

export interface RegistroHistorico {
  ciclo: number;
  timestamp: string;
  valor_antigo: string;
  valor_novo: string;
}

export interface SessaoHistorica {
  id: string;
  usuario_id: number;
  url: string;
  xpath_monitorado: string | null;
  valor_inicial: string | null;
  valor_final: string | null;
  total_alteracoes: number;
  iniciada_em: string;
  encerrada_em: string;
}

// --- Endpoints -------------------------------------------------------------

export const api = {
  listarUsuarios: () => request<Usuario[]>('/usuarios'),
  criarUsuario: (nome: string, email: string) =>
    request<Usuario>('/usuarios', {
      method: 'POST',
      body: JSON.stringify({ nome, email }),
    }),

  criarSessao: (usuario_id: number, url: string, headless: boolean) =>
    request<Sessao>('/sessoes', {
      method: 'POST',
      body: JSON.stringify({ usuario_id, url, headless }),
    }),
  obterSessao: (id: string) => request<Sessao>(`/sessoes/${id}`),
  listarValores: (id: string) =>
    request<ValorEncontrado[]>(`/sessoes/${id}/valores`),
  screenshot: (id: string) =>
    request<{ data: string }>(`/sessoes/${id}/screenshot`),
  selecionarValor: (id: string, xpath: string, text: string) =>
    request<Sessao>(`/sessoes/${id}/selecionar`, {
      method: 'POST',
      body: JSON.stringify({ xpath, text }),
    }),
  historico: (id: string) =>
    request<RegistroHistorico[]>(`/sessoes/${id}/historico`),
  encerrar: (id: string) =>
    request<void>(`/sessoes/${id}`, { method: 'DELETE' }),

  // Histórico persistente
  sessoesDoUsuario: (usuarioId: number) =>
    request<SessaoHistorica[]>(`/usuarios/${usuarioId}/sessoes`),
  sessaoHistorica: (id: string) =>
    request<SessaoHistorica>(`/sessoes/historicas/${id}`),
  alteracoesHistoricas: (id: string) =>
    request<RegistroHistorico[]>(`/sessoes/historicas/${id}/alteracoes`),
};
