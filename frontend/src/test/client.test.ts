/**
 * Testes do cliente HTTP — cobrem a parte mais sensível:
 *   - Parsing de erros do FastAPI (detail string e Pydantic array)
 *   - ApiError com status e detail expostos
 *   - mensagemDeErro cai nos fallbacks certos
 *
 * O módulo usa `fetch` global, que mockamos com `vi.stubGlobal`.
 */

import { afterEach, describe, expect, it, vi } from 'vitest';
import { ApiError, api, mensagemDeErro } from '../api/client';

function respostaOk(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe('ApiError', () => {
  it('expõe status e detail e herda de Error', () => {
    const e = new ApiError(404, 'não achei');
    expect(e.status).toBe(404);
    expect(e.detail).toBe('não achei');
    expect(e.message).toBe('não achei');
    expect(e).toBeInstanceOf(Error);
  });
});

describe('mensagemDeErro', () => {
  it('usa detail para ApiError', () => {
    expect(mensagemDeErro(new ApiError(400, 'x'))).toBe('x');
  });
  it('usa message para Error comum', () => {
    expect(mensagemDeErro(new Error('boom'))).toBe('boom');
  });
  it('cai em fallback para tipos esquisitos', () => {
    expect(mensagemDeErro(42)).toBe('Erro inesperado.');
  });
});

describe('client.request (via api.listarUsuarios)', () => {
  it('transforma 404 com detail string em ApiError', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        new Response(JSON.stringify({ detail: 'não encontrado' }), {
          status: 404,
          headers: { 'Content-Type': 'application/json' },
        }),
      ),
    );
    await expect(api.listarUsuarios()).rejects.toMatchObject({
      status: 404,
      detail: 'não encontrado',
    });
  });

  it('extrai msg de array de validação Pydantic', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        new Response(
          JSON.stringify({
            detail: [{ msg: 'email inválido', type: 'value_error' }],
          }),
          {
            status: 422,
            headers: { 'Content-Type': 'application/json' },
          },
        ),
      ),
    );
    await expect(api.criarUsuario('x', 'y')).rejects.toMatchObject({
      status: 422,
      detail: 'email inválido',
    });
  });

  it('falha de rede vira ApiError(0, ...) mesmo depois dos retries', async () => {
    const fakeFetch = vi.fn(async () => {
      throw new TypeError('network');
    });
    vi.stubGlobal('fetch', fakeFetch);
    vi.useFakeTimers();

    const p = api.listarUsuarios();
    // Evita unhandled-rejection enquanto os timers avançam — Vitest
    // reclama se o motor de Promises vê a rejeição antes do `await`.
    p.catch(() => {});
    // Avança todos os retries agendados (250 + 750 ms).
    await vi.runAllTimersAsync();
    await expect(p).rejects.toMatchObject({ status: 0 });
    // GET → 1 tentativa + 2 retries = 3 chamadas de fetch.
    expect(fakeFetch).toHaveBeenCalledTimes(3);
    vi.useRealTimers();
  });

  it('devolve json em 200', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => respostaOk([{ id: 1, nome: 'g', email: 'g@x' }])));
    const r = await api.listarUsuarios();
    expect(r).toHaveLength(1);
    expect(r[0].nome).toBe('g');
  });
});
