import { renderHook } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useNotificarAlteracoes } from '../hooks/useNotificarAlteracoes';
import { useSessionStore } from '../store/sessionStore';
import { toast } from '../store/toastStore';

vi.mock('../store/sessionStore');
vi.mock('../store/toastStore', () => ({
  toast: { info: vi.fn() }
}));

type SessionState = ReturnType<typeof useSessionStore.getState>;

describe('useNotificarAlteracoes', () => {
  /**
   * Antes de cada teste, todos os mocks são limpos (chamadas, instâncias, resultados),
   * garantindo que o `toast.info` não carregue contagens de chamadas de testes anteriores.
   */
  beforeEach(() => {
    vi.clearAllMocks();
  });

  /**
   * Cenário: o hook é renderizado pela primeira vez com um histórico já contendo 1 item
   * Esperado:
   * - `toast.info` NÃO deve ser chamado, pois o item já existia no carregamento inicial
   *   e não representa uma alteração nova — o hook deve ignorar o estado inicial
   */
  it('não notifica no primeiro render (carregamento inicial)', () => {
    vi.mocked(useSessionStore).mockImplementation((selector) => {
      const state = { 
        historico: [{ valor_antigo: '0', valor_novo: '1' }], 
        sessao: null 
      } as unknown as SessionState;
      
      return selector(state);
    });

    renderHook(() => useNotificarAlteracoes());
    expect(toast.info).not.toHaveBeenCalled();
  });

  /**
   * Cenário: após o primeiro render, um novo item é adicionado ao histórico e o hook re-renderiza
   * Esperado:
   * - `toast.info` deve ser chamado exatamente 1 vez
   * - A mensagem do toast deve ser 'Valor mudou: 1 → 2', formatada com o
   *   `valor_antigo` e `valor_novo` do registro recém-adicionado
   */
  it('dispara toast quando um novo item é adicionado ao histórico', () => {
    let historicoMock = [{ valor_antigo: '0', valor_novo: '1' }];
    
    vi.mocked(useSessionStore).mockImplementation((selector) => {
      const state = { 
        historico: historicoMock, 
        sessao: null 
      } as unknown as SessionState;
      
      return selector(state);
    });

    const { rerender } = renderHook(() => useNotificarAlteracoes());
    historicoMock = [
      ...historicoMock, 
      { valor_antigo: '1', valor_novo: '2' }
    ];
    
    rerender();
    
    expect(toast.info).toHaveBeenCalledTimes(1);
    expect(toast.info).toHaveBeenCalledWith('Valor mudou: 1 → 2');
  });
});