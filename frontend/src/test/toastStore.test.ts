/**
 * Testes do toastStore.
 *
 * Usamos fake timers pra avançar o auto-dismiss sem esperar 3s reais.
 */

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { toast, useToastStore } from '../store/toastStore';

describe('toastStore', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    // Zera entre testes — o store é singleton.
    useToastStore.setState({ toasts: [] });
  });
  afterEach(() => {
    vi.useRealTimers();
  });

  it('emite um toast de sucesso e remove após o timeout', () => {
    toast.sucesso('ok');
    expect(useToastStore.getState().toasts).toHaveLength(1);
    expect(useToastStore.getState().toasts[0].mensagem).toBe('ok');
    expect(useToastStore.getState().toasts[0].tipo).toBe('sucesso');

    // Auto-dismiss padrão: 3500ms
    vi.advanceTimersByTime(3500);
    expect(useToastStore.getState().toasts).toHaveLength(0);
  });

  it('toasts de erro duram mais (5s)', () => {
    toast.erro('bum');
    vi.advanceTimersByTime(3500);
    expect(useToastStore.getState().toasts).toHaveLength(1);
    vi.advanceTimersByTime(1500);
    expect(useToastStore.getState().toasts).toHaveLength(0);
  });

  it('remover manualmente tira da fila imediatamente', () => {
    toast.info('oi');
    const id = useToastStore.getState().toasts[0].id;
    useToastStore.getState().remover(id);
    expect(useToastStore.getState().toasts).toHaveLength(0);
  });

  it('múltiplos toasts coexistem', () => {
    toast.sucesso('1');
    toast.aviso('2');
    toast.erro('3');
    expect(useToastStore.getState().toasts.map((t) => t.mensagem)).toEqual([
      '1',
      '2',
      '3',
    ]);
  });
});
