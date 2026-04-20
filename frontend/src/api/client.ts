/**
 * Cliente HTTP centralizado para a API FastAPI.
 *
 * Fase 1 (MVP): `fetch` puro com um wrapper de erro.
 * Em fases futuras pode ganhar interceptors, retry, etc.
 */

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
    ...init,
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`HTTP ${res.status}: ${detail}`);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
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
};
