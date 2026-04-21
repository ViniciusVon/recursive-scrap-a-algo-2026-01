/**
 * Testes dos schemas Zod.
 *
 * Fazem dupla função: validam as regras e servem como contrato vivo
 * com o backend. Se um dia um campo mudar no Pydantic, esses testes
 * precisarão mudar junto.
 */

import { describe, expect, it } from 'vitest';
import {
  primeiraMensagem,
  selecaoInSchema,
  sessaoInSchema,
  usuarioInSchema,
} from '../api/schemas';

describe('usuarioInSchema', () => {
  it('aceita nome e e-mail válidos', () => {
    const r = usuarioInSchema.safeParse({ nome: 'Gabriel', email: 'g@x.com' });
    expect(r.success).toBe(true);
  });

  it('faz trim no nome', () => {
    const r = usuarioInSchema.parse({ nome: '   Gabriel   ', email: 'g@x.com' });
    expect(r.nome).toBe('Gabriel');
  });

  it('rejeita nome com menos de 3 caracteres', () => {
    const r = usuarioInSchema.safeParse({ nome: 'Ga', email: 'g@x.com' });
    expect(r.success).toBe(false);
  });

  it('rejeita e-mail inválido', () => {
    const r = usuarioInSchema.safeParse({ nome: 'Gabriel', email: 'n/a' });
    expect(r.success).toBe(false);
  });
});

describe('sessaoInSchema', () => {
  it('aceita URL https', () => {
    expect(
      sessaoInSchema.safeParse({
        usuario_id: 1,
        url: 'https://site.com/p',
        headless: true,
      }).success,
    ).toBe(true);
  });

  it('rejeita protocolo fora de http(s)', () => {
    const r = sessaoInSchema.safeParse({
      usuario_id: 1,
      url: 'ftp://site.com',
      headless: true,
    });
    expect(r.success).toBe(false);
  });

  it('rejeita usuario_id <= 0', () => {
    const r = sessaoInSchema.safeParse({
      usuario_id: 0,
      url: 'https://a.com/b',
      headless: true,
    });
    expect(r.success).toBe(false);
  });
});

describe('selecaoInSchema', () => {
  it('exige xpath e text não-vazios', () => {
    expect(selecaoInSchema.safeParse({ xpath: '', text: 'x' }).success).toBe(false);
    expect(selecaoInSchema.safeParse({ xpath: '//a', text: '' }).success).toBe(false);
    expect(selecaoInSchema.safeParse({ xpath: '//a', text: 'R$ 10' }).success).toBe(true);
  });
});

describe('primeiraMensagem', () => {
  it('devolve null quando válido', () => {
    expect(primeiraMensagem(usuarioInSchema.shape.nome, 'Gabriel')).toBeNull();
  });

  it('devolve a mensagem do primeiro erro', () => {
    const msg = primeiraMensagem(usuarioInSchema.shape.email, 'abc');
    expect(msg).toBeTruthy();
    expect(typeof msg).toBe('string');
  });
});
